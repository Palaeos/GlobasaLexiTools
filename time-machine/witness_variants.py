# Word-level variants between the Heinemann text (base, UK 1895) and each other witness by Wells,
# all public domain:
#   holt      Holt (US) 1895
#   atlantic  Atlantic Edition (The Works of H. G. Wells vol. 1) 1924, Wells's late revision
# Where Wells reworded a passage, the other reading often shows the plainer word a paraphrase can
# follow (user, 2026-11-20: use the editions to inform paraphrases).
#
# The edition comparison is edition_variants.py (shared with war-of-the-worlds/):
# 1. every Heinemann sentence is matched to the most similar witness sentence within a positional
#    window (difflib ratio >= MIN_RATIO); passages rewritten wholesale stay unmatched (Holt's
#    opening chapter).
# 2. word diff of each matched pair, labelled by SHAPE only (spelling, punctuation, substitution,
#    insertion, deletion; script tier, meaning is left to the reader).
# 3. glossary join: a short substitution/deletion (edition_variants.lexical) that covers a
#    glossary row's lemma in that row's sentence fills the witness's column of
#    obscure_resolved.tsv with its reading ("—" = the witness omits the word).
# The comparison takes minutes per witness: <witness>_variants.tsv is reused while it is newer
# than both texts.
#
# Output: <witness>_variants.tsv (h_sentence_no, ratio, kind, heinemann, <witness>, h_context),
#         obscure_resolved.tsv columns holt, atlantic.
import csv
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from edition_variants import lexical, sentences, variants as find_variants, write_tsv

HERE = Path(__file__).parent
BASE = HERE / "text" / "heinemann.txt"
WITNESSES = {"holt": HERE / "text" / "holt.txt", "atlantic": HERE / "text" / "atlantic.txt"}
GLOSSARY = HERE / "obscure_resolved.tsv"


def norm(s):
    return re.sub(r"\s+", " ", s).lower()


def witness_variants(name, H):
    out = HERE / f"{name}_variants.tsv"
    text = WITNESSES[name]
    if out.exists() and out.stat().st_mtime > max(BASE.stat().st_mtime, text.stat().st_mtime):
        with open(out, encoding="utf-8") as f:
            return [(int(r["h_sentence_no"]), float(r["ratio"]), r["kind"], r["heinemann"], r[name])
                    for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)]
    found = find_variants(H, sentences(text))
    write_tsv(out, H, found, "heinemann", name, prefix="h")
    return found


def reading(row, by_sent, Hn):
    # the witness's reading of the row's lemma in the row's sentence, or ""
    if not row["ref"].startswith("H:") or row["verdict"] == "transparent":
        return ""
    q = norm(row["quote"]).strip(" .,;:!?\"'")
    hits = [i for i, s in enumerate(Hn) if q and q in s]
    if not hits:
        return ""
    # the lemma's longest word, as itself or with a short inflection
    # (presently must not match "presence"; "prove you" must not match "you")
    lemma = max(row["lemma"].lower().split(), key=len)
    if len(lemma) <= 3 and " " in row["lemma"]:
        return ""  # phrase of short function words (by the bye): no safe anchor
    stems = {lemma, lemma[:-1] if lemma[-1] in "ey" and len(lemma) > 4 else lemma}
    for h, u in by_sent.get(hits[0], []):
        hw = [re.sub(r"[^\w]", "", w.lower()) for w in h.split()]
        if any(w.startswith(st) and len(w) - len(st) <= 3 for w in hw for st in stems):
            return f"{h} → {u or '—'}"
    return ""


H = sentences(BASE)
Hn = [norm(s) for s in H]
lines = GLOSSARY.read_text(encoding="utf-8").rstrip("\n").split("\n")
hdr = lines[0].split("\t")
rows = [dict(zip(hdr, ln.split("\t"))) for ln in lines[1:]]
for name in WITNESSES:
    found = witness_variants(name, H)
    by_sent = {}
    for v in found:
        if lexical(v):
            by_sent.setdefault(v[0], []).append((v[3], v[4]))
    if name not in hdr:
        hdr.append(name)
    for r in rows:
        r[name] = reading(r, by_sent, Hn)
    print(f"{name}: {len(found)} variants {dict(Counter(v[2] for v in found))}; "
          f"{sum(1 for r in rows if r[name])} glossary rows with a reading")
with open(GLOSSARY, "w", encoding="utf-8") as f:
    f.write("\t".join(hdr) + "\n")
    for r in rows:
        f.write("\t".join(r.get(c, "") for c in hdr) + "\n")
