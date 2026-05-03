"""
Sentence-level tokenizer.

Steps:
  1. Single-pass scanner — walk text once, emitting word / punct chunks with offsets.
     Hyphen handling: '-' between alphabetic characters stays inside the word token.
     '-' adjacent to whitespace is treated as punctuation.
  2. MWE merge — greedy longest match against lex.phrases.
     Conservative pattern from PosTagger.py: only match when first word is
     fe/cel/he/no or second word is in MULTI_WORD_PARTS.
  3. segment_word() for each token.

Detokenize: join word surfaces; punctuation tokens attach to the preceding word
if they were originally adjacent (no space between them).
"""

from __future__ import annotations

import string
from typing import Iterable, Iterator, Optional

from ._types import Morpheme, MorphKind
from .lexicon import Lexicon, build_lexicon
from .segmenter import segment_word

# Punctuation set (precomputed frozenset)
_PUNCT_CHARS: frozenset = frozenset(string.punctuation) | frozenset("«»„""''…—–")

# Multi-word parts (from PosTagger.py)
_MULTI_WORD_PARTS = frozenset({
    "kom", "fe", "xafe", "lefe", "leya", "xaya", "na", "hu",
    "mara", "watu", "din", "noce", "leki", "xaki", "de",
})
# MWE merging is OFF by default for the morphology-aware tokenizer: the goal
# of this tokenizer is to expose morphological structure word-by-word, and
# fusing multi-word phrases (`cel na`, `fe of`, …) hides the constituent
# function words. Aligners that need the phrase-as-unit grouping should opt
# in via tokenizer.merge_mwes=True (or do it themselves on top of the output).
_MWE_FIRST_WORDS = frozenset()


def _is_alpha(ch: str) -> bool:
    return ch.isalpha()

# Pre-build MWE candidate set from lex.phrases ∩ _MWE_FIRST_WORDS at build time
_EMPTY_PHRASES: dict = {}


def _scan_tokens(text: str) -> list[tuple[int, int, str, bool]]:
    """Single-pass scanner. Returns list of (start, end, surface, is_punct).

    Hyphen rule: '-' between two alphabetic characters → part of word.
    """
    tokens: list[tuple[int, int, str, bool]] = []
    tokens_append = tokens.append  # avoid method lookup in hot loop
    n = len(text)
    i = 0
    while i < n:
        ch = text[i]
        # Skip whitespace
        if ch == ' ' or ch == '\t' or ch == '\n' or ch == '\r':
            i += 1
            continue
        # Determine if this is the start of a word or a punctuation char
        ch_is_alpha = ch.isalpha()
        if ch_is_alpha or ch == '-':
            # Start of a word token (may include hyphens between alpha chars)
            start = i
            j = i
            while j < n:
                c = text[j]
                if c.isalpha():
                    j += 1
                elif c == '-':
                    # Hyphen: keep if flanked by alpha chars on both sides
                    if (j > 0 and j + 1 < n
                            and text[j - 1].isalpha()
                            and text[j + 1].isalpha()):
                        j += 1
                    else:
                        break
                else:
                    break
            if j > start:
                tokens_append((start, j, text[start:j], False))
                i = j
            else:
                # Lone hyphen → punct
                tokens_append((i, i + 1, ch, True))
                i += 1
        elif ch in _PUNCT_CHARS:
            tokens_append((i, i + 1, ch, True))
            i += 1
        else:
            # Non-alpha, non-punct character (digit, etc.) → treat as word
            start = i
            j = i
            while j < n and not text[j].isspace() and text[j] not in _PUNCT_CHARS:
                j += 1
            tokens_append((start, j, text[start:j], False))
            i = j

    return tokens


def _merge_mwe(
    raw_tokens: list[tuple[int, int, str, bool]],
    lex: Lexicon,
    sorted_phrases: dict = None,
    mwe_keys: frozenset = None,
) -> list[tuple[int, int, str, bool]]:
    """Greedily merge multi-word expressions using lex.phrases.

    Conservative pattern: only attempt when first word is in _MWE_FIRST_WORDS.
    sorted_phrases and mwe_keys are pre-computed at init for performance.
    """
    if not lex.phrases:
        return raw_tokens
    if sorted_phrases is None:
        sorted_phrases = {k: sorted(v, key=lambda x: -x[0]) for k, v in lex.phrases.items()}
    if mwe_keys is None:
        mwe_keys = frozenset(k for k in sorted_phrases if k in _MWE_FIRST_WORDS)

    out: list[tuple[int, int, str, bool]] = []
    seen = set()  # raw indices already consumed
    ri = 0
    while ri < len(raw_tokens):
        if ri in seen:
            ri += 1
            continue
        start, end, surf, is_punct = raw_tokens[ri]
        if is_punct:
            out.append(raw_tokens[ri])
            ri += 1
            continue

        w_lower = surf.lower()
        matched = False
        if w_lower in mwe_keys:
            candidates = sorted_phrases[w_lower]
            for phrase_len, full_phrase in candidates:
                # Collect next (phrase_len - 1) word tokens from raw
                phrase_words = [w_lower]
                next_ri = ri + 1
                collected_ris = [ri]
                count = 1
                while count < phrase_len and next_ri < len(raw_tokens):
                    ns, ne, nsurf, nip = raw_tokens[next_ri]
                    if not nip:
                        phrase_words.append(nsurf.lower())
                        collected_ris.append(next_ri)
                        count += 1
                    next_ri += 1
                if " ".join(phrase_words) == full_phrase and count == phrase_len:
                    merged_start = raw_tokens[collected_ris[0]][0]
                    merged_end = raw_tokens[collected_ris[-1]][1]
                    merged_surf = text_slice = full_phrase  # use normalised form
                    # Actually reconstruct from raw
                    merged_surf = "".join(
                        raw_tokens[cri][2] + (
                            " " if k < len(collected_ris) - 1 else ""
                        )
                        for k, cri in enumerate(collected_ris)
                    )
                    out.append((merged_start, merged_end, merged_surf, False))
                    seen.update(range(ri, next_ri))
                    ri = next_ri
                    matched = True
                    break
        if not matched:
            out.append(raw_tokens[ri])
            ri += 1
    return out


class _GlobasaTokenizerImpl:
    """Internal implementation (separated from the public GlobasaTokenizer wrapper)."""

    def __init__(
        self,
        decompose_pseudo_morphemes: bool = False,
        fallback: str = "cascade",
        with_pos: bool = False,
        max_root_chars: Optional[int] = None,
        wordlist_path: Optional[str] = None,
    ):
        self._decompose_pseudo = decompose_pseudo_morphemes
        self._fallback = fallback
        self._with_pos = with_pos
        self._max_root_chars = max_root_chars
        if wordlist_path:
            self.lex = build_lexicon(wordlist_path)
        else:
            from .lexicon import get_lexicon
            self.lex = get_lexicon()
        # Pre-sort phrases so _merge_mwe doesn't sort on every call
        self._sorted_phrases: dict[str, list] = {
            k: sorted(v, key=lambda x: -x[0])
            for k, v in self.lex.phrases.items()
        }
        # Active MWE keys: only phrases whose first word is in _MWE_FIRST_WORDS
        self._mwe_keys: frozenset = frozenset(
            k for k in self._sorted_phrases if k in _MWE_FIRST_WORDS
        )

    def tokenize(self, text: str) -> list[list[Morpheme]]:
        """Tokenize sentence → list[list[Morpheme]]."""
        raw = _scan_tokens(text)
        merged = _merge_mwe(raw, self.lex, self._sorted_phrases, self._mwe_keys)
        result: list[list[Morpheme]] = []
        word_counter = 0
        for start, end, surf, is_punct in merged:
            if is_punct:
                morphs = [Morpheme(
                    surface=surf,
                    lemma=surf,
                    kind=MorphKind.PUNCT,
                    start=start,
                    end=end,
                    word_index=word_counter,
                )]
                result.append(morphs)
            else:
                morphs = segment_word(
                    surf, start, word_counter, self.lex,
                    decompose_pseudo_morphemes=self._decompose_pseudo,
                    max_root_chars=self._max_root_chars,
                )
                result.append(morphs)
                word_counter += 1
        return result

    def tokenize_batch(self, texts: Iterable[str]) -> Iterator[list[list[Morpheme]]]:
        """Generator: yield tokenized sentences."""
        for text in texts:
            yield self.tokenize(text)

    def detokenize(self, tokens: list[list[Morpheme]]) -> str:
        """Reconstruct text from token groups.

        Punctuation tokens attach to preceding word without space.
        All other tokens separated by single spaces.
        """
        if not tokens:
            return ""
        parts: list[str] = []
        for i, group in enumerate(tokens):
            surface = "".join(m.surface for m in group)
            is_punct = len(group) == 1 and group[0].kind == MorphKind.PUNCT
            if i == 0:
                parts.append(surface)
            elif is_punct:
                # Attach to previous with no space
                parts.append(surface)
            else:
                parts.append(" " + surface)
        return "".join(parts)
