# Script tier: dated attestations per English Wiktionary sense, for temporal ranges of
# translations (which years a sense, and so its Globasa translation, applies to).
#
#   venv/bin/python wiktionary_quote_years.py              (whole dump, ~20 GB, one pass)
#   QY_SAMPLE_MB=500 venv/bin/python wiktionary_quote_years.py   (first 500 MB, to measure)
#
# Streams the raw wiktextract English dump (word_selection.dump.source("en")) line by line; only
# lines of English entries that carry a quotation reference are JSON-decoded. Each quotation's
# "ref" starts with its date: "1895, H. G. Wells, ...", "c. 1600", "1590-2", "1610–1611 (date
# written)", "1897 December (indicated as 1898)"; the first year is taken (date written when the
# ref gives it, as the range's first year). Senses without dated quotations are not written.
#
# Output (OUT, tab-separated, one row per sense with at least one dated quotation):
#   word, pos, sense_n (position in the entry), gloss (last gloss), tags, n_dated,
#   first_year, last_year, years (sorted, space-separated: one per quotation)
# The gloss joins the row to WiktionaryLMDB senses (Sense.glosses[-1]) by (word, pos, gloss).
import os
import re
import time

import orjson

from word_selection import dump

OUT = os.environ.get("QY_OUT", "/media/paleos/Warehouse2/Language/Claude/wiktionary_quote_years.tsv")
SAMPLE = int(float(os.environ.get("QY_SAMPLE_MB", "0")) * 1024 * 1024)
YEAR = re.compile(r"\s*(?:c\.|ca\.|circa|a\.|ante|p\.|post)?\s*(\d{3,4})(?!\d)")
FIRST_YEAR, LAST_YEAR = 700, 2026
ENGLISH = b'"lang_code": "en"'
HAS_REF = b'"ref": "'


def year_of(ref):
    m = YEAR.match(ref)
    if not m:
        return None
    y = int(m.group(1))
    return y if FIRST_YEAR <= y <= LAST_YEAR else None


def clean(text):
    return text.replace("\t", " ").replace("\n", " ")


src = dump.source("en")
t0 = time.time()
read = rows = entries = 0
with dump.open_lines(src, binary=True) as lines, open(OUT, "w", encoding="utf-8") as out:
    out.write("word\tpos\tsense_n\tgloss\ttags\tn_dated\tfirst_year\tlast_year\tyears\n")
    for line in lines:
        read += len(line)
        if SAMPLE and read > SAMPLE:
            break
        if HAS_REF not in line or ENGLISH not in line:
            continue
        entry = orjson.loads(line)
        if entry.get("lang_code") != "en":
            continue
        entries += 1
        for n, sense in enumerate(entry.get("senses", ())):
            years = sorted(y for ex in sense.get("examples", ()) if (y := year_of(ex.get("ref", ""))))
            if not years:
                continue
            glosses = sense.get("glosses") or [""]
            out.write("\t".join([entry.get("word", ""), entry.get("pos", ""), str(n), clean(glosses[-1]),
                                 ",".join(sense.get("tags", ())), str(len(years)), str(years[0]),
                                 str(years[-1]), " ".join(map(str, years))]) + "\n")
            rows += 1
        if entries % 200000 == 0:
            print(f"  {read / 1e9:.1f} GB, {entries} entries, {rows} senses, {time.time() - t0:.0f} s", flush=True)
print(f"{read / 1e9:.2f} GB read, {entries} English entries with quotations, {rows} dated senses "
      f"-> {OUT} ({time.time() - t0:.0f} s)")
