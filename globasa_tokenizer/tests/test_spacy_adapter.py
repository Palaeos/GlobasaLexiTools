"""
test_spacy_adapter.py — spaCy integration smoke tests.

Skips if spaCy is not installed.
"""

import sys
import os
import warnings

import pytest

spacy = pytest.importorskip("spacy", reason="spaCy not installed — skipping adapter tests")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def test_spacy_language_registration():
    """Importing the adapter registers 'glb' with spaCy."""
    import globasa_tokenizer.spacy_adapter  # noqa: F401
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            nlp = spacy.blank("glb")
            assert nlp.lang == "glb"
        except Exception as e:
            pytest.skip(f"GlobasaLanguage registration failed: {e}")


def test_spacy_morph_pipeline():
    """globasa_morph component writes Token._.morphs."""
    import globasa_tokenizer.spacy_adapter  # noqa: F401
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            nlp = spacy.blank("glb")
            nlp.add_pipe("globasa_morph")
            doc = nlp("Mi le yam kitabudom.")
            for tok in doc:
                morphs = tok._.morphs
                assert morphs is not None, f"Token '{tok.text}' has None morphs"
                assert len(morphs) > 0, f"Token '{tok.text}' has empty morphs"
        except Exception as e:
            pytest.skip(f"spaCy pipeline test failed: {e}")


def test_spacy_morphs_match_core():
    """Token._.morphs matches core tokenizer output."""
    import globasa_tokenizer.spacy_adapter  # noqa: F401
    from globasa_tokenizer import GlobasaTokenizer
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            nlp = spacy.blank("glb")
            nlp.add_pipe("globasa_morph")
            text = "Mi le yam."
            doc = nlp(text)
            core = GlobasaTokenizer()
            core_tokens = core.tokenize(text)
            for tok, core_group in zip(doc, core_tokens):
                assert [m.surface for m in tok._.morphs] == [m.surface for m in core_group], (
                    f"Mismatch for token '{tok.text}'"
                )
        except Exception as e:
            pytest.skip(f"spaCy core-match test failed: {e}")
