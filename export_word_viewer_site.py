# Static GitHub Pages build of the Word Viewer, with the TMX and PoS viewers.
#
# Tier: script. It drives the live Flask routes of "Word Viewer.py" through
# app.test_client(), so every JSON file is exactly what the local viewer
# serves, then removes what the public site must not carry:
#   - pronunciation clips (Hector's recordings): no audio, no pronunciation keys
#   - SITE_EXCLUDE_CONTEXTS (copyrighted source texts), from the dictionary
#     examples and from the TMX/PoS corpus
#   - images that are not openly licensed (fair use, Giphy hotlinks with none)
#   - GIZA alignments in examples (noisy; never shipped, see project notes)
#   - glb-x-fokus annotation (never read: _load_tmx_raw only takes "glb")
#
# Inputs: Word Viewer.py with its WordViewerLMDB and sources, word_viewer.html,
#         tmx_viewer.html, pos_viewer.html, corpus_data.js, word_viewer_scripts.js,
#         Source Sans 3 in ~/.local/share/fonts/SourceSans3 (optional).
# Output: site_build/ (git-ignored), ready to copy into Palaeos/globasa-tools.
#   index.html, tmx.html, pos.html, *.js, fonts/, .nojekyll, LICENSE, SOURCES.json
#   data/i18n.json, etym_langs.json, lang_coverage.json, tags.json, glossary.json,
#   translation_langs.json
#   data/lookup/<site_key(word)>.json     one per headword
#   data/suggest/words.json, <site_key(lang)>.json
#   data/corpus/languages.json, glb.json, <lang>.json, pos_tags.json
# Run: venv/bin/python export_word_viewer_site.py   (deploy_site.sh runs it)
# Fails loudly (exit 1) when the final audit finds anything that must not ship.
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import urllib.parse
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, "site_build")
OUT_MARKER = ".site_build"  # only a directory carrying this is ever wiped
FONT_SRC = os.path.expanduser("~/.local/share/fonts/SourceSans3")
FONT_FILES = ["SourceSans3VF-Upright.otf.woff2", "SourceSans3VF-Italic.otf.woff2"]

# Copyrighted source texts (user, 2026-11-28): dropped everywhere on the site.
# Prefix match on the TMX x-context; the local viewer still shows them.
SITE_EXCLUDE_CONTEXTS = (
    "Preata de Mansenyor Quin fal Agatha Christie",
    "“Am Eskri Jandan” fal Paul Graham",
)
PAGES = {"index.html": "word_viewer.html", "tmx.html": "tmx_viewer.html", "pos.html": "pos_viewer.html"}
SCRIPTS = ["word_viewer_scripts.js", "corpus_data.js"]
MODE_SERVER = '<meta name="wv-mode" content="server">'
MODE_STATIC = '<meta name="wv-mode" content="static">'


def site_key(text):
    """Filename for a word or language. Must match siteKey() in word_viewer.html:
    URL-safe, and distinct on case-insensitive filesystems (atlas / Atlas)."""
    out = []
    for ch in text:
        if ch in "abcdefghijklmnopqrstuvwxyz0123456789-":
            out.append(ch)
        elif ch.isascii() and ch.isupper():
            out.append("_" + ch.lower())
        else:
            out.append("~%04x" % ord(ch))
    return "".join(out)


def load_word_viewer():
    os.environ["WV_NO_RUN"] = "1"
    spec = importlib.util.spec_from_file_location("word_viewer", os.path.join(BASE_DIR, "Word Viewer.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.app.config["WV_EXCLUDE_CONTEXTS"] = SITE_EXCLUDE_CONTEXTS
    return module


def ensure_credit_fields(wv, client):
    """Image rows built before the credit line (2026-11-28) lack `publishable`;
    rebuild the LMDB through the viewer's own /rebuild route then."""
    for word in ("betula", "abakus"):
        for sense in (wv._db.get_images(word) or {}).get("senses") or []:
            for img in sense.get("images") or []:
                if "publishable" in img:
                    return
                print("  WordViewerLMDB predates image credits: rebuilding...")
                get_json(client, "/rebuild")
                return


def fresh_out_dir():
    if os.path.isdir(OUT_DIR):
        if not os.path.isfile(os.path.join(OUT_DIR, OUT_MARKER)):
            sys.exit(f"{OUT_DIR} exists but was not made by this script; not deleting it.")
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR)
    open(os.path.join(OUT_DIR, OUT_MARKER), "w").close()


def write_json(rel_path, obj):
    path = os.path.join(OUT_DIR, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


def get_json(client, url):
    r = client.get(url)
    if r.status_code != 200:
        sys.exit(f"{url}: HTTP {r.status_code}")
    return r.get_json()


def is_excluded(context):
    return context.startswith(SITE_EXCLUDE_CONTEXTS)


# ---------------------------------------------------------------- dictionary

def clean_images(senses, word, dropped):
    for sense in senses or []:
        keep = []
        for img in sense.get("images") or []:
            if img.pop("publishable", True):
                keep.append(img)
            else:
                dropped.append((word, img.get("license") or "(no licence)", img.get("source_page") or img.get("url")))
        sense["images"] = keep


def compact_languages(data, lang_keys):
    """Translation tables in the compact site form (2026-11-28; 19.5 -> 8 MB):
    `languages` {lang: [{gender, text}]} becomes `langs` {lang: [text | [text, gender]]}
    with empty languages left out. Every PoS group lists the same languages
    (written once, data/translation_langs.json); wvFetch restores the exact
    server shape. Fails loudly if a group breaks those assumptions."""
    for group in (data.get("translations") or {}).get("pos_groups") or []:
        languages = group.pop("languages")
        keys = list(languages)
        if not lang_keys:
            lang_keys.extend(keys)
        elif keys != lang_keys:
            sys.exit(f"{data['word']}: translation languages differ from the first lookup's")
        langs = {}
        for lang, glosses in languages.items():
            if not glosses:
                continue
            out = []
            for g in glosses:
                if set(g) != {"gender", "text"} or not isinstance(g["text"], str):
                    sys.exit(f"{data['word']}/{lang}: unexpected gloss shape {g!r}")
                out.append(g["text"] if g["gender"] is None else [g["text"], g["gender"]])
            langs[lang] = out
        group["langs"] = langs


def clean_lookup(data, word, dropped_images):
    data["has_pronunciation"] = False
    data.pop("pronunciation_file", None)
    data.pop("pronunciation_voice", None)
    for ex in data.get("examples") or []:
        ex.pop("alignments", None)
    clean_images(data.get("image_senses"), word, dropped_images)
    for group in (data.get("translations") or {}).get("pos_groups") or []:
        clean_images(group.get("image_senses"), word, dropped_images)
    # Legacy single-image field: rebuilt from what survived (or dropped).
    first = next((img for sense in data.get("image_senses") or [] for img in sense["images"]), None)
    if first is None:
        first = next((img for g in (data.get("translations") or {}).get("pos_groups") or []
                      for sense in g.get("image_senses") or [] for img in sense["images"]), None)
    data["image"] = {"direct_url": first["url"], "source_page": first["source_page"]} if first else None
    return data


def export_dictionary(wv, client):
    write_json("data/i18n.json", get_json(client, "/i18n"))
    write_json("data/etym_langs.json", get_json(client, "/etym_langs"))
    write_json("data/lang_coverage.json", get_json(client, "/lang_coverage"))
    write_json("data/tags.json", {tag: sorted(words) for tag, words in wv._tag_index.items()})

    # /suggest: the index in the server's iteration order, as [term, words]
    # pairs (a JS object would reorder integer-like keys).
    write_json("data/suggest/words.json", list(wv._all_entries))
    for lang, idx in wv._trans_index.items():
        write_json(f"data/suggest/{site_key(lang)}.json", [[term, sorted(words)] for term, words in idx.items()])

    # word_glossary (example tooltips) depends only on the phrase, so every
    # lookup repeated the same entries: 69 of 127 MB (2026-11-28). It goes
    # into one shared data/glossary.json; wvFetch re-attaches it to each lookup.
    # The tooltip code only reads n-grams of the sentence shown, so a superset
    # renders the same.
    dropped_images = []
    glossary = {}
    lang_keys = []
    words = list(wv._all_entries)
    for n, word in enumerate(words, 1):
        data = get_json(client, "/lookup/" + urllib.parse.quote(word, safe=""))
        for phrase, glosses in (data.pop("word_glossary", None) or {}).items():
            if glossary.setdefault(phrase, glosses) != glosses:
                sys.exit(f"glossary entry for {phrase!r} differs between lookups ({word}): cannot share it")
        data = clean_lookup(data, word, dropped_images)
        compact_languages(data, lang_keys)
        write_json(f"data/lookup/{site_key(word)}.json", data)
        if n % 1000 == 0:
            print(f"  lookups: {n}/{len(words)}")
    write_json("data/glossary.json", glossary)
    write_json("data/translation_langs.json", lang_keys)
    print(f"  lookups: {len(words)} written; shared glossary: {len(glossary)} phrases")
    return dropped_images


# ---------------------------------------------------------------- corpus

def export_corpus(wv, client):
    """Each Globasa sentence is tokenized (morphemes + PoS) once into glb.json;
    the per-language files only point into it."""
    glb_index = {}
    glb_rows = []
    languages = []
    excluded = 0
    for lang in wv._tmx_available_langs():
        rows = []
        for e in wv._load_tmx_raw(lang):
            if is_excluded(e["context"]):
                excluded += 1
                continue
            g = glb_index.get(e["glb_text"])
            if g is None:
                g = glb_index[e["glb_text"]] = len(glb_rows)
                glb_rows.append(e["glb_text"])
            rows.append([g, e["context"], e["target_text"]])
        wv._tmx_raw_cache.pop(lang, None)
        if rows:
            write_json(f"data/corpus/{urllib.parse.quote(lang, safe='')}.json", rows)
            languages.append({"lang": lang, "count": len(rows)})

    unique = [{"id": i, "context": "", "glb_text": t, "target_text": ""} for i, t in enumerate(glb_rows)]
    glb_out = []
    for start in range(0, len(unique), 200):
        chunk = unique[start:start + 200]
        for tmx, pos in zip(wv._tokenize_page(chunk, decompose=False), wv._pos_tokenize_page(chunk)):
            glb_out.append({"glb_text": tmx["glb_text"], "glb_morphs": tmx["glb_morphs"],
                            "mwes": tmx["mwes"], "glb_pos_tokens": pos["glb_pos_tokens"]})
    write_json("data/corpus/glb.json", glb_out)
    write_json("data/corpus/languages.json", languages)
    write_json("data/corpus/pos_tags.json", get_json(client, "/api/pos/tags"))
    print(f"  corpus: {len(languages)} languages, {len(glb_out)} Globasa sentences, "
          f"{excluded} excluded TU-language pairs")


# ---------------------------------------------------------------- assets

def export_assets():
    for out_name, src in PAGES.items():
        with open(os.path.join(BASE_DIR, src), encoding="utf-8") as f:
            html = f.read()
        if html.count(MODE_SERVER) != 1:
            sys.exit(f"{src}: expected one {MODE_SERVER}")
        with open(os.path.join(OUT_DIR, out_name), "w", encoding="utf-8") as f:
            f.write(html.replace(MODE_SERVER, MODE_STATIC))
    for name in SCRIPTS:
        shutil.copy(os.path.join(BASE_DIR, name), OUT_DIR)
    shutil.copy(os.path.join(BASE_DIR, "LICENSE"), OUT_DIR)
    open(os.path.join(OUT_DIR, ".nojekyll"), "w").close()

    font_out = os.path.join(OUT_DIR, "fonts", "SourceSans3")
    present = [f for f in FONT_FILES if os.path.isfile(os.path.join(FONT_SRC, f))]
    if present:
        os.makedirs(font_out)
        for f in present:
            shutil.copy(os.path.join(FONT_SRC, f), font_out)
        licence = next((f for f in os.listdir(FONT_SRC) if f.upper().startswith(("LICENSE", "OFL"))), None)
        if licence:
            shutil.copy(os.path.join(FONT_SRC, licence), font_out)
        else:
            print("  Warning: Source Sans 3 licence file not found; add OFL.txt to fonts/SourceSans3")
    else:
        print(f"  Warning: Source Sans 3 not in {FONT_SRC} (fallback: the page uses its font stack)")


def write_sources():
    def git(*args):
        return subprocess.run(["git", "-C", BASE_DIR, *args], capture_output=True, text=True).stdout.strip()
    wordlist = os.path.join(BASE_DIR, "word-list.csv")
    write_json("SOURCES.json", {
        "built": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "GlobasaLexiTools": {"repo": "https://github.com/Palaeos/GlobasaLexiTools",
                             "commit": git("rev-parse", "HEAD"),
                             "uncommitted_changes": bool(git("status", "--porcelain", "--untracked-files=no"))},
        "word_list": {"url": "https://cdn.globasa.net/api2/word-list.csv",
                      "fetched": datetime.fromtimestamp(os.path.getmtime(wordlist), timezone.utc).strftime("%Y-%m-%d")},
        "excluded_contexts": list(SITE_EXCLUDE_CONTEXTS),
    })


# ---------------------------------------------------------------- audit

ALLOWED_TOP = {"index.html", "tmx.html", "pos.html", "LICENSE", "SOURCES.json", ".nojekyll", OUT_MARKER,
               *SCRIPTS}
FORBIDDEN_STRINGS = ["pronunciation_file", "pronunciation_voice", "glb-x-fokus", "/audio/", "giphy.com",
                     *SITE_EXCLUDE_CONTEXTS]


def audit():
    problems = []
    for root, _, files in os.walk(OUT_DIR):
        rel_root = os.path.relpath(root, OUT_DIR)
        for name in files:
            rel = os.path.normpath(os.path.join(rel_root, name))
            top = rel.split(os.sep)[0]
            if rel_root == "." and name not in ALLOWED_TOP:
                problems.append(f"unexpected file {rel}")
            elif top == "data" and not name.endswith(".json"):
                problems.append(f"non-JSON in data/: {rel}")
            elif top == "fonts" and not name.endswith((".woff2", ".txt", ".md")) and not name.upper().startswith(("LICENSE", "OFL")):
                problems.append(f"unexpected font file {rel}")
            elif top not in ("data", "fonts") and rel_root != ".":
                problems.append(f"unexpected directory {rel}")
            if top == "data":
                with open(os.path.join(root, name), encoding="utf-8") as f:
                    text = f.read()
                for bad in FORBIDDEN_STRINGS:
                    if bad in text:
                        problems.append(f"{rel} contains {bad!r}")
                if '"has_pronunciation":true' in text:
                    problems.append(f"{rel} has a pronunciation")
    return problems


def report_size():
    total = files = 0
    for root, _, names in os.walk(OUT_DIR):
        for name in names:
            files += 1
            total += os.path.getsize(os.path.join(root, name))
    print(f"site_build/: {files} files, {total / 1e6:.1f} MB")


print("Loading Word Viewer...")
wv = load_word_viewer()
client = wv.app.test_client()
ensure_credit_fields(wv, client)
fresh_out_dir()
print("Exporting dictionary...")
dropped = export_dictionary(wv, client)
print("Exporting TMX/PoS corpus...")
export_corpus(wv, client)
export_assets()
write_sources()
if dropped:
    unique_dropped = sorted(set(dropped))
    print(f"  images left out (not openly licensed): {len(unique_dropped)}")
    for word, licence, src in unique_dropped:
        print(f"    {word}: {licence} {src}")
report_size()
problems = audit()
if problems:
    print("AUDIT FAILED:")
    for p in problems[:50]:
        print("  " + p)
    sys.exit(1)
print("Audit passed.")
