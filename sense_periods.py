# Script tier: draft year ranges for English -> Globasa translations (which years a sense, and so
# its Globasa word, applies to). Drafts only: every range is evidence for vetting, never a decision.
#
#   venv/bin/python sense_periods.py
#
# Rows:
#   vetted   person-vetted senses (vetted_senses.load_rows: App? s, Tier v/e); the translation-
#            table label is matched to its Wiktionary sense (sense_rows.match_sense_strict, else
#            the word-overlap tier of match_sense_to_definition, marked as a fallback)
#   archaic  proposals of archaic_senses.py (strength A-D; glb = its first candidate)
#   curated  time-machine/victorian_wordlist.tsv (the source of truth for period senses): each row
#            is matched to the Wiktionary sense of the same word and PoS whose gloss shares the most
#            content words with the row's sense (>= CURATED_MIN of the smaller set or 2 shared words,
#            marked as a fallback); a curated row replaces the archaic proposal for that sense (user 2026-11-20:
#            gay 'festive, colourful' is kolorpul, not the proposed luminpul)
# Dates: wiktionary_quote_years.tsv (wiktionary_quote_years.py), joined on (word, pos, gloss);
#        the gloss is compared normalised, else by word overlap >= FUZZY, marked as a fallback.
# Range:
#   from  first dated quotation (a lower bound of use, not the coinage)
#   to    last dated quotation when the sense is tagged obsolete / archaic / dated / historical
#         (a later quotation can be a deliberate archaism: see n_dated and the years); open ("")
#         for current senses
#   basis what the range rests on; "(fallback: ...)" when the gloss join was fuzzy
# Throughout Modern English (user, 2026-11-20: an option for translations that hold for the whole
# of Modern English, MODERN_ENGLISH_FROM to today):
#   yes      the sense is current (no ending tag) and quoted by EARLY_ENOUGH; quotations are sparse
#            and only bound the start from above, so a later first quote is "unknown", never "no"
#   no       the sense ended (obsolete / archaic / dated / historical)
#   unknown  current but first quoted after EARLY_ENOUGH, or no dated quotation
# Story focus (user, 2026-11-20: mainly the widespread senses that matter for translating stories):
#   story    core, or marginal (rare / uncommon / nonce-word / dialectal without a named region)
#   variety  general, or the regional / national tags (UK, US, Scotland, Northern-England, ...): a
#            variety layer chosen by the work's variety in works.tsv, never dropped. A variety is
#            a preference, not a filter: Lovecraft (US) writes "mad" = insane, a sense Wiktionary
#            tags British-Isles
#
# Output: sense_periods_draft.tsv (column throughout), sense_periods_modern_english.tsv (the "yes"
#         rows: the translations to use when a text's date is unknown or a dictionary should hold
#         for all of Modern English), sense_periods_report.txt
import csv
import os
import re
from functools import lru_cache

import vetted_senses
from sense_rows import match_sense_strict, match_sense_to_definition
from wiktionary_db import WiktionaryDB

HERE = os.path.dirname(os.path.abspath(__file__))
QUOTE_YEARS = os.environ.get("QY_OUT", "/media/paleos/Warehouse2/Language/Claude/wiktionary_quote_years.tsv")
ARCHAIC = os.path.join(HERE, "archaic_senses.tsv")
CURATED = os.path.join(HERE, "time-machine", "victorian_wordlist.tsv")
CURATED_POS = {"n": "noun", "adj": "adj", "vblex": "verb", "adv": "adv"}
CURATED_MIN = 0.6
STOP = set("a an the of or and in to for by with as on at from be is any one some".split())
OUT = os.path.join(HERE, "sense_periods_draft.tsv")
REPORT = os.path.join(HERE, "sense_periods_report.txt")
THROUGHOUT = os.path.join(HERE, "sense_periods_modern_english.tsv")
MODERN_ENGLISH_FROM = 1500
EARLY_ENOUGH = 1700
MARGINAL = {"rare", "uncommon", "nonce-word", "dialectal"}
# national varieties keep one name each (works.tsv names a work's variety as US or UK)
VARIETY_ALIAS = {"British": "UK", "American": "US", "England": "UK", "Britain": "UK", "British-Isles": "UK"}
GENERAL_CAPS = {"Commonwealth", "English", "Internet", "Modern", "Early",
                "Judaism", "Christianity", "Islam", "Hinduism", "Buddhism", "Greek", "Roman", "Ancient-Rome",
                "Ancient-Greece", "Latin", "Japanese", "Western", "Oxford", "Cambridge"}
POS = {"noun", "verb", "adj", "adv"}
ENDING = ("obsolete", "archaic", "dated", "historical")
LABEL = re.compile(r"\((?:[^)]*?\b)?(obsolete|archaic|dated|historical)\b", re.I)
FUZZY = 0.6
SHOW = ["gay", "queer", "man", "dumb", "nice", "awful", "broadcast", "film", "fancy", "presently"]

db = WiktionaryDB(os.path.join(HERE, "WiktionaryLMDB"))


@lru_cache(maxsize=None)
def senses_of(word, pos):
    return tuple(db.get_senses(word, pos) or ())


def norm(text):
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def status_of(tags, raw=""):
    found = [t for t in ENDING if t in tags]
    m = LABEL.search(raw)
    if m:
        found.append(m.group(1).lower())
    return next((t for t in ENDING if t in found), "current")


# --- the translations to date -------------------------------------------------------------------
rows = []
for r in vetted_senses.load_rows():
    if (r["Source"] != "en" or r["App?"] != "s" or r["Tier"] not in ("v", "e")
            or r["Prt of Sp"] not in POS or not r["Glb"]):
        continue
    senses = senses_of(r["Eng"], r["Prt of Sp"])
    sense, how = match_sense_strict(r["Wiktionary Sense"], senses), ""
    if sense is None:
        # paraphrased labels ("pertaining to non-normative sexuality"): word-overlap tier
        sense, how = match_sense_to_definition(r["Wiktionary Sense"], senses), " (fallback: overlap sense match)"
    rows.append({"glb": r["Glb"], "eng": r["Eng"], "pos": r["Prt of Sp"], "source": "vetted",
                 "label": r["Wiktionary Sense"], "how": how if sense else "",
                 "gloss": sense.glosses[-1] if sense and sense.glosses else "",
                 "status": status_of(sense.tags, " ".join(sense.raw_glosses)) if sense else "",
                 "tags": set(sense.tags) if sense else set()})

with open(ARCHAIC, encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        first = (re.match(r"(.+?) \(\d+ langs\)", r["table"]) or re.match(r"([^(;]+?) \(", r["gloss_glb"]))
        rows.append({"glb": first.group(1).strip() if first else "", "eng": r["eng"], "pos": r["pos"],
                     "source": f"archaic {r['strength']}", "label": r["label"], "gloss": r["gloss"],
                     "status": r["period"] if r["period"] in ENDING else "current",
                     "tags": next((set(x.tags) for x in senses_of(r["eng"], r["pos"])
                                   if x.glosses and x.glosses[-1] == r["gloss"]), set())})

def content(text):
    return set(norm(re.sub(r"\([^)]*\)", " ", text)).split()) - STOP


curated_keys = set()
with open(CURATED, encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        pos = CURATED_POS.get(r["eng_tags"])
        if not pos or not r["glb"]:
            continue
        mine = content(r["sense"])
        best, score, best_shared = None, 0.0, 0
        for sense in senses_of(r["headword"], pos):
            theirs = content(sense.glosses[-1]) if sense.glosses else set()
            if mine and theirs:
                shared = len(mine & theirs)
                sc = shared / min(len(mine), len(theirs))
                if (sc, shared) > (score, best_shared):
                    best, score, best_shared = sense, sc, shared
        # >= CURATED_MIN of the smaller set, or two shared words (lexikal "wordless, speechless,
        # without words" ~ "Unaccompanied by words or speech, silent, wordless")
        matched = best is not None and (score >= CURATED_MIN or best_shared >= 2)
        gloss = best.glosses[-1] if matched else ""
        rows.append({"glb": r["glb"], "eng": r["headword"], "pos": pos, "source": "curated",
                     "label": r["sense"], "gloss": gloss,
                     "how": f" (fallback: curated sense matched by word overlap {score:.2f})" if matched else "",
                     "status": status_of(best.tags, " ".join(best.raw_glosses)) if matched else "",
                     "tags": set(best.tags) if matched else set()})
        if matched:
            curated_keys.add((r["headword"], pos, norm(gloss)))
rows = [r for r in rows if not (r["source"].startswith("archaic")
                               and (r["eng"], r["pos"], norm(r["gloss"])) in curated_keys)]

# --- quotation years, only for the (word, pos) pairs needed ---------------------------------------
needed = {(r["eng"], r["pos"]) for r in rows}
quotes = {}
with open(QUOTE_YEARS, encoding="utf-8") as f:
    for q in csv.DictReader(f, delimiter="\t"):
        if (q["word"], q["pos"]) in needed:
            quotes.setdefault((q["word"], q["pos"]), []).append(q)


def dated(r):
    cands = quotes.get((r["eng"], r["pos"]), ())
    g = norm(r["gloss"])
    if not g:
        return None, ""
    for q in cands:
        if norm(q["gloss"]) == g:
            return q, ""
    words = set(g.split())
    best, score = None, 0.0
    for q in cands:
        qw = set(norm(q["gloss"]).split())
        j = len(words & qw) / len(words | qw) if qw else 0
        if j > score:
            best, score = q, j
    if score >= FUZZY:
        return best, f" (fallback: fuzzy gloss match {score:.2f})"
    return None, ""


stats = {"rows": 0, "dated": 0, "fuzzy": 0, "no sense": 0}
for r in rows:
    stats["rows"] += 1
    if not r["gloss"]:
        stats["no sense"] += 1
        r.update(n_dated="", first_year="", last_year="", period_from="", period_to="",
                 basis="(fallback: no matching Wiktionary sense)")
        continue
    q, fallback = dated(r)
    if q is None:
        r.update(n_dated="0", first_year="", last_year="", period_from="", period_to="",
                 basis=f"no dated quotation; tag {r['status']}")
        continue
    stats["dated"] += 1
    stats["fuzzy"] += bool(fallback)
    status = r["status"] if r["status"] in ENDING else status_of(q["tags"].split(","))
    r["status"] = status
    r["tags"] = r.get("tags", set()) | {t for t in q["tags"].split(",") if t}
    ends = status in ENDING
    r.update(n_dated=q["n_dated"], first_year=q["first_year"], last_year=q["last_year"],
             period_from=q["first_year"], period_to=q["last_year"] if ends else "",
             basis=f"{q['n_dated']} quotes {q['first_year']}-{q['last_year']}; tag {status}{fallback}"
                   + r.get("how", ""))



def variety(tags):
    # regional and national senses form variety layers, never dropped: Northern English or
    # Scottish glosses for texts in those varieties (user 2026-11-20), and US vs UK senses, since a
    # work's variety decides between them (user 2026-11-20: Lovecraft wrote American English, with
    # British spellings, Wells British; works.tsv records each work's variety); topic tags
    # (Judaism, Ancient-Rome) are no region
    regions = {VARIETY_ALIAS.get(t, t) for t in tags if t[:1].isupper() and t not in GENERAL_CAPS}
    return ",".join(sorted(regions)) or "general"


def story(tags):
    # what matters for translating stories first: rare, uncommon and nonce senses, and dialect
    # senses without a named region (with one, they belong to that variety layer) are marginal
    hit = sorted(tags & MARGINAL - ({"dialectal"} if variety(tags) != "general" else set()))
    return f"marginal ({','.join(hit)})" if hit else "core"


def throughout(r):
    if r["status"] in ENDING:
        return f"no (ended: {r['status']})"
    if not r["period_from"]:
        return "unknown (no dated quotation)"
    if int(r["period_from"]) <= EARLY_ENOUGH:
        return "yes"
    return f"unknown (first quoted {r['period_from']})"


for r in rows:
    r["throughout"] = throughout(r)
    r["variety"] = variety(r.get("tags", set()))
    r["story"] = story(r.get("tags", set()))

cols = ["glb", "eng", "pos", "source", "status", "story", "variety", "throughout", "period_from", "period_to", "n_dated",
        "first_year", "last_year", "gloss", "label", "basis"]
rows.sort(key=lambda r: (r["eng"], r["pos"], r["period_from"] or "9999", r["glb"]))
with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, cols, delimiter="\t", lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)

with open(THROUGHOUT, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, ["eng", "pos", "glb", "source", "period_from", "gloss", "basis"], delimiter="\t",
                       lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    w.writerows(r for r in rows if r["throughout"] == "yes")

rep = [f"{k}: {v}" for k, v in stats.items()]
kinds = {}
for r in rows:
    k = r["throughout"].split(" ")[0]
    kinds[k] = kinds.get(k, 0) + 1
rep.append(f"throughout Modern English ({MODERN_ENGLISH_FROM}-now, quoted by {EARLY_ENOUGH}): {kinds}")
for src in ("vetted", "archaic", "curated"):
    sel = [r for r in rows if r["source"].startswith(src)]
    rep.append(f"{src}: {len(sel)} rows, {sum(1 for r in sel if r['period_from'])} with a start year, "
               f"{sum(1 for r in sel if r['period_to'])} with an end year")
rep.append("\nALL = holds throughout Modern English, ? = unknown, blank = ended")
for word in SHOW:
    rep.append(f"\n== {word}")
    for r in rows:
        if r["eng"] == word:
            span = f"{r['period_from'] or '?'}–{r['period_to'] or ('now' if r['period_from'] else '?')}"
            mark = {"yes": "ALL", "no": "   "}.get(r["throughout"].split(" ")[0], " ? ")
            rep.append(f"   {mark} {r['pos']:4s} {span:11s} {r['glb']:14s} [{r['source']}, {r['status']}] {r['gloss'][:70]}")
open(REPORT, "w", encoding="utf-8").write("\n".join(rep) + "\n")
print("\n".join(rep))
