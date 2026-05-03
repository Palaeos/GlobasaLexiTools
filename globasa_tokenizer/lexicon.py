"""
Lexicon loader for globasa_tokenizer.

Reads word-list.csv using header names (never hardcoded column indices — column order
changes over time per the project cerebrum). Strips trailing spaces from index keys.

Builds read-only Python dicts/sets/tries; drops the pandas DataFrame after init.
Stored morpheme offsets in `derived` are word-relative (start at 0); the segmenter
shifts them by the word's sentence offset at use time.
"""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

from .affix_parser import parse_lexiliasel
from .affix_trie import AffixTrie, ReversedAffixTrie
from .mined_stems import MinedStemMatcher
from .pseudo_morphemes import PseudoMorphemeMatcher
from .offsets import align, AlignmentError

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_WORDLIST_PATH = os.path.join(_DATA_DIR, "word-list.csv")

# Function-word sets copied from PosTagger.py (keep in sync)
_TENSE_PARTICLES = {"le", "xa", "nun", "am", "na", "ger", "jale", "jaxa", "u"}
_PREPOSITIONS_WC = {"p", "jm p"}
_DETERMINERS_WC = {"d", "tabl: d"}
_POSSESSIVES_WC = {"su s", "tabl: su s", "su pn"}
_PRONOUNS_WC = {"pn", "tabl: pn"}
_CONJUNCTIONS_WC = {"l", "jm l", "l jm"}
_PARTICLES_WC = {"par", "f par"}
_INTERJECTIONS_WC = {"il"}


def _wc_matches(wc_str: str, patterns: set[str]) -> bool:
    stripped = str(wc_str).strip()
    return stripped in patterns or any(stripped.startswith(p) for p in patterns)


@dataclass(frozen=True, slots=True)
class Lexicon:
    """Frozen lexicon. Attribute lookup is fast (no __dict__); safe to share across threads."""

    # Core word sets (hot path)
    roots: frozenset
    derived: dict          # word_lower → tuple of (surface, lemma, kind, start, end)
    prefixes: frozenset
    suffixes: frozenset
    function_words: frozenset
    proper_nouns: frozenset
    phrases: dict          # first_word → list of (phrase_length, full_phrase)

    # Tries for greedy affix matching
    prefix_trie: AffixTrie
    suffix_trie: ReversedAffixTrie

    # Fallback matchers
    mined_matcher: MinedStemMatcher
    pseudo_matcher: PseudoMorphemeMatcher

    # Stats (for vocabulary count reporting)
    n_roots: int
    n_prefixes: int
    n_suffixes: int
    n_function_words: int
    n_proper_nouns: int
    n_derived: int
    n_phrases: int


def build_lexicon(
    wordlist_path: str = _WORDLIST_PATH,
    pseudo_tsv: Optional[str] = None,
    mined_tsv: Optional[str] = None,
) -> Lexicon:
    """Parse word-list.csv and return a frozen Lexicon.

    wordlist_path: path to word-list.csv (default: bundled data/word-list.csv)
    pseudo_tsv:    override path for pseudo_morphemes.tsv (default: bundled)
    mined_tsv:     override path for mined_stems.tsv (default: bundled)
    """
    df = pd.read_csv(wordlist_path, index_col="Word", dtype=str)
    df.index = df.index.astype(str).str.strip()

    # ── Prefixes & suffixes ────────────────────────────────────────────────
    affix_rows = df[df["Category"] == "affix"]
    prefixes_raw: set[str] = set()
    suffixes_raw: set[str] = set()
    for word, row in affix_rows.iterrows():
        wc = str(row.get("WordClass", "")).strip()
        # Bare form stored in `word` index (already stripped)
        bare = str(word).strip().strip("-")
        if not bare:
            continue
        if wc.startswith("lfik") or wc == "lfik":
            prefixes_raw.add(bare)
        elif "xfik" in wc:
            suffixes_raw.add(bare)

    prefix_trie = AffixTrie()
    for p in prefixes_raw:
        prefix_trie.insert(p)
    suffix_trie = ReversedAffixTrie()
    for s in suffixes_raw:
        suffix_trie.insert(s)

    # ── Function words (from PosTagger word-class sets) ────────────────────
    fn_words: set[str] = set(_TENSE_PARTICLES)

    for word, row in df.iterrows():
        wc = str(row.get("WordClass", "")).strip()
        w = str(word).strip()
        if (wc in _PREPOSITIONS_WC or any(wc.startswith(p) for p in _PREPOSITIONS_WC)
                or wc in _DETERMINERS_WC
                or wc in _POSSESSIVES_WC
                or wc in _PRONOUNS_WC
                or wc in _CONJUNCTIONS_WC or any(wc.startswith(p) for p in _CONJUNCTIONS_WC)
                or wc in _PARTICLES_WC
                or wc in _INTERJECTIONS_WC):
            fn_words.add(w.lower())

    # ── Roots ─────────────────────────────────────────────────────────────
    root_rows = df[df["Category"] == "root"]
    roots_raw: set[str] = {str(w).strip().lower() for w in root_rows.index}

    # Bound roots (Category == "bound root") are also treated as roots
    bound_root_rows = df[df["Category"] == "bound root"]
    roots_raw.update(str(w).strip().lower() for w in bound_root_rows.index)

    # ── Proper nouns ───────────────────────────────────────────────────────
    proper_rows = df[df["Category"] == "proper word"]
    proper_nouns_raw: set[str] = {str(w).strip() for w in proper_rows.index}

    # ── Phrases ───────────────────────────────────────────────────────────
    phrase_rows = df[df["Category"] == "phrase"]
    phrases_map: dict[str, list] = {}
    for word, row in phrase_rows.iterrows():
        phrase = str(word).strip().lower()
        parts = phrase.split()
        if len(parts) < 2:
            continue
        first = parts[0]
        phrases_map.setdefault(first, []).append((len(parts), phrase))

    # ── Derived words (LexiliAsel ground truth) ────────────────────────────
    # Also ingests breakdowns from `Category == "proper word"` rows that have
    # a non-empty LexiliAsel (e.g. Globasa = globa + -sa, Englisa = Engli + -sa).
    # For proper-word rows the FIRST root morpheme is retagged as PROPER so the
    # rendered chip stays in the proper-noun colour band for its first piece.
    derived_rows = df[df["Category"] == "derived"]
    proper_with_breakdown = df[
        (df["Category"] == "proper word") & df["LexiliAsel"].notna()
    ]
    derived_map: dict[str, tuple] = {}
    n_align_ok = 0
    n_align_fail = 0

    def _ingest(word_str: str, lex_str: str, is_proper: bool):
        nonlocal n_align_ok, n_align_fail
        w_local = word_str.strip()
        w_lower = w_local.lower()
        lex_str = lex_str.strip()
        if not lex_str or lex_str in ("nan", ""):
            return
        try:
            with warnings.catch_warnings(record=True):
                warnings.simplefilter("always")
                raw_morphs = parse_lexiliasel(lex_str, w_local)
            if raw_morphs is None:
                n_align_fail += 1
                return
            aligned = align(w_local, raw_morphs)
            if is_proper and aligned:
                # Promote the first ROOT-kinded morpheme to PROPER.
                first = aligned[0]
                surface, lemma, kind, start, end = first
                if kind == "ROOT":
                    aligned[0] = (surface, lemma, "PROPER", start, end)
            derived_map[w_lower] = tuple(aligned)
            n_align_ok += 1
        except AlignmentError:
            n_align_fail += 1
        except Exception:
            n_align_fail += 1

    for word, row in derived_rows.iterrows():
        _ingest(str(word), str(row.get("LexiliAsel", "")), is_proper=False)
    for word, row in proper_with_breakdown.iterrows():
        _ingest(str(word), str(row.get("LexiliAsel", "")), is_proper=True)

    # ── Mined stems & pseudo-morpheme matchers ─────────────────────────────
    mined_matcher = MinedStemMatcher(mined_tsv) if mined_tsv else MinedStemMatcher()
    pseudo_matcher = PseudoMorphemeMatcher(pseudo_tsv) if pseudo_tsv else PseudoMorphemeMatcher()

    return Lexicon(
        roots=frozenset(roots_raw),
        derived=derived_map,
        prefixes=frozenset(prefixes_raw),
        suffixes=frozenset(suffixes_raw),
        function_words=frozenset(fn_words),
        proper_nouns=frozenset(proper_nouns_raw),
        phrases=phrases_map,
        prefix_trie=prefix_trie,
        suffix_trie=suffix_trie,
        mined_matcher=mined_matcher,
        pseudo_matcher=pseudo_matcher,
        n_roots=len(roots_raw),
        n_prefixes=len(prefixes_raw),
        n_suffixes=len(suffixes_raw),
        n_function_words=len(fn_words),
        n_proper_nouns=len(proper_nouns_raw),
        n_derived=n_align_ok,
        n_phrases=len(phrases_map),
    )


# Module-level singleton (lazy — built on first access)
_GLOBAL_LEXICON: Optional[Lexicon] = None


def get_lexicon() -> Lexicon:
    """Return the module-level Lexicon, building it on first call."""
    global _GLOBAL_LEXICON
    if _GLOBAL_LEXICON is None:
        _GLOBAL_LEXICON = build_lexicon()
    return _GLOBAL_LEXICON


def refresh_lexicon(
    wordlist_path: str = _WORDLIST_PATH,
    pseudo_tsv: Optional[str] = None,
    mined_tsv: Optional[str] = None,
) -> Lexicon:
    """Rebuild and replace the global lexicon. Useful after updating data/word-list.csv."""
    global _GLOBAL_LEXICON
    _GLOBAL_LEXICON = build_lexicon(wordlist_path, pseudo_tsv, mined_tsv)
    return _GLOBAL_LEXICON
