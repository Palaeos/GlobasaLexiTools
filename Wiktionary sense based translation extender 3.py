import os
import pickle
import sys
import csv
import re
import json
import shutil
from datetime import datetime
from typing import NamedTuple
from collections import defaultdict

from Lexilista_parser import (parseWordEntry, GlossPoS, ParsedGloss,
                               ParsedWordEntry, _expand_gloss_context)


# Required for pickle deserialization of Wiktionary translation data
class Translation(NamedTuple):
    word: str
    romanization: str
    tags: str


# Required for pickle deserialization of Wiktionary sense data
class Example(NamedTuple):
    text: str
    english: str
    type: str


class Sense(NamedTuple):
    glosses: tuple
    raw_glosses: tuple
    tags: tuple
    examples: tuple


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
    "name": ["noun"],
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
existing_markings = {}  # (glb, eng, pos, sense) -> (app, llm, vetted, expert)

if os.path.exists(senseKeyPath):
    with open(senseKeyPath, newline='', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t', quotechar='"')
        header = next(reader, None)

        # Build column index map from header names
        if header:
            col = {name: i for i, name in enumerate(header)}
            eng_col = col.get('Eng', 1)
            pos_col = col.get('Prt of Sp', 2)
            sense_col = col.get('Wiktionary Sense (in Translations)', 3)
            app_col = col.get('App?')
            llm_col = col.get('LLM?')
            vet_col = col.get('Vetted?')
            exp_col = col.get('Expert?')

            for row in reader:
                if len(row) <= sense_col:
                    continue
                key = (row[0], row[eng_col], row[pos_col], row[sense_col])
                app = row[app_col] if app_col is not None and app_col < len(row) else ''
                llm = row[llm_col] if llm_col is not None and llm_col < len(row) else ''
                vetted = row[vet_col] if vet_col is not None and vet_col < len(row) else ''
                expert = row[exp_col] if exp_col is not None and exp_col < len(row) else ''
                if llm or vetted or expert:
                    existing_markings[key] = (app, llm, vetted, expert)

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


sense_pickle_cache = {}


def load_sense_pickle(english_word):
    """Load the pickled Wiktionary sense dict for a word's prefix."""
    if len(english_word) >= 2:
        prefix = english_word[:2].upper()
        if "/" in prefix or "\\" in prefix:
            prefix = "single_char"
    else:
        prefix = "single_char"

    if prefix in sense_pickle_cache:
        return sense_pickle_cache[prefix]

    path = f"./WiktionaryPickled/senses/{prefix}.pkl"
    if not os.path.exists(path):
        sense_pickle_cache[prefix] = {}
        return {}

    with open(path, 'rb') as f:
        data = pickle.load(f)
    sense_pickle_cache[prefix] = data
    return data


# ---------------------------------------------------------------------------
# Sense matching
# ---------------------------------------------------------------------------

_STOPWORDS = frozenset(
    'a an the of or and in for to is are was were be been being '
    'by with at on from as it its that this which who whom whose'.split()
)


def _content_words(text):
    """Extract lowercased content words, stripping possessives and stopwords."""
    words = set()
    for w in re.findall(r"[a-zA-Z']+", text.lower()):
        w = w.rstrip("'s") if w.endswith("'s") else w
        if w and w not in _STOPWORDS:
            words.add(w)
    return words


def match_sense_to_definition(sense_key, sense_list):
    """Match a translation sense key to a Sense object from the definitions.

    3-tier strategy:
      Tier 1: sense_key is a substring of a gloss (case-insensitive)
      Tier 2: sense_key is a substring of a raw_gloss
      Tier 3: content-word overlap scoring (threshold >= 0.5)
    """
    sk_lower = sense_key.lower().strip()
    if not sk_lower:
        return None

    # Also try the part after a colon (e.g. "gambling: banker's funds" -> "banker's funds")
    sk_after_colon = sk_lower.split(":", 1)[1].strip() if ":" in sk_lower else ""

    # Tier 1: substring match against glosses
    for sense in sense_list:
        for gloss in sense.glosses:
            gl = gloss.lower()
            if sk_lower in gl or (sk_after_colon and sk_after_colon in gl):
                return sense

    # Tier 2: substring match against raw_glosses
    for sense in sense_list:
        for raw in sense.raw_glosses:
            rl = raw.lower()
            if sk_lower in rl or (sk_after_colon and sk_after_colon in rl):
                return sense

    # Tier 3: content-word overlap
    sk_words = _content_words(sense_key)
    if not sk_words:
        return None

    best_sense = None
    best_score = 0.0
    for sense in sense_list:
        for gloss in sense.glosses:
            gloss_words = _content_words(gloss)
            overlap = sk_words & gloss_words
            score = len(overlap) / len(sk_words)
            if score > best_score:
                best_score = score
                best_sense = sense

    return best_sense if best_score >= 0.5 else None


def extract_definition_and_examples(matched_sense):
    """Extract definition and example from a matched Sense.
    Returns (definition, example_text)."""
    if matched_sense is None:
        return ('', '')
    definition = matched_sense.glosses[-1] if matched_sense.glosses else ''
    example_text = ''
    if matched_sense.examples:
        example_text = matched_sense.examples[0].text
    return (definition, example_text)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

_ITALIC_ANNOTATION_RE = re.compile(r'\(_([^_]*)_\)')


def extract_italic_annotation(text):
    """Extract and strip markdown italic annotations like '(_bird_)' from a gloss.
    Returns (stripped_text, clarification)."""
    matches = _ITALIC_ANNOTATION_RE.findall(text)
    stripped = _ITALIC_ANNOTATION_RE.sub('', text).strip()
    clarification = ", ".join(matches) if matches else ""
    return stripped, clarification


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
# Determine output path: full run overwrites senses file (with backup),
# filtered run writes to a separate file.
# ---------------------------------------------------------------------------

if startPrefix:
    outputPath = 'GLB_ENG_WiktionarySenses_initial.tsv'
else:
    outputPath = senseKeyPath
    if os.path.exists(senseKeyPath):
        backup_dir = "./backups"
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"GLB_ENG_WiktionarySenses_{timestamp}.tsv"
        backup_path = os.path.join(backup_dir, backup_name)
        shutil.copy2(senseKeyPath, backup_path)
        print(f"Backed up {senseKeyPath} to {backup_path}")

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

with (open("./" + menalari_name, newline='', encoding='utf-8') as menalari_file,
      open(outputPath, 'w', newline='', encoding='utf-8') as perSense,
      open('menalariExtension.tsv', 'w', newline='', encoding='utf-8') as menaExp):

    writer = csv.writer(perSense, delimiter='\t', lineterminator='\n')
    menaWriter = csv.writer(menaExp, delimiter='\t', lineterminator='\n')

    # Build headers
    senses_lang_headers = [lang_display_name(c) for c in SENSES_LANGS]
    extension_lang_headers = [lang_display_name(c) for c in EXTENSION_LANGS]

    writer.writerow(['Glb', 'Eng', 'Clarification', 'Prt of Sp',
                      'Wiktionary Sense (in Translations)',
                      'Definition', 'Example',
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

            # Split commas, extract italic annotations, expand parentheticals
            # Each entry is (lookup_word, clarification, original_form)
            lookup_entries = []
            for part in eng_parsed.gloss.split(","):
                part = part.strip()
                if not part:
                    continue
                stripped, clarification = extract_italic_annotation(part)
                if stripped:
                    for v in _expand_gloss_context(stripped):
                        lookup_entries.append((v, clarification, part))

            # Build list of (word, pos_key) pairs to try
            pos_keys = [wikt_pos] + WIKT_POS_FALLBACKS.get(wikt_pos, [])
            if single_pos:
                pos_keys += WIKT_POS_SINGLE_FALLBACKS.get(wikt_pos, [])

            for eng_word, clarification, original_form in lookup_entries:
                if eng_word.startswith("_"):
                    writer.writerow([globasa_word, eng_word, clarification, wikt_pos])
                    continue

                pickle_data = load_pickle(eng_word)
                sense_data = load_sense_pickle(eng_word)
                if not pickle_data:
                    writer.writerow([globasa_word, eng_word, clarification, wikt_pos])
                    continue

                found_any = False
                for pos_key in pos_keys:
                    if (eng_word, pos_key) not in pickle_data:
                        continue
                    found_any = True

                    sense_list = sense_data.get((eng_word, pos_key), [])

                    for sense, lang_translations in pickle_data[(eng_word, pos_key)].items():
                        # Match translation sense to definition
                        matched_sense = match_sense_to_definition(sense, sense_list)
                        definition, example_text = extract_definition_and_examples(matched_sense)

                        # Cross-validation heuristic
                        heuristic_app, spa_col, epo_col = crossvalidate(
                            lang_translations, spa_words, epo_words)

                        # Inherit vetted markings from existing TSV.
                        # Try multiple key variants to handle annotation differences
                        # between v2 (raw, paren-stripped, paren-removed) and v3 (italic-stripped).
                        inherited_app, llm, vetted, expert = ('', '', '', '')
                        v2_reduced = re.sub(r'\(.*?\)', '', original_form).strip()
                        v2_unparened = original_form.replace("(", "").replace(")", "").strip()
                        for eng_key in dict.fromkeys([eng_word, original_form,
                                                      v2_reduced, v2_unparened]):
                            marking = existing_markings.get(
                                (globasa_word, eng_key, pos_key, sense))
                            if marking:
                                inherited_app, llm, vetted, expert = marking
                                break

                        # If any vetting column is marked, inherit the vetted App? judgment;
                        # otherwise use the fresh heuristic result
                        if llm or vetted or expert:
                            app = inherited_app
                        else:
                            app = heuristic_app

                        # Senses TSV: per-sense language translations
                        sense_lang_cols = [
                            get_sense_lang_translations(lang_translations, lc, pos_key)
                            for lc in SENSES_LANGS
                        ]

                        sense_row = [globasa_word, eng_word, clarification,
                                     pos_key, sense,
                                     definition, example_text,
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
                    writer.writerow([globasa_word, eng_word, clarification, wikt_pos])

        # Write extensions TSV row
        eng_sense_output = ', '.join(
            word + " [" + "|".join(senses) + "]"
            for word, senses in eng_sense_dict.items()
        )
        ext_row = ([globasa_word, eng_sense_output]
                   + [entry_to_string(output_glosses[j]) for j in range(len(EXTENSION_LANGS))])
        menaWriter.writerow(ext_row)
