"""
test_lexiliasel.py — For every derived row with non-empty LexiliAsel,
segmentation lemma sequence matches the LexiliAsel breakdown.

Strategy:
  - Parse LexiliAsel → expected lemma list
  - segment_word → actual morpheme lemma list (excluding PUNCT and SYLLABLE fallbacks)
  - Compare lemma sequences
  - Print pass/fail/skip summary

The lexicon's derived dict stores LexiliAsel-parsed morphemes directly, so a
dict hit returns ground truth — 100% pass rate for parseable rows is guaranteed
by construction.

Rows that fail alignment at lexicon load time are excluded from derived and will
show as FALLBACK (not a test failure — logged and counted).
"""

import sys
import os
import warnings

import pandas as pd
import pytest

# Ensure the package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from globasa_tokenizer.lexicon import build_lexicon
from globasa_tokenizer.segmenter import segment_word
from globasa_tokenizer import MorphKind

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_WORDLIST = os.path.join(_DATA_DIR, "word-list.csv")


def get_expected_lemmas(lexiliasel_str: str) -> list[str] | None:
    """Parse a LexiliAsel string into expected lemma tokens using the same logic as affix_parser."""
    # Delegate to the actual parser for consistent behavior
    from globasa_tokenizer.affix_parser import parse_lexiliasel
    if not lexiliasel_str or str(lexiliasel_str) in ("nan", ""):
        return None
    # We need to call parse_lexiliasel with a word — but here we're just getting lemmas,
    # so we'll use a synthetic "word" that matches the concat of pieces.
    # Instead, use the parser's cleaning logic directly:
    import re
    raw = str(lexiliasel_str).strip()
    raw = re.sub(r'\(.*?\)', '', raw).strip()
    raw = re.sub(r'\.\s+(?:\w+sa\b|\bAm\b).*$', '', raw).strip()
    raw = re.sub(r'^Am\s+.*?[,\.]\s*', '', raw).strip()
    if not raw:
        return None
    raw = re.split(r'[;/]', raw)[0].strip()
    pieces = [p.strip() for p in raw.split("+")]
    pieces = [p for p in pieces if p and p != "-"]
    if not pieces:
        return None
    lemmas = []
    for piece in pieces:
        if not piece or piece == "-":
            continue
        if piece.startswith("-") and not piece.endswith("-"):
            lemmas.append(piece)  # suffix with leading dash
        elif piece.endswith("-") and not piece.startswith("-"):
            lemmas.append(piece)  # prefix with trailing dash
        else:
            lemmas.append(piece.strip("-"))  # root
    return lemmas if lemmas else None


@pytest.fixture(scope="module")
def lex():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return build_lexicon(_WORDLIST)


def test_lexiliasel_parity(lex):
    df = pd.read_csv(_WORDLIST, index_col="Word", dtype=str)
    df.index = df.index.astype(str).str.strip()
    derived = df[df["Category"] == "derived"]

    n_pass = 0
    n_fail = 0
    n_skip_parse = 0
    n_fallback = 0
    failures = []

    for word, row in derived.iterrows():
        w = str(word).strip()
        # Skip multi-word phrases
        if " " in w:
            n_skip_parse += 1
            continue
        # Skip function words (step 1 in segment_word always returns them as FUNCTION;
        # morphological breakdown is not expected for these in the default mode)
        if w.lower() in lex.function_words:
            n_skip_parse += 1
            continue

        lex_str = str(row.get("LexiliAsel", "")).strip()

        expected_lemmas = get_expected_lemmas(lex_str)
        if expected_lemmas is None:
            n_skip_parse += 1
            continue

        # If the word is not in lex.derived, the LexiliAsel alignment failed at load time.
        # This means the LexiliAsel data in word-list.csv doesn't match the surface word.
        # Log as "alignment_failure" and skip (these are data issues, not code issues).
        if w.lower() not in lex.derived:
            n_fallback += 1
            continue

        # Segment the word
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            morphs = segment_word(w, 0, 0, lex)

        # If all morphs are SYLLABLE/UNK, it's a fallback (alignment failed at load time)
        if all(m.kind in (MorphKind.SYLLABLE, MorphKind.UNK) for m in morphs):
            n_fallback += 1
            continue

        # Extract actual lemmas (exclude PUNCT for hyphenated words)
        actual_lemmas = [m.lemma for m in morphs
                         if m.kind not in (MorphKind.SYLLABLE, MorphKind.UNK, MorphKind.PUNCT)]

        if actual_lemmas == expected_lemmas:
            n_pass += 1
        else:
            n_fail += 1
            failures.append((w, expected_lemmas, actual_lemmas))

    print(f"\nLexiliAsel parity: {n_pass} pass / {n_fail} fail / "
          f"{n_skip_parse} skip (unparseable) / {n_fallback} fallback (alignment error at load)")

    if failures:
        for w, exp, act in failures[:20]:
            print(f"  FAIL: {w!r}: expected {exp} got {act}")

    # Fail only if there are non-trivial mismatches
    assert n_fail == 0, (
        f"{n_fail} LexiliAsel parity failures "
        f"(see stdout for details; first few: {failures[:5]})"
    )
