"""
test_grammar_constraints.py — Xwexi-derived structural rules.

Tests:
  - Hyphenated compounds tokenize as single words (Mexiko-Usali, moge-yamne)
  - Em-dash adjacent to whitespace is punctuation
  - -cu optionality: both buka-ne and buka-cu-ne segment cleanly
  - Stacking limits enforced on greedy path (multi-suffix novel word → cascade fallback)
"""

import sys
import os
import warnings

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from globasa_tokenizer import GlobasaTokenizer, MorphKind


@pytest.fixture(scope="module")
def tok():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return GlobasaTokenizer()


def test_hyphen_inside_word_preserved(tok):
    """Hyphens between alphabetic characters stay inside the word token."""
    text = "Mexiko-Usali sen bon."
    tokens = tok.tokenize(text)
    surfaces = ["".join(m.surface for m in group) for group in tokens]
    # The hyphenated compound should be ONE token
    assert "Mexiko-Usali" in surfaces, (
        f"Expected 'Mexiko-Usali' as one token, got: {surfaces}"
    )


def test_hyphen_inside_word_second_example(tok):
    """moge-yamne is a single word token (object+verb+ne adj form)."""
    text = "un moge-yamne doku"
    tokens = tok.tokenize(text)
    surfaces = ["".join(m.surface for m in group) for group in tokens]
    assert "moge-yamne" in surfaces, (
        f"Expected 'moge-yamne' as one token, got: {surfaces}"
    )


def test_emdash_is_punct(tok):
    """Em-dash (—) adjacent to spaces is punctuation."""
    text = "Mi — te."
    tokens = tok.tokenize(text)
    kinds = [group[0].kind for group in tokens]
    assert MorphKind.PUNCT in kinds, (
        f"Expected PUNCT in token kinds for '—', got: {kinds}"
    )


def test_cu_optional_both_forms_no_crash(tok):
    """buka + -ne and buka + -cu + -ne should both segment without UNK."""
    for word in ["bukane", "bukacune"]:
        tokens = tok.tokenize(word)
        morphs = [m for g in tokens for m in g if m.kind != MorphKind.PUNCT]
        assert MorphKind.UNK not in [m.kind for m in morphs], (
            f"'{word}' produced UNK: {[(m.surface, m.kind) for m in morphs]}"
        )
        # Round-trip
        assert "".join(m.surface for m in morphs) == word


def test_roundtrip_hyphenated(tok):
    """Round-trip: detokenize(tokenize(text)) == text for hyphenated input."""
    text = "Mexiko-Usali sen poli-bon."
    tokens = tok.tokenize(text)
    recovered = tok.detokenize(tokens)
    # Allow whitespace normalization
    assert recovered.replace("  ", " ") == text


def test_no_crash_multi_suffix_oov(tok):
    """A synthetic word requiring multi-suffix stacking falls back cleanly (no crash, no UNK)."""
    word = "xulinemo"  # would require -li + -ne + -mo stacking
    tokens = tok.tokenize(word)
    morphs = [m for g in tokens for m in g if m.kind != MorphKind.PUNCT]
    assert MorphKind.UNK not in [m.kind for m in morphs], (
        f"'{word}' produced UNK"
    )
    assert "".join(m.surface for m in morphs) == word
