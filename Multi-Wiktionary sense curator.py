"""Interactive CLI for curating non-English Wiktionary sense-marked translations.

Workflow:
  1. Enter a Globasa word
  2. See suggested lookup words from word-list.csv translation columns
  3. Pick a suggestion or type "word;lang" manually (e.g. "est-ce que;fr")
  4. See all senses with translations, select which to keep
  5. Selected senses appended to GLB_MULTI_WiktionarySenses.xlsx
"""

import os
import sys
import csv
import json
import re

from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter

from wiktionary_db import WiktionaryDB
from wiktionary_constants import (
    GLOSSPOS_TO_WIKT, WIKT_POS_FALLBACKS, SENSES_LANGS, WIKTIONARY_SOURCES,
    lang_display_name, extract_italic_annotation, get_sense_lang_translations,
    _load_markings_from_rows, _load_markings_from_xlsx, _find_latest_backup,
)

# ---------------------------------------------------------------------------
# csv.field_size_limit fix
# ---------------------------------------------------------------------------

maxInt = sys.maxsize
while True:
    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt / 10)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

MULTI_SENSES_FILENAME = "GLB_MULTI_WiktionarySenses.xlsx"
CONFIG_FILE = ".senses_config.json"

default_dir = "./"
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        default_dir = json.load(f).get("senses_dir", default_dir)

senses_dir = input(
    f"Directory for {MULTI_SENSES_FILENAME} [{default_dir}]:\n"
).strip() or default_dir

multi_senses_path = os.path.join(senses_dir, MULTI_SENSES_FILENAME)

# ---------------------------------------------------------------------------
# Load word-list.csv
# ---------------------------------------------------------------------------

menalari_name = "word-list.csv"
if not os.path.exists("./" + menalari_name):
    import wget
    print("Downloading the Globasa word-list")
    wget.download("https://cdn.globasa.net/api2/word-list.csv", menalari_name)

wordlist = {}  # word -> dict of column values
with open("./" + menalari_name, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        wordlist[row['Word']] = row

# ---------------------------------------------------------------------------
# Open non-English LMDBs
# ---------------------------------------------------------------------------

dbs = {}
available_sources = []
for code, config in WIKTIONARY_SOURCES.items():
    lmdb_dir = config['lmdb_dir']
    if os.path.exists(lmdb_dir):
        dbs[code] = WiktionaryDB(path=lmdb_dir, readonly=True)
        available_sources.append(code)
        print(f"  Opened {code} LMDB ({config['native_lang_name']})")

if not dbs:
    print("No non-English LMDBs found. Run 'JSONL parser non-English.py' first.")
    sys.exit(1)

print(f"Available sources: {', '.join(available_sources)}")

# ---------------------------------------------------------------------------
# Load existing curated senses
# ---------------------------------------------------------------------------

existing_markings = {}
existing_col_widths = {}

if os.path.exists(multi_senses_path):
    try:
        existing_markings, existing_col_widths = _load_markings_from_xlsx(multi_senses_path)
        print(f"Loaded {len(existing_markings)} existing curated senses")
    except Exception as e:
        print(f"Warning: could not load {multi_senses_path}: {e}")

# Track curated keys to avoid duplicates within this session
curated_keys = set(existing_markings.keys())

# ---------------------------------------------------------------------------
# Load or create output workbook
# ---------------------------------------------------------------------------

senses_lang_headers = [lang_display_name(c) for c in SENSES_LANGS]

HEADER = (['Glb', 'Source', 'LookupWord', 'Prt of Sp',
           'Wiktionary Sense',
           'Definition', 'Example', 'Example 2', 'Example 3',
           '|',
           'App?', 'Tier']
          + senses_lang_headers)

if os.path.exists(multi_senses_path):
    wb_out = load_workbook(multi_senses_path)
    ws_out = wb_out.active
    print(f"Appending to existing {multi_senses_path}")
else:
    wb_out = Workbook()
    ws_out = wb_out.active
    ws_out.title = "Senses"
    ws_out.append(HEADER)
    CM = 4.96
    DEFAULT_WIDTHS = {
        'Definition': 3 * CM, 'Example': 3 * CM,
        'Example 2': 3 * CM, 'Example 3': 3 * CM,
        '|': 1 * CM, 'App?': 1 * CM, 'Tier': 1 * CM,
    }
    for i, name in enumerate(HEADER, 1):
        col_letter = get_column_letter(i)
        if name in DEFAULT_WIDTHS:
            ws_out.column_dimensions[col_letter].width = DEFAULT_WIDTHS[name]
        else:
            ws_out.column_dimensions[col_letter].width = min(len(name) + 4, 10 * CM)
    print(f"Created new {multi_senses_path}")


def save_workbook():
    wb_out.save(multi_senses_path)


# ---------------------------------------------------------------------------
# Helper: extract lookup words from a word-list translation field
# ---------------------------------------------------------------------------

_PAREN_RE = re.compile(r'\([^)]*\)')


def extract_lookup_words(text):
    """Extract individual lookup words from a word-list translation field.
    Strips parenthetical annotations and italic markdown, splits on commas/semicolons."""
    words = []
    for part in re.split(r'[,;]', text):
        part = part.strip()
        if not part:
            continue
        # Strip italic annotations like (_bird_)
        stripped, _ = extract_italic_annotation(part)
        if not stripped:
            continue
        # Strip PoS prefix like "n: " or "f: "
        if ':' in stripped and len(stripped.split(':')[0]) <= 6:
            stripped = stripped.split(':', 1)[1].strip()
        # Strip plain parentheticals
        stripped = _PAREN_RE.sub('', stripped).strip()
        if stripped and stripped != '_':
            words.append(stripped)
    return words


# ---------------------------------------------------------------------------
# Helper: display sense with translations
# ---------------------------------------------------------------------------

def display_sense(idx, sense_key, lang_translations, sense_list, pos):
    """Display a Wiktionary sense with its translations."""
    # Try to find matching definition
    definition = ''
    ex1, ex2, ex3 = '', '', ''
    if sense_list:
        for s in sense_list:
            for g in s.glosses:
                if sense_key.lower() in g.lower():
                    definition = s.glosses[-1] if s.glosses else ''
                    for i, ex in enumerate(s.examples[:3]):
                        if i == 0: ex1 = ex.text
                        elif i == 1: ex2 = ex.text
                        elif i == 2: ex3 = ex.text
                    break

    print(f"\n  [{idx}] Sense: \"{sense_key}\"")
    if definition:
        print(f"      Definition: {definition[:100]}")
    if ex1:
        print(f"      Example: {ex1[:80]}")

    # Show translations summary (top languages)
    summary_langs = ['en', 'es', 'de', 'fr', 'ja', 'ru', 'cmn', 'ar', 'ko']
    trans_parts = []
    for lc in summary_langs:
        if lc in lang_translations:
            words = [t.word for t in lang_translations[lc]][:3]
            trans_parts.append(f"{lc}={','.join(words)}")
    if trans_parts:
        print(f"      Translations: {'  '.join(trans_parts)}")

    return definition, ex1, ex2, ex3


# ---------------------------------------------------------------------------
# Interactive loop
# ---------------------------------------------------------------------------

print("\n" + "=" * 60)
print("Multi-Wiktionary Sense Curator")
print("Enter Globasa word, or 'q' to quit and save.")
print("=" * 60)

added_count = 0

while True:
    print()
    glb_input = input("Globasa word: ").strip()

    if not glb_input or glb_input == 'q':
        break

    if glb_input not in wordlist:
        print(f"  '{glb_input}' not found in word-list.csv")
        continue

    wl_row = wordlist[glb_input]
    eng_text = wl_row.get('TranslationEng', '').strip()
    wordclass = wl_row.get('WordClass', '').strip()
    print(f"\n  {glb_input} — {wordclass}: {eng_text}")

    # Show suggested lookups from word-list.csv
    suggestions = []
    for code in available_sources:
        wl_col = WIKTIONARY_SOURCES[code]['wl_column']
        text = wl_row.get(wl_col, '').strip()
        if text:
            words = extract_lookup_words(text)
            if words:
                suggestions.append((code, words))
                print(f"    [{code}] {', '.join(words)}")

    if not suggestions:
        print("    No word-list.csv translations for available sources.")

    print("  Or type a word manually with language (e.g. \"est-ce que;fr\")")

    lookup_input = input("  Lookup: ").strip()
    if not lookup_input:
        continue
    if lookup_input == 'q':
        break

    # Parse input: either pick from suggestions or manual "word;lang"
    if ';' in lookup_input:
        parts = lookup_input.rsplit(';', 1)
        lookup_word = parts[0].strip()
        source_lang = parts[1].strip()
    else:
        # Try to match against suggestions
        lookup_word = lookup_input
        source_lang = None
        for code, words in suggestions:
            if lookup_input in words:
                source_lang = code
                break
        if source_lang is None and len(suggestions) == 1:
            source_lang = suggestions[0][0]
        if source_lang is None:
            print("  Ambiguous — use 'word;lang' format (e.g. \"hirondelle;fr\")")
            continue

    if source_lang not in dbs:
        print(f"  No LMDB for '{source_lang}'. Available: {', '.join(available_sources)}")
        continue

    db = dbs[source_lang]

    # Try multiple PoS variants
    # Map wordclass to Wiktionary PoS
    from Lexilista_parser import GlossPoS, parseWordEntry
    parsed = parseWordEntry(eng_text, wordclass, {})
    eng_glosses = parsed.translations.get("Eng", [])
    wikt_pos_list = list({GLOSSPOS_TO_WIKT.get(g.pos) for g in eng_glosses} - {None})

    if not wikt_pos_list:
        wikt_pos_list = ['noun', 'verb', 'adj', 'adv', 'conj', 'particle', 'phrase']

    found_any = False
    for wikt_pos in wikt_pos_list:
        pos_keys = [wikt_pos] + WIKT_POS_FALLBACKS.get(wikt_pos, [])
        for pos_key in pos_keys:
            trans_entry = db.get_translations(lookup_word, pos_key)
            if trans_entry is None:
                continue

            found_any = True
            sense_list = db.get_senses(lookup_word, pos_key) or []

            print(f"\n  Found in {source_lang} Wiktionary as \"{lookup_word}\" ({pos_key}):")

            # Display all senses
            sense_items = list(trans_entry.items())
            sense_data = []  # (sense_key, lang_translations, definition, ex1, ex2, ex3)
            for idx, (sense_key, lang_translations) in enumerate(sense_items, 1):
                definition, ex1, ex2, ex3 = display_sense(
                    idx, sense_key, lang_translations, sense_list, pos_key)
                sense_data.append((sense_key, lang_translations, definition, ex1, ex2, ex3))

            # Ask which to keep
            print(f"\n  Select senses to keep (e.g. '1,3' or 'all' or 'none'):")
            selection = input("  Keep: ").strip().lower()

            if selection in ('none', 'n', ''):
                continue
            if selection == 'all':
                selected = list(range(len(sense_data)))
            else:
                try:
                    selected = [int(x.strip()) - 1 for x in selection.split(',')]
                except ValueError:
                    print("  Invalid selection")
                    continue

            for idx in selected:
                if idx < 0 or idx >= len(sense_data):
                    continue
                sense_key, lang_translations, definition, ex1, ex2, ex3 = sense_data[idx]

                # Check for duplicates
                key = (glb_input, lookup_word, pos_key, sense_key)
                if key in curated_keys:
                    print(f"    Skipping duplicate: {sense_key}")
                    continue

                # Build sense language columns
                sense_lang_cols = [
                    get_sense_lang_translations(lang_translations, lc, pos_key)
                    for lc in SENSES_LANGS
                ]

                row = [glb_input, source_lang, lookup_word, pos_key,
                       sense_key,
                       definition, ex1, ex2, ex3,
                       '|',
                       's', 'v'] + sense_lang_cols
                ws_out.append(row)
                curated_keys.add(key)
                added_count += 1

            if selected:
                save_workbook()
                kept = len([i for i in selected if 0 <= i < len(sense_data)])
                print(f"\n  Appended {kept} sense(s) for {glb_input} "
                      f"(source: {source_lang}/{lookup_word})")

    if not found_any:
        print(f"  No entries found for \"{lookup_word}\" in {source_lang} Wiktionary")

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

save_workbook()
for db in dbs.values():
    db.close()

print(f"\nSaved {added_count} new senses to {multi_senses_path}")
