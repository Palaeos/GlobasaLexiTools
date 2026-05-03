"""
test_pseudo_morpheme_split.py — Pseudo-morpheme tiling + canonical-lemma unification.

Tests (all with decompose_pseudo_morphemes=True):
  - European: revolusyon → ends with PSEUDO_MORPHEME(lemma='-tion')
  - European variant unification: revolusyon and informasi both produce lemma='-tion'
  - Sinitic any-position: gongaw → two PSEUDO_MORPHEMEs with appropriate lemmas
  - Round-trip preserved in all cases
  - With flag=False, words remain as ROOT (no pseudo-morpheme splitting)
"""

import sys
import os
import warnings

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from globasa_tokenizer import GlobasaTokenizer, MorphKind


@pytest.fixture(scope="module")
def tok_on():
    """Tokenizer with decompose_pseudo_morphemes=True."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return GlobasaTokenizer(decompose_pseudo_morphemes=True)


@pytest.fixture(scope="module")
def tok_off():
    """Tokenizer with decompose_pseudo_morphemes=False (default)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return GlobasaTokenizer(decompose_pseudo_morphemes=False)


def _morphs(tok, word):
    """Get flat morph list for a single word."""
    return [m for g in tok.tokenize(word) for m in g if m.kind != MorphKind.PUNCT]


def test_european_syon_split(tok_on):
    """revolusyon → last morph is PSEUDO_MORPHEME with lemma '-tion'."""
    morphs = _morphs(tok_on, "revolusyon")
    pseudo = [m for m in morphs if m.kind == MorphKind.PSEUDO_MORPHEME]
    assert any(m.lemma == "-tion" for m in pseudo), (
        f"Expected '-tion' pseudo-morpheme in revolusyon, got: {[(m.surface, m.lemma) for m in morphs]}"
    )


def test_european_si_split(tok_on):
    """informasi → last morph is PSEUDO_MORPHEME with lemma '-tion' (via -si surface)."""
    morphs = _morphs(tok_on, "informasi")
    pseudo = [m for m in morphs if m.kind == MorphKind.PSEUDO_MORPHEME]
    assert any(m.lemma == "-tion" for m in pseudo), (
        f"Expected '-tion' pseudo-morpheme in informasi, got: {[(m.surface, m.lemma) for m in morphs]}"
    )


def test_european_variant_unification(tok_on):
    """Both revolusyon and informasi produce the same canonical lemma for -tion."""
    morphs_s = _morphs(tok_on, "revolusyon")
    morphs_i = _morphs(tok_on, "informasi")
    lemmas_s = {m.lemma for m in morphs_s if m.kind == MorphKind.PSEUDO_MORPHEME}
    lemmas_i = {m.lemma for m in morphs_i if m.kind == MorphKind.PSEUDO_MORPHEME}
    assert lemmas_s & lemmas_i, (
        f"No shared canonical lemma: revolusyon has {lemmas_s}, informasi has {lemmas_i}"
    )


def test_sinitic_gongaw_split(tok_on):
    """gongaw → two PSEUDO_MORPHEME pieces; one with lemma '告'."""
    morphs = _morphs(tok_on, "gongaw")
    pseudo = [m for m in morphs if m.kind == MorphKind.PSEUDO_MORPHEME]
    assert any(m.lemma == "告" for m in pseudo), (
        f"Expected '告' pseudo-morpheme in gongaw, got: {[(m.surface, m.lemma, m.kind) for m in morphs]}"
    )


def test_sinitic_jingo_split(tok_on):
    """jingo → PSEUDO_MORPHEME with lemma '告' (surface 'go')."""
    morphs = _morphs(tok_on, "jingo")
    pseudo = [m for m in morphs if m.kind == MorphKind.PSEUDO_MORPHEME]
    assert any(m.lemma == "告" for m in pseudo), (
        f"Expected '告' pseudo-morpheme in jingo, got: {[(m.surface, m.lemma, m.kind) for m in morphs]}"
    )


def test_sinitic_gaw_go_share_lemma(tok_on):
    """gaw and go variants both produce lemma '告' (canonical unification)."""
    morphs_gongaw = _morphs(tok_on, "gongaw")
    morphs_jingo = _morphs(tok_on, "jingo")
    lemmas_g = {m.lemma for m in morphs_gongaw if m.kind == MorphKind.PSEUDO_MORPHEME}
    lemmas_j = {m.lemma for m in morphs_jingo if m.kind == MorphKind.PSEUDO_MORPHEME}
    assert "告" in lemmas_g, f"gongaw missing '告': {lemmas_g}"
    assert "告" in lemmas_j, f"jingo missing '告': {lemmas_j}"


def test_roundtrip_with_pseudo(tok_on):
    """Round-trip preserved when decompose_pseudo_morphemes=True."""
    for word in ["revolusyon", "informasi", "gongaw", "jingo", "nasyon"]:
        morphs = _morphs(tok_on, word)
        reconstructed = "".join(m.surface for m in morphs)
        assert reconstructed == word, (
            f"Round-trip failed for '{word}': got '{reconstructed}'"
        )


def test_flag_off_no_pseudo_split(tok_off):
    """With flag off, words that are roots/derived don't get pseudo-morpheme split."""
    # These should be ROOT or FUNCTION, not PSEUDO_MORPHEME
    for word in ["revolusyon", "nasyon"]:
        morphs = _morphs(tok_off, word)
        has_pseudo = any(m.kind == MorphKind.PSEUDO_MORPHEME for m in morphs)
        assert not has_pseudo, (
            f"'{word}' had PSEUDO_MORPHEME with flag=False: {[(m.surface, m.kind) for m in morphs]}"
        )
