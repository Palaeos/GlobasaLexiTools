"""Globasa proposals for old terms and senses: period text (or words) + year -> ranked Globasa.

    ../venv/bin/python time-machine/period_glb.py work "The War of the Worlds" [--apply]
    ../venv/bin/python time-machine/period_glb.py text path/to/text.txt 1897 [--apply]
    ../venv/bin/python time-machine/period_glb.py words 1895 presently queer [--context "Presently I ..."]

Pipeline (the measured best set-up of period_sense_probe.py, MacBERTh pooled + year prior; for
texts from 1950 on a modern encoder, PERIOD_GLB_MODERN, default mBERT):
 1. Find: every content word of the text; a lemma is a candidate when it is RARE (lemma and
    surface below Zipf 3.0 in modern English, as scan_obscure.py) or has a NON-CURRENT sense in a
    part of speech it has in the text: Wiktionary dated/archaic/obsolete/historical, Webster 1913
    [Obs.]/[Archaic]/[Poetic]/[R.], or (weaker) last quoted before 1950 with >= QUOTES_MIN dated
    quotations.
 2. Sense: each occurrence -> period_senses.choose() over period_senses.build() (Wiktionary +
    Webster 1913 pooled, period dictionaries attached): the Wiktionary sense GROUP (sub-senses
    under one heading) whose MacBERTh prototype is nearest + PRIOR_W x prior for the year, then
    the member of that group. Kept: occurrences of rare lemmas, and occurrences whose picked sense is
    non-current AND whose group beats the best group holding a current sense by >= MARGIN.
    tier: 'likely' = labelled old sense; 'possible' = old only by its quotation dates; 'rare' =
    rare word (any sense).
 3. Globasa, strongest evidence first: curated row (victorian_wordlist.tsv / obscure_resolved.tsv
    matched to the sense) > vetted Wiktionary sense (vetted_senses.tsv) > period Esperanto
    (Rhodes/O'Connor) via the word list > Spanish only (labelled: 1910 Spanish may have
    drifted) > modern Wiktionary tables (fallback) > 'needs rendering' with the definition.
 4. Output: <work folder>/period_glb_<slug>.tsv (text/words mode: time-machine/cache/), one row
    per (lemma, sense) with counts, examples, routes. --apply (years <= 1914 only: the list is
    Victorian/Edwardian) appends the 'likely' and 'rare' rows that have a Globasa word and are not
    in the list yet to victorian_wordlist.tsv as apertium=pending; existing rows never change.
Script tier: proposals for review, not decisions. Embeddings are cached on GLOBASA_BIG_CACHE
(Warehouse2), so a second run of a work is fast.
The Time Machine run also prints recall against the hand-made glossary (obscure_resolved.tsv)."""
import csv
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
import wordlist_tags as wt  # noqa: E402
from bert_words import MACBERTH, MBERT, embed_cached, words  # noqa: E402

LAYER = 8
PRIOR_W = 0.05
# encoder by the text's year: MacBERTh (trained on 1450-1950 text) has barely seen modern senses
# (gay 'homosexual': 1/3 modern sentences vs mBERT 2/3, RoBERTa 2/3; period: MacBERTh 2/2,
# mBERT 1/2), so texts from MODERN_FROM on use a modern encoder
MODERN_ENCODER = os.environ.get("PERIOD_GLB_MODERN", MBERT)


def encoder(year):
    return MACBERTH if year < ps.MODERN_FROM else MODERN_ENCODER
MARGIN = 0.03
# 'last quoted before 1950' counts only with >= QUOTES_MIN dated quotations: one late-ending
# quotation is noise (2026-11-21: 1,218 'possible' rows, mostly single-quote senses)
QUOTES_MIN = 2
ZIPF_MAX = 3.0
APPLY_MAX_YEAR = 1914
BIG = os.environ.get("GLOBASA_BIG_CACHE", "/media/paleos/Warehouse2/Language/Claude")
EMB_CACHE = os.path.join(BIG, "period_glb") if os.path.isdir(BIG) else None
OLD_LABELS = {"Obs.", "Obs", "Archaic", "Poetic", "R."}
CONTENT_POS = {"NOUN": "noun", "VERB": "verb", "ADJ": "adj", "ADV": "adv"}
MAX_WORDS = 120


# ---------------------------------------------------------------- arguments
args = sys.argv[1:]
APPLY = "--apply" in args
args = [a for a in args if a != "--apply"]
CONTEXT = None
if "--context" in args:
    i = args.index("--context")
    CONTEXT = args[i + 1]
    args = args[:i] + args[i + 2:]
if not args or args[0] not in ("work", "text", "words"):
    sys.exit(__doc__)
MODE = args[0]


def first_year(text):
    m = re.search(r"\d{4}", text or "")
    return int(m.group()) if m else None


def old_evidence(s, quotes_min=QUOTES_MIN):
    """'labelled' / 'quotes end <1950' / '' -- why the sense counts as not current today.
    years = (first, last, number of dated quotations)."""
    if s["tags"] & ps.OLD_TAGS or s["labels"] & OLD_LABELS:
        return "labelled"
    y = s.get("years")
    if y and y[1] < 1950 and y[2] >= quotes_min:
        return "quotes end <1950"
    return ""


# ---------------------------------------------------------------- Globasa routes
ENG_TAG_POS = {"n": "noun", "vblex": "verb", "vbmod": "verb", "adj": "adj", "adv": "adv", "pr": "prep",
               "cnjsub": "conj", "cnjcoo": "conj", "ij": "intj"}
_, vw = wt.read_tsv(wt.WL)
_, gl = wt.read_tsv(wt.GLOSSARY)
tag_of = {(r["headword"].lower(), r["glb"].strip()): ENG_TAG_POS.get(r["eng_tags"].split(".")[0]) for r in vw}
# (headword, sense, glb, part of speech or None, how)
curated_rows = [(r["headword"].lower(), r["sense"], r["glb"].strip(), tag_of[r["headword"].lower(), r["glb"].strip()],
                 f"curated: victorian_wordlist (apertium={r['apertium']})") for r in vw if r.get("glb", "").strip()]
curated_rows += [(r["lemma"].lower(), r["sense"], r["glb"].strip(), tag_of.get((r["lemma"].lower(), r["glb"].strip())),
                  "curated: obscure_resolved glossary")
                 for r in gl if r.get("glb", "").strip() and r.get("verdict") != "transparent"]
in_list = set(tag_of)


def stems(text):
    return {w[:5] for w in ps.content(text)}


def curated_for(lemma, inv_l):
    """{sense index: [(glb, how)]} -- each curated row goes to the sense of its part of speech
    (when known) whose definitions share most 5-letter stems with its gloss (>= 1; a tie goes
    to every tied sense, labelled)."""
    out = defaultdict(list)
    for head, sense, glb, pos, how in curated_rows:
        if head != lemma:
            continue
        sc = [max(len(stems(sense) & stems(d)) for d in s["defs"]) if pos in (None, s["pos"]) else 0
              for s in inv_l]
        best = max(sc) if sc else 0
        if best:
            tied = [k for k, x in enumerate(sc) if x == best]
            for k in tied:
                out[k].append((glb, how if len(tied) == 1 else how + " (fallback: gloss matches several senses)"))
    return out


def vetted_for(lemmas):
    """{(lemma, pos, gloss): [glb]} from accepted vetted senses (sense key -> definition)."""
    import vetted_senses
    from sense_rows import match_sense_to_definition
    from wiktionary_db import WiktionaryDB
    rows = [r for r in vetted_senses.load_rows(sync_first=False)
            if r["App?"] == "s" and r["Tier"] in ("v", "e") and r["Eng"].lower() in lemmas]
    out = defaultdict(list)
    with WiktionaryDB() as db:
        cache = {}
        for r in rows:
            key = (r["Eng"].lower(), r["Prt of Sp"])
            if key not in cache:
                cache[key] = db.get_senses(*key) or []
            m = match_sense_to_definition(r["Wiktionary Sense"], cache[key])
            if m is not None and m.glosses:  # same key as period_senses: the specific (last) gloss
                out[key[0], key[1], m.glosses[-1].strip()].append(r["Glb"])
    return out


def routes(lemma, k, inv_l, cur, vet):
    s = inv_l[k]
    out = list(cur.get(k, []))
    out += [(g, "vetted Wiktionary sense") for g in dict.fromkeys(vet.get((lemma, s["pos"], s["gloss"].strip()), []))]
    out += ps.glb_candidates(s)
    seen, res = set(), []
    for g, how in out:
        g = g.strip()
        if g and g not in seen:
            seen.add(g)
            res.append((g, how))
    return res


def definition(s):
    return " / ".join(dict.fromkeys(d for d in s["defs"] if d))[:200]


# ---------------------------------------------------------------- words mode
if MODE == "words":
    year = int(args[1])
    lemmas = [w.lower() for w in args[2:]]
    inv, _ = ps.build(lemmas)
    vet = vetted_for(set(lemmas))
    occ = None
    if CONTEXT:
        cw = words(CONTEXT)
    for lemma in lemmas:
        if lemma not in inv:
            print(f"\n{lemma}: no Wiktionary or Webster senses")
            continue
        ss = inv[lemma]
        cur = curated_for(lemma, ss)
        print(f"\n== {lemma} ({year}) ==")
        order = list(range(len(ss)))
        if CONTEXT:
            idx = next((i for i, w in enumerate(cw) if ps.form_matches(w, lemma)), None)
            if idx is None:
                print("  (context does not contain the word)")
            else:
                exs = [(lemma, k, x) for k, s in enumerate(ss) for x in s["examples"]]
                vecs = embed_cached(encoder(year), [cw] + [list(x[0]) for _, _, x in exs], LAYER, EMB_CACHE)
                occv = np.nan_to_num(vecs[0][idx])
                ev = np.stack([np.nan_to_num(v[x[1]]) for v, (_, _, x) in zip(vecs[1:], exs)])
                mu = ev.mean(0)
                unit = lambda x: x / (np.linalg.norm(x, axis=-1, keepdims=True) + 1e-8)
                ev, occv = unit(ev - mu), unit(occv - mu)
                grp = ps.groups(ss)
                sim = {k: float(occv @ unit(ev[[i for i, (_, kk, _) in enumerate(exs) if kk == k]].mean(0)))
                       for k in range(len(ss))}
                gsim = {g: float(occv @ unit(ev[[i for i, (_, kk, _) in enumerate(exs) if grp[kk] == g]].mean(0)))
                        for g in set(grp.values())}
                pick, gscore = ps.choose(ss, list(range(len(ss))), sim, gsim, year, PRIOR_W)
                # the pick first, then by group score, then by the member's own score
                order = sorted(range(len(ss)), key=lambda k: (k != pick, -gscore[k],
                                                             -(sim[k] + PRIOR_W * ps.prior(ss[k], year))))
                print(f"  context: {CONTEXT}")
        for rank, k in enumerate(order[: (5 if CONTEXT else len(ss))]):
            s = ss[k]
            ev = old_evidence(s)
            if not CONTEXT and not ev and ps.prior(s, year) < 1:
                continue
            r = routes(lemma, k, ss, cur, vet)
            mark = "->" if CONTEXT and rank == 0 else "  "
            print(f" {mark} [{s['pos']}] {definition(s)}")
            print(f"      old: {ev or 'no'}; prior {ps.prior(s, year):+d}; source {s['source']}"
                  + (f"; quoted {s['years'][0]}-{s['years'][1]}" if s.get("years") else ""))
            print("      Globasa: " + ("; ".join(f"{g} ({how})" for g, how in r[:3]) if r
                                       else "needs rendering (no curated, vetted or dictionary route)"))
    sys.exit(0)

# ---------------------------------------------------------------- work / text mode
if MODE == "work":
    title = args[1].lower()
    with open("works.tsv", encoding="utf-8") as f:
        work = next((r for r in csv.DictReader(f, delimiter="\t") if r["work"].lower().startswith(title)), None)
    if not work or not work["text"]:
        sys.exit(f"no work with a text file starting with {args[1]!r} in works.tsv")
    path, year, name, folder = work["text"], first_year(work["written"]), work["work"], work["folder"]
else:
    path, year = args[1], int(args[2])
    name, folder = os.path.splitext(os.path.basename(path))[0], os.path.join("time-machine", "cache")
slug = re.sub(r"\W+", "_", name.lower()).strip("_")
OUT = os.path.join(folder, f"period_glb_{slug}.tsv")
print(f"{name} ({year}) -> {OUT}")

import spacy  # noqa: E402
from wordfreq import zipf_frequency  # noqa: E402

nlp = spacy.load("en_core_web_sm", disable=["ner"])
text = re.sub(r"\[p\. \d+\]", " ", open(path, encoding="utf-8").read())
sents = []
for doc in nlp.pipe([" ".join(p.split()) for p in re.split(r"\n\s*\n", text)
                     if len(p.strip()) > 20 and not p.strip().startswith("#")], batch_size=64):
    for s in doc.sents:
        toks = [t for t in s if not t.is_space]
        if 3 <= len(toks) <= MAX_WORDS:
            sents.append([(t.text, t.lemma_.lower(), t.pos_, t.dep_) for t in toks])
del nlp, text

lemma_pos = Counter((t[1], t[2]) for s in sents for t in s if t[2] in CONTENT_POS and t[1].isalpha() and len(t[1]) > 2)
lemmas = {l for l, _ in lemma_pos}
rare = {l for l in lemmas if zipf_frequency(l, "en") < ZIPF_MAX}
inv, st = ps.build(lemmas)
pos_in_text = defaultdict(set)
for l, p in lemma_pos:
    pos_in_text[l].add(CONTENT_POS[p])
    if p == "NOUN":
        pos_in_text[l].add("adj")  # attributive nouns may take adjective senses (below)


def has_old_sense(l, quotes_min=QUOTES_MIN):
    """An old sense in a part of speech the lemma has in this text (any, if none matches)."""
    ss = [s for s in inv[l] if s["pos"] in pos_in_text[l]] or inv[l]
    return any(old_evidence(s, quotes_min) for s in ss)


relevant = {l for l in inv if l in rare or has_old_sense(l)}
loose = sum(1 for l in inv if l in rare or any(old_evidence(s, 1) for s in inv[l]))
print(f"{len(lemmas)} content lemmas, {len(rare)} rare, {len(relevant)} candidates "
      f"(pre-2026-11-21 rule, any old sense, single quotation enough: {loose}); inventory {st}")

occ = [(si, ti) for si, s in enumerate(sents) for ti, t in enumerate(s)
       if t[1] in relevant and t[2] in CONTENT_POS]
exs = [(l, k, x) for l in sorted(relevant) for k, s in enumerate(inv[l]) for x in s["examples"]]
occ_sents = sorted({si for si, _ in occ})
print(f"{len(occ)} occurrences in {len(occ_sents)} sentences; {len(exs)} sense examples to embed (cached: {EMB_CACHE})")
ENC = encoder(year)
print(f"encoder: {ENC}")
sv = embed_cached(ENC, [[t[0] for t in sents[si]] for si in occ_sents], LAYER, EMB_CACHE)
row_of = {si: i for i, si in enumerate(occ_sents)}
ev = embed_cached(ENC, [list(x[0]) for _, _, x in exs], LAYER, EMB_CACHE)
E = np.stack([np.nan_to_num(v[x[1]]) for v, (_, _, x) in zip(ev, exs)])
del ev
mu = E.mean(0)
unit = lambda x: x / (np.linalg.norm(x, axis=-1, keepdims=True) + 1e-8)
E = unit(E - mu)
proto_rows = defaultdict(list)
for i, (l, k, _) in enumerate(exs):
    proto_rows[l, k].append(i)
protos = {key: unit(E[rows].mean(0)) for key, rows in proto_rows.items()}
grp_of = {l: ps.groups(inv[l]) for l in relevant}
gproto_rows = defaultdict(list)
for i, (l, k, _) in enumerate(exs):
    gproto_rows[l, grp_of[l][k]].append(i)
gprotos = {key: unit(E[rows].mean(0)) for key, rows in gproto_rows.items()}
del E

agg = defaultdict(lambda: {"n": 0, "margins": [], "examples": [], "forms": set()})
picked_old = []  # (lemma, sense, margin) of every rare-lemma or old-sense pick, before the margin filter
for si, ti in occ:
    t = sents[si][ti]
    l, ss = t[1], inv[t[1]]
    pos = CONTENT_POS[t[2]]
    if pos == "noun" and t[3] in ("amod", "compound") and any(s["pos"] == "adj" for s in ss):
        pos = "adj"
    cand = [k for k, s in enumerate(ss) if s["pos"] == pos] or list(range(len(ss)))
    v = unit(np.nan_to_num(sv[row_of[si]][ti]) - mu)
    sim = {j: float(v @ protos[l, j]) for j in cand}
    gsim = {grp_of[l][j]: float(v @ gprotos[l, grp_of[l][j]]) for j in cand}
    k, gscore = ps.choose(ss, cand, sim, gsim, year, PRIOR_W)  # group first, then member
    old = old_evidence(ss[k])
    if l not in rare and not old:
        continue
    # margin over the best group that holds a current sense (0 if that is the pick's own group)
    current = [gscore[j] for j in cand if not old_evidence(ss[j])]
    margin = gscore[k] - max(current) if current else 1.0
    picked_old.append((l, k, margin))
    # keep an old pick only when it beats every current sense group by MARGIN (2026-11-21:
    # 'some old sense' flagged 2,875 of 3,451 lemmas of The Time Machine)
    if l not in rare and margin < MARGIN:
        continue
    a = agg[l, k]
    a["n"] += 1
    a["margins"].append(margin)
    a["forms"].add(t[0].lower())
    if len(a["examples"]) < 2:
        a["examples"].append(" ".join(("**" + x[0] + "**") if j == ti else x[0] for j, x in enumerate(sents[si])))
del sv

vet = vetted_for({l for l, _ in agg})
rows = []
for (l, k), a in agg.items():
    s = inv[l][k]
    old = old_evidence(s)
    m = float(np.median(a["margins"]))
    tier = "rare" if l in rare else ("likely" if old == "labelled" and m >= MARGIN else "possible")
    r = routes(l, k, inv[l], curated_for(l, inv[l]), vet)
    rows.append({"lemma": l, "pos": s["pos"], "sense": definition(s), "sense_source": s["source"],
                 "old_evidence": old or "-", "years": f"{s['years'][0]}-{s['years'][1]}" if s.get("years") else "",
                 "prior": ps.prior(s, year), "tier": tier, "count": a["n"], "margin": f"{m:.3f}",
                 "glb": r[0][0] if r else "", "glb_how": r[0][1] if r else "needs rendering (LLM/human tier)",
                 "alternatives": "; ".join(f"{g} ({h})" for g, h in r[1:4]),
                 "in_wordlist": "yes" if r and (l, r[0][0]) in in_list else "",
                 "attested": "; ".join(sorted(a["forms"])), "example1": a["examples"][0],
                 "example2": a["examples"][1] if len(a["examples"]) > 1 else ""})
TIER_ORDER = {"likely": 0, "rare": 1, "possible": 2}
rows.sort(key=lambda r: (TIER_ORDER[r["tier"]], -r["count"], r["lemma"]))
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
    w.writeheader()
    w.writerows(rows)
how = Counter(re.sub(r" \(.*|:.*", "", r["glb_how"]) for r in rows)
print(f"{len(rows)} proposals: tiers {dict(Counter(r['tier'] for r in rows))}; "
      f"first route {dict(how)}; already in the word list {sum(bool(r['in_wordlist']) for r in rows)}")

# ---------------------------------------------------------------- recall against the glossary
if name == "The Time Machine":
    gold = [r for r in gl if r["verdict"] in ("dated_sense", "obscure") and " " not in r["lemma"].strip()]
    flagged = {r["lemma"] for r in rows}
    for v in ("dated_sense", "obscure"):
        g = {r["lemma"].lower() for r in gold if r["verdict"] == v}
        print(f"  glossary {v}: {len(g & flagged)}/{len(g)} lemmas flagged "
              f"({100 * len(g & flagged) / max(len(g), 1):.0f}%)")
    # the candidate filter, variant by variant (lemma recall; senses are not checked)
    print("  filter variants (rows = lemma+sense proposals; recall dated_sense / obscure):")
    g_by = {v: {r["lemma"].lower() for r in gold if r["verdict"] == v} for v in ("dated_sense", "obscure")}
    variants = {
        "rare or old pick (no margin)": lambda l, k, m: True,
        "rare or old pick beating current by MARGIN": lambda l, k, m: l in rare or m >= MARGIN,
        "rare or labelled old pick beating by MARGIN": lambda l, k, m: l in rare or (
            m >= MARGIN and old_evidence(inv[l][k]) == "labelled"),
    }
    for vname, keep in variants.items():
        kept = {(l, k) for l, k, m in picked_old if keep(l, k, m)}
        fl = {l for l, _ in kept}
        print(f"    {vname:45s} rows {len(kept):5d} lemmas {len(fl):5d}  "
              + "  ".join(f"{len(g & fl)}/{len(g)} ({100 * len(g & fl) / max(len(g), 1):.0f}%)"
                          for g in g_by.values()))
    known = {r["lemma"].lower() for r in gl} | {r["headword"].lower() for r in vw}
    lk = [r for r in rows if r["tier"] == "likely"]
    print(f"  'likely' rows whose lemma the glossary/word list already has: "
          f"{sum(r['lemma'] in known for r in lk)}/{len(lk)}")

# ---------------------------------------------------------------- --apply
if APPLY:
    if year > APPLY_MAX_YEAR:
        sys.exit(f"--apply refused: {year} is after {APPLY_MAX_YEAR}; victorian_wordlist.tsv is "
                 f"Victorian/Edwardian. Proposals stay in {OUT}.")
    new = [r for r in rows if r["tier"] in ("likely", "rare") and r["glb"] and not r["in_wordlist"]
           and not r["glb_how"].startswith("curated")]
    eng = wt.analyse(wt.ENG_AN, sorted({r["lemma"] for r in new}))
    glb = wt.analyse(wt.GLB_AN, sorted({r["glb"] for r in new if " " not in r["glb"]}))
    _, current = wt.read_tsv(wt.WL)
    have = {(r["headword"].lower(), r["glb"].strip()) for r in current}
    added = []
    for r in new:
        lemma, eng_tags = wt.eng_lemma_tags(r["lemma"], eng)
        if (lemma, r["glb"]) in have:
            continue
        have.add((lemma, r["glb"]))
        added.append({"headword": lemma, "eng_tags": eng_tags, "sense": r["sense"], "glb": r["glb"],
                      "glb_tags": wt.glb_tags_for(r["glb"], eng_tags, glb), "glb_how": "word-list",
                      "layer": "rare" if r["tier"] == "rare" else "period", "apertium": "pending",
                      "reason": f"period_glb.py: {r['glb_how']}",
                      "attested": r["attested"],
                      "notes": f"{name} ({year}) x{r['count']}; {r['tier']}; old: {r['old_evidence']}; "
                               f"sense from {r['sense_source']}"})
    wt.write_wordlist(current + sorted(added, key=lambda r: (r["headword"], r["glb"])))
    print(f"--apply: {len(added)} pending rows appended to {wt.WL}")
