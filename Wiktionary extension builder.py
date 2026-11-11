"""Wiktionary extension builder — reads the vetting decisions,
fetches translations from LMDB, writes menalariExtension.tsv.

Reads:
  - vetted_senses.tsv  (the decisions; re-exported from the senses
    spreadsheets first when those are newer, see vetted_senses.py)
  - WiktionaryLMDB/  (English; or an extract made by wiktionary_extract.py:
    WiktionaryLMDB_senses/, every word-list gloss, or WiktionaryLMDB_vetted/,
    just the vetted entries)
  - WiktionaryLMDB_{lang}/  (non-English, per source)
  - word-list.csv  (for annotation overlays and word ordering)

Writes:
  - menalariExtension.tsv
"""

import os
import sys
import csv

from Lexilista_parser import parseWordEntry, VerbType as _VT
from wiktionary_db import WiktionaryDB
from wiktionary_extract import VETTED_LMDB, SENSES_LMDB
import vetted_senses
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
# Load vetted senses (vetted_senses.tsv; re-exported from the spreadsheets
# first if they are newer)
# ---------------------------------------------------------------------------

all_senses = vetted_senses.load_vetted()
print(f"  {sum(s['source'] == 'en' for s in all_senses)} vetted English senses, "
      f"{sum(s['source'] != 'en' for s in all_senses)} from other Wiktionaries")

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

# The full English database ("JSONL parser 2.py") when this machine has it;
# otherwise an extract (wiktionary_extract.py), which yields the same rows
# when both come from the same dump.
if os.path.exists("./WiktionaryLMDB"):
    dbs['en'] = WiktionaryDB(readonly=True)
    print("  Opened English LMDB")
elif os.path.exists(SENSES_LMDB):
    dbs['en'] = WiktionaryDB(path=SENSES_LMDB, readonly=True)
    print(f"  Opened English LMDB at {SENSES_LMDB} "
          f"(fallback: no full WiktionaryLMDB, extract of the word list's glosses)")
elif os.path.exists(VETTED_LMDB):
    dbs['en'] = WiktionaryDB(path=VETTED_LMDB, readonly=True)
    print(f"  Opened English LMDB at {VETTED_LMDB} "
          f"(fallback: no full WiktionaryLMDB, extract of the vetted entries)")
else:
    sys.exit("No English Wiktionary database: run wiktionary_extract.py first.")

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
    # Decisions the dump cannot serve: a different dump than the one vetted
    # against renames or drops senses. Reported, never silently lost.
    unmatched = defaultdict(list)

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
                unmatched['no database for this Wiktionary'].append(s)
                continue

            trans_entry = db.get_translations(s['lookup_word'], s['pos'])
            if trans_entry is None:
                unmatched['word/part of speech not in the dump'].append(s)
                continue

            if s['sense'] not in trans_entry:
                unmatched['sense not in the dump'].append(s)
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
            word + " [" + "|".join(sorted(senses_set)) + "]"
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
for reason, lst in unmatched.items():
    print(f"  {len(lst)} vetted senses skipped: {reason}, e.g. "
          + "; ".join(f"{s['glb']} / {s['lookup_word']} [{s['sense']}]" for s in lst[:3]))
