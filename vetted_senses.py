"""The vetting decisions on Wiktionary senses, stored without the dump data.

vetted_senses.tsv is the committed record of every judgment made in the
sense spreadsheets: one row per (Glb, Source, Eng, Prt of Sp, VerbType,
Wiktionary Sense) with its App? and Tier. Everything else in those spreadsheets
-- definitions, examples, translations, tags, the heuristic App? of unreviewed
rows -- is regenerated from the word list and a Wiktionary dump, so it is not
stored.

The spreadsheets stay the place to vet (they carry the translations that make
vetting comfortable):
  GLB_ENG_WiktionarySenses.xlsx    English senses; written by
                                   "Wiktionary sense based translation extender 3.py"
                                   (the expanded view), vetted by hand and by
                                   LLM_sense_judge.py
  GLB_MULTI_WiktionarySenses.xlsx  senses from other Wiktionary editions
They live in the directory named by .senses_config.json. Whenever one of them
is newer than vetted_senses.tsv, sync() exports the decisions again, so the
TSV follows the spreadsheets without a manual step. On a fresh clone there are
no spreadsheets and the TSV is the only source.

The other place to vet is the browser page of sense_vetter.py. It appends to
sense_vetting.jsonl, a log that load_rows() lays over the TSV: the latest
verdict on a sense wins over the spreadsheet's (an expert's Tier e excepted),
and "clear" or "unsure" leaves the spreadsheet's decision. It stays a separate
file because sync() rewrites the TSV wholesale from the spreadsheets.

Run directly to export now:  python vetted_senses.py
"""
import csv
import json
import os

from openpyxl import load_workbook

from wiktionary_constants import _load_markings_from_rows

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VETTED_TSV = os.path.join(BASE_DIR, "vetted_senses.tsv")
CONFIG_FILE = os.path.join(BASE_DIR, ".senses_config.json")
VETTING_LOG = os.path.join(BASE_DIR, "sense_vetting.jsonl")
ENG_XLSX = "GLB_ENG_WiktionarySenses.xlsx"
MULTI_XLSX = "GLB_MULTI_WiktionarySenses.xlsx"

COLUMNS = ["Glb", "Source", "Eng", "Prt of Sp", "VerbType", "Wiktionary Sense",
           "App?", "Tier"]
# Tiers, highest first: expert, vetted, LLM, automatic script.
TIERS = ("e", "v", "l", "a")


def senses_dir():
    """The spreadsheets' directory from .senses_config.json, or None."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f).get("senses_dir")
    return None


def _sheet_rows(path):
    wb = load_workbook(path, read_only=True)
    it = wb.active.iter_rows(values_only=True)
    header = [str(h) if h is not None else "" for h in next(it, ())]
    rows = [[str(c) if c is not None else "" for c in r] for r in it]
    wb.close()
    return header, rows


def _clean_tier(tier, where, notes):
    """Strip stray whitespace ("v " was silently not 'v'); keep and report
    anything that is not a known tier rather than guess what was meant."""
    t = tier.strip()
    if t != tier:
        notes.append(f"{where}: Tier {tier!r} read as {t!r}")
    if t not in TIERS:
        notes.append(f"{where}: unknown Tier {t!r} kept as is (not used by the builder)")
    return t


def export(eng_xlsx, multi_xlsx=None, out=VETTED_TSV):
    """Write the decisions of the spreadsheets to `out`. Returns notes on
    values that needed attention."""
    notes = []
    out_rows = []

    # English: the generator's own loader, so the keys and the "a row is a
    # decision when it has a Tier" rule are exactly the ones it inherits by.
    header, rows = _sheet_rows(eng_xlsx)
    for (glb, eng, pos, vt, sense), (app, tier) in \
            _load_markings_from_rows(header, rows).items():
        tier = _clean_tier(tier, f"{glb} / {eng} ({pos})", notes)
        out_rows.append([glb, "en", eng, pos, vt, sense, app.strip(), tier])

    if multi_xlsx and os.path.exists(multi_xlsx):
        header, rows = _sheet_rows(multi_xlsx)
        col = {name: i for i, name in enumerate(header)}

        def get(row, name):
            i = col.get(name)
            return row[i] if i is not None and i < len(row) else ""

        seen = set()
        for row in rows:
            tier = get(row, "Tier")
            if not tier:
                continue
            key = (row[0], get(row, "Source"), get(row, "LookupWord"),
                   get(row, "Prt of Sp"), get(row, "VerbType"),
                   get(row, "Wiktionary Sense"))
            if key in seen:
                continue
            seen.add(key)
            tier = _clean_tier(tier, f"{row[0]} / {key[2]} ({key[1]})", notes)
            out_rows.append(list(key) + [get(row, "App?").strip(), tier])

    tmp = out + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(COLUMNS)
        w.writerows(out_rows)
    os.replace(tmp, out)
    return notes


def sync(verbose=True):
    """Export again if a spreadsheet is newer than vetted_senses.tsv."""
    d = senses_dir()
    if not d:
        return
    eng, multi = os.path.join(d, ENG_XLSX), os.path.join(d, MULTI_XLSX)
    if not os.path.exists(eng):
        return
    newest = max(os.path.getmtime(p) for p in (eng, multi) if os.path.exists(p))
    if os.path.exists(VETTED_TSV) and os.path.getmtime(VETTED_TSV) >= newest:
        return
    if verbose:
        print(f"Exporting vetting decisions from {d} to {os.path.basename(VETTED_TSV)}...")
    try:
        notes = export(eng, multi)
    except Exception as e:
        if not os.path.exists(VETTED_TSV):
            raise
        print(f"  Warning: could not read the spreadsheets ({e}); "
              f"using {os.path.basename(VETTED_TSV)} as it is (fallback: unreadable spreadsheet)")
        return
    for note in notes:
        if verbose:
            print("  " + note)


def log_decisions(path=VETTING_LOG):
    """{(glb, eng, pos, verb_type, sense): app} from the vetting page's log.

    Replays the log, so the latest entry per sense wins and undos count.
    Unsure ("u") and "clear" are no judgement and leave the spreadsheet's
    decision. Each entry names the rows it covers in "keys" ([eng, pos,
    verb_type] triples); a sense is one label of one word, met under each of
    the word's English glosses that share it.
    """
    latest = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                latest[entry["id"]] = entry
    decided = {}
    for entry in latest.values():
        if entry["verdict"] not in ("s", "n"):
            continue
        for eng, pos, vt in entry.get("keys", ()):
            decided[(entry["word"], eng, pos, vt, entry["label"])] = entry["verdict"]
    return decided


def load_rows(include_log=True):
    """Every decision as a dict keyed by COLUMNS (syncs first), with the
    vetting page's verdicts laid over them unless include_log is False."""
    sync()
    with open(VETTED_TSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    if not include_log:
        return rows
    decided = log_decisions()
    for r in rows:
        key = (r["Glb"], r["Eng"], r["Prt of Sp"], r["VerbType"], r["Wiktionary Sense"])
        if r["Source"] == "en" and key in decided:
            app = decided.pop(key)
            if r["Tier"] != "e":
                r["App?"], r["Tier"] = app, "v"
    for (glb, eng, pos, vt, sense), app in decided.items():
        rows.append({"Glb": glb, "Source": "en", "Eng": eng, "Prt of Sp": pos,
                     "VerbType": vt, "Wiktionary Sense": sense, "App?": app, "Tier": "v"})
    return rows


def load_markings(source="en", include_log=True):
    """{(glb, eng, pos, verb_type, sense): (app, tier)} -- what the sense
    generator inherits when it rebuilds the spreadsheet."""
    return {(r["Glb"], r["Eng"], r["Prt of Sp"], r["VerbType"], r["Wiktionary Sense"]):
            (r["App?"], r["Tier"])
            for r in load_rows(include_log) if r["Source"] == source}


def load_vetted():
    """The senses that go into menalariExtension.tsv: applicable (App? s) and
    vetted by a person (Tier v or e). Dicts as the extension builder uses them."""
    return [{"glb": r["Glb"], "lookup_word": r["Eng"], "pos": r["Prt of Sp"],
             "verb_type": r["VerbType"], "sense": r["Wiktionary Sense"],
             "source": r["Source"]}
            for r in load_rows()
            if r["App?"] == "s" and r["Tier"] in ("v", "e")
            and r["Glb"] and r["Eng"] and r["Prt of Sp"] and r["Wiktionary Sense"]]


if __name__ == "__main__":
    d = senses_dir() or "."
    for note in export(os.path.join(d, ENG_XLSX), os.path.join(d, MULTI_XLSX)):
        print(note)
    print(f"Wrote {VETTED_TSV}")
