"""Plural -> singular for nouns of the source languages, from the noun entries'
inflected forms in the raw English Wiktionary dump (forms tagged "plural"):
Wikispecies often gives a genus or family its vernacular name in the plural
(German Birken, Finnish koivut), and a root is cut from the singular.
Built once into word_selection_cache/plurals.json (Wiktionary data, CC BY-SA)."""

import json
import os
from functools import lru_cache

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "word_selection_cache", "plurals.json")


def build(dump=None, out=OUT):
    from .dump import open_lines, source
    from .languages import LANGS
    langs = {l["dump"]: l["code"] for l in LANGS}
    marks = [f'"lang_code": "{d}"' for d in langs]
    index = {}
    with open_lines(dump or source("en")) as f:
        for line in f:
            if '"pos": "noun"' not in line or '"plural"' not in line or not any(m in line for m in marks):
                continue
            d = json.loads(line)
            code = langs.get(d.get("lang_code"))
            if not code or d.get("pos") != "noun":
                continue
            lemma = d.get("word", "")
            for fm in d.get("forms", []) or []:
                tags = set(fm.get("tags") or [])
                form = (fm.get("form") or "").strip()
                if "plural" in tags and form and form != lemma and not tags & {"genitive", "dative", "accusative",
                                                                             "instrumental", "prepositional", "locative"}:
                    lst = index.setdefault(f"{code}\t{form}", [])
                    if lemma not in lst:
                        lst.append(lemma)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False)
    return len(index)


@lru_cache(maxsize=1)
def _index():
    try:
        with open(OUT, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def singular(lang, word):
    """[singular, ...] if `word` is a plural noun form in `lang`, else []."""
    idx = _index()
    return idx.get(f"{lang}\t{word}") or idx.get(f"{lang}\t{word.lower()}") or []
