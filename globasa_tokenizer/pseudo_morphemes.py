"""
Pseudo-morpheme inventory loader + Aho-Corasick + DP cover.

Pseudo-morphemes are bound loanword fragments that recur across multiple Globasa
words but are NOT listed as Category=affix in word-list.csv. They can appear in
any position (initial, medial, final). Examples: -syon/-si (Romance -tion),
gaw/go (Sinitic 告), viu (Romance view).

TSV format: surface, lemma, origin, gloss, notes (tab-separated).
  - surface: the literal Globasa-spelled fragment (e.g. "syon")
  - lemma: canonical key shared by variant surfaces (e.g. "-tion" or "告")
  - origin: sinitic | romance | greek | candidate
  - gloss: human-readable gloss
  - notes: cross-references, example words

Lookup uses a hand-rolled Aho-Corasick automaton for any-position matching.
The DP cover picks the tiling with fewest pseudo-morphemes, longest individual
pieces, preferring earlier positions on ties.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_TSV_PATH = os.path.join(_DATA_DIR, "pseudo_morphemes.tsv")


@dataclass(frozen=True)
class PseudoMorphEntry:
    surface: str
    lemma: str
    origin: str
    gloss: str
    notes: str


def load_inventory(
    path: str = _TSV_PATH,
    include_candidates: bool = False,
) -> list[PseudoMorphEntry]:
    """Load the TSV; skip header and blank/comment lines.

    By default, rows with ``origin == "candidate"`` are skipped — those are
    auto-mined frequent letter combos awaiting human review (their lemmas
    look like ``?le``, ``?te``); they are noisy and expensive to apply
    (every Globasa word containing the bigram matches), so they are gated
    behind ``include_candidates=True``.
    """
    entries: list[PseudoMorphEntry] = []
    if not os.path.exists(path):
        return entries
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.rstrip("\n")
            if i == 0 or not line.strip() or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            surface = parts[0].strip()
            lemma = parts[1].strip() if len(parts) > 1 else surface
            origin = parts[2].strip() if len(parts) > 2 else ""
            gloss = parts[3].strip() if len(parts) > 3 else ""
            notes = parts[4].strip() if len(parts) > 4 else ""
            if not surface:
                continue
            if not include_candidates and origin == "candidate":
                continue
            entries.append(PseudoMorphEntry(surface, lemma, origin, gloss, notes))
    return entries


# ---------------------------------------------------------------------------
# Hand-rolled Aho-Corasick automaton
# ---------------------------------------------------------------------------
#
# IMPORTANT: outputs are NOT propagated eagerly along fail links at build time
# (the previous design did, which exploded memory for the 6,551-pattern mined-
# stems matcher — every node would carry copies of all reachable suffix outputs).
# Instead, each node stores only its OWN terminal output (or None), plus a
# pointer to the nearest ancestor-via-fail that has its own output (`out_link`).
# At search time we walk the out_link chain at each position to enumerate all
# matches reachable via failure suffixes — same correctness, O(text + matches)
# search, O(N) memory in the trie.

class _AhoCorasickNode:
    __slots__ = ("children", "fail", "output", "out_link")

    def __init__(self):
        self.children: dict[str, _AhoCorasickNode] = {}
        self.fail: Optional[_AhoCorasickNode] = None
        self.output: Optional[tuple[str, str]] = None  # (surface, lemma) at this terminal, or None
        self.out_link: Optional[_AhoCorasickNode] = None  # nearest fail-ancestor with .output set


class AhoCorasick:
    """Simple Aho-Corasick automaton for multi-pattern any-position matching.

    Finds ALL occurrences of all patterns in a text in O(text_len + #matches).
    """

    def __init__(self, patterns: list[tuple[str, str]]):
        """patterns: list of (surface, lemma)."""
        self._root = _AhoCorasickNode()
        for surface, lemma in patterns:
            self._insert(surface, lemma)
        self._build_fail_links()

    def _insert(self, surface: str, lemma: str) -> None:
        node = self._root
        for ch in surface:
            if ch not in node.children:
                node.children[ch] = _AhoCorasickNode()
            node = node.children[ch]
        # If two patterns share the same surface, the last one wins (deterministic).
        node.output = (surface, lemma)

    def _build_fail_links(self) -> None:
        from collections import deque
        q: deque[_AhoCorasickNode] = deque()
        root = self._root
        for child in root.children.values():
            child.fail = root
            child.out_link = None
            q.append(child)
        while q:
            node = q.popleft()
            for ch, child in node.children.items():
                fail = node.fail
                while fail is not None and fail is not root and ch not in fail.children:
                    fail = fail.fail
                if fail is None:
                    child.fail = root
                else:
                    child.fail = fail.children[ch] if ch in fail.children and fail.children[ch] is not child else root
                if child.fail is child:
                    child.fail = root
                # out_link: the nearest fail-ancestor that has its own output.
                f = child.fail
                child.out_link = f if f.output is not None else f.out_link
                q.append(child)

    def search(self, text: str) -> list[tuple[int, int, str, str]]:
        """Return list of (start, end, surface, lemma) for all matches in text."""
        results: list[tuple[int, int, str, str]] = []
        root = self._root
        node = root
        for i, ch in enumerate(text):
            while node is not root and ch not in node.children:
                node = node.fail  # type: ignore[assignment]
            if ch in node.children:
                node = node.children[ch]
            # Emit this node's own output, then walk the out_link chain.
            n = node
            if n.output is not None:
                surface, lemma = n.output
                results.append((i - len(surface) + 1, i + 1, surface, lemma))
            link = n.out_link
            while link is not None:
                surface, lemma = link.output  # by construction, link.output is not None
                results.append((i - len(surface) + 1, i + 1, surface, lemma))
                link = link.out_link
        return results


# ---------------------------------------------------------------------------
# DP cover
# ---------------------------------------------------------------------------

def dp_cover(
    word: str,
    matches: list[tuple[int, int, str, str]],
) -> Optional[list[tuple[int, int, str, str]]]:
    """Choose the best tiling of word using pseudo-morpheme matches.

    Cost lexicographic, lower is better:
      (1) #residue characters       — match-coverage maximised first
      (2) #match tokens             — fewer larger tokens preferred over many small
      (3) -max_seg_len              — within ties, longer individual segments win
      (4) leftmost match position   — implicit via DP order

    Returns None if dp[n] is unreachable (shouldn't happen since residue always
    extends). Cover entries include __residue__ runs for unmatched chars.

    Memory-efficient: dp[i] stores only (cost_tuple, back_pointer, last_segment).
    Cover is reconstructed via back-pointer walk. O(n) memory.
    """
    n = len(word)
    if n == 0:
        return []

    # dp[i] = (cost_tuple, back_pointer, last_segment) or None
    # cost_tuple = (residue_chars, token_count, -max_seg_len)
    INF = (10**9, 10**9, 10**9)
    dp: list[Optional[tuple[tuple[int, int, int], int, tuple]]] = [None] * (n + 1)
    dp[0] = ((0, 0, 0), -1, ())

    ends: dict[int, list[tuple[int, int, str, str]]] = {}
    for m in matches:
        ends.setdefault(m[1], []).append(m)

    for i in range(1, n + 1):
        best: Optional[tuple[tuple[int, int, int], int, tuple]] = None

        # Option 1: extend with a pseudo-morpheme ending at i.
        if i in ends:
            for start, end, surface, lemma in ends[i]:
                prev = dp[start]
                if prev is None:
                    continue
                (p_res, p_tok, p_neg_max), _, _ = prev
                seg_len = end - start
                new_neg_max = p_neg_max if p_neg_max <= -seg_len else -seg_len
                cand_cost = (p_res, p_tok + 1, new_neg_max)
                cand = (cand_cost, start, (start, end, surface, lemma))
                if best is None or cand_cost < best[0]:
                    best = cand

        # Option 2: extend by one char as residue.
        prev = dp[i - 1]
        if prev is not None:
            (p_res, p_tok, p_neg_max), _, _ = prev
            cand_cost = (p_res + 1, p_tok, p_neg_max)
            cand = (cand_cost, i - 1, (i - 1, i, word[i - 1:i], "__residue__"))
            if best is None or cand_cost < best[0]:
                best = cand

        dp[i] = best

    if dp[n] is None:
        return None

    # Reconstruct cover by walking back-pointers, coalesce adjacent residue runs.
    raw: list[tuple[int, int, str, str]] = []
    i = n
    while i > 0:
        cell = dp[i]
        assert cell is not None
        _, back, seg = cell
        raw.append(seg)
        i = back
    raw.reverse()

    out: list[tuple[int, int, str, str]] = []
    for s, e, surf, lemma in raw:
        if lemma == "__residue__" and out and out[-1][3] == "__residue__" and out[-1][1] == s:
            last = out[-1]
            out[-1] = (last[0], e, word[last[0]:e], "__residue__")
        else:
            out.append((s, e, surf, lemma))
    return out


# ---------------------------------------------------------------------------
# PseudoMorphemeMatcher — the public interface
# ---------------------------------------------------------------------------

class PseudoMorphemeMatcher:
    """Loads inventory and exposes match() for a word string."""

    def __init__(self, path: str = _TSV_PATH, include_candidates: bool = False):
        self._entries = load_inventory(path, include_candidates=include_candidates)
        patterns = [(e.surface, e.lemma) for e in self._entries]
        self._lemma_map: dict[str, str] = {e.surface: e.lemma for e in self._entries}
        if patterns:
            self._ac = AhoCorasick(patterns)
        else:
            self._ac = None

    def match(self, word: str) -> list[tuple[int, int, str, str]]:
        """Return dp_cover result for `word`.

        Returns list of (start, end, surface, lemma|"__residue__").
        Empty list if no pseudo-morphemes are loaded or none match.
        """
        if self._ac is None:
            return [(0, len(word), word, "__residue__")]
        raw_matches = self._ac.search(word)
        if not raw_matches:
            return [(0, len(word), word, "__residue__")]
        cover = dp_cover(word, raw_matches)
        if cover is None:
            return [(0, len(word), word, "__residue__")]
        return cover
