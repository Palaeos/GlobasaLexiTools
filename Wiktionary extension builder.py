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

from Lexilista_parser import parseWordEntry, VerbType as _VT
from wiktionary_db import WiktionaryDB
from wiktionary_constants import (
    GLOSSPOS_TO_WIKT, EXTENSION_LANGS, DIALECT_LANGS, WIKTIONARY_SOURCES,
    lang_display_name, format_translation_word, _resolve_lang,
    build_annotation_map, entry_to_string,
)

_VT_NAMES = {
    _VT.INTRANSITIVE: "intransitive", _VT.TRANSITIVE: "transitive",
    _VT.ECHO_TRANSITIVE: "echo-transitive", _VT.COPULAR: "copular",
    _VT.AUXILIARY: "auxiliary", _VT.INTRANSITIVE_CU: "intransitive (-cu)",
    _VT.FEELING: "feeling (hisi)", _VT.STATE: "state (jotay)",
}

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
    vt_idx = col.get('VerbType')
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
        verb_type = row[vt_idx] if vt_idx is not None and vt_idx < len(row) else ''
        sense = row[sense_idx] if sense_idx < len(row) else ''
        source = row[source_idx] if source_idx is not None and source_idx < len(row) else 'en'

        if not glb or not lookup_word or not pos or not sense:
            continue

        senses.append({
            'glb': glb,
            'lookup_word': lookup_word,
            'pos': pos,
            'verb_type': verb_type,
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
            'wordclass': row.get('WordClass', '').strip(),
        }

# ---------------------------------------------------------------------------
# Build extension TSV
# ---------------------------------------------------------------------------

extension_lang_headers = [lang_display_name(c) for c in EXTENSION_LANGS]
ext_lang_idx = {code: i for i, code in enumerate(EXTENSION_LANGS)}

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

        # Determine PoS groups from word-list.csv English glosses
        # The wordlist defines the group structure (via WordClass → VerbType).
        # The xlsx VerbType column tells us which group each sense belongs to.
        eng_text = wl.get('eng', '')
        wordclass = wl.get('wordclass', '')
        parsed = parseWordEntry(eng_text, wordclass, {})
        eng_glosses = parsed.translations.get("Eng", [])

        group_key_to_idx = {}
        for g in eng_glosses:
            wikt_pos = GLOSSPOS_TO_WIKT.get(g.pos)
            vt_name = _VT_NAMES.get(g.verb_type, '') if g.verb_type else ''
            key = (wikt_pos, vt_name)
            if wikt_pos and key not in group_key_to_idx:
                group_key_to_idx[key] = len(group_key_to_idx)
        num_groups = max(len(group_key_to_idx), 1)

        # Accumulators: per-group sets for each language
        eng_sense_dict = {}
        output_glosses = [[set() for _ in range(num_groups)] for _ in EXTENSION_LANGS]

        for s in senses:
            source = s['source']
            db = dbs.get(source)
            if db is None:
                continue

            trans_entry = db.get_translations(s['lookup_word'], s['pos'])
            if trans_entry is None:
                continue

            if s['sense'] not in trans_entry:
                continue

            lang_translations = trans_entry[s['sense']]
            eng_sense_dict.setdefault(s['lookup_word'], set()).add(s['sense'])

            # Use xlsx VerbType to determine which transitivity group
            vt = s.get('verb_type', '')
            group_idx = group_key_to_idx.get((s['pos'], vt))
            if group_idx is None:
                # Fallback: first group matching this pos
                for (gp, gvt), gidx in group_key_to_idx.items():
                    if gp == s['pos']:
                        group_idx = gidx
                        break
            if group_idx is None:
                group_idx = 0

            for j, lang_code in enumerate(EXTENSION_LANGS):
                resolved, found = _resolve_lang(lang_code, lang_translations)
                if not found:
                    continue
                for t in resolved:
                    formatted = format_translation_word(t, s['pos'])
                    ann_key = DIALECT_LANGS[lang_code][0] if lang_code in DIALECT_LANGS else lang_code
                    ann = annotation_maps.get(ann_key, {}).get(t.word, "")
                    if ann:
                        formatted += f" (_{ann}_)"
                    output_glosses[j][group_idx].add(formatted)

            # For non-English sources, include the lookup word itself as a
            # translation for the source language (e.g. Lebewesen → German),
            # with gender tag if available from the entry's sense tags
            if s['source'] != 'en' and s['source'] in ext_lang_idx:
                j = ext_lang_idx[s['source']]
                pivot = s['lookup_word']
                if s['pos'] in ('noun', 'name'):
                    sense_list = db.get_senses(s['lookup_word'], s['pos']) or []
                    if sense_list:
                        stags = sense_list[0].tags
                        genders = []
                        if 'masculine' in stags:
                            genders.append('<m>')
                        if 'feminine' in stags:
                            genders.append('<f>')
                        if 'neuter' in stags:
                            genders.append('<n>')
                        if genders:
                            pivot += ' ' + '/'.join(genders)
                output_glosses[j][group_idx].add(pivot)

        # Build eng_sense_output
        eng_sense_output = ', '.join(
            word + " [" + "|".join(senses_set) + "]"
            for word, senses_set in eng_sense_dict.items()
        )

        ext_row = ([globasa_word, eng_sense_output]
                   + [entry_to_string(output_glosses[j])
                      for j in range(len(EXTENSION_LANGS))])
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
