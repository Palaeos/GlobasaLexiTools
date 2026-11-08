"""Wiktionary translation tables (English Wiktionary via WiktionaryLMDB_concepts;
French/German Wiktionary via WiktionaryLMDB_fr / _de when built)."""

import os
import re
from functools import lru_cache

from ..concept_index import ConceptIndex, match_sense
from ..languages import BY_CODE, CODES, DUMP_TO_CODE, WIKT_TO_CODE

META = {"name": "wiktionary", "license": "CC BY-SA", "langs": CODES, "reliability": "high"}
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from wiktionary_constants import DIALECT_TAGS as _DT
except Exception:      # config xlsx missing: fall back to the local list only
    _DT = frozenset()
NON_STANDARD = set(_DT) | {
    "Cantonese", "Hakka", "Wu", "Min-Nan", "Min-Dong", "Min-Bei", "Teochew", "Gan", "Xiang", "Jin",
    "Taishanese", "Puxian-Min", "Sichuanese", "Hokkien", "Dungan", "Classical-Chinese", "Literary-Chinese",
    "Ottoman-Turkish", "Dari", "Tajik", "Classical-Persian", "archaic", "obsolete", "dated",
}


@lru_cache(maxsize=1)
def index():
    return ConceptIndex()


@lru_cache(maxsize=4)
def other_wiki(lang):
    path = os.path.join(ROOT, f"WiktionaryLMDB_{lang}")
    if not os.path.isdir(path):
        return None
    import sys
    sys.path.insert(0, ROOT)
    from wiktionary_db import WiktionaryDB
    return WiktionaryDB(path, readonly=True)


def nonstandard(tags):
    tl = set(tags.split("\t")) if isinstance(tags, str) else set(tags)
    return bool(tl & NON_STANDARD) or any(t.endswith("-Arabic") for t in tl)


def split_variants(word):
    """'詞典 /词典' -> ['词典', '詞典'] (simplified first); strips stray markup."""
    parts = [p.strip() for p in re.split(r"\s*/\s*", word) if p.strip()]
    return parts[::-1] if len(parts) == 2 else parts


def table(wiki, word, pos, sense):
    """{code: [(word, roman, tags)]} for one translation-table sense."""
    if wiki == "en":
        raw = index().translations(word, pos).get(sense, {})
        return {c: [tuple(t) for t in ts] for c, ts in raw.items()}
    db = other_wiki(wiki)
    if db is None:
        return {}
    raw = (db.get_translations(word, pos) or {}).get(sense, {})
    return {c: [(t.word, t.romanization, t.tags) for t in ts] for c, ts in raw.items()}


def gather(concept):
    out = []
    for wiki, word, pos, sense in concept.get("wikt_senses", []):
        prov = f"wiktionary:{wiki}:{word}/{pos}"
        if wiki in BY_CODE or wiki in DUMP_TO_CODE:
            out.append({"lang": DUMP_TO_CODE.get(wiki, wiki), "word": word, "provenance": [prov + " (headword)"],
                        "sense": sense, "tags": [], "url": f"https://{wiki}.wiktionary.org/wiki/{word}"})
        for code, ts in table(wiki, word, pos, sense).items():
            lang = WIKT_TO_CODE.get(code)
            if not lang:
                continue
            for w, rom, tags in ts:
                if nonstandard(tags):
                    continue
                for v in split_variants(w):
                    out.append({"lang": lang, "word": v, "roman": rom, "provenance": [prov],
                                "sense": sense, "tags": [t for t in tags.split("\t") if t],
                                "url": f"https://en.wiktionary.org/wiki/{v}"})
    return out


def senses_for(word):
    """Translation-table senses of an English headword, for the sense picker:
    [{wiki, word, pos, sense, n_langs, definition, examples, qids}]."""
    ix = index()
    out = []
    entries = ix.entries("en", word)
    for pos in ix.headword_pos(word):
        defs = [s for e in entries if e["pos"] == pos for s in e["senses"]]
        qmap = ix.trans_qids(word, pos)
        for sense, langs in ix.translations(word, pos).items():
            i = match_sense(sense, defs) if sense else None
            d = defs[i] if i is not None else None
            n = sum(1 for c in langs if WIKT_TO_CODE.get(c))
            out.append({"wiki": "en", "word": word, "pos": pos, "sense": sense, "n_langs": n,
                        "definition": d["g"][-1] if d else "",
                        "examples": [x[0] for x in d["ex"]] if d else [],
                        "qids": qmap.get(sense, [])})
    return sorted(out, key=lambda s: -s["n_langs"])


def _ipa_rank(ipa_tags):
    """Prefer rhotic General American for English (er/ir/ur keep their r), then phonemic /.../."""
    ipa, tags = ipa_tags
    return (0 if ("US" in tags or "General-American" in tags) else 1, 0 if ipa.startswith("/") else 1)


def lookup(lang, word):
    """Entries of a word in its own language: senses, pronunciation, etymology."""
    dump = BY_CODE[lang]["dump"] if lang in BY_CODE else lang
    es = index().entries(dump, word)
    return {
        "senses": [{"pos": e["pos"], "gloss": s["g"][-1], "tags": s["tags"], "qid": s["qid"],
                    "example": s["ex"][0] if s["ex"] else None} for e in es for s in e["senses"]],
        "roman": [r for e in es for r in e["roman"]],
        "ipa": [i[0] for i in sorted((i for e in es for i in e["ipa"]), key=_ipa_rank)],
        "etym": [x for e in es for x in e["etym"]],
    }
