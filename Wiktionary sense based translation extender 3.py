import os
import json
import shutil
from datetime import datetime
from openpyxl import Workbook
from openpyxl.utils import get_column_letter

from wiktionary_db import WiktionaryDB
import vetted_senses
import sense_rows
from wiktionary_constants import _load_markings_from_xlsx, _find_latest_backup


# ---------------------------------------------------------------------------
# Senses file path: configurable directory, persisted across runs
# ---------------------------------------------------------------------------

SENSES_FILENAME = "GLB_ENG_WiktionarySenses.xlsx"
CONFIG_FILE = ".senses_config.json"

default_dir = "./"
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        default_dir = json.load(f).get("senses_dir", default_dir)

senses_dir = input(
    f"Directory for {SENSES_FILENAME} [{default_dir}]:\n"
).strip() or default_dir

with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
    json.dump({"senses_dir": senses_dir}, f)

senseKeyPath = os.path.join(senses_dir, SENSES_FILENAME)

# ---------------------------------------------------------------------------
# Preload the vetting decisions (vetted_senses.tsv, re-exported from the
# spreadsheet first when that is newer) and the spreadsheet's column widths
# ---------------------------------------------------------------------------

existing_markings = vetted_senses.load_markings("en")
print(f"Loaded {len(existing_markings)} vetted markings from "
      f"{os.path.basename(vetted_senses.VETTED_TSV)}")

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
    if os.path.exists(senseKeyPath):
        backup_dir = "./backups"
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"GLB_ENG_WiktionarySenses_{timestamp}.xlsx"
        backup_path = os.path.join(backup_dir, backup_name)
        shutil.copy2(senseKeyPath, backup_path)
        print(f"Backed up {senseKeyPath} to {backup_path}")

# ---------------------------------------------------------------------------
# Main loop: the rows come from sense_rows.py (shared with sense_vetter.py)
# ---------------------------------------------------------------------------

wb_out = Workbook()
ws_out = wb_out.active
ws_out.title = "Senses"

senses_header = sense_rows.HEADER
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
}
for i, name in enumerate(senses_header, 1):
    col_letter = get_column_letter(i)
    if name in existing_col_widths:
        ws_out.column_dimensions[col_letter].width = existing_col_widths[name]
    elif name in DEFAULT_WIDTHS:
        ws_out.column_dimensions[col_letter].width = DEFAULT_WIDTHS[name]
    else:
        ws_out.column_dimensions[col_letter].width = min(len(name) + 4, 10 * CM)

for sense_row in sense_rows.rows(db, existing_markings, startPrefix, "./" + menalari_name):
    ws_out.append(sense_row)
    if len(sense_row) > 7:
        print("\t".join(sense_row))

wb_out.save(outputPath)
db.close()
print(f"Saved senses to {outputPath}")
