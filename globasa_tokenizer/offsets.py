"""
Surface alignment for LexiliAsel-decomposed compounds.

Takes a word string and a list of RawMorpheme (from affix_parser) and produces
Morpheme objects with correct start/end character offsets relative to word[0].

These offsets are *word-relative* (start from 0). The sentence tokenizer shifts
them by the word's start offset in the sentence.
"""

from __future__ import annotations

from dataclasses import dataclass, replace as dataclass_replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .affix_parser import RawMorpheme


class AlignmentError(ValueError):
    """Raised when a LexiliAsel breakdown doesn't align to the word surface."""

    def __init__(self, word: str, morphs, pos: int, surface: str):
        self.word = word
        self.morphs = morphs
        self.pos = pos
        self.surface = surface
        super().__init__(
            f"Cannot align '{surface}' in '{word}' at position {pos} "
            f"(morphs={[m.surface for m in morphs]})"
        )


def align(word: str, morphs: list) -> list:
    """Walk the surface string and assign start/end offsets to each RawMorpheme.

    Returns a list of (surface, lemma, kind, start, end) tuples.
    Raises AlignmentError if alignment fails.
    """
    pos = 0
    out = []
    for m in morphs:
        s = m.surface
        remaining = word[pos:]
        if remaining.lower().startswith(s.lower()):
            # Use exact case from the word surface
            actual_surface = word[pos: pos + len(s)]
            out.append((actual_surface, m.lemma, m.kind, pos, pos + len(s)))
            pos += len(s)
        else:
            raise AlignmentError(word, morphs, pos, s)

    if pos != len(word):
        raise AlignmentError(
            word, morphs, pos,
            f"<leftover '{word[pos:]}'>"
        )

    return out
