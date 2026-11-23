"""
Score the den-/hin- focus stage (glb-neural.py focus) on the Christie excerpt: the English TUs
of "Preata de Mansenyor Quin fal Agatha Christie" (extend_tmx_christie.py) are translated as
one document, one TU per line, so focus carries across sentences, then the person-reference
forms of each output line are aligned with those of the Globasa TU.

    python3 focus_eval.py            # focus on (default) vs AP_SETVAR=nofocus
    python3 focus_eval.py --lines    # also list every line whose forms differ
    python3 focus_eval.py --setvar=cast=PATH   # extra AP_SETVAR for every run (a cast list)

Needs eng-nlp-service.py running (port 8597); without it the stage passes through and the
script says so. Reported: aligned positions where gold and output agree, the confusion pairs,
and the den/hin forms the gold has; then the same for the man-/fem- nouns and titles (Mansenyor
/ Senyor, femixu / ixu, femgami / gami ...) against AP_SETVAR=nomanfem.
"""
import difflib
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter

TMX = "Doxo_passages_extended.tmx"
CONTEXT = "Preata de Mansenyor Quin fal Agatha Christie"
PAIR = "GlobasaTranslation/apertium-glb-eng"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
FORMS = {"te", "ete", "dente", "denete", "hinte", "hinete", "tesu", "etesu", "densu", "hinsu", "sesu"}
FOCUS = {"dente", "denete", "hinte", "hinete", "densu", "hinsu"}
# man-/fem- nouns and titles with their neutral forms (the excerpt's vocabulary)
MANFEM = {"senyor", "mansenyor", "femsenyor", "ixu", "manixu", "femixu", "gami", "mangami",
          "femgami", "nini", "mannini", "femnini"}


def units():
    out = []
    for tu in ET.parse(TMX).iter("tu"):
        props = {p.get("type"): p.text for p in tu.iter("prop")}
        if props.get("x-context") != CONTEXT:
            continue
        t = {v.get(XML_LANG): " ".join("".join(v.itertext()).split()) for v in tu.iter("tuv")}
        out.append((t["en"], t["glb"]))
    return out[1:]                                   # the title is not a sentence


def forms(text, vocab=FORMS):
    return [w for w in re.findall(r"[\wø]+", text.lower()) if w in vocab]


def translate(lines, setvar=""):
    env = dict(os.environ)
    if setvar:
        env["AP_SETVAR"] = setvar
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
        path = f.name
    try:
        r = subprocess.run(["apertium", "-d", PAIR, "eng-glb", path], capture_output=True,
                           text=True, env=env)
    finally:
        os.unlink(path)
    out = r.stdout.rstrip("\n").split("\n")
    if len(out) != len(lines):
        raise SystemExit(f"line count changed: {len(lines)} in, {len(out)} out")
    return out


def score(gold, mt, vocab=FORMS):
    agree, total, conf = 0, 0, Counter()
    for g, m in zip(gold, mt):
        gf, mf = forms(g, vocab), forms(m, vocab)
        sm = difflib.SequenceMatcher(a=gf, b=mf, autojunk=False)
        for op, a1, a2, b1, b2 in sm.get_opcodes():
            if op == "equal":
                agree += a2 - a1
                total += a2 - a1
            elif op == "replace" and a2 - a1 == b2 - b1:
                total += a2 - a1
                conf.update(zip(gf[a1:a2], mf[b1:b2]))
            else:
                total += a2 - a1
                conf.update((x, "∅") for x in gf[a1:a2])
                conf.update(("∅", x) for x in mf[b1:b2])
    return agree, total, conf


try:
    urllib.request.build_opener(urllib.request.ProxyHandler({})).open(
        urllib.request.Request("http://127.0.0.1:8597/analyze", data=b'{"text": "Hi."}',
                               headers={"Content-Type": "application/json"}), timeout=30)
except Exception as e:
    raise SystemExit(f"eng-nlp-service.py is not reachable on :8597 ({e}); start it first")

tus = units()
en, gold = [e for e, _ in tus], [g for _, g in tus]
gold_focus = Counter(f for g in gold for f in forms(g) if f in FOCUS)
print(f"{len(tus)} sentences; gold den/hin forms: {dict(gold_focus)}\n")
EXTRA = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--setvar=")), "")
join = lambda v: ",".join(x for x in (v, EXTRA) if x)
runs = {"focus": translate(en, join("")), "nofocus": translate(en, join("nofocus"))}
for name, mt in runs.items():
    agree, total, conf = score(gold, mt)
    mt_focus = Counter(f for m in mt for f in forms(m) if f in FOCUS)
    print(f"== {name}: {agree}/{total} gold person forms matched ({100 * agree / max(total, 1):.1f}%);"
          f" output den/hin forms: {dict(mt_focus)}")
    for (g, m), n in conf.most_common():
        print(f"   gold {g:7s} -> output {m:7s} {n}")
    print()
runs["nomanfem"] = translate(en, join("nomanfem"))
for name in ("focus", "nomanfem"):
    agree, total, conf = score(gold, runs[name], MANFEM)
    print(f"== man-/fem- ({'default' if name == 'focus' else name}): {agree}/{total} gold forms matched"
          f" ({100 * agree / max(total, 1):.1f}%)")
    for (g, m), n in conf.most_common():
        print(f"   gold {g:9s} -> output {m:9s} {n}")
    print()
if "--lines" in sys.argv:
    for e, g, m in zip(en, gold, runs["focus"]):
        if forms(g) != forms(m):
            print(f"EN   {e}\nGOLD {g}\nMT   {m}\n     gold {forms(g)} / output {forms(m)}\n")
