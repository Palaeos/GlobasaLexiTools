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


@lru_cache(maxsize=8)      # en is separate; de fr ja zh built, es ru ko may follow
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


def _gloss_tokens(text):
    return {t for t in re.findall(r"\w+", text.lower()) if len(t) > 3}


def _edition_definition(label, defs):
    """The edition's definition for a translation-table label: the label itself when
    the edition's tables are keyed by definition (de.wiktionary: 'kleines Gefäß'), else
    the definition sharing most words with it (fr: 'récipient à anse' ~ 'Vase de
    terre ou de grès, à anse, ...'); "" when none does."""
    if not label:
        return ""
    for d in defs:
        if label in d.glosses:
            return label
    lt = _gloss_tokens(label)
    best = max(defs, key=lambda d: len(lt & _gloss_tokens(" ".join(d.glosses))), default=None)
    if best is not None and lt & _gloss_tokens(" ".join(best.glosses)):
        return best.glosses[-1]
    return ""


def edition_words(wiki, word):
    """Spellings to try in an edition: as typed, then capitalised (German nouns:
    de:topf -> Topf), then lower-case."""
    return list(dict.fromkeys([word, word[:1].upper() + word[1:], word.lower()]))


def senses_in(wiki, word):
    """senses_for() for any edition: the translation-table senses of `word` in
    WiktionaryLMDB_<wiki>, in the same shape; [] when the edition is not built."""
    if wiki == "en":
        return senses_for(word)
    db = other_wiki(wiki)
    if db is None:
        return []
    from ..contrasts import foreign_senses
    out = []
    for w in edition_words(wiki, word):
        for s in foreign_senses(wiki, w):
            defs = db.get_senses(w, s["pos"]) or []
            d = _edition_definition(s["sense"], defs)
            out.append({"wiki": wiki, "word": w, "pos": s["pos"], "sense": s["sense"],
                        "n_langs": len(s["trans"]), "definition": "" if d == s["sense"] else d,
                        "examples": [], "qids": [], "trans": {k: sorted(v) for k, v in s["trans"].items()}})
        if out:
            break
    return sorted(out, key=lambda s: -s["n_langs"])


def english_view(concept):
    """The concept as English senses, for checks that read English glosses (sense_fit).
    A sense from another edition (de: Topf 'kleines Gefäß') is bridged to the English
    tables that list that word AND are named by an English translation in its own
    table (pot): those English senses stand for it. Unchanged when every sense is
    English; {"bridged": [...], "unbridged": [...]} say what happened."""
    rows = [list(r) for r in concept.get("wikt_senses", [])]
    if all(r[0] == "en" for r in rows):
        return concept
    ix = index()
    en_rows, bridged, unbridged = [r for r in rows if r[0] == "en"], [], []
    for wiki, word, pos, sense in [r for r in rows if r[0] != "en"]:
        en_words = {w for w, _, _ in table(wiki, word, pos, sense).get("en", [])
                    for w in split_variants(w)}
        lang = DUMP_TO_CODE.get(wiki, wiki)
        got = []      # may already be among the concept's English senses: still a bridge
        for code in (BY_CODE[lang]["wikt"] if lang in BY_CODE else [wiki]):
            for en_word, en_pos, en_sense in ix.tables_listing(code, word):
                if en_word in en_words and ["en", en_word, en_pos, en_sense] not in got:
                    got.append(["en", en_word, en_pos, en_sense])
        (bridged if got else unbridged).append(f"{wiki}:{word} '{sense}'")
        en_rows += [r for r in got if r not in en_rows]
    return dict(concept, wikt_senses=en_rows, bridged=bridged, unbridged=unbridged)


def _ipa_rank(ipa_tags):
    """Prefer rhotic General American for English (er/ir/ur keep their r), then phonemic /.../."""
    ipa, tags = ipa_tags
    return (0 if ("US" in tags or "General-American" in tags) else 1, 0 if ipa.startswith("/") else 1)


def _roman_rank(lang, r):
    """Persian entries list the Classical/Dari romanization first (kitāb, afsāna,
    pilk, du) and the Iranian one after (ketâb, afsâne, pelk, do); the Word
    Selector follows the Iranian pronunciation. Dari/Classical marks (ā ī ū ē ō ô:
    mômiyâ, sôsan) rank last; then â; then e/o, the Iranian reflexes of short i/u."""
    if lang != "fa":
        return 0
    if re.search("[āīūēōô]", r):
        return 3
    if "â" in r:
        return 0
    return 1 if re.search("[eo]", r) else 2


_HARAKAT = re.compile("[\u064b-\u0652\u0670\u0640]")


@lru_cache(maxsize=50000)
def table_romans(lang, word):
    """Romanizations English translation tables give this word (their tr=), most
    often given first: 357 of the 726 LexiliAsel Persian etymons with no entry
    romanization (most have no entry at all) are listed in some table with one."""
    code = DUMP_TO_CODE.get(lang, lang)
    if code not in BY_CODE:
        return []
    ix = index()
    bare = _HARAKAT.sub("", word).strip()
    votes = {}
    for wk in BY_CODE[code]["wikt"]:
        for en, pos, sense in ix.tables_listing(wk, word)[:30]:
            items = ix.translations(en, pos).get(sense, {})
            for item in (items.get(wk, []) if isinstance(items, dict) else []):
                if item[1] and _HARAKAT.sub("", item[0]).strip() == bare:
                    votes[item[1]] = votes.get(item[1], 0) + 1
    ranked = sorted(votes, key=lambda r: (_roman_rank(code, r), -votes[r]))
    return ranked


def lookup(lang, word):
    """Entries of a word in its own language: senses, pronunciation, etymology.
    roman: the entries' romanizations (Persian: Iranian first), else those the
    translation tables give the word (roman_from says which)."""
    dump = BY_CODE[lang]["dump"] if lang in BY_CODE else lang
    code = DUMP_TO_CODE.get(dump, lang)
    es = index().entries(dump, word)
    roman = sorted(dict.fromkeys(r for e in es for r in e["roman"]), key=lambda r: _roman_rank(code, r))
    roman_from = "entry" if roman else ""
    if not roman and code in ("ar", "fa", "hi", "te", "ru", "ja", "ko", "cmn"):
        roman = table_romans(code, word)
        roman_from = "table" if roman else ""
    return {
        "senses": [{"pos": e["pos"], "gloss": s["g"][-1], "tags": s["tags"], "qid": s["qid"],
                    "example": s["ex"][0] if s["ex"] else None} for e in es for s in e["senses"]],
        "roman": roman,
        "roman_from": roman_from,
        "ipa": [i[0] for i in sorted((i for e in es for i in e["ipa"]), key=_ipa_rank)],
        "etym": [x for e in es for x in e["etym"]],
    }
