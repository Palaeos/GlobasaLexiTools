import os
import sys
import csv
import re
import json
import shutil
from datetime import datetime
from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter

from Lexilista_parser import parseWordEntry, GlossPoS, VerbType, _expand_gloss_context
from wiktionary_db import WiktionaryDB
import vetted_senses
from wiktionary_constants import (
    GLOSSPOS_TO_WIKT, WIKT_POS_FALLBACKS, WIKT_POS_SINGLE_FALLBACKS,
    SENSES_LANGS,
    lang_display_name, extract_italic_annotation,
    expand_comma_glosses, get_words_for_pos, get_sense_lang_translations,
    _load_markings_from_xlsx, _find_latest_backup,
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
# Verb type display names
# ---------------------------------------------------------------------------

_VERB_TYPE_NAMES = {
    VerbType.INTRANSITIVE: "intransitive",
    VerbType.TRANSITIVE: "transitive",
    VerbType.ECHO_TRANSITIVE: "echo-transitive",
    VerbType.COPULAR: "copular",
    VerbType.AUXILIARY: "auxiliary",
    VerbType.INTRANSITIVE_CU: "intransitive (-cu)",
    VerbType.FEELING: "feeling (hisi)",
    VerbType.STATE: "state (jotay)",
}


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
    """Extract definition and up to 3 examples from a matched Sense.
    Returns (definition, example1, example2, example3)."""
    if matched_sense is None:
        return ('', '', '', '')
    definition = matched_sense.glosses[-1] if matched_sense.glosses else ''
    examples = ['', '', '']
    for i, ex in enumerate(matched_sense.examples[:3]):
        examples[i] = ex.text
    return (definition, examples[0], examples[1], examples[2])


# ---------------------------------------------------------------------------
# English-specific helper functions
# ---------------------------------------------------------------------------


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
# Main loop
# ---------------------------------------------------------------------------

wb_out = Workbook()
ws_out = wb_out.active
ws_out.title = "Senses"

with open("./" + menalari_name, newline='', encoding='utf-8') as menalari_file:

    # Build headers
    senses_lang_headers = [lang_display_name(c) for c in SENSES_LANGS]

    senses_header = (['Glb', 'Tags', 'Antonyms', 'Eng', 'Clarification', 'Prt of Sp',
                       'VerbType',
                       'Wiktionary Sense (in Translations)',
                       'Definition', 'Example', 'Example 2', 'Example 3',
                       '|',
                       'App?', 'Tier', 'Spa', 'Epo']
                      + senses_lang_headers)
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

    menalariReader = csv.reader(menalari_file, delimiter=',', quotechar='"')
    wl_header = next(menalariReader, [])
    wl = {name: i for i, name in enumerate(wl_header)}

    started = False

    for row in menalariReader:
        if not started:
            if row[0].startswith(startPrefix):
                started = True
            else:
                continue

        def wl_get(col_name):
            idx = wl.get(col_name)
            return (row[idx].strip() if idx is not None and idx < len(row) else '')

        globasa_word = row[0]
        wordclass = wl_get('WordClass')
        eng_text = wl_get('TranslationEng')
        spa_text = wl_get('TranslationSpa')
        epo_text = wl_get('TranslationEpo')
        tags = wl_get('Tags')
        antonyms = wl_get('Antonyms')

        if not eng_text:
            ws_out.append([globasa_word, tags, antonyms])
            continue

        # Parse all three languages via Lexilista_parser
        parsed = parseWordEntry(eng_text, wordclass, {"Spa": spa_text, "Epo": epo_text})
        eng_glosses = parsed.translations.get("Eng", [])
        spa_glosses = expand_comma_glosses(parsed.translations.get("Spa", []))
        epo_glosses = expand_comma_glosses(parsed.translations.get("Epo", []))

        if not eng_glosses:
            ws_out.append([globasa_word, tags, antonyms])
            continue

        # Determine if single unique Wiktionary PoS (for extra fallbacks)
        unique_wikt_pos = {GLOSSPOS_TO_WIKT.get(g.pos) for g in eng_glosses} - {None}
        single_pos = len(unique_wikt_pos) == 1

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
                    vt = _VERB_TYPE_NAMES.get(eng_parsed.verb_type, '') if eng_parsed.verb_type else ''
                    ws_out.append([globasa_word, tags, antonyms, eng_word, clarification, wikt_pos, vt])
                    continue

                found_any = False
                for pos_key in pos_keys:
                    trans_entry = db.get_translations(eng_word, pos_key)
                    if trans_entry is None:
                        continue
                    found_any = True

                    sense_list = db.get_senses(eng_word, pos_key) or []

                    for sense, lang_translations in trans_entry.items():
                        # Match translation sense to definition
                        matched_sense = match_sense_to_definition(sense, sense_list)
                        definition, ex1, ex2, ex3 = extract_definition_and_examples(matched_sense)

                        # Cross-validation heuristic
                        heuristic_app, spa_col, epo_col = crossvalidate(
                            lang_translations, spa_words, epo_words)

                        # Inherit vetted markings from existing file.
                        # Try multiple key variants to handle annotation differences
                        # between v2 (raw, paren-stripped, paren-removed) and v3 (italic-stripped).
                        inherited_app, tier = '', ''
                        v2_reduced = re.sub(r'\(.*?\)', '', original_form).strip()
                        v2_unparened = original_form.replace("(", "").replace(")", "").strip()
                        vt_name = _VERB_TYPE_NAMES.get(eng_parsed.verb_type, '') if eng_parsed.verb_type else ''
                        for eng_key in dict.fromkeys([eng_word, original_form,
                                                      v2_reduced, v2_unparened]):
                            # Try with verb_type first, then without (legacy compat)
                            marking = existing_markings.get(
                                (globasa_word, eng_key, pos_key, vt_name, sense))
                            if not marking:
                                marking = existing_markings.get(
                                    (globasa_word, eng_key, pos_key, '', sense))
                            if marking:
                                inherited_app, tier = marking
                                break

                        # If any tier has reviewed this, inherit the vetted App? judgment;
                        # otherwise use the fresh heuristic result
                        if tier:
                            app = inherited_app
                        else:
                            app = heuristic_app

                        # Senses xlsx: per-sense language translations
                        sense_lang_cols = [
                            get_sense_lang_translations(lang_translations, lc, pos_key)
                            for lc in SENSES_LANGS
                        ]

                        verb_type_name = _VERB_TYPE_NAMES.get(eng_parsed.verb_type, '') if eng_parsed.verb_type else ''

                        sense_row = [globasa_word, tags, antonyms,
                                     eng_word, clarification,
                                     pos_key, verb_type_name, sense,
                                     definition, ex1, ex2, ex3,
                                     '|',
                                     app, tier, spa_col, epo_col
                                     ] + sense_lang_cols
                        ws_out.append(sense_row)
                        print("\t".join(sense_row))

                if not found_any:
                    vt = _VERB_TYPE_NAMES.get(eng_parsed.verb_type, '') if eng_parsed.verb_type else ''
                    ws_out.append([globasa_word, tags, antonyms, eng_word, clarification, wikt_pos, vt])

wb_out.save(outputPath)
db.close()
print(f"Saved senses to {outputPath}")
