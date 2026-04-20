import os
import pickle
import sys
import csv
import re
import json
from typing import NamedTuple
from collections import defaultdict

from Lexilista_parser import (parseWordEntry, GlossPoS, ParsedGloss,
                               ParsedWordEntry, _expand_gloss_context)


# Required for pickle deserialization of Wiktionary translation data
class Translation(NamedTuple):
    word: str
    romanization: str
    tags: str


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GLOSSPOS_TO_WIKT = {
    GlossPoS.NOUN: "noun",
    GlossPoS.PROPER_NOUN: "name",
    GlossPoS.VERB: "verb",
    GlossPoS.ADJECTIVE: "adj",
    GlossPoS.PROPER_ADJECTIVE: "adj",
    GlossPoS.VERBAL_ADVERB: "adv",
    GlossPoS.ADVERB: "adv",
    GlossPoS.PHRASAL_ADVERB: "adv",
    GlossPoS.INTERJECTION: "intj",
    GlossPoS.PRONOUN: "pron",
    GlossPoS.POSSESSIVE_PRONOUN: "pron",
    GlossPoS.NUMBER: "num",
    GlossPoS.PREPOSITION: "prep",
    GlossPoS.PHRASAL_PREPOSITION: "prep_phrase",
    GlossPoS.PREPOSITIONAL_PHRASE: "prep_phrase",
    GlossPoS.CONJUNCTION: "conj",
    GlossPoS.DETERMINER: "det",
    GlossPoS.PARTICLE: "particle",
    GlossPoS.PREFIX: "prefix",
    GlossPoS.POSSESSIVE_ADJECTIVE: "adj",
    GlossPoS.PHRASE: "phrase",
}

# Fallbacks always tried for a given Wiktionary PoS
WIKT_POS_FALLBACKS = {
    "noun": ["name"],
    "phrase": ["particle", "adv"],
    "verb particle": ["adv"],
}

# Extra fallbacks tried only when the word has a single unique Wiktionary PoS
WIKT_POS_SINGLE_FALLBACKS = {
    "noun": ["verb"],
    "adj": ["adv"],
}

# Validation languages: well-covered in word-list.csv, used for App? cross-validation
# Maps display name -> (Wiktionary lang code, word-list.csv column index)
VALIDATION_LANGS = {"Spa": ("es", 9), "Epo": ("eo", 8)}

# Annotation-aid languages: shown per-sense in senses TSV to help annotators
ANNOTATION_AID_LANGS = ['de', 'fr', 'ru', 'cmn']

# Extension languages: fetched from Wiktionary for menalariExtension.tsv
EXTENSION_LANGS = ['de', 'nl', 'ang', 'grc', 'la', 'fr', 'it', 'ru',
                   'yi', 'he', 'ar', 'cmn', 'ja', 'tr', 'tt']

# All languages appearing in the senses TSV (annotation-aid ∪ extension, order preserved)
SENSES_LANGS = []
_seen = set()
for lang in ANNOTATION_AID_LANGS + EXTENSION_LANGS:
    if lang not in _seen:
        SENSES_LANGS.append(lang)
        _seen.add(lang)

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
# Load language name lookups
# ---------------------------------------------------------------------------

with open("language-codes ISO 639-2.json", 'r', encoding='utf-8') as f:
    twoLetterCodes = json.load(f)

if not os.path.exists("./iso-639-3.tab"):
    import wget
    print("Downloading the ISO-639-3 names for language codes")
    wget.download("https://iso639-3.sil.org/sites/iso639-3/files/downloads/iso-639-3.tab",
                  'iso-639-3.tab')

languageNames = {}
with open("./iso-639-3.tab", 'r', newline='', encoding='utf-8') as infile:
    reader = csv.reader(infile, delimiter='\t')
    next(reader, None)
    for row in reader:
        languageNames.setdefault(row[0], row[6])


def lang_display_name(code):
    if code in twoLetterCodes:
        return twoLetterCodes[code]
    return languageNames.get(code, code)


# ---------------------------------------------------------------------------
# Preload existing vetted markings from GLB_ENG_WiktionarySenses.tsv
# ---------------------------------------------------------------------------

senseKeyPath = "./GLB_ENG_WiktionarySenses.tsv"
existing_markings = {}  # (glb, eng, pos, sense) -> (llm, vetted, expert)

if os.path.exists(senseKeyPath):
    with open(senseKeyPath, newline='', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t', quotechar='"')
        header = next(reader, None)

        # Detect old vs new column format
        if header and len(header) >= 6:
            if header[5] == "LLM?":
                # New format: App? | LLM? | Vetted? | Expert?
                llm_col, vet_col, exp_col = 5, 6, 7
            else:
                # Old format: App? | Vetted?
                llm_col, vet_col, exp_col = None, 5, None

            for row in reader:
                if len(row) < 4:
                    continue
                key = (row[0], row[1], row[2], row[3])
                llm = row[llm_col] if llm_col is not None and llm_col < len(row) else ''
                vetted = row[vet_col] if vet_col < len(row) else ''
                expert = row[exp_col] if exp_col is not None and exp_col < len(row) else ''
                # Only store if at least one vetting flag is set
                if llm or vetted or expert:
                    existing_markings[key] = (llm, vetted, expert)

    print(f"Loaded {len(existing_markings)} vetted markings from {senseKeyPath}")
else:
    print(f"No existing senses file found at {senseKeyPath}, starting fresh")

# ---------------------------------------------------------------------------
# Pickle cache
# ---------------------------------------------------------------------------

pickle_cache = {}


def load_pickle(english_word):
    """Load the pickled Wiktionary translation dict for a word's prefix."""
    if len(english_word) >= 2:
        prefix = english_word[:2].upper()
        if "/" in prefix or "\\" in prefix:
            prefix = "single_char"
    else:
        prefix = "single_char"

    if prefix in pickle_cache:
        return pickle_cache[prefix]

    path = f"./WiktionaryPickled/{prefix}.pkl"
    if not os.path.exists(path):
        pickle_cache[prefix] = {}
        return {}

    with open(path, 'rb') as f:
        data = pickle.load(f)
    pickle_cache[prefix] = data
    return data


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def expand_comma_glosses(glosses):
    """Split comma-separated glosses into individual ParsedGloss entries,
    then apply parenthetical expansion to each part."""
    expanded = []
    for g in glosses:
        parts = g.gloss.split(",")
        for part in parts:
            part = part.strip()
            if not part:
                continue
            variants = _expand_gloss_context(part)
            for v in variants:
                expanded.append(ParsedGloss(v, g.pos, g.verb_type, g.qualifier, g.affix_type))
    return expanded


def get_words_for_pos(glosses, target_pos):
    """Extract individual words from expanded glosses matching target PoS."""
    return {g.gloss.strip() for g in glosses if g.pos == target_pos}


def crossvalidate(lang_translations, spa_words, epo_words):
    """Cross-validate a Wiktionary sense against known Spa/Epo translations.

    Returns (app, spa_col, epo_col) where:
        app: 's' if cross-validation passes, '' otherwise
        spa_col: formatted string showing matched/unmatched Spanish words
        epo_col: formatted string showing matched/unmatched Esperanto words
    """
    spa_found = False
    spa_match = False
    epo_found = False
    epo_match = False
    spa_col = ""
    epo_col = ""

    if 'es' in lang_translations and spa_words:
        spa_found = True
        wikt_spa = {t.word for t in lang_translations['es']}
        matched = wikt_spa & spa_words
        unmatched = wikt_spa - spa_words
        spa_col = ", ".join(matched)
        if unmatched:
            spa_col += " /" + ", ".join(unmatched) + "/"
        if matched:
            spa_match = True

    if 'eo' in lang_translations and epo_words:
        epo_found = True
        wikt_epo = {t.word for t in lang_translations['eo']}
        matched = wikt_epo & epo_words
        unmatched = wikt_epo - epo_words
        epo_col = ", ".join(matched)
        if unmatched:
            epo_col += " /" + ", ".join(unmatched) + "/"
        if matched:
            epo_match = True

    # Match if at least one validation language has data AND all that have data match
    app_match = (((spa_match and spa_found) or not spa_found)
                 and ((epo_match and epo_found) or not epo_found)
                 and (spa_found or epo_found))

    return ('s' if app_match else '', spa_col, epo_col)


def format_translation_word(translation, wikt_pos):
    """Format a Translation with gender tags for nouns."""
    word = translation.word
    if wikt_pos in ('noun', 'name'):
        genders = []
        if 'masculine' in translation.tags:
            genders.append("<m>")
        if 'feminine' in translation.tags:
            genders.append("<f>")
        if 'neuter' in translation.tags:
            genders.append("<n>")
        if genders:
            word += " " + "/".join(genders)
    return word


def get_sense_lang_translations(lang_translations, lang_code, wikt_pos):
    """Get formatted translation words for a language from a sense."""
    if lang_code not in lang_translations:
        return ""
    words = [format_translation_word(t, wikt_pos) for t in lang_translations[lang_code]]
    return ", ".join(words)


def entry_to_string(entry):
    """Format a list of sets into 'a, b; c, d' (comma within group, semicolon between)."""
    parts = []
    for s in entry:
        if s:
            parts.append(", ".join(s))
    return "; ".join(parts)


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
# Main loop
# ---------------------------------------------------------------------------

with (open("./" + menalari_name, newline='', encoding='utf-8') as menalari_file,
      open('GLB_ENG_WiktionarySenses_initial.tsv', 'w', newline='', encoding='utf-8') as perSense,
      open('menalariExtension.tsv', 'w', newline='', encoding='utf-8') as menaExp):

    writer = csv.writer(perSense, delimiter='\t', lineterminator='\n')
    menaWriter = csv.writer(menaExp, delimiter='\t', lineterminator='\n')

    # Build headers
    senses_lang_headers = [lang_display_name(c) for c in SENSES_LANGS]
    extension_lang_headers = [lang_display_name(c) for c in EXTENSION_LANGS]

    writer.writerow(['Glb', 'Eng', 'Prt of Sp', 'Wiktionary Sense (in Translations)',
                      'App?', 'LLM?', 'Vetted?', 'Expert?', 'Spa', 'Epo']
                     + senses_lang_headers)
    menaWriter.writerow(['Globasa', 'Eng with Senses'] + extension_lang_headers)

    menalariReader = csv.reader(menalari_file, delimiter=',', quotechar='"')
    next(menalariReader, None)

    started = False

    for row in menalariReader:
        if not started:
            if row[0].startswith(startPrefix):
                started = True
            else:
                continue

        globasa_word = row[0]
        wordclass = row[3]
        eng_text = row[6].strip()
        spa_text = row[9].strip() if len(row) > 9 else ''
        epo_text = row[8].strip() if len(row) > 8 else ''
        tags = row[15] if len(row) > 15 else ''

        if not eng_text:
            menaWriter.writerow([globasa_word])
            writer.writerow([globasa_word])
            continue

        # Parse all three languages via Lexilista_parser
        parsed = parseWordEntry(eng_text, wordclass, {"Spa": spa_text, "Epo": epo_text})
        eng_glosses = parsed.translations.get("Eng", [])
        spa_glosses = expand_comma_glosses(parsed.translations.get("Spa", []))
        epo_glosses = expand_comma_glosses(parsed.translations.get("Epo", []))

        if not eng_glosses:
            menaWriter.writerow([globasa_word])
            writer.writerow([globasa_word])
            continue

        # Determine if single unique Wiktionary PoS (for extra fallbacks)
        unique_wikt_pos = {GLOSSPOS_TO_WIKT.get(g.pos) for g in eng_glosses} - {None}
        single_pos = len(unique_wikt_pos) == 1

        # Accumulators for extensions TSV
        eng_sense_dict = {}  # eng_word -> set of sense keys
        output_glosses = [[set() for _ in eng_glosses] for _ in EXTENSION_LANGS]

        for i, eng_parsed in enumerate(eng_glosses):
            wikt_pos = GLOSSPOS_TO_WIKT.get(eng_parsed.pos)
            if not wikt_pos:
                continue

            # PoS-aware validation word sets
            spa_words = get_words_for_pos(spa_glosses, eng_parsed.pos)
            epo_words = get_words_for_pos(epo_glosses, eng_parsed.pos)

            # Split commas and expand parentheticals for individual lookups
            lookup_words = []
            for part in eng_parsed.gloss.split(","):
                part = part.strip()
                if part:
                    lookup_words.extend(_expand_gloss_context(part))

            # Build list of (word, pos_key) pairs to try
            pos_keys = [wikt_pos] + WIKT_POS_FALLBACKS.get(wikt_pos, [])
            if single_pos:
                pos_keys += WIKT_POS_SINGLE_FALLBACKS.get(wikt_pos, [])

            for eng_word in lookup_words:
                if eng_word.startswith("_"):
                    writer.writerow([globasa_word, eng_word, wikt_pos])
                    continue

                pickle_data = load_pickle(eng_word)
                if not pickle_data:
                    writer.writerow([globasa_word, eng_word, wikt_pos])
                    continue

                found_any = False
                for pos_key in pos_keys:
                    if (eng_word, pos_key) not in pickle_data:
                        continue
                    found_any = True

                    for sense, lang_translations in pickle_data[(eng_word, pos_key)].items():
                        # Fresh cross-validation
                        app, spa_col, epo_col = crossvalidate(
                            lang_translations, spa_words, epo_words)

                        # Inherit LLM/Vetted/Expert from existing markings
                        llm, vetted, expert = existing_markings.get(
                            (globasa_word, eng_word, pos_key, sense), ('', '', ''))

                        # Senses TSV: per-sense language translations
                        sense_lang_cols = [
                            get_sense_lang_translations(lang_translations, lc, pos_key)
                            for lc in SENSES_LANGS
                        ]

                        sense_row = [globasa_word, eng_word, pos_key, sense,
                                     app, llm, vetted, expert, spa_col, epo_col
                                     ] + sense_lang_cols
                        writer.writerow(sense_row)
                        print("\t".join(sense_row))

                        # Collect for extensions TSV if vetted
                        if app == 's' and (expert == 'e' or vetted == 'v' or llm == 'l'):
                            eng_sense_dict.setdefault(eng_word, set()).add(sense)
                            for j, lang_code in enumerate(EXTENSION_LANGS):
                                if lang_code in lang_translations:
                                    for t in lang_translations[lang_code]:
                                        output_glosses[j][i].add(
                                            format_translation_word(t, pos_key))

                if not found_any:
                    writer.writerow([globasa_word, eng_word, wikt_pos])

        # Write extensions TSV row
        eng_sense_output = ', '.join(
            word + " [" + "|".join(senses) + "]"
            for word, senses in eng_sense_dict.items()
        )
        ext_row = ([globasa_word, eng_sense_output]
                   + [entry_to_string(output_glosses[j]) for j in range(len(EXTENSION_LANGS))])
        menaWriter.writerow(ext_row)
