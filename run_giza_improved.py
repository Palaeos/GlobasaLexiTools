"""
Improved GIZA++ alignment pipeline for Globasa.
Builds on run_giza.py with:
  1. Dictionary seeding from word-list.csv + menalariExtension.tsv
  2. Word-level pair augmentation
  3. Factored morphological representation (PosTagger.py + spaCy)
  4. Bidirectional alignment + GDFA symmetrization
"""

import csv
import re
import xml.etree.ElementTree as ET
import subprocess
from pathlib import Path

import spacy
from PosTagger import tokenize as glb_tokenize, assign_pos

TMX_FILE = Path(__file__).resolve().parent / "Doxo_passages.tmx"
WORDLIST = Path(__file__).resolve().parent / "Old wordlists" / "word-list.csv"
MENALARI = Path(__file__).resolve().parent / "menalariExtension.tsv"
BASE_DIR = Path(__file__).resolve().parent
GIZA_DIR = BASE_DIR / "giza-pp"
GIZA = GIZA_DIR / "GIZA++-v2/GIZA++"
PLAIN2SNT = GIZA_DIR / "GIZA++-v2/plain2snt.out"
SNT2COOC = GIZA_DIR / "GIZA++-v2/snt2cooc.out"
MKCLS = GIZA_DIR / "mkcls-v2/mkcls"
OUT_DIR = Path(__file__).resolve().parent / "giza_output_improved"
NS = "{http://www.w3.org/XML/1998/namespace}"

# Map GIZA target language codes to word-list.csv and menalariExtension.tsv columns
LANG_TO_WORDLIST_COL = {
    "en": "TranslationEng", "eo": "TranslationEpo", "es": "TranslationSpa",
    "de": "TranslationDeu", "fr": "TranslationFra", "ru": "TranslationRus",
    "zh": "TranslationZho",
}

LANG_TO_MENALARI_COL = {
    "en": "Eng with Senses", "eo": "Esperanto", "es": "Spanish",
    "de": "German", "fr": "French", "ru": "Russian", "zh": "Mandarin",
    "nl": "Dutch", "pt": "Portuguese", "id": "Indonesian", "tr": "Turkish",
    "ar": "Arabic", "hi": "Hindi", "sw": "Swahili", "da": None,
}


# ---------------------------------------------------------------------------
# Gloss parsing
# ---------------------------------------------------------------------------

_WORDLIST_ANNOTATION_RE = re.compile(
    r'^(?:n|v\.tr|v\.intr|v\.cop|v\.aux|v phrs|adj|adv|interj|prep|conj|det|'
    r'pron|num|par|prop n|prop adj|poss pron|poss adj|phrs|pfx|m|'
    r'n/v\.tr sfx|n/v\.intr sfx|adj/adv sfx|n sfx|v\.tr sfx|adj sfx|adv sfx|'
    r'cop plus prep|bound root|root sfx[^:]*|root pfx|'
    r'tr|intr|tr/intr|intr \(optional -cu\)|tr/intr \(optional -cu\))'
    r'(?:\s*\([^)]+\))?\s*:\s*',
    re.IGNORECASE,
)

_ITALIC_RE = re.compile(r'_([^_]+)_')
_PARENS_RE = re.compile(r'\([^)]*\)')
_GENDER_TAG_RE = re.compile(r'\s*<[fmn]+(?:pl)?>\s*')
_SENSE_BRACKET_RE = re.compile(r'\s*\[[^\]]*\]\s*')


def parse_wordlist_gloss(text):
    """Extract clean individual words from a word-list.csv translation cell.
    Returns list of lowercase single-word strings.
    """
    if not text or not text.strip():
        return []
    words = set()
    for segment in text.split(";"):
        segment = segment.strip()
        # Strip PoS annotation prefix
        segment = _WORDLIST_ANNOTATION_RE.sub("", segment)
        # Strip italic markers
        segment = _ITALIC_RE.sub(r"\1", segment)
        # Strip parenthetical qualifiers
        segment = _PARENS_RE.sub("", segment)
        # Split on comma
        for part in segment.split(","):
            part = part.strip().lower().replace("\n", "").replace("\r", "")
            # Only keep single clean words (no phrases, no whitespace)
            if part and " " not in part and "\t" not in part and len(part) > 1 and not part.startswith("-"):
                words.add(part)
    return list(words)


def parse_menalari_gloss(text):
    """Extract clean individual words from a menalariExtension.tsv cell.
    Returns list of lowercase single-word strings.
    """
    if not text or not text.strip():
        return []
    words = set()
    # Strip gender tags like <f>, <m>, <n>, <mf>
    text = _GENDER_TAG_RE.sub(" ", text)
    # Strip sense brackets like [bird]
    text = _SENSE_BRACKET_RE.sub(" ", text)
    for part in text.split(","):
        part = part.strip().lower().replace("\n", "").replace("\r", "")
        # Only keep single clean words, skip affixes
        if part and " " not in part and "\t" not in part and len(part) > 1 and not part.startswith("-"):
            words.add(part)
    return list(words)


# ---------------------------------------------------------------------------
# Load lexical data
# ---------------------------------------------------------------------------

_wordlist_cache = None
_menalari_cache = None
_morphemes_cache = None


def _load_wordlist():
    global _wordlist_cache
    if _wordlist_cache is not None:
        return _wordlist_cache
    _wordlist_cache = []
    with open(WORDLIST, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            _wordlist_cache.append(row)
    return _wordlist_cache


def _load_menalari():
    global _menalari_cache
    if _menalari_cache is not None:
        return _menalari_cache
    _menalari_cache = []
    with open(MENALARI, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            _menalari_cache.append(row)
    return _menalari_cache


def get_word_pairs(lang2):
    """Get (globasa_word, target_word) pairs for a target language.
    Combines word-list.csv and menalariExtension.tsv sources.
    Returns deduplicated list of (glb, tgt) tuples.
    """
    pairs = set()

    # Source 1: word-list.csv
    wl_col = LANG_TO_WORDLIST_COL.get(lang2)
    if wl_col:
        for row in _load_wordlist():
            glb = row.get("Word", "").strip().lower()
            if not glb or glb.startswith("(") or glb.startswith("-"):
                continue
            trans = row.get(wl_col, "")
            for word in parse_wordlist_gloss(trans):
                pairs.add((glb, word))

    # Source 2: menalariExtension.tsv
    men_col = LANG_TO_MENALARI_COL.get(lang2)
    if men_col:
        for row in _load_menalari():
            glb = (row.get("Globasa") or "").strip().lower()
            if not glb:
                continue
            trans = row.get(men_col) or ""
            for word in parse_menalari_gloss(trans):
                pairs.add((glb, word))

    return list(pairs)


# ---------------------------------------------------------------------------
# Morphological segmentation
# ---------------------------------------------------------------------------

# Grammatical affixes that typically map to separate words in target
# languages. These get separated and marked (-li, be-) during decomposition.
#
# Compound-root suffixes like -dom, -din, -bol, -doku are NOT in this list
# because they carry independent meaning and behave like noun roots in
# compounds (e.g., kitabu+dom = library, where dom = building).
_GRAMMATICAL_SUFFIXES = {
    "li",   # adjective marker → "of", "-al", "-ic" (insanli ↔ "human" / "des hommes")
    "ya",   # abstract noun → "-ness", "-ity" (huruya ↔ "freedom")
    "do",   # passive participle → "-ed" (basataytido ↔ "translated")
    "ne",   # active participle/agent → "-ing", "-er" (ergone ↔ "worker")
    "mo",   # adverb marker → "-ly" (perfetomo ↔ "perfectly")
    "cu",   # become / intransitive → "become" (sahi+cu ↔ "become correct")
    "gi",   # causative → "make" (sahi+gi ↔ "make correct" / "correct")
    "abil", # -able / can be (lubiabil ↔ "lovable")
    "ible", # -ible (variant of -abil)
    "bisu", # must be
    "musi", # which must
    "gimu", # which should
    "kal",  # without sufficient / -less (huruya+kal ↔ "freedomless")
    "laye", # worthy
    "fil",  # tending to / -prone
    "pul",  # full of / -ful (jiwa+pul ↔ "vibrant")
    "ple",  # multiplier (-uple)
}
_GRAMMATICAL_PREFIXES = {
    "be",   # passive marker → "be"/"is"/"was" (bekrea ↔ "was created")
    "du",   # continuous/durative → "keep -ing"
    "ri",   # again / re- → "re-" (riskri ↔ "rewrite")
    "aw",   # away / un-do → "away", "un-"
    "ja",   # already (perfective) → "already", "have"
    "no",   # negation → "not"/"un-"
    "nen",  # without → "-less"
    "ge",   # collective / group
}


def _load_morphemes():
    """Build morpheme lookup and affix inventory from word-list.csv."""
    global _morphemes_cache
    if _morphemes_cache is not None:
        return _morphemes_cache

    # Pass 1: collect affixes
    prefixes = set()
    suffixes = set()
    all_words = set()
    for row in _load_wordlist():
        word = row.get("Word", "").strip().lower()
        if word:
            all_words.add(word.lstrip("-").rstrip("-"))
        cat = row.get("Category", "")
        wc = row.get("WordClass", "")
        if cat == "affix":
            clean = word.strip("-")
            if word.startswith("-"):
                suffixes.add(clean)
            elif word.endswith("-"):
                prefixes.add(clean)
            elif "lfik" in wc:
                prefixes.add(clean)
            elif "xfik" in wc:
                suffixes.add(clean)

    # Pass 2: build explicit morpheme lookup from LexiliAsel
    explicit = {}
    for row in _load_wordlist():
        la = row.get("LexiliAsel", "")
        word = row.get("Word", "").strip().lower()
        if "+" not in la or not word:
            continue
        plus_parts = la.split("+")
        if len(plus_parts) < 2:
            continue
        morphemes = []
        for i, part in enumerate(plus_parts):
            subparts = [s.strip() for s in part.split(",")]
            if i == 0:
                candidate = subparts[-1].strip()
            elif i == len(plus_parts) - 1:
                candidate = subparts[0].strip()
            else:
                candidate = part.strip()
            candidate = candidate.strip("-").strip().lower()
            if candidate:
                morphemes.append(candidate)
        if len(morphemes) >= 2:
            explicit[word] = morphemes

    # Pass 3: build full lookup with productive affix stripping
    _morphemes_cache = dict(explicit)

    # Sort suffixes/prefixes longest-first for greedy matching
    sorted_suffixes = sorted(suffixes, key=len, reverse=True)
    sorted_prefixes = sorted(prefixes, key=len, reverse=True)

    # For words in text not in explicit lookup, try affix stripping
    # We store the affix lists for runtime use
    _morphemes_cache["__suffixes__"] = sorted_suffixes
    _morphemes_cache["__prefixes__"] = sorted_prefixes
    _morphemes_cache["__all_words__"] = all_words
    _morphemes_cache["__explicit__"] = explicit

    return _morphemes_cache


def segment_word(word, morphemes=None):
    """Segment a Globasa word into morphemes.

    Affix marking:
    - Suffixes are marked with leading hyphen: -li, -ya, -do
    - Prefixes are marked with trailing hyphen: be-, du-, mal-

    Decomposition rules:
    - Always strip known affixes (e.g., insanli → insan + -li), even if the
      derived form is in the word-list. This preserves cross-linguistic
      information (e.g., -li ↔ "de" in French possessive constructions).
    - Root+root compounds (kitabudom): keep whole if in word-list.
    - Otherwise, find minimum decomposition where each piece is a word-list
      entry or a known affix.

    Returns list of strings, or [word] if no decomposition found.
    """
    if morphemes is None:
        morphemes = _load_morphemes()

    all_words = morphemes["__all_words__"]
    sorted_suffixes = morphemes["__suffixes__"]
    sorted_prefixes = morphemes["__prefixes__"]

    # Use curated grammatical affix lists (sorted longest-first for matching)
    gram_sfx = sorted(_GRAMMATICAL_SUFFIXES, key=len, reverse=True)
    gram_pfx = sorted(_GRAMMATICAL_PREFIXES, key=len, reverse=True)

    # First priority: strip a grammatical suffix if the stem is a valid word.
    # Applied even if the full word is in the word-list (e.g., insanli)
    # since these suffixes carry cross-linguistic information.
    for sfx in gram_sfx:
        if word.endswith(sfx) and len(word) > len(sfx) + 1:
            stem = word[:-len(sfx)]
            if stem in all_words:
                stem_parts = segment_word(stem, morphemes)
                return stem_parts + [f"-{sfx}"]

    # Second priority: strip a grammatical prefix if the stem is a valid word
    for pfx in gram_pfx:
        if word.startswith(pfx) and len(word) > len(pfx) + 1:
            stem = word[len(pfx):]
            if stem in all_words:
                stem_parts = segment_word(stem, morphemes)
                return [f"{pfx}-"] + stem_parts

    # If the word is in the word-list (and has no grammatical affix), keep it whole
    # This protects compound roots like kitabudom, xorsomno, somnokamer
    if word in all_words:
        return [word]

    # Not in word-list — try fuller decomposition (any affix, any compound)

    # Grammatical prefix + stem + grammatical suffix
    for pfx in gram_pfx:
        if word.startswith(pfx) and len(word) > len(pfx) + 2:
            remainder = word[len(pfx):]
            for sfx in gram_sfx:
                if remainder.endswith(sfx) and len(remainder) > len(sfx) + 1:
                    stem = remainder[:-len(sfx)]
                    if stem in all_words:
                        return [f"{pfx}-", stem, f"-{sfx}"]

    # Fallback: full affix inventory (compound roots like -dom, -din)
    # These are NOT marked with hyphens since they're semantic content
    for sfx in sorted_suffixes:
        if word.endswith(sfx) and len(word) > len(sfx) + 1:
            stem = word[:-len(sfx)]
            if stem in all_words:
                return [stem, sfx]

    for pfx in sorted_prefixes:
        if word.startswith(pfx) and len(word) > len(pfx) + 1:
            stem = word[len(pfx):]
            if stem in all_words:
                return [pfx, stem]

    # Root + root compound (try splitting at every position)
    for split_pos in range(2, len(word) - 1):
        left, right = word[:split_pos], word[split_pos:]
        if left in all_words and right in all_words:
            return [left, right]

    return [word]


_mwe_cache = None


def _load_mwes():
    """Load multi-word expressions from word-list.csv.
    Returns dict mapping (word1, word2, ...) → joined form for known MWEs.

    Sources:
    1. Entries with spaces in the Word column (e.g., "bon xanse")
    2. Derived words whose LexiliAsel components are all standalone roots
       (e.g., "tigades" = "tiga + des" → MWE ("tiga", "des") → "tigades")
    """
    global _mwe_cache
    if _mwe_cache is not None:
        return _mwe_cache
    _mwe_cache = {}

    # Collect all root words for validation
    roots = set()
    for row in _load_wordlist():
        cat = row.get("Category", "")
        if cat == "root":
            roots.add(row.get("Word", "").strip().lower())

    for row in _load_wordlist():
        word = row.get("Word", "").strip()

        # Source 1: explicit multi-word entries
        if " " in word and not word.startswith("("):
            parts = tuple(word.lower().split())
            if len(parts) >= 2:
                _mwe_cache[parts] = word.lower().replace(" ", "")

        # Source 2: derived words decomposable into roots (compound words)
        la = row.get("LexiliAsel", "")
        if "+" in la and " " not in word:
            plus_parts = la.split("+")
            if len(plus_parts) >= 2:
                morphemes = []
                for i, part in enumerate(plus_parts):
                    subparts = [s.strip() for s in part.split(",")]
                    candidate = (subparts[-1] if i == 0 else subparts[0]).strip().strip("-").lower()
                    morphemes.append(candidate)
                # Only create MWE if ALL parts are standalone roots
                if len(morphemes) >= 2 and all(m in roots for m in morphemes):
                    _mwe_cache[tuple(morphemes)] = word.lower()

    return _mwe_cache


def join_mwes(tokens):
    """Join adjacent tokens that form known multi-word expressions.
    Uses greedy longest-match from left to right.
    """
    mwes = _load_mwes()
    if not mwes:
        return tokens
    # Find max MWE length
    max_len = max(len(k) for k in mwes)
    result = []
    i = 0
    while i < len(tokens):
        matched = False
        # Try longest match first
        for length in range(min(max_len, len(tokens) - i), 1, -1):
            candidate = tuple(tokens[i:i + length])
            if candidate in mwes:
                result.append(mwes[candidate])
                i += length
                matched = True
                break
        if not matched:
            result.append(tokens[i])
            i += 1
    return result


# ---------------------------------------------------------------------------
# TMX extraction
# ---------------------------------------------------------------------------

def extract_parallel(tmx_path, lang1, lang2):
    """Extract parallel sentences for a language pair from TMX."""
    tree = ET.parse(tmx_path)
    pairs = []
    for tu in tree.getroot().find("body").findall("tu"):
        texts = {}
        for tuv in tu.findall("tuv"):
            lang = tuv.get(f"{NS}lang")
            seg = tuv.find("seg")
            if seg is not None and seg.text:
                texts[lang] = seg.text.strip()
        if lang1 in texts and lang2 in texts:
            pairs.append((texts[lang1], texts[lang2]))
    return pairs


# ---------------------------------------------------------------------------
# Tokenization
# ---------------------------------------------------------------------------

def tokenize(text, segment_morphemes=False):
    """Tokenize text: lowercase, split punctuation, optionally segment morphemes.
    When segment_morphemes=True:
      1. Join known multi-word expressions (e.g., "tiga des" → "tiga_des")
      2. Segment compounds into morphemes (e.g., "kitabudom" → "kitabu dom")
    """
    text = text.lower()
    text = re.sub(r'([.,:;!?\u201c\u201d\u201e\u201f"()\'—\-])', r' \1 ', text)
    tokens = text.split()
    if segment_morphemes:
        # Step 1: join multi-word expressions into single tokens
        tokens = join_mwes(tokens)
        # Step 2: segment each token into morphemes
        morphemes = _load_morphemes()
        expanded = []
        for tok in tokens:
            expanded.extend(segment_word(tok, morphemes))
        tokens = expanded
    return " ".join(tokens)


# ---------------------------------------------------------------------------
# Factored tokenization
# ---------------------------------------------------------------------------

_spacy_models = {}


def _get_spacy(lang):
    """Load and cache a spaCy model for the given language code."""
    if lang not in _spacy_models:
        model_map = {
            "en": "en_core_web_sm", "de": "de_core_news_sm",
            "fr": "fr_core_news_sm", "es": "es_core_news_sm",
            "pt": "pt_core_news_sm", "nl": "nl_core_news_sm",
            "ru": "ru_core_news_sm", "zh": "zh_core_web_sm",
            "ja": "ja_core_news_sm", "tr": "tr_core_news_lg",
        }
        model_name = model_map.get(lang)
        if model_name:
            try:
                _spacy_models[lang] = spacy.load(model_name)
            except OSError:
                _spacy_models[lang] = None
        else:
            _spacy_models[lang] = None
    return _spacy_models[lang]


def _infer_pos_from_wordclass(word):
    """Infer a POS label from word-list.csv WordClass for a single word.
    Used as fallback when PosTagger returns UNK.
    """
    rows = _load_wordlist()
    for row in rows:
        if row.get("Word", "").strip().lower() == word:
            wc = row.get("WordClass", "").strip()
            if wc.startswith("b"):
                return "N"  # default to noun for b-class
            elif wc.startswith("t"):
                return "ADJ"
            elif wc.startswith("f"):
                return "V"
            elif wc.startswith("num"):
                return "NUM"
            elif wc == "p" or wc.startswith("jm p") or wc.startswith("p jm"):
                return "PREP"
            elif wc == "l" or wc.startswith("l ") or wc.startswith("jm l"):
                return "CONJ"
            elif wc in ("d", "tabl: d"):
                return "DET"
            elif wc in ("pn", "tabl: pn"):
                return "PRON"
            elif wc == "m" or wc.startswith("tabl: m"):
                return "ADV"
            elif wc in ("par", "f par"):
                return "PAR"
            elif wc == "il":
                return "INTJ"
            elif "lfik" in wc:
                return "PFX"
            elif "xfik" in wc:
                return "SFX"
            elif wc.startswith("su n"):
                return "PROPN"
            elif wc.startswith("su t"):
                return "PROPN"
            break
    return "UNK"


def factorize_glb(sentence):
    """Factored Globasa tokenization: morpheme segmentation + head-final POS.

    1. Run PosTagger to get contextual POS for each word
    2. Segment the SURFACE form (not lemma) into morphemes via segment_word()
    3. Tag only the last morpheme (head) with the resolved POS

    Uses PosTagger for POS disambiguation but segment_word() for decomposition,
    since segment_word() handles the full morpheme inventory (73 prefixes,
    61 suffixes, 4571 explicit decompositions) while PosTagger's lemmatize()
    only strips a small set of affixes.

    Returns list of factored token strings.
    """
    tokens = glb_tokenize(sentence)
    pos_list = assign_pos(tokens)
    morphemes_data = _load_morphemes()

    result = []
    for (surface, lemma, trail), pos in zip(tokens, pos_list):
        # Strip trailing punctuation from surface to get the core word
        core = surface
        if trail and core.endswith(trail):
            core = core[:-len(trail)]
        core = core.lower().strip()

        if not core:
            if trail:
                result.append(trail)
            continue

        # Decompose multi-word tokens (e.g., "fe nunya" → "fe" PREP + "nunya" N)
        # PosTagger joins them for POS disambiguation, but alignment needs them split
        if " " in core:
            mw_parts = core.split()
            for mw_word in mw_parts:
                mw_pos = _infer_pos_from_wordclass(mw_word)
                mw_morphemes = segment_word(mw_word, morphemes_data)
                for j, morph in enumerate(mw_morphemes):
                    if j == len(mw_morphemes) - 1:
                        result.append(f"{morph}|{mw_pos}")
                    else:
                        result.append(morph)
            if trail:
                result.append(trail)
            continue

        # For UNK words, try to resolve POS from WordClass via segment_word
        if pos == "UNK":
            parts = segment_word(core, morphemes_data)
            # If segmentation found morphemes, infer POS from the last morpheme
            if len(parts) > 1:
                last = parts[-1]
                all_words = morphemes_data.get("__all_words__", set())
                if last in all_words:
                    pos = _infer_pos_from_wordclass(last)
            elif core in morphemes_data.get("__all_words__", set()):
                pos = _infer_pos_from_wordclass(core)
        else:
            # Segment the surface form into morphemes
            parts = segment_word(core, morphemes_data)

        # Emit morphemes without POS factors (LEX/FERF/FERR/HMM priors
        # provide POS-like constraints; factoring would prevent priors from
        # matching the corpus tokens).
        for morph in parts:
            result.append(morph)

        # Append trailing punctuation as separate token
        if trail:
            result.append(trail)

    return result


def factorize_target(sentence, lang):
    """Factored target language tokenization via spaCy: lemma|POS.

    Returns list of factored token strings.
    Falls back to plain lowercase tokens if no spaCy model available.
    """
    nlp = _get_spacy(lang)
    if nlp is None:
        # Fallback: whitespace tokenization, preserve case (important for German etc.)
        text = sentence
        text = re.sub(r'([.,:;!?"""()\'—\-])', r' \1 ', text)
        return text.split()

    doc = nlp(sentence)
    result = []
    for token in doc:
        if token.is_punct:
            result.append(token.text)
        else:
            result.append(token.lemma_.lower())
    return result


def defactorize(token):
    """Strip |POS suffix from a factored token."""
    if "|" in token:
        return token.rsplit("|", 1)[0]
    return token


# ---------------------------------------------------------------------------
# Dictionary seeding
# ---------------------------------------------------------------------------

def build_seed_dict(lang2, work_dir):
    """Write a GIZA++ dictionary file from lexical resources.
    Format: source_id target_id (using .vcb vocabulary IDs).
    Must be called after plain2snt has generated .vcb files.
    """
    lang1 = "glb"
    vcb1_path = work_dir / f"{lang1}.vcb"
    vcb2_path = work_dir / f"{lang2}.vcb"

    # Build word→id maps from .vcb files (format: id word count)
    word2id_src = {}
    for line in open(vcb1_path, encoding="utf-8"):
        parts = line.strip().split()
        if len(parts) >= 2:
            word2id_src[parts[1]] = parts[0]

    word2id_tgt = {}
    for line in open(vcb2_path, encoding="utf-8"):
        parts = line.strip().split()
        if len(parts) >= 2:
            word2id_tgt[parts[1]] = parts[0]

    pairs = get_word_pairs(lang2)
    dict_path = work_dir / f"{lang1}_{lang2}.dict"
    written = 0
    with open(dict_path, "w", encoding="utf-8") as f:
        for glb, tgt in pairs:
            src_id = word2id_src.get(glb)
            tgt_id = word2id_tgt.get(tgt)
            if src_id and tgt_id:
                f.write(f"{src_id} {tgt_id}\n")
                written += 1
    print(f"  Dictionary: {written}/{len(pairs)} seed pairs mapped to vocab IDs → {dict_path.name}")
    return dict_path


# ---------------------------------------------------------------------------
# Multi-way concordance (Improvement 5)
# ---------------------------------------------------------------------------

MULTIWAY_CONTEXTS = {"Globatotal Deklaradoku tem Insanli Haki", "Pilpil ji Karote"}


def multiway_concordance(tmx_path):
    """Extract confirmed word pairs from multi-way TUs (UDHR + P&C).

    For each TU with multiple target languages:
    1. Identify Globasa content words (from word-list.csv)
    2. Look up their translations in menalariExtension.tsv
    3. Check if those translations appear in the target sentence
    4. Confirmed matches become high-confidence alignment anchors

    Returns dict of {lang_code: [(glb_word, tgt_word), ...]}
    """
    tree = ET.parse(tmx_path)
    NS_XML = "{http://www.w3.org/XML/1998/namespace}"

    # Build Globasa → {lang: [translations]} from menalari
    menalari = _load_menalari()
    glb_translations = {}  # glb_word → {lang_code: set of target words}
    for row in menalari:
        glb = (row.get("Globasa") or "").strip().lower()
        if not glb:
            continue
        for lang_code, col_name in LANG_TO_MENALARI_COL.items():
            if col_name is None:
                continue
            trans = row.get(col_name) or ""
            words = parse_menalari_gloss(trans)
            if words:
                glb_translations.setdefault(glb, {}).setdefault(lang_code, set()).update(words)

    # Also add word-list translations
    for row in _load_wordlist():
        glb = row.get("Word", "").strip().lower()
        if not glb or glb.startswith("(") or glb.startswith("-"):
            continue
        for lang_code, col_name in LANG_TO_WORDLIST_COL.items():
            trans = row.get(col_name, "")
            words = parse_wordlist_gloss(trans)
            if words:
                glb_translations.setdefault(glb, {}).setdefault(lang_code, set()).update(words)

    confirmed = {}  # lang_code → [(glb, tgt)]
    tu_count = 0

    for tu in tree.getroot().find("body").findall("tu"):
        # Check if this TU is from a multi-way context
        props = {p.get("type"): p.text for p in tu.findall("prop")}
        ctx = props.get("x-context", "")
        if not any(ctx.startswith(c) for c in MULTIWAY_CONTEXTS):
            continue

        # Extract all translations
        texts = {}
        for tuv in tu.findall("tuv"):
            lang = tuv.get(f"{NS_XML}lang")
            seg = tuv.find("seg")
            if seg is not None and seg.text:
                texts[lang] = seg.text.strip()

        if "glb" not in texts:
            continue
        tu_count += 1

        # Tokenize Globasa sentence to get content words
        glb_words = set(texts["glb"].lower().split())

        # For each target language, check concordance
        for lang_code, tgt_text in texts.items():
            if lang_code == "glb":
                continue
            tgt_lower = tgt_text.lower()
            tgt_words = set(tgt_lower.split())

            for glb_word in glb_words:
                if glb_word not in glb_translations:
                    continue
                expected = glb_translations[glb_word].get(lang_code, set())
                for tgt_word in expected:
                    if tgt_word in tgt_words:
                        confirmed.setdefault(lang_code, set()).add((glb_word, tgt_word))

    # Convert sets to lists
    result = {lang: list(pairs) for lang, pairs in confirmed.items()}
    total = sum(len(v) for v in result.values())
    print(f"  Multi-way concordance: {tu_count} TUs → {total} confirmed pairs across {len(result)} languages")
    for lang in sorted(result.keys()):
        print(f"    {lang}: {len(result[lang])} pairs")
    return result


# ---------------------------------------------------------------------------
# SimAlign pivot alignment (Improvement 4)
# ---------------------------------------------------------------------------

def simalign_pivot(tmx_path, glb_en_a3_path):
    """Derive glb↔X word pairs via English pivot using SimAlign.

    1. Extract multi-way TUs (UDHR + P&C) from TMX
    2. Parse existing glb↔en alignment from GIZA++ A3 output
    3. Run SimAlign on en↔X for each target language
    4. Compose: glb→en→X to get glb↔X word pairs

    Returns dict of {lang_code: [(glb_word, tgt_word), ...]}
    """
    from simalign import SentenceAligner
    aligner = SentenceAligner(model="bert-base-multilingual-cased", token_type="bpe")

    tree = ET.parse(tmx_path)
    NS_XML = "{http://www.w3.org/XML/1998/namespace}"

    # Parse glb↔en alignments
    fwd_aligns = parse_a3(glb_en_a3_path)

    # Build sentence index: en_text → alignment_index (for matching TMX to A3)
    en_to_idx = {}
    for idx, (tgt_tokens, src_tokens, align) in enumerate(fwd_aligns):
        en_key = " ".join(tgt_tokens).lower()
        en_to_idx[en_key] = idx

    # Collect multi-way TUs
    result = {}  # lang → set of (glb, tgt) pairs
    tu_count = 0
    aligned_count = 0

    for tu in tree.getroot().find("body").findall("tu"):
        props = {p.get("type"): p.text for p in tu.findall("prop")}
        ctx = props.get("x-context", "")
        if not any(ctx.startswith(c) for c in MULTIWAY_CONTEXTS):
            continue

        texts = {}
        for tuv in tu.findall("tuv"):
            lang = tuv.get(f"{NS_XML}lang")
            seg = tuv.find("seg")
            if seg is not None and seg.text:
                texts[lang] = seg.text.strip()

        if "glb" not in texts or "en" not in texts:
            continue
        tu_count += 1

        # Find matching glb↔en alignment
        en_factored = " ".join(factorize_target(texts["en"], "en")).lower()
        a3_idx = en_to_idx.get(en_factored)
        if a3_idx is None:
            continue
        aligned_count += 1

        tgt_tokens_a3, src_tokens_a3, glb_en_align = fwd_aligns[a3_idx]

        # For each non-English, non-Globasa language
        for lang_code, tgt_text in texts.items():
            if lang_code in ("glb", "en"):
                continue

            # Run SimAlign on en↔X
            en_words = texts["en"].split()
            x_words = tgt_text.split()
            if not en_words or not x_words:
                continue

            try:
                sim_result = aligner.get_word_aligns(en_words, x_words)
                en_x_pairs = sim_result["itermax"]
            except Exception:
                continue

            # Build en_pos → x_pos map
            en_to_x = {}
            for en_pos, x_pos in en_x_pairs:
                en_to_x.setdefault(en_pos, []).append(x_pos)

            # Compose: glb→en→X
            # glb_en_align: src_pos → set of tgt_pos (in factored A3)
            # We need to map A3 target positions (factored en) back to raw en positions
            # Since factored en may differ in tokenization, use string matching
            for src_pos, tgt_positions in glb_en_align.items():
                if src_pos >= len(src_tokens_a3):
                    continue
                glb_word = defactorize(src_tokens_a3[src_pos])
                if not glb_word or glb_word in (".", ",", ";", ":", "!", "?"):
                    continue

                for tgt_pos in tgt_positions:
                    if tgt_pos >= len(tgt_tokens_a3):
                        continue
                    # Find which raw en_word this factored position corresponds to
                    # Use position directly (approximate — factored/raw may differ slightly)
                    if tgt_pos in en_to_x:
                        for x_pos in en_to_x[tgt_pos]:
                            if x_pos < len(x_words):
                                x_word = x_words[x_pos].lower().strip(".,;:!?\"'")
                                if x_word and len(x_word) > 1:
                                    result.setdefault(lang_code, set()).add(
                                        (glb_word, x_word))

    result_lists = {lang: list(pairs) for lang, pairs in result.items()}
    total = sum(len(v) for v in result_lists.values())
    print(f"  SimAlign pivot: {tu_count} TUs, {aligned_count} matched A3, "
          f"{total} derived pairs across {len(result_lists)} languages")
    for lang in sorted(result_lists.keys()):
        print(f"    {lang}: {len(result_lists[lang])} pairs")
    return result_lists


# ---------------------------------------------------------------------------
# GIZA++ pipeline
# ---------------------------------------------------------------------------

def run_giza(lang1, lang2, pairs, work_dir, concordance_pairs=None):
    """Run improved GIZA++ on a language pair with factored tokenization."""
    work_dir.mkdir(parents=True, exist_ok=True)

    # Factorize all sentences
    print("  Factorizing sentences...")
    factored_pairs = []
    glb_vocab = set()
    for s1, s2 in pairs:
        glb_tokens = factorize_glb(s1)
        tgt_tokens = factorize_target(s2, lang2)
        glb_line = " ".join(glb_tokens)
        tgt_line = " ".join(tgt_tokens)
        factored_pairs.append((glb_line, tgt_line))
        glb_vocab.update(defactorize(t) for t in glb_tokens)

    # Write tokenized parallel files
    f1 = work_dir / f"{lang1}.txt"
    f2 = work_dir / f"{lang2}.txt"
    with open(f1, "w") as out1, open(f2, "w") as out2:
        # Real sentences (duplicated 3x to outweigh word pairs)
        for line1, line2 in factored_pairs:
            for _ in range(3):
                out1.write(line1 + "\n")
                out2.write(line2 + "\n")

        # Word-level pairs (only for words in TMX, unfactored)
        # Combine dictionary pairs + concordance-confirmed pairs
        word_pairs = get_word_pairs(lang2)
        conc_pairs = concordance_pairs.get(lang2, []) if concordance_pairs else []
        all_word_pairs = set(word_pairs) | set(conc_pairs)
        wp_count = 0
        for glb, tgt in all_word_pairs:
            if glb in glb_vocab:
                out1.write(glb + "\n")
                out2.write(tgt + "\n")
                wp_count += 1

    total = len(pairs) * 3 + wp_count
    print(f"\n{'='*60}")
    print(f"  {lang1}-{lang2}: {len(pairs)} sentences (×3) + {wp_count} word pairs = {total} lines")
    print(f"{'='*60}")

    # plain2snt
    subprocess.run([str(PLAIN2SNT), str(f1), str(f2)], cwd=str(work_dir),
                   check=True, capture_output=True)

    vcb1 = work_dir / f"{lang1}.vcb"
    vcb2 = work_dir / f"{lang2}.vcb"
    snt12 = work_dir / f"{lang1}_{lang2}.snt"
    snt21 = work_dir / f"{lang2}_{lang1}.snt"

    for src, dst in [
        (work_dir / f"{lang1}.txt.vcb", vcb1),
        (work_dir / f"{lang2}.txt.vcb", vcb2),
        (work_dir / f"{lang1}.txt_{lang2}.txt.snt", snt12),
        (work_dir / f"{lang2}.txt_{lang1}.txt.snt", snt21),
    ]:
        if src.exists() and src != dst:
            src.rename(dst)

    # mkcls
    for lang in [lang1, lang2]:
        subprocess.run(
            [str(MKCLS), "-c50", f"-p{lang}.txt", f"-V{lang}.cls"],
            cwd=str(work_dir), check=True, capture_output=True
        )

    # snt2cooc
    cooc_name = f"{lang1}_{lang2}.cooc"
    with open(work_dir / cooc_name, "w") as cooc_f:
        subprocess.run(
            [str(SNT2COOC), f"{lang1}.vcb", f"{lang2}.vcb", f"{lang1}_{lang2}.snt"],
            cwd=str(work_dir), check=True, stdout=cooc_f
        )

    # Build seed dictionary
    dict_path = build_seed_dict(lang2, work_dir)

    # GIZA++ forward: glb → en
    print("  Running GIZA++ forward...")
    subprocess.run([
        str(GIZA),
        "-S", f"{lang1}.vcb",
        "-T", f"{lang2}.vcb",
        "-C", f"{lang1}_{lang2}.snt",
        "-CoocurrenceFile", cooc_name,
        "-o", f"{lang1}_{lang2}",
        "-outputpath", "./",
        "-dictionary", str(dict_path.name),
    ], cwd=str(work_dir), check=True, capture_output=True)

    # GIZA++ backward: en → glb
    print("  Running GIZA++ backward...")
    cooc_rev = f"{lang2}_{lang1}.cooc"
    with open(work_dir / cooc_rev, "w") as cooc_f:
        subprocess.run(
            [str(SNT2COOC), f"{lang2}.vcb", f"{lang1}.vcb", f"{lang2}_{lang1}.snt"],
            cwd=str(work_dir), check=True, stdout=cooc_f
        )
    subprocess.run([
        str(GIZA),
        "-S", f"{lang2}.vcb",
        "-T", f"{lang1}.vcb",
        "-C", f"{lang2}_{lang1}.snt",
        "-CoocurrenceFile", cooc_rev,
        "-o", f"{lang2}_{lang1}",
        "-outputpath", "./",
    ], cwd=str(work_dir), check=True, capture_output=True)

    # Report forward results
    fwd_files = sorted(work_dir.glob(f"{lang1}_{lang2}.A3.final*"))
    bwd_files = sorted(work_dir.glob(f"{lang2}_{lang1}.A3.final*"))

    if fwd_files:
        print(f"  Forward alignment: {fwd_files[0].name}")
        show_alignments(fwd_files[0], lang1, lang2, n=3)

    t_files = sorted(work_dir.glob(f"{lang1}_{lang2}.t3.final*"))
    if t_files:
        print(f"  T-table: {t_files[0].name}")
        show_top_translations(t_files[0], vcb1, vcb2, n=10)

    # Symmetrize with GDFA
    if fwd_files and bwd_files:
        print("  Symmetrizing (GDFA)...")
        fwd_aligns = parse_a3(fwd_files[0])
        bwd_aligns = parse_a3(bwd_files[0])
        symmetric = gdfa_symmetrize(fwd_aligns, bwd_aligns)

        # Apply function word alignment rules
        print("  Applying function word rules...")
        symmetric, fw_stats = apply_funcword_rules(symmetric)
        print(f"    le→NULL (before passive): {fw_stats['le_fixed']}")
        print(f"    na→to|TO only: {fw_stats['na_fixed']}")
        print(f"    da→NULL (resumptive): {fw_stats['da_nulled']}")
        print(f"    kam→NULL (question): {fw_stats['kam_nulled']}")

        pharaoh_file = work_dir / f"{lang1}_{lang2}.gdfa"
        write_pharaoh(symmetric, pharaoh_file)
        print(f"  Corrected: {pharaoh_file.name} ({len(symmetric)} sentences)")
        show_symmetric_alignments(symmetric, n=5)
    else:
        print("  WARNING: Could not symmetrize — missing alignment files")


# ---------------------------------------------------------------------------
# A3 parsing and GDFA symmetrization
# ---------------------------------------------------------------------------

def parse_a3(a3_file):
    """Parse GIZA++ A3.final into list of (target_tokens, source_tokens, alignment).
    alignment: dict mapping source_pos (0-based) → set of target_pos (0-based).
    In GIZA++ A3 format, source line has: NULL ({...}) word1 ({...}) word2 ({...})
    The numbers in braces are 1-based target positions aligned to that source word.
    """
    lines = open(a3_file).readlines()
    results = []
    for i in range(0, len(lines), 3):
        if i + 2 >= len(lines):
            break
        target_tokens = lines[i + 1].strip().split()
        src_line = lines[i + 2].strip()
        # Parse: NULL ({ 3 7 }) word1 ({ 1 }) word2 ({ 2 4 }) ...
        align = {}
        src_pos = -1  # -1 for NULL
        for token in src_line.split():
            if token == "NULL":
                src_pos = -1
            elif token == "({":
                continue
            elif token == "})":
                src_pos += 1
            else:
                try:
                    tgt_pos = int(token) - 1  # convert 1-based to 0-based
                    if src_pos >= 0:
                        align.setdefault(src_pos, set()).add(tgt_pos)
                except ValueError:
                    # It's a source word
                    pass
        # Re-parse to get clean source tokens
        source_tokens = []
        for token in src_line.split():
            if token in ("NULL", "({", "})"):
                continue
            try:
                int(token)
            except ValueError:
                source_tokens.append(token)
        results.append((target_tokens, source_tokens, align))
    return results


def gdfa_symmetrize(fwd_aligns, bwd_aligns):
    """Grow-diag-final-and symmetrization.
    fwd_aligns: list of (tgt_tokens, src_tokens, src2tgt_dict) from glb→en
    bwd_aligns: list of (src_tokens, tgt_tokens, tgt2src_dict) from en→glb
    Returns: list of (src_tokens, tgt_tokens, set of (src_pos, tgt_pos) pairs)
    """
    results = []
    for idx in range(min(len(fwd_aligns), len(bwd_aligns))):
        tgt_tokens_f, src_tokens_f, fwd = fwd_aligns[idx]
        src_tokens_b, tgt_tokens_b, bwd = bwd_aligns[idx]

        n_src = len(src_tokens_f)
        n_tgt = len(tgt_tokens_f)

        # Convert forward: src→{tgt} to set of (src, tgt) pairs
        fwd_set = set()
        for s, tgts in fwd.items():
            for t in tgts:
                fwd_set.add((s, t))

        # Convert backward: tgt→{src} to set of (src, tgt) pairs
        bwd_set = set()
        for t, srcs in bwd.items():
            for s in srcs:
                bwd_set.add((s, t))

        # Intersection
        alignment = fwd_set & bwd_set
        union = fwd_set | bwd_set

        # Grow: add neighboring points from union
        neighbors = [(-1, 0), (1, 0), (0, -1), (0, 1),
                     (-1, -1), (-1, 1), (1, -1), (1, 1)]
        changed = True
        while changed:
            changed = False
            aligned_src = {s for s, t in alignment}
            aligned_tgt = {t for s, t in alignment}
            for s, t in list(union - alignment):
                if s not in aligned_src or t not in aligned_tgt:
                    for ds, dt in neighbors:
                        ns, nt = s + ds, t + dt
                        if (ns, nt) in alignment:
                            alignment.add((s, t))
                            aligned_src.add(s)
                            aligned_tgt.add(t)
                            changed = True
                            break

        # Final: add remaining unaligned points from union
        aligned_src = {s for s, t in alignment}
        aligned_tgt = {t for s, t in alignment}
        for s, t in fwd_set:
            if s not in aligned_src:
                alignment.add((s, t))
                aligned_src.add(s)
        for s, t in bwd_set:
            if t not in aligned_tgt:
                alignment.add((s, t))
                aligned_tgt.add(t)

        results.append((src_tokens_f, tgt_tokens_f, alignment))
    return results


def write_pharaoh(alignments, output_file):
    """Write alignments in Pharaoh format (i-j pairs per line)."""
    with open(output_file, "w") as f:
        for src_tokens, tgt_tokens, pairs in alignments:
            line = " ".join(f"{s}-{t}" for s, t in sorted(pairs))
            f.write(line + "\n")


# ---------------------------------------------------------------------------
# Function word alignment rules (post-hoc correction)
# ---------------------------------------------------------------------------

def apply_funcword_rules(alignments):
    """Apply deterministic rules to correct function word alignments.

    Operates on GDFA output: list of (src_tokens, tgt_tokens, set of (s,t) pairs).
    Returns corrected alignments (same format).

    Rules:
    1. le|PAR before passive be- → le goes to NULL, be inherits le's target
    2. le|PAR aligned to a content verb → keep (correct: past tense marker)
    3. na|PAR → prefer to|TO; drop links to content words
    4. da|PRON (resumptive) → NULL (no English equivalent)
    5. kam|PAR (question marker) → NULL
    6. hay|V → prefer there|EX; also link to be|VBD/VBZ
    """
    corrected = []
    stats = {"le_fixed": 0, "na_fixed": 0, "da_nulled": 0, "kam_nulled": 0}

    for src_tokens, tgt_tokens, pairs in alignments:
        new_pairs = set(pairs)

        # Build lookup: src_pos → set of tgt_pos
        src_to_tgt = {}
        for s, t in pairs:
            src_to_tgt.setdefault(s, set()).add(t)

        for s_pos in range(len(src_tokens)):
            stok = src_tokens[s_pos]

            # Rule 1: le before passive be- → transfer le's target to be
            if stok == "le" and s_pos + 1 < len(src_tokens):
                if src_tokens[s_pos + 1] == "be-":
                    le_targets = src_to_tgt.get(s_pos, set())
                    for t in list(le_targets):
                        new_pairs.discard((s_pos, t))
                        new_pairs.add((s_pos + 1, t))
                    stats["le_fixed"] += 1

            # Rule 2: na — keep only links to "to" (English infinitive marker)
            if stok == "na":
                na_targets = src_to_tgt.get(s_pos, set())
                has_to = any(
                    t < len(tgt_tokens) and tgt_tokens[t] == "to"
                    for t in na_targets
                )
                if has_to:
                    for t in list(na_targets):
                        if t < len(tgt_tokens) and tgt_tokens[t] != "to":
                            new_pairs.discard((s_pos, t))
                            stats["na_fixed"] += 1

            # Rule 3: da (resumptive pronoun) → NULL
            if stok == "da":
                for t in list(src_to_tgt.get(s_pos, set())):
                    new_pairs.discard((s_pos, t))
                stats["da_nulled"] += 1

            # Rule 4: kam (question marker) → NULL
            if stok == "kam":
                for t in list(src_to_tgt.get(s_pos, set())):
                    new_pairs.discard((s_pos, t))
                stats["kam_nulled"] += 1

        corrected.append((src_tokens, tgt_tokens, new_pairs))

    return corrected, stats


def show_symmetric_alignments(alignments, n=5):
    """Display symmetrized alignments with many-to-many links."""
    print(f"\n  Symmetrized alignments (GDFA):")
    for src_tokens, tgt_tokens, pairs in alignments[:n]:
        # Build tgt_pos → [src words] map
        tgt_to_src = {}
        for s, t in pairs:
            tgt_to_src.setdefault(t, []).append(s)
        print(f"    TGT: {' '.join(tgt_tokens)}")
        print(f"    SRC: {' '.join(src_tokens)}")
        links = []
        for t_pos in sorted(tgt_to_src.keys()):
            src_words = [src_tokens[s] for s in sorted(tgt_to_src[t_pos]) if s < len(src_tokens)]
            tgt_word = tgt_tokens[t_pos] if t_pos < len(tgt_tokens) else "?"
            if src_words:
                links.append(f"{'+'.join(src_words)}↔{tgt_word}")
        print(f"    Links: {', '.join(links)}")
        print()


def show_alignments(a3_file, lang1, lang2, n=5):
    """Display n sample alignments from GIZA++ A3 output."""
    print(f"\n  Sample alignments ({lang1} → {lang2}):")
    lines = open(a3_file).readlines()
    count = 0
    for i in range(0, len(lines), 3):
        if count >= n or i + 2 >= len(lines):
            break
        target = lines[i + 1].strip()
        source_aligned = lines[i + 2].strip()
        print(f"    {lang2}: {target}")
        print(f"    {lang1}: {source_aligned}")
        print()
        count += 1


def show_top_translations(t_file, vcb1_file, vcb2_file, n=15):
    """Show top translation pairs from the t-table."""
    vcb1 = {}
    for line in open(vcb1_file):
        parts = line.strip().split()
        if len(parts) >= 2:
            vcb1[parts[0]] = parts[1]

    vcb2 = {}
    for line in open(vcb2_file):
        parts = line.strip().split()
        if len(parts) >= 2:
            vcb2[parts[0]] = parts[1]

    top_pairs = []
    for line in open(t_file):
        parts = line.strip().split()
        if len(parts) >= 3:
            src_id, tgt_id, prob = parts[0], parts[1], float(parts[2])
            src_word = vcb1.get(src_id, f"?{src_id}")
            tgt_word = vcb2.get(tgt_id, f"?{tgt_id}")
            if src_word != "NULL" and tgt_word != "NULL" and prob > 0.3:
                top_pairs.append((src_word, tgt_word, prob))

    top_pairs.sort(key=lambda x: -x[2])
    print(f"\n  Top translation pairs (p > 0.3):")
    for src, tgt, prob in top_pairs[:n]:
        print(f"    {src:20s} → {tgt:20s}  ({prob:.3f})")


# ---------------------------------------------------------------------------
# eflomal aligner (alternative to GIZA++)
# ---------------------------------------------------------------------------

def _build_eflomal_priors(lang2, priors_file, word_pairs):
    """Build Dirichlet priors file for eflomal from lexical resources.

    Priors format (one per line):
        LEX  src_word  tgt_word  alpha   — lexical translation prior
        FERF src_word  fertility alpha   — forward fertility prior
        FERR tgt_word  fertility alpha   — reverse fertility prior
        HMMF jump      alpha             — forward HMM distortion prior
        HMMR jump      alpha             — reverse HMM distortion prior

    Sources:
    1. Dictionary word pairs (word-list + menalari + concordance) → LEX priors
    2. Function word fertility knowledge → FERF priors
    3. Language-specific word order knowledge → HMMF/HMMR distortion priors
    """
    lex_count = 0
    fert_count = 0
    hmm_count = 0

    with open(priors_file, "w") as f:
        # LEX priors from dictionary pairs
        seen = set()
        for glb, tgt in word_pairs:
            key = (glb, tgt)
            if key not in seen:
                seen.add(key)
                f.write(f"LEX\t{glb}\t{tgt}\t1.0\n")
                lex_count += 1

        # Decomposition LEX priors:
        # When a Globasa derived word (e.g., huruya) maps to a target word
        # (e.g., "freedom"), distribute the LEX evidence to BOTH the root
        # (huru) AND the affix marker (-ya). Use HIGH alpha (2.0) so this
        # overcomes the bare-root direct LEX prior (e.g., huru → "free")
        # and forces both root and affix to compete for the derived-form
        # target, producing many-to-one alignment.
        morphemes_data = _load_morphemes()
        decomp_count = 0
        decomp_seen = set()
        for glb, tgt in list(seen):
            parts = segment_word(glb, morphemes_data)
            if len(parts) >= 2:
                has_affix = any(p.startswith("-") or p.endswith("-") for p in parts)
                if has_affix:
                    for part in parts:
                        key = (part, tgt)
                        if key not in seen and key not in decomp_seen:
                            decomp_seen.add(key)
                            f.write(f"LEX\t{part}\t{tgt}\t2.0\n")
                            decomp_count += 1
        lex_count += decomp_count

        # Function word fertility priors (Globasa-specific)
        funcword_fert = {
            "le": [(0, 5.0), (1, 1.0)],
            "xa": [(0, 3.0), (1, 2.0)],
            "nun": [(0, 5.0)],
            "am": [(0, 5.0)],
            "ger": [(0, 5.0)],
            "da": [(0, 10.0)],
            "kam": [(0, 10.0)],
            "na": [(1, 5.0)],
            "cel": [(1, 5.0)],
            "fe": [(1, 3.0), (0, 2.0)],
            "be-": [(1, 5.0)],
            # Derivational suffixes: strongly encourage fertility 1 so the
            # suffix aligns to the same target word as its root (e.g., huruya
            # → "freedom" with both huru and -ya linking to "freedom").
            # In some languages (-li ↔ "de" / "of" in possessive constructions)
            # the suffix may align to a separate word; in others, it merges
            # with the root in the target translation.
            "-li": [(1, 6.0), (0, 1.0)],   # strong fertility 1 (merge or → "of")
            "-ya": [(1, 8.0), (0, 0.5)],   # very strong fertility 1 (merge w/ root)
            "-do": [(1, 6.0), (0, 1.0)],   # passive participle (merges)
            "-ne": [(1, 6.0), (0, 1.0)],   # agent suffix (merges or → "-er"/"-ing")
            "-mo": [(1, 5.0), (0, 1.0)],   # adverb suffix (merges or → "-ly")
            "-cu": [(1, 5.0), (0, 1.0)],   # become suffix (merges or → "become")
            "-gi": [(1, 5.0), (0, 1.0)],   # causative (merges or → "make")
            "-pul": [(1, 6.0), (0, 1.0)],  # -ful (merges with root, e.g., jiwapul ↔ "vibrant")
            "-abil": [(1, 6.0), (0, 1.0)], # -able (typically merges)
            "-fil": [(1, 5.0), (0, 1.0)],  # -prone (merges)
            "-kal": [(1, 5.0), (0, 1.0)],  # -less (merges)
            # Existential/locative verbs: often map to multi-word English
            # constructions like "there is/are/was" + content, hence
            # fertility 2 is plausible (many-to-one alignment).
            "hay": [(2, 4.0), (1, 2.0), (0, 0.5)],  # existential: "there is/are"
            "ogar": [(2, 3.0), (1, 3.0), (0, 1.0)], # live/dwell, esp. "there was X"
            "loka": [(2, 2.0), (1, 3.0), (0, 1.0)], # be located, esp. existential
        }

        for word, ferts in funcword_fert.items():
            for fertility, alpha in ferts:
                f.write(f"FERF\t{word}\t{fertility}\t{alpha}\n")
                fert_count += 1

        # Existential LEX priors: words that often align to "there be" in English
        # (Globasa has lexical existentials, not "there is/are" syntax)
        existential_priors = {
            "en": {
                "hay": [("there", 10.0), ("be", 5.0), ("is", 3.0), ("are", 3.0)],
                "ogar": [("there", 5.0), ("be", 4.0), ("live", 3.0), ("dwell", 2.0)],
                "loka": [("there", 5.0), ("be", 4.0), ("locate", 3.0)],
            },
            "de": {
                "hay": [("es", 3.0), ("geben", 4.0), ("gibt", 3.0)],
                "ogar": [("leben", 2.0), ("wohnen", 2.0), ("es", 1.5)],
                "loka": [("liegen", 2.0), ("befinden", 2.0)],
            },
            "fr": {
                "hay": [("il", 3.0), ("y", 4.0), ("avoir", 3.0)],
                "ogar": [("vivre", 2.0), ("habiter", 2.0)],
                "loka": [("se", 2.0), ("trouver", 2.0), ("situer", 2.0)],
            },
            "es": {
                "hay": [("haber", 4.0), ("hay", 3.0), ("existir", 2.0)],
                "ogar": [("vivir", 2.0), ("habitar", 2.0)],
                "loka": [("ubicar", 2.0), ("encontrar", 2.0)],
            },
            "ru": {
                "hay": [("есть", 4.0), ("быть", 2.0)],
            },
        }
        ex_priors = existential_priors.get(lang2, {})
        for src, tgts in ex_priors.items():
            for tgt, alpha in tgts:
                key = (src, tgt)
                if key not in seen and key not in decomp_seen:
                    f.write(f"LEX\t{src}\t{tgt}\t{alpha}\n")
                    lex_count += 1

        # Target-side article fertility priors (FERR)
        # Articles in European languages typically have NO Globasa counterpart
        # (Globasa has no definite/indefinite articles). Exception: hin (this/the
        # demonstrative), den (as/like). So articles → fertility 0 (NULL alignment).
        article_fert = _get_article_fertility_priors(lang2)
        for word, ferts in article_fert.items():
            for fertility, alpha in ferts:
                f.write(f"FERR\t{word}\t{fertility}\t{alpha}\n")
                fert_count += 1

        # HMM distortion priors (language-pair-specific word order)
        # HMMF jump alpha: forward direction (glb→tgt)
        #   jump = difference in target position between consecutive source words
        #   Positive jump = target word is to the right (monotone)
        #   Negative jump = target word is to the left (reordering)
        #
        # Globasa is SVO. Distortion depends on target language word order.

        hmm_priors = _get_distortion_priors(lang2)
        for jump, alpha in hmm_priors["hmmf"].items():
            f.write(f"HMMF\t{jump}\t{alpha}\n")
            hmm_count += 1
        for jump, alpha in hmm_priors["hmmr"].items():
            f.write(f"HMMR\t{jump}\t{alpha}\n")
            hmm_count += 1

    print(f"  Built priors: {lex_count} LEX + {fert_count} FERF + {hmm_count} HMM")


# Language-specific distortion patterns relative to Globasa SVO
_DISTORTION_PROFILES = {
    # SVO + Adj-N: English, Danish (monotone, adjective before noun like Globasa)
    "svo": {
        "hmmf": {1: 10.0, 2: 3.0, -1: 2.0, 0: 1.0, 3: 1.0, -2: 1.0},
        "hmmr": {1: 10.0, 2: 3.0, -1: 2.0, 0: 1.0, 3: 1.0, -2: 1.0},
    },
    # German V2/V-final + Adj-N (adjective order matches Globasa)
    # Verb can jump to end in subordinate clauses
    # Separable verb prefixes cause backward jumps
    # Adverbs before verb in subclauses (matches Globasa)
    "de": {
        "hmmf": {
            1: 8.0,    # monotone (most common)
            2: 3.0,    # small forward skip
            -1: 3.0,   # German article before noun where Globasa has none
            0: 1.5,    # same position (1-to-many)
            3: 2.0,    # medium forward skip
            -2: 2.0,   # separable prefix or reordering
            4: 1.5,    # larger forward (verb to end in subclause)
            5: 1.0,
            6: 1.0,    # long jump (verb-final in long subordinate clause)
            -3: 1.0,   # backward jump (German compound split)
        },
        "hmmr": {
            1: 8.0, 2: 3.0, -1: 3.0, 0: 1.5, 3: 2.0, -2: 2.0,
            4: 1.5, 5: 1.0, 6: 1.0, -3: 1.0,
        },
    },
    # Turkish SOV: verb systematically at end of clause
    # Globasa SVO → Turkish SOV means:
    #   S maps near start (monotone), V jumps to end, O stays in middle
    # Postpositions: Globasa "in X" → Turkish "X-de" (prep follows noun)
    # Agglutination: one Turkish word may cover multiple Globasa words
    "tr": {
        "hmmf": {
            1: 6.0,    # monotone (adj-noun, within noun phrases)
            2: 3.0,    # small forward skip
            -1: 4.0,   # backward jump (very common: SOV reordering)
            0: 2.0,    # same position (agglutinative: multiple→one)
            -2: 3.0,   # medium backward (verb skipping object)
            3: 2.0,    # forward skip
            -3: 2.0,   # larger backward
            -4: 1.5,   # verb from position 2 to end
            -5: 1.0,
            4: 1.5,
            5: 1.0,    # postposition follows noun
        },
        "hmmr": {
            1: 6.0, 2: 3.0, -1: 4.0, 0: 2.0, -2: 3.0, 3: 2.0,
            -3: 2.0, -4: 1.5, -5: 1.0, 4: 1.5, 5: 1.0,
        },
    },
    # Arabic VSO + N-Adj: verb-initial, adjective after noun
    # Globasa SVO → Arabic VSO: V jumps left, S jumps right
    # Globasa Adj-N → Arabic N-Adj: adjective swaps to after noun
    # Also: zero copula, articles fused as al-, adverbs after verb
    "ar": {
        "hmmf": {
            1: 5.0,    # monotone (within phrases)
            -1: 6.0,   # backward (VSO + N-Adj: both cause backward jumps)
            2: 3.0,    # forward skip (S jumps past V)
            0: 2.0,    # same position (proclitic fusion)
            -2: 4.0,   # medium backward (VSO + N-Adj compound)
            3: 2.0,    # medium forward
            -3: 2.0,   # larger backward
            4: 1.5,
            -4: 1.5,
            5: 1.0,
            -5: 1.0,
        },
        "hmmr": {
            1: 5.0, -1: 6.0, 2: 3.0, 0: 2.0, -2: 4.0, 3: 2.0,
            -3: 2.0, 4: 1.5, -4: 1.5, 5: 1.0, -5: 1.0,
        },
    },
    # Russian: flexible SVO + Adj-N (adjective order matches Globasa)
    # No articles → Globasa determiners map to NULL
    # Rich case morphology → frequent SOV/OVS scrambling
    # Adverbs flexible (before or after verb)
    "ru": {
        "hmmf": {
            1: 7.0,    # monotone (SVO default)
            -1: 4.0,   # backward (OVS, topic fronting)
            2: 3.0,    # forward skip
            0: 2.0,    # same position
            -2: 3.0,   # medium backward (flexible order)
            3: 2.0,
            -3: 1.5,   # larger backward (scrambling)
            4: 1.5,
            -4: 1.0,
            5: 1.0,
        },
        "hmmr": {
            1: 7.0, -1: 4.0, 2: 3.0, 0: 2.0, -2: 3.0, 3: 2.0,
            -3: 1.5, 4: 1.5, -4: 1.0, 5: 1.0,
        },
    },
    # Dutch: V2/V-final (like German) + Adj-N (matches Globasa)
    # Very similar to German profile
    "nl": {
        "hmmf": {
            1: 8.0,    # monotone
            2: 3.0,    # small forward
            -1: 3.0,   # article/determiner reordering
            0: 1.5,    # same position
            3: 2.0,    # medium forward
            -2: 2.0,   # separable verb / reordering
            4: 1.5,    # verb-final in subclause
            5: 1.0,
            6: 1.0,
            -3: 1.0,
        },
        "hmmr": {
            1: 8.0, 2: 3.0, -1: 3.0, 0: 1.5, 3: 2.0, -2: 2.0,
            4: 1.5, 5: 1.0, 6: 1.0, -3: 1.0,
        },
    },
    # Chinese: SVO but relative clauses precede noun (head-final for RC)
    # No inflection → 1-to-1 word mapping more common
    # Topic-comment structure → topic can front
    "zh": {
        "hmmf": {
            1: 8.0,    # monotone (SVO)
            -1: 3.0,   # backward (RC precedes noun, topic fronting)
            2: 3.0,    # forward skip
            0: 2.0,    # same position (no inflection, classifiers)
            -2: 2.0,   # relative clause reordering
            3: 1.5,
            -3: 1.5,   # longer RC
            4: 1.0,
            -4: 1.0,
        },
        "hmmr": {
            1: 8.0, -1: 3.0, 2: 3.0, 0: 2.0, -2: 2.0, 3: 1.5,
            -3: 1.5, 4: 1.0, -4: 1.0,
        },
    },
    # Hindi: SOV, postpositions, head-final
    # Like Turkish but less agglutinative, more analytic
    # Compound verbs (light verb constructions): "kaam karna" = work do
    "hi": {
        "hmmf": {
            1: 6.0,    # monotone (within NP)
            -1: 4.0,   # backward (SOV)
            2: 3.0,    # forward skip
            0: 2.5,    # same position (compound verbs, postpositions)
            -2: 3.0,   # verb past object
            3: 2.0,
            -3: 2.0,
            -4: 1.5,
            4: 1.5,
            -5: 1.0,
            5: 1.0,
        },
        "hmmr": {
            1: 6.0, -1: 4.0, 2: 3.0, 0: 2.5, -2: 3.0, 3: 2.0,
            -3: 2.0, -4: 1.5, 4: 1.5, -5: 1.0, 5: 1.0,
        },
    },
    # Japanese: strictly SOV, head-final, postpositions, particles
    # Very different from Globasa SVO — large reordering
    # Verb always final, modifiers always precede head
    "ja": {
        "hmmf": {
            1: 5.0,    # monotone (within phrases)
            -1: 5.0,   # backward (very frequent: head-final)
            0: 3.0,    # same position (particles, agglutination)
            -2: 4.0,   # medium backward (verb to end)
            2: 2.5,    # forward skip
            -3: 3.0,   # larger backward
            -4: 2.0,
            3: 2.0,
            -5: 1.5,
            -6: 1.0,   # very long backward (verb in long sentence)
            4: 1.0,
            5: 1.0,
        },
        "hmmr": {
            1: 5.0, -1: 5.0, 0: 3.0, -2: 4.0, 2: 2.5, -3: 3.0,
            -4: 2.0, 3: 2.0, -5: 1.5, -6: 1.0, 4: 1.0, 5: 1.0,
        },
    },
    # Korean: SOV, head-final, postpositions (similar to Japanese)
    "ko": {
        "hmmf": {
            1: 5.0, -1: 5.0, 0: 3.0, -2: 4.0, 2: 2.5, -3: 3.0,
            -4: 2.0, 3: 2.0, -5: 1.5, -6: 1.0, 4: 1.0, 5: 1.0,
        },
        "hmmr": {
            1: 5.0, -1: 5.0, 0: 3.0, -2: 4.0, 2: 2.5, -3: 3.0,
            -4: 2.0, 3: 2.0, -5: 1.5, -6: 1.0, 4: 1.0, 5: 1.0,
        },
    },
    # Esperanto: SVO, Adj-N (like Globasa), very regular
    # Accusative -n allows some flexibility but SVO + Adj-N strongly dominant
    "eo": {
        "hmmf": {1: 12.0, 2: 3.0, -1: 1.5, 0: 1.0, 3: 1.0, -2: 0.5},
        "hmmr": {1: 12.0, 2: 3.0, -1: 1.5, 0: 1.0, 3: 1.0, -2: 0.5},
    },
    # French: SVO + N-Adj (noun before adjective, opposite of Globasa Adj-N)
    # Globasa "bon kitabu" → French "bon livre" (short adj before) BUT
    # Globasa "day kitabu" → French "livre grand" (most adj after)
    # Adverbs typically follow verb: Globasa "velosi doxo" → French "lire vite"
    "fr": {
        "hmmf": {
            1: 7.0,    # monotone (SVO matches)
            -1: 5.0,   # backward (N-Adj swap: adj follows noun)
            2: 3.0,    # forward skip
            0: 1.5,    # same position
            -2: 2.0,   # larger backward (adj + adverb reordering)
            3: 1.5,
            -3: 1.0,
            4: 1.0,
        },
        "hmmr": {
            1: 7.0, -1: 5.0, 2: 3.0, 0: 1.5, -2: 2.0, 3: 1.5,
            -3: 1.0, 4: 1.0,
        },
    },
    # Spanish: SVO + N-Adj (like French, most adjectives after noun)
    # Adverbs flexible but often after verb
    "es": {
        "hmmf": {
            1: 7.0,    # monotone (SVO matches)
            -1: 5.0,   # backward (N-Adj swap)
            2: 3.0,    # forward skip
            0: 1.5,    # same position
            -2: 2.0,   # larger backward
            3: 1.5,
            -3: 1.0,
            4: 1.0,
        },
        "hmmr": {
            1: 7.0, -1: 5.0, 2: 3.0, 0: 1.5, -2: 2.0, 3: 1.5,
            -3: 1.0, 4: 1.0,
        },
    },
    # Portuguese: SVO + N-Adj (like Spanish/French)
    "pt": {
        "hmmf": {
            1: 7.0, -1: 5.0, 2: 3.0, 0: 1.5, -2: 2.0, 3: 1.5,
            -3: 1.0, 4: 1.0,
        },
        "hmmr": {
            1: 7.0, -1: 5.0, 2: 3.0, 0: 1.5, -2: 2.0, 3: 1.5,
            -3: 1.0, 4: 1.0,
        },
    },
    # Indonesian: SVO + N-Adj (adjective follows noun: "buku besar" = book big)
    # Analytic like Globasa but opposite adjective order
    # Also: possessor follows head ("rumah saya" = house my)
    "id": {
        "hmmf": {
            1: 8.0,    # monotone (SVO, analytic)
            -1: 4.0,   # backward (N-Adj swap, possessor after head)
            2: 3.0,
            0: 1.5,    # same position (analytic, no inflection)
            -2: 2.0,
            3: 1.0,
        },
        "hmmr": {
            1: 8.0, -1: 4.0, 2: 3.0, 0: 1.5, -2: 2.0, 3: 1.0,
        },
    },
    # Swahili: SVO + N-Adj (adjective follows noun)
    # Noun class agreement prefixes on adjectives
    # Adverbs typically follow verb
    "sw": {
        "hmmf": {
            1: 7.0,    # monotone (SVO)
            -1: 4.0,   # backward (N-Adj, verb-initial in some constructions)
            2: 3.0,
            0: 2.0,    # same position (noun class prefixes → multiple:one)
            -2: 2.0,
            3: 1.5,
            -3: 1.0,
            4: 1.0,
        },
        "hmmr": {
            1: 7.0, -1: 4.0, 2: 3.0, 0: 2.0, -2: 2.0, 3: 1.5,
            -3: 1.0, 4: 1.0,
        },
    },
}

# Map language codes to distortion profiles
_LANG_TO_PROFILE = {
    # Adj-N + SVO (monotone, matches Globasa closely)
    "en": "svo", "da": "svo",
    # Adj-N + SVO, very regular
    "eo": "eo",
    # N-Adj + SVO (adjective after noun, unlike Globasa)
    "fr": "fr", "es": "es", "pt": "pt",
    "id": "id", "sw": "sw",
    # Adj-N + V2/V-final
    "de": "de", "nl": "nl",
    # Adj-N + flexible SVO
    "ru": "ru",
    # N-Adj + VSO
    "ar": "ar",
    # SVO + head-final RC
    "zh": "zh",
    # SOV + Adj-N + postpositions
    "tr": "tr", "hi": "hi",
    # SOV + Adj-N + head-final (strictest reordering)
    "ja": "ja", "ko": "ko",
}


def _get_distortion_priors(lang2):
    """Get HMM distortion priors for a language pair."""
    profile_key = _LANG_TO_PROFILE.get(lang2, "svo")
    return _DISTORTION_PROFILES.get(profile_key, _DISTORTION_PROFILES["svo"])


# Target-side article fertility priors (factored as lemma|POS to match spaCy output)
# Globasa has no articles, so articles in European languages typically map to NULL
# (fertility 0). Exception: definite article often corresponds to demonstrative
# `hin` ("this") and `den` (~"as"/"like"), so we allow some fertility-1 mass.
_ARTICLE_FERTILITY_PRIORS = {
    "en": {
        "the": [(0, 5.0), (1, 1.0)],   # mostly NULL, sometimes ↔ hin
        "a": [(0, 8.0), (1, 0.5)],     # almost always NULL
        "an": [(0, 8.0), (1, 0.5)],
    },
    "de": {
        "der": [(0, 5.0), (1, 1.0)],
        "die": [(0, 5.0), (1, 1.0)],
        "das": [(0, 5.0), (1, 1.0)],
        "den": [(0, 5.0), (1, 1.0)],
        "dem": [(0, 5.0), (1, 1.0)],
        "des": [(0, 5.0), (1, 1.0)],
        "ein": [(0, 8.0), (1, 0.5)],
        "eine": [(0, 8.0), (1, 0.5)],
        "einer": [(0, 8.0), (1, 0.5)],
        "eines": [(0, 8.0), (1, 0.5)],
        "einem": [(0, 8.0), (1, 0.5)],
        "einen": [(0, 8.0), (1, 0.5)],
    },
    "fr": {
        "le": [(0, 5.0), (1, 1.0)],
        "la": [(0, 5.0), (1, 1.0)],
        "les": [(0, 5.0), (1, 1.0)],
        "l'": [(0, 5.0), (1, 1.0)],
        "un": [(0, 8.0), (1, 0.5)],
        "une": [(0, 8.0), (1, 0.5)],
        "du": [(0, 5.0), (1, 1.0)],
    },
    "es": {
        "el": [(0, 5.0), (1, 1.0)],
        "la": [(0, 5.0), (1, 1.0)],
        "los": [(0, 5.0), (1, 1.0)],
        "las": [(0, 5.0), (1, 1.0)],
        "un": [(0, 8.0), (1, 0.5)],
        "una": [(0, 8.0), (1, 0.5)],
        "unos": [(0, 8.0), (1, 0.5)],
        "unas": [(0, 8.0), (1, 0.5)],
    },
    "pt": {
        "o": [(0, 5.0), (1, 1.0)],
        "os": [(0, 5.0), (1, 1.0)],
        "as": [(0, 5.0), (1, 1.0)],
        "um": [(0, 8.0), (1, 0.5)],
        "uma": [(0, 8.0), (1, 0.5)],
    },
    "nl": {
        "de": [(0, 5.0), (1, 1.0)],
        "het": [(0, 5.0), (1, 1.0)],
        "een": [(0, 8.0), (1, 0.5)],
    },
    # Esperanto: definite article only (no indefinite)
    "eo": {
        "la": [(0, 5.0), (1, 1.0)],
    },
    # Italian
    "it": {
        "il": [(0, 5.0), (1, 1.0)],
        "lo": [(0, 5.0), (1, 1.0)],
        "i": [(0, 5.0), (1, 1.0)],
    },
    # Danish: definite article is a suffix, indefinite is "en"/"et"
    "da": {
        "en": [(0, 8.0), (1, 0.5)],
        "et": [(0, 8.0), (1, 0.5)],
    },
    # Russian, Mandarin, Indonesian, Swahili, Arabic, Hindi, Turkish: no
    # standalone articles, so no FERR priors needed
}


def _get_article_fertility_priors(lang2):
    """Get target-side article fertility priors (FERR) for a language."""
    return _ARTICLE_FERTILITY_PRIORS.get(lang2, {})


def run_eflomal(lang1, lang2, pairs, work_dir, concordance_pairs=None):
    """Run eflomal alignment with factored tokenization.

    Uses the same preprocessing as run_giza (factorized tokens, word pair
    augmentation) but replaces GIZA++ with eflomal's Bayesian HMM+fertility
    model. Natively outputs both directions; symmetrized with atools grow-diag.
    """
    import eflomal
    from tempfile import NamedTemporaryFile

    work_dir.mkdir(parents=True, exist_ok=True)

    # Factorize all sentences
    print("  Factorizing sentences...")
    factored_pairs = []
    glb_vocab = set()
    for s1, s2 in pairs:
        glb_tokens = factorize_glb(s1)
        tgt_tokens = factorize_target(s2, lang2)
        glb_line = " ".join(glb_tokens)
        tgt_line = " ".join(tgt_tokens)
        factored_pairs.append((glb_line, tgt_line))
        glb_vocab.update(defactorize(t) for t in glb_tokens)

    # Prepare corpus: sentences (no duplication — eflomal handles small corpora)
    # + word-level pairs
    word_pairs = get_word_pairs(lang2)
    conc_pairs = concordance_pairs.get(lang2, []) if concordance_pairs else []
    all_word_pairs = set(word_pairs) | set(conc_pairs)

    src_lines = []
    tgt_lines = []
    sent_count = 0
    for glb_line, tgt_line in factored_pairs:
        if glb_line.strip() and tgt_line.strip():
            src_lines.append(glb_line)
            tgt_lines.append(tgt_line)
            sent_count += 1
    wp_count = 0
    for glb, tgt in all_word_pairs:
        if glb in glb_vocab and glb.strip() and tgt.strip():
            src_lines.append(glb)
            tgt_lines.append(tgt)
            wp_count += 1

    print(f"\n{'='*60}")
    print(f"  {lang1}-{lang2} (eflomal): {len(pairs)} sentences + {wp_count} word pairs = {len(src_lines)} lines")
    print(f"{'='*60}")

    # Write to temp files
    src_file = work_dir / f"{lang1}.txt"
    tgt_file = work_dir / f"{lang2}.txt"
    fwd_file = work_dir / f"{lang1}_{lang2}.fwd"
    rev_file = work_dir / f"{lang1}_{lang2}.rev"

    with open(src_file, "w") as f:
        f.write("\n".join(src_lines) + "\n")
    with open(tgt_file, "w") as f:
        f.write("\n".join(tgt_lines) + "\n")

    # Build Dirichlet priors from lexical resources
    priors_file = work_dir / f"{lang1}_{lang2}.priors"
    _build_eflomal_priors(lang2, priors_file, all_word_pairs)
    print(f"  Priors: {priors_file.name}")

    # Run eflomal with priors
    aligner = eflomal.Aligner(model=3, n_samplers=3)
    with open(src_file) as sf, open(tgt_file) as tf, open(priors_file) as pf:
        aligner.align(
            sf, tf,
            links_filename_fwd=str(fwd_file),
            links_filename_rev=str(rev_file),
            priors_input=pf,
        )

    # Read Pharaoh-format alignments
    fwd_links = open(fwd_file).readlines()
    rev_links = open(rev_file).readlines()

    # Symmetrize (grow-diag-final-and on Pharaoh links)
    alignments = []
    for i in range(min(len(src_lines), len(fwd_links), len(rev_links))):
        src_tokens = src_lines[i].split()
        tgt_tokens = tgt_lines[i].split()

        def parse_pharaoh(line):
            pairs_set = set()
            for pair in line.strip().split():
                if "-" in pair:
                    s, t = pair.split("-", 1)
                    pairs_set.add((int(s), int(t)))
            return pairs_set

        fwd_set = parse_pharaoh(fwd_links[i])
        rev_set = parse_pharaoh(rev_links[i])

        # GDFA symmetrization
        alignment = fwd_set & rev_set
        union = fwd_set | rev_set
        neighbors = [(-1, 0), (1, 0), (0, -1), (0, 1),
                     (-1, -1), (-1, 1), (1, -1), (1, 1)]
        changed = True
        while changed:
            changed = False
            aligned_src = {s for s, t in alignment}
            aligned_tgt = {t for s, t in alignment}
            for s, t in list(union - alignment):
                if s not in aligned_src or t not in aligned_tgt:
                    for ds, dt in neighbors:
                        if (s + ds, t + dt) in alignment:
                            alignment.add((s, t))
                            changed = True
                            break
        aligned_src = {s for s, t in alignment}
        aligned_tgt = {t for s, t in alignment}
        for s, t in fwd_set:
            if s not in aligned_src:
                alignment.add((s, t))
        for s, t in rev_set:
            if t not in aligned_tgt:
                alignment.add((s, t))

        alignments.append((src_tokens, tgt_tokens, alignment))

    # Apply function word rules (only on sentence alignments, not word pairs)
    sentence_alignments = alignments[:sent_count]
    sentence_alignments, fw_stats = apply_funcword_rules(sentence_alignments)
    print(f"  Function word corrections:")
    print(f"    le→NULL (before passive): {fw_stats['le_fixed']}")
    print(f"    da→NULL (resumptive): {fw_stats['da_nulled']}")
    print(f"    kam→NULL (question): {fw_stats['kam_nulled']}")

    # Write final Pharaoh output
    gdfa_file = work_dir / f"{lang1}_{lang2}.gdfa"
    write_pharaoh(sentence_alignments, gdfa_file)
    print(f"  Output: {gdfa_file.name} ({len(sentence_alignments)} sentences)")

    # Show samples
    show_symmetric_alignments(sentence_alignments, n=5)

    return sentence_alignments


if __name__ == "__main__":
    import sys
    OUT_DIR.mkdir(exist_ok=True)

    # Choose aligner: --eflomal or default GIZA++
    use_eflomal = "--eflomal" in sys.argv

    # Compute multi-way concordance once for all language pairs
    print("Computing multi-way concordance...")
    conc = multiway_concordance(TMX_FILE)

    target_langs = ["en", "eo", "es", "de", "fr", "ru", "nl", "pt", "id",
                    "da", "ar", "hi", "sw", "tr", "zh"]
    for l2 in target_langs:
        l1 = "glb"
        pairs = extract_parallel(TMX_FILE, l1, l2)
        if len(pairs) < 10:
            print(f"SKIP {l1}-{l2}: only {len(pairs)} pairs")
            continue
        if use_eflomal:
            run_eflomal(l1, l2, pairs, OUT_DIR / f"{l1}_{l2}", concordance_pairs=conc)
        else:
            run_giza(l1, l2, pairs, OUT_DIR / f"{l1}_{l2}", concordance_pairs=conc)
