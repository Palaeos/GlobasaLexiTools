"""
Fallback cascade — picks the best subword cover for OOV residue.

Tier 1: Mined corpus-frequent stems (MinedStemMatcher)
Tier 2: Phonotactic syllables (syllable_fallback.syllable_cover)
Tier 3: Character bigrams
Tier 4: Single characters

The cover with the fewest tokens wins. Ties broken by longest individual token,
then leftmost position. Tiers 2-4 always succeed (so cascade always returns a result).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .syllable_fallback import syllable_cover

if TYPE_CHECKING:
    from .mined_stems import MinedStemMatcher


def _bigrams_cover(word: str) -> list[tuple[int, int, str]]:
    out = []
    for i in range(0, len(word), 2):
        chunk = word[i:i+2]
        out.append((i, i + len(chunk), chunk))
    return out


def _chars_cover(word: str) -> list[tuple[int, int, str]]:
    return [(i, i + 1, ch) for i, ch in enumerate(word)]


def _score(cover: list[tuple[int, int, str]]) -> tuple[int, int]:
    """Lower is better: (token_count, -max_length) so fewer tokens & longer pieces win."""
    if not cover:
        return (0, 0)
    max_len = max(e - s for s, e, _ in cover)
    return (len(cover), -max_len)


def cascade(
    word: str,
    mined_matcher,  # MinedStemMatcher | None
) -> list[tuple[int, int, str, str]]:
    """Return the best (start, end, surface, kind_str) cover for word.

    kind_str is "syllable" for all tiers (the Morpheme kind will be SYLLABLE).
    """
    candidates: list[list[tuple[int, int, str]]] = []

    # Tier 1: mined stems
    if mined_matcher is not None:
        stem_cover = mined_matcher.match(word)
        if stem_cover is not None:
            # Convert from (start, end, surface, lemma) to (start, end, surface)
            as_triples = [(s, e, surf) for s, e, surf, _ in stem_cover]
            candidates.append(as_triples)

    # Tier 2: syllables (always succeeds)
    syl = syllable_cover(word)
    candidates.append(syl)

    # Tier 3: bigrams (always succeeds)
    bi = _bigrams_cover(word)
    candidates.append(bi)

    # Tier 4: chars (always succeeds)
    ch = _chars_cover(word)
    candidates.append(ch)

    # Pick best
    best = min(candidates, key=_score)
    return [(s, e, surf, "syllable") for s, e, surf in best]
