import os
import json
import shutil
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from wiktionary_db import WiktionaryDB
import vetted_senses
import sense_ranking
import sense_rows
from wiktionary_constants import _load_markings_from_xlsx, _find_latest_backup


# ---------------------------------------------------------------------------
# Senses file path: configurable directory, persisted across runs
# ---------------------------------------------------------------------------

SENSES_FILENAME = "GLB_ENG_WiktionarySenses.xlsx"
CONFIG_FILE = ".senses_config.json"

config = {}
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
default_dir = config.get("senses_dir", "./")

senses_dir = input(
    f"Directory for {SENSES_FILENAME} [{default_dir}]:\n"
).strip() or default_dir

config["senses_dir"] = senses_dir  # other keys (the owner's "vetter") are kept
with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
    json.dump(config, f)

senseKeyPath = os.path.join(senses_dir, SENSES_FILENAME)

# ---------------------------------------------------------------------------
# Preload the vetting decisions (vetted_senses.tsv, re-exported from the
# spreadsheet first when that is newer) and the spreadsheet's column widths
# ---------------------------------------------------------------------------

existing_markings = vetted_senses.load_markings("en")
vetters = vetted_senses.vetters_known()
print(f"Loaded {len(existing_markings)} vetted markings from "
      f"{os.path.basename(vetted_senses.VETTED_TSV)} (vetters: {', '.join(vetters)})")

existing_col_widths = {}  # header name -> width (character units)
for _path in (senseKeyPath, _find_latest_backup()):
    if _path and os.path.exists(_path):
        try:
            _, existing_col_widths = _load_markings_from_xlsx(_path)
            break
        except Exception as e:
            print(f"Warning: column widths not read from {_path} ({e})")

# ---------------------------------------------------------------------------
# LMDB database
# ---------------------------------------------------------------------------

db = WiktionaryDB(readonly=True)


# ---------------------------------------------------------------------------
# Download word-list if needed
# ---------------------------------------------------------------------------

menalari_name = "word-list.csv"
if not os.path.exists("./word-list.csv"):
    import wget
    print("Downloading the Globasa word-list")
    wget.download("https://cdn.globasa.net/api2/word-list.csv", menalari_name)

# ---------------------------------------------------------------------------
# Interactive start prefix
# ---------------------------------------------------------------------------

startPrefix = input(
    "Lexi ingay na xoru har keto fe xoru? / What should the word begin with at the start?\n"
    "Am sol presyon 'enter' na xoru xorfe xoru. / Just hit enter to start from the beginning.\n"
)

# ---------------------------------------------------------------------------
# Determine output path: full run overwrites senses file (with backup),
# filtered run writes to a separate file.
# ---------------------------------------------------------------------------

if startPrefix:
    outputPath = os.path.join(senses_dir, 'GLB_ENG_WiktionarySenses_initial.xlsx')
else:
    outputPath = senseKeyPath
if os.path.exists(vetted_senses.lock_file(outputPath)):
    raise SystemExit(f"{outputPath} is open (LibreOffice lock file): close it first, "
                     "or the vetters' unsaved scores would be lost. If it is not open anywhere, "
                     f"the lock is left over from a crash: delete {vetted_senses.lock_file(outputPath)}")
if not startPrefix:
    if os.path.exists(senseKeyPath):
        backup_dir = "./backups"
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"GLB_ENG_WiktionarySenses_{timestamp}.xlsx"
        backup_path = os.path.join(backup_dir, backup_name)
        shutil.copy2(senseKeyPath, backup_path)
        print(f"Backed up {senseKeyPath} to {backup_path}")

# ---------------------------------------------------------------------------
# Main loop: the rows come from sense_rows.py (shared with sense_vetter.py). They are
# buffered so each word's rows can be ordered like the vetter page: by gloss part of
# speech, most promising sense first (sense_ranking.py), the rows of one sense together.
# ---------------------------------------------------------------------------

all_rows = list(sense_rows.rows(db, existing_markings, startPrefix, "./" + menalari_name,
                                vetters=vetters))
db.close()
n_header = len(sense_rows.HEADER)
glosses = sense_ranking.load_glosses("./" + menalari_name)
senses = sense_ranking.senses_from_rows((r[:n_header] for r in all_rows), glosses)
sense_ranking.rank(senses, glosses)
COL = {name: i for i, name in enumerate(sense_rows.HEADER)}
SENSE_COL = next(i for i, name in enumerate(sense_rows.HEADER) if name.startswith("Wiktionary Sense"))


def word_order(rows):
    """One word's rows: PoS groups in first-seen order; in each, the senses people accepted first
    (highest mean first), then the unjudged by the ranking score, then the rejected
    (sense_ranking.judged_key); a sense's rows together, in their original order. Rows without a
    sense close their PoS group."""
    pos_first, sense_first, judged, keyed = {}, {}, {}, []
    for i, r in enumerate(rows):
        label = r[SENSE_COL] if len(r) > SENSE_COL else ""
        sense = senses.get(sense_ranking.row_id(r[0].strip().lower(), label.strip())) if label else None
        pos = sense["gloss_pos"] if sense else (r[COL["Prt of Sp"]] if len(r) > COL["Prt of Sp"] else "")
        pos_first.setdefault(pos, i)
        sense_first.setdefault(label, i)
        if label not in judged:  # the sense's first row carries its scores
            judged[label] = sense_ranking.judged_key(
                {v: sc for v, sc in zip(vetters, r[n_header:]) if sc != ''},
                vetted_senses.ACCEPT_MEAN, vetted_senses.REJECT_MEAN)
        score = sense["score"] if sense else -10 ** 6
        keyed.append(((pos_first[pos], (2, 0) if not sense else judged[label], -score, sense_first[label], i), r))
    return [r for _, r in sorted(keyed, key=lambda k: k[0])]


def ordered_rows():
    group = []
    for r in all_rows:
        if group and r[0] != group[0][0]:
            yield from word_order(group)
            group = []
        group.append(r)
    yield from word_order(group)


wb_out = Workbook()
ws_out = wb_out.active
ws_out.title = "Senses"

SPARE_VETTERS = 10  # blank, validated columns where new vetters add their pseudonym
senses_header = (list(sense_rows.HEADER) + [vetted_senses.MEAN_COLUMN, vetted_senses.DECISION_COLUMN]
                 + vetters)
ws_out.append(senses_header)

# Column widths: inherit from existing file, fall back to defaults
# Default: ~4.96 chars/cm (8.43 default width ≈ 1.70 cm)
CM = 4.96
DEFAULT_WIDTHS = {
    'Definition': 3 * CM, 'Example': 3 * CM,
    'Example 2': 3 * CM, 'Example 3': 3 * CM,
    '|': 1 * CM,
    'VerbType': 2 * CM,
    'App?': 1 * CM, 'Tier': 1 * CM,
    vetted_senses.MEAN_COLUMN: 1.5 * CM, vetted_senses.DECISION_COLUMN: 2.2 * CM,
}
for i, name in enumerate(senses_header, 1):
    col_letter = get_column_letter(i)
    if name in existing_col_widths:
        ws_out.column_dimensions[col_letter].width = existing_col_widths[name]
    elif name in DEFAULT_WIDTHS:
        ws_out.column_dimensions[col_letter].width = DEFAULT_WIDTHS[name]
    elif i > n_header + 2:
        ws_out.column_dimensions[col_letter].width = max(len(name) + 2, 2 * CM)
    else:
        ws_out.column_dimensions[col_letter].width = min(len(name) + 4, 10 * CM)

mean_letter = get_column_letter(n_header + 1)
first_vetter = get_column_letter(n_header + 3)
last_vetter = get_column_letter(n_header + 2 + len(vetters) + SPARE_VETTERS)
n_rows = 1
for r in ordered_rows():
    n_rows += 1
    if len(r) > n_header:  # a sense row: formulas, then the vetters' scores
        scores = [int(v) if v != '' else None for v in r[n_header:]]
        r = r[:n_header] + [
            f'=IFERROR(ROUND(AVERAGE({first_vetter}{n_rows}:{last_vetter}{n_rows}),2),"")',
            f'=IF({mean_letter}{n_rows}="","",IF({mean_letter}{n_rows}>={vetted_senses.ACCEPT_MEAN},"accepted",'
            f'IF({mean_letter}{n_rows}<={vetted_senses.REJECT_MEAN},"rejected","undecided")))'] + scores
    ws_out.append(r)

# Scores are whole numbers 1-5; the header row and the vetter block stand out.
scale = DataValidation(type="whole", operator="between", formula1="1", formula2="5", allow_blank=True,
                       showErrorMessage=True, errorTitle="Score 1-5",
                       error="5 = applies, 4 = probably, 3 = unsure, 2 = probably not, 1 = does not apply")
scale.add(f"{first_vetter}2:{last_vetter}{max(n_rows, 2)}")
ws_out.add_data_validation(scale)
bold = Font(bold=True)
vetter_fill = PatternFill("solid", fgColor="FFF2CC")
for i in range(1, len(senses_header) + SPARE_VETTERS + 1):
    cell = ws_out.cell(row=1, column=i)
    cell.font = bold
    if i > n_header + 2:
        cell.fill = vetter_fill
        ws_out.column_dimensions[get_column_letter(i)].width = max(
            ws_out.column_dimensions[get_column_letter(i)].width or 0, 2 * CM)
ws_out.freeze_panes = "B2"
ws_out.auto_filter.ref = f"A1:{last_vetter}{n_rows}"

how = wb_out.create_sheet("How to vet")
for line in [
    ["How to vet these senses"],
    [],
    ["Each row pairs a Globasa word (Glb) and one of its English glosses (Eng) with a Wiktionary sense of"],
    ["that English word. Question: does this sense express the meaning of the Globasa word?"],
    ["The word's other senses for the same part of speech follow, the most promising first."],
    [],
    ["Score", "Meaning"],
    [5, "applies: sure"],
    [4, "probably applies"],
    [3, "unsure"],
    [2, "probably does not apply"],
    [1, "does not apply: sure"],
    [],
    ["Your column: the yellow columns right of 'Decision'. Use an existing one with your pseudonym, or type"],
    ["your pseudonym (never your real name) into the first blank yellow header. Score only in your own column;"],
    ["leave a cell blank when you have no opinion."],
    [],
    [f"Mean = the average of all scores. Decision: mean >= {vetted_senses.ACCEPT_MEAN} accepted, "
     f"<= {vetted_senses.REJECT_MEAN} rejected, otherwise undecided (counts as not vetted)."],
    ["App? / Tier: the computer's suggestion (Tier a = script, l = LLM), or v = already decided by the scores."],
    ["Clues: Spa / Epo and the other language columns are the sense's translations; compare them with the"],
    ["Globasa word's own translations in the word list."],
    ["Columns whose header contains 'note' or 'comment' are free text and are not read as scores."],
]:
    how.append(line)
how["A1"].font = Font(bold=True, size=14)
how.column_dimensions["A"].width = 12
how.column_dimensions["B"].width = 40

wb_out.save(outputPath)
print(f"Saved senses to {outputPath} ({n_rows - 1} rows, each word's senses ranked by part of speech)")
