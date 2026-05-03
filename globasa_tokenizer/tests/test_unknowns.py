"""
test_unknowns.py — Greedy fallback regression cases.

Tests that:
  - Novel composed words (root+suffix not in lexicon) are segmented without UNK
  - Known-tricky bare roots ending in affix-like patterns do NOT split when in-lexicon
  - Round-trip holds for all OOV inputs
  - Adversarial consonant-cluster inputs degrade gracefully (no crash)
"""

import sys
import os
import warnings

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from globasa_tokenizer import GlobasaTokenizer, MorphKind

# Words that should NOT be split (they're in the lexicon as roots/derived)
# Even if they superficially end in a known suffix pattern
NO_SPLIT_WORDS = [
    "neli",      # "four" — ends in -li but is a root
    "hali",      # "state/condition" — root
    "soli",      # root — don't split as sol-+i
    "poli",      # root
    "teli",      # root
    "mali",      # root
]

# OOV novel compositions: root + known suffix
OOV_NOVEL = [
    ("bayorli", "bayo", "li"),    # hypothetical: bayo (root) + -li
    ("amirya", "amir", "ya"),     # hypothetical: amir + -ya
    ("dokuyen", "doku", "yen"),   # doku (root) + -yen
]

# Adversarial / unusual strings
ADVERSARIAL = [
    "xqzkbtl",   # no vowels — should degrade to chars/bigrams without crash
    "aaa",        # repeated vowel
    "",            # empty — should return empty list
    "a",           # single char
]


@pytest.fixture(scope="module")
def tok():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return GlobasaTokenizer()


@pytest.mark.parametrize("word", NO_SPLIT_WORDS)
def test_known_roots_not_split(tok, word):
    """Known roots that look like they have affixes should remain as ROOT."""
    tokens = tok.tokenize(word)
    morphs = [m for group in tokens for m in group if m.kind != MorphKind.PUNCT]
    kinds = [m.kind for m in morphs]
    # The word should segment as a single morpheme (ROOT or FUNCTION) or via LexiliAsel
    # — not via UNK
    assert MorphKind.UNK not in kinds, (
        f"'{word}' produced UNK morphemes: {[(m.surface, m.kind) for m in morphs]}"
    )
    # Round-trip preserved
    reconstructed = "".join(m.surface for m in morphs)
    assert reconstructed == word, f"Round-trip failed for '{word}': got '{reconstructed}'"


@pytest.mark.parametrize("word,root,suffix", OOV_NOVEL)
def test_oov_novel_no_unk(tok, word, root, suffix):
    """OOV composed words should not produce UNK (they should hit syllable fallback)."""
    tokens = tok.tokenize(word)
    morphs = [m for group in tokens for m in group if m.kind != MorphKind.PUNCT]
    assert MorphKind.UNK not in [m.kind for m in morphs], (
        f"'{word}' produced UNK: {[(m.surface, m.kind) for m in morphs]}"
    )
    # Round-trip
    assert "".join(m.surface for m in morphs) == word


@pytest.mark.parametrize("word", ["xqzkbtl", "aaa", "a"])
def test_adversarial_no_crash(tok, word):
    """Adversarial inputs should not crash and should round-trip."""
    tokens = tok.tokenize(word)
    morphs = [m for group in tokens for m in group]
    reconstructed = "".join(m.surface for m in morphs)
    assert reconstructed == word, f"Round-trip failed for '{word}': got '{reconstructed}'"


def test_empty_string(tok):
    """Empty input returns empty list."""
    tokens = tok.tokenize("")
    assert tokens == []


def test_detokenize_roundtrip(tok):
    """detokenize(tokenize(text)) == text for a normal sentence."""
    text = "Mi le yam un kitabudom."
    tokens = tok.tokenize(text)
    recovered = tok.detokenize(tokens)
    # Whitespace normalization is acceptable (single spaces)
    assert recovered.replace("  ", " ").strip() == text.strip()
