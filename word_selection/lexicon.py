"""The Globasa lexicon: word-list.csv, LexiliAsel etymons, affixes, reverse index."""

import os
import re
import unicodedata
from functools import lru_cache

import pandas as pd

from .languages import BASA_TO_CODE, HISTORICAL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORDLIST = os.path.join(ROOT, "word-list.csv")

_LANG_GROUP = re.compile(r"([A-Z][\w\-]*(?: [A-Z][\w\-]*)?)\s*\(([^()]*)\)")
_ITEM = re.compile(r"\s*([^“”,]+?)\s*(?:“([^”]*)”)?\s*(?:,|$)")


def parse_etymons(lexiliasel):
    """'Putunhwa (茶 “ca”), Vyetnamsa (trà “ca”, chè “ce”)' ->
    [{basa, code, word, roman}] (code None for non-source languages)."""
    out = []
    for basa, inner in _LANG_GROUP.findall(lexiliasel or ""):
        code = BASA_TO_CODE.get(basa) or HISTORICAL.get(basa)
        for m in _ITEM.finditer(inner):
            w = m.group(1).strip()
            if w:
                out.append({"basa": basa, "code": code, "word": w, "roman": (m.group(2) or "").strip()})
    return out


@lru_cache(maxsize=1)
def load():
    df = pd.read_csv(WORDLIST, dtype=str).fillna("")
    df["Word"] = df["Word"].str.strip()
    return df


@lru_cache(maxsize=1)
def words():
    """{word: {cls, cat, eng, epo}} for every headword (split on ', ' variants)."""
    out = {}
    for r in load().itertuples(index=False):
        for w in re.split(r",\s*", r.Word):
            if w:
                out[w.lower()] = {"word": w, "cls": r.WordClass, "cat": r.Category,
                                  "eng": r.TranslationEng, "epo": r.TranslationEpo}
    return out


@lru_cache(maxsize=1)
def roots():
    """[{word, cls, eng, epo, etymons}] for Category == root."""
    df = load()
    out = []
    for r in df[df["Category"] == "root"].itertuples(index=False):
        out.append({"word": r.Word, "cls": r.WordClass, "eng": r.TranslationEng,
                    "epo": r.TranslationEpo, "etymons": parse_etymons(r.LexiliAsel)})
    return out


@lru_cache(maxsize=1)
def affixes():
    """(prefixes, suffixes) as bare strings, e.g. ('bur', ...), ('yen', ...)."""
    df = load()
    a = df[df["Category"] == "affix"]["Word"].tolist()
    pre = sorted({x.rstrip("-") for x in a if x.endswith("-")}, key=len, reverse=True)
    suf = sorted({x.lstrip("-") for x in a if x.startswith("-")}, key=len, reverse=True)
    return pre, suf


_MARKS = re.compile("[\u0300-\u036f\u064b-\u0652\u0670]")


def _norm(w):
    """Strip diacritics and Arabic harakat, lowercase (for etymon matching)."""
    return _MARKS.sub("", unicodedata.normalize("NFD", w)).lower()


@lru_cache(maxsize=1)
def etymon_index():
    """(lang_code, normalised source word) -> [Globasa root, ...]."""
    idx = {}
    for r in roots():
        for e in r["etymons"]:
            if e["code"]:
                idx.setdefault((e["code"], _norm(e["word"])), []).append(r["word"])
    return idx


def roots_using(lang, word):
    return etymon_index().get((lang, _norm(word)), [])


def search_glosses(terms):
    """Existing words whose Eng or Epo gloss contains any of the terms (whole word)."""
    out = []
    pats = [re.compile(r"\b" + re.escape(t.lower()) + r"\b") for t in terms if t]
    if not pats:
        return out
    for w in words().values():
        hay = (w["eng"] + " | " + w["epo"]).lower()
        if any(p.search(hay) for p in pats):
            out.append(w)
    return out
