"""British / American English glosses of word-list.csv with the years each one applies.

Pipeline: CDN download -> extract_constructions.py -> apply_eng_variety.py
-> sense_periods.py -> apply_eng_periods.py. Re-run after any of them.

Writes a separate list, eng_periods.tsv (user 2026-11-28: the periods are a
list appended to the word list, not columns inside word-list.csv): Word plus two
columns in the format of TranslationEngGB / TranslationEngUS (PoS prefixes,
"; " segments, ", " items), so readers need no new parsing. A reader appends
them by Word; only words whose period view adds years or † are listed, every
other word's period view is its plain GB / US gloss.

    TranslationEngGBPeriods   the GB view, each item with its years
    TranslationEngUSPeriods   the US view, each item with its years

    adj: merry (1590-), cheerful (1600-), gay† (1692-1974)

  (1692-1974)  an ended sense: first and last dated Wiktionary quotation, bounds of
               attested use, not exact dates (quotations are sparse); (1850) = one quotation
  (~1960-)     a current sense dated by histwords_ranges.py: the decade it became the word's
               dominant sense in HistWords (Google Books), approximate
  (1611-)      a current sense quoted by 1700: in use throughout Modern English; a
               current sense first quoted later gets no years (a late first quotation is
               only an example, not the sense's start); starts of new senses (queer
               "LGBT") come from curated rows or HistWords switch-overs, not from here
  †            the sense ended (obsolete / archaic / dated / historical)
  no years     no dated quotation joins the item to a sense

Evidence: sense_periods_draft.tsv rows from person-vetted senses and from the
curated period list (time-machine/victorian_wordlist.tsv); unvetted script
proposals (archaic_senses.py) never enter these columns (user 2026-11-20: the
final output is the word list's English glosses with a range per US or UK).

Per variety: a sense tagged with a national or regional variety appears only in
its view: UK and British regions (Scotland, Northern-England, ...) in GB, US and
American regions in US, untagged senses in both; other varieties (India,
Australia, ...) in neither, listed in the report. Wiktionary quotations are not
split by country, so a sense shared by both views has the same years in both.

Curated period glosses a word lacks (kweho: gay "merry, cheerful") are added to
the segment of their PoS, marked by their years. Curated renderings that are not
a word-list entry (paraphrases, derived proposals such as palakal) are reported.

word-list.csv is only read. Idempotent: a run that would change nothing writes
nothing.
"""
import csv
import re
from collections import defaultdict
from pathlib import Path

import constructions
from constructions import read_wordlist

WORDLIST = "word-list.csv"
OUT = Path("eng_periods.tsv")
PERIODS = Path("sense_periods_draft.tsv")
HISTWORDS = Path("histwords_ranges.tsv")     # histwords_ranges.py: switch-over decades
REPORT = Path("eng_periods_report.tsv")
VIEWS = {"GB": ("TranslationEngGB", "TranslationEngGBPeriods"),
         "US": ("TranslationEngUS", "TranslationEngUSPeriods")}
ENDING = {"obsolete", "archaic", "dated", "historical"}
EARLY_ENOUGH = 1700        # as sense_periods.py: a current sense quoted by then covers Modern English
REGIONS = {
    "GB": {"UK", "Scotland", "Northern-England", "England", "Wales", "Cornwall", "Yorkshire", "West-Country",
           "Northern-Ireland", "Ireland", "Cockney", "Midlands", "Geordie", "Lancashire", "Devon", "Norfolk",
           "Multicultural-London-English", "Scouse", "Somerset", "Cumbria"},
    "US": {"US", "Southern-US", "Appalachia", "New-England", "Northern-US", "Western-US", "Midwestern-US",
           "California", "New-York", "Texas", "Boston", "Philadelphia", "Pennsylvania"},
}
POS_OF_PREFIX = {"n": "noun", "v": "verb", "adj": "adj", "adv": "adv"}
PREFIX_OF_POS = {"noun": "n: ", "verb": "v: ", "adj": "adj: ", "adv": "adv: "}


def pos_of(prefix):
    head = re.split(r"[.\s:(]", prefix.strip(), maxsplit=1)[0].lower()
    return POS_OF_PREFIX.get(head)


def in_view(variety, view):
    tags = set(variety.split(",")) - {"general", ""}
    if not tags:
        return True
    return bool(tags & REGIONS[view])


def years(rows):
    """'1692-1974', '1850', '1598-' or '' for the rows of one item; † when all ended.
    A current sense shows a start only when quoted by EARLY_ENOUGH (it then covers Modern
    English): a later first quotation is whatever example Wiktionary happens to have (weird
    "strange" 1999, odd 2003), not the start of the sense."""
    starts = [int(r["period_from"]) for r in rows if r["period_from"]]
    ended = all(r["status"] in ENDING for r in rows)
    ends = [int(r["period_to"]) for r in rows if r["period_to"]]
    if ended:
        if not starts and not ends:
            return "", True
        a, b = (str(min(starts)) if starts else ""), (str(max(ends)) if ends else "")
        return (a if a == b else f"{a}-{b}"), True
    if starts and min(starts) <= EARLY_ENOUGH:
        return f"{min(starts)}-", False
    return "", False


def mark(item, dagger, region, yrs):
    # "gay† (1692-1974)", "abroad (Scotland)", "gay† (Scotland, 1832-1903)"
    label = ", ".join(x for x in (region, yrs) if x)
    return f"{item}{'†' if dagger else ''}{f' ({label})' if label else ''}"


def regional(rows, view):
    # a region label only for senses not also national: "tin" (can) is tagged Ireland and UK,
    # so it is plain British, not Irish
    tags = {t for r in rows for t in r["variety"].split(",")}
    if tags & {"UK", "US"}:
        return ""
    return ", ".join(sorted(tags & REGIONS[view]))


# ---- evidence: vetted and curated senses only
evidence = defaultdict(list)          # (glb, normalised eng, pos) -> rows
by_word = defaultdict(list)           # glb -> curated rows (for added glosses)
with open(PERIODS, encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        if r["source"] not in ("vetted", "curated") or not r["glb"]:
            continue
        evidence[(r["glb"], constructions.normalise_item(r["eng"]), r["pos"])].append(r)
        if r["source"] == "curated":
            by_word[r["glb"]].append(r)


# HistWords switch-overs: the decade a current sense became dominant ("~1960-"), for current senses
# whose Wiktionary quotations give no usable start
rise = {}
if HISTWORDS.exists():
    with open(HISTWORDS, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["rise"] and r["status"] not in ENDING:
                rise[(r["glb"], constructions.normalise_item(r["eng"]), r["pos"])] = r["rise"]


def annotate(word, text, view, report, placed):
    segs = []
    seen = set()
    for seg in text.split(";") if text.strip() else []:
        prefix, body = constructions.split_annotation(seg)
        pos = pos_of(prefix)
        items = constructions.split_items(body) if body.strip() else []
        out = []
        for it in items:
            norm = constructions.normalise_item(it)
            seen.add((norm, pos))
            rows = [r for r in evidence.get((word, norm, pos), []) if in_view(r["variety"], view)]
            yrs, ended = years(rows) if rows else ("", False)
            region = regional(rows, view) if rows else ""
            if not yrs and not ended and (word, norm, pos) in rise:
                yrs = f"~{rise[(word, norm, pos)]}-"
            out.append(mark(it, ended and bool(yrs), region, yrs))
        segs.append([prefix, pos, out])
    # curated period glosses the word lacks
    added = defaultdict(list)
    for r in by_word.get(word, []):
        norm = constructions.normalise_item(r["eng"])
        if (norm, r["pos"]) in seen or not in_view(r["variety"], view) or (norm, r["pos"]) in added:
            continue
        yrs, ended = years([r])
        region = regional([r], view)
        added[(norm, r["pos"])] = mark(r["eng"], ended and bool(yrs), region, yrs)
        placed.add((word, r["eng"], r["pos"]))
    for (norm, pos), item in added.items():
        seg = next((s for s in segs if s[1] == pos), None)
        if seg:
            seg[2].append(item)
        else:
            segs.append([PREFIX_OF_POS[pos], pos, [item]])
    return "; ".join(prefix + ", ".join(items) for prefix, _, items in segs)


rows, _, _ = read_wordlist(WORDLIST)
header = rows[0]
word_col = header.index("Word")
missing = [src for src, _ in VIEWS.values() if src not in header]
if missing:
    raise SystemExit(f"{WORDLIST} has no {', '.join(missing)}: run apply_eng_variety.py first")
cols = {view: header.index(src) for view, (src, _) in VIEWS.items()}

report, placed, dated = [], set(), 0
words = set()
out_rows = []
for row in rows[1:]:
    word = row[word_col].strip() if len(row) > word_col else ""
    if not word or word in words:   # blank CDN rows; first occurrence wins (AnkiMaker3's dedupe)
        continue
    words.add(word)
    views = {}
    for view, src in cols.items():
        plain = row[src] if len(row) > src else ""
        views[view] = (plain, annotate(word, plain, view, report, placed))
    if any(new != plain for plain, new in views.values()):
        out_rows.append([word] + [views[view][1] for view in VIEWS])
        dated += bool(re.search(r"\(\d{3,4}-", views["GB"][1]))

# report: curated renderings that are not word-list entries, and senses of other varieties
for glb, rs in by_word.items():
    for r in rs:
        if glb not in words:
            report.append((glb, r["eng"], r["pos"], "curated rendering is not a word-list entry (paraphrase or derived proposal)"))
for (glb, eng, pos), rs in evidence.items():
    for r in rs:
        if not in_view(r["variety"], "GB") and not in_view(r["variety"], "US"):
            report.append((glb, eng, pos, f"variety {r['variety']}: in neither view"))
with open(REPORT, "w", encoding="utf-8") as f:
    f.write("Word\teng\tpos\tnote\n")
    for x in sorted(set(report)):
        f.write("\t".join(x) + "\n")

text = "\t".join(["Word"] + [dst for _, dst in VIEWS.values()]) + "\n"
text += "".join("\t".join(r) + "\n" for r in out_rows)
print(f"{len(words)} entries; {len(out_rows)} with a period view ({dated} dated in GB); "
      f"{len(placed)} curated period glosses added; {len(set(report))} report rows ({REPORT})")
if OUT.exists() and OUT.read_text(encoding="utf-8") == text:
    print(f"{OUT} unchanged")
else:
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT} ({WORDLIST} not modified)")
