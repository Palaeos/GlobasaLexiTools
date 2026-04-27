"""Wiktionary extension builder — reads vetted senses from xlsx files,
fetches translations from LMDB, writes menalariExtension.tsv.

Reads:
  - GLB_ENG_WiktionarySenses.xlsx  (English Wiktionary senses)
  - GLB_MULTI_WiktionarySenses.xlsx  (non-English curated senses, optional)
  - WiktionaryLMDB/  (English)
  - WiktionaryLMDB_{lang}/  (non-English, per source)
  - word-list.csv  (for annotation overlays and word ordering)

Writes:
  - menalariExtension.tsv
"""

import os
import sys
import csv
import json

from openpyxl import load_workbook

from wiktionary_db import WiktionaryDB
from wiktionary_constants import (
    EXTENSION_LANGS, DIALECT_LANGS, WIKTIONARY_SOURCES,
    lang_display_name, format_translation_word, _resolve_lang,
    build_annotation_map, entry_to_string,
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
# Configurable paths
# ---------------------------------------------------------------------------

ENG_SENSES_FILENAME = "GLB_ENG_WiktionarySenses.xlsx"
MULTI_SENSES_FILENAME = "GLB_MULTI_WiktionarySenses.xlsx"
CONFIG_FILE = ".senses_config.json"

default_dir = "./"
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        default_dir = json.load(f).get("senses_dir", default_dir)

senses_dir = input(
    f"Directory for senses xlsx files [{default_dir}]:\n"
).strip() or default_dir

eng_senses_path = os.path.join(senses_dir, ENG_SENSES_FILENAME)
multi_senses_path = os.path.join(senses_dir, MULTI_SENSES_FILENAME)

# ---------------------------------------------------------------------------
# Load vetted senses from xlsx
# ---------------------------------------------------------------------------


def load_vetted_senses(xlsx_path, source_type):
    """Load vetted senses from an xlsx file.

    Returns list of dicts:
      {glb, lookup_word, pos, sense, source, source_type}

    source_type: 'eng' or 'multi'
    For 'eng': source='en', lookup_word from 'Eng' column
    For 'multi': source from 'Source' column, lookup_word from 'LookupWord' column
    """
    if not os.path.exists(xlsx_path):
        return []

    wb = load_workbook(xlsx_path, read_only=True)
    ws = wb.active
    row_iter = ws.iter_rows(values_only=True)
    header = next(row_iter, None)
    if not header:
        wb.close()
        return []

    header = [str(h) if h is not None else '' for h in header]
    col = {name: i for i, name in enumerate(header)}

    app_idx = col.get('App?')
    tier_idx = col.get('Tier')

    if source_type == 'eng':
        word_idx = col.get('Eng', 1)
        source_idx = None
    else:
        word_idx = col.get('LookupWord', col.get('Eng', 1))
        source_idx = col.get('Source')

    pos_idx = col.get('Prt of Sp', 2)
    sense_idx = col.get('Wiktionary Sense (in Translations)',
                        col.get('Wiktionary Sense', 3))

    senses = []
    for row in row_iter:
        row = [str(c) if c is not None else '' for c in row]
        if len(row) <= max(x for x in [app_idx, tier_idx, word_idx, pos_idx, sense_idx] if x is not None):
            continue

        app = row[app_idx] if app_idx is not None else ''
        tier = row[tier_idx] if tier_idx is not None else ''

        if app != 's' or tier not in ('v', 'e'):
            continue

        glb = row[0]
        lookup_word = row[word_idx] if word_idx < len(row) else ''
        pos = row[pos_idx] if pos_idx < len(row) else ''
        sense = row[sense_idx] if sense_idx < len(row) else ''
        source = row[source_idx] if source_idx is not None and source_idx < len(row) else 'en'

        if not glb or not lookup_word or not pos or not sense:
            continue

        senses.append({
            'glb': glb,
            'lookup_word': lookup_word,
            'pos': pos,
            'sense': sense,
            'source': source,
        })

    wb.close()
    return senses


print(f"Loading English senses from {eng_senses_path}...")
eng_senses = load_vetted_senses(eng_senses_path, 'eng')
print(f"  {len(eng_senses)} vetted English senses")

multi_senses = []
if os.path.exists(multi_senses_path):
    print(f"Loading multi-source senses from {multi_senses_path}...")
    multi_senses = load_vetted_senses(multi_senses_path, 'multi')
    print(f"  {len(multi_senses)} vetted multi-source senses")

all_senses = eng_senses + multi_senses

# ---------------------------------------------------------------------------
# Group senses by Globasa word
# ---------------------------------------------------------------------------

from collections import defaultdict

word_senses = defaultdict(list)
for s in all_senses:
    word_senses[s['glb']].append(s)

# ---------------------------------------------------------------------------
# Open LMDB databases
# ---------------------------------------------------------------------------

dbs = {}

if eng_senses:
    dbs['en'] = WiktionaryDB(readonly=True)
    print(f"  Opened English LMDB")

for source_code, config in WIKTIONARY_SOURCES.items():
    lmdb_dir = config['lmdb_dir']
    if os.path.exists(lmdb_dir):
        dbs[source_code] = WiktionaryDB(path=lmdb_dir, readonly=True)
        print(f"  Opened {source_code} LMDB at {lmdb_dir}")

# ---------------------------------------------------------------------------
# Load word-list.csv for annotation overlays and word ordering
# ---------------------------------------------------------------------------

menalari_name = "word-list.csv"
if not os.path.exists("./" + menalari_name):
    import wget
    print("Downloading the Globasa word-list")
    wget.download("https://cdn.globasa.net/api2/word-list.csv", menalari_name)

wordlist_order = []  # ordered list of all Globasa words
wordlist_data = {}   # glb -> {eng_text, spa_text, epo_text}

with open("./" + menalari_name, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        word = row['Word']
        wordlist_order.append(word)
        wordlist_data[word] = {
            'eng': row.get('TranslationEng', '').strip(),
            'spa': row.get('TranslationSpa', '').strip(),
            'epo': row.get('TranslationEpo', '').strip(),
        }

# ---------------------------------------------------------------------------
# Build extension TSV
# ---------------------------------------------------------------------------

extension_lang_headers = [lang_display_name(c) for c in EXTENSION_LANGS]

with open('menalariExtension.tsv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f, delimiter='\t', lineterminator='\n')
    writer.writerow(['Globasa', 'Eng with Senses'] + extension_lang_headers)

    words_with_data = 0

    for globasa_word in wordlist_order:
        senses = word_senses.get(globasa_word, [])

        if not senses:
            writer.writerow([globasa_word])
            continue

        # Build annotation maps from word-list.csv
        wl = wordlist_data.get(globasa_word, {})
        annotation_maps = {}
        if wl.get('spa'):
            annotation_maps['es'] = build_annotation_map(wl['spa'])
        if wl.get('epo'):
            annotation_maps['eo'] = build_annotation_map(wl['epo'])

        # Accumulators
        eng_sense_dict = {}  # lookup_word -> set of sense keys
        # For each EXTENSION_LANG, collect translation words across all senses
        lang_translations_all = {lc: set() for lc in EXTENSION_LANGS}

        for s in senses:
            source = s['source']
            db = dbs.get(source)
            if db is None:
                continue

            trans_entry = db.get_translations(s['lookup_word'], s['pos'])
            if trans_entry is None:
                continue

            # Find the matching sense in the translations dict
            if s['sense'] not in trans_entry:
                continue

            lang_translations = trans_entry[s['sense']]
            eng_sense_dict.setdefault(s['lookup_word'], set()).add(s['sense'])

            for lang_code in EXTENSION_LANGS:
                resolved, found = _resolve_lang(lang_code, lang_translations)
                if not found:
                    continue
                for t in resolved:
                    formatted = format_translation_word(t, s['pos'])
                    ann_key = DIALECT_LANGS[lang_code][0] if lang_code in DIALECT_LANGS else lang_code
                    ann = annotation_maps.get(ann_key, {}).get(t.word, "")
                    if ann:
                        formatted += f" (_{ann}_)"
                    lang_translations_all[lang_code].add(formatted)

        # Build eng_sense_output
        eng_sense_output = ', '.join(
            word + " [" + "|".join(senses_set) + "]"
            for word, senses_set in eng_sense_dict.items()
        )

        ext_row = ([globasa_word, eng_sense_output]
                   + [", ".join(sorted(lang_translations_all[lc]))
                      for lc in EXTENSION_LANGS])
        writer.writerow(ext_row)

        if eng_sense_output:
            words_with_data += 1

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

for db in dbs.values():
    db.close()

print(f"\nWrote menalariExtension.tsv: {words_with_data} words with translations, "
      f"{len(wordlist_order)} total rows")
