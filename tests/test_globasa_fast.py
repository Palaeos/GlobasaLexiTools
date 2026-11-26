"""The Rust extension (rust/globasa_fast) against its Python originals.

    venv/bin/python -m pytest tests/test_globasa_fast.py -q

Skipped when the extension is not built (./setup.sh --fast). GLOBASA_FAST=0 runs the callers
on their Python path, which these tests use as the reference anyway.
"""
import os
import random
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

globasa_fast = pytest.importorskip("globasa_fast", reason="extension not built: ./setup.sh --fast")


# ---- align -----------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def forms():
    from word_selection import lexicon
    words = sorted(w for w in lexicon.words() if w.isascii() and w.isalpha() and w.islower())
    rng = random.Random(20261126)
    sample = rng.sample(words, 1500)
    # mutated copies: the near pairs clustering and blending compare most
    letters = "abcdefghijklmnoprstuvwxyz"
    mutants = []
    for w in sample[:500]:
        i = rng.randrange(len(w))
        mutants.append(w[:i] + rng.choice(letters) + w[i + 1:])
        mutants.append(w[:i] + w[i + 1:] or w)
    return sample + mutants + ["", "a", "mn", "nm", "nyan", "sanmen", "kwang", "ngu"]


def _configs():
    from word_selection import align as al
    return [
        dict(),
        dict(sub=al.sino_sub_cost),
        dict(sub=al.sino_sub_cost, coda=al._sino_coda, nasal_pos=al.NASAL_POS),
        dict(sub=al.sino_sub_cost, coda=al._sino_coda, nasal_pos=al.NASAL_POS, edge_gap=al.GAP),
        dict(nasal_pos=0.3, edge_gap=al.GAP),
    ]


def test_align_matches_python(forms):
    from word_selection import align as al
    rng = random.Random(7)
    pairs = [(rng.choice(forms), rng.choice(forms)) for _ in range(5000)]
    pairs += [(f, f) for f in forms[:200]]
    for cfg in _configs():
        assert al._rust("ab", "ab", cfg.get("sub"), cfg.get("coda"), cfg.get("nasal_pos", 0.0),
                        cfg.get("edge_gap", al.EDGE_GAP)) is not None
        for a, b in pairs:
            want = al.align_py(a, b, **cfg)
            got = al.align(a, b, **cfg)
            assert got[0] == want[0], (cfg, a, b, got[0], want[0])     # bit-identical cost
            assert got[1] == want[1], (cfg, a, b)
            assert al.align_cost(a, b, **cfg) == want[0]


def test_sino_distance_matches_python(forms):
    from word_selection import align as al
    rng = random.Random(11)
    langs = ["ja", "ko", "vi", "zh", "zh-pivot"]
    for _ in range(1500):
        la, lb = rng.choice(langs), rng.choice(langs)
        a, b = rng.choice(forms) or "a", rng.choice(forms) or "a"
        va, vb = al.sino_norm(la, a), al.sino_norm(lb, b)
        want = min(al.align_py(x, y, sub=al.sino_sub_cost, coda=al._sino_coda,
                               nasal_pos=al.NASAL_POS)[0] / max(len(x), len(y), 1)
                   for x in va for y in vb)
        # sino_distance also expands the ja long-vowel variants; compare on the same sets
        al_ = al._aligner(al.sino_sub_cost, "sino", al.NASAL_POS, al.EDGE_GAP)
        assert al_.min_norm_cost(list(va), list(vb)) == want, (la, a, lb, b)


def test_uncovered_letters_fall_back():
    from word_selection import align as al
    assert al._rust("café", "cafe", None, None, 0.0, al.EDGE_GAP) is None
    assert al.align("café", "cafe") == al.align_py("café", "cafe")


# ---- gestalt (difflib) ------------------------------------------------------------------------
@pytest.fixture(scope="module")
def edition_sentences():
    from pathlib import Path
    from edition_variants import sentences
    texts = {}
    for book in ("war-of-the-worlds", "time-machine"):
        d = Path(ROOT) / book / "text"
        texts[book] = (sentences(d / "heinemann.txt"), sentences(d / "atlantic.txt"))
    return texts


def test_gestalt_matches_difflib(edition_sentences):
    import difflib
    rng = random.Random(3)
    pairs = []
    for H, A in edition_sentences.values():
        for i in rng.sample(range(len(H)), 300):         # aligned neighbours: real near-matches
            c = int(i * len(A) / len(H))
            pairs += [(H[i], A[min(len(A) - 1, c + d)]) for d in (-1, 0, 1)]
        pairs += [(rng.choice(H), rng.choice(A)) for _ in range(300)]
    pairs += [("", ""), ("", "abc"), ("abc", ""), ("aaaa", "aa"), ("ab" * 150, "ba" * 150)]
    for a, b in pairs:
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        assert globasa_fast.real_quick_ratio(a, b) == sm.real_quick_ratio()
        assert globasa_fast.quick_ratio(a, b) == sm.quick_ratio()
        assert globasa_fast.matching_blocks(a, b) == [tuple(m) for m in sm.get_matching_blocks()]
        assert globasa_fast.ratio(a, b) == sm.ratio()


def test_best_matches_matches_python(edition_sentences):
    import edition_variants as ev
    H, A = edition_sentences["time-machine"]
    H, A = H[:250], A[:260]
    got = globasa_fast.best_matches(H, A, ev.WINDOW, ev.MIN_RATIO)
    assert got == ev.best_matches_py(H, A, ev.MIN_RATIO, ev.WINDOW)


# ---- mst (stanza's Chu-Liu-Edmonds) -----------------------------------------------------------
def _score_matrices(count, seed):
    import numpy as np
    rng = np.random.default_rng(seed)
    for t in range(count):
        n = int(rng.integers(2, 70))
        if t % 2:       # small integers: many ties and cycles
            m = rng.integers(-4, 4, (n, n)).astype(np.float64)
        else:           # log-probability-like, as the parser's
            m = rng.standard_normal((n, n)) * 3 - 5
        if t % 7 == 0:
            m[rng.random((n, n)) < 0.1] = -np.inf
        if t % 5 == 0:
            m = m.astype(np.float32)        # the parser's dtype
        yield m


def test_mst_matches_stanza():
    import numpy as np
    stanza_ce = pytest.importorskip("stanza.models.common.chuliu_edmonds")
    for m in _score_matrices(10000, 5):
        want = stanza_ce.chuliu_edmonds_one_root(m)
        got = globasa_fast.chuliu_edmonds_one_root(np.ascontiguousarray(m, dtype=np.float64))
        assert got is not None
        assert got.dtype == want.dtype and np.array_equal(got, want), m


def test_mst_nan_defers_to_stanza():
    import numpy as np
    m = np.zeros((4, 4)); m[1, 2] = np.nan
    assert globasa_fast.chuliu_edmonds_one_root(m) is None
