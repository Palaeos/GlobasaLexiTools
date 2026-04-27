"""Parameterized JSONL parser for non-English Wiktionary dumps from kaikki.org.

Usage:
    python "JSONL parser non-English.py" fr
    python "JSONL parser non-English.py" de
    python "JSONL parser non-English.py" fr --discover

Downloads JSONL from kaikki.org if not found locally.
Writes translations + senses to WiktionaryLMDB_{lang}/.
"""

import csv
import gzip
import json
import os
import sys
from collections import Counter

from wiktionary_db import (WiktionaryDB, Translation, Example, Sense,
                            encode_key, serialize_translations,
                            serialize_senses)
from wiktionary_constants import WIKTIONARY_SOURCES

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
# Parse arguments
# ---------------------------------------------------------------------------

if len(sys.argv) < 2:
    print("Usage: python \"JSONL parser non-English.py\" <lang_code> [--discover]")
    print(f"Available: {', '.join(WIKTIONARY_SOURCES.keys())}")
    sys.exit(1)

lang_code = sys.argv[1]
discover_mode = '--discover' in sys.argv

if lang_code not in WIKTIONARY_SOURCES:
    print(f"Unknown language code '{lang_code}'. Available: {', '.join(WIKTIONARY_SOURCES.keys())}")
    sys.exit(1)

config = WIKTIONARY_SOURCES[lang_code]
native_lang_name = config['native_lang_name']
lmdb_dir = config['lmdb_dir']

# ---------------------------------------------------------------------------
# Locate JSONL file
# ---------------------------------------------------------------------------

JSONL_DIR = "/media/paleos/Warehouse2/Language"
jsonl_path = os.path.join(JSONL_DIR, f"raw-wiktextract-data-{lang_code}.jsonl")
jsonl_gz_path = jsonl_path + ".gz"

if not os.path.exists(jsonl_path):
    if os.path.exists(jsonl_gz_path):
        print(f"Decompressing {jsonl_gz_path}...")
        import shutil
        with gzip.open(jsonl_gz_path, 'rb') as f_in:
            with open(jsonl_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        print(f"Decompressed to {jsonl_path}")
    else:
        download_url = f"https://kaikki.org/{lang_code}wiktionary/raw-wiktextract-data.jsonl.gz"
        print(f"JSONL not found. Download it from:\n  {download_url}")
        print(f"Save as: {jsonl_gz_path}")
        ans = input("Download now? [y/N]: ").strip().lower()
        if ans == 'y':
            import wget
            os.makedirs(JSONL_DIR, exist_ok=True)
            print(f"Downloading {download_url}...")
            wget.download(download_url, jsonl_gz_path)
            print(f"\nDecompressing {jsonl_gz_path}...")
            import shutil
            with gzip.open(jsonl_gz_path, 'rb') as f_in:
                with open(jsonl_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            print(f"Decompressed to {jsonl_path}")
        else:
            sys.exit(1)

# ---------------------------------------------------------------------------
# Discover mode: print unique data['lang'] values
# ---------------------------------------------------------------------------

if discover_mode:
    print(f"\nScanning first 50000 lines of {jsonl_path} for language names...")
    lang_counts = Counter()
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 50000:
                break
            try:
                data = json.loads(line)
                lang = data.get('lang', '(missing)')
                lang_counts[lang] += 1
            except json.JSONDecodeError:
                pass

    print(f"\nTop 30 data['lang'] values:")
    for lang, count in lang_counts.most_common(30):
        marker = " <-- configured" if lang == native_lang_name else ""
        print(f"  {count:>6d}  {lang}{marker}")

    if native_lang_name not in lang_counts:
        print(f"\nWARNING: configured native_lang_name '{native_lang_name}' not found!")
        print(f"Update wiktionary_config.xlsx WiktionarySources sheet.")
    sys.exit(0)

# ---------------------------------------------------------------------------
# Parse JSONL
# ---------------------------------------------------------------------------

print(f"\nParsing {jsonl_path} for '{native_lang_name}' entries...")

translationDictionary = {}
senseDictionary = {}
line_count = 0
matched = 0

with open(jsonl_path, 'r', encoding='utf-8') as file:
    for line in file:
        line_count += 1
        if line_count % 500000 == 0:
            print(f"  {line_count} lines, {matched} {native_lang_name} entries...")
        try:
            data = json.loads(line)
            if 'word' not in data or 'lang' not in data:
                continue

            lang = data['lang']
            if lang != native_lang_name:
                continue

            matched += 1
            word = data['word']
            PoS = data['pos']

            # --- Senses extraction ---
            if 'senses' in data:
                if (word, PoS) not in senseDictionary:
                    senseDictionary[(word, PoS)] = []

                for sense_data in data['senses']:
                    glosses = tuple(sense_data.get('glosses', ()))
                    raw_glosses = tuple(sense_data.get('raw_glosses', ()))
                    tags = tuple(sense_data.get('tags', ()))
                    examples = tuple(
                        Example(
                            ex.get('text', ''),
                            ex.get('english', ''),
                            ex.get('type', '')
                        )
                        for ex in sense_data.get('examples', ())
                    )
                    senseDictionary[(word, PoS)].append(
                        Sense(glosses, raw_glosses, tags, examples)
                    )

            # --- Translations extraction ---
            if 'translations' in data:
                translations = data['translations']
                if (word, PoS) not in translationDictionary:
                    translationDictionary[(word, PoS)] = {}
                for translation in translations:
                    if 'word' not in translation or 'sense' not in translation or 'code' not in translation:
                        continue
                    sense_key = translation['sense']
                    lang_code_t = translation['code']
                    if sense_key not in translationDictionary[(word, PoS)]:
                        translationDictionary[(word, PoS)][sense_key] = {}
                    if lang_code_t not in translationDictionary[(word, PoS)][sense_key]:
                        translationDictionary[(word, PoS)][sense_key][lang_code_t] = set()
                    if 'tags' in translation:
                        rom = translation.get('romanization', '')
                        translationDictionary[(word, PoS)][sense_key][lang_code_t].add(
                            Translation(translation['word'], rom,
                                        "\t".join(translation['tags'])))
                    else:
                        translationDictionary[(word, PoS)][sense_key][lang_code_t].add(
                            Translation(translation['word'], "", ""))
        except json.JSONDecodeError as e:
            print(f"Error parsing line {line_count}: {e}")

print(f"\nParsed {line_count} lines, {matched} '{native_lang_name}' entries")
print(f"  {len(translationDictionary)} translation entries")
print(f"  {len(senseDictionary)} sense entries")

# ---------------------------------------------------------------------------
# Write to LMDB
# ---------------------------------------------------------------------------

print(f"\nWriting to {lmdb_dir}...")
os.makedirs(lmdb_dir, exist_ok=True)

with WiktionaryDB(path=lmdb_dir, readonly=False) as db:
    with db.env.begin(write=True) as txn:
        for (word, pos), trans_dict in translationDictionary.items():
            key = encode_key(word, pos)
            val = serialize_translations(trans_dict)
            txn.put(key, val, db=db.db_translations)

    with db.env.begin(write=True) as txn:
        for (word, pos), sense_list in senseDictionary.items():
            key = encode_key(word, pos)
            val = serialize_senses(sense_list)
            txn.put(key, val, db=db.db_senses)

print(f"Done. LMDB at {lmdb_dir}")
