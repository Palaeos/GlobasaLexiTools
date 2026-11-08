"""Seed words typed by the user ('fa:منت, tr:minnet, ja:義理').

gather(): the seeds themselves are sources.
expand(): proposes Wiktionary translation-table senses for the concept --
  (1) tables that already list a seed word (strongest: a Wiktionary editor put it there),
  (2) English headwords taken from the seed's own glosses,
and the QIDs carried by the seeds' senses. The user picks which to add.
"""

import re

from ..languages import BY_CODE, CODES
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
