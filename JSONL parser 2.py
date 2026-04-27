import csv
import json
import sys

from wiktionary_db import (WiktionaryDB, Translation, Example, Sense,
                            encode_key, serialize_translations,
                            serialize_senses, serialize_spanish_pos)

maxInt = sys.maxsize

while True:
    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt / 10)

PoSDict = {"n": ['noun'], "f": ['verb'], "f.sah": ['verb'], "b": ['noun', 'verb'], "t": ['adj', 'adv'],
           "s": ['adj'], "p jm": ['prep_phrase'], "jm": ['phrase'], "par": ['particle'],
           "m": ['adv'], "lfik": ['prefix'], "xfik": ['suffix'], "b xfik": ['suffix'], "t xfik": ['suffix'],
           "su n": ['name'], "su t": ['adj'], "il": ['intj'], "l": ['conj'],
           "num": ['num'], "p": ['prep'], "pn": ['pron'], "d": ['det']}


maximumLines = -1
file_path = "/media/paleos/Warehouse2/Language/raw-wiktextract-data.jsonl"

translationDictionary = {}
senseDictionary = {}
spanishPosDictionary = {}

with open(file_path, 'r', encoding='utf-8') as file:
    for line in file:
        if maximumLines > -1:
            maximumLines -= 1
            if maximumLines == 0:
                break
        try:
            data = json.loads(line)
            if 'word' not in data or 'lang' not in data:
                continue

            lang = data['lang']

            if lang == 'Spanish':
                spa_word = data['word']
                spa_pos = data['pos']
                if spa_word not in spanishPosDictionary:
                    spanishPosDictionary[spa_word] = set()
                spanishPosDictionary[spa_word].add(spa_pos)
                continue

            if lang != 'English':
                continue

            word = data['word']
            PoS = data['pos']

            # --- Senses extraction (definitions + examples) ---
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
                    if 'word' not in translation or 'sense' not in translation:
                        continue
                    lang_code_t = translation.get('code') or translation.get('lang_code')
                    if not lang_code_t:
                        continue
                    sense_key = translation['sense']
                    if sense_key not in translationDictionary[(word, PoS)]:
                        translationDictionary[(word, PoS)][sense_key] = {}
                    if lang_code_t not in translationDictionary[(word, PoS)][sense_key]:
                        translationDictionary[(word, PoS)][sense_key][lang_code_t] = set()
                    tags = translation.get('tags', [])
                    rom = translation.get('romanization', '') or translation.get('roman', '')
                    if tags:
                        translationDictionary[(word, PoS)][sense_key][lang_code_t].add(
                            Translation(translation['word'], rom, "\t".join(tags)))
                    else:
                        translationDictionary[(word, PoS)][sense_key][lang_code_t].add(
                            Translation(translation['word'], rom, ""))
        except json.JSONDecodeError as e:
            print(f"Error parsing line: {line}")
            print(e)

# --- Write to LMDB ---
print(f"Writing {len(translationDictionary)} translation entries, "
      f"{len(senseDictionary)} sense entries, "
      f"{len(spanishPosDictionary)} spanish_pos entries to LMDB...")

with WiktionaryDB(readonly=False) as db:
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

    with db.env.begin(write=True) as txn:
        for spa_word, pos_set in spanishPosDictionary.items():
            key = spa_word.encode('utf-8')
            val = serialize_spanish_pos(pos_set)
            txn.put(key, val, db=db.db_spanish_pos)

print("Done.")
