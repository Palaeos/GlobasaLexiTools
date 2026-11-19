# Checks obscure_resolved.tsv against obscure_candidates.tsv and word-list.csv.
#  1. coverage: every candidate lemma has at least one row
#  2. fields: verdict in the allowed set; glb filled for obscure/dated_sense/
#     technical; glb_how one of the allowed labels; a fallback states why
#  3. lexicon: every Globasa token in glb is a word-list entry, or segments
#     wholly into word-list entries and affixes (labelled "segmented: a+b").
#     Tokens that do neither are listed as UNKNOWN. A segmentation is only
#     shape-level evidence; it does not vet the meaning.
# Prints a report; exit status 1 if any coverage/field problem or UNKNOWN token.
import csv
import re
import sys
from functools import lru_cache
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
VERDICTS = {"obscure", "dated_sense", "transparent", "technical", "misprint"}
HOW = re.compile(r"^(word-list|derived \(proposed\)|paraphrase|fallback: .+)$")

wl = pd.read_csv(HERE.parent / "word-list.csv", dtype=str)
words = set()
for w in wl["Word"].dropna():
    for part in re.split(r"[ ,]+", w.lower()):
        part = part.strip("-")
        if part:
            words.add(part)
# grammatical endings not listed as entries
words |= {"li", "ya", "cu", "gi"}
# names coined in the novel, rendered as names
NAMES = {"morlok", "morloka", "eloi", "wina", "weena"}


@lru_cache(maxsize=None)
def segment(tok):
    if tok in words:
        return (tok,)
    best = None
    for i in range(len(tok) - 1, 1, -1):
        head = tok[:i]
        if head in words:
            rest = segment(tok[i:])
            if rest and (best is None or len(rest) + 1 < len(best)):
                best = (head,) + rest
    return best


rows = list(csv.DictReader(open(HERE / "obscure_resolved.tsv", encoding="utf-8"), delimiter="\t",
                           quoting=csv.QUOTE_NONE))
cands = {r["lemma"] for r in csv.DictReader(open(HERE / "obscure_candidates.tsv", encoding="utf-8"),
                                             delimiter="\t", quoting=csv.QUOTE_NONE)}
bad = 0
missing = sorted(cands - {r["lemma"] for r in rows})
if missing:
    bad += 1
    print("MISSING candidates:", ", ".join(missing))

for n, r in enumerate(rows, 2):
    v, glb, how = r["verdict"], (r["glb"] or "").strip(), (r["glb_how"] or "").strip()
    if v not in VERDICTS:
        bad += 1
        print(f"line {n}: bad verdict {v!r} ({r['lemma']})")
    if v in ("obscure", "dated_sense", "technical") and not glb:
        bad += 1
        print(f"line {n}: no glb for {v} {r['lemma']}")
    if glb and not HOW.match(how):
        bad += 1
        print(f"line {n}: bad glb_how {how!r} ({r['lemma']})")

unknown, segmented = {}, {}
for r in rows:
    glb = (r["glb"] or "")
    # alternatives and notes inside glb: "a / b", "a (b)"
    for tok in re.findall(r"[a-zñ]+", glb.lower()):
        if tok in words or tok in NAMES:
            continue
        seg = segment(tok)
        if seg:
            segmented.setdefault(tok, ("+".join(seg), r["lemma"]))
        else:
            fb = (r["glb_how"] or "").startswith("fallback")
            unknown.setdefault(tok, []).append((r["lemma"], fb))

print(f"\n{len(rows)} rows; verdicts:",
      {v: sum(r["verdict"] == v for r in rows) for v in sorted(VERDICTS)})
print(f"\nsegmented ({len(segmented)}):")
for tok, (seg, lem) in sorted(segmented.items()):
    print(f"  {tok:24} {seg:32} [{lem}]")
# an unknown token is acceptable only in a row labelled as a fallback (a
# borrowing with its reason given); anywhere else it is an invented root
hard = {t: l for t, l in unknown.items() if not all(fb for _, fb in l)}
print(f"\nunknown in fallback rows ({len(unknown) - len(hard)}):")
for tok, lems in sorted(unknown.items()):
    if tok not in hard:
        print(f"  {tok:24} [{', '.join(sorted({x for x, _ in lems}))}]")
print(f"\nUNKNOWN outside fallback rows ({len(hard)}):")
for tok, lems in sorted(hard.items()):
    print(f"  {tok:24} [{', '.join(sorted({x for x, _ in lems}))}]")
sys.exit(1 if bad or hard else 0)
