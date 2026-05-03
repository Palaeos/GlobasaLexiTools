"""
HuggingFace tokenizers adapter for Globasa.

Provides GlobasaPreTokenizer — a custom PreTokenizer for the `tokenizers` library
that splits text into morpheme-aligned spans before BPE/Unigram/WordPiece.

Usage:
    from tokenizers import Tokenizer, models
    from globasa_tokenizer.hf_adapter import build_pre_tokenizer
    tk = Tokenizer(models.WordLevel(unk_token='[UNK]'))
    tk.pre_tokenizer = build_pre_tokenizer()
    print(tk.pre_tokenizer.pre_tokenize_str('Mi le yam kitabudom.'))

The `tokenizers` import is wrapped in try/except — this module can be imported
without HuggingFace tokenizers installed. It raises an informative ImportError
only at use time.
"""

from __future__ import annotations

from .. import GlobasaTokenizer

try:
    from tokenizers import NormalizedString, PreTokenizedString
    _HF_AVAILABLE = True
except ImportError:
    _HF_AVAILABLE = False
    NormalizedString = None
    PreTokenizedString = None


def _require_hf():
    if not _HF_AVAILABLE:
        raise ImportError(
            "HuggingFace tokenizers is not installed. "
            "Install it with: pip install tokenizers\n"
            "Or: pip install 'globasa-tokenizer[hf]'"
        )


class GlobasaPreTokenizer:
    """Custom HuggingFace PreTokenizer that splits on Globasa morpheme boundaries."""

    def __init__(self):
        _require_hf()
        self._core = GlobasaTokenizer()

    def globasa_split(self, i: int, normalized: "NormalizedString"):
        """Split a NormalizedString into morpheme-aligned spans."""
        text = str(normalized)
        groups = self._core.tokenize(text)
        # Flatten: one span per morpheme (including punct)
        spans = [(m.start, m.end) for grp in groups for m in grp]
        return [normalized[s:e] for s, e in spans]

    def pre_tokenize(self, pretok: "PreTokenizedString"):
        """Called by the tokenizers library on each piece."""
        pretok.split(self.globasa_split)


def build_pre_tokenizer():
    """Build and return a HuggingFace PreTokenizer.custom wrapping GlobasaPreTokenizer."""
    _require_hf()
    try:
        from tokenizers import pre_tokenizers
        return pre_tokenizers.PreTokenizer.custom(GlobasaPreTokenizer())
    except Exception as e:
        raise RuntimeError(f"Failed to build HF pre-tokenizer: {e}") from e


__all__ = ["GlobasaPreTokenizer", "build_pre_tokenizer"]
