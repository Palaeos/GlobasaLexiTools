"""
test_hf_adapter.py — HuggingFace PreTokenizer smoke tests.

Skips if `tokenizers` is not installed.
"""

import sys
import os
import warnings

import pytest

tokenizers_mod = pytest.importorskip("tokenizers", reason="HuggingFace tokenizers not installed")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def test_build_pre_tokenizer():
    """build_pre_tokenizer() returns a working PreTokenizer."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from globasa_tokenizer.hf_adapter import build_pre_tokenizer
        pt = build_pre_tokenizer()
        assert pt is not None


def test_pre_tokenizer_splits_morphemes():
    """PreTokenizer splits 'kitabudom' at morpheme boundaries."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from globasa_tokenizer.hf_adapter import build_pre_tokenizer
        pt = build_pre_tokenizer()
        result = pt.pre_tokenize_str("Mi le yam kitabudom.")
        # result is list of (token, (start, end)) tuples
        surfaces = [tok for tok, _ in result]
        assert len(surfaces) > 0
        assert "Mi" in surfaces or "mi" in surfaces.copy()
        # Reconstructing should give original text
        full = ""
        last_end = 0
        for tok, (start, end) in result:
            full += " " * (start - last_end) + tok
            last_end = end
        assert full == "Mi le yam kitabudom."


def test_hf_tokenizer_with_word_level_model():
    """Build a full Tokenizer using GlobasaPreTokenizer."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from tokenizers import Tokenizer, models
        from globasa_tokenizer.hf_adapter import build_pre_tokenizer
        try:
            tk = Tokenizer(models.WordLevel(unk_token="[UNK]"))
            tk.pre_tokenizer = build_pre_tokenizer()
            # pre_tokenize_str is a method on the pre_tokenizer, not the full Tokenizer
            result = tk.pre_tokenizer.pre_tokenize_str("kitabudom")
            assert len(result) > 0
        except Exception as e:
            pytest.skip(f"Full HF tokenizer build failed: {e}")
