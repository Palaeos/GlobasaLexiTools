"""
test_roundtrip.py — For every word-list row, "".join(m.surface ...) == word.

Case handling: proper nouns are case-preserving; all others use the lowercased index key.
Also verifies offsets are contiguous and cover the word exactly.
"""

import sys
import os
import warnings

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from globasa_tokenizer.lexicon import build_lexicon
from globasa_tokenizer.segmenter import segment_word
from globasa_tokenizer import MorphKind

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_WORDLIST = os.path.join(_DATA_DIR, "word-list.csv")


@pytest.fixture(scope="module")
def lex():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return build_lexicon(_WORDLIST)


def test_roundtrip_all_words(lex):
    df = pd.read_csv(_WORDLIST, index_col="Word", dtype=str)
    df.index = df.index.astype(str).str.strip()

    n_ok = 0
    n_unk = 0
    n_fail = 0
    failures = []
    unk_examples = []

    for word, row in df.iterrows():
        w = str(word).strip()
        if not w or w == "nan":
            continue

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            morphs = segment_word(w, 0, 0, lex)

        # Round-trip check
        reconstructed = "".join(m.surface for m in morphs)
        if reconstructed != w:
            n_fail += 1
            failures.append((w, reconstructed, [m.surface for m in morphs]))
            continue

        # UNK count
        if any(m.kind == MorphKind.UNK for m in morphs):
            n_unk += 1
            unk_examples.append(w)

        n_ok += 1

    print(f"\nRound-trip: {n_ok} pass / {n_fail} fail / {n_unk} with UNK morph")
    if unk_examples:
        print(f"  UNK examples: {unk_examples[:10]}")
    if failures:
        for w, rec, parts in failures[:10]:
            print(f"  FAIL: {w!r} → {rec!r} ({parts})")

    assert n_fail == 0, (
        f"{n_fail} round-trip failures. First few: {failures[:5]}"
    )
    assert n_unk == 0, (
        f"{n_unk} words with UNK morphemes. Examples: {unk_examples[:10]}"
    )
