"""Mode manifests for the browser translator (web/), generated from the compiled pairs.

For every installed Globasa mode of the pairs in PAIRS, builds the pipeline the apertium
command runs for plain text: apertium-destxt, then the mode as apertium-wblank-mode
rewrites it (apertium-normalize first, word-bound blanks attached after the analyser and
detached before generation; taken from the installed apertium-wblank-mode itself), then
apertium-retxt. The AP_SETVAR stream command goes in after destxt and out before retxt.
Writes

    web/dist/pairs/index.json      the modes: label, languages, preferences, size
    web/dist/pairs/<mode>.json     ordered steps (wasm tool or Python script) and files
    web/dist/pairs/files/<dir>/... the compiled files and Python steps, copied

Paths inside the pipelines become /p/<pair dir>/<file>, the same in the wasm tools'
file system and in Pyodide's. Generated output: never edit by hand, rerun instead.

    python3 web/build_modes.py
"""
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from apertium_common import APERTIUM_ROOT  # noqa: E402

PAIRS = ["glb-eng", "glb-fra", "glb-spa", "glb-epo", "glb-deu", "glb-nld"]
# Not in the browser yet: jpn (MeCab front end), grc (treebank corpus pipelines).
EXCLUDED = {"glb-jpn": "needs MeCab in the browser", "glb-grc": "corpus pipelines, not text"}
OUT = os.path.join(HERE, "dist", "pairs")
TOOLS = {"lt-proc", "cg-proc", "apertium-tagger", "apertium-pretransfer", "lrx-proc",
         "lsx-proc", "apertium-anaphora", "rtx-proc", "apertium-destxt", "apertium-retxt",
         "apertium-normalize", "apertium-wblank-attach", "apertium-wblank-detach"}
# Files of the apertium installation itself, served from web/dist/wasm/ (build_wasm.sh)
SYSTEM_FILES = {"/usr/share/apertium/nfcn.nrm": "/icu/nfcn.nrm"}
DATA_EXT = (".py", ".tsv", ".json", ".lst")
LANG_NAMES = {"glb": "Globasa", "eng": "English", "deu": "German", "fra": "French",
              "nld": "Dutch", "spa": "Spanish", "epo": "Esperanto"}
# Same as the Word Viewer's translation aide: choice = one option at a time.
PREF_KINDS = {"eng_variety": "choice"}

# Python steps that need a local NLP service, and the switch that turns each off.
# The runner sets the switch and reports "(fallback: no neural service in browser)".
# glb-neural.py's manfem and render stages need no service and run as they are.
NEURAL = {"glb-neural.py": ("GLB_NEURAL", {"parse", "coref", "focus"}),
          "eng-glb-neural.py": ("ENG_GLB_NEURAL", None),
          "fra-glb-neural.py": ("FRA_GLB_NEURAL", None)}

# Steps whose service the page can stand in for with a model of its own (src/tagger.mjs), keyed
# by the step's script and arguments: the step's client is pointed at http://browser-nlp
# (py/runner.py answers it); the "neural" switch above stays the fallback when the browser model
# is not loaded. needs_parse: without the parser files the step is not run on the browser model
# (the switch turns it off). no_parser: added to the note when the parser is missing. fallback:
# what the browser model never gives (always labelled).
ENG_PAGE = {"lang": "eng", "env": {"ENG_NLP_URL": "http://browser-nlp", "GLB_NLP_URL": "http://browser-nlp"}}
BROWSER_NLP = {
    ("eng-glb-neural.py", "pos"): {
        **ENG_PAGE, "note": "in-browser tagger and parser (stanza combined + gum tagger, combined parser; "
                            "non-transformer)",
        "no_parser": "no parser in browser, so the name and that/which checks are skipped"},
    ("eng-glb-neural.py", "coref"): {
        **ENG_PAGE, "needs_parse": True, "note": "in-browser parser",
        "fallback": "no coreference model in browser; sesu only for an agreeing pronoun subject with "
                    "no other owner in the clause"},
    ("glb-neural.py", "eng", "parse"): {
        **ENG_PAGE, "needs_parse": True, "note": "in-browser parser (questions)"},
}

JOIN_RE = re.compile(r'os\.path\.join\(\s*(?:HERE|_HERE)\s*,\s*"\.\."\s*,\s*"([^"]+)"(?:\s*,\s*"([^"]+)")?\s*\)')


def virtual(path):
    """Absolute pair path -> /p/<dir>/<file>."""
    rel = os.path.relpath(path, APERTIUM_ROOT)
    if rel.startswith(".."):
        raise ValueError(f"outside {APERTIUM_ROOT}: {path}")
    return "/p/" + rel.replace(os.sep, "/")


def mode_langs(name):
    m = re.fullmatch(r"([a-z]{2,3})(?:_\w+)?-([a-z]{2,3})(?:_(\w+))?", name)
    return (m.group(1), m.group(2), m.group(3)) if m else (None, None, None)


def read_prefs(path):
    """[{id, kind, description, options}] from prefs/<mode>.xml (as the translation aide)."""
    if not os.path.exists(path):
        return []
    out = []
    for pref in ET.parse(path).getroot().iter("preference"):
        desc = next((d.text for d in pref.findall("description") if d.get("lang") == "eng"), None) \
            or next((d.text for d in pref.findall("description")), "") or pref.get("id")
        out.append({"id": pref.get("id"), "kind": PREF_KINDS.get(pref.get("id"), "switch"),
                    "description": " ".join(desc.split()),
                    "options": [o.get("id") for o in pref.iter("option")]})
    return out


def dir_data(d):
    """Top-level data and script files of a pair folder."""
    return [os.path.join(d, f) for f in sorted(os.listdir(d))
            if f.endswith(DATA_EXT) and os.path.isfile(os.path.join(d, f))]


def script_refs(script, d):
    """Files a Python step reads: names of files in its folder that occur in its text,
    and os.path.join(HERE, "..", dir[, file]) references to sibling folders."""
    text = open(script, encoding="utf-8").read()
    refs = set()
    for f in os.listdir(d):
        p = os.path.join(d, f)
        if os.path.isfile(p) and f"\"{f}\"" in text:
            refs.add(p)
    for sub, f in JOIN_RE.findall(text):
        other = os.path.join(APERTIUM_ROOT, sub)
        if not os.path.isdir(other):
            continue
        if f:
            if os.path.isfile(os.path.join(other, f)):
                refs.add(os.path.join(other, f))
        else:
            refs.update(dir_data(other))
    return refs


def build_mode(pair, d, name):
    steps, files = [], set(dir_data(d))
    mode = subprocess.run(["apertium-wblank-mode", os.path.join(d, "modes", name + ".mode")],
                          capture_output=True, text=True, check=True).stdout.strip()
    # $1 = -g (generator), $2 = "" (tagger option), as the apertium command passes them
    cmds = [c.strip().replace("$1", "-g").replace("$2", "") for c in mode.split(" | ")]
    for cmd in ["apertium-destxt"] + cmds + ["apertium-retxt"]:
        argv = shlex.split(cmd)
        if argv[0] == "python3":
            argv = [a for a in argv[1:] if a != "-I"]
            script = argv[0]
            files.add(script)
            files |= script_refs(script, os.path.dirname(script))
            args = []
            for a in argv[1:]:           # e.g. fra-glb-imparfait.py <pair>/fra-glb.imparfait.json
                if a.startswith("/"):
                    files.add(a)
                    args.append(virtual(a))
                else:
                    args.append(a)
            step = {"py": virtual(script), "args": args, "cmd": cmd}
            base = os.path.basename(script)
            if base in NEURAL:
                env, stages = NEURAL[base]
                stage = argv[-1] if len(argv) > 1 else ""
                if stages is None or stage in stages:
                    step["neural"] = env
                if (base, *argv[1:]) in BROWSER_NLP:
                    step["browser_nlp"] = BROWSER_NLP[(base, *argv[1:])]
            steps.append(step)
        elif argv[0] in TOOLS:
            args = []
            for a in argv[1:]:
                if a in SYSTEM_FILES:
                    args.append(SYSTEM_FILES[a])
                elif a.startswith("/"):
                    files.add(a)
                    args.append(virtual(a))
                else:
                    args.append(a)
            steps.append({"tool": argv[0], "args": args, "cmd": cmd})   # cmd: native, for tests
        else:
            raise ValueError(f"{name}: unsupported step {argv[0]!r}")
    missing = sorted(f for f in files if not os.path.exists(f))
    if missing:
        raise FileNotFoundError(f"{name}: missing {missing[0]}")
    return steps, files


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "files"))
    index, copied = [], set()
    for pair in PAIRS:
        d = os.path.join(APERTIUM_ROOT, f"apertium-{pair}")
        xml = open(os.path.join(d, "modes.xml"), encoding="utf-8").read()
        for m in re.finditer(r'<mode name="([^"]+)"([^>]*)>', xml):
            name, attrs = m.groups()
            src, tgt, variant = mode_langs(name)
            if 'install="yes"' not in attrs or "glb" not in (src, tgt):
                continue
            if not os.path.exists(os.path.join(d, "modes", name + ".mode")):
                continue
            steps, files = build_mode(pair, d, name)
            text = open(os.path.join(d, "modes", name + ".mode"), encoding="utf-8").read()
            prefs = read_prefs(os.path.join(d, "prefs", name + ".xml"))
            if "glb-story.py" in text and not any(p["id"] == "story" for p in prefs):
                prefs.append({"id": "story", "kind": "switch", "options": [],
                              "description": 'Story mode: narrative past without "le"'})
            entries = []
            for f in sorted(files):
                v = virtual(f)
                dst = os.path.join(OUT, "files", v[len("/p/"):])
                if v not in copied:
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copyfile(f, dst)
                    copied.add(v)
                entries.append({"path": v, "url": "files/" + v[len("/p/"):],
                                "size": os.path.getsize(f)})
            label = f"{LANG_NAMES.get(src, src)} → {LANG_NAMES.get(tgt, tgt)}"
            if variant:
                label += f" ({variant})"
            manifest = {"mode": name, "label": label, "src": src, "tgt": tgt,
                        "steps": steps, "files": entries}
            with open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8") as f:
                json.dump(manifest, f, ensure_ascii=False, indent=1)
            index.append({"mode": name, "label": label, "src": src, "tgt": tgt, "prefs": prefs,
                          "neural": sorted({s["neural"] for s in steps if "neural" in s}),
                          "bytes": sum(e["size"] for e in entries)})
    index.sort(key=lambda p: (p["mode"] not in ("eng-glb", "glb-eng"), p["label"]))
    # content hash of everything copied: the page's cache name, so a rebuild invalidates it
    h = hashlib.sha256()
    for r, _, fs in sorted(os.walk(OUT)):
        for f in sorted(fs):
            h.update(f.encode())
            with open(os.path.join(r, f), "rb") as fh:
                h.update(fh.read())
    with open(os.path.join(OUT, "index.json"), "w", encoding="utf-8") as f:
        json.dump({"version": h.hexdigest()[:12], "modes": index, "excluded": EXCLUDED},
                  f, ensure_ascii=False, indent=1)
    for p in index:
        print(f"{p['mode']:16} {p['bytes'] / 1e6:6.1f} MB  {len(p['prefs'])} prefs  neural={','.join(p['neural']) or '-'}")
    total = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(OUT) for f in fs)
    print(f"{len(index)} modes, {total / 1e6:.1f} MB in {OUT}")


main()
