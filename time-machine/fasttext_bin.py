# Read a fastText .bin model (e.g. facebook/fasttext-es-vectors on Hugging Face, CC BY-SA 3.0)
# without the fasttext package, and write the top-N word vectors as {out}-vocab.txt + {out}-w.npy
# (float32, unit-normalised). Functions only: safe to import.
#
# A word vector is computed as fastText's getWordVector does (= the .vec file): the mean of the
# word's own input row and the rows of its character n-grams (minn..maxn over "<word>",
# FNV-1a hash with signed-char bytes, mod bucket).

import struct

import numpy as np

CHUNK_ROWS = 100000      # rows of the input matrix read at a time (~120 MB at dim 300)


def _hash(b):
    h = 2166136261
    for c in b:
        h ^= (c - 256 if c > 127 else c) & 0xFFFFFFFF   # int8 -> uint32, as in fastText
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def _ngrams(word, minn, maxn):
    w = ("<" + word + ">").encode("utf-8")
    out = []
    for i in range(len(w)):
        if (w[i] & 0xC0) == 0x80:
            continue
        j, n = i, 1
        while j < len(w) and n <= maxn:
            j += 1
            while j < len(w) and (w[j] & 0xC0) == 0x80:
                j += 1
            if n >= minn and not (n == 1 and (i == 0 or j == len(w))):
                out.append(w[i:j])
            n += 1
    return out


def read_bin(path, top_n=200000):
    with open(path, "rb") as f:
        magic, version = struct.unpack("<ii", f.read(8))
        assert magic == 793712314, "not a fastText .bin"
        (dim, ws, epoch, min_count, neg, word_ngrams, loss, model, bucket, minn, maxn,
         lr_update) = struct.unpack("<12i", f.read(48))
        f.read(8)                                           # t (double)
        size, nwords, nlabels = struct.unpack("<iii", f.read(12))
        ntokens, prune_size = struct.unpack("<qq", f.read(16))
        words = []
        buf = f.read(64 << 20)
        pos = 0
        for _ in range(size):
            end = buf.find(b"\0", pos)
            while end < 0:                                  # entry crosses the buffer: read more
                buf = buf[pos:] + f.read(64 << 20)
                pos = 0
                end = buf.find(b"\0", pos)
            if end + 9 > len(buf):
                buf = buf[pos:] + f.read(64 << 20)
                end -= pos
                pos = 0
            if len(words) < top_n:                          # only the words returned are kept
                words.append(buf[pos:end].decode("utf-8", "replace"))
            pos = end + 1 + 9                               # count int64 + type int8
        rest = buf[pos:]
        offset = f.tell() - len(rest)
        prune = {}
        f.seek(offset)
        if prune_size > 0:
            data = struct.unpack(f"<{2 * prune_size}i", f.read(8 * prune_size))
            prune = dict(zip(data[0::2], data[1::2]))
        quant = f.read(1)
        assert quant == b"\0", "quantised models not supported"
        m, n = struct.unpack("<qq", f.read(16))
        assert n == dim
        mat_offset = f.tell()
    # Only what is needed (user, 2026-11-20): the input matrix (~4.8 GB for the cc models) is
    # streamed in CHUNK_ROWS slices; each slice adds its rows to the words that use them. Peak
    # RAM = the output (top_n x dim float32) + one slice + the (word, row) pairs. Scattered memmap
    # reads took > 50 min under load; whole-matrix np.fromfile helped exhaust the RAM.
    vocab = words[:min(top_n, nwords)]
    wid, rid = [], []
    for k, w in enumerate(vocab):
        rows = [k]
        if prune_size != 0:
            for g in _ngrams(w, minn, maxn):
                h = _hash(g) % bucket
                if prune_size > 0:
                    if h not in prune:
                        continue
                    h = prune[h]
                rows.append(nwords + h)
        wid += [k] * len(rows)
        rid += rows
    wid = np.asarray(wid, dtype=np.int32)
    rid = np.asarray(rid, dtype=np.int64)
    order = np.argsort(rid, kind="stable")
    wid, rid = wid[order], rid[order]
    n_rows = np.bincount(wid, minlength=len(vocab)).astype(np.float32)
    out = np.zeros((len(vocab), dim), dtype=np.float32)
    needed = np.unique(rid)
    for start in range(0, m, CHUNK_ROWS):
        stop = min(m, start + CHUNK_ROWS)
        lo, hi = np.searchsorted(rid, [start, stop])
        if lo == hi:
            continue
        first = needed[np.searchsorted(needed, start)]          # skip the unneeded head of the slice
        last = rid[hi - 1] + 1
        chunk = np.fromfile(path, dtype=np.float32, count=(last - first) * n,
                            offset=mat_offset + first * n * 4).reshape(-1, n)
        np.add.at(out, wid[lo:hi], chunk[rid[lo:hi] - first])
        del chunk
        print(f"  rows {start}-{stop} of {m}", flush=True)
    out /= n_rows[:, None]
    out /= np.linalg.norm(out, axis=1, keepdims=True).clip(1e-8)
    return vocab, out


def extract(path, out_prefix, top_n=200000):
    vocab, w = read_bin(path, top_n)
    with open(out_prefix + "-vocab.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(vocab) + "\n")
    np.save(out_prefix + "-w.npy", w)
    return len(vocab)
