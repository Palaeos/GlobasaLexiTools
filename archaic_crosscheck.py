# Script tier: cross-check archaic_senses.tsv with modern Spanish and Esperanto embeddings.
# Flags and orders; never chooses a Globasa word on its own (embedding neighbourhoods put deaf
# next to mute: dumb -> orenenabil, 2026-11-20).
#
#   FASTTEXT_DIR=... venv/bin/python archaic_crosscheck.py
#
# 1. Modern English fastText is mapped onto es and eo (orthogonal Procrustes, Artetxe
#    normalisation as in time-machine/histwords_crossling.py) with Wiktionary eng->X translations
#    of the SEED_N most frequent English words as seed pairs; held-out P@1 is reported.
# 2. A period sense = the weighted mean of its definition's content words, mapped into X (the
#    definition is written in modern English; rarer words weigh more, the headword is left out).
# 3. A Globasa candidate = the mean of its TranslationSpa / TranslationEpo items in the segment of
#    the sense's PoS (PoS from the TranslationEng label at the same position).
# 4. sim = cosine(sense, candidate) per language. Per row:
#      ok        the proposal's first candidate is the best candidate in es and eo, sim >= SIM_OK[lang]
#      low       the first candidate is best but below SIM_OK[lang] in a language (check by hand)
#      other     both languages prefer the same other candidate (named in emb_best)
#      split     es and eo disagree
#      n/a       no vector for the sense or the candidates
#
# Inputs: archaic_senses.tsv (archaic_senses.py), word-list.csv, WiktionaryLMDB,
#         FASTTEXT_DIR/{en,es,eo}-vocab.txt + -w.npy (time-machine/fasttext_bin.extract)
# Output: archaic_crosscheck.tsv (archaic_senses.tsv + es/eo columns), archaic_crosscheck_report.txt
import csv
import math
import os
import re
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

from wiktionary_db import WiktionaryDB

HERE = os.path.dirname(os.path.abspath(__file__))
FASTTEXT_DIR = os.environ.get("FASTTEXT_DIR", "/media/paleos/Warehouse2/Language/Claude/fasttext")
LANGS = {"es": "TranslationSpa", "eo": "TranslationEpo"}
POS_LABEL = {"noun": "n", "verb": "v", "adj": "adj", "adv": "adv"}
SEED_N = 20000
N_VOCAB = 200000
# per language: about the 5th percentile of the A rows (table and definition agree), first run
# 2026-11-20: es A p5 0.45, eo A p5 0.28 (the eo map is weaker: held-out P@1 0.44 vs es 0.73)
SIM_OK = {"es": 0.40, "eo": 0.25}
STOP = set("a an the of or and in for to is are was were be been being by with at on from as it its that this "
           "which who whom one something someone some any very such into not no also used especially "
           "etc person thing way".split())


def load(lang, keep):
    # only the rows keep(word) accepts, copied once from the memory-mapped file and normalised in
    # place (RAM ran out on 2026-11-20: no full-size zero matrices or float64 temporaries)
    vocab = open(os.path.join(FASTTEXT_DIR, f"{lang}-vocab.txt"), encoding="utf-8").read().split("\n")[:N_VOCAB]
    rows = [i for i, v in enumerate(vocab) if v and keep(v)]
    w = np.asarray(np.load(os.path.join(FASTTEXT_DIR, f"{lang}-w.npy"), mmap_mode="r")[rows], dtype=np.float32)
    normalise(w)
    words = [vocab[i] for i in rows]
    index = {}
    for i, v in enumerate(words):
        index.setdefault(v, i)
    return words, index, w


def normalise(x):
    # in place: unit length, mean-centre, unit length (Artetxe et al. 2018)
    x /= np.linalg.norm(x, axis=1, keepdims=True).clip(1e-8)
    x -= x.mean(axis=0)
    x /= np.linalg.norm(x, axis=1, keepdims=True).clip(1e-8)


def unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 0 else None


def segments(cell):
    # (label, [items]) per ';' segment; commas outside parentheses; parentheticals dropped
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
            if depth == 0 and ch == ",":
                it = re.sub(r"\([^)]*\)", "", cur).strip().lower()
                if it:
                    items.append(it)
                cur = ""
            else:
                cur += ch
        out.append((label, items))
    return out


def items_for(glb, lang, pos):
    # the glb word's items in LANGS[lang], in the segment whose English label has this PoS
    if glb not in wl.index:
        return []
    eng = [lab.split(".")[0] for lab, _ in segments(wl.at[glb, "TranslationEng"])]
    segs = segments(wl.at[glb, LANGS[lang]])
    if len(segs) != len(eng):
        return [it for _, its in segs for it in its]
    return [it for p, (_, its) in zip(eng, segs) if p == POS_LABEL[pos] for it in its]


wl = pd.read_csv(os.path.join(HERE, "word-list.csv"), index_col=0)
wl = wl[~wl.index.duplicated()]
db = WiktionaryDB(os.path.join(HERE, "WiktionaryLMDB"))

ev, ei, ewn = load("en", lambda w: w.isalpha() and w.islower())   # web tokens "man.The" out
seed_words = ev[:SEED_N]

spaces, report = {}, []
for lang in LANGS:
    tv, ti, twn = load(lang, str.islower)
    pairs = set()
    for w in seed_words:
        for pos in POS_LABEL:
            for _, langs in (db.get_translations(w, pos) or {}).items():
                for t in langs.get(lang, ()):
                    t = t.word.lower()
                    if t in ti:
                        pairs.add((w, t))
    pairs = sorted(pairs)
    rng = np.random.default_rng(0)
    test_src = set(rng.choice(sorted({s for s, _ in pairs}), size=500, replace=False))
    train = [p for p in pairs if p[0] not in test_src]
    u, _, vt = np.linalg.svd(ewn[[ei[s] for s, _ in train]].T @ twn[[ti[t] for _, t in train]])
    W = u @ vt
    gold = defaultdict(set)
    for s, t in pairs:
        if s in test_src:
            gold[s].add(t)
    hits = sum(tv[int(np.argmax(twn @ (ewn[ei[s]] @ W)))] in g for s, g in gold.items())
    report.append(f"en -> {lang}: {len(train)} seed pairs, held-out P@1 {hits / len(gold):.2f} ({len(gold)} words)")
    spaces[lang] = (ti, twn, W)


def sense_vec(eng, gloss):
    words = [w for w in re.findall(r"[a-z]+", re.sub(r"\([^)]*\)", " ", gloss.lower()))
             if w not in STOP and w != eng and len(w) > 2 and w in ei]
    if not words:
        return None
    v = sum(ewn[ei[w]] * min(1.0, math.log10(ei[w] + 10) / 4) for w in words)
    return unit(v)


def cand_vec(glb, lang, pos):
    ti, twn, _ = spaces[lang]
    vs = []
    for it in items_for(glb, lang, pos):
        ws = [w for w in re.findall(r"\w+", it) if w in ti and w not in ("se", "de", "la", "el")]
        if ws:
            vs.append(unit(sum(twn[ti[w]] for w in ws)))
    vs = [v for v in vs if v is not None]
    return unit(sum(vs)) if vs else None


def candidates(row):
    out = []
    m = re.match(r"(.+?) \(\d+ langs\)", row["table"])
    if m:
        out.append(m.group(1))
    for part in row["gloss_glb"].split("; "):
        g = re.sub(r" \([^)]*\)$", "", part).strip()
        if g and g not in out:
            out.append(g)
    return out


rows = list(csv.DictReader(open(os.path.join(HERE, "archaic_senses.tsv"), encoding="utf-8"), delimiter="\t"))
stats = Counter()
for r in rows:
    cands = candidates(r)
    sv = sense_vec(r["eng"], r["gloss"])
    best, sims = {}, {}
    for lang, (ti, twn, W) in spaces.items():
        if sv is None:
            continue
        s_x = unit(sv @ W)
        scored = []
        for g in cands:
            cv = cand_vec(g, lang, r["pos"])
            if cv is not None:
                scored.append((float(s_x @ cv), g))
        scored.sort(reverse=True)
        sims[lang] = scored
        if scored:
            best[lang] = scored[0]
    first = cands[0] if cands else ""
    if len(best) < 2:
        verdict = "n/a"
    elif best["es"][1] == best["eo"][1] == first:
        verdict = "ok" if all(best[l][0] >= SIM_OK[l] for l in LANGS) else "low"
    elif best["es"][1] == best["eo"][1]:
        verdict = "other"
    else:
        verdict = "split"
    r["emb"] = verdict
    r["emb_best"] = best["es"][1] if verdict == "other" else ""
    for lang in LANGS:
        r[f"{lang}_sims"] = "; ".join(f"{g} {s:.2f}" for s, g in sims.get(lang, []))
    stats[(r["strength"][0], verdict)] += 1

cols = list(rows[0].keys())
with open(os.path.join(HERE, "archaic_crosscheck.tsv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, cols, delimiter="\t", lineterminator="\n")
    w.writeheader()
    w.writerows(rows)

verdicts = ["ok", "low", "other", "split", "n/a"]
report.append("\nstrength x verdict: " + "  ".join(verdicts))
for s in "ABCD":
    report.append(f"  {s}: " + "  ".join(f"{stats[(s, v)]:5d}" for v in verdicts))
for s, v, n in (("B", "low", 25), ("B", "other", 15), ("C", "low", 20), ("C", "other", 20), ("D", "ok", 25), ("D", "other", 15)):
    sel = sorted([r for r in rows if r["strength"][0] == s and r["emb"] == v], key=lambda r: -float(r["freq_1800s"] or 0))[:n]
    report.append(f"\n-- {s} {v}")
    for r in sel:
        report.append(f"   {r['eng']} ({r['pos']}) “{r['gloss'][:60]}” | es: {r['es_sims']} | eo: {r['eo_sims']}")
out = "\n".join(report) + "\n"
open(os.path.join(HERE, "archaic_crosscheck_report.txt"), "w", encoding="utf-8").write(out)
print(out)
