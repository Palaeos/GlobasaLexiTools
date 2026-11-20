# Word-level variants between the Heinemann (UK) and Holt (US) texts, both
# by Wells, both public domain.
#
# 1. Sentences of each edition; every Heinemann sentence is matched to the
#    most similar Holt sentence within a positional window (difflib ratio
#    >= MIN_RATIO). Holt's opening chapter and some passages differ wholesale
#    and stay unmatched.
# 2. Word diff of each matched pair. Each change is labelled by SHAPE only
#    (script tier; meaning is left to the reader):
#      spelling     same words after US/UK normalisation (travelled/traveled,
#                   colour/color, centre/center, -ise/-ize, hyphens, case)
#      punctuation  same words, different punctuation
#      substitution n words -> m words, both sides non-empty
#      insertion    Holt adds words      (often explicitation)
#      deletion     Holt lacks words
# 3. Glossary join: a short substitution/deletion (<= 4 words a side, not an
#    orthographic near-match) that covers a glossary row's lemma in that
#    row's sentence fills column `holt` of obscure_resolved.tsv with Holt's
#    reading ("—" = Holt omits the word).
#
# Output: holt_variants.tsv (h_sentence_no, ratio, kind, heinemann, holt,
# h_context), obscure_resolved.tsv column `holt`.
import difflib
import re
from pathlib import Path

HERE = Path(__file__).parent
MIN_RATIO = 0.6
WINDOW = 150


def sents(name):
    t = (HERE / "text" / name).read_text(encoding="utf-8")
    t = re.sub(r"^## .*$", "", t, flags=re.M)
    t = re.sub(r"\s+", " ", t)
    return [s for s in re.split(r'(?<=[.!?])\s+(?=["A-Z])', t) if len(s) > 40]


def spell(w):
    w = re.sub(r"[^\w]", "", w.lower().replace("æ", "ae").replace("œ", "oe"))
    for a, b in (("our", "or"), ("tre", "ter"), ("lled", "led"), ("lling", "ling"), ("ller", "ler"),
                 ("ise", "ize"), ("isation", "ization"), ("ence", "ense"), ("grey", "gray"), ("mme", "m")):
        w = w.replace(a, b)
    return w


def kind(h, u):
    if not h:
        return "insertion"
    if not u:
        return "deletion"
    if "".join(map(spell, h)) == "".join(map(spell, u)):
        bare = lambda ws: [re.sub(r"[^\w]", "", w.lower()) for w in ws]
        return "punctuation" if bare(h) == bare(u) else "spelling"
    return "substitution"


H, U = sents("heinemann.txt"), sents("holt.txt")
variants = []   # (i, ratio, kind, h, u)
for i, h in enumerate(H):
    c = int(i * len(U) / len(H))
    best = (0.0, None)
    for u in U[max(0, c - WINDOW): c + WINDOW]:
        sm = difflib.SequenceMatcher(None, h, u, autojunk=False)
        if sm.real_quick_ratio() < MIN_RATIO or sm.quick_ratio() < MIN_RATIO:
            continue
        r = sm.ratio()
        if r > best[0]:
            best = (r, u)
    if best[0] < MIN_RATIO or best[0] == 1.0:
        continue
    hw, uw = h.split(), best[1].split()
    for op, a, b, c2, d in difflib.SequenceMatcher(None, hw, uw, autojunk=False).get_opcodes():
        if op != "equal":
            variants.append((i, best[0], kind(hw[a:b], uw[c2:d]), " ".join(hw[a:b]), " ".join(uw[c2:d])))

with open(HERE / "holt_variants.tsv", "w", encoding="utf-8") as f:
    f.write("h_sentence_no\tratio\tkind\theinemann\tholt\th_context\n")
    for i, r, k, h, u in variants:
        f.write(f"{i}\t{r:.2f}\t{k}\t{h}\t{u}\t{H[i]}\n")

# ---- glossary join
path = HERE / "obscure_resolved.tsv"
lines = path.read_text(encoding="utf-8").rstrip("\n").split("\n")
hdr = lines[0].split("\t")
if "holt" not in hdr:
    hdr.append("holt")
rows = [dict(zip(hdr, ln.split("\t"))) for ln in lines[1:]]
norm = lambda s: re.sub(r"\s+", " ", s).lower()
by_sent = {}
for i, r, k, h, u in variants:
    # short lexical changes only: whole-clause rewrites/drops say nothing
    # about one word, and near-identical strings are spelling (plough/plow)
    if k not in ("substitution", "deletion") or len(h.split()) > 4 or len(u.split()) > 4:
        continue
    if u and difflib.SequenceMatcher(None, spell(h), spell(u)).ratio() >= 0.75:
        continue
    by_sent.setdefault(i, []).append((h, u))
Hn = [norm(s) for s in H]
joined = 0
for r in rows:
    r["holt"] = ""
    if not r["ref"].startswith("H:") or r["verdict"] == "transparent":
        continue
    q = norm(r["quote"]).strip(" .,;:!?\"'")
    hits = [i for i, s in enumerate(Hn) if q and q in s]
    if not hits:
        continue
    # the lemma's longest word, as itself or with a short inflection
    # (presently must not match "presence"; "prove you" must not match "you")
    l = max(r["lemma"].lower().split(), key=len)
    if len(l) <= 3 and " " in r["lemma"]:
        continue  # phrase of short function words (by the bye): no safe anchor
    stems = {l, l[:-1] if l[-1] in "ey" and len(l) > 4 else l}
    for h, u in by_sent.get(hits[0], []):
        hw = [re.sub(r"[^\w]", "", w.lower()) for w in h.split()]
        if any(w.startswith(st) and len(w) - len(st) <= 3 for w in hw for st in stems):
            r["holt"] = f"{h} → {u or '—'}"
            joined += 1
            break
with open(path, "w", encoding="utf-8") as f:
    f.write("\t".join(hdr) + "\n")
    for r in rows:
        f.write("\t".join(r.get(c, "") for c in hdr) + "\n")

from collections import Counter

print(len(variants), "variants:", dict(Counter(k for _, _, k, _, _ in variants)))
print(joined, "glossary rows with a Holt reading")
