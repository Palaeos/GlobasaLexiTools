"""
AffixTrie and ReversedAffixTrie — O(L) longest-match prefix/suffix lookup.

Builds once at lexicon load; trivially small (Globasa has ~70 prefixes / ~55 suffixes,
max depth ≤ 7 chars). Replaces the O(N×L) length-sorted scan in run_giza_improved.
"""

from __future__ import annotations
from typing import Optional


class AffixTrie:
    """Forward trie for prefix longest-match.

    Insert bare affix strings (without trailing '-').
    longest_match(word) → (matched_string, length) | None
    """

    __slots__ = ("children", "is_terminal", "value")

    def __init__(self):
        self.children: dict[str, AffixTrie] = {}
        self.is_terminal: bool = False
        self.value: Optional[str] = None  # the full affix string at this terminal

    def insert(self, affix: str) -> None:
        node = self
        for ch in affix:
            if ch not in node.children:
                node.children[ch] = AffixTrie()
            node = node.children[ch]
        node.is_terminal = True
        node.value = affix

    def longest_match(self, word: str) -> Optional[tuple[str, int]]:
        """Return (affix, length) for the longest affix that is a prefix of word,
        or None if no affix matches."""
        node = self
        last_match: Optional[tuple[str, int]] = None
        for i, ch in enumerate(word):
            if ch not in node.children:
                break
            node = node.children[ch]
            if node.is_terminal:
                last_match = (node.value, i + 1)
        return last_match


class ReversedAffixTrie:
    """Suffix trie built from reversed affix strings.

    Insert bare affix strings (without leading '-').
    longest_match(word) walks word from the right and returns (affix, length) | None.
    """

    __slots__ = ("_forward",)

    def __init__(self):
        self._forward = AffixTrie()

    def insert(self, affix: str) -> None:
        self._forward.insert(affix[::-1])

    def longest_match(self, word: str) -> Optional[tuple[str, int]]:
        """Return (affix, length) for the longest affix that is a suffix of word,
        or None if no affix matches."""
        result = self._forward.longest_match(word[::-1])
        if result is None:
            return None
        rev_affix, length = result
        return (rev_affix[::-1], length)
