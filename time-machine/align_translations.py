# Use a published translation of The Time Machine as evidence for the sense
# of each glossary row in obscure_resolved.tsv.
#
#   venv/bin/python time-machine/align_translations.py <lang> <translation.txt>
#     lang: spa | epo (the word-list column TranslationSpa / TranslationEpo
#     is used for the comparison)
#
# 1. Sentences: Heinemann (spaCy en) and the translation (regex splitter;
#    OCR page markers "=== p..." dropped).
# 2. Sentence alignment over the whole book: LaBSE embeddings, beads 1-1, 1-2,
#    2-1, 1-0, 0-1, scored cos - MATCH_COST (same method as
#    parallel_lexsel/sent_align.py), DP restricted to a diagonal band.
# 3. For each glossary row with a Heinemann quote: the English sentence that
#    holds the quote, its bead, SimAlign (mBERT; mwmf/inter/itermax, a link's
#    confidence = number of methods) from the lemma's tokens to the
#    translation; linked tokens with confidence >= 2 are the translator's
#    rendering.
# 4. Comparison (script tier, shape only) against the TranslationSpa/Epo
#    glosses of the row's Globasa word (a derived word not in word-list is
#    split into its listed parts). Roots are compared on their first 5
#    letters; for epo the ending and common affixes (mal-, -ig-, -ec-, ...)
#    are stripped first.
#      agree       the linked word shares a root with a gloss
#      agree-sent  no linked match, but a gloss root occurs in the aligned
#                  sentence (word links are noisy; this is the main test)
#      differ      neither: review the row (not an error — translators
#                  paraphrase)
#      none (why)  no evidence
#
# Output: cache/align_<lang>.tsv (beads), cache/evidence_<lang>.tsv (per
# glossary row: row key, en sentence, translated sentence, bead score,
# translator's words, glb glosses, verdict). Cache only: the translation text
# is not committed.
import csv
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
CACHE = HERE / "cache"
LANG, SRC = sys.argv[1], Path(sys.argv[2])
COL = {"spa": "TranslationSpa", "epo": "TranslationEpo"}[LANG]
MATCH_COST = 0.30
WEAK_SCORE = 0.55
BAND = 250

# ---------------------------------------------------------------- sentences
import spacy

nlp = spacy.load("en_core_web_sm", disable=["ner"])
nlp.max_length = 400000
eng_text = (HERE / "text" / "heinemann.txt").read_text(encoding="utf-8")
eng_text = re.sub(r"^## .*$", "", eng_text, flags=re.M)
en = [re.sub(r"\s+", " ", s.text).strip() for s in nlp(eng_text).sents]
en = [s for s in en if re.search(r"\w", s)]

tr_text = SRC.read_text(encoding="utf-8")
tr_text = re.sub(r"^=== .*$", "", tr_text, flags=re.M)
tr_text = re.sub(r"\s+", " ", tr_text)
# split after . ! ? (also before an opening dialogue dash)
tr = re.split(r"(?<=[.!?…])\s+(?=[—\-¡¿«\"A-ZÁÉÍÓÚÑĈĜĤĴŜŬ])|\s+(?=—)", tr_text)
tr = [s.strip() for s in tr if re.search(r"\w{2}", s)]
print(f"{len(en)} en / {len(tr)} {LANG} sentences")

# ---------------------------------------------------------------- alignment
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/LaBSE", device="cpu")


def embed(texts):
    return model.encode(texts, batch_size=64, normalize_embeddings=True, show_progress_bar=False)


n, m = len(en), len(tr)
e1, e2 = embed(en), embed(tr)
e1p = embed([en[i] + " " + en[i + 1] for i in range(n - 1)])
e2p = embed([tr[j] + " " + tr[j + 1] for j in range(m - 1)])
NEG = -1e9
best = np.full((n + 1, m + 1), NEG)
back = np.zeros((n + 1, m + 1, 2), dtype=np.int8)
score = np.zeros((n + 1, m + 1))
best[0, 0] = 0.0
for i in range(n + 1):
    c = i * m / max(n, 1)
    for j in range(max(0, int(c - BAND)), min(m, int(c + BAND)) + 1):
        if i == 0 and j == 0:
            continue
        cands = []
        if i >= 1 and j >= 1:
            s = float(e1[i - 1] @ e2[j - 1]); cands.append((best[i - 1, j - 1] + s - MATCH_COST, 1, 1, s))
        if i >= 1 and j >= 2:
            s = float(e1[i - 1] @ e2p[j - 2]); cands.append((best[i - 1, j - 2] + s - MATCH_COST, 1, 2, s))
        if i >= 2 and j >= 1:
            s = float(e1p[i - 2] @ e2[j - 1]); cands.append((best[i - 2, j - 1] + s - MATCH_COST, 2, 1, s))
        if i >= 1:
            cands.append((best[i - 1, j], 1, 0, 0.0))
        if j >= 1:
            cands.append((best[i, j - 1], 0, 1, 0.0))
        v, di, dj, s = max(cands, key=lambda x: x[0])
        best[i, j], back[i, j], score[i, j] = v, (di, dj), s
bead_of = {}  # en index -> (tr indices, score)
beads = []
i, j = n, m
while i > 0 or j > 0:
    di, dj = int(back[i, j][0]), int(back[i, j][1])
    beads.append((list(range(i - di, i)), list(range(j - dj, j)), score[i, j]))
    i, j = i - di, j - dj
beads.reverse()
for a, b, s in beads:
    for x in a:
        bead_of[x] = (a, b, s)
with open(CACHE / f"align_{LANG}.tsv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["en_idx", f"{LANG}_idx", "score", "en", LANG])
    for a, b, s in beads:
        w.writerow([" ".join(map(str, a)), " ".join(map(str, b)), f"{s:.3f}",
                    " ".join(en[x] for x in a), " ".join(tr[y] for y in b)])
matched = [s for a, b, s in beads if a and b]
print(f"{len(beads)} beads, {len(matched)} matched, {sum(s < WEAK_SCORE for s in matched)} weak")

# ---------------------------------------------------------------- word links
from simalign import SentenceAligner

aligner = SentenceAligner(model="bert-base-multilingual-cased", token_type="bpe",
                          matching_methods="mai", device="cpu")
TOK = re.compile(r"\w+(?:['’]\w+)?", re.U)


def fold(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


EPO_PRE = ("mal", "dis", "ek", "re", "ne", "for", "sen")
EPO_SUF = ("ig", "iĝ", "ec", "ul", "ej", "il", "ad", "et", "eg", "aĵ", "em", "ebl", "ist", "ism", "an", "ar", "ind")


def stem(w):
    """Comparable root: epo — strip ending, then common affixes; spa — fold.
    Compared on the first 5 letters (whole root if shorter)."""
    w = w.lower()
    if LANG == "epo":
        w = re.sub(r"(o|a|e|i|u|as|is|os|us)(j)?(n)?$", "", w)
        for _ in range(2):
            for suf in EPO_SUF:
                if w.endswith(suf) and len(w) - len(suf) >= 3:
                    w = w[: -len(suf)]
                    break
        for pre in EPO_PRE:
            if w.startswith(pre) and len(w) - len(pre) >= 3:
                w = w[len(pre):]
                break
    w = fold(w)
    return w[:5] if len(w) > 5 else w


STOP = {"kaj", "konj", "pron", "esti", "por", "tiam", "estas", "aŭ", "che", "por", "the", "que", "del",
        "los", "las", "una", "uno", "con", "ser", "estar", "para", "conj", "pron", "prep", "sfx", "pfx",
        "ntr", "det", "num", "helpv", "kiu", "per"}


wl = pd.read_csv(HERE.parent / "word-list.csv", dtype=str).set_index("Word")


def parts(word):
    """word-list entries a Globasa word is built from: itself if listed, else
    the longest listed prefix + parts(rest) (fatminfilya -> fatminfil, ya)."""
    if word in wl.index:
        return [word]
    for i in range(len(word) - 1, 2, -1):
        if word[:i] in wl.index:
            rest = parts(word[i:]) if len(word) - i > 2 else []
            return [word[:i]] + rest
    return []


def glosses(glb):
    out = set()
    for word in re.findall(r"[a-zñA-ZÑ\-]+", glb or ""):
        key = word if word in wl.index else word.lower()
        for key in parts(key):
            g = wl.loc[key, COL]
            if isinstance(g, pd.Series):
                g = " ".join(g.dropna())
            g = re.sub(r"\b(n|v|adj|adv|s|v\.tr|v\.intr|v\.ntr|prep|conj|interj)\s*:", " ", str(g))
            g = re.sub(r"_[^_]*_|\([^)]*\)", " ", g)
            out |= {t for t in TOK.findall(g) if len(t) > 2 and t.lower() not in STOP}
    return out


def norm(s):
    return re.sub(r"\s+", " ", s).replace("’", "'").strip().lower()


en_norm = [norm(s) for s in en]
rows = list(csv.DictReader(open(HERE / "obscure_resolved.tsv", encoding="utf-8"), delimiter="\t",
                           quoting=csv.QUOTE_NONE))
out = []
for k, r in enumerate(rows):
    key = f"{r['lemma']}|{r['ref']}|{r['quote']}"
    base = {"key": key, "lemma": r["lemma"], "verdict": r["verdict"], "ref": r["ref"], "glb": r["glb"]}
    if r["verdict"] == "transparent" or not r["ref"].startswith("H:"):
        continue
    q = norm(r["quote"]).strip(" .,;:!?\"'")
    hits = [i for i, s in enumerate(en_norm) if q and q in s]
    if not hits:
        out.append({**base, "evidence": "none (quote not found in one sentence)"}); continue
    i = hits[0]
    a, b, s = bead_of[i]
    if not b:
        out.append({**base, "en": en[i], "evidence": "none (sentence not translated: 1-0 bead)"}); continue
    src = TOK.findall(" ".join(en[x] for x in a))
    tgt = TOK.findall(" ".join(tr[y] for y in b))
    lem = r["lemma"].lower().split()
    lstem = [w[: max(4, len(w) - 3)] for w in lem]
    qtok = {t.lower() for t in TOK.findall(r["quote"])}
    idx = [x for x, t in enumerate(src) if t.lower() in qtok and any(t.lower().startswith(ls) for ls in lstem)]
    if not idx:
        out.append({**base, "en": en[i], LANG: " ".join(tr[y] for y in b),
                    "evidence": "none (lemma token not located)"}); continue
    res = aligner.get_word_aligns(src, tgt) if len(src) < 200 and len(tgt) < 200 else {}
    conf = {}
    for links in res.values():
        for x, y in links:
            conf[(x, y)] = conf.get((x, y), 0) + 1
    ys = sorted({y for (x, y), c in conf.items() if x in idx and c >= 2})
    words = [tgt[y] for y in ys]
    gl = glosses(r["glb"])
    gstems = {stem(g) for g in gl}
    def hit(t):
        # root match, or (compounds: maranemonoj, kremaciejoj) a gloss root of
        # 5+ letters inside the token
        ft = fold(t)
        return t.lower() not in STOP and (stem(t) in gstems or any(len(g) >= 5 and g in ft for g in gstems))

    sent_hit = [t for t in tgt if hit(t)]
    if not gl:
        ev = f"none (no {COL} gloss for the Globasa rendering)"
    elif words and any(hit(w) for w in words):
        ev = "agree"                      # the linked word itself matches
    elif sent_hit:
        ev = "agree-sent"                 # a gloss of it is in the aligned sentence
        words = sent_hit                  # show the evidence, not the noisy link
    elif not words:
        ev = "none (no confident word link)"
    else:
        ev = "differ"
    out.append({**base, "en": en[i], LANG: " ".join(tr[y] for y in b), "bead_score": f"{s:.3f}",
                f"{LANG}_words": " ".join(words), "glb_glosses": ", ".join(sorted(gl)), "evidence": ev})
    if k % 50 == 0:
        print(k, end=" ", flush=True)
print()
cols = ["key", "lemma", "verdict", "ref", "glb", f"{LANG}_words", "glb_glosses", "evidence", "bead_score", "en", LANG]
with open(CACHE / f"evidence_{LANG}.tsv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, delimiter="\t", lineterminator="\n", extrasaction="ignore",
                       quoting=csv.QUOTE_NONE, escapechar=None, quotechar="\x00")
    w.writeheader()
    w.writerows(out)
from collections import Counter

print(Counter(re.sub(r" \(.*", "", o["evidence"]) for o in out))
