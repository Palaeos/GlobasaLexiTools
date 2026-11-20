# Word-level variants between two editions of one work (both by the author), as evidence for
# plain-language paraphrases: where the author reworded a passage, the other reading is often the
# plainer one. Functions only: safe to import. Used by time-machine/witness_variants.py (Heinemann
# 1895 vs Holt 1895 and Atlantic 1924) and
# war-of-the-worlds/atlantic_variants.py (Heinemann 1898 vs Atlantic 1924).
#
# 1. sentences(path): the text's sentences ("## " headings dropped, > 40 characters).
# 2. variants(A, B): every A sentence is matched to the most similar B sentence within a
#    positional window (difflib ratio >= min_ratio; identical sentences are skipped), then the
#    two are diffed word by word. Each change is labelled by SHAPE only (script tier):
#      spelling     same words after US/UK normalisation (travelled/traveled, colour/color, ...)
#      punctuation  same words, different punctuation
#      substitution n words -> m words, both sides non-empty
#      insertion    B adds words      (often explicitation)
#      deletion     B lacks words
# 3. lexical(v): the short substitutions/deletions (<= 4 words a side, not an orthographic
#    near-match) that can speak for one word: the ones worth showing next to a glossary row.
import difflib
import re

MIN_RATIO = 0.6
WINDOW = 150


def sentences(path):
    t = path.read_text(encoding="utf-8")
    t = re.sub(r"^## .*$", "", t, flags=re.M)
    t = re.sub(r"\s+", " ", t)
    return [s for s in re.split(r'(?<=[.!?])\s+(?=["A-Z])', t) if len(s) > 40]


def spell(w):
    w = re.sub(r"[^\w]", "", w.lower().replace("æ", "ae").replace("œ", "oe"))
    for a, b in (("our", "or"), ("tre", "ter"), ("lled", "led"), ("lling", "ling"), ("ller", "ler"),
                 ("ise", "ize"), ("isation", "ization"), ("ence", "ense"), ("grey", "gray"), ("mme", "m")):
        w = w.replace(a, b)
    return w


def kind(a, b):
    if not a:
        return "insertion"
    if not b:
        return "deletion"
    if "".join(map(spell, a)) == "".join(map(spell, b)):
        bare = lambda ws: [re.sub(r"[^\w]", "", w.lower()) for w in ws]
        return "punctuation" if bare(a) == bare(b) else "spelling"
    return "substitution"


def variants(A, B, min_ratio=MIN_RATIO, window=WINDOW):
    """[(i, ratio, kind, a_words, b_words)] for the sentences A[i] that have a close B match."""
    out = []
    for i, a in enumerate(A):
        c = int(i * len(B) / len(A))
        best = (0.0, None)
        for b in B[max(0, c - window): c + window]:
            sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
            if sm.real_quick_ratio() < min_ratio or sm.quick_ratio() < min_ratio:
                continue
            r = sm.ratio()
            if r > best[0]:
                best = (r, b)
        if best[0] < min_ratio or best[0] == 1.0:
            continue
        aw, bw = a.split(), best[1].split()
        for op, x, y, z, w in difflib.SequenceMatcher(None, aw, bw, autojunk=False).get_opcodes():
            if op != "equal":
                out.append((i, best[0], kind(aw[x:y], bw[z:w]), " ".join(aw[x:y]), " ".join(bw[z:w])))
    return out


def lexical(v):
    """Short word changes only: whole-clause rewrites say nothing about one word, and
    near-identical strings are spelling (plough/plow)."""
    i, r, k, a, b = v
    if k not in ("substitution", "deletion") or len(a.split()) > 4 or len(b.split()) > 4:
        return False
    return not (b and difflib.SequenceMatcher(None, spell(a), spell(b)).ratio() >= 0.75)


def write_tsv(path, A, found, a_name, b_name, prefix=None):
    prefix = prefix or a_name
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"{prefix}_sentence_no\tratio\tkind\t{a_name}\t{b_name}\t{prefix}_context\n")
        for i, r, k, a, b in found:
            f.write(f"{i}\t{r:.2f}\t{k}\t{a}\t{b}\t{A[i]}\n")
