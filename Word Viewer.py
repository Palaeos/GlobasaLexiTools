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
import json
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
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
ALIGNMENT_HTML = os.path.join(BASE_DIR, "alignment_viewer.html")
TRANSLATE_HTML = os.path.join(BASE_DIR, "translation_aide.html")
APERTIUM_DIR = "/home/paleos/ApplicationSource/GlobasaTranslation/apertium-glb-eng"
GIZA_IMPROVED_DIR = os.path.join(BASE_DIR, "giza_output_improved")
ANNOTATE_HTML = os.path.join(BASE_DIR, "annotate_alignments.html")
GOLD_DIR = os.path.join(BASE_DIR, "gold_alignments")

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
    # Auto-discover all glb_XX alignment directories
    pairs = {}
    for lang in ["en", "eo", "es", "de", "fr", "ru", "nl", "pt", "id",
                 "da", "ar", "hi", "sw", "tr", "zh"]:
        path = os.path.join(GIZA_DIR, f"glb_{lang}", f"glb_{lang}.A3.final")
        if os.path.isfile(path):
            pairs[lang] = path

    result = {}
    for lang, path in pairs.items():
        if os.path.isfile(path):
            print(f"  Parsing GIZA++ alignments for {lang}...")
            result[lang] = parse_giza_a3(path)
    return result


# ---------------------------------------------------------------------------
# Full alignment parsers (for Alignment Viewer page)
# ---------------------------------------------------------------------------

ALIGN_LANGS = ["en", "eo", "es", "de", "fr", "ru", "nl", "pt", "id",
               "da", "ar", "hi", "sw", "tr", "zh"]

_alignment_cache = {}  # (lang, source) -> list of entries
_tmx_contexts_cache = {}  # lang -> list of contexts in alignment order


_GIZA_PUNCT_RE = re.compile(r'([.,:;!?"""()\'—\-])')


def _giza_tokenize_preserve_case(text):
    """Same tokenization as run_giza.py but preserves original case."""
    text = _GIZA_PUNCT_RE.sub(r' \1 ', text)
    return text.split()


def _load_tmx_contexts(lang):
    """Extract context and original-case sentences for each (glb, lang)
    sentence pair from the TMX, in the same order as the A3.final file.

    Returns list of dicts: [{context, glb_tokens, target_tokens}]
    Tokenized the same way as run_giza.py (punctuation split) but with
    original casing preserved.
    """
    if lang in _tmx_contexts_cache:
        return _tmx_contexts_cache[lang]

    entries = []
    try:
        tree = ET.parse(TMX_FILE)
        body = tree.getroot().find("body")
        if body is None:
            body = tree.getroot()
        ns = "{http://www.w3.org/XML/1998/namespace}"
        for tu in body.findall("tu"):
            ctx = ""
            for prop in tu.findall("prop"):
                if prop.get("type") == "x-context":
                    ctx = (prop.text or "").strip()
                    break
            segs = {}
            for tuv in tu.findall("tuv"):
                tv_lang = tuv.get(f"{ns}lang", "")
                seg = tuv.find("seg")
                if seg is not None and seg.text and seg.text.strip():
                    segs[tv_lang] = seg.text.strip()
            if "glb" in segs and lang in segs:
                entries.append({
                    "context": ctx,
                    "glb_tokens": _giza_tokenize_preserve_case(segs["glb"]),
                    "target_tokens": _giza_tokenize_preserve_case(segs[lang]),
                })
    except Exception as e:
        print(f"  Warning: TMX context load failed for {lang}: {e}")

    _tmx_contexts_cache[lang] = entries
    return entries


def parse_giza_a3_full(a3_path, lang=None):
    """Parse A3.final preserving full sentence pairs and alignment links.

    If lang is given, uses the TMX original-case tokens for display
    (GIZA lowercases input). The token positions match because both use
    whitespace tokenization.

    Returns list of dicts: [{glb_tokens, target_tokens, links, context}]
    """
    entries = []
    try:
        with open(a3_path, encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return entries

    tmx_entries = _load_tmx_contexts(lang) if lang else []

    i = 0
    while i + 2 < len(lines):
        target_line = lines[i + 1].strip()
        giza_target_tokens = target_line.split()
        align_line = lines[i + 2].strip()

        giza_glb_tokens = []
        links = []
        for m in re.finditer(r'(\S+)\s+\(\{\s*((?:\d+\s*)*)\}\)', align_line):
            glb_word = m.group(1)
            indices_str = m.group(2).strip()
            if glb_word == "NULL":
                continue
            src_idx = len(giza_glb_tokens)
            giza_glb_tokens.append(glb_word)
            if indices_str:
                for x in indices_str.split():
                    links.append([src_idx, int(x) - 1])

        if giza_glb_tokens:
            entry_idx = len(entries)
            ctx = ""
            glb_tokens = giza_glb_tokens
            target_tokens = giza_target_tokens
            # Replace with original-case tokens from TMX if available and lengths match
            if entry_idx < len(tmx_entries):
                tmx = tmx_entries[entry_idx]
                ctx = tmx["context"]
                if len(tmx["glb_tokens"]) == len(giza_glb_tokens):
                    glb_tokens = tmx["glb_tokens"]
                if len(tmx["target_tokens"]) == len(giza_target_tokens):
                    target_tokens = tmx["target_tokens"]
            entries.append({
                "glb_tokens": glb_tokens,
                "target_tokens": target_tokens,
                "links": links,
                "context": ctx,
            })
        i += 3

    return entries


def parse_improved_alignments(lang, align_type="gdfa"):
    """Parse improved alignment files (.fwd/.rev/.gdfa).

    Reads glb.txt, {lang}.txt (strips |POS tags), and alignment file.
    Returns list of dicts: [{glb_tokens, target_tokens, links}]
    """
    lang_dir = os.path.join(GIZA_IMPROVED_DIR, f"glb_{lang}")
    glb_path = os.path.join(lang_dir, "glb.txt")
    tgt_path = os.path.join(lang_dir, f"{lang}.txt")
    align_path = os.path.join(lang_dir, f"glb_{lang}.{align_type}")

    for p in [glb_path, tgt_path, align_path]:
        if not os.path.isfile(p):
            return []

    def strip_pos(tokens_line):
        """Strip |POS tags from 'word|POS word|POS ...' format."""
        return [t.rsplit("|", 1)[0] for t in tokens_line.split()]

    entries = []
    with open(glb_path, encoding="utf-8") as fg, \
         open(tgt_path, encoding="utf-8") as ft, \
         open(align_path, encoding="utf-8") as fa:
        for glb_line, tgt_line, align_line in zip(fg, ft, fa):
            glb_tokens = strip_pos(glb_line.strip())
            target_tokens = strip_pos(tgt_line.strip())
            links = []
            for pair in align_line.strip().split():
                if "-" in pair:
                    s, t = pair.split("-", 1)
                    links.append([int(s), int(t)])
            if glb_tokens:
                entries.append({
                    "glb_tokens": glb_tokens,
                    "target_tokens": target_tokens,
                    "links": links,
                    "context": "",
                })
    return entries


def _load_alignments(lang, source):
    """Load and cache alignment data for a language pair and source type."""
    key = (lang, source)
    if key in _alignment_cache:
        return _alignment_cache[key]

    if source == "a3":
        path = os.path.join(GIZA_DIR, f"glb_{lang}", f"glb_{lang}.A3.final")
        data = parse_giza_a3_full(path, lang=lang)
    elif source in ("fwd", "rev", "gdfa"):
        data = parse_improved_alignments(lang, source)
    else:
        data = []

    _alignment_cache[key] = data
    return data


# ---------------------------------------------------------------------------
# Apertium helpers
# ---------------------------------------------------------------------------

_APERTIUM_PIPELINES = {
    "eng-glb": {
        "front": (
            "lt-proc -w {d}/eng.automorf.bin"
            " | cg-proc -w {d}/eng-glb.rlx.bin"
            " | apertium-tagger -g {d}/eng-glb.prob"
            " | lsx-proc {d}/eng-glb.autoseq.bin"
            " | apertium-pretransfer"
            " | lt-proc -b {d}/eng-glb.autobil.bin"
        ),
        "back": (
            "lrx-proc -m {d}/eng-glb.autolex.bin"
            " | apertium-anaphora {d}/apertium-glb-eng.eng-glb.arx"
            " | rtx-proc -a {d}/eng-glb.rtx.bin"
            " | lsx-proc {d}/eng-glb.revautoseq.bin"
            " | lt-proc -g {d}/eng-glb.autogen.bin"
            " | lt-proc -p {d}/eng-glb.autopgen.bin"
        ),
    },
    "glb-eng": {
        "front": (
            "lt-proc -w {d}/glb-eng.automorf.bin"
            " | cg-proc -w {d}/glb-eng.rlx.bin"
            " | apertium-tagger -g {d}/glb-eng.prob"
            " | lsx-proc {d}/glb-eng.autoseq.bin"
            " | apertium-pretransfer"
            " | lt-proc -b {d}/glb-eng.autobil.bin"
        ),
        "back": (
            "lrx-proc -m {d}/glb-eng.autolex.bin"
            " | apertium-anaphora {d}/apertium-glb-eng.glb-eng.arx"
            " | rtx-proc -a {d}/glb-eng.rtx.bin"
            " | lsx-proc {d}/glb-eng.revautoseq.bin"
            " | lt-proc -g {d}/glb-eng.autogen.bin"
            " | lt-proc -p {d}/glb-eng.autopgen.bin"
        ),
    },
}


def _run_apertium(text, mode):
    """Run a full apertium translation."""
    try:
        proc = subprocess.run(
            ["apertium", "-d", APERTIUM_DIR, mode],
            input=text, capture_output=True, text=True, timeout=10,
        )
        return proc.stdout.strip()
    except (subprocess.TimeoutExpired, Exception) as e:
        return f"[Error: {e}]"


def _run_pipeline_half(text, direction, half):
    """Run the front or back half of the Apertium pipeline.

    half: "front" or "back"
    """
    pipeline = _APERTIUM_PIPELINES.get(direction, {}).get(half, "")
    if not pipeline:
        return ""
    cmd = pipeline.format(d=APERTIUM_DIR)
    try:
        proc = subprocess.run(
            ["bash", "-c", cmd],
            input=text, capture_output=True, text=True, timeout=10,
        )
        return proc.stdout.strip()
    except (subprocess.TimeoutExpired, Exception) as e:
        return f"[Error: {e}]"


_BILTRANS_RE = re.compile(r'\^([^$]+)\$')
_BILTRANS_UNIT_RE = re.compile(r'([^<>/]+)((?:<[^>]+>)*)')


def _parse_biltrans(biltrans_str):
    """Parse biltrans output into structured token list.

    Each ^...$ unit becomes a dict:
    {
        "raw": original ^...$ text,
        "source_lemma": str,
        "source_tags": str,
        "alternatives": [{lemma, tags, raw}],
        "is_noun": bool,
        "is_suppressed_article": bool,
    }
    """
    tokens = []
    for m in _BILTRANS_RE.finditer(biltrans_str):
        raw = m.group(1)
        parts = raw.split("/")
        if not parts:
            continue

        # Source side
        src = parts[0]
        sm = _BILTRANS_UNIT_RE.match(src)
        source_lemma = sm.group(1) if sm else src
        source_tags = sm.group(2) if sm else ""

        # Target alternatives
        alternatives = []
        for alt in parts[1:]:
            am = _BILTRANS_UNIT_RE.match(alt.lstrip("@"))
            if am:
                alternatives.append({
                    "lemma": am.group(1),
                    "tags": am.group(2),
                    "raw": alt,
                })

        is_noun = any("<n>" in a.get("tags", "") for a in alternatives)
        # Articles: @-prefixed det units have no Globasa equivalent
        is_suppressed = src.startswith("@") or (
            alternatives and alternatives[0]["raw"].startswith("@")
        )
        is_det = "<det>" in source_tags

        tokens.append({
            "raw": "^" + raw + "$",
            "source_lemma": source_lemma.lstrip("@"),
            "source_tags": source_tags,
            "alternatives": alternatives,
            "is_noun": is_noun,
            "is_det": is_det,
            "is_suppressed_article": is_det and is_suppressed,
            "is_numeral": "<num>" in source_tags,
        })

    return tokens


def _apply_overrides(biltrans_tokens, overrides, articles, direction):
    """Apply user overrides and article choices to biltrans tokens.

    overrides: {str(idx): chosen_lemma}
    articles: {str(idx): "un"|"a"|"the"|""}
    direction: "eng-glb" or "glb-eng"

    Returns modified biltrans string ready for the back half.
    """
    # eng→glb: find which nouns follow suppressed articles and should have
    # their <sg> changed to <sp> to prevent transfer-rule un insertion
    suppress_sg = set()  # biltrans indices of nouns to suppress
    if direction == "eng-glb":
        for i, tok in enumerate(biltrans_tokens):
            if tok["is_suppressed_article"]:
                idx_str = str(i)
                # Unless user explicitly requested un
                if not (idx_str in articles and articles[idx_str] == "un"):
                    # Find the next noun token
                    for j in range(i + 1, len(biltrans_tokens)):
                        if biltrans_tokens[j]["is_noun"]:
                            suppress_sg.add(j)
                            break

    result_units = []
    for i, tok in enumerate(biltrans_tokens):
        idx_str = str(i)

        # Apply lexical override: reorder alternatives so chosen is first
        if idx_str in overrides:
            chosen = overrides[idx_str]
            alts = tok["alternatives"]
            reordered = [a for a in alts if a["lemma"] == chosen]
            reordered += [a for a in alts if a["lemma"] != chosen]
            if reordered:
                src = tok["raw"].split("/")[0].lstrip("^")
                raw = "^" + src + "/" + "/".join(a["raw"] for a in reordered) + "$"
                # Also suppress sg if needed
                if i in suppress_sg:
                    raw = raw.replace("<sg>", "<sp>")
                result_units.append(raw)
                continue

        # Handle article insertion (glb→eng): insert det before noun
        if direction == "glb-eng" and tok["is_noun"] and idx_str in articles:
            art = articles[idx_str]
            if art == "the":
                result_units.append("^the<det><def><sp>/the<det><def><sp>$")
            elif art == "a":
                result_units.append("^a<det><ind><sg>/a<det><ind><sg>$")

        # Handle eng→glb: suppress @-prefixed articles (keep them out of stream)
        if direction == "eng-glb" and tok["is_suppressed_article"]:
            # Article is always removed from biltrans; un suppression is done
            # by changing noun's <sg> to <sp> (see suppress_sg above)
            continue

        raw = tok["raw"]
        # Suppress un insertion: change <sg> to <sp> on affected nouns
        if i in suppress_sg:
            raw = raw.replace("<sg>", "<sp>")
        result_units.append(raw)

    return " ".join(result_units)


def _build_token_info(output_text, biltrans_tokens, direction):
    """Build interactive token info by matching biltrans lemmas to output words.

    The Apertium transfer can insert/reorder words, so we match by lemma
    rather than sequential position.

    Returns:
      output_words: list of output word strings (for rendering)
      interactions: list of dicts, one per biltrans token that is interactive
    """
    # Clean output: strip trailing \uffff and other control chars
    output_text = re.sub(r'[\uffff\x00-\x1f]+', '', output_text).strip()
    output_words = output_text.split() if output_text else []

    # Build set of lemmas from biltrans first alternatives (selected translation)
    # Match them to output word positions. Try exact match first, then substring
    # (for compound nouns merged by transfer rules, e.g. myaw+somno -> myawsomno).
    lemma_to_out = {}
    used_positions = set()
    biltrans_lemmas = []
    for tok in biltrans_tokens:
        if tok["alternatives"]:
            biltrans_lemmas.append(tok["alternatives"][0]["lemma"])
        else:
            biltrans_lemmas.append(None)

    # Pass 1: exact match (each output word can be claimed by only one lemma)
    for lemma in biltrans_lemmas:
        if not lemma or lemma in lemma_to_out:
            continue
        ll = lemma.lower()
        for j, ow in enumerate(output_words):
            if j in used_positions:
                continue
            if ow.lower().lstrip("*@#") == ll:
                lemma_to_out[lemma] = j
                used_positions.add(j)
                break

    # Pass 2: substring match for compound nouns
    for lemma in biltrans_lemmas:
        if not lemma or lemma in lemma_to_out:
            continue
        ll = lemma.lower()
        for j, ow in enumerate(output_words):
            if ll in ow.lower():
                lemma_to_out[lemma] = j
                break

    interactions = []
    for i, tok in enumerate(biltrans_tokens):
        # Suppressed articles (eng→glb): emit info for un toggle
        if direction == "eng-glb" and tok["is_suppressed_article"]:
            # Find the next noun token's lemma in the output
            # The noun following this article can have un toggled
            interactions.append({
                "biltrans_idx": i,
                "type": "suppressed_article",
                "source": tok["source_lemma"],
            })
            continue

        if not tok["alternatives"]:
            continue

        lemma = tok["alternatives"][0]["lemma"]
        out_pos = lemma_to_out.get(lemma)

        # Build alternatives (only for tokens with >1 unique lemma)
        seen_lemmas = set()
        alts = []
        for a in tok["alternatives"]:
            if a["lemma"] in seen_lemmas:
                continue
            seen_lemmas.add(a["lemma"])
            if direction == "eng-glb":
                gloss = _get_gloss(a["lemma"])
            else:
                gloss = ""
            alts.append({"lemma": a["lemma"], "gloss": gloss})
        if len(alts) <= 1:
            alts = []  # No choices to show if only 1 unique lemma

        if out_pos is not None or alts or tok["is_noun"]:
            interactions.append({
                "biltrans_idx": i,
                "type": "word",
                "source": tok["source_lemma"],
                "output_idx": out_pos,
                "is_noun": tok["is_noun"],
                "is_numeral": tok.get("is_numeral", False),
                "alternatives": alts,
            })

    return output_words, interactions


def _get_gloss(lemma):
    """Look up a short English gloss for a Globasa lemma."""
    entry = _all_entries.get(lemma)
    if not entry:
        return ""
    # Get the wordlist entry from LMDB for full translations
    wl = _db.get_wordlist(lemma)
    if wl:
        eng = wl.get("TranslationEng", "")
        if eng:
            short = eng.split(";")[0].strip()
            short = re.sub(r"^[a-z./ ]+:\s*", "", short)
            return short
    return ""


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


# ---------------------------------------------------------------------------
# Alignment Viewer
# ---------------------------------------------------------------------------

@app.route("/alignments")
def alignment_viewer():
    return send_file(ALIGNMENT_HTML)


@app.route("/api/alignment_langs")
def alignment_langs():
    """Return available languages and sources with entry counts."""
    result = []
    for lang in ALIGN_LANGS:
        entry = {"lang": lang, "sources": []}
        # A3
        a3_path = os.path.join(GIZA_DIR, f"glb_{lang}", f"glb_{lang}.A3.final")
        if os.path.isfile(a3_path):
            data = _load_alignments(lang, "a3")
            entry["sources"].append({"source": "a3", "count": len(data)})
        # Improved
        for src in ("fwd", "rev", "gdfa"):
            p = os.path.join(GIZA_IMPROVED_DIR, f"glb_{lang}", f"glb_{lang}.{src}")
            if os.path.isfile(p):
                data = _load_alignments(lang, src)
                entry["sources"].append({"source": src, "count": len(data)})
        if entry["sources"]:
            result.append(entry)
    return jsonify(result)


@app.route("/api/alignment_contexts")
def api_alignment_contexts():
    """Return distinct corpus sections (TMX contexts) for a language.

    Only meaningful for source='a3' (the natural-text corpus).
    """
    lang = request.args.get("lang", "en")
    source = request.args.get("source", "a3")
    if lang not in ALIGN_LANGS:
        return jsonify([])

    data = _load_alignments(lang, source)
    counts = {}
    for entry in data:
        ctx = entry.get("context", "")
        counts[ctx] = counts.get(ctx, 0) + 1
    result = [{"context": c, "count": n} for c, n in counts.items() if c]
    result.sort(key=lambda x: -x["count"])
    return jsonify(result)


@app.route("/api/alignments")
def api_alignments():
    """Paginated alignment data for a language pair."""
    lang = request.args.get("lang", "en")
    source = request.args.get("source", "a3")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))
    q = request.args.get("q", "").strip().lower()
    context_filter = request.args.get("context", "").strip()

    if lang not in ALIGN_LANGS:
        return jsonify({"error": f"Unknown language: {lang}"}), 400

    data = _load_alignments(lang, source)

    # Filter by corpus section
    if context_filter:
        data = [e for e in data if e.get("context", "") == context_filter]

    # Filter by query
    if q:
        filtered = []
        for entry in data:
            glb_match = any(q in t.lower() for t in entry["glb_tokens"])
            tgt_match = any(q in t.lower() for t in entry["target_tokens"])
            if glb_match or tgt_match:
                filtered.append(entry)
        data = filtered

    total = len(data)
    start = (page - 1) * per_page
    end = start + per_page
    page_data = data[start:end]

    return jsonify({
        "lang": lang,
        "source": source,
        "total": total,
        "page": page,
        "per_page": per_page,
        "entries": page_data,
    })


# ---------------------------------------------------------------------------
# Gold Alignment Annotation
# ---------------------------------------------------------------------------

def _gold_tsv_path(lang):
    """Return path to the gold TSV file for a language."""
    os.makedirs(GOLD_DIR, exist_ok=True)
    return os.path.join(GOLD_DIR, f"{lang}.tsv")


def _load_gold_annotation(lang, sentence_id):
    """Return the latest gold annotation for (lang, sentence_id), or None."""
    path = _gold_tsv_path(lang)
    if not os.path.isfile(path):
        return None
    best = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 6:
                continue
            try:
                sid = int(parts[0])
            except ValueError:
                continue
            if sid != sentence_id:
                continue
            timestamp = parts[5]
            if best is None or timestamp > best["timestamp"]:
                try:
                    links = json.loads(parts[3])
                except json.JSONDecodeError:
                    links = []
                best = {
                    "sentence_id": sid,
                    "links": links,
                    "annotator": parts[4],
                    "timestamp": timestamp,
                }
    return best


def _load_all_annotated_ids(lang):
    """Return a set of sentence_ids that have at least one gold annotation."""
    path = _gold_tsv_path(lang)
    if not os.path.isfile(path):
        return set()
    ids = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 1:
                try:
                    ids.add(int(parts[0]))
                except ValueError:
                    pass
    return ids


@app.route("/annotate")
def annotation_viewer():
    return send_file(ANNOTATE_HTML)


@app.route("/api/gold_alignment", methods=["GET"])
def api_get_gold_alignment():
    """Return the latest gold annotation for (lang, sentence_id).

    Query params: lang, sentence_id
    Returns 200 with {sentence_id, links, annotator, timestamp} or 404.
    """
    lang = request.args.get("lang", "en")
    try:
        sid = int(request.args.get("sentence_id", -1))
    except ValueError:
        return jsonify({"error": "sentence_id must be an integer"}), 400

    if lang not in ALIGN_LANGS:
        return jsonify({"error": f"Unknown language: {lang}"}), 400

    annotation = _load_gold_annotation(lang, sid)
    if annotation is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(annotation)


@app.route("/api/gold_alignment", methods=["POST"])
def api_post_gold_alignment():
    """Save a gold annotation for one sentence.

    Body JSON: {lang, sentence_id, glb_tokens (list), tgt_tokens (list),
                links ([[i,j],...]), annotator (optional)}
    Appends one TSV row to gold_alignments/{lang}.tsv.
    """
    data = request.get_json(force=True, silent=True) or {}
    lang = data.get("lang", "en")
    try:
        sid = int(data.get("sentence_id", -1))
    except (TypeError, ValueError):
        return jsonify({"error": "sentence_id must be an integer"}), 400

    if lang not in ALIGN_LANGS:
        return jsonify({"error": f"Unknown language: {lang}"}), 400

    glb_tokens = data.get("glb_tokens", [])
    tgt_tokens = data.get("tgt_tokens", [])
    links = data.get("links", [])
    annotator = data.get("annotator", "anonymous")
    timestamp = datetime.now(timezone.utc).isoformat()

    glb_str = " ".join(str(t) for t in glb_tokens)
    tgt_str = " ".join(str(t) for t in tgt_tokens)
    links_json = json.dumps(links, separators=(",", ":"))

    path = _gold_tsv_path(lang)
    row = "\t".join([str(sid), glb_str, tgt_str, links_json, annotator, timestamp])
    with open(path, "a", encoding="utf-8") as f:
        f.write(row + "\n")

    return jsonify({"status": "saved", "timestamp": timestamp})


@app.route("/api/annotated_ids")
def api_annotated_ids():
    """Return set of sentence_ids already annotated for a language.

    Query params: lang
    Returns {lang, annotated_ids: [int, ...]}
    """
    lang = request.args.get("lang", "en")
    if lang not in ALIGN_LANGS:
        return jsonify({"error": f"Unknown language: {lang}"}), 400
    ids = sorted(_load_all_annotated_ids(lang))
    return jsonify({"lang": lang, "annotated_ids": ids})


# ---------------------------------------------------------------------------
# Translation Aide (Apertium)
# ---------------------------------------------------------------------------

@app.route("/translate")
def translation_aide():
    return send_file(TRANSLATE_HTML)


@app.route("/api/translate", methods=["POST"])
def api_translate():
    """Translate text using the Apertium eng-glb pair.

    Supports lexical overrides and article/number resolution.
    """
    data = request.get_json()
    text = (data.get("text", "") or "").strip()
    direction = data.get("direction", "eng-glb")
    overrides = data.get("overrides", {})
    articles = data.get("articles", {})
    show_stages = data.get("stages", False)

    if not text:
        return jsonify({"error": "No text provided"}), 400
    if direction not in ("eng-glb", "glb-eng"):
        return jsonify({"error": "Invalid direction"}), 400
    if len(text) > 5000:
        return jsonify({"error": "Text too long (max 5000 chars)"}), 400

    # Run front half (stages 1-6) to get biltrans
    biltrans_str = _run_pipeline_half(text, direction, "front")

    # Parse biltrans
    biltrans_tokens = _parse_biltrans(biltrans_str)

    # Apply overrides and article choices, rebuild biltrans stream
    modified_biltrans = _apply_overrides(
        biltrans_tokens, overrides, articles, direction
    )

    # Run back half (stages 7-12) to get final output
    raw_output = _run_pipeline_half(modified_biltrans, direction, "back")

    # Build interactive token info
    output_words, interactions = _build_token_info(
        raw_output, biltrans_tokens, direction
    )

    # Clean output string
    output = " ".join(output_words)

    # Optional pipeline stages for debug view
    stages = None
    if show_stages:
        stages = {
            "biltrans": biltrans_str,
        }
        for suffix in ("morph", "disam", "biltrans", "transfer"):
            mode = f"{direction}-{suffix}"
            stages[suffix] = _run_apertium(text, mode)

    return jsonify({
        "input": text,
        "direction": direction,
        "output": output,
        "output_words": output_words,
        "interactions": interactions,
        "stages": stages,
    })


if __name__ == "__main__" or True:
    app.run(debug=True, port=5000)
