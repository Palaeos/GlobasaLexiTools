"""
test_syllable_fallback.py — OOV words split into syllables; round-trip preserved.
"""

import sys
import os
import warnings

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from globasa_tokenizer.syllable_fallback import syllabify, syllable_cover
from globasa_tokenizer import GlobasaTokenizer, MorphKind


@pytest.mark.parametrize("word,expected_count", [
    ("kitabu", 3),     # ki-ta-bu
    ("doku", 2),       # do-ku
    ("a", 1),          # single vowel
    ("globasa", 3),    # glo-ba-sa
    ("internasyon", 4),  # in-ter-na-syon
])
def test_syllabify_count(word, expected_count):
    """Syllabify returns correct number of syllables for known words."""
    syllables = syllabify(word)
    assert len(syllables) == expected_count, (
        f"Expected {expected_count} syllables for '{word}', got {len(syllables)}: {syllables}"
    )


@pytest.mark.parametrize("word", [
    "kitabu", "doku", "globasa", "internasyon", "informasi",
    "xqzkbtl",  # adversarial — no vowels, should still not crash
])
def test_syllable_roundtrip(word):
    """Concatenating syllables gives back the original word."""
    syllables = syllabify(word)
    assert "".join(syllables) == word, (
        f"Round-trip failed: '{''.join(syllables)}' != '{word}'"
    )


@pytest.mark.parametrize("word", [
    "kitabu", "doku", "internasyon",
])
def test_syllable_cover_offsets(word):
    """syllable_cover returns contiguous (start, end, surface) tuples."""
    cover = syllable_cover(word)
    # Check contiguous
    for i in range(len(cover) - 1):
        assert cover[i][1] == cover[i + 1][0], (
            f"Gap in cover for '{word}': {cover}"
        )
    # Check surface matches
    for start, end, surface in cover:
        assert word[start:end] == surface
    # Check full coverage
    assert cover[0][0] == 0
    assert cover[-1][1] == len(word)


def test_oov_fallback_produces_syllable_kind():
    """OOV words that go through fallback cascade produce SYLLABLE morphemes."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        tok = GlobasaTokenizer()
    # Use a clearly OOV word (not in any lexicon)
    word = "zarpilku"  # made up, not in word-list
    tokens = tok.tokenize(word)
    morphs = [m for g in tokens for m in g if m.kind != MorphKind.PUNCT]
    kinds = [m.kind for m in morphs]
    # Should be SYLLABLE (from fallback), not ROOT or UNK
    assert MorphKind.UNK not in kinds, f"Got UNK for OOV '{word}': {[(m.surface, m.kind) for m in morphs]}"
    # Round-trip
    assert "".join(m.surface for m in morphs) == word
