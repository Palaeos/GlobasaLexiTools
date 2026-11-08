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
from word_selection import collision, contrasts, dossier, methodology, pipeline
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


PROGRESS = {"stage": "", "started": 0.0, "running": False}


def _progress(stage):
    PROGRESS["stage"] = stage


def _run(concept, overrides):
    import time
    k = _key(concept, overrides)
    if k not in _cache:
        PROGRESS.update(stage="Starting", started=time.time(), running=True)
        try:
            _cache[k] = pipeline.run(concept, overrides, progress=_progress)
        finally:
            PROGRESS["running"] = False
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
        c["methodology"] = methodology.for_cluster(c)
        for p in c.get("proposals") or []:
            p["methodology"] = methodology.for_proposal(p)
    for q in res.get("team_questions", []):
        q["methodology"] = methodology.justify(["BLEND", "loose resemblances not counted"])
    try:
        hint = contrasts.suggestion(concept)
    except Exception as e:      # the hint is optional; never sink the run
        hint = {"suggest": False, "reason": f"unavailable: {e}"}
    return jsonify({**res, "contrast_hint": hint})


_contrast_cache = {}


@app.route("/api/entry")
def entry():
    """A source word's own-language Wiktionary senses, to investigate its meaning."""
    lang, word = request.args.get("lang", ""), request.args.get("word", "")
    info = wiktionary.lookup(lang, word)
    return jsonify({"lang": lang, "word": word, "senses": [{"pos": s["pos"], "gloss": s["gloss"], "tags": s["tags"]}
                                                          for s in info["senses"]][:30],
                    "etym": info["etym"][:8], "ipa": info["ipa"][:3], "roman": info["roman"][:3]})


@app.route("/api/progress")
def progress():
    """The running pipeline's current stage, for the page to show while it waits."""
    import time
    return jsonify({**PROGRESS, "elapsed": round(time.time() - PROGRESS["started"]) if PROGRESS["running"] else 0})


@app.route("/api/methodology")
def methodology_passages():
    """Every passage of the methodology, Q&A and grammar phonotactics, for the reader."""
    return jsonify(methodology.passages())


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
