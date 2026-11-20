# Script tier: historical English (HistWords decade) -> modern English / Spanish / Esperanto
# (fastText Common Crawl, ~2017) -> Globasa. Proposes, decides nothing.
# Modern English (user, 2026-11-20): same-word pairs as seeds, so it measures each word's drift
# from the 1890s (and the 1990s) to today's web, past the end of Google Books HistWords.
#
# 1. Seed pairs = Wiktionary eng->X translations (../WiktionaryLMDB) of the 20k most frequent
#    HistWords words, kept only where the English word barely moved 1890s->1990s (bottom
#    STABLE_SHARE by aligned cosine distance), so shifted words do not bend the map.
# 2. Orthogonal Procrustes (unit-norm, mean-centred, unit-norm; Artetxe et al. 2018 normalisation)
#    from the English decade onto X; quality = precision@1/@5 with CSLS on held-out pairs.
# 3. For each TARGET: the English decade vector mapped into X, its CSLS-nearest X words, and the
#    Globasa entries whose TranslationSpa / TranslationEpo items contain those words
#    (vote = sum of neighbour similarities; both pivots shown side by side).
#    Part of speech (user, 2026-11-20): a Globasa word only counts for the PoS of the word-list
#    segment its item sits in (labels from TranslationEng: n, adj, v.*, adv), and only for a PoS
#    the TARGET has in TARGET_POS; multi-PoS targets get one candidate line per PoS (1890s fancy:
#    adj -> zarif, n 'imagination' -> imajeya), so a noun can no longer answer an adjective.
#
# Inputs: HistWords (histwords.py); X vectors as {lang}-vocab.txt + {lang}-w.npy made by
# fasttext_bin.extract() from facebook/fasttext-{lang}-vectors (CC BY-SA 3.0), folder FASTTEXT_DIR.
# Output: histwords_crossling_report.txt

import os
import re
import sys
from collections import defaultdict

import numpy as np
import pandas as pd

import histwords as hw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from wiktionary_db import WiktionaryDB

FASTTEXT_DIR = os.environ.get("FASTTEXT_DIR", "/media/paleos/Warehouse2/Language/Claude/fasttext")
LANGS = [l for l in ("en", "es", "eo") if os.path.exists(os.path.join(FASTTEXT_DIR, f"{l}-w.npy"))]
LANG_COL = {"en": "TranslationEng", "es": "TranslationSpa", "eo": "TranslationEpo"}
DECADES = [1890, 1990]
N_SOURCE = 20000         # English seed candidates (most frequent)
STABLE_SHARE = 0.6
N_TARGET = 100000        # target vocabulary searched
CSLS_K = 10
NN = 10
# PoS the target is checked for (English column labels; v = v.tr/v.intr/...). A type vector mixes
# all PoS, so words used in more than one keep each.
TARGET_POS = {"gay": ["adj"], "queer": ["adj"], "awful": ["adj"], "dumb": ["adj"], "intercourse": ["n"],
              "wanted": ["v", "adj"], "broadcast": ["v", "adj", "adv"], "film": ["n"], "tremendous": ["adj"],
              "terrific": ["adj"], "liberal": ["adj"], "race": ["n"], "man": ["n"], "presently": ["adv"],
              "fancy": ["adj", "n"], "nice": ["adj"], "sick": ["adj"], "cunning": ["adj", "n"],
              "mistress": ["n"], "car": ["n"], "tank": ["n"], "computer": ["n"], "checked": ["v", "adj"],
              "militant": ["adj", "n"], "weird": ["adj"], "fantastic": ["adj"]}
TARGETS = list(TARGET_POS)


def segments(cell):
    # same splitting as histwords_senses.segments: commas outside parentheses; returns
    # (item, annotated) so 'tanque (_militar_)' counts half (it is restricted to one domain);
    # one (label, items) per segment
    if not isinstance(cell, str):
        return []
    out = []
    for seg in cell.split(";"):
        m = re.match(r"\s*([^:(]{1,15}):\s*(.*)", seg)
        label, body = (m.group(1).strip(), m.group(2)) if m else ("", seg)
        items, depth, cur = [], 0, ""
        for ch in body + ",":
            depth += ch == "("
            depth -= ch == ")"
            if depth == 0 and ch in ",،、，":
                it = re.sub(r"\([^)]*\)", "", cur).strip().lower()
                if it:
                    items.append((it, "(" in cur))
                cur = ""
            else:
                cur += ch
        out.append((label, items))
    return out


def pos_of(label):
    # 'v.tr' -> 'v'; 'prop n', 'prep phrs' etc. -> None (never a candidate for a TARGET_POS)
    head = label.split(".")[0]
    return head if head in ("n", "adj", "v", "adv") else None


def normalise(x, present=None):
    # in place (memory, 2026-11-20): unit, mean-centre, unit; rows outside `present` (absent
    # words, all zero) stay zero and do not enter the mean
    x /= np.linalg.norm(x, axis=1, keepdims=True).clip(1e-8)
    n = len(x) if present is None else int(present.sum())
    x -= x.sum(axis=0) / max(n, 1)
    if present is not None:
        x[~present] = 0
    x /= np.linalg.norm(x, axis=1, keepdims=True).clip(1e-8)
    return x


def topk_mean(a, b, k, chunk=4096):
    out = np.empty(len(a), dtype=np.float32)
    for i in range(0, len(a), chunk):
        s = a[i:i + chunk] @ b.T
        out[i:i + chunk] = np.sort(np.partition(s, -k, axis=1)[:, -k:], axis=1).mean(axis=1)
    return out


wl = pd.read_csv(os.path.join(os.path.dirname(HERE), "word-list.csv"), index_col=0)
wl = wl[~wl.index.duplicated()]
db = WiktionaryDB(os.path.join(os.path.dirname(HERE), "WiktionaryLMDB"))

# English stability 1890s -> 1990s
vo, io, wo, co = hw.load(1890)
vn, inn, wn, cn = hw.load(1990)
src_words = [w for w in vn[:N_SOURCE * 2] if w in io and w in inn and w.isalpha()][:N_SOURCE]
R = hw.procrustes(1890, 1990, src_words)
dist = {w: 1 - float((wo[io[w]] @ R) @ wn[inn[w]]) for w in src_words}
stable = set(sorted(src_words, key=dist.get)[:int(len(src_words) * STABLE_SHARE)])

report = []
agree = defaultdict(lambda: defaultdict(set))       # (decade, word) -> glb -> {langs}
for lang in LANGS:
    tvocab = open(os.path.join(FASTTEXT_DIR, f"{lang}-vocab.txt"), encoding="utf-8").read().split("\n")[:N_TARGET]
    keep = list(range(len(tvocab)))
    if lang == "en":
        # web tokens like "man.The", "car." and capitalised duplicates: lowercase alphabetic only
        keep = [i for i, w in enumerate(tvocab) if w.isalpha() and w.islower()]
    if lang == "eo":
        # Esperanto neighbours are mostly inflections (gaja -> gajaj, tanko -> tankon); the word
        # list's Epo column holds dictionary forms, so search lowercase -o/-a/-e/-i forms only
        keep = [i for i, w in enumerate(tvocab) if w.islower() and re.fullmatch(r"\w+[oaei]", w)]
    tvocab = [tvocab[i] for i in keep]
    # only the kept rows are read from the memory-mapped file
    tw = normalise(np.asarray(np.load(os.path.join(FASTTEXT_DIR, f"{lang}-w.npy"), mmap_mode="r")[keep],
                              dtype=np.float32))
    tindex = {w: i for i, w in enumerate(tvocab) if w}

    # item -> {(globasa word, pos): weight}; the PoS comes from the English column's label for the
    # segment at the same position ('*' = segment counts differ, PoS unknown: counts for any PoS)
    glb_of = defaultdict(dict)
    for g, row in wl.iterrows():
        pos_seq = [pos_of(lab) for lab, _ in segments(row["TranslationEng"])]
        segs = segments(row[LANG_COL[lang]])
        for i, (_, items) in enumerate(segs):
            p = pos_seq[i] if len(segs) == len(pos_seq) else "*"
            if p is None:
                continue
            for it, note in items:
                glb_of[it][(g, p)] = max(glb_of[it].get((g, p), 0), 0.5 if note else 1.0)

    pairs = []
    for w in sorted(stable):
        if lang == "en":                                       # identity seeds: the stable word itself
            if w in tindex:
                pairs.append((w, w))
            continue
        for pos in ("noun", "verb", "adj", "adv"):
            for _, langs in (db.get_translations(w, pos) or {}).items():
                for t in langs.get(lang, ()):
                    t = t.word.lower()
                    if t in tindex:
                        pairs.append((w, t))
    pairs = sorted(set(pairs))
    rng = np.random.default_rng(0)
    test_src = set(rng.choice(sorted({p[0] for p in pairs}), size=500, replace=False))
    train = [p for p in pairs if p[0] not in test_src]
    test = defaultdict(set)
    for s, t in pairs:
        if s in test_src:
            test[s].add(t)
    report.append(f"== {lang}: {len(pairs)} seed pairs from {len(stable)} stable English words; "
                  f"{len(train)} train, {len(test)} held-out English words")

    for decade in DECADES:
        sv, si, sw, _ = hw.load(decade)
        present = np.array([v in si for v in sv])
        srcmat = normalise(sw.copy(), present)                 # absent words stay zero rows
        present = np.flatnonzero(present).tolist()
        tr = [(s, t) for s, t in train if s in si]
        a = srcmat[[si[s] for s, _ in tr]]
        b = tw[[tindex[t] for _, t in tr]]
        u, _, vt = np.linalg.svd(a.T @ b)
        W = u @ vt
        mapped = srcmat @ W
        r_t = topk_mean(tw, mapped[present[:50000]], CSLS_K)   # target hubness

        def nearest(word, k=NN):
            x = mapped[si[word]]
            sims = tw @ x
            r_s = np.sort(sims)[-CSLS_K:].mean()
            csls = 2 * sims - r_s - r_t
            top = np.argsort(-csls)[:k]
            return [(tvocab[i], float(sims[i])) for i in top]

        hits1 = hits5 = n = 0
        for s, golds in test.items():
            if s not in si:
                continue
            nb = [w for w, _ in nearest(s, 5)]
            n += 1
            hits1 += nb[0] in golds
            hits5 += any(w in golds for w in nb)
        report.append(f"   {decade}s English -> {lang}: P@1 {hits1 / n:.2f}, P@5 {hits5 / n:.2f} on {n} held-out words")

        for word in TARGETS:
            if word not in si:
                continue
            nb = nearest(word)
            extra = ""
            if lang == "en" and word in tindex:                  # drift: decade vector vs today's vector
                today = tw[tindex[word]]
                sims = tw @ mapped[si[word]]
                extra = f" (cos to today {float(today @ mapped[si[word]]):.2f}, today's form ranks {int((sims > sims[tindex[word]]).sum()) + 1})"
            report.append(f"   [{decade}s] {word:12s}{extra} -> " + ", ".join(w for w, _ in nb))
            for want in TARGET_POS[word]:
                votes = defaultdict(float)
                via = defaultdict(list)
                for w, s in nb:
                    for (g, p), weight in glb_of.get(w, {}).items():
                        if p == want or p == "*":
                            votes[g] += s * weight
                            via[g].append(w)
                glb = sorted(votes, key=lambda g: -votes[g])[:4]
                for g in glb:
                    agree[(decade, word, want)][g].add(lang)
                if glb:
                    report.append(" " * 25 + f"glb {want}: " + "; ".join(f"{g} ({'/'.join(via[g])})" for g in glb))

report.append("\n== agreement: Globasa words proposed by 2+ pivots (en/es/eo) per decade and PoS")
for word in TARGETS:
    for decade in DECADES:
        for want in TARGET_POS[word]:
            both = {g: l for g, l in agree[(decade, word, want)].items() if len(l) >= 2}
            if both:
                report.append(f"   [{decade}s] {word + ' ' + want:16s} " + "; ".join(
                    f"{g} ({'+'.join(sorted(l))})" for g, l in sorted(both.items(), key=lambda x: -len(x[1]))))
out = "\n".join(report) + "\n"
open(os.path.join(HERE, "histwords_crossling_report.txt"), "w", encoding="utf-8").write(out)
print(out)
