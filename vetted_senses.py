"""The vetting decisions on Wiktionary senses, stored without the dump data.

Vetters score senses from 1 to 5, each in a column of their own headed with their pseudonym
(never a real name): 5 = sure the sense applies to the Globasa word, 1 = sure it does not,
3 = unsure, 2 and 4 = leaning. The mean of a sense's scores decides: >= 4 accepted, <= 2
rejected, anything between undecided, which counts as not vetted (the script's or LLM's
suggestion stays visible as a hint).

vetted_senses.tsv is the committed record: one row per (Glb, Source, Eng, Prt of Sp, VerbType,
Wiktionary Sense) with
  App?, Tier   the machine suggestion (Tier a = script, l = LLM) or an expert's decision
               (Tier e, which outranks the scores); never a person's score
  <vetter>...  one column per vetter, 1-5 or blank; the owner's column first
Everything else in the spreadsheets -- definitions, examples, translations, tags -- is
regenerated from the word list and a Wiktionary dump, so it is not stored.

load_rows() returns every row with the EFFECTIVE App?/Tier the readers have always used
(accepted -> s/v, rejected -> n/v, undecided -> the machine suggestion), plus "scores",
"Mean" and "Decision". So "App? s and Tier v/e" still means accepted by people.

Where vetters work:
  GLB_ENG_WiktionarySenses.xlsx    the shared sheet (directory in .senses_config.json),
                                   written by "Wiktionary sense based translation extender 3.py":
                                   every column right of "Decision" is a vetter. Whenever it is
                                   newer than vetted_senses.tsv, sync() reads the scores back.
  GLB_MULTI_WiktionarySenses.xlsx  senses from other Wiktionary editions (Tier v = the owner's)
  sense_vetter.py                  the owner's page; it appends to sense_vetting.jsonl, a log
                                   that load_rows() lays over the TSV in the owner's column.
                                   push_owner_scores() writes those scores into the sheet so
                                   the other vetters see them.
The owner scores on the page or in the sheet, and the later judgement wins: a sheet edit of
the owner's column becomes a log entry dated with the sheet's save time, unless the log
already holds a later page score for that row. A blank sheet cell never clears a page
score; clear it on the page.

The owner's pseudonym: SV_VETTER, else "vetter" in .senses_config.json, else Paleos.

    python vetted_senses.py            export the spreadsheets now
    python vetted_senses.py --push     write the owner's page scores into the shared sheet
    python vetted_senses.py --migrate  rewrite vetted_senses.tsv in the score format
"""
import csv
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VETTED_TSV = os.path.join(BASE_DIR, "vetted_senses.tsv")
CONFIG_FILE = os.path.join(BASE_DIR, ".senses_config.json")
VETTING_LOG = os.path.join(BASE_DIR, "sense_vetting.jsonl")
ENG_XLSX = "GLB_ENG_WiktionarySenses.xlsx"
MULTI_XLSX = "GLB_MULTI_WiktionarySenses.xlsx"

COLUMNS = ["Glb", "Source", "Eng", "Prt of Sp", "VerbType", "Wiktionary Sense",
           "App?", "Tier"]
# Tiers, highest first: expert, vetted (derived from the scores), LLM, automatic script.
TIERS = ("e", "v", "l", "a")
MACHINE_TIERS = ("l", "a")
SCORES = (1, 2, 3, 4, 5)
ACCEPT_MEAN, REJECT_MEAN = 4, 2
# The page's old verdicts on the 1-5 scale (user decisions 2026-11-20/21): they were not
# confidence-graded, so leaning, not certain. "clear" (None) removes a page score.
VERDICT_SCORES = {"s": 4, "n": 2, "u": 3}
# The sheet: the vetter block starts right of this column; Mean and Decision are formulas.
DECISION_COLUMN = "Decision"
MEAN_COLUMN = "Mean"
DEFAULT_OWNER = "Paleos"
# The shared sheet shows the machine's suggestion as a number on the vetters' scale, with who
# made it, instead of the stored App?/Tier letters (user, 2026-11-21: numbers, not letters).
# "cross-check" is the generator's Spa/Epo translation check, never stored.
SUGGESTION_COLUMN = "Suggestion"
SUGGESTED_BY_COLUMN = "Suggested by"
SUGGESTERS = {"a": "script", "l": "LLM", "e": "expert", "": "cross-check"}
TIER_OF_SUGGESTER = {name.lower(): tier for tier, name in SUGGESTERS.items()}
NOT_A_VETTER = ("note", "comment")  # headers containing these are free-text columns


def _config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def senses_dir():
    """The spreadsheets' directory from .senses_config.json, or None."""
    return _config().get("senses_dir")


def owner():
    """The pseudonym whose column the page writes (SV_VETTER > config "vetter" > Paleos)."""
    return os.environ.get("SV_VETTER") or _config().get("vetter") or DEFAULT_OWNER


OWNER = owner()


def score_value(value):
    """A cell or log value as a score 1-5, None for blank; raises ValueError otherwise."""
    if value is None or str(value).strip() == "":
        return None
    number = float(str(value).strip().replace(",", "."))
    if number != int(number) or int(number) not in SCORES:
        raise ValueError(value)
    return int(number)


def entry_score(entry):
    """The score a log entry gives (old verdicts mapped), or None for "clear"."""
    if "score" in entry:
        return entry["score"]
    return VERDICT_SCORES.get(entry.get("verdict"))


def decide(scores):
    """'s' accepted, 'n' rejected, '' undecided, None when nobody has scored."""
    given = [s for s in scores.values() if s]
    if not given:
        return None
    mean = sum(given) / len(given)
    return "s" if mean >= ACCEPT_MEAN else "n" if mean <= REJECT_MEAN else ""


def suggestion_cells(app, tier):
    """(number, who) for the sheet from a stored App?/Tier: s 4, n 2 (an expert's 5 and 1)."""
    if app not in ("s", "n"):
        return None, None
    if tier == "e":
        return (5 if app == "s" else 1), SUGGESTERS["e"]
    return (4 if app == "s" else 2), SUGGESTERS.get(tier, tier)


def suggestion_letters(number, who):
    """(App?, Tier) from the sheet's Suggestion / Suggested by cells (the reverse)."""
    try:
        value = score_value(number)
    except ValueError:
        return "", ""
    if value is None or value == 3:
        return "", ""
    tier = TIER_OF_SUGGESTER.get(str(who or "").strip().lower(), str(who or "").strip())
    return ("s" if value >= 4 else "n"), tier


def mean(scores):
    given = [s for s in scores.values() if s]
    return round(sum(given) / len(given), 2) if given else None


def row_id(word, label):
    """The sense id of the page and its log (as sense_ranking.row_id): sha1 "word|label"[:16]."""
    return hashlib.sha1(f"{word}|{label}".encode()).hexdigest()[:16]


def _key(r):
    return (r["Glb"], r["Eng"], r["Prt of Sp"], r["VerbType"], r["Wiktionary Sense"])


# ---------------------------------------------------------------------------
# The TSV
# ---------------------------------------------------------------------------

def _read_tsv(notes=None):
    """Stored rows (App?/Tier = machine suggestion or expert) with "scores", and the vetter
    columns in order. A TSV in the old format (App?/Tier only) is migrated as it is read:
    Tier v was the owner's verdict, s -> 4, anything else -> 2 (a vetted row without s was
    the old spreadsheets' 'does not apply')."""
    with open(VETTED_TSV, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)
        vetters = header[len(COLUMNS):]
        rows = []
        for cells in reader:
            cells += [""] * (len(header) - len(cells))
            r = dict(zip(COLUMNS, cells))
            r["scores"] = {}
            for name, cell in zip(vetters, cells[len(COLUMNS):]):
                try:
                    if (s := score_value(cell)) is not None:
                        r["scores"][name] = s
                except ValueError:
                    if notes is not None:
                        notes.append(f"{r['Glb']} / {r['Eng']}: {name} {cell!r} is not a score 1-5 (skipped)")
            rows.append(r)
    if not vetters:  # the old format
        vetters = [OWNER]
        for r in rows:
            if r["Tier"] == "v":
                r["scores"] = {OWNER: 4 if r["App?"] == "s" else 2}
                r["App?"] = r["Tier"] = ""
    return rows, vetters


def _write_tsv(rows, vetters, out=None):
    out = out or VETTED_TSV
    order = [OWNER] + [v for v in vetters if v != OWNER]
    tmp = out + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(COLUMNS + order)
        for r in rows:
            if not r["Tier"] and not r["scores"]:
                continue
            w.writerow([r[c] for c in COLUMNS] + [r["scores"].get(v, "") for v in order])
    os.replace(tmp, out)


# ---------------------------------------------------------------------------
# The page's log
# ---------------------------------------------------------------------------

def log_entries(path=None):
    path = path or VETTING_LOG
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)


def log_scores(path=None):
    """{(vetter, glb, eng, pos, verb_type, sense): (score, when)} from the page's log.

    Replays the log, so the latest entry per row wins and undos count ("undo" entries carry
    the restored verdict). A score of None ("clear") removes the page's score, leaving the
    TSV's. Each entry names the rows it covers in "keys" ([eng, pos, verb_type] triples); a
    sense is one label of one word, met under each of the word's English glosses that share it.
    """
    latest = {}
    for entry in log_entries(path):
        vetter = entry.get("vetter") or OWNER
        score = entry_score(entry)
        for eng, pos, vt in entry.get("keys", ()):
            key = (vetter, entry["word"], eng, pos, vt, entry["label"])
            if score is None:
                latest.pop(key, None)
            else:
                latest[key] = (score, entry["when"])
    return latest


def append_log(entries, path=None):
    with open(path or VETTING_LOG, "a", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Reading: effective decisions
# ---------------------------------------------------------------------------

def _settle(r):
    """Effective App?/Tier, Mean and Decision of a stored row, in place."""
    r["stored_app"], r["stored_tier"] = r["App?"], r["Tier"]
    r["Mean"], r["Decision"] = mean(r["scores"]), decide(r["scores"])
    if r["Tier"] == "e":
        return r
    if r["Decision"] in ("s", "n"):
        r["App?"], r["Tier"] = r["Decision"], "v"
    # Undecided or unscored: the stored machine suggestion (or an unknown tier such as 'sl',
    # kept as is and not used by the builder).
    return r


def load_rows(include_log=True, sync_first=True):
    """Every decision as a dict keyed by COLUMNS (effective App?/Tier) plus "scores"
    {vetter: 1-5}, "Mean", "Decision" ('s'/'n'/''/None), "stored_app", "stored_tier".
    The page's log is laid over the owner's column unless include_log is False."""
    if sync_first:
        sync()
    rows, _ = _read_tsv()
    if include_log:
        by_key = {(r["Source"], _key(r)): r for r in rows}
        for (vetter, *key), (score, _) in log_scores().items():
            r = by_key.get(("en", tuple(key)))
            if r is None:
                glb, eng, pos, vt, sense = key
                r = by_key[("en", tuple(key))] = {
                    "Glb": glb, "Source": "en", "Eng": eng, "Prt of Sp": pos, "VerbType": vt,
                    "Wiktionary Sense": sense, "App?": "", "Tier": "", "scores": {}}
                rows.append(r)
            r["scores"][vetter] = score
    return [_settle(r) for r in rows]


def vetters_known():
    """The vetter columns of the TSV, the owner first."""
    _, vetters = _read_tsv()
    return [OWNER] + [v for v in vetters if v != OWNER]


def load_markings(source="en", include_log=True):
    """{(glb, eng, pos, verb_type, sense): (app, tier, scores, stored_app, stored_tier)} --
    what the sense generator inherits when it rebuilds the spreadsheet (effective App?/Tier,
    the vetters' scores, and the machine suggestion as stored)."""
    return {_key(r): (r["App?"], r["Tier"], r["scores"], r["stored_app"], r["stored_tier"])
            for r in load_rows(include_log) if r["Source"] == source}


def load_vetted():
    """The senses that go into menalariExtension.tsv: accepted by people (App? s, Tier v or e).
    Dicts as the extension builder uses them."""
    return [{"glb": r["Glb"], "lookup_word": r["Eng"], "pos": r["Prt of Sp"],
             "verb_type": r["VerbType"], "sense": r["Wiktionary Sense"],
             "source": r["Source"]}
            for r in load_rows()
            if r["App?"] == "s" and r["Tier"] in ("v", "e")
            and r["Glb"] and r["Eng"] and r["Prt of Sp"] and r["Wiktionary Sense"]]


# ---------------------------------------------------------------------------
# The spreadsheets
# ---------------------------------------------------------------------------

def vetter_columns(header):
    """{column index: vetter} -- every named column right of "Decision" that is not a note."""
    if DECISION_COLUMN not in header:
        return {}
    start = header.index(DECISION_COLUMN) + 1
    return {i: name.strip() for i, name in enumerate(header) if i >= start and name.strip()
            and not any(word in name.lower() for word in NOT_A_VETTER)}


def _sheet_rows(path):
    from openpyxl import load_workbook
    wb = load_workbook(path, read_only=True)
    ws = wb["Senses"] if "Senses" in wb.sheetnames else wb.active
    it = ws.iter_rows(values_only=True)
    header = [str(h).strip() if h is not None else "" for h in next(it, ())]
    rows = [["" if c is None else c if isinstance(c, (int, float)) else str(c) for c in r] for r in it]
    wb.close()
    return header, rows


def _clean_tier(tier, where, notes):
    """Strip stray whitespace ("v " was silently not 'v'); keep and report
    anything that is not a known tier rather than guess what was meant."""
    t = tier.strip()
    if t != tier:
        notes.append(f"{where}: Tier {tier!r} read as {t!r}")
    if t and t not in TIERS:
        notes.append(f"{where}: unknown Tier {t!r} kept as is (not used by the builder)")
    return t


def _sheet_records(header, rows, source, notes):
    """(source, key, app, tier, {vetter: score}) per sheet row, first occurrence of a key only."""
    col = {name: i for i, name in enumerate(header)}
    eng_col = col.get("Eng", col.get("LookupWord"))
    sense_col = col.get("Wiktionary Sense (in Translations)", col.get("Wiktionary Sense"))
    if eng_col is None or sense_col is None or "Prt of Sp" not in col:
        raise ValueError("the sheet lacks Eng/LookupWord, Prt of Sp or Wiktionary Sense")
    vetters = vetter_columns(header)

    def get(row, name):
        i = col.get(name)
        return str(row[i]).strip() if i is not None and i < len(row) and row[i] != "" else ""

    def exact(row, i):
        # Key cells exactly as written: word-list entries can end in a space ("kabel "), and
        # the TSV keys keep it; a stripped key would file the judgement as a new sense.
        return str(row[i]) if i is not None and i < len(row) and row[i] not in ("", None) else ""

    seen = set()
    for row in rows:
        glb = exact(row, 0)
        sense = exact(row, sense_col)
        if not glb.strip() or not sense.strip():
            continue
        src = get(row, "Source") or source
        key = (glb, exact(row, eng_col), exact(row, col.get("Prt of Sp")), exact(row, col.get("VerbType")), sense)
        if (src, key) in seen:
            continue
        seen.add((src, key))
        where = f"{glb} / {key[1]} ({key[2]})"
        scores = {}
        for i, name in vetters.items():
            cell = row[i] if i < len(row) else ""
            try:
                if (s := score_value(cell)) is not None:
                    scores[name] = s
            except ValueError:
                notes.append(f"{where}: {name} {cell!r} is not a score 1-5 (skipped)")
        if SUGGESTION_COLUMN in col:  # the score-format sheet
            app, tier = suggestion_letters(get(row, SUGGESTION_COLUMN), get(row, SUGGESTED_BY_COLUMN))
            tier = _clean_tier(tier, where, notes)
        else:  # an older sheet with App?/Tier letters
            tier = _clean_tier(get(row, "Tier"), where, notes)
            app = get(row, "App?")
        if tier == "v" and OWNER not in vetters:
            # A sheet without vetter columns: Tier v was the owner's verdict.
            scores.setdefault(OWNER, 4 if app == "s" else 2)
        yield src, key, app, tier, scores, vetters


def export(eng_xlsx, multi_xlsx=None, out=None):
    """Read the spreadsheets' scores and machine suggestions into `out`. Returns notes on
    values that needed attention. The owner's sheet edits become log entries (see above)."""
    notes = []
    out = out or VETTED_TSV
    stored, vetters = _read_tsv(notes) if os.path.exists(out) else ([], [OWNER])
    by_key = {(r["Source"], _key(r)): r for r in stored}
    page = log_scores()
    vetters = list(vetters)
    new_entries = []

    def merge(path, source):
        sheet_time = datetime.fromtimestamp(os.path.getmtime(path)).isoformat(timespec="seconds")
        header, rows = _sheet_rows(path)
        for src, key, app, tier, scores, sheet_vetters in _sheet_records(header, rows, source, notes):
            for name in sheet_vetters.values():
                if name not in vetters:
                    vetters.append(name)
            r = by_key.get((src, key))
            if r is None:
                glb, eng, pos, vt, sense = key
                r = by_key[(src, key)] = {"Glb": glb, "Source": src, "Eng": eng, "Prt of Sp": pos,
                                          "VerbType": vt, "Wiktionary Sense": sense,
                                          "App?": "", "Tier": "", "scores": {}}
                stored.append(r)
            # Machine suggestions and expert decisions come from the sheet; Tier v there is
            # derived from the scores, so the stored suggestion stays.
            if tier != "v":
                r["App?"], r["Tier"] = (app, tier) if tier else ("", "")
            # The other vetters' columns: the sheet is theirs (a blank cell clears).
            for name in sheet_vetters.values():
                if name == OWNER:
                    continue
                if name in scores:
                    r["scores"][name] = scores[name]
                else:
                    r["scores"].pop(name, None)
            mine = scores.get(OWNER)
            if mine is None:
                continue
            if src != "en":  # no page for other editions: the sheet is the owner's record
                r["scores"][OWNER] = mine
                continue
            logged = page.get((OWNER, *key))
            current = logged[0] if logged else r["scores"].get(OWNER)
            if mine == current or (logged and logged[1] > sheet_time):
                continue  # unchanged, or a later page score wins
            glb, eng, pos, vt, sense = key
            new_entries.append({"id": row_id(glb.lower(), sense), "word": glb,
                                "label": sense, "score": mine, "vetter": OWNER,
                                "when": sheet_time, "batch": f"sheet-{sheet_time}",
                                "source": "sheet", "keys": [[eng, pos, vt]]})
            page[(OWNER, *key)] = (mine, sheet_time)

    merge(eng_xlsx, "en")
    if multi_xlsx and os.path.exists(multi_xlsx):
        merge(multi_xlsx, "")
    if new_entries:
        append_log(new_entries)
        notes.append(f"{len(new_entries)} edits of the {OWNER} column in the sheet logged "
                     f"(later than the page's scores for those rows)")
    _write_tsv(stored, vetters, out)
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
        print(f"Reading vetting scores from {d} into {os.path.basename(VETTED_TSV)}...")
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


def lock_file(path):
    """LibreOffice's lock file for `path` (present while someone has it open here)."""
    return os.path.join(os.path.dirname(path), f".~lock.{os.path.basename(path)}#")


def backup(path):
    """A dated copy in a backups/ folder beside the sheet (the home disk fills up)."""
    folder = os.path.join(os.path.dirname(path), "backups")
    os.makedirs(folder, exist_ok=True)
    stem, ext = os.path.splitext(os.path.basename(path))
    target = os.path.join(folder, f"{stem}_{datetime.now():%Y%m%d_%H%M%S}{ext}")
    shutil.copy2(path, target)
    return target


def push_owner_scores(path=None):
    """Write the owner's current scores (TSV + page log) into the owner's column of the shared
    sheet, so the other vetters see them. Returns a message; changes nothing when the sheet is
    open in LibreOffice or has no vetter block."""
    from openpyxl import load_workbook
    d = senses_dir()
    path = path or (os.path.join(d, ENG_XLSX) if d else None)
    if not path or not os.path.exists(path):
        return "No shared sheet to push to (no senses_dir or no GLB_ENG_WiktionarySenses.xlsx)."
    if os.path.exists(lock_file(path)):
        return f"{os.path.basename(path)} is open (lock file present): close it and push again."
    sync(verbose=False)  # the sheet's own edits first, or they would be overwritten
    mine = {_key(r): r["scores"].get(OWNER) for r in load_rows(sync_first=False) if r["Source"] == "en"}
    wb = load_workbook(path)
    ws = wb["Senses"] if "Senses" in wb.sheetnames else wb.active
    header = [str(c.value).strip() if c.value is not None else "" for c in ws[1]]
    vetters = vetter_columns(header)
    if not vetters and DECISION_COLUMN not in header:
        wb.close()
        return f"{os.path.basename(path)} has no vetter columns (regenerate it with the sense generator)."
    col = next((i for i, name in vetters.items() if name == OWNER), None)
    if col is None:  # first blank header right of Decision
        col = next(i for i in range(header.index(DECISION_COLUMN) + 1, len(header) + 1)
                   if i >= len(header) or not header[i])
        ws.cell(row=1, column=col + 1, value=OWNER)
    c = {name: i for i, name in enumerate(header)}
    sense_col = c.get("Wiktionary Sense (in Translations)", c.get("Wiktionary Sense"))
    changed = 0
    for row in ws.iter_rows(min_row=2):
        def get(i):  # exact, as _sheet_records reads keys ("kabel " keeps its space)
            return str(row[i].value) if i is not None and i < len(row) and row[i].value not in (None, "") else ""
        key = (get(0), get(c["Eng"]), get(c["Prt of Sp"]), get(c.get("VerbType")), get(sense_col))
        if not key[0].strip() or not key[4].strip():
            continue  # a row without a sense has no score
        score = mine.get(key, mine.get(key[:3] + ("",) + key[4:]))
        cell = ws.cell(row=row[0].row, column=col + 1)
        if (cell.value if cell.value != "" else None) != score:
            cell.value = score
            changed += 1
    if not changed:
        wb.close()
        return f"{os.path.basename(path)}: the {OWNER} column is up to date."
    saved = backup(path)
    tmp = path + ".tmp.xlsx"
    wb.save(tmp)
    wb.close()
    os.replace(tmp, path)
    return f"{os.path.basename(path)}: {changed} cells of the {OWNER} column written (backup {saved})."


if __name__ == "__main__":
    if "--push" in sys.argv:
        print(push_owner_scores())
    elif "--migrate" in sys.argv:
        rows, vetters = _read_tsv()
        _write_tsv(rows, vetters)
        print(f"Wrote {VETTED_TSV} with vetter columns {', '.join(vetters)}")
    else:
        d = senses_dir() or "."
        for note in export(os.path.join(d, ENG_XLSX), os.path.join(d, MULTI_XLSX)):
            print(note)
        print(f"Wrote {VETTED_TSV}")
