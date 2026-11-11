"""Pronunciations from other Wiktionary editions, for the words of each edition's own
language: German Wiktionary for German words, French Wiktionary for French words.
English Wiktionary often has no entry for a loan as it is used in German or French
(Unix), and the spelling misleads: German writes Unix and says [ˈjuːnɪks], French
says \\y.niks\\.

Built once from the raw wiktextract dumps (kaikki.org format, Wiktionary data
CC BY-SA) into word_selection_cache/pronunciation_<edition>.json, never committed.
"""

import json
import os
import re
from functools import lru_cache

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "word_selection_cache")
EDITIONS = {"de": "de", "fr": "fr"}       # our language code -> edition (its own words)


def _path(ed):
    return os.path.join(CACHE, f"pronunciation_{ed}.json")


def build(ed, dump=None):
    """One pass over the <ed> edition's raw wiktextract dump (dump.source(ed)):
    word -> [IPA, ...] for entries in the edition's own language (lang_code == ed)."""
    from .dump import open_lines, source
    src = dump or source(ed)
    mark = f'"lang_code": "{ed}"'
    out = {}
    with open_lines(src) as f:
        for line in f:
            if mark not in line or '"ipa"' not in line:
                continue
            d = json.loads(line)
            if d.get("lang_code") != ed:
                continue
            w = d.get("word", "")
            for s in d.get("sounds", []) or []:
                ipa = (s.get("ipa") or "").strip()
                if ipa:
                    ipa = re.sub(r"^[\\/\[]+|[\\/\]]+$", "", ipa)
                    lst = out.setdefault(w, [])
                    if ipa not in lst:
                        lst.append(ipa)
    os.makedirs(CACHE, exist_ok=True)
    with open(_path(ed), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    return len(out)


@lru_cache(maxsize=4)
def _index(ed):
    try:
        with open(_path(ed), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def ipa(lang, word):
    """IPA of a word in its own language's Wiktionary edition ([] if none or not built)."""
    ed = EDITIONS.get(lang)
    if not ed:
        return []
    idx = _index(ed)
    return idx.get(word) or idx.get(word.lower()) or idx.get(word[:1].upper() + word[1:]) or []
