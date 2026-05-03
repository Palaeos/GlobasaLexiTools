"""
globasa_tokenizer — Globasa morphology-aware tokenizer.

Public API:
  GlobasaTokenizer  — main class; tokenize() / detokenize() / tokenize_batch()
  Morpheme          — frozen dataclass (surface, lemma, kind, start, end, word_index, pos)
  MorphKind         — enum of morpheme types
  refresh_lexicon() — rebuild the module-level lexicon (after word-list updates)
"""

from __future__ import annotations

from typing import Iterable, Iterator, Optional

# Import from _types.py to avoid circular imports with segmenter/tokenizer
from ._types import MorphKind, Morpheme

__all__ = ["GlobasaTokenizer", "Morpheme", "MorphKind", "refresh_lexicon"]


# Lazy imports to avoid circular deps at module load time
def _get_tokenizer_cls():
    from .tokenizer import _GlobasaTokenizerImpl
    return _GlobasaTokenizerImpl


def _get_lexicon_fn():
    from .lexicon import refresh_lexicon as _refresh
    return _refresh


class GlobasaTokenizer:
    """Main tokenizer class.

    Args:
        decompose_pseudo_morphemes: if True, apply pseudo-morpheme tiling (step 6)
        fallback: "cascade" | "syllables_only" | "characters_only"
        with_pos: if True, run PosTagger for contextual POS on head morphemes
        max_root_chars: if set, split ROOT morphemes longer than this via cascade
        wordlist_path: override path to word-list.csv (default: bundled)
    """

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
        self._wordlist_path = wordlist_path
        self._impl = None  # lazy

    def _get_impl(self):
        if self._impl is None:
            cls = _get_tokenizer_cls()
            self._impl = cls(
                decompose_pseudo_morphemes=self._decompose_pseudo,
                fallback=self._fallback,
                with_pos=self._with_pos,
                max_root_chars=self._max_root_chars,
                wordlist_path=self._wordlist_path,
            )
        return self._impl

    def tokenize(self, text: str) -> list[list[Morpheme]]:
        """Tokenize a sentence into word-level morpheme groups.

        Returns list[list[Morpheme]]: one inner list per token (word or punct).
        """
        return self._get_impl().tokenize(text)

    def tokenize_batch(self, texts: Iterable[str]) -> Iterator[list[list[Morpheme]]]:
        """Yield tokenized sentences. Generator — doesn't materialize the corpus."""
        return self._get_impl().tokenize_batch(texts)

    def detokenize(self, tokens: list[list[Morpheme]]) -> str:
        """Reconstruct sentence from morpheme groups.

        Joins words with single spaces. Punctuation tokens are emitted without spaces
        if they were originally adjacent to the preceding word.
        """
        return self._get_impl().detokenize(tokens)

    @property
    def lexicon(self):
        """Access the underlying Lexicon for stats/inspection."""
        return self._get_impl().lex

    def vocab_stats(self) -> dict:
        """Return vocabulary counts (feeds NLLB wrapper planning)."""
        lex = self.lexicon
        return {
            "roots": lex.n_roots,
            "prefixes": lex.n_prefixes,
            "suffixes": lex.n_suffixes,
            "function_words": lex.n_function_words,
            "proper_nouns": lex.n_proper_nouns,
            "derived_with_lexiliasel": lex.n_derived,
            "phrases": lex.n_phrases,
            "total_morpheme_types": (
                lex.n_roots + lex.n_prefixes + lex.n_suffixes + lex.n_function_words
            ),
        }


def refresh_lexicon(wordlist_path: Optional[str] = None) -> None:
    """Rebuild the module-level lexicon (e.g. after updating data/word-list.csv)."""
    fn = _get_lexicon_fn()
    if wordlist_path:
        fn(wordlist_path)
    else:
        fn()
