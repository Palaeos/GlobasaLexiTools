"""
test_offsets.py — For ~10 hand-picked sentences, verify:
  - text[m.start:m.end] == m.surface for every morpheme
  - Morpheme offsets within a word are contiguous (no gaps, no overlaps)
  - word_index values are monotonically non-decreasing and reset for punct
"""

import sys
import os
import warnings

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from globasa_tokenizer import GlobasaTokenizer, MorphKind

SENTENCES = [
    "Mi le yam un kitabudom.",
    "Te eskri fe poli taim.",
    "Yu no hedo na sida.",
    "Globasa sen bon.",
    "Le be-yam-ne doku.",
    "Mi doku plu kitabu.",
    "Xencudin loga Globasa.",
    "Fe mingo, mi xa yam.",
    "Un lil-dom sen amisi.",
    "Kitabu-dom-li doku sen bon.",
]


@pytest.fixture(scope="module")
def tokenizer():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return GlobasaTokenizer()


@pytest.mark.parametrize("sentence", SENTENCES)
def test_offsets_exact_match(tokenizer, sentence):
    """text[m.start:m.end] == m.surface for every morpheme."""
    tokens = tokenizer.tokenize(sentence)
    for group in tokens:
        for m in group:
            assert sentence[m.start:m.end] == m.surface, (
                f"Offset mismatch in '{sentence}': "
                f"expected {sentence[m.start:m.end]!r} but morph.surface={m.surface!r} "
                f"at [{m.start}:{m.end}]"
            )


@pytest.mark.parametrize("sentence", SENTENCES)
def test_offsets_contiguous_within_word(tokenizer, sentence):
    """Within each word group, morpheme offsets are contiguous."""
    tokens = tokenizer.tokenize(sentence)
    for group in tokens:
        if len(group) <= 1:
            continue
        for i in range(len(group) - 1):
            assert group[i].end == group[i + 1].start, (
                f"Gap/overlap in '{sentence}': "
                f"morph[{i}].end={group[i].end} != morph[{i+1}].start={group[i+1].start}"
            )


@pytest.mark.parametrize("sentence", SENTENCES)
def test_word_index_monotone(tokenizer, sentence):
    """word_index values are non-decreasing across non-punct tokens."""
    tokens = tokenizer.tokenize(sentence)
    last_wi = -1
    for group in tokens:
        if len(group) == 1 and group[0].kind == MorphKind.PUNCT:
            continue
        wi = group[0].word_index
        assert wi >= last_wi, f"word_index decreased from {last_wi} to {wi}"
        last_wi = wi
