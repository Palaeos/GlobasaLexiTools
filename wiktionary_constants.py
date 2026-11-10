"""Shared constants and helpers for Wiktionary sense extender scripts.

Loads configurable constants from wiktionary_config.xlsx and provides
helper functions used by both the English extender and the multi-Wiktionary
curator/builder.
"""

import os
import csv
import re
import json

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

from Lexilista_parser import ParsedGloss, _expand_gloss_context

# ---------------------------------------------------------------------------
# Load configuration from wiktionary_config.xlsx
# ---------------------------------------------------------------------------

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "wiktionary_config.xlsx")


def _load_config():
    """Load all sheets from wiktionary_config.xlsx into Python structures."""
    wb = load_workbook(_CONFIG_PATH, read_only=True, data_only=True)

    # --- ExtensionLangs sheet ---
    ws = wb["ExtensionLangs"]
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    extension_langs = []
    senses_langs = []
    _display_names = {}   # code -> display_name (for non-ISO codes)
    for code, display_name, in_senses, in_extension in rows:
        if not code:
            continue
        code = str(code).strip()
        display_name = str(display_name).strip() if display_name else code
        if str(in_extension or '').strip().lower() == 'yes':
            extension_langs.append(code)
        if str(in_senses or '').strip().lower() == 'yes':
            senses_langs.append(code)
        _display_names[code] = display_name

    # --- Dialects sheet ---
    ws = wb["Dialects"]
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    dialect_langs = {}
    dialect_display_names = {}
    exclude_tags = set()
    in_exclude_section = False
    for row in rows:
        if row[0] and str(row[0]).strip() == 'exclude_tags':
            in_exclude_section = True
            continue
        if in_exclude_section:
            if row[0]:
                exclude_tags.add(str(row[0]).strip())
            continue
        code, parent, tag, display_name = (str(c).strip() if c else '' for c in row[:4])
        if code and parent and tag:
            dialect_langs[code] = (parent, tag)
            dialect_display_names[code] = display_name or code

    dialect_tags = frozenset(
        {tag for _, tag in dialect_langs.values()} | exclude_tags
    )

    # --- PoSMapping sheet ---
    ws = wb["PoSMapping"]
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    glosspos_to_wikt = {}
    for globasa_pos, wikt_pos in rows:
        if globasa_pos and wikt_pos:
            glosspos_to_wikt[str(globasa_pos).strip()] = str(wikt_pos).strip()

    # --- PoSFallbacks sheet ---
    ws = wb["PoSFallbacks"]
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    wikt_pos_fallbacks = {}
    wikt_pos_single_fallbacks = {}
    for wikt_pos, fallback, single_only in rows:
        if not wikt_pos or not fallback:
            continue
        wikt_pos = str(wikt_pos).strip()
        fallback = str(fallback).strip()
        if str(single_only or '').strip().lower() == 'yes':
            wikt_pos_single_fallbacks.setdefault(wikt_pos, []).append(fallback)
        else:
            wikt_pos_fallbacks.setdefault(wikt_pos, []).append(fallback)

    # --- WiktionarySources sheet ---
    ws = wb["WiktionarySources"]
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    wiktionary_sources = {}
    for row in rows:
        code, native_name, wl_col, lmdb_dir = (str(c).strip() if c else '' for c in row[:4])
        if code:
            wiktionary_sources[code] = {
                'native_lang_name': native_name,
                'wl_column': wl_col,
                'lmdb_dir': lmdb_dir,
            }

    wb.close()

    return {
        'extension_langs': extension_langs,
        'senses_langs': senses_langs,
        'display_names': _display_names,
        'dialect_langs': dialect_langs,
        'dialect_tags': dialect_tags,
        'dialect_display_names': dialect_display_names,
        'glosspos_to_wikt': glosspos_to_wikt,
        'wikt_pos_fallbacks': wikt_pos_fallbacks,
        'wikt_pos_single_fallbacks': wikt_pos_single_fallbacks,
        'wiktionary_sources': wiktionary_sources,
    }


_cfg = _load_config()

EXTENSION_LANGS = _cfg['extension_langs']
SENSES_LANGS = _cfg['senses_langs']
ANNOTATION_AID_LANGS = SENSES_LANGS  # alias
DIALECT_LANGS = _cfg['dialect_langs']
DIALECT_TAGS = _cfg['dialect_tags']
DIALECT_DISPLAY_NAMES = _cfg['dialect_display_names']
WIKT_POS_FALLBACKS = _cfg['wikt_pos_fallbacks']
WIKT_POS_SINGLE_FALLBACKS = _cfg['wikt_pos_single_fallbacks']
WIKTIONARY_SOURCES = _cfg['wiktionary_sources']

# GLOSSPOS_TO_WIKT needs GlossPoS enum values as keys, not strings.
# Convert from string names loaded from xlsx.
from Lexilista_parser import GlossPoS as _GlossPoS
GLOSSPOS_TO_WIKT = {}
for _name, _wikt in _cfg['glosspos_to_wikt'].items():
    _member = getattr(_GlossPoS, _name, None)
    if _member is not None:
        GLOSSPOS_TO_WIKT[_member] = _wikt

# Config display names (for dialects and xlsx-specified names)
_XLSX_DISPLAY_NAMES = _cfg['display_names']

# ---------------------------------------------------------------------------
# Load language name lookups (ISO 639-2/3)
# ---------------------------------------------------------------------------

_iso2_path = os.path.join(os.path.dirname(__file__), "language-codes ISO 639-2.json")
with open(_iso2_path, 'r', encoding='utf-8') as _f:
    _twoLetterCodes = json.load(_f)

_iso3_path = os.path.join(os.path.dirname(__file__), "iso-639-3.tab")
if not os.path.exists(_iso3_path):
    import wget
    print("Downloading the ISO-639-3 names for language codes")
    wget.download("https://iso639-3.sil.org/sites/iso639-3/files/downloads/iso-639-3.tab",
                  _iso3_path)

_languageNames = {}
with open(_iso3_path, 'r', newline='', encoding='utf-8') as _infile:
    _reader = csv.reader(_infile, delimiter='\t')
    next(_reader, None)
    for _row in _reader:
        _languageNames.setdefault(_row[0], _row[6])


def lang_display_name(code):
    """Get display name for a language code. Checks xlsx config, then ISO tables."""
    if code in _XLSX_DISPLAY_NAMES:
        return _XLSX_DISPLAY_NAMES[code]
    if code in DIALECT_DISPLAY_NAMES:
        return DIALECT_DISPLAY_NAMES[code]
    if code in _twoLetterCodes:
        return _twoLetterCodes[code]
    return _languageNames.get(code, code)


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


def build_annotation_map(text):
    """Build {stripped_word: annotation_text} from a word-list translation field.

    E.g. 'absurdidad (_dicho o hecho absurdo_), ridiculez'
      -> {'absurdidad': 'dicho o hecho absurdo'}
    """
    annotations = {}
    for part in re.split(r'[,;]', text):
        part = part.strip()
        if not part:
            continue
        stripped, annotation = extract_italic_annotation(part)
        if stripped and annotation:
            annotations[stripped] = annotation
    return annotations


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


def is_dialect(translation):
    """Return True if a Translation carries a known dialect tag."""
    if not translation.tags:
        return False
    return bool(DIALECT_TAGS & frozenset(translation.tags.split('\t')))


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


def _resolve_lang(lang_code, lang_translations):
    """Resolve a (possibly virtual dialect) lang code to filtered translations.

    For dialect codes (e.g. 'de-ale'): looks up parent in lang_translations,
    returns only translations carrying the required dialect tag.
    For standard codes: returns translations excluding all dialect tags.
    Returns (translations_list, found_bool)."""
    if lang_code in DIALECT_LANGS:
        parent, required_tag = DIALECT_LANGS[lang_code]
        if parent not in lang_translations:
            return [], False
        filtered = [t for t in lang_translations[parent]
                    if required_tag in (t.tags or '').split('\t')]
        return filtered, bool(filtered)
    else:
        if lang_code not in lang_translations:
            return [], False
        filtered = [t for t in lang_translations[lang_code] if not is_dialect(t)]
        return filtered, bool(filtered)


def get_sense_lang_translations(lang_translations, lang_code, wikt_pos):
    """Get formatted translation words for a language from a sense."""
    translations, found = _resolve_lang(lang_code, lang_translations)
    if not found:
        return ""
    return ", ".join(format_translation_word(t, wikt_pos) for t in translations)


def entry_to_string(entry):
    """Format a list of sets into 'a, b; c, d' (comma within group, semicolon between).
    Empty groups are preserved as empty strings to maintain positional alignment
    with PoS groups (e.g. [set(), {'verb'}] -> '; verb')."""
    # Strip trailing empty groups
    last_nonempty = -1
    for i, s in enumerate(entry):
        if s:
            last_nonempty = i
    if last_nonempty < 0:
        return ""
    # Sorted: sets have no stable order, and a rebuild must not reshuffle.
    parts = [", ".join(sorted(s)) if s else "" for s in entry[:last_nonempty + 1]]
    return "; ".join(parts)


# ---------------------------------------------------------------------------
# Marking loaders (for xlsx vetting data)
# ---------------------------------------------------------------------------

def _load_markings_from_rows(header, rows):
    """Build markings dict from header + iterable of row tuples/lists.
    Returns {(glb, eng, pos, verb_type, sense): (app, tier)} where tier is a
    single letter representing the highest vetting tier: 'e' > 'v' > 'l' > 'a'.
    Handles both new format (single 'Tier' column) and legacy format
    (separate Script?/LLM?/Vetted?/Expert? columns).
    For files without a VerbType column, verb_type defaults to ''."""
    markings = {}
    col = {name: i for i, name in enumerate(header)}
    eng_col = col.get('Eng', col.get('LookupWord', 1))
    pos_col = col.get('Prt of Sp', 2)
    vt_col = col.get('VerbType')
    sense_col = col.get('Wiktionary Sense (in Translations)',
                        col.get('Wiktionary Sense', 3))
    app_col = col.get('App?')
    tier_col = col.get('Tier')
    scr_col = col.get('Script?')
    llm_col = col.get('LLM?')
    vet_col = col.get('Vetted?')
    exp_col = col.get('Expert?')

    def _get(row, c):
        return (row[c] or '') if c is not None and c < len(row) else ''

    for row in rows:
        if len(row) <= sense_col:
            continue
        verb_type = _get(row, vt_col)
        key = (row[0] or '', row[eng_col] or '', row[pos_col] or '', verb_type, row[sense_col] or '')
        app = _get(row, app_col)

        if tier_col is not None:
            tier = _get(row, tier_col)
        else:
            expert = _get(row, exp_col)
            vetted = _get(row, vet_col)
            llm = _get(row, llm_col)
            script = _get(row, scr_col)
            tier = expert or vetted or llm or script

        if tier:
            markings[key] = (app, tier)
    return markings


def _load_markings_from_xlsx(path):
    """Load markings and column widths from an .xlsx file.
    Returns (markings, col_widths) or raises on corruption."""
    markings = {}
    col_widths = {}

    wb_in = load_workbook(path, read_only=True)
    ws_in = wb_in.active
    row_iter = ws_in.iter_rows(values_only=True)
    header = next(row_iter, None)
    if header:
        header = [str(h) if h is not None else '' for h in header]
        rows = ([str(c) if c is not None else '' for c in r] for r in row_iter)
        markings = _load_markings_from_rows(header, rows)
    wb_in.close()

    wb_dims = load_workbook(path, read_only=False, data_only=True)
    ws_dims = wb_dims.active
    dims_header = [str(c.value) if c.value is not None else ''
                   for c in next(ws_dims.iter_rows(min_row=1, max_row=1))]
    for i, name in enumerate(dims_header, 1):
        col_letter = get_column_letter(i)
        dim = ws_dims.column_dimensions.get(col_letter)
        if dim and dim.width:
            col_widths[name] = dim.width
    wb_dims.close()

    return markings, col_widths


def _find_latest_backup(prefix="GLB_ENG_WiktionarySenses_"):
    """Find the most recent .xlsx backup in ./backups/, or None."""
    backup_dir = "./backups"
    if not os.path.isdir(backup_dir):
        return None
    candidates = sorted(
        [f for f in os.listdir(backup_dir)
         if f.startswith(prefix) and f.endswith(".xlsx")],
        reverse=True)
    return os.path.join(backup_dir, candidates[0]) if candidates else None
