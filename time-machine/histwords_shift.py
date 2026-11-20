# Script tier (proposes, decides nothing): rank the words of The Time Machine by how far
# their HistWords embedding moved between the decade the book was written (1890s) and the
# 1990s. A high rank means "check this word's sense in context"; it is never a substitution.
#
# Two measures, both from Hamilton, Leskovec & Jurafsky 2016 (ACL; global) and Hamilton,
# Leskovec & Jurafsky 2016 (EMNLP, "Cultural shift or linguistic drift"; local):
#   global = cosine distance of the word's vector after orthogonal Procrustes alignment
#   local  = cosine distance between the word's similarity profiles over the union of its
#            k nearest neighbours in both decades (no alignment; tracks cultural/sense shifts)
#   loss   = how far the word moved away from its OWN 1890s neighbours (mean similarity to them in
#            the 1890s minus the same in the 1990s). A lost sense is what misleads a modern reader/MT;
#            a gained sense (click, antenna) usually leaves the old one intact. Rows are sorted by loss.
#   gain   = the same from the 1990s neighbours' side (a new sense appeared).
#   score  = mean z of global and local (kept for comparison).
# Words below MIN_PER_MILLION in either decade get noise vectors (their 1990s neighbours are random
# rare words: loth, dexterous) and are dropped. First run (2026-11-20): of the top 70 by loss, 3 were
# dated senses in the book (gay, checked, militant); most others are topical or gained-sense hits.
#
# Inputs: text/heinemann.txt, HistWords (see histwords.py), obscure_resolved.tsv and
# victorian_wordlist.tsv (only to label rows already covered). Output: histwords_shift.tsv
# (all scored words, sorted by loss) and histwords_eval.txt (how the known dated senses rank).

import collections
import csv
import os
import re

import numpy as np
from spacy.lang.en.stop_words import STOP_WORDS

import histwords as hw

HERE = os.path.dirname(os.path.abspath(__file__))
YEAR = 1895
OLD, NEW = hw.decade_of(YEAR), 1990
MIN_COUNT = 500          # occurrences per decade in Google Books (Hamilton's threshold)
MIN_PER_MILLION = 0.5    # relative frequency floor in both decades (below this vectors are noise)
K = 25                   # neighbours for the local measure
N_ANCHORS = 20000        # most frequent shared words used for Procrustes

text = open(os.path.join(HERE, "text", "heinemann.txt"), encoding="utf-8").read()
text = re.sub(r"^## .*$", "", text, flags=re.M)
tokens = re.findall(r"[A-Za-z]+(?:'[a-z]+)?", text)
tm_count = collections.Counter(t.lower() for t in tokens)
capital = collections.Counter(t.lower() for t in tokens if t[0].isupper())

# first context per word
sentences = re.split(r"(?<=[.!?])\s+", text)
first_ctx = {}
for s in sentences:
    for t in set(re.findall(r"[a-z]+", s.lower())):
        first_ctx.setdefault(t, " ".join(s.split())[:200])

glossary = {}
with open(os.path.join(HERE, "obscure_resolved.tsv"), encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        glossary[r["lemma"].lower()] = "resolved:" + r["verdict"]
with open(os.path.join(HERE, "victorian_wordlist.tsv"), encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        h = r["headword"].lower()
        if " " not in h:
            glossary.setdefault(h, "wordlist:" + r["apertium"])

vo, io, wo, co = hw.load(OLD)
vn, inn, wn, cn = hw.load(NEW)

tot_o, tot_n = sum(co.values()), sum(cn.values())
shared = [v for v in vo if v in io and v in inn]
anchors = sorted(shared, key=lambda v: -(co.get(v, 0) + cn.get(v, 0)))[:N_ANCHORS]
R = hw.procrustes(OLD, NEW, anchors)
wo_al = wo @ R

cands = []
for wd, n in tm_count.items():
    if wd in STOP_WORDS or len(wd) < 3:
        continue
    if capital[wd] > n / 2:          # mostly capitalised in the text: a name or sentence-initial only
        continue
    if wd not in io or wd not in inn:
        continue
    if co.get(wd, 0) < MIN_COUNT or cn.get(wd, 0) < MIN_COUNT:
        continue
    if co[wd] / tot_o * 1e6 < MIN_PER_MILLION or cn[wd] / tot_n * 1e6 < MIN_PER_MILLION:
        continue
    cands.append(wd)


def topk(w, index, vec, k):
    s = w @ vec
    order = np.argsort(-s)[:k + 1]
    return [i for i in order if s[i] < 0.9999][:k]


rows = []
for wd in cands:
    a, b = io[wd], inn[wd]
    glob = 1 - float(wo_al[a] @ wn[b])
    nn_o = [vo[i] for i in topk(wo, io, wo[a], K)]
    nn_n = [vn[i] for i in topk(wn, inn, wn[b], K)]
    union = [u for u in dict.fromkeys(nn_o + nn_n) if u in io and u in inn and u != wd]
    so = wo[[io[u] for u in union]] @ wo[a]
    sn = wn[[inn[u] for u in union]] @ wn[b]
    loc = 1 - float(so @ sn / (np.linalg.norm(so) * np.linalg.norm(sn)))
    old_nb = [u for u in nn_o[:10] if u in inn]
    new_nb = [u for u in nn_n[:10] if u in io]
    loss = float(np.mean(wo[[io[u] for u in old_nb]] @ wo[a]) - np.mean(wn[[inn[u] for u in old_nb]] @ wn[b])) if old_nb else 0.0
    gain = float(np.mean(wn[[inn[u] for u in new_nb]] @ wn[b]) - np.mean(wo[[io[u] for u in new_nb]] @ wo[a])) if new_nb else 0.0
    rows.append([wd, tm_count[wd], co.get(wd, 0), cn.get(wd, 0), glob, loc, nn_o[:8], nn_n[:8], loss, gain])

g = np.array([r[4] for r in rows])
l = np.array([r[5] for r in rows])
z = ((g - g.mean()) / g.std() + (l - l.mean()) / l.std()) / 2
order = np.argsort([-r[8] for r in rows])

with open(os.path.join(HERE, "histwords_shift.tsv"), "w", encoding="utf-8") as f:
    f.write("\t".join(["rank", "word", "loss", "gain", "score", "global", "local", "tm_count", f"gb_{OLD}", f"gb_{NEW}",
                       "glossary", f"nn_{OLD}", f"nn_{NEW}", "first_context"]) + "\n")
    for rank, i in enumerate(order, 1):
        wd, n, c1, c2, glob, loc, nn_o, nn_n, loss, gain = rows[i]
        f.write("\t".join([str(rank), wd, f"{loss:.3f}", f"{gain:.3f}", f"{z[i]:.2f}", f"{glob:.3f}", f"{loc:.3f}", str(n), str(c1), str(c2),
                           glossary.get(wd, ""), ", ".join(nn_o), ", ".join(nn_n),
                           first_ctx.get(wd, "").replace("\t", " ")]) + "\n")

# How do words a human reader already marked as dated senses rank?
rank_of = {rows[i][0]: r for r, i in enumerate(order, 1)}
known = sorted(w for w, v in glossary.items() if v == "resolved:dated_sense")
scored = [w for w in known if w in rank_of]
with open(os.path.join(HERE, "histwords_eval.txt"), "w", encoding="utf-8") as f:
    f.write(f"{len(rows)} words scored ({OLD}s vs {NEW}s, count >= {MIN_COUNT} in both decades)\n")
    f.write(f"dated_sense rows in obscure_resolved.tsv: {len(known)}; single words scored: {len(scored)}\n")
    for cut in (50, 100, 200, 500):
        hit = sum(rank_of[w] <= cut for w in scored)
        f.write(f"  in top {cut}: {hit}\n")
    if scored:
        f.write(f"  median percentile: {np.median([rank_of[w] / len(rows) for w in scored]) * 100:.0f}\n")
    for w in sorted(scored, key=rank_of.get):
        f.write(f"  {rank_of[w]:5d}  {w}\n")
print(open(os.path.join(HERE, "histwords_eval.txt")).read())
