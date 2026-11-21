"""Period senses: Wiktionary vs Webster 1913 vs pooled inventory, gold test + Wells/Lovecraft scan.

Each occurrence of a target word gets the sense whose PROTOTYPE is nearest (cosine of layer-8
word vectors, bert_words.py); a prototype = mean vector of the headword in the sense's examples
(fallback when it has none: the headword in "word: definition", flagged). Inventories
(period_senses.py):
  wiktionary  Wiktionary senses, Wiktionary quotations
  webster     Webster 1913 senses, Webster quotations and "as, ..." phrases
  pooled      Webster senses joined to Wiktionary senses (+ period-only Webster senses), both
              sets of examples (+ synonym substitution for senses without any); '+prior' adds
              PRIOR_W x prior(sense, year written): sense attested around the year +1, first
              attested well after it -1, dated/obsolete-tagged in a year >= 1950 -1 (never dropped)
  'grouped'   period_senses.choose(): the Wiktionary sense group (sub-senses under one heading)
              first, then the member
Encoders: A mBERT, B MacBERTh; C = MacBERTh rotated into mBERT space (Procrustes map fit on
the period sources, MAP_PERIOD=sources run of macberth_map.py) against mBERT prototypes.
Quotations sharing an 8-word sequence with any of the works are dropped (leakage).

1. Gold: obscure_resolved.tsv verdict dated_sense (The Time Machine). Gold senses = those whose
   definitions share most content words with the gold gloss (ties all gold); compared on the
   items every inventory covers. Globasa: glb_candidates() of the picked sense vs the curated
   rendering (obscure_resolved glb).
2. Scan: every occurrence of a target word in every Wells and Lovecraft work of works.tsv,
   pooled B+prior with the work's year; Globasa suggestion with how it was reached.

    ../venv/bin/python time-machine/period_sense_probe.py

Writes time-machine/period_sense_probe_report.txt, period_sense_probe_items.tsv (public works),
lovecraft/private/period_sense_probe_items.tsv (At the Mountains of Madness, git-ignored)."""
import csv
import glob
import os
import re
import sys
from collections import Counter, defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
os.chdir(ROOT)
import period_senses as ps  # noqa: E402
from bert_words import MACBERTH, MBERT, embed_cached, words  # noqa: E402

LAYER = 8
BIG = os.environ.get("GLOBASA_BIG_CACHE", "/media/paleos/Warehouse2/Language/Claude")
EMB_CACHE = os.path.join(BIG, "period_glb") if os.path.isdir(BIG) else None  # shared with period_glb.py
PRIOR_W = 0.05  # fixed beforehand; the sweep below is indicative only (tuned on the test)
MAPS = os.path.join(HERE, "cache", f"macberth_to_mbert_L{LAYER}_sources.npz")
REPORT = os.path.join(HERE, "period_sense_probe_report.txt")
ITEMS_PUBLIC = os.path.join(HERE, "period_sense_probe_items.tsv")
ITEMS_PRIVATE = os.path.join(ROOT, "lovecraft", "private", "period_sense_probe_items.tsv")
SPACY_POS = {"NOUN": "noun", "VERB": "verb", "AUX": "verb", "ADJ": "adj", "ADV": "adv",
             "ADP": "prep", "SCONJ": "conj", "CCONJ": "conj", "INTJ": "intj"}
OLD = {"dated", "archaic", "obsolete", "historical"}
MAX_WORDS = 120
NGRAM = 8
INVS = ("wiktionary", "webster", "pooled")
out_lines = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out_lines.append(s)


def first_year(text):
    m = re.search(r"\d{4}", text or "")
    return int(m.group()) if m else 1900


# ---------------------------------------------------------------- works
works = []
with open("works.tsv", encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        if r["author"] in ("H. G. Wells", "H. P. Lovecraft") and r["text"] and os.path.exists(r["text"]):
            works.append({"title": r["work"], "path": r["text"], "private": "PRIVATE" in r["notes"],
                          "year": first_year(r["written"])})
say("works: " + "; ".join(f"{w['title']} ({w['year']}{', private' if w['private'] else ''})" for w in works))

import spacy  # noqa: E402

nlp = spacy.load("en_core_web_sm", disable=["ner"])
ngrams = set()
for w in works:
    text = re.sub(r"\[p\. \d+\]", " ", open(w["path"], encoding="utf-8").read())
    paras = [" ".join(p.split()) for p in re.split(r"\n\s*\n", text)]
    w["sents"] = []
    for doc in nlp.pipe([p for p in paras if len(p) > 20 and not p.startswith("#")], batch_size=64):
        for s in doc.sents:
            toks = [t for t in s if not t.is_space]
            if 3 <= len(toks) <= MAX_WORDS:
                w["sents"].append([(t.text, t.lemma_.lower(), t.pos_, t.dep_) for t in toks])
    lw = [x.lower() for x in words(text)]
    ngrams.update(" ".join(lw[i:i + NGRAM]) for i in range(len(lw) - NGRAM + 1))
    del text, paras
del nlp


def keep_quote(ws):
    lw = [x.lower() for x in ws]
    return not any(" ".join(lw[i:i + NGRAM]) in ngrams for i in range(len(lw) - NGRAM + 1))


# ---------------------------------------------------------------- targets, inventory
gold_rows = [r for r in csv.DictReader(open(os.path.join(HERE, "obscure_resolved.tsv"), encoding="utf-8"),
                                       delimiter="\t") if r["verdict"] == "dated_sense"]
targets = {r["lemma"].strip().lower() for r in gold_rows if " " not in r["lemma"].strip()}
with open(os.path.join(HERE, "victorian_wordlist.tsv"), encoding="utf-8") as f:
    targets |= {r["headword"].lower() for r in csv.DictReader(f, delimiter="\t")
                if r["headword"] and " " not in r["headword"].strip()}
proposals = {}
for w in works:
    slug = re.sub(r"\W+", "_", w["title"].lower()).strip("_")
    for p in glob.glob(f"*/period_proposals_{slug}.tsv") + glob.glob(f"*/*/period_proposals_{slug}.tsv"):
        for r in csv.DictReader(open(p, encoding="utf-8"), delimiter="\t"):
            proposals[w["title"], r["lemma"].lower()] = r["sense"]
            targets.add(r["lemma"].lower())
inv, st = ps.build(targets, keep_quote)
say(f"{len(targets)} target lemmas; inventory: {st}")


def view(lemma, name):
    """(sense indices, {k: definitions}, {k: examples}) of one inventory."""
    idx, defs, exs = [], {}, {}
    for k, s in enumerate(inv[lemma]):
        if name == "wiktionary" and s["source"] in ("wiktionary", "both"):
            d, e = [s["gloss"]], [x for x in s["examples"] if x[2] == "wiktionary"]
        elif name == "webster" and s["source"] in ("webster", "both"):
            d = s["defs"][1:] if s["source"] == "both" else s["defs"]
            e = [x for x in s["examples"] if x[2] == "webster"]
        elif name == "pooled":
            d, e = s["defs"], [x for x in s["examples"] if x[2] != "gloss fallback"]
        else:
            continue
        idx.append(k)
        defs[k] = d
        exs[k] = e or [([lemma, ":"] + words(d[0])[:MAX_WORDS - 2], 0, "fallback")]
    return idx, defs, exs


views = {(l, n): view(l, n) for l in inv for n in INVS}

# ---------------------------------------------------------------- occurrences
STOP = ps.STOP
content = ps.content
tm = next(w for w in works if w["title"] == "The Time Machine")
norm = lambda s: " ".join(re.findall(r"\w+", s.lower()))
tm_norm = [norm(" ".join(t[0] for t in s)) for s in tm["sents"]]
occ, skipped = [], Counter()
for r in gold_rows:
    lemma = r["lemma"].strip().lower()
    if " " in lemma or lemma not in inv:
        skipped["multiword or no senses"] += 1
        continue
    q = norm(r["quote"])
    si = next((i for i, t in enumerate(tm_norm) if q and q in t), None)
    if si is None:
        skipped["quote not found"] += 1
        continue
    ti = next((i for i, t in enumerate(tm["sents"][si]) if t[1] == lemma or ps.form_matches(t[0], lemma)), None)
    if ti is None:
        skipped["word not found"] += 1
        continue
    gold = {}
    for n in INVS:
        idx, defs, _ = views[lemma, n]
        ov = {k: max(len(content(r["sense"]) & content(d)) for d in defs[k]) for k in idx}
        best = max(ov.values()) if ov else 0
        gold[n] = {k for k, o in ov.items() if o == best} if best else set()
    if not any(gold.values()):
        skipped["gold gloss matches no sense"] += 1
        continue
    t = tm["sents"][si][ti]
    occ.append({"work": tm["title"], "year": tm["year"], "sent": si, "idx": ti, "lemma": lemma,
                "pos": t[2], "dep": t[3], "gold": gold, "glb_gold": r["glb"], "gold_text": r["sense"]})
n_gold = len(occ)
say(f"gold items: {n_gold} of {len(gold_rows)} (skipped {dict(skipped)})")
gold_keys = {(o["sent"], o["idx"]) for o in occ}
for w in works:
    for si, toks in enumerate(w["sents"]):
        for ti, t in enumerate(toks):
            if t[1] in inv and t[2] in SPACY_POS and not (w["title"] == tm["title"] and (si, ti) in gold_keys):
                occ.append({"work": w["title"], "year": w["year"], "sent": si, "idx": ti, "lemma": t[1],
                            "pos": t[2], "dep": t[3], "gold": None})
say(f"corpus occurrences: {len(occ) - n_gold} (+ {n_gold} gold)")


def candidates(o, n):
    idx = views[o["lemma"], n][0]
    ss = inv[o["lemma"]]
    pos = SPACY_POS.get(o["pos"])
    if pos == "noun" and o["dep"] in ("amod", "compound") and any(ss[k]["pos"] == "adj" for k in idx):
        pos = "adj"
    c = [k for k in idx if ss[k]["pos"] == pos]
    if o["gold"] is not None and not (set(c) & o["gold"][n]):
        c = []
    return c or idx


# ---------------------------------------------------------------- embeddings
by_work = {w["title"]: w for w in works}
occ_sents = sorted({(o["work"], o["sent"]) for o in occ})
occ_row = {k: i for i, k in enumerate(occ_sents)}
ex_keys = {}
for (lemma, n), (idx, _, exs) in views.items():
    for k in idx:
        for ws, j, _ in exs[k]:
            ex_keys.setdefault((tuple(ws), j), len(ex_keys))
ex_list = sorted(ex_keys, key=ex_keys.get)
maps = np.load(MAPS)
W_proc, mu_mac_map = maps["W_procrustes"], maps["mean_macberth"]


def unit(x):
    return x / (np.linalg.norm(x, axis=-1, keepdims=True) + 1e-8)


vec = {}
for name in (MBERT, MACBERTH):
    sv = embed_cached(name, [[t[0] for t in by_work[w]["sents"][s]] for w, s in occ_sents], LAYER, EMB_CACHE)
    ev = embed_cached(name, [list(ws) for ws, _ in ex_list], LAYER, EMB_CACHE)
    o_raw = np.stack([np.nan_to_num(sv[occ_row[o["work"], o["sent"]]][o["idx"]]) for o in occ])
    e_raw = np.stack([np.nan_to_num(v[j]) for v, (_, j) in zip(ev, ex_list)])
    del sv, ev
    mu = e_raw.mean(0)
    vec[name] = (unit(o_raw - mu), unit(e_raw - mu))
    if name == MACBERTH:
        vec["C"] = unit(unit(o_raw - mu_mac_map) @ W_proc)
    del o_raw, e_raw
ENC = {"A": (vec[MBERT][0], vec[MBERT][1]), "B": (vec[MACBERTH][0], vec[MACBERTH][1]),
       "C": (vec["C"], vec[MBERT][1])}
protos = {}
for enc, (_, exv) in ENC.items():
    if enc == "C":
        protos["C"] = protos["A"]
        continue
    p = {}
    for (lemma, n), (idx, _, exs) in views.items():
        grp = ps.groups(inv[lemma])
        g_rows = defaultdict(list)
        for k in idx:
            rows = [ex_keys[tuple(ws), j] for ws, j, _ in exs[k]]
            p[lemma, n, k] = unit(exv[rows].mean(0))
            g_rows[grp[k]] += rows
        for g, rows in g_rows.items():  # group prototype: all members' examples in this inventory
            p[lemma, n, g] = unit(exv[rows].mean(0))
    protos[enc] = p


def pick(o, i, enc, n, prior_w=0.0, grouped=False):
    occv = ENC[enc][0][i]
    cand = o["cand"][n]
    if not cand:
        return None  # the lemma has no sense in this inventory
    P = protos[enc]
    if grouped:  # period_senses.choose(): sense group first, then the member
        ss = inv[o["lemma"]]
        grp = ps.groups(ss)
        sim = {k: float(occv @ P[o["lemma"], n, k]) for k in cand}
        gsim = {grp[k]: float(occv @ P[o["lemma"], n, grp[k]]) for k in cand}
        return ps.choose(ss, cand, sim, gsim, o["year"], prior_w)[0]
    sc = [float(occv @ P[o["lemma"], n, k]) + prior_w * ps.prior(inv[o["lemma"]][k], o["year"])
          for k in cand]
    return cand[int(np.argmax(sc))]


CONDS = ([(enc, n, 0.0, False) for n in INVS for enc in ("A", "B")]
         + [("C", "pooled", 0.0, False), ("A", "pooled", PRIOR_W, False), ("B", "pooled", PRIOR_W, False),
            ("B", "wiktionary", 0.0, True), ("B", "wiktionary", PRIOR_W, True), ("B", "pooled", PRIOR_W, True)])
label = lambda c: f"{c[0]} {c[1]}{'+prior' if c[2] else ''}{' grouped' if c[3] else ''}"
for i, o in enumerate(occ):
    o["cand"] = {n: candidates(o, n) for n in INVS}
    o["pick"] = {c: pick(o, i, *c) for c in CONDS}

# ---------------------------------------------------------------- 1. gold
gold = [o for o in occ[:n_gold] if all(o["gold"][n] for n in INVS)]
say(f"\n== 1. The Time Machine gold: {len(gold)} items every inventory covers (of {n_gold}) ==")
for n in INVS:
    ch = np.mean([len(set(o["cand"][n]) & o["gold"][n]) / len(o["cand"][n]) for o in gold])
    first = np.mean([o["cand"][n][0] in o["gold"][n] for o in gold])
    say(f"  {n:11s} chance {100 * ch:5.1f}%  first sense {100 * first:5.1f}%  "
        f"senses {np.mean([len(o['cand'][n]) for o in gold]):.1f}")
for c in CONDS:
    right = sum(o["pick"][c] in o["gold"][c[1]] for o in gold)
    say(f"  {label(c):22s} {right:3d}/{len(gold)} = {100 * right / len(gold):5.1f}%")
say("  prior weight sweep, B pooled (indicative only: chosen on this test):")
for wgt in (0.0, 0.02, 0.05, 0.1, 0.2):
    right = sum(pick(o, occ.index(o), "B", "pooled", wgt, True) in o["gold"]["pooled"] for o in gold)
    say(f"    {wgt:4.2f}: {right}/{len(gold)}")

# Globasa suggestions vs the curated rendering
glb_words = lambda s: set(re.findall(r"[a-z]+", (s or "").lower()))
best = ("B", "pooled", PRIOR_W, True)
hits, how = Counter(), Counter()
for o in [o for o in occ[:n_gold]]:
    curated = glb_words(o["glb_gold"])
    if not curated:
        continue
    hits["items"] += 1
    sug = ps.glb_candidates(inv[o["lemma"]][o["pick"][best]]) if o["pick"][best] is not None else []
    hits["picked sense"] += any(g in curated for g, _ in sug)
    if sug:
        hits["picked sense has a suggestion"] += 1
        how[re.sub(r" \(.*", "", sug[0][1]) + (" (fallback)" if "fallback" in sug[0][1] else "")] += 1
    if o["gold"]["pooled"]:
        gs = [g for k in o["gold"]["pooled"] for g, _ in ps.glb_candidates(inv[o["lemma"]][k])]
        hits["gold sense (oracle)"] += any(g in curated for g in gs)
    allw = {g for s in inv[o["lemma"]] for g, _ in ps.glb_candidates(s, n=10)}
    hits["any sense of the lemma"] += any(g in curated for g in allw)
say(f"\n  Globasa: suggestion (top 3) contains a word of the curated rendering, {hits['items']} gold items:")
for k in ("picked sense", "gold sense (oracle)", "any sense of the lemma"):
    say(f"    {k:24s} {hits[k]:3d} ({100 * hits[k] / max(hits['items'], 1):4.1f}%)")
say(f"    picked sense has a suggestion: {hits['picked sense has a suggestion']}; first route: {dict(how)}")

# ---------------------------------------------------------------- 2. scan
say("\n== 2. Corpus scan: pooled B+prior (work's year) vs Wiktionary B ==")
say(f"  {'work':30s} {'occ':>5s} {'old B-wikt':>10s} {'old pooled':>10s} {'same':>6s} {'webster-only':>12s}"
    f" {'prop.':>5s} {'=wikt':>6s} {'=pooled':>7s} {'glb sugg.':>9s}")
wk = ("B", "wiktionary", 0.0, False)
for w in works:
    os_ = [o for o in occ if o["work"] == w["title"] and o["pick"][wk] is not None and o["pick"][best] is not None]
    if not os_:
        continue
    n = len(os_)
    is_old = lambda s: bool(s["tags"] & OLD or s["labels"] & ps.OLD_LABELS)
    old_w = sum(is_old(inv[o["lemma"]][o["pick"][wk]]) for o in os_)
    old_p = sum(is_old(inv[o["lemma"]][o["pick"][best]]) for o in os_)
    same = sum(o["pick"][wk] == o["pick"][best] for o in os_)
    wonly = sum(inv[o["lemma"]][o["pick"][best]]["source"] == "webster" for o in os_)
    per_lemma = defaultdict(list)
    for o in os_:
        if (w["title"], o["lemma"]) in proposals:
            per_lemma[o["lemma"]].append(o)
    pa = Counter()
    for lemma, lo in per_lemma.items():
        want = proposals[w["title"], lemma].strip().lower()
        for c in (wk, best):
            top = Counter(x["pick"][c] for x in lo).most_common(1)[0][0]
            pa[c] += inv[lemma][top]["gloss"].strip().lower() == want
    sug = sum(bool(ps.glb_candidates(inv[o["lemma"]][o["pick"][best]])) for o in os_)
    say(f"  {w['title'][:30]:30s} {n:5d} {100 * old_w / n:9.1f}% {100 * old_p / n:9.1f}% {100 * same / n:5.1f}%"
        f" {wonly:12d} {len(per_lemma):5d} {pa[wk]:6d} {pa[best]:7d} {100 * sug / n:8.1f}%")

diff = Counter()
for o in occ:
    if not by_work[o["work"]]["private"] and None not in (o["pick"][wk], o["pick"][best]) and o["pick"][wk] != o["pick"][best]:
        a, b = inv[o["lemma"]][o["pick"][wk]], inv[o["lemma"]][o["pick"][best]]
        diff[o["lemma"], a["gloss"][:45], b["gloss"][:45] + f" [{b['source']}]"] += 1
say("\n  most frequent changes, Wiktionary B -> pooled B+prior (public works):")
for (lemma, a, b), v in diff.most_common(25):
    say(f"    {v:3d}  {lemma} | {a} | {b}")

# ---------------------------------------------------------------- outputs
cols = ["work", "year", "lemma", "pos", "sentence", "gold", "wiktionary_B", "pooled_B_prior", "source",
        "prior", "glb_suggestion", "glb_how", "glb_curated"]


def fmt(s):
    old = sorted((s["tags"] & OLD) | s["labels"])
    return s["gloss"][:150] + (f" [{','.join(old)}]" if old else "")


def row(o):
    ss = inv[o["lemma"]]
    if o["pick"][best] is None:
        return None
    b = ss[o["pick"][best]]
    sug = ps.glb_candidates(b)
    toks = by_work[o["work"]]["sents"][o["sent"]]
    return {"work": o["work"], "year": o["year"], "lemma": o["lemma"], "pos": o["pos"],
            "sentence": " ".join(("**" + t[0] + "**") if i == o["idx"] else t[0] for i, t in enumerate(toks)),
            "gold": " / ".join(fmt(ss[k]) for k in sorted(o["gold"]["pooled"])) if o["gold"] else "",
            "wiktionary_B": fmt(ss[o["pick"][wk]]) if o["pick"][wk] is not None else "", "pooled_B_prior": fmt(b), "source": b["source"],
            "prior": ps.prior(b, o["year"]), "glb_suggestion": ", ".join(g for g, _ in sug),
            "glb_how": sug[0][1] if sug else "", "glb_curated": o.get("glb_gold", "")}


for path, private in ((ITEMS_PUBLIC, False), (ITEMS_PRIVATE, True)):
    with open(path, "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=cols, delimiter="\t")
        wr.writeheader()
        wr.writerows(r for r in (row(o) for o in occ if by_work[o["work"]]["private"] == private) if r)
open(REPORT, "w", encoding="utf-8").write("\n".join(out_lines) + "\n")
say(f"\nreport: {REPORT}\nitems: {ITEMS_PUBLIC}\nprivate items: {ITEMS_PRIVATE}")
