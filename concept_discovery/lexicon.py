"""Globasa word-list indexes for the concept-discovery scripts (functions only, safe
to import).

  load()           -> Lexicon: which Globasa words were selected from a source form
                      (LexiliAsel), list a Chinese translation, or an English gloss item
  keys(term, lang) -> lookup keys of a form (traditional Han spellings added)
  Lexicon.covering(lang, term) / .glossed(eng) -> {Globasa word: how}

LexiliAsel items look like  Niponsa (旨味 “umami”), Hindi (कर्म “karm”),
Arabisa (أَمِيرُ البَحْر “amiru albahr”, أَدْمِيرَال “admiral”): a source language
named in Globasa, then one or more forms, each with an optional romanization.
"""

import os
import re
import sys
import unicodedata
from collections import defaultdict

import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO not in sys.path:
    sys.path.insert(0, REPO)
from apertium_common import expand_gloss_tokens
from word_selection import sinosphere

WORD_LIST = os.path.join(REPO, "word-list.csv")

# LexiliAsel language names -> Wiktionary codes (the names that occur in word-list.csv)
LEXILIASEL_CODES = {
    "Englisa": "en", "Espanisa": "es", "Fransesa": "fr", "Turkisa": "tr", "Doycisa": "de",
    "Parsisa": "fa", "Indonesisa": "id", "Rusisa": "ru", "Niponsa": "ja", "Hindi": "hi",
    "Arabisa": "ar", "Koreasa": "ko", "Pilipinasa": "tl", "Swahilisa": "sw", "Putunhwa": "zh",
    "Kantonsa": "zh", "Gwandonsa": "zh", "Vyetnamsa": "vi", "Telugusa": "te", "Telugu": "te", "Italisa": "it",
    "Portugalsa": "pt", "Elinisa": "el", "Tamilsa": "ta", "Ivrisa": "he", "Karnatakasa": "kn",
    "Nederisa": "nl", "Banglasa": "bn", "Malaysisa": "ms", "Keralasa": "ml", "Urdu": "ur",
    "Panjabisa": "pa", "Gujaratisa": "gu", "Maharaxtrasa": "mr", "Taysa": "th",
}
# Wiktionary language codes of the Sinosphere -> the code LexiliAsel forms are filed under
SINOSPHERE = {"zh": "zh", "cmn": "zh", "yue": "zh", "ja": "ja", "ko": "ko", "vi": "vi"}

ITEM_RE = re.compile(r"(\w+)\s*\(([^()]*)\)")
ROMAN_RE = re.compile(r"“[^”]*”")


def normal(form):
    return unicodedata.normalize("NFC", form.strip())


def keys(term, lang="zh"):
    """Lookup keys of a form: itself plus its traditional Han spellings, so that
    Wiktionary 洗腦 meets the word list's 洗脑 (sinosphere.normalise)."""
    term = normal(term or "")
    if not term:
        return set()
    out = {term}
    if sinosphere.is_han_word(term):
        out.update(sinosphere.normalise(term, "ja" if lang == "ja" else "cmn"))
    return out


class Lexicon:
    def __init__(self):
        self.source = defaultdict(set)   # (code, form) -> Globasa words; Han forms also under ("han", form)
        self.zho = defaultdict(set)      # Chinese translation (with traditional keys) -> words
        self.gloss = defaultdict(set)    # lowercased English gloss item -> words

    def covering(self, lang, term):
        """{Globasa word: how} for a source form: LexiliAsel (same language, or any
        Sinosphere language for a Han spelling), then the Zho column. A single Han
        character matches only within its own language (2026-11-21: Japanese 和
        'harmony, Japan' had matched Mandarin 和 'and' -> ji; Vietnamese 華 the name
        form 華 of Hana)."""
        code = SINOSPHERE.get(lang, lang)
        out = {}
        for k in keys(term, code):
            for glb in self.source.get((code, k), ()):
                out.setdefault(glb, "source")
            if sinosphere.is_han_word(k) and (len(k) > 1 or code == "zh"):
                if len(k) > 1:
                    for glb in self.source.get(("han", k), ()):
                        out.setdefault(glb, "source")
                for glb in self.zho.get(k, ()):
                    out.setdefault(glb, "zho")
        return out

    def glossed(self, eng):
        return {glb: "gloss" for glb in self.gloss.get((eng or "").lower(), ())}


def load(path=None):
    df = pd.read_csv(path or WORD_LIST, usecols=["Word", "TranslationEng", "TranslationZho", "LexiliAsel"],
                     dtype=str, keep_default_na=False)
    lex = Lexicon()
    for row in df.itertuples(index=False):
        glb = row.Word
        for name, content in ITEM_RE.findall(row.LexiliAsel):
            code = LEXILIASEL_CODES.get(name)
            if not code:
                continue
            for form in ROMAN_RE.sub("", content).split(","):
                for k in keys(form, code):
                    lex.source[(code, k)].add(glb)
                    if code in ("zh", "ja", "ko", "vi") and sinosphere.is_han_word(k):
                        lex.source[("han", k)].add(glb)
        for item in re.split(r"[;,，、]\s*", row.TranslationZho):
            item = re.sub(r"^[a-z. ]+:\s*", "", item).strip()
            for k in keys(item):
                lex.zho[k].add(glb)
        for segment in row.TranslationEng.split("; "):
            for token in expand_gloss_tokens(segment):
                lex.gloss[token.lower()].add(glb)
    return lex
