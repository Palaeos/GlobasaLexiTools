"""Word Selector -- local page for automated Globasa word selection.

    venv/bin/python "Word Selector.py"        then open http://localhost:8092

Build a concept from Wiktionary senses (any built wiki), Wikipedia articles /
Wikidata QIDs and seed words; the page gathers the source words, renders them
in Globasa letters, clusters etymons, ranks clusters by the methodology,
proposes blended roots and assembles a decision dossier. Nothing is written to
the word list: Save appends to word_selection_decisions.jsonl (and the dossier
to word_selection_dossiers/), and hand-edited renderings to
word_selection_overrides.jsonl, which word_selection_eval.py can use as gold.
"""

import datetime
import hashlib
import json
import os
import sys

from flask import Flask, jsonify, request, send_from_directory

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from word_selection import collision, contrasts, dossier, pipeline
from word_selection.align import distance, edit_count
from word_selection.languages import LANGS
from word_selection.sources import seeds as seeds_src, wikidata, wiktionary

DECISIONS = os.path.join(ROOT, "word_selection_decisions.jsonl")
OVERRIDES = os.path.join(ROOT, "word_selection_overrides.jsonl")
DOSSIERS = os.path.join(ROOT, "word_selection_dossiers")
PORT = 8092

app = Flask(__name__)
_cache = {}


def _key(concept, overrides):
    return hashlib.sha1(json.dumps([concept, overrides], sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _run(concept, overrides):
    k = _key(concept, overrides)
    if k not in _cache:
        _cache[k] = pipeline.run(concept, overrides)
    return _cache[k]


def _saved_overrides():
    out = {}
    if os.path.exists(OVERRIDES):
        with open(OVERRIDES, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                    out[f"{r['lang']}\t{r['word']}"] = r["form"]
                except (ValueError, KeyError):
                    pass
    return out


@app.route("/")
def index():
    return send_from_directory(ROOT, "word_selector.html")


@app.route("/fonts/<path:filename>")
def fonts(filename):
    return send_from_directory(os.path.expanduser("~/.local/share/fonts"), filename)


@app.route("/api/langs")
def langs():
    return jsonify([{"code": l["code"], "basa": l["basa"], "family": l["family"]} for l in LANGS])


@app.route("/api/senses")
def senses():
    word = request.args.get("word", "").strip()
    return jsonify(wiktionary.senses_for(word) if word else [])


@app.route("/api/expand", methods=["POST"])
def expand():
    text = request.json.get("seeds", "")
    seeds = seeds_src.parse(text)
    return jsonify({"seeds": seeds, **seeds_src.expand(seeds)})


@app.route("/api/article")
def article():
    lang, title = request.args.get("lang", "en"), request.args.get("title", "")
    try:
        qid, titles = wikidata.langlinks(lang, title)
    except Exception as e:
        return jsonify({"error": f"Wikipedia unreachable: {e}"}), 502
    if not titles:
        return jsonify({"error": "no such article"}), 404
    return jsonify({"qid": qid, "title": titles.get(lang, title), "n_langs": len(titles)})


@app.route("/api/wdsearch")
def wdsearch():
    try:
        return jsonify(wikidata.search(request.args.get("q", ""), request.args.get("lang", "en")))
    except Exception as e:
        return jsonify({"error": f"Wikidata unreachable: {type(e).__name__}"}), 502


@app.route("/api/run", methods=["POST"])
def run():
    concept = request.json["concept"]
    overrides = {**_saved_overrides(), **request.json.get("overrides", {})}
    res = _run(concept, overrides)
    for c in res["clusters"]:
        c["lexiliasel"] = pipeline.lexiliasel(c)
    try:
        hint = contrasts.suggestion(concept)
    except Exception as e:      # the hint is optional; never sink the run
        hint = {"suggest": False, "reason": f"unavailable: {e}"}
    return jsonify({**res, "contrast_hint": hint})


_contrast_cache = {}


@app.route("/api/contrasts", methods=["POST"])
def find_contrasts():
    """Auto-pivot sweep: contrasts the source languages make inside this concept."""
    concept = request.json["concept"]
    overrides = {**_saved_overrides(), **request.json.get("overrides", {})}
    k = _key(concept, overrides)
    if k not in _contrast_cache:
        res = _run(concept, overrides)
        _contrast_cache[k] = contrasts.summarize(contrasts.auto_pivot(res["words"], concept))
    return jsonify({"contrasts": _contrast_cache[k]})


@app.route("/api/dossier", methods=["POST"])
def make_dossier():
    concept = request.json["concept"]
    overrides = {**_saved_overrides(), **request.json.get("overrides", {})}
    res = _run(concept, overrides)
    d = dossier.build(concept, res, int(request.json.get("cluster", 0)), request.json.get("form"))
    return jsonify({"dossier": d, "markdown": dossier.to_markdown(d)})


@app.route("/api/check", methods=["POST"])
def check():
    """Evaluate a form the user typed: collisions + closeness to a cluster's sources."""
    form = request.json["form"].strip().lower()
    concept = request.json.get("concept")
    rep = collision.check(form)
    dists = []
    if concept:
        res = _run(concept, {**_saved_overrides(), **request.json.get("overrides", {})})
        c = res["clusters"][int(request.json.get("cluster", 0))]
        for m in [m for m in c["members"] if m["forms"]]:
            n, close = edit_count(form, m["forms"][0])
            dists.append({"lang": m["lang"], "word": m["word"], "form": m["forms"][0], "edits": n,
                          "d": round(distance(form, m["forms"][0], normalized=True), 3)})
    return jsonify({"collision": rep, "distances": sorted(dists, key=lambda x: x["d"]),
                    "derivatives": dossier.derivatives(form),
                    "unattested_clusters": dossier.unattested_clusters(form)})


@app.route("/api/override", methods=["POST"])
def override():
    r = request.json
    with open(OVERRIDES, "a", encoding="utf-8") as f:
        f.write(json.dumps({"lang": r["lang"], "word": r["word"], "form": r["form"],
                            "when": datetime.datetime.now().isoformat(timespec="seconds")},
                           ensure_ascii=False) + "\n")
    return jsonify({"ok": True})


@app.route("/api/save", methods=["POST"])
def save():
    r = request.json
    when = datetime.datetime.now().isoformat(timespec="seconds")
    os.makedirs(DOSSIERS, exist_ok=True)
    md_path = os.path.join(DOSSIERS, f"{r['form']}_{when[:10]}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(r.get("markdown", ""))
    rec = {"when": when, "form": r["form"], "concept": r["concept"], "cluster": r.get("cluster", 0),
           "lexiliasel": r.get("lexiliasel", ""), "note": r.get("note", ""),
           "dossier": os.path.relpath(md_path, ROOT)}
    with open(DECISIONS, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return jsonify({"ok": True, "dossier": rec["dossier"]})


print(f"Word Selector on http://localhost:{PORT}")
app.run(port=PORT, debug=False)
