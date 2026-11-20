# Script tier: period-accurate translation proposals per work (user, 2026-11-20: the Wiktionary +
# embeddings pipeline should give a list of proposals for period-accurate translations).
# Proposes, decides nothing: every row is for vetting.
#
#   venv/bin/python period_proposals.py                 every English work in works.tsv
#   venv/bin/python period_proposals.py "The Call of Cthulhu"
#
# For one work (works.tsv: year written, variety, language, text):
# 1. Words: the text is lemmatised (spaCy en_core_web_sm); every lemma + PoS is counted.
# 2. Wiktionary: the word's senses from sense_periods_draft.tsv (sense_periods.py) still in use in
#    the work's year (ended senses: last quote >= year - SLACK). Current senses always compete;
#    one first quoted after year + SLACK is scored down and flagged ("later sense"), since sparse
#    quotations only bound a sense's start. Curated rows count only when matched to a Wiktionary
#    sense. A word is considered only if one of its senses is a period sense (obsolete / archaic
#    / dated / historical) or curated, and listed only if such a sense wins or competes.
# 3. Embeddings in context: each occurrence's context (WINDOW content words either side) and each
#    sense's definition are embedded in HistWords vectors of the work's own decade; the occurrence
#    goes to the closest sense. share = the sense's part of the occurrences.
# 4. Ranking of the Globasa words: share + source prior (curated > vetted > archaic A..D)
#    + the es/eo embedding cross-check of archaic_crosscheck.tsv (script proposals it rated low
#    or other are left out, as are C/D guesses resting on fewer than two occurrences, D guesses
#    the context does not pick clearly (share < CLEAR), and script proposals for later senses) + the
#    work's variety
#    (a preference, never a filter). today = the translation of the current senses, so the trap
#    shows. flag "context" when no sense wins clearly (top share < CLEAR).
#
# Output: <folder>/period_proposals_<slug>.tsv (a private work's folder stays private).
# Languages: en only so far; fr (Le Petit Prince) needs a French sense table first.
import csv
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from functools import lru_cache

import numpy as np
import spacy
from spacy.lang.en.stop_words import STOP_WORDS as STOP

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "time-machine"))
sys.path.insert(0, str(HERE))
import histwords as hw
from wiktionary_db import WiktionaryDB

WORKS = HERE / "works.tsv"
PERIODS = HERE / "sense_periods_draft.tsv"
CROSSCHECK = HERE / "archaic_crosscheck.tsv"
ENDING = {"obsolete", "archaic", "dated", "historical"}
SPACY_POS = {"NOUN": "noun", "VERB": "verb", "ADJ": "adj", "ADV": "adv"}
SLACK = 25          # years: quotations are sparse, a range is only a bound
WINDOW = 12
CLEAR = 0.6
LATER_PENALTY = 0.3
PRIOR = {"curated": 0.5, "vetted": 0.3, "archaic A": 0.25, "archaic B": 0.15, "archaic C": 0.15, "archaic D": 0.05}


def slug(work):
    return re.sub(r"[^a-z0-9]+", "_", work.lower()).strip("_")


def first_year(text):
    m = re.search(r"\d{4}", text)
    return int(m.group()) if m else None


def live(r, year):
    # ended senses must reach the work's year; a current sense always competes: a first quotation
    # after the year only bounds it (tree 'woody plant' is first quoted 1992), see later()
    end = int(r["period_to"]) if r["period_to"] else None
    return not (r["status"] in ENDING and end and end < year - SLACK)


def later(r, year):
    # a sense first quoted well after the work's year: kept, but scored down and flagged (gay
    # 'homosexual', first quoted 1947, must not win in an 1890s text unless the context insists)
    return bool(r["period_from"]) and int(r["period_from"]) > year + SLACK


def prior(source):
    return next((v for k, v in PRIOR.items() if source.startswith(k)), 0.0)


def load_senses():
    by_word = defaultdict(list)
    with open(PERIODS, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            # curated rows only when matched to a Wiktionary sense: unmatched ones are renderings
            # of one passage (Time Machine "little-go", "the Downs"), not general senses
            if r["glb"] and r["story"].startswith("core") and (r["source"] != "curated" or r["gloss"]):
                by_word[(r["eng"], r["pos"])].append(r)
    emb = {}
    if CROSSCHECK.exists():
        with open(CROSSCHECK, encoding="utf-8") as f:
            for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
                emb[(r["eng"], r["pos"], r["gloss"])] = r["emb"]
    return by_word, emb


def occurrences(nlp, text, wanted):
    # (lemma, pos) -> [(sentence index, token index)], and the tokenised sentences
    paras = [p for p in re.split(r"\n\s*\n", text) if p.strip() and not p.startswith("## ")]
    sents, occ, counts = [], defaultdict(list), Counter()
    for doc in nlp.pipe(paras, batch_size=64):
        for sent in doc.sents:
            # a noun-tagged modifier is an adjective: en_core_web_sm tags attributive "queer"
            # ("the queer clay bas-relief") as NOUN 7 times of 8 in The Call of Cthulhu
            toks = [(t.lemma_.lower(), "adj" if t.dep_ in ("amod", "compound") and t.pos_ == "NOUN" else SPACY_POS.get(t.pos_),
                     t.text) for t in sent]
            for k, (lemma, pos, _) in enumerate(toks):
                if pos and (lemma, pos) in wanted:
                    occ[(lemma, pos)].append((len(sents), k))
                    counts[(lemma, pos)] += 1
            sents.append(toks)
    return sents, occ, counts


def vector(words, index, w, counts, skip):
    # rarer words weigh more (log inverse frequency in the decade)
    vs = [(w[index[x]], 1 / math.log(counts.get(x, 0) + 10)) for x in words
          if x in index and x not in STOP and x not in skip and len(x) > 2]
    if not vs:
        return None
    v = sum(a * b for a, b in vs)
    n = np.linalg.norm(v)
    return v / n if n else None


@lru_cache(maxsize=None)
def wikt_senses(lemma, pos):
    return tuple(db.get_senses(lemma, pos) or ())


def with_competitors(lemma, pos, rows):
    # every Wiktionary sense of the word competes in the embedding step, linked to Globasa or not:
    # otherwise a weak archaic guess wins by default for words whose modern senses have no vetted
    # Globasa link (suspect, sink, carry). Unlinked senses carry glb "" (today's sense, no link).
    linked = {r["gloss"] for r in rows}
    out = list(rows)
    for sense in wikt_senses(lemma, pos):
        gloss = sense.glosses[-1] if sense.glosses else ""
        tags = set(sense.tags) | set(re.findall(r"\b(obsolete|archaic|dated|historical)\b", " ".join(sense.raw_glosses)))
        if gloss and gloss not in linked and not tags & ENDING:
            out.append({"glb": "", "gloss": gloss, "label": "", "source": "wiktionary", "status": "current",
                        "period_from": "", "period_to": "", "variety": "", "eng": lemma, "pos": pos})
    return out


def propose(work, row, by_word, emb, nlp):
    year = first_year(row["written"])
    variety = row["variety"]
    text = (HERE / row["text"]).read_text(encoding="utf-8")
    candidates = {k: [r for r in rs if live(r, year)] for k, rs in by_word.items()}
    wanted = {k for k, rs in candidates.items()
              if any(r["status"] in ENDING or r["source"] == "curated" for r in rs)}
    sents, occ, counts = occurrences(nlp, text, wanted)
    decade = hw.decade_of(year)
    _, index, w, wcounts = hw.load(decade)
    out, modern_wins, weak = [], 0, 0
    for key, positions in sorted(occ.items(), key=lambda x: -len(x[1])):
        lemma, pos = key
        senses = with_competitors(lemma, pos, candidates[key])
        svecs = [vector(re.findall(r"[a-z]+", (r["gloss"] + " " + r["label"]).lower()), index, w, wcounts, {lemma})
                 for r in senses]
        votes, example = Counter(), ""
        for si, ti in positions:
            toks = sents[si]
            ctx = [t[0] for t in toks[max(0, ti - WINDOW): ti + WINDOW + 1]]
            cv = vector(ctx, index, w, wcounts, {lemma})
            sims = [float(cv @ sv) if cv is not None and sv is not None else -1 for sv in svecs]
            if max(sims) > -1:
                votes[int(np.argmax(sims))] += 1
            if not example:
                example = " ".join(t[2] for t in toks)[:200]
        n = sum(votes.values()) or 1
        by_glb = defaultdict(lambda: {"score": 0.0, "share": 0.0, "senses": [], "sources": set()})
        for i, r in enumerate(senses):
            share = votes[i] / n
            g = by_glb[r["glb"]]
            g["share"] += share
            g["score"] = max(g["score"], share + prior(r["source"])
                             + {"ok": 0.1, "other": -0.1}.get(emb.get((r["eng"], r["pos"], r["gloss"]), ""), 0)
                             + (0.1 if variety in r["variety"].split(",") else 0)
                             - (LATER_PENALTY if later(r, year) else 0))
            g["senses"].append(r)
            g["sources"].add(r["source"])
        ranked = sorted(by_glb.items(), key=lambda x: -(x[1]["score"] + x[1]["share"]))
        if ranked[0][0] == "" and len(ranked) > 1 and ranked[0][1]["share"] >= CLEAR:
            modern_wins += 1
            continue   # a modern sense without a Globasa link wins clearly
        if ranked[0][0] == "" and len(ranked) > 1:
            ranked = ranked[1:] + ranked[:1]   # propose the best linked sense, keep the unlinked one listed
        top_glb, top = ranked[0]
        top_sense = max(top["senses"], key=lambda r: prior(r["source"]))
        today = sorted({r["glb"] for r in by_word[key] if r["status"] == "current" and r["source"] == "vetted"})
        flags = []
        if len(ranked) > 1 and top["share"] < CLEAR:
            flags.append("context")
        if top_sense["status"] in ENDING:
            flags.append(top_sense["status"])
        if today and top_glb not in today:
            flags.append("differs from today")
        period_alt = any(r["status"] in ENDING or r["source"] == "curated"
                         for g, d in ranked[:2] for r in d["senses"] if d["share"] >= 1 - CLEAR)
        if top_sense["status"] not in ENDING and top_sense["source"] != "curated" and not period_alt:
            modern_wins += 1
            continue   # today's sense wins clearly: nothing period-specific to propose
        verdict = emb.get((top_sense["eng"], top_sense["pos"], top_sense["gloss"]), "")
        if top_sense["source"].startswith("archaic") and verdict in ("low", "other"):
            weak += 1
            continue   # the es/eo cross-check rejected this script proposal (cannon -> bol: low)
        if top_sense["source"].startswith("archaic") and later(top_sense, year):
            weak += 1
            continue   # a script proposal for a sense first quoted after the work (most 'best', 1978)
        if top_sense["source"].startswith("archaic D") and top["share"] < CLEAR:
            weak += 1
            continue   # the weakest script guess must be picked clearly by the context (sky -> megu)
        if top_sense["source"].startswith(("archaic C", "archaic D")) and top["share"] * n < 2:
            weak += 1
            continue   # a weak script guess resting on fewer than two occurrences
        if later(top_sense, year):
            flags.append(f"later sense (first quoted {top_sense['period_from']})")
        out.append({"lemma": lemma, "pos": pos, "count": counts[key], "proposal": top_glb,
                    "sense": top_sense["gloss"] or top_sense["label"],
                    "source": "/".join(sorted(top["sources"])),
                    "range": f"{top_sense['period_from'] or '?'}-{top_sense['period_to'] or 'now'}",
                    "share": f"{top['share']:.2f}",
                    "alternatives": "; ".join(f"{g or '(unlinked modern sense)'} {d['share']:.2f}" for g, d in ranked[1:5]),
                    "today": "/".join(today), "flags": ",".join(flags), "example": example})
    hw.release(decade)
    path = HERE / row["folder"] / f"period_proposals_{slug(work)}.tsv"
    cols = ["lemma", "pos", "count", "proposal", "sense", "source", "range", "share", "alternatives", "today",
            "flags", "example"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, cols, delimiter="\t", lineterminator="\n")
        wr.writeheader()
        wr.writerows(out)
    differs = sum("differs from today" in r["flags"] for r in out)
    print(f"{work} ({year}, {variety}, HistWords {decade}s): {len(out)} words where a period sense wins or "
          f"competes ({modern_wins} more where today's sense wins, {weak} weak guesses left out), "
          f"{differs} differ from today's "
          f"translation -> {path.relative_to(HERE)}", flush=True)


with open(WORKS, encoding="utf-8") as f:
    works = {r["work"]: r for r in csv.DictReader(f, delimiter="\t")}
chosen = sys.argv[1:] or list(works)
by_word, emb = load_senses()
db = WiktionaryDB(str(HERE / "WiktionaryLMDB"))
nlp = spacy.load("en_core_web_sm", disable=["ner"])
for work in chosen:
    row = works[work]
    if row["language"] != "en":
        print(f"{work}: language {row['language']} not supported yet (needs a {row['language']} sense table)")
        continue
    if not row["text"] or not (HERE / row["text"]).exists():
        print(f"{work}: no text file")
        continue
    propose(work, row, by_word, emb, nlp)
