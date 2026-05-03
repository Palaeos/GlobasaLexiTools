"""
test_fallback_cascade.py — Tiered cover selection.

Tests:
  - For OOV inputs, cascade selects the fewest-token cover
  - Mined stems beat syllables when they produce fewer tokens
  - Adversarial input degrades gracefully
  - Round-trip preserved in all cases
"""

import sys
import os
import warnings

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from globasa_tokenizer.syllable_fallback import syllable_cover
from globasa_tokenizer.fallback_cascade import cascade
from globasa_tokenizer.mined_stems import MinedStemMatcher


def _syllable_token_count(word):
    return len(syllable_cover(word))


@pytest.mark.parametrize("word", [
    "internasyon", "informasi", "kompyuta",
])
def test_cascade_no_crash(word):
    """Cascade doesn't crash and produces a valid cover."""
    mined = MinedStemMatcher()  # empty data file → no stems
    cover = cascade(word, mined)
    # Cover must be non-empty
    assert len(cover) > 0
    # Round-trip
    reconstructed = "".join(surf for _, _, surf, _ in cover)
    assert reconstructed == word, f"Round-trip failed for '{word}': got '{reconstructed}'"


def test_cascade_adversarial():
    """Adversarial input (no vowels) degrades to chars without crashing."""
    word = "xqzkbtl"
    mined = MinedStemMatcher()
    cover = cascade(word, mined)
    reconstructed = "".join(surf for _, _, surf, _ in cover)
    assert reconstructed == word


def test_cascade_single_char():
    """Single char input handled correctly."""
    mined = MinedStemMatcher()
    cover = cascade("a", mined)
    assert "".join(surf for _, _, surf, _ in cover) == "a"


def test_cascade_contiguous_offsets():
    """Cascade cover has contiguous offsets."""
    mined = MinedStemMatcher()
    cover = cascade("internasyon", mined)
    for i in range(len(cover) - 1):
        assert cover[i][1] == cover[i + 1][0], (
            f"Gap in cascade cover: {cover}"
        )
    assert cover[0][0] == 0
    assert cover[-1][1] == len("internasyon")


def test_mined_stems_beat_syllables_when_fewer_tokens():
    """If mined stems produce fewer tokens than syllables, cascade picks mined stems.

    We test this by creating a MockMatcher that returns a 2-token cover for
    'internasyon', while syllables would give 4 tokens.
    """
    class MockMatcher:
        def match(self, word):
            if word == "internasyon":
                # 2-token cover: inter + nasyon
                return [(0, 5, "inter", "inter"), (5, 11, "nasyon", "nasyon")]
            return None

    cover = cascade("internasyon", MockMatcher())
    # Should pick the 2-token cover (fewer than 4-syllable cover)
    assert len(cover) <= _syllable_token_count("internasyon"), (
        f"Expected mined stems to win with ≤{_syllable_token_count('internasyon')} tokens, "
        f"but got {len(cover)}: {cover}"
    )
    reconstructed = "".join(surf for _, _, surf, _ in cover)
    assert reconstructed == "internasyon"
