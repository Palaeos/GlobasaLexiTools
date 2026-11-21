# How far does the existing coreference output get in choosing Globasa ∅ vs demonstrative
# (hin/den) for English "the"?  No new models: coref comes from the running eng->glb NLP service
# (GlobasaTranslation/apertium-glb-eng/eng-nlp-service.py, stanza GUM coref), the same output the
# `coref` stage of eng-glb-neural.py uses.
#
# Gold: "Short Stories by Vanege, Globasa - English.xlsx" (one Globasa sentence per row with its
# English translation).  Label of a "the" NP = whether the Globasa row has hin/den right before a
# Globasa word whose word-list English gloss is the NP's head lemma; rows where no such word is
# found are "unaligned" and left out of the scores (never guessed).
#
#   1. start the service:  cd GlobasaTranslation/apertium-glb-eng; ../../venv/bin/python eng-nlp-service.py
#   2. venv/bin/python definiteness/coref_the.py      -> definiteness/the_items.tsv + tables on stdout
import csv
import json
import os
import re
import sys
import urllib.request
from collections import Counter, defaultdict

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLD = os.path.join(ROOT, "Short Stories by Vanege, Globasa - English.xlsx")
WORDLIST = os.path.join(ROOT, "word-list.csv")
OUT = os.path.join(ROOT, "definiteness", "the_items.tsv")
URL = os.environ.get("ENG_NLP_URL", "http://127.0.0.1:8597") + "/analyze"

DEM = {"hin", "den"}                          # determiners; hinto/dento are pronouns
# words that may stand between a determiner and its noun inside one Globasa NP: anything but these
NP_BREAK = {"sen", "ji", "or", "mas", "ki", "hu", "fe", "de", "of", "tas", "yon", "in", "per", "na",
            "le", "xa", "am", "no", "kom", "cel", "kos", "bax", "ex", "har", "sol", "pia", "te",
            "ete", "mi", "yu", "imi", "uyu", "to", "oto", "da", "hay", "el", "eger", "denwatu"}
GLB_TOKEN = re.compile(r"[a-zA-Z]+")
PAREN = re.compile(r"\s*\((?:sg\.|pl\.|lit\.[^)]*)\)")      # translator's notes in the English
POS_PREFIX = re.compile(r"^\s*[a-z]+\.?:\s*")
QUOTES = re.compile(r"[\"“”]")


# ── service client: the same request eng-glb-neural.py's analyze() sends (that file runs its
#    pipeline at import time, so it is not imported) ─────────────────────────────────────────
def analyze(text):
    req = urllib.request.Request(URL, data=json.dumps({"text": text}).encode(),
                                 headers={"Content-Type": "application/json"})
    direct = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with direct.open(req, timeout=600) as r:
        return json.loads(r.read())


def chain_of(w, chains):                     # as in eng-glb-neural.py
    return next((k for k, c in enumerate(chains) if w["i"] in {m["head"] for m in c}), None)


# ── word list: English noun gloss -> Globasa words ────────────────────────────────────────
def gloss_index():
    wl = pd.read_csv(WORDLIST, usecols=["Word", "TranslationEng"], dtype=str).dropna()
    index = defaultdict(set)
    for word, eng in zip(wl["Word"], wl["TranslationEng"]):
        for part in re.split(r"[;,]", re.sub(r"\([^)]*\)|_[^_]*_", "", eng)):
            gloss = POS_PREFIX.sub("", part).strip().lower()
            if gloss and " " not in gloss:
                index[gloss].add(word.lower())
    return index


def stories(df):
    """[(title, [(glb, eng), ...])]; a title row has no sentence-final punctuation."""
    out = []
    for glb, eng in zip(df[1].astype(str), df[2].astype(str)):
        title = not re.search(r"[.!?:;\"”…]\s*$", eng) and len(eng) < 40 and eng[:1].isupper()
        if title or not out:
            out.append((eng, []))
            if title:
                continue
        out[-1][1].append((glb.strip(), PAREN.sub("", eng).strip()))
    return out


def label(glb, candidates):
    """dem / zero / unaligned for one NP, from its Globasa row."""
    toks = [t.lower() for t in GLB_TOKEN.findall(glb)]
    hits = [k for k, t in enumerate(toks) if t in candidates]
    if not hits:
        return "unaligned", ""
    for k in hits:
        j = k - 1
        while j >= 0 and toks[j] not in DEM and toks[j] not in NP_BREAK and k - j <= 3:
            j -= 1
        if j >= 0 and toks[j] in DEM:
            return "dem", toks[j]
    return "zero", ""


def mention_form(head, words):
    if head["upos"] == "PRON":
        return "pron"
    if head["upos"] == "PROPN":
        return "proper"
    dets = [w["lemma"].lower() for w in words if w["head"] == head["i"] and w["deprel"] in ("det", "det:poss")]
    for d in dets:
        if d in ("a", "an"):
            return "a"
        if d in ("this", "that", "these", "those"):
            return "this/that"
        if d == "the":
            return "the"
        return "poss/other"
    return "bare"


index = gloss_index()
df = pd.read_excel(GOLD, header=None, dtype=str).fillna("")
items = []
for title, rows in stories(df):
    text = "\n\n".join(e for _, e in rows)
    bounds, pos = [], 0
    for _, e in rows:
        bounds.append((pos, pos + len(e)))
        pos += len(e) + 2
    try:
        res = analyze(text)
    except Exception as e:
        sys.exit(f"coref_the: NLP service unavailable at {URL}: {e} -- start eng-nlp-service.py "
                 "(no fallback: the study measures the coref output itself)")
    words, chains = res["words"], res["coref"]
    mentions = sorted((m["start"], m["head"], k) for k, c in enumerate(chains) for m in c)
    for w in words:
        if w["lemma"].lower() != "the" or w["deprel"] != "det" or w["head"] < 0:
            continue
        head = words[w["head"]]
        if head["upos"] not in ("NOUN", "PROPN", "ADJ"):
            continue
        row = next(r for r, (a, b) in enumerate(bounds) if a <= head["start"] <= b)
        glb = rows[row][0]
        cands = index.get(head["lemma"].lower(), set())
        gold, dem_word = label(glb, cands) if cands else ("unaligned", "")
        k = chain_of(head, chains)
        prev = None
        if k is not None:
            before = [m for m in chains[k] if m["head"] != head["i"] and m["start"] < w["i"]]
            prev = max(before, key=lambda m: m["start"]) if before else None
        if prev:
            ph = words[prev["head"]]
            sent_dist = head["sent"] - ph["sent"]
            ment_dist = sum(1 for s, _, _ in mentions if prev["start"] < s < w["i"])
            rival = any(c != k and words[h]["lemma"].lower() == head["lemma"].lower()
                        and prev["start"] < s < w["i"] for s, h, c in mentions)
            pform, same_head = mention_form(ph, words), ph["lemma"].lower() == head["lemma"].lower()
        else:
            sent_dist = ment_dist = ""
            rival, pform, same_head = False, "", False
        quoted = len(QUOTES.findall(text[bounds[row][0]:head["start"]])) % 2 == 1
        items.append({
            "story": title, "row": row, "np": " ".join(x["text"] for x in words
                                                        if x["i"] >= w["i"] and x["i"] <= head["i"]),
            "head": head["lemma"].lower(), "role": head["deprel"],
            "in_chain": k is not None, "first_mention": k is not None and prev is None,
            "anaphoric": prev is not None, "sent_dist": sent_dist, "ment_dist": ment_dist,
            "prev_form": pform, "same_head": same_head, "rival": rival, "quoted": quoted,
            "gold": gold, "dem_word": dem_word, "eng": rows[row][1], "glb": glb})

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", newline="", encoding="utf-8") as f:
    wr = csv.DictWriter(f, fieldnames=list(items[0]), delimiter="\t")
    wr.writeheader()
    wr.writerows(items)

scored = [it for it in items if it["gold"] != "unaligned"]
print(f"'the' NPs: {len(items)}  aligned: {len(scored)}  unaligned: {len(items) - len(scored)}")
print("gold:", dict(Counter(it["gold"] for it in scored)))


def near(it, n):
    return it["anaphoric"] and it["sent_dist"] <= n


RULES = {
    "R0 always zero": lambda it: False,
    "R1 anaphoric": lambda it: it["anaphoric"],
    **{f"R2 anaphoric, <= {n} sent": (lambda n: lambda it: near(it, n))(n) for n in (0, 1, 2, 3)},
    **{f"R3 R2(<= {n}) and (rival or not subject)": (lambda n: lambda it: near(it, n) and (
        it["rival"] or not it["role"].startswith("nsubj")))(n) for n in (1, 2)},
    **{f"R4 R2(<= {n}) and antecedent 'a'": (lambda n: lambda it: near(it, n)
                                              and it["prev_form"] == "a")(n) for n in (1, 2, 3)},
    "R5 anaphoric, same head, not subject": lambda it: it["anaphoric"] and it["same_head"]
                                                        and not it["role"].startswith("nsubj"),
}
print(f"\n{'rule':42} {'tp':>4} {'fp':>4} {'fn':>4} {'tn':>4} {'P':>6} {'R':>6} {'F1':>6}")
for name, rule in RULES.items():
    c = Counter((rule(it), it["gold"] == "dem") for it in scored)
    tp, fp, fn, tn = c[True, True], c[True, False], c[False, True], c[False, False]
    p = tp / (tp + fp) if tp + fp else 0
    r = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * p * r / (p + r) if p + r else 0
    print(f"{name:42} {tp:4} {fp:4} {fn:4} {tn:4} {p:6.2f} {r:6.2f} {f1:6.2f}")


def bucket_table(name, key):
    print(f"\nP(dem | {name})")
    groups = defaultdict(Counter)
    for it in scored:
        groups[key(it)][it["gold"]] += 1
    for g in sorted(groups, key=str):
        c = groups[g]
        n = c["dem"] + c["zero"]
        print(f"  {str(g):24} n={n:4}  dem={c['dem']:3}  P={c['dem'] / n:.2f}")


bucket_table("chain status", lambda it: "anaphoric" if it["anaphoric"] else
             ("first mention" if it["first_mention"] else "no chain"))
bucket_table("sentence distance", lambda it: it["sent_dist"] if it["anaphoric"] else "-")
bucket_table("antecedent form", lambda it: it["prev_form"] or "-")
bucket_table("same head as antecedent", lambda it: it["same_head"] if it["anaphoric"] else "-")
bucket_table("rival same-head chain", lambda it: it["rival"])
bucket_table("role", lambda it: it["role"].split(":")[0])
bucket_table("quoted", lambda it: it["quoted"])
