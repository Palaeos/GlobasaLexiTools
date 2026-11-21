"""Period sense prototypes from a contemporary dictionary: Webster 1913 vs Wiktionary.

Same task as period_sense_probe.py (Time Machine dated-sense gold of obscure_resolved.tsv), but
the sense inventory and the prototypes come from Webster's Revised Unabridged (1913,
cache/sources/webster_1913.txt): every entry of the headword (all parts of speech), every
numbered or 'Defn:' sense, its labels ([Obs.], [Colloq.] ...) and its examples = the sense's
quotation lines and 'as, ...' phrases that contain the headword. A sense's prototype is the mean
vector of the headword in its examples (fallback: "word: definition", flagged). Gold = the
senses whose definition shares most content words with the gold gloss (ties all gold).

Conditions: first (Webster's first sense of the part of speech: Webster orders senses oldest
first), A mBERT, B MacBERTh (both layer 8, own prototypes). The Wiktionary-inventory B of
period_sense_probe_items.tsv is reported on the items both cover.

    ../venv/bin/python time-machine/webster_sense_probe.py

Writes time-machine/webster_sense_probe_items.tsv."""
import csv
import os
import re
import sys
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from bert_words import MACBERTH, MBERT, embed, load, words  # noqa: E402

WEBSTER = os.path.join(HERE, "cache", "sources", "webster_1913.txt")
OUT = os.path.join(HERE, "webster_sense_probe_items.tsv")
LAYER = 8
MAX_WORDS = 120
HEAD = re.compile(r"^[A-Z][A-Z' -]*$")
POS_RE = re.compile(r",\s*(v\.\s*[ti]\.|a\.|adv\.|n\.|prep\.|conj\.|interj\.|p\.\s*p\.|p\.\s*a\.)")
POS_MAP = {"a": "adj", "adv": "adv", "n": "noun", "prep": "prep", "conj": "conj", "interj": "intj",
           "v": "verb", "p": "adj"}
SPACY_POS = {"NOUN": "noun", "VERB": "verb", "AUX": "verb", "ADJ": "adj", "ADV": "adv",
             "ADP": "prep", "SCONJ": "conj", "CCONJ": "conj", "INTJ": "intj"}
SENSE_START = re.compile(r"^(?:(\d{1,2})\.\s+|Defn:\s*)")
LABEL = re.compile(r"\[(Obs\.?|Archaic|Poetic|R\.|Colloq\.|Slang|Prov\. Eng\.|Eng\.|Local[^\]]*)\]")
SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"“'(])")
AS_EX = re.compile(r"\bas,\s+([^;.]+)")
STOP = set("a an the of to in on for and or by with as at from that this be is are was it its "
           "one's someone something oneself who which what not no very more most into out up "
           "being having make made do done any thing".split())


def content(text):
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOP and len(w) > 2}


def form_matches(tok, lemma):
    t = tok.lower()
    if t == lemma:
        return True
    stem = lemma[:-1] if lemma[-1:] in "ey" and len(lemma) > 4 else lemma
    return len(stem) >= 3 and t.startswith(stem) and len(t) - len(lemma) <= 4


gold_rows = [r for r in csv.DictReader(open(os.path.join(HERE, "obscure_resolved.tsv"), encoding="utf-8"),
                                       delimiter="\t") if r["verdict"] == "dated_sense"
             and " " not in r["lemma"].strip()]
lemmas = {r["lemma"].strip().lower() for r in gold_rows}

# ---------------------------------------------------------------- Webster: all entries of the lemmas
entries = {}  # lemma -> [(pos, text)]
head, buf = None, []
with open(WEBSTER, encoding="latin-1") as f:
    for line in f:
        s = line.rstrip("\n")
        if HEAD.match(s.strip()) and len(s.strip()) > 1:
            if head in lemmas and buf:
                entries.setdefault(head, []).append("\n".join(buf))
            head, buf = s.strip().lower(), []
        elif head in lemmas:
            buf.append(s)
if head in lemmas and buf:
    entries.setdefault(head, []).append("\n".join(buf))

senses = {}  # lemma -> [{pos, defn, labels, examples:[(words, idx)], fallback}]
for lemma, blocks in entries.items():
    out = []
    for block in blocks:
        first = block.strip().split("\n", 1)[0]
        m = POS_RE.search(first)
        pos = POS_MAP.get(m.group(1).split(".")[0].strip(), "?") if m else "?"
        for para in re.split(r"\n\s*\n", block):
            para = " ".join(para.split())
            sm = SENSE_START.match(para)
            if not sm:
                continue
            body = para[sm.end():]
            labels = set(LABEL.findall(body))
            sents = SENT.split(body)
            defn, examples = [], []
            for i, s in enumerate(sents):
                ws = words(s)
                k = next((j for j, w in enumerate(ws) if form_matches(w, lemma)), None)
                if i > 0 and k is not None:
                    examples.append((ws[:MAX_WORDS], k))
                elif not examples:
                    defn.append(s)
            for ex in AS_EX.findall(" ".join(defn)):
                ws = words(ex)
                k = next((j for j, w in enumerate(ws) if form_matches(w, lemma)), None)
                if k is not None:
                    examples.append((ws, k))
            d = re.sub(r"\bas,\s+[^;.]+", "", " ".join(defn))
            fallback = not examples
            if fallback:
                examples = [([lemma, ":"] + words(d)[:MAX_WORDS - 2], 0)]
            out.append({"pos": pos, "defn": d.strip(), "labels": labels, "examples": examples,
                        "fallback": fallback})
    if out:
        senses[lemma] = out
print(f"{len(senses)}/{len(lemmas)} gold lemmas in Webster, {sum(map(len, senses.values()))} senses "
      f"({sum(s['fallback'] for v in senses.values() for s in v)} without an example)")

# ---------------------------------------------------------------- gold occurrences in the book
import spacy  # noqa: E402

nlp = spacy.load("en_core_web_sm", disable=["ner"])
text = open(os.path.join(HERE, "text", "heinemann.txt"), encoding="utf-8").read()
paras = [" ".join(p.split()) for p in re.split(r"\n\s*\n", text)]
book = []
for doc in nlp.pipe([p for p in paras if len(p) > 20 and not p.startswith("#")], batch_size=64):
    for s in doc.sents:
        toks = [t for t in s if not t.is_space]
        if 3 <= len(toks) <= MAX_WORDS:
            book.append([(t.text, t.lemma_.lower(), t.pos_, t.dep_) for t in toks])
del nlp, text, paras
norm = lambda s: " ".join(re.findall(r"\w+", s.lower()))
book_norm = [norm(" ".join(t[0] for t in s)) for s in book]

items, skipped = [], Counter()
for r in gold_rows:
    lemma = r["lemma"].strip().lower()
    if lemma not in senses:
        skipped["not in Webster"] += 1
        continue
    q = norm(r["quote"])
    si = next((i for i, t in enumerate(book_norm) if q and q in t), None)
    if si is None:
        skipped["quote not found"] += 1
        continue
    ti = next((i for i, t in enumerate(book[si]) if t[1] == lemma or form_matches(t[0], lemma)), None)
    if ti is None:
        skipped["word not found"] += 1
        continue
    ov = [len(content(r["sense"]) & content(s["defn"])) for s in senses[lemma]]
    if not max(ov):
        skipped["gold gloss matches no sense"] += 1
        continue
    gold = {k for k, o in enumerate(ov) if o == max(ov)}
    t = book[si][ti]
    pos = SPACY_POS.get(t[2])
    ss = senses[lemma]
    if pos == "noun" and t[3] in ("amod", "compound") and any(s["pos"] == "adj" for s in ss):
        pos = "adj"
    cand = [k for k, s in enumerate(ss) if s["pos"] == pos]
    if not set(cand) & gold:
        cand = list(range(len(ss)))
    items.append({"lemma": lemma, "sent": si, "idx": ti, "gold": gold, "cand": cand,
                  "gold_text": r["sense"], "quote": r["quote"]})
print(f"items: {len(items)} of {len(gold_rows)} single-word gold rows (skipped {dict(skipped)})")

# ---------------------------------------------------------------- embed + decide
ex_list = [(lemma, k, ex) for lemma, ss in senses.items() for k, s in enumerate(ss) for ex in s["examples"]]
sent_ids = sorted({it["sent"] for it in items})
row_of = {s: i for i, s in enumerate(sent_ids)}


def unit(x):
    return x / (np.linalg.norm(x, axis=-1, keepdims=True) + 1e-8)


for name, cond in ((MBERT, "A"), (MACBERTH, "B")):
    tok, model = load(name)
    sv = embed(tok, model, [[t[0] for t in book[s]] for s in sent_ids], LAYER)
    ev = embed(tok, model, [ex[0] for _, _, ex in ex_list], LAYER)
    del tok, model
    occ = np.stack([np.nan_to_num(sv[row_of[it["sent"]]][it["idx"]]) for it in items])
    exv = np.stack([np.nan_to_num(v[ex[1]]) for v, (_, _, ex) in zip(ev, ex_list)])
    mu = np.concatenate([occ, exv]).mean(0)  # no separate map here: centre on this data
    occ, exv = unit(occ - mu), unit(exv - mu)
    protos = {}
    for v, (lemma, k, _) in zip(exv, ex_list):
        protos.setdefault((lemma, k), []).append(v)
    protos = {key: unit(np.mean(v, 0)) for key, v in protos.items()}
    for i, it in enumerate(items):
        sims = [float(occ[i] @ protos[it["lemma"], k]) for k in it["cand"]]
        it[cond] = it["cand"][int(np.argmax(sims))]
    del sv, ev, occ, exv, protos
for it in items:
    it["first"] = it["cand"][0]

n = len(items)
chance = sum(len(set(it["cand"]) & it["gold"]) / len(it["cand"]) for it in items)
print(f"\n== Webster 1913 inventory + examples, Time Machine dated-sense gold: {n} items ==")
print(f"  chance {100 * chance / n:5.1f}%   mean competing senses {np.mean([len(it['cand']) for it in items]):.1f}")
for c, label in (("first", "first Webster sense (oldest)"), ("A", "A mBERT"), ("B", "B MacBERTh")):
    right = sum(it[c] in it["gold"] for it in items)
    print(f"  {label:30s} {right:4d}/{n} = {100 * right / n:5.1f}%")
fb = sum(any(senses[it['lemma']][k]["fallback"] for k in it["gold"]) for it in items)
print(f"  gold sense without a Webster example: {fb}/{n}")

# Wiktionary B on the shared items
wk = [r for r in csv.DictReader(open(os.path.join(HERE, "period_sense_probe_items.tsv"), encoding="utf-8"),
                                delimiter="\t") if r["gold"]]
strip = lambda g: re.sub(r" \[[^\]]*\]$", "", g.replace(" (fallback: gloss, no quotation)", "")).strip()
shared = Counter()
for it in items:
    q = norm(it["quote"])
    w = next((r for r in wk if r["lemma"] == it["lemma"] and q in norm(r["sentence"].replace("**", ""))), None)
    if not w:
        continue
    g = {strip(x) for x in w["gold"].split(" / ")}
    shared["n"] += 1
    shared["wiktionary B"] += strip(w["B"]) in g
    shared["wiktionary A"] += strip(w["A"]) in g
    shared["webster B"] += it["B"] in it["gold"]
    shared["webster A"] += it["A"] in it["gold"]
    shared["webster first"] += it["first"] in it["gold"]
m = shared["n"]
if m:
    print(f"\n  on the {m} items both inventories cover:")
    for k in ("wiktionary A", "wiktionary B", "webster first", "webster A", "webster B"):
        print(f"    {k:16s} {shared[k]:3d}/{m} = {100 * shared[k] / m:5.1f}%")

with open(OUT, "w", newline="", encoding="utf-8") as f:
    wr = csv.writer(f, delimiter="\t")
    wr.writerow(["lemma", "sentence", "gold_gloss", "gold_webster", "first", "A", "B", "candidates"])
    fmt = lambda it, k: senses[it["lemma"]][k]["defn"][:120] + (" [" + ",".join(sorted(senses[it["lemma"]][k]["labels"])) + "]" if senses[it["lemma"]][k]["labels"] else "") + (" (fallback: definition, no example)" if senses[it["lemma"]][k]["fallback"] else "")
    for it in items:
        sent = " ".join(("**" + t[0] + "**") if i == it["idx"] else t[0] for i, t in enumerate(book[it["sent"]]))
        wr.writerow([it["lemma"], sent, it["gold_text"], " / ".join(fmt(it, k) for k in sorted(it["gold"])),
                     fmt(it, it["first"]), fmt(it, it["A"]), fmt(it, it["B"]), len(it["cand"])])
print(f"\nitems: {OUT}")
