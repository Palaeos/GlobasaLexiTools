# Script tier: HistWords switch-over decades for English words whose senses compete in the
# period view (an ended sense and a current one, vetted or curated), to make the year ranges of
# apply_eng_periods.py more precise (user 2026-11-20: use HistWords to improve the ranges).
#
#   venv/bin/python histwords_ranges.py
#
# For each such word and each decade 1800-1990 (time-machine/histwords.py, one decade in memory
# at a time): every sense gets probe words (content words of its gloss, frequent in the 1990s,
# minus words shared with the word's other senses); the sense's score in a decade is the mean
# cosine between the word and its probes in that decade's own space. A sense is dominant in a
# decade when it leads the next sense by MARGIN, smoothed over three decades.
#   rise  first decade a sense is dominant (after another sense was)
#   fall  last decade an ended sense is dominant
# Only clean switches are written (the old sense dominant first, the new one after, no flapping).
#
# Output: histwords_ranges.tsv (glb, eng, pos, gloss, status, rise, fall, scores per decade)
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from spacy.lang.en.stop_words import STOP_WORDS

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "time-machine"))
import histwords as hw

PERIODS = HERE / "sense_periods_draft.tsv"
OUT = HERE / "histwords_ranges.tsv"
ENDING = {"obsolete", "archaic", "dated", "historical"}
MARGIN = 0.02
MIN_PER_MILLION = 1.0

# senses per English word: vetted + curated, at least one ended and one current
words = defaultdict(list)
with open(PERIODS, encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        if r["source"] in ("vetted", "curated") and r["glb"] and (r["gloss"] or r["label"]):
            words[(r["eng"], r["pos"])].append(r)
words = {k: rs for k, rs in words.items()
         if " " not in k[0] and any(r["status"] in ENDING for r in rs) and any(r["status"] not in ENDING for r in rs)}

_, idx90, _, c90 = hw.load(1990)
total90 = sum(c90.values())
hw.release(1990)


def probes(text, word):
    return {w for w in re.findall(r"[a-z]+", text.lower())
            if w not in STOP_WORDS and w != word and len(w) > 2 and c90.get(w, 0) / total90 * 1e6 >= MIN_PER_MILLION}


plan = {}
for (eng, pos), rs in words.items():
    sets = [probes(r["gloss"] + " " + r["label"], eng) for r in rs]
    shared = set.intersection(*sets) if len(sets) > 1 else set()
    sets = [s - shared for s in sets]
    if sum(1 for s in sets if s) >= 2:
        plan[(eng, pos)] = (rs, sets)

scores = defaultdict(dict)                     # (eng, pos, i) -> {decade: score}
for decade in hw.DECADES:
    _, index, w, _ = hw.load(decade)
    for (eng, pos), (rs, sets) in plan.items():
        if eng not in index:
            continue
        v = w[index[eng]]
        for i, s in enumerate(sets):
            vecs = [w[index[p]] for p in s if p in index]
            if vecs:
                scores[(eng, pos, i)][decade] = float(np.mean(np.stack(vecs) @ v))
    hw.release(decade)
    print(f"  {decade}s", flush=True)


def dominant(eng, pos, n):
    # decade -> index of the dominant sense (or None), on three-decade means
    out = {}
    for k, d in enumerate(hw.DECADES):
        window = hw.DECADES[max(0, k - 1): k + 2]
        means = []
        for i in range(n):
            vals = [scores[(eng, pos, i)].get(x) for x in window]
            vals = [x for x in vals if x is not None]
            means.append(np.mean(vals) if vals else None)
        if sum(m is not None for m in means) < 2:
            out[d] = None
            continue
        order = sorted((m, i) for i, m in enumerate(means) if m is not None)[::-1]
        out[d] = order[0][1] if order[0][0] - order[1][0] >= MARGIN else None
    return out


rows = []
for (eng, pos), (rs, sets) in plan.items():
    dom = dominant(eng, pos, len(rs))
    seq = [(d, i) for d, i in dom.items() if i is not None]
    if not seq:
        continue
    runs = []                                   # [(sense index, first decade, last decade)]
    for d, i in seq:
        if runs and runs[-1][0] == i:
            runs[-1][2] = d
        else:
            runs.append([i, d, d])
    # clean switch only: each sense dominates in one run, an ended sense before a current one
    if len(runs) < 2 or len({r[0] for r in runs}) != len(runs):
        continue
    if not any(rs[a[0]]["status"] in ENDING and rs[b[0]]["status"] not in ENDING for a, b in zip(runs, runs[1:])):
        continue
    for i, first, last in runs:
        r = rs[i]
        rows.append({"glb": r["glb"], "eng": eng, "pos": pos, "gloss": r["gloss"] or r["label"],
                     "status": r["status"], "rise": first if i != runs[0][0] else "",
                     "fall": last if r["status"] in ENDING and i != runs[-1][0] else "",
                     "scores": " ".join(f"{d}:{scores[(eng, pos, i)].get(d, float('nan')):.2f}" for d in hw.DECADES[::2])})

with open(OUT, "w", encoding="utf-8", newline="") as f:
    wr = csv.DictWriter(f, ["glb", "eng", "pos", "gloss", "status", "rise", "fall", "scores"], delimiter="\t",
                        lineterminator="\n")
    wr.writeheader()
    wr.writerows(rows)
print(f"{len(words)} words with an ended and a current sense; {len(plan)} with probes; "
      f"{len({(r['eng'], r['pos']) for r in rows})} clean switches -> {OUT.name}")
for r in rows:
    print(f"  {r['eng']:12} {r['glb']:12} {r['status']:9} rise {r['rise'] or '-':5} fall {r['fall'] or '-':5} {r['gloss'][:50]}")
