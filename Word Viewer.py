"""Word Viewer — Flask-based local dictionary for Globasa.

Builds an LMDB cache from source files, then serves a JSON lookup API
and a single-page HTML frontend.

Run:
    python "Word Viewer.py"
Then open http://localhost:5000
"""

import os
import re
import csv
import xml.etree.ElementTree as ET
import lmdb
import msgpack
import pandas as pd
from flask import Flask, jsonify, send_file, abort, request

from Lexilista_parser import parseWordEntry, GlossPoS, VerbType

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LMDB_DIR = os.path.join(BASE_DIR, "WordViewerLMDB")
AUDIO_DIR = "/media/paleos/Warehouse2/Applications/Segmentation/Ektor_su_Lafuzu_processed"
WORDLIST_CSV = os.path.join(BASE_DIR, "word-list.csv")
EXTENSION_TSV = os.path.join(BASE_DIR, "menalariExtension.tsv")
PRONOUNS_TSV = os.path.join(BASE_DIR, "menalariPronouns_edited.tsv")
IMAGES_TSV = os.path.join(BASE_DIR, "menalariImages_edited.csv")
SOTI_TSV = os.path.join(BASE_DIR, "Soti.tsv")
GRAPHIC_BLACKLIST = os.path.join(BASE_DIR, "graphic_blacklist")
CONSTRUCTIONS_XLSX = os.path.join(BASE_DIR, "Constructions.xlsx")
TMX_FILE = os.path.join(BASE_DIR, "Doxo_passages.tmx")
GIZA_DIR = os.path.join(BASE_DIR, "giza_output")
HTML_FILE = os.path.join(BASE_DIR, "word_viewer.html")

MAP_SIZE = 512 * 1024 * 1024  # 512 MB

# ---------------------------------------------------------------------------
# Gender marker regex
# ---------------------------------------------------------------------------

GENDER_RE = re.compile(r"\s*<([mfn])>")


def _strip_gender(text):
    """Remove all gender markers from text."""
    return GENDER_RE.sub("", text).strip()


def parse_extension_cell(cell_text):
    """Parse an extension TSV cell into a list of {text, gender} dicts.

    Semicolons separate PoS groups. Within each group, commas separate
    individual words/phrases. Each word may have a trailing <m>/<f>/<n> marker.

    Returns list of dicts: {text: str, gender: 'm'|'f'|'n'|None}
    """
    if not cell_text or cell_text == "False":
        return []

    groups = cell_text.split("; ")
    result = []
    for group in groups:
        items = group.split(", ")
        for item in items:
            item = item.strip()
            if not item:
                continue
            m = GENDER_RE.search(item)
            gender = m.group(1) if m else None
            text = _strip_gender(item)
            if text:
                result.append({"text": text, "gender": gender})
    return result


def parse_extension_cell_grouped(cell_text):
    """Parse extension cell -> list-of-lists grouped by PoS semicolon separators.

    Returns list of PoS groups, each group is a list of {text, gender}.
    """
    if not cell_text or cell_text == "False":
        return []

    groups = cell_text.split("; ")
    result = []
    for group in groups:
        group_items = []
        items = group.split(", ")
        for item in items:
            item = item.strip()
            if not item:
                continue
            m = GENDER_RE.search(item)
            gender = m.group(1) if m else None
            text = _strip_gender(item)
            if text:
                group_items.append({"text": text, "gender": gender})
        result.append(group_items)
    return result


# ---------------------------------------------------------------------------
# WordViewerDB class
# ---------------------------------------------------------------------------

DB_NAMES = [b"wordlist", b"extensions", b"pronouns", b"tmx",
            b"images", b"sound_effects", b"nsfw", b"constructions"]


class WordViewerDB:
    def __init__(self, path=LMDB_DIR, readonly=True):
        self.env = lmdb.open(
            path,
            map_size=MAP_SIZE,
            max_dbs=len(DB_NAMES),
            readonly=readonly,
            readahead=True,
            lock=not readonly,
        )
        self.dbs = {name: self.env.open_db(name) for name in DB_NAMES}
        self._readonly = readonly

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self.env.close()

    def _db(self, db_name):
        """Resolve db handle from string or bytes name."""
        if isinstance(db_name, str):
            return self.dbs[db_name.encode("utf-8")]
        return self.dbs[db_name]

    def _get(self, db_name, key_str):
        key = key_str.encode("utf-8")
        with self.env.begin(db=self._db(db_name)) as txn:
            val = txn.get(key)
            if val is None:
                return None
            return msgpack.unpackb(bytes(val), raw=False)

    def _put(self, db_name, key_str, obj, txn):
        key = key_str.encode("utf-8")
        val = msgpack.packb(obj, use_bin_type=True)
        txn.put(key, val, db=self._db(db_name))

    def _has(self, db_name, key_str):
        key = key_str.encode("utf-8")
        with self.env.begin(db=self._db(db_name)) as txn:
            return txn.get(key) is not None

    def get_wordlist(self, word):
        return self._get("wordlist", word)

    def get_extensions(self, word):
        return self._get("extensions", word)

    def get_pronoun(self, word):
        return self._get("pronouns", word)

    def get_tmx(self, word):
        return self._get("tmx", word)

    def get_image(self, word):
        return self._get("images", word)

    def get_sound_effect(self, word):
        return self._get("sound_effects", word)

    def is_nsfw(self, word):
        return self._has("nsfw", word)

    def get_constructions(self, word):
        return self._get("constructions", word)

    def get_all_words(self):
        """Return list of all words in the wordlist db."""
        words = []
        with self.env.begin(db=self._db("wordlist")) as txn:
            cursor = txn.cursor()
            for key, _ in cursor.iternext():
                words.append(key.decode("utf-8"))
        return words

    def begin_write(self):
        return self.env.begin(write=True)


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# GIZA++ alignment parser
# ---------------------------------------------------------------------------

def _giza_tokenize(text):
    """Match run_giza.py tokenization."""
    text = text.lower()
    text = re.sub(r'([.,:;!?"""()\'—\-])', r' \1 ', text)
    return text.split()


def parse_giza_a3(a3_path):
    """Parse a GIZA++ A3.final file.

    Returns a dict keyed by normalized (lowercased, tokenized) Globasa segment
    -> dict mapping Globasa token -> set of 0-indexed target token positions.
    """
    alignments = {}  # glb_seg_key -> {glb_word: {target_positions}}
    try:
        with open(a3_path, encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return alignments

    # Every 3 lines: comment, target sentence, source (Globasa) with alignment
    i = 0
    while i + 2 < len(lines):
        # line i: # Sentence pair (N) ...
        # line i+1: target sentence (e.g. English)
        target_line = lines[i + 1].strip()
        target_tokens = target_line.split()
        # line i+2: Globasa tokens with alignments: NULL ({ }) word1 ({ 1 3 }) word2 ({ 2 }) ...
        align_line = lines[i + 2].strip()

        # Parse: each "word ({ idx idx ... })" block
        glb_tokens = []
        word_aligns = {}
        for m in re.finditer(r'(\S+)\s+\(\{\s*((?:\d+\s*)*)\}\)', align_line):
            glb_word = m.group(1)
            indices_str = m.group(2).strip()
            if glb_word == "NULL":
                pass  # skip NULL alignments
            else:
                glb_tokens.append(glb_word)
                if indices_str:
                    # GIZA uses 1-indexed positions into the target
                    positions = {int(x) - 1 for x in indices_str.split()}
                    word_aligns[glb_word] = positions

        if glb_tokens:
            seg_key = " ".join(glb_tokens)
            alignments[seg_key] = word_aligns

        i += 3

    return alignments


def load_all_giza_alignments():
    """Load GIZA++ alignments for all available language pairs.

    Returns dict: tmx_lang_code -> {glb_seg_key: {glb_word: {target_positions}}}
    """
    pairs = {
        "en": os.path.join(GIZA_DIR, "glb_en", "glb_en.A3.final"),
        "eo": os.path.join(GIZA_DIR, "glb_eo", "glb_eo.A3.final"),
    }
    # Spanish alignment would be glb_es if it exists
    es_path = os.path.join(GIZA_DIR, "glb_es", "glb_es.A3.final")
    if os.path.isfile(es_path):
        pairs["es"] = es_path

    result = {}
    for lang, path in pairs.items():
        if os.path.isfile(path):
            print(f"  Parsing GIZA++ alignments for {lang}...")
            result[lang] = parse_giza_a3(path)
    return result


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def build_db():
    """Populate LMDB from source files. Run once (or when data changes)."""
    print("Building WordViewerLMDB...")

    db = WordViewerDB(LMDB_DIR, readonly=False)

    # -- Load word-list.csv --
    wl = pd.read_csv(WORDLIST_CSV, dtype=str).fillna("")
    wl = wl.set_index("Word")

    # -- Load extension TSV (direct output of Wiktionary extender) --
    ext_df = pd.read_csv(EXTENSION_TSV, sep="\t", index_col=0, dtype=str).fillna("")
    ext_df = ext_df[~ext_df.index.duplicated(keep="first")]

    # -- Load pronouns TSV --
    pron_df = pd.read_csv(PRONOUNS_TSV, sep="\t", index_col=0, dtype=str).fillna("")

    # -- Load images TSV (is actually tab-separated despite .csv) --
    img_rows = {}
    with open(IMAGES_TSV, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader)  # skip header
        for row in reader:
            if len(row) >= 4 and row[0] and row[2].strip():
                img_rows[row[0].strip()] = {
                    "direct_url": row[2].strip(),
                    "source_page": row[3].strip() if len(row) > 3 else "",
                }

    # -- Load Soti.tsv (sound effects) --
    soti_rows = {}
    with open(SOTI_TSV, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if len(row) >= 2 and row[0]:
                soti_rows[row[0].strip()] = {
                    "audio_url": row[1].strip(),
                    "source_url": row[2].strip() if len(row) > 2 else "",
                }

    # -- Load NSFW blacklist --
    nsfw_words = set()
    with open(GRAPHIC_BLACKLIST, encoding="utf-8") as f:
        for line in f:
            w = line.strip()
            if w:
                nsfw_words.add(w)

    # -- Load Constructions.xlsx --
    constructions_map = {}
    try:
        cx = pd.read_excel(CONSTRUCTIONS_XLSX, dtype=str).fillna("")
        for _, row in cx.iterrows():
            lexi = str(row.get("Lexi", "")).strip()
            if not lexi:
                continue
            to_exclude = str(row.get("to_exclude", "")).strip()
            c_list = []
            for i in ["1", "2"]:
                c = str(row.get(f"construction{i}", "")).strip()
                ct = str(row.get(f"construction{i}basatayti", "")).strip()
                if c:
                    c_list.append({
                        "construction": c,
                        "translation": ct,
                        "to_exclude": to_exclude if i == "1" else "",
                    })
            if c_list or to_exclude:
                constructions_map[lexi] = c_list
    except Exception as e:
        print(f"  Warning: could not load Constructions.xlsx: {e}")

    # -- Load GIZA++ alignments --
    giza_aligns = load_all_giza_alignments()
    # giza_aligns: {lang_code: {glb_seg_key: {glb_word: {target_positions}}}}

    # -- Parse TMX --
    print("  Parsing TMX...")
    tmx_by_word = {}  # word -> list of {glb_seg, translations, context, alignments}

    try:
        tree = ET.parse(TMX_FILE)
        root = tree.getroot()
        body = root.find("body")
        if body is None:
            body = root

        for tu in body.findall("tu"):
            context = ""
            for prop in tu.findall("prop"):
                if prop.get("type") == "x-context":
                    context = (prop.text or "").strip()

            glb_seg = ""
            translations = {}
            for tuv in tu.findall("tuv"):
                lang = tuv.get("{http://www.w3.org/XML/1998/namespace}lang", "")
                seg_el = tuv.find("seg")
                seg_text = (seg_el.text or "").strip() if seg_el is not None else ""
                if lang == "glb":
                    glb_seg = seg_text
                elif lang and seg_text:
                    translations[lang] = seg_text

            if not glb_seg:
                continue

            # Look up GIZA alignments for this sentence
            giza_key = " ".join(_giza_tokenize(glb_seg))
            # alignments: {lang_code: {glb_word: [target_positions]}}
            aligns = {}
            for lang_code, lang_aligns in giza_aligns.items():
                if giza_key in lang_aligns:
                    # Convert sets to sorted lists for msgpack
                    aligns[lang_code] = {
                        w: sorted(positions)
                        for w, positions in lang_aligns[giza_key].items()
                    }

            entry = {
                "glb_seg": glb_seg,
                "translations": translations,
                "context": context,
                "alignments": aligns,
            }

            # Tokenize Globasa segment for indexing
            tokens = re.findall(r"[a-zğüşıöçA-ZĞÜŞİÖÇ]+", glb_seg.lower())
            seen = set()
            for tok in tokens:
                if tok not in seen:
                    seen.add(tok)
                    if tok not in tmx_by_word:
                        tmx_by_word[tok] = []
                    tmx_by_word[tok].append(entry)

    except Exception as e:
        print(f"  Warning: could not parse TMX: {e}")

    # -- Also build reverse lookup (derived words) --
    # We store the full wordlist in LMDB and do reverse lookup at request time.

    print("  Writing to LMDB...")
    with db.begin_write() as txn:

        for word, row in wl.iterrows():
            word = str(word).strip()
            if not word:
                continue

            # wordlist db
            entry = {
                "WordClass": str(row.get("WordClass", "")).strip(),
                "TranslationEng": str(row.get("TranslationEng", "")).strip(),
                "TranslationSpa": str(row.get("TranslationSpa", "")).strip(),
                "TranslationEpo": str(row.get("TranslationEpo", "")).strip(),
                "Synonyms": str(row.get("Synonyms", "")).strip(),
                "Antonyms": str(row.get("Antonyms", "")).strip(),
                "Tags": str(row.get("Tags", "")).strip(),
                "Category": str(row.get("Category", "")).strip(),
                "LexiliAsel": str(row.get("LexiliAsel", "")).strip(),
            }
            db._put("wordlist", word, entry, txn)

            # extensions db
            if word in ext_df.index:
                ext_row = ext_df.loc[word]
                ext_entry = {}
                for col in ext_df.columns:
                    v = str(ext_row[col]).strip()
                    if v and v != "False":
                        ext_entry[col] = v
                if ext_entry:
                    db._put("extensions", word, ext_entry, txn)

            # pronouns db
            if word in pron_df.index:
                pron_row = pron_df.loc[word]
                pronoun = str(pron_row.get("Pronoun", "")).strip()
                if pronoun and pronoun != "False":
                    db._put("pronouns", word, pronoun, txn)

            # images db
            if word in img_rows:
                db._put("images", word, img_rows[word], txn)

            # sound_effects db
            if word in soti_rows:
                db._put("sound_effects", word, soti_rows[word], txn)

            # nsfw db
            if word in nsfw_words:
                txn.put(word.encode("utf-8"), b"1", db=db._db("nsfw"))

            # constructions db
            if word in constructions_map:
                db._put("constructions", word, constructions_map[word], txn)

        # TMX db
        for word, entries in tmx_by_word.items():
            db._put("tmx", word, entries, txn)

    db.close()
    print("  Done.")


# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------

app = Flask(__name__)

# Open DB at startup (will build if missing)
if not os.path.exists(LMDB_DIR):
    build_db()

_db = WordViewerDB(LMDB_DIR, readonly=True)

# Cache the full word list for derived-word reverse lookup and search index
print("Loading word list index for reverse lookup and search...")
_all_entries = {}
# _trans_index: {lang_display: {lowered_translation_term: set of globasa words}}
_trans_index = {}
# _tag_index: {tag_string: [list of globasa words]}
_tag_index = {}

_TRANS_COLS = {
    "TranslationEng": "English",
    "TranslationSpa": "Spanish",
    "TranslationEpo": "Esperanto",
    "TranslationDeu": "German",
    "TranslationFra": "French",
    "TranslationRus": "Russian",
    "TranslationZho": "Mandarin Chinese",
}

_STRIP_ANNOT_RE = re.compile(r"_[^_]+_")  # strip _markdown_ annotations
_STRIP_POS_RE = re.compile(r"^[a-z./ ]+:\s*")  # strip "n: " prefixes

def _index_translation(text, lang, glb_word):
    """Extract individual glosses from a translation string and index them."""
    if not text:
        return
    if lang not in _trans_index:
        _trans_index[lang] = {}
    idx = _trans_index[lang]
    # Split on semicolons (PoS groups) then commas (individual glosses)
    for part in text.split(";"):
        part = _STRIP_POS_RE.sub("", part).strip()
        for gloss in part.split(","):
            gloss = _STRIP_ANNOT_RE.sub("", gloss).strip()
            gloss = re.sub(r"[()]+", "", gloss).strip()
            if gloss and len(gloss) > 1:
                key = gloss.lower()
                if key not in idx:
                    idx[key] = set()
                idx[key].add(glb_word)

wl_df = pd.read_csv(WORDLIST_CSV, dtype=str).fillna("")
for _, row in wl_df.iterrows():
    word = str(row.get("Word", "")).strip()
    if word:
        _all_entries[word] = {
            "WordClass": str(row.get("WordClass", "")).strip(),
            "Synonyms": str(row.get("Synonyms", "")).strip(),
            "Antonyms": str(row.get("Antonyms", "")).strip(),
            "Category": str(row.get("Category", "")).strip(),
            "LexiliAsel": str(row.get("LexiliAsel", "")).strip(),
        }
        # Index tags
        for t in str(row.get("Tags", "")).split(","):
            t = t.strip()
            if t:
                if t not in _tag_index:
                    _tag_index[t] = []
                _tag_index[t].append(word)
        for col, lang in _TRANS_COLS.items():
            _index_translation(str(row.get(col, "")), lang, word)
        # Index SearchTermsEng under English
        _index_translation(str(row.get("SearchTermsEng", "")), "English", word)

# Also index extension languages
try:
    ext_df = pd.read_csv(EXTENSION_TSV, sep="\t", dtype=str, index_col=0).fillna("")
    ext_df = ext_df[~ext_df.index.duplicated(keep="first")]
    for word, row in ext_df.iterrows():
        word = str(word).strip()
        for col in EXT_LANG_COLS:
            val = str(row.get(col, "")).strip()
            if val and val != "False":
                display = LANG_DISPLAY.get(col, col)
                _index_translation(val, display, word)
except Exception:
    pass

print(f"  Loaded {len(_all_entries)} entries, {sum(len(v) for v in _trans_index.values())} translation index terms.")


def find_derived_words(target_word):
    """Find words derived from target_word by checking etymology compounds.

    A word is derived if its LexiliAsel (etymology) is a compound like
    "root1 + root2 + ..." and target_word (or -target_word as a suffix)
    appears as one of the components.
    """
    import re
    derived = []
    target_lower = target_word.lower()
    # Pattern: etymology is purely "word1 + word2 + ..." (no language names/parens)
    compound_re = re.compile(r'^-?[a-zA-ZğüşıöçĞÜŞİÖÇ]+(\s*\+\s*-?[a-zA-ZğüşıöçĞÜŞİÖÇ]+)+$')
    for w, info in _all_entries.items():
        if w.lower() == target_lower:
            continue
        etym = info.get("LexiliAsel", "")
        if not etym or not compound_re.match(etym.strip()):
            continue
        # Split compound into components, strip leading hyphens for suffix matching
        components = [c.strip().lstrip("-").lower() for c in etym.split("+")]
        if target_lower in components:
            derived.append(w)
    return sorted(derived)


# POS display names mapping for the API (canonical English)
_POS_NAMES = {
    GlossPoS.NOUN: "noun",
    GlossPoS.PROPER_NOUN: "proper noun",
    GlossPoS.VERB: "verb",
    GlossPoS.VERB_PHRASE: "verb phrase",
    GlossPoS.ADJECTIVE: "adjective",
    GlossPoS.PROPER_ADJECTIVE: "proper adjective",
    GlossPoS.VERBAL_ADVERB: "verbal adverb",
    GlossPoS.ADVERB: "adverb",
    GlossPoS.INTERJECTION: "interjection",
    GlossPoS.PRONOUN: "pronoun",
    GlossPoS.NUMBER: "number",
    GlossPoS.PREPOSITION: "preposition",
    GlossPoS.PHRASAL_PREPOSITION: "phrasal preposition",
    GlossPoS.PREPOSITIONAL_PHRASE: "prepositional phrase",
    GlossPoS.POSTPOSITION: "postposition",
    GlossPoS.CONJUNCTION: "conjunction",
    GlossPoS.DETERMINER: "determiner",
    GlossPoS.PARTICLE: "particle",
    GlossPoS.PREFIX: "prefix",
    GlossPoS.PHRASE: "phrase",
    GlossPoS.POSSESSIVE_PRONOUN: "possessive pronoun",
    GlossPoS.POSSESSIVE_ADJECTIVE: "possessive adjective",
    GlossPoS.PHRASAL_ADVERB: "phrasal adverb",
    GlossPoS.NOUN_PHRASE: "noun phrase",
    GlossPoS.CONJUNCTION_PHRASE: "conjunction phrase",
    GlossPoS.ADJECTIVE_PHRASE: "adjective phrase",
    GlossPoS.PHRASAL_CONJUNCTION: "phrasal conjunction",
}

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

# Extension language column names (as in the unedited menalariExtension.tsv)
EXT_LANG_COLS = [
    # Romance
    "French", "Italian", "Portuguese", "Romanian",
    # Germanic
    "German", "Dutch", "Swedish", "Old English (ca. 450-1100)",
    # Classical
    "Ancient Greek (to 1453)", "Latin", "Sanskrit", "Greek",
    # Slavic + E-European
    "Russian", "Polish", "Bulgarian", "Ukrainian", "Serbian", "Czech", "Hungarian",
    # Semitic + Turkic
    "Yiddish", "Hebrew", "Arabic", "Turkish", "Tatar",
    # East Asian
    "Mandarin Chinese", "Japanese", "Korean", "Vietnamese",
    # SE Asian / Austronesian
    "Indonesian", "Malay", "Tagalog",
    # Iranian + Indic
    "Persian", "Hindi", "Urdu", "Bengali", "Tamil", "Telugu", "Kannada",
    "Malayalam", "Gujarati", "Panjabi",
    # African
    "Swahili",
]

# Display names for languages (TSV column name -> shorter display name)
LANG_DISPLAY = {col: col for col in EXT_LANG_COLS}
LANG_DISPLAY.update({
    "Old English (ca. 450-1100)": "Old English",
    "Ancient Greek (to 1453)": "Ancient Greek",
    "Spanish": "Spanish",
    "Esperanto": "Esperanto",
})


def build_translations_payload(wl_entry, ext_entry, to_exclude_glosses=None):
    """Build the full translations structure for the JSON response.

    Returns dict:
      {
        "has_verbs": bool,
        "pos_groups": [
          {
            "pos": "noun",
            "verb_type": null,
            "languages": {
              "Spanish": [{"text": "...", "gender": null}, ...],
              "German": [{"text": "...", "gender": "f"}, ...],
              ...
            }
          },
          ...
        ]
      }
    """
    wordclass = wl_entry.get("WordClass", "")
    eng_text = wl_entry.get("TranslationEng", "")
    spa_text = wl_entry.get("TranslationSpa", "")
    epo_text = wl_entry.get("TranslationEpo", "")

    # Build non-English translations dict for parseWordEntry
    non_eng = {}
    if spa_text:
        non_eng["Spa"] = spa_text
    if epo_text:
        non_eng["Epo"] = epo_text
    if ext_entry:
        for col in EXT_LANG_COLS:
            v = ext_entry.get(col, "")
            if v and v != "False":
                non_eng[col] = v

    parsed = parseWordEntry(eng_text, wordclass, non_eng)

    # Build the pos_groups list — one entry per unique (pos, verb_type) pair
    # We align all languages by the English gloss structure.
    eng_glosses = parsed.translations.get("Eng", [])

    # Deduplicate English glosses by (pos, verb_type) — keep one representative per pos group
    pos_group_keys = []
    seen_pg = set()
    for g in eng_glosses:
        key = (_POS_NAMES.get(g.pos, "phrase"), _VERB_TYPE_NAMES.get(g.verb_type) if g.verb_type else None)
        if key not in seen_pg:
            seen_pg.add(key)
            pos_group_keys.append(key)

    # For each pos group, gather translations from every language
    # We need to map the i-th pos group to the i-th semicolon segment in each language
    pos_groups = []
    has_verbs = any(k[0] == "verb" for k in pos_group_keys)

    for idx, (pos_name, verb_type_name) in enumerate(pos_group_keys):
        lang_data = {}

        # English
        eng_items = [g for g in eng_glosses
                     if _POS_NAMES.get(g.pos, "phrase") == pos_name
                     and (_VERB_TYPE_NAMES.get(g.verb_type) if g.verb_type else None) == verb_type_name]
        # Filter out to_exclude glosses from main table
        if to_exclude_glosses:
            eng_items = [g for g in eng_items if g.gloss not in to_exclude_glosses]

        lang_data["English"] = [{"text": g.gloss, "gender": None} for g in eng_items]

        # Spanish (from parseWordEntry, no gender markers)
        spa_glosses = parsed.translations.get("Spa", [])
        spa_for_pos = [g for g in spa_glosses
                       if _POS_NAMES.get(g.pos, "phrase") == pos_name
                       and (_VERB_TYPE_NAMES.get(g.verb_type) if g.verb_type else None) == verb_type_name]
        lang_data["Spanish"] = [{"text": _strip_gender(g.gloss), "gender": None} for g in spa_for_pos]

        # Esperanto (from parseWordEntry, no gender markers)
        epo_glosses = parsed.translations.get("Epo", [])
        epo_for_pos = [g for g in epo_glosses
                       if _POS_NAMES.get(g.pos, "phrase") == pos_name
                       and (_VERB_TYPE_NAMES.get(g.verb_type) if g.verb_type else None) == verb_type_name]
        lang_data["Esperanto"] = [{"text": _strip_gender(g.gloss), "gender": None} for g in epo_for_pos]

        # Extension languages — use semicolon-grouped raw parsing
        for col in EXT_LANG_COLS:
            raw_val = ext_entry.get(col, "") if ext_entry else ""
            groups = parse_extension_cell_grouped(raw_val)
            if idx < len(groups):
                lang_data[LANG_DISPLAY[col]] = groups[idx]
            else:
                lang_data[LANG_DISPLAY[col]] = []

        pos_groups.append({
            "pos": pos_name,
            "verb_type": verb_type_name,
            "languages": lang_data,
        })

    return {"has_verbs": has_verbs, "pos_groups": pos_groups}


@app.route("/")
def index():
    return send_file(HTML_FILE)


@app.route("/word_viewer_scripts.js")
def scripts_js():
    return send_file(os.path.join(BASE_DIR, "word_viewer_scripts.js"), mimetype="text/javascript")


@app.route("/fonts/<path:filename>")
def serve_font(filename):
    font_dir = os.path.expanduser("~/.local/share/fonts")
    return send_file(os.path.join(font_dir, filename))


@app.route("/etym_langs")
def etym_langs():
    import csv as csv_mod
    path = os.path.join(os.path.dirname(__file__), "word_viewer_etym_langs.csv")
    result = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv_mod.DictReader(f):
            result[row["globasa"]] = row["internal"]
    return jsonify(result)


@app.route("/i18n")
def i18n():
    import csv as csv_mod
    i18n_path = os.path.join(os.path.dirname(__file__), "word_viewer_i18n.csv")
    result = {}
    with open(i18n_path, newline="", encoding="utf-8") as f:
        reader = csv_mod.DictReader(f)
        for row in reader:
            key = row.pop("key")
            result[key] = {lang: val for lang, val in row.items() if val and lang}
    return jsonify(result)


@app.route("/suggest")
def suggest():
    """Return search suggestions for partial input.

    Searches both Globasa words (prefix match) and translations (substring match
    in selected display languages). Returns up to 15 results.
    """
    q_raw = request.args.get("q", "").strip()
    q = q_raw.lower()
    langs = request.args.get("langs", "English").split(",")
    if not q or len(q) < 2:
        return jsonify([])

    MAX = 15
    results = []  # list of {word, match_type, via}
    seen = set()

    # 1. Exact Globasa match (try original case, then lowercase)
    for candidate in [q_raw, q]:
        if candidate in _all_entries and candidate.lower() not in seen:
            seen.add(candidate.lower())
            results.append({"word": candidate, "type": "exact"})

    # 2. Globasa prefix matches
    for w in _all_entries:
        if len(results) >= MAX:
            break
        wl = w.lower()
        if wl.startswith(q) and wl not in seen:
            seen.add(wl)
            results.append({"word": w, "type": "prefix"})

    # 3. Translation matches in selected languages
    for lang in langs:
        idx = _trans_index.get(lang, {})
        # Exact translation match
        if q in idx:
            for glb_word in sorted(idx[q]):
                if len(results) >= MAX:
                    break
                if glb_word.lower() not in seen:
                    seen.add(glb_word.lower())
                    results.append({"word": glb_word, "type": "translation", "via": q, "lang": lang})
        # Prefix match on translation terms
        if len(results) < MAX:
            for term, glb_words in idx.items():
                if len(results) >= MAX:
                    break
                if term.startswith(q) and term != q:
                    for glb_word in sorted(glb_words):
                        if len(results) >= MAX:
                            break
                        if glb_word.lower() not in seen:
                            seen.add(glb_word.lower())
                            results.append({"word": glb_word, "type": "translation", "via": term, "lang": lang})

    return jsonify(results[:MAX])


@app.route("/tags")
def list_tags():
    """Return all tags with word counts, sorted by name."""
    result = [{"tag": t, "count": len(words)} for t, words in _tag_index.items()]
    result.sort(key=lambda x: x["tag"])
    return jsonify(result)


@app.route("/tags/<path:tag>")
def tag_words(tag):
    """Return words for a given tag."""
    words = _tag_index.get(tag)
    if words is None:
        return jsonify({"error": f"Tag '{tag}' not found"}), 404
    return jsonify({"tag": tag, "words": sorted(words)})


@app.route("/lookup/<word>")
def lookup(word):
    word = word.strip()

    # Try original case first, then lowercase
    wl_entry = _db.get_wordlist(word)
    if wl_entry is None:
        word = word.lower()
        wl_entry = _db.get_wordlist(word)
    if wl_entry is None:
        return jsonify({"error": f"Word '{word}' not found"}), 404

    ext_entry = _db.get_extensions(word) or {}
    pronoun = _db.get_pronoun(word)
    image = _db.get_image(word)
    sound_effect = _db.get_sound_effect(word)
    nsfw = _db.is_nsfw(word)
    constructions = _db.get_constructions(word) or []
    tmx_entries = _db.get_tmx(word) or []

    # Pronunciation: check if file exists
    audio_path = os.path.join(AUDIO_DIR, f"{word}.ogg")
    has_pronunciation = os.path.isfile(audio_path)

    # Derived words (prefix match)
    derived_words = find_derived_words(word)

    # to_exclude glosses (from constructions) — exclude from main table
    to_exclude = set()
    for c in constructions:
        excl = c.get("to_exclude", "")
        if excl:
            for part in excl.split(", "):
                to_exclude.add(part.strip())

    # Build translations
    translations = build_translations_payload(wl_entry, ext_entry, to_exclude)

    # Build word glossary for tooltip (all Globasa words in examples)
    # Returns {word_or_phrase: {lang_display_name: short_gloss}}
    # Includes multi-word entries (up to 5 words) for greedy matching

    def _short_gloss(text):
        short = text.split(";")[0].strip()
        short = re.sub(r"^[a-z./ ]+:\s*", "", short)
        return short

    def _build_glosses(key):
        we = _db.get_wordlist(key)
        ext_w = _db.get_extensions(key)
        if not we:
            return None
        glosses = {}
        for field, display in [("TranslationEng", "English"), ("TranslationSpa", "Spanish"), ("TranslationEpo", "Esperanto")]:
            val = we.get(field, "")
            if val:
                glosses[display] = _short_gloss(val)
        if ext_w:
            for col, display in LANG_DISPLAY.items():
                val = ext_w.get(col, "")
                if val and val != "False":
                    glosses[display] = _short_gloss(_strip_gender(val))
        return glosses if glosses else None

    # Collect all word tokens from examples
    all_tokens = []  # list of token lists per sentence
    for entry in tmx_entries[:20]:
        seg = entry.get("glb_seg", "")
        tokens = re.findall(r"[a-zğüşıöçA-ZĞÜŞİÖÇ]+", seg.lower())
        all_tokens.append(tokens)

    word_glossary = {}
    checked = set()
    MAX_NGRAM = 5
    for tokens in all_tokens:
        # Check n-grams from longest to shortest
        for n in range(MAX_NGRAM, 0, -1):
            for i in range(len(tokens) - n + 1):
                phrase = " ".join(tokens[i:i + n])
                if phrase in checked:
                    continue
                checked.add(phrase)
                glosses = _build_glosses(phrase)
                if glosses:
                    word_glossary[phrase] = glosses

    # Send up to 20 examples; the frontend sorts and caps at 5
    examples = []
    for entry in tmx_entries[:20]:
        examples.append({
            "glb_seg": entry.get("glb_seg", ""),
            "translations": entry.get("translations", {}),
            "context": entry.get("context", ""),
            "alignments": entry.get("alignments", {}),
        })

    return jsonify({
        "word": word,
        "wordclass": wl_entry.get("WordClass", ""),
        "globasa_gender": pronoun,
        "etymology": wl_entry.get("LexiliAsel", ""),
        "synonyms": [s.strip() for s in wl_entry.get("Synonyms", "").split(",") if s.strip()],
        "antonyms": [a.strip() for a in wl_entry.get("Antonyms", "").split(",") if a.strip()],
        "tags": [t.strip() for t in wl_entry.get("Tags", "").split(",") if t.strip()],
        "category": wl_entry.get("Category", ""),
        "image": image,
        "nsfw": nsfw,
        "has_pronunciation": has_pronunciation,
        "sound_effect": sound_effect,
        "constructions": constructions,
        "derived_words": derived_words,
        "translations": translations,
        "examples": examples,
        "word_glossary": word_glossary,
    })


@app.route("/audio/<path:filename>")
def serve_audio(filename):
    # Only allow .ogg files; sanitize path
    if not filename.endswith(".ogg"):
        abort(404)
    word = filename[:-4]
    if not re.fullmatch(r"[a-z_]+", word):
        abort(404)
    path = os.path.join(AUDIO_DIR, filename)
    if not os.path.isfile(path):
        abort(404)
    return send_file(path, mimetype="audio/ogg")


@app.route("/rebuild")
def rebuild():
    """Admin endpoint to rebuild LMDB from source files."""
    global _db
    _db.close()
    build_db()
    _db = WordViewerDB(LMDB_DIR, readonly=True)
    return jsonify({"status": "rebuilt"})


if __name__ == "__main__" or True:
    app.run(debug=True, port=5000)
