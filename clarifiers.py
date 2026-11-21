"""Guessed clarifiers for the Menalari extension's translations, word-list style: martinet (_oiseau_).

A translation needs one only when it is shared: the same word in the same language column
translates two or more Globasa words (in menalariExtension.tsv or in the word list's own
translation columns), so a reader going from that language back to Globasa could not tell which
is meant (user decision 2026-11-21; not Wiktionary's own ambiguity, which only 17 languages have).

What a clarifier says, in order (the first one that tells this Globasa word apart from all the
others sharing the translation, and that can be written in the column's language):
  1. the word list's own English clarifier on that gloss    swallow (_bird_)       -> bird
  2. the Wiktionary sense label of a noun, when short         [bird], [plant]
  3. the Globasa word's tags listed in clarifier_tags.tsv    basa, musika (kinds and fields)
Labels come before tags: a tag names a category (noce, night, is tagged din, day), a label the
sense itself.
How it is written in the column's language:
  - a tag: its own word-list translation in that language (Spa, Epo, Fra, Deu, Rus, Zho, Hin, Ara);
  - an English concept: the Globasa word glossed exactly so in the word list, then its
    translation in that language;
  - otherwise (fallback: Wiktionary): the first translation of the English word in its first
    translation table listing the language. Dialect columns use the parent language's word
    (fallback: parent language).
Every clarifier is reported with how it was found (report_rows), fallbacks labelled.

    clar = Clarifiers(wordlist_rows, en_db)
    shared = clar.shared_index(items)            # items: (lang, word, glb)
    text, how = clar.choose(lang, word, glb, sense, others)
"""
import csv
import os
import re
from collections import defaultdict
from functools import lru_cache

from wiktionary_constants import DIALECT_LANGS, _resolve_lang, build_annotation_map

# Extension language code -> the word list's own translation column.
WORDLIST_COLUMNS = {"es": "TranslationSpa", "eo": "TranslationEpo", "fr": "TranslationFra",
                    "de": "TranslationDeu", "ru": "TranslationRus", "cmn": "TranslationZho",
                    "hi": "TranslationHin", "ar": "TranslationAra"}
MAX_LABEL_WORDS = 3
# The tags allowed as clarifiers: a curated list (user, 2026-11-21: stricter), each a KIND the
# word is one of (basa language, labas clothing, tul tool) or a FIELD it belongs to (musika,
# jismulogi anatomy, lega law). Not listed, never used: tags for where things are found (kokikamer
# kitchen, eskrimesa desk), loose associations (din day, watu time, dom place, harka motion),
# sensitive ones (sekso, fahexxey), the empty xey/name, and the list tags (bage 3 de lista 500).
CLARIFIER_TAGS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clarifier_tags.tsv")


def load_clarifier_tags(path=CLARIFIER_TAGS):
    """{tag: 'kind' | 'field'} from clarifier_tags.tsv (Tag, English, Use)."""
    if not os.path.exists(path):
        print(f"  {os.path.basename(path)} missing: no tags used as clarifiers "
              f"(fallback: labels and gloss clarifiers only)")
        return {}
    with open(path, encoding="utf-8", newline="") as f:
        return {r["Tag"].strip(): r["Use"].strip() for r in csv.DictReader(f, delimiter="\t")
                if r.get("Tag") and r.get("Use", "").strip() in ("kind", "field")}
ITEM_SPLIT = re.compile(r"[,;،؛、，；]\s*(?![^()]*\))")  # Latin, Arabic and CJK commas
POS_PREFIX = re.compile(r"^\s*[^:,;()_]{1,25}:\s*")    # "n: ", "сущ: ", "prep frazparto: "
ANNOTATED = re.compile(r"\(_[^)]*_\)")
NOTES = re.compile(r"\s*\(_[^)]*_\)|\s*\([^)]*\)|_[^_]*_")
CONCEPT_POS = ("noun", "adj", "verb")
PARENS = re.compile(r"\s*\([^)]*\)")
# Wiktionary markup, footnotes, numbering; and ',' ';' which build_bidix.py splits cells on
NOT_A_WORD = re.compile(r"[\[\]^(){}<>_\d,;،؛、，；]|please verify")


def clean(text):
    """A clarifier as a plain word or short phrase, or None (markup, footnotes, long phrases)."""
    text = PARENS.sub("", text or "").strip(" ,;:")
    if (not text or NOT_A_WORD.search(text) or len(text.split()) > MAX_LABEL_WORDS
            or text.startswith("-") or text.endswith("-")):  # affixes say nothing
        return None
    return text


def wordlist_items(cell):
    """The words of a word-list translation cell, without PoS prefixes or (_notes_)."""
    words = []
    for group in (cell or "").split("; "):
        group = POS_PREFIX.sub("", group)
        for item in ITEM_SPLIT.split(group):
            item = POS_PREFIX.sub("", NOTES.sub("", item)).strip()
            if item:
                words.append(item)
    return words


def parent(lang):
    return DIALECT_LANGS[lang][0] if lang in DIALECT_LANGS else lang


class Clarifiers:
    def __init__(self, wordlist_rows, en_db, extension_words=None):
        """wordlist_rows: word-list.csv rows (dicts); en_db: the English WiktionaryDB;
        extension_words: {(glb, lang): [(word, pos)]} -- the extension's own translations of
        each Globasa word (from vetted senses), the best way to write a tag or pivot word; only
        its noun translations are used (medis, medicine, is also the verb 'treat')."""
        self.db = en_db
        self.ext = extension_words or {}
        self.allowed_tags = load_clarifier_tags()
        self.rows = {r["Word"]: r for r in wordlist_rows}
        self.tags = {w: [t.strip() for t in (r.get("Tags") or "").split(",") if t.strip()]
                     for w, r in self.rows.items()}
        # English gloss -> Globasa words glossed exactly so, for writing a concept in a language.
        # Only plain glosses: "plant (_factory_)" names one sense of "plant", not the concept.
        self.glossed = defaultdict(list)
        for w, r in self.rows.items():
            for group in (r.get("TranslationEng") or "").split("; "):
                for item in ITEM_SPLIT.split(POS_PREFIX.sub("", group)):
                    if item.strip() and not ANNOTATED.search(item):
                        plain = POS_PREFIX.sub("", NOTES.sub("", item)).strip().lower()
                        if plain:
                            self.glossed[plain].append(w)

    # -- sharing ---------------------------------------------------------------------------
    def shared_index(self, items):
        """{(lang, word): {glb}} from the extension's (lang, word, glb) items plus the word
        list's own columns."""
        index = defaultdict(set)
        for lang, word, glb in items:
            index[(lang, word)].add(glb)
        for lang, column in WORDLIST_COLUMNS.items():
            for w, r in self.rows.items():
                for item in wordlist_items(r.get(column)):
                    index[(lang, item)].add(w)
        return index

    # -- concepts ----------------------------------------------------------------------------
    def concepts(self, glb, sense):
        """[(kind, value)] most telling first, for one Globasa word and vetted sense."""
        found = []
        eng = (self.rows.get(glb) or {}).get("TranslationEng", "")
        note = build_annotation_map(eng).get(sense.get("lookup_word", ""), "") if sense.get("source") == "en" else ""
        if note:
            found.append(("gloss", note))
        label = re.sub(r"\([^)]*\)", "", sense.get("sense", "")).strip(" ;,")
        # A noun's label names what it is ([bird], [plant]); a verb's or adjective's paraphrases
        # it ([move], [action]) and is no clarifier.
        if (label and len(label.split()) <= MAX_LABEL_WORDS and ";" not in label
                and sense.get("pos") in ("noun", "name")):
            found.append(("label", label))
        found += [("tag", t) for t in self.tags.get(glb, ()) if t in self.allowed_tags]
        return found

    # -- writing a concept in a language ---------------------------------------------------------
    @lru_cache(maxsize=None)
    def _wiktionary(self, english, lang, note=""):
        """The concept's main sense = its translation table listing the most languages (a first
        table can be a slang or rare sense: 'nut' [slang: testicle]). With a word-list note
        ("medicine (_science, practice_)") only a table whose label shares a word with it counts,
        or nothing is written (the main table of 'medicine' is the drug)."""
        hint = {w for w in re.findall(r"[a-z]{4,}", note.lower())}
        for pos in CONCEPT_POS:
            entry = self.db.get_translations(english, pos) if self.db else None
            tables = sorted((entry or {}).items(), key=lambda kv: -len(kv[1]))
            if hint:
                tables = [(t, tr) for t, tr in tables if hint & set(re.findall(r"[a-z]{4,}", t.lower()))]
            for table, translations in tables:
                resolved, found = _resolve_lang(lang, translations)
                words = sorted(w for w in (clean(t.word) for t in resolved) if w) if found else []
                if words:
                    return words[0], f"(fallback: Wiktionary, main table of '{english}' [{table}])"
        return None

    def _own(self, glb, column, lang):
        """A Globasa word written in a language: its word-list translation, else the extension's
        translation from its vetted senses. (text, how) or None."""
        if column:
            items = [w for w in map(clean, wordlist_items((self.rows.get(glb) or {}).get(column))) if w]
            if items:
                return items[0], "word list"
        # Kinds, fields and concepts are nouns: a verb reading would mislead (medis -> "to treat").
        items = [w for w in (clean(word) for word, pos in self.ext.get((glb, lang), ())
                             if pos in ("noun", "name")) if w]
        return (items[0], "its vetted senses") if items else None

    @lru_cache(maxsize=None)
    def render(self, kind, value, lang):
        """(text in the language, how) or None."""
        base = parent(lang)
        dialect = " (fallback: parent language)" if base != lang else ""
        column = WORDLIST_COLUMNS.get(base)
        if kind == "tag":
            row = self.rows.get(value) or self.rows.get(value.lower())
            if row is None:
                return None
            own = self._own(value if value in self.rows else value.lower(), column, lang)
            if own:
                return own[0], f"tag {value} ({own[1]})" + dialect
            english = wordlist_items(row.get("TranslationEng"))
            first = ITEM_SPLIT.split(POS_PREFIX.sub("", (row.get("TranslationEng") or "").split("; ")[0]))[0]
            note = (ANNOTATED.search(first) or [""])[0]  # "(_science, practice_)"
            got = self._wiktionary(english[0], base, note) if english else None
            return (got[0], f"tag {value} = '{english[0]}', {got[1]}" + dialect) if got else None
        # an English concept (gloss clarifier or sense label): through Globasa only when exactly
        # one Globasa word has that plain gloss (several = the English word is ambiguous)
        pivots = self.glossed.get(value.lower(), [])
        for glb in pivots if len(pivots) == 1 else ():
            own = self._own(glb, column, lang)
            if own:
                return own[0], f"{kind} '{value}' = Globasa {glb} ({own[1]})" + dialect
        got = self._wiktionary(value, base)
        return (got[0], f"{kind} '{value}', {got[1]}" + dialect) if got else None

    def candidates(self, glb, sense, lang):
        """[(text, how)] for one occurrence, most telling first, each written once."""
        seen, out = set(), []
        for kind, value in self.concepts(glb, sense):
            got = self.render(kind, value, lang)
            if got and got[0].lower() not in seen:
                seen.add(got[0].lower())
                out.append(got)
        return out

    def choose(self, lang, word, glb, sense, others, own=()):
        """The clarifier for `word` (in `lang`) under `glb`, telling it apart from `others`
        ([(glb2, sense2)], the other Globasa words sharing it; sense2 may be None for a word-list
        translation). `own`: the word's other translations in this language, which tell a
        reader nothing as a clarifier. Returns (text, how) or (None, why)."""
        own = {o.lower() for o in own} | {word.lower()}
        mine = self.candidates(glb, sense, lang)
        if not mine:
            return None, "no clarifier can be written in this language"
        theirs = set()
        for other_glb, other_sense in others:
            for text, _ in self.candidates(other_glb, other_sense or {"source": "", "sense": ""}, lang):
                theirs.add(text.lower())
        for text, how in mine:
            if text.lower() not in theirs and text.lower() not in own:
                return text, how
        return None, "every clarifier also fits " + ", ".join(sorted({g for g, _ in others}))
