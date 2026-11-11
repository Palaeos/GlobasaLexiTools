"""Seed words typed by the user ('fa:منت, tr:minnet, ja:義理').

gather(): the seeds themselves are sources.
expand(): proposes Wiktionary translation-table senses for the concept --
  (1) tables that already list a seed word (strongest: a Wiktionary editor put it there),
  (2) English headwords taken from the seed's own glosses,
and the QIDs carried by the seeds' senses. The user picks which to add.
tuple_senses(): each seed's senses in its OWN Wiktionary edition (de:Topf in
  de.wiktionary), scored by how many of the other seeds that sense's table lists:
  a seed tuple (en:pot, de:Topf, fr:cruche) pins one meaning across editions.
"""

import os
import re

from ..languages import BY_CODE, CODES, WIKT_TO_CODE
from . import wiktionary

META = {"name": "seeds", "license": "user input", "langs": CODES, "reliability": "high"}


def parse(text):
    """'fa:منت, tr:minnet ja:義理' -> [[lang, word]]"""
    out = []
    for m in re.finditer(r"([a-z]{2,3})\s*:\s*([^,;\n]+?)(?=\s+[a-z]{2,3}\s*:|[,;\n]|$)", text):
        lang, word = m.group(1), m.group(2).strip()
        if lang == "zh":
            lang = "cmn"
        out.append([lang, word])
    return out


def gather(concept):
    return [{"lang": l, "word": w, "provenance": ["seed"], "tags": []}
            for l, w in concept.get("seeds", []) if l in BY_CODE]


def _gloss_headwords(gloss):
    g = re.sub(r"\([^)]*\)", "", gloss)
    out = []
    for part in re.split(r"[,;]", g):
        p = part.strip().lower()
        p = re.sub(r"^(to|a|an|the)\s+", "", p)
        if p and len(p.split()) <= 3:
            out.append(p)
    return out


def expand(seeds):
    """-> {senses: [sense dicts as wiktionary.senses_for, plus 'via'], qids: [[qid, via]]}"""
    ix = wiktionary.index()
    found, qids = {}, {}
    for lang, word in seeds:
        if lang not in BY_CODE:
            continue
        for code in BY_CODE[lang]["wikt"]:
            for en_word, pos, sense in ix.tables_listing(code, word):
                k = (en_word, pos, sense)
                found.setdefault(k, set()).add(f"{lang}:{word} is in this table")
        for s in wiktionary.lookup(lang, word)["senses"]:
            for q in s["qid"]:
                qids.setdefault(q, set()).add(f"{lang}:{word} — {s['gloss'][:60]}")
            for hw in _gloss_headwords(s["gloss"]):
                for cand in wiktionary.senses_for(hw)[:6]:
                    k = (cand["word"], cand["pos"], cand["sense"])
                    found.setdefault(k, set()).add(f"gloss of {lang}:{word} → '{hw}'")
    senses = []
    for (w, pos, sense), via in found.items():
        info = next((s for s in wiktionary.senses_for(w) if s["pos"] == pos and s["sense"] == sense), None)
        if info:
            senses.append({**info, "via": sorted(via)})
    # tables listing a seed come first, then by how many seeds point at them
    senses.sort(key=lambda s: (-sum("is in this table" in v for v in s["via"]), -len(s["via"]), -s["n_langs"]))
    return {"senses": senses[:40], "qids": [[q, sorted(v)] for q, v in qids.items()]}


def edition_of(lang):
    """Wiktionary edition written in a source language (cmn -> zh), or None."""
    from ..contrasts import EDITIONS
    if lang == "en":
        return "en"
    return next((e for e, l in EDITIONS.items() if l == lang), None)


def editions():
    """{built: [...], not_built: [...]}: editions a seed's senses can come from."""
    from ..contrasts import EDITIONS, available
    from ..concept_index import DIR
    built = (["en"] if os.path.isdir(DIR) else []) + available()
    return {"built": built, "not_built": [e for e in ["en", *EDITIONS] if e not in built]}


def _norm(w):
    from ..contrasts import _variants
    return {v.lower() for v in _variants(w)}


def _sense_trans(s):
    """{lang: {normalised words}} of a sense's table."""
    if "trans" in s:
        raw = s["trans"]
    else:
        raw = {}
        for code, ts in wiktionary.table(s["wiki"], s["word"], s["pos"], s["sense"]).items():
            lang = WIKT_TO_CODE.get(code)
            if lang:
                raw.setdefault(lang, []).extend(w for w, _, _ in ts)
    return {l: {n for w in ws for n in _norm(w)} for l, ws in raw.items()}


def tuple_senses(seeds):
    """For each seed: its senses in its own edition, each with `listed` (the other
    seeds its table lists) and `score`; `pick` is the index of the one best-scoring
    sense, None when the best is tied or lists no other seed (the user chooses).
    -> [{seed, edition, built, senses, pick, note}]"""
    out = []
    for lang, word in seeds:
        ed = edition_of(lang)
        db_ok = ed == "en" or (ed is not None and wiktionary.other_wiki(ed) is not None)
        rec = {"seed": [lang, word], "edition": ed, "built": db_ok, "senses": [], "pick": None, "note": ""}
        if not db_ok:
            rec["note"] = (f"no {ed or lang}.wiktionary edition built; seed used as a source word only"
                           + (f" (build it with: JSONL parser non-English.py {ed})" if ed else ""))
            out.append(rec)
            continue
        others = [(l, w) for l, w in seeds if (l, w) != (lang, word)]
        for s in wiktionary.senses_in(ed, word)[:30]:
            tr = _sense_trans(s)
            listed = [f"{l}:{w}" for l, w in others if _norm(w) & tr.get(l, set())]
            rec["senses"].append({**{k: v for k, v in s.items() if k != "trans"},
                                  "listed": listed, "score": len(listed), "n_others": len(others)})
        if not rec["senses"]:
            rec["note"] = f"{word} has no translation table in {ed}.wiktionary"
        scores = sorted((s["score"] for s in rec["senses"]), reverse=True)
        if scores and scores[0] > 0 and (len(scores) == 1 or scores[1] < scores[0]):
            rec["pick"] = next(i for i, s in enumerate(rec["senses"]) if s["score"] == scores[0])
        elif scores and scores[0] > 0:
            rec["note"] = "several senses list the same number of other seeds: choose"
        out.append(rec)
    return out
