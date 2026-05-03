"""
test_alignment.py — Aligner format + projection round-trips.
"""

import sys
import os
import warnings

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from globasa_tokenizer.lexicon import build_lexicon
from globasa_tokenizer.alignment import (
    to_aligner_text,
    to_awesome_align_pair,
    project_to_words,
    project_to_morphs,
)

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_WORDLIST = os.path.join(_DATA_DIR, "word-list.csv")


@pytest.fixture(scope="module")
def lex():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return build_lexicon(_WORDLIST)


def test_to_aligner_text_basic(lex):
    """to_aligner_text returns a space-separated morph string and a flat morph list."""
    text = "Mi le yam un kitabudom."
    morph_str, flat = to_aligner_text(text, lex)
    assert isinstance(morph_str, str)
    assert len(morph_str) > 0
    # Should have the period as a separate token
    parts = morph_str.split()
    assert "." in parts, f"Expected '.' in morph string: {morph_str}"
    # Flat list should be non-empty
    assert len(flat) > 0
    # word_index for 'mi' should be 0
    assert flat[0].word_index == 0


def test_to_aligner_text_word_index_chain(lex):
    """Morphemes from the same word share the same word_index."""
    text = "Mi le yam un kitabudom."
    _, flat = to_aligner_text(text, lex)
    # Find morphemes for kitabudom (the compound) — they should share word_index
    kitabu_morphs = [m for m in flat if "kitabu" in m.surface.lower() or "dom" in m.surface.lower()]
    if len(kitabu_morphs) >= 2:
        word_indices = {m.word_index for m in kitabu_morphs}
        assert len(word_indices) == 1, (
            f"kitabu and dom should share word_index, got: "
            f"{[(m.surface, m.word_index) for m in kitabu_morphs]}"
        )


def test_project_to_words_collapses(lex):
    """project_to_words collapses multiple morpheme alignments to one word alignment."""
    text = "Mi le yam un kitabudom."
    _, flat = to_aligner_text(text, lex)
    # Find kitabudom morpheme indices
    kitabu_indices = [i for i, m in enumerate(flat) if "kitabu" in m.surface.lower() or "dom" in m.surface.lower()]
    if len(kitabu_indices) >= 2:
        # Both align to English word 2 (say)
        alignments = [(kitabu_indices[0], 2), (kitabu_indices[1], 2)]
        projected = project_to_words(alignments, flat)
        # Should collapse to one pair
        word_indices = {w for w, _ in projected}
        assert len(word_indices) == 1, (
            f"Expected collapse to one word_index, got: {projected}"
        )


def test_project_to_words_drops_duplicates(lex):
    """project_to_words removes duplicate (word_idx, other_idx) pairs."""
    text = "Mi le yam."
    _, flat = to_aligner_text(text, lex)
    # Create duplicate alignments
    if flat:
        alignments = [(0, 5), (0, 5)]  # same pair twice
        projected = project_to_words(alignments, flat)
        assert len(projected) == 1


def test_awesome_align_pair_format(lex):
    """to_awesome_align_pair produces '... ||| ...' format."""
    line = to_awesome_align_pair("Mi le yam.", ["I", "ate"], lex)
    assert " ||| " in line, f"Missing ' ||| ' separator: {line!r}"
    parts = line.split(" ||| ")
    assert len(parts) == 2
    glb_side, eng_side = parts
    assert len(glb_side.strip()) > 0
    assert eng_side.strip() == "I ate"


def test_project_to_morphs_returns_morpheme_objects(lex):
    """project_to_morphs returns (Morpheme, other_idx) pairs."""
    text = "Mi le."
    _, flat = to_aligner_text(text, lex)
    if flat:
        projected = project_to_morphs([(0, 3)], flat)
        assert len(projected) == 1
        morph, other_idx = projected[0]
        assert other_idx == 3
        # Use type name comparison to avoid double-import issues
        assert type(morph).__name__ == "Morpheme"
        assert hasattr(morph, "surface") and hasattr(morph, "lemma") and hasattr(morph, "kind")
