# Shared HistWords loader (functions only: safe to import).
# HistWords = Hamilton, Leskovec & Jurafsky 2016, "Diachronic Word Embeddings Reveal
# Statistical Laws of Semantic Change" (ACL). SGNS embeddings per decade 1800-1990
# from Google Books Ngrams (eng-all), 100k words x 300 dims. Code and data: Apache-2.0
# (github.com/williamleif/histwords). Files: http://snap.stanford.edu/historical_embeddings/
#
# Files are too big for the repo (240 MB per decade). Default location is
# /media/paleos/Warehouse2/Language/Claude/histwords/eng-all (fetched by refetch.sh there);
# set HISTWORDS_DIR to use another folder. Per decade: {y}-vocab.pkl, {y}-w.npy,
# {y}-counts.pkl as downloaded from eng-all/sgns and eng-all/counts.

import os
import pickle

import numpy as np

# large downloaded data lives on the Warehouse2 drive (the repo disk is nearly full)
HISTWORDS_DIR = os.environ.get("HISTWORDS_DIR", "/media/paleos/Warehouse2/Language/Claude/histwords/eng-all")
DECADES = list(range(1800, 2000, 10))

_cache = {}


def decade_of(year):
    return max(1800, min(1990, int(year) // 10 * 10))


def load(decade):
    """Return (vocab list, index dict, unit-normalised matrix, counts dict) for one decade.
    Words absent in a decade have all-zero rows; they are left out of the index.
    Memory: float32 (120 MB per decade), normalised in place; release(decade) drops a cached
    decade when a script walks through many."""
    if decade in _cache:
        return _cache[decade]
    with open(os.path.join(HISTWORDS_DIR, f"{decade}-vocab.pkl"), "rb") as f:
        vocab = pickle.load(f, encoding="latin1")
    w = np.load(os.path.join(HISTWORDS_DIR, f"{decade}-w.npy"), mmap_mode="r").astype(np.float32)
    norms = np.linalg.norm(w, axis=1)
    present = norms > 0
    norms[~present] = 1
    w /= norms[:, None]
    index = {v: i for i, v in enumerate(vocab) if present[i]}
    counts = {}
    p = os.path.join(HISTWORDS_DIR, f"{decade}-counts.pkl")
    if os.path.exists(p):
        with open(p, "rb") as f:
            counts = pickle.load(f, encoding="latin1")
    _cache[decade] = (vocab, index, w, counts)
    return _cache[decade]


def release(decade):
    _cache.pop(decade, None)


def neighbours(decade, word, k=10, restrict=None):
    """Top-k cosine neighbours of word in a decade (optionally only among words in `restrict`)."""
    vocab, index, w, _ = load(decade)
    if word not in index:
        return []
    sims = w @ w[index[word]]
    sims[index[word]] = -2
    if restrict is not None:
        mask = np.full(len(vocab), False)
        for r in restrict:
            if r in index:
                mask[index[r]] = True
        sims[~mask] = -2
    top = np.argsort(-sims)[:k]
    return [(vocab[i], float(sims[i])) for i in top if sims[i] > -2]


def sim(decade, a, b):
    _, index, w, _ = load(decade)
    if a not in index or b not in index:
        return None
    return float(w[index[a]] @ w[index[b]])


def procrustes(d_from, d_to, anchors):
    """Orthogonal map R so that W_from @ R ~ W_to over shared anchor words (Hamilton 2016)."""
    _, i1, w1, _ = load(d_from)
    _, i2, w2, _ = load(d_to)
    shared = [a for a in anchors if a in i1 and a in i2]
    a = w1[[i1[s] for s in shared]]
    b = w2[[i2[s] for s in shared]]
    u, _, vt = np.linalg.svd(a.T @ b)
    return u @ vt
