"""
Mined corpus-frequent stems — Tier 1 of the fallback cascade.

TSV format: surface, frequency, example_words (tab-separated).
Loaded into an Aho-Corasick automaton for any-position matching.
DP cover identical to pseudo_morphemes.dp_cover but for stems.

The data file starts empty and is populated by tools/mine_frequent_stems.py.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from .pseudo_morphemes import AhoCorasick, dp_cover

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_TSV_PATH = os.path.join(_DATA_DIR, "mined_stems.tsv")


@dataclass(frozen=True)
class MinedStemEntry:
    surface: str
    frequency: int
    example_words: str


def load_mined_stems(
    path: str = _TSV_PATH,
    min_freq: int = 5,
    min_len: int = 3,
) -> list[MinedStemEntry]:
    """Load the TSV; skip header and blank/comment lines.

    Filters out low-signal rows: ``min_freq`` (default 5) and ``min_len`` (default 3)
    drop very-short / very-rare entries that mostly produce false matches and
    inflate the AC automaton. The full inventory has ~6,500 rows; the default
    filters keep the ~2,000 most useful.
    """
    entries: list[MinedStemEntry] = []
    if not os.path.exists(path):
        return entries
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.rstrip("\n")
            if i == 0 or not line.strip() or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 1:
                continue
            surface = parts[0].strip()
            freq = int(parts[1].strip()) if len(parts) > 1 and parts[1].strip().isdigit() else 0
            examples = parts[2].strip() if len(parts) > 2 else ""
            if not surface:
                continue
            if len(surface) < min_len or freq < min_freq:
                continue
            entries.append(MinedStemEntry(surface, freq, examples))
    return entries


class MinedStemMatcher:
    """Loads mined stems and exposes match() for DP cover.

    The TSV load and AC build are deferred to first ``match()`` call — most
    workloads (tokenizing in-lexicon Globasa text) never hit the cascade and
    therefore never pay the build cost.
    """

    def __init__(
        self,
        path: str = _TSV_PATH,
        min_freq: int = 5,
        min_len: int = 3,
    ):
        self._path = path
        self._min_freq = min_freq
        self._min_len = min_len
        self._entries: Optional[list[MinedStemEntry]] = None
        self._ac: Optional[AhoCorasick] = None
        self._built = False

    def _ensure_built(self) -> None:
        if self._built:
            return
        self._built = True
        self._entries = load_mined_stems(self._path, self._min_freq, self._min_len)
        patterns = [(e.surface, e.surface) for e in self._entries]
        if patterns:
            self._ac = AhoCorasick(patterns)

    def match(self, word: str) -> Optional[list[tuple[int, int, str, str]]]:
        """Return dp_cover result, or None if no full cover is possible.

        A full cover means no __residue__ segments remain. Unlike pseudo-morphemes,
        mined stems must cover the entire word or we return None so the cascade
        can try the next tier.
        """
        self._ensure_built()
        if self._ac is None:
            return None
        raw_matches = self._ac.search(word)
        if not raw_matches:
            return None
        cover = dp_cover(word, raw_matches)
        if cover is None:
            return None
        # Check for residue — if any residue remains, mined stems can't fully cover
        has_residue = any(lemma == "__residue__" for _, _, _, lemma in cover)
        if has_residue:
            return None
        return cover
