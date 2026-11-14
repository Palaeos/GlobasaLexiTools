"""Shared helpers for writing Globasa Apertium dictionaries.

Used by dictionaryPreprocess.py (monolingual + function-word drafts) and
build_bidix.py (the generated part of the glb-X bilingual dictionaries).
"""

import os
import re
import shutil
from xml.sax.saxutils import escape as xml_escape

from Lexilista_parser import GlossPoS, VerbType

# Apertium checkouts. The Globasa pairs (apertium-glb, apertium-glb-eng/-fra/
# -deu/-nld) are submodules here; the upstream monolinguals they build
# against (apertium-eng, apertium-fra, ...) are plain, untracked clones.
APERTIUM_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "GlobasaTranslation")


# ── PoS → Apertium symbol ────────────────────────────────────────────────
GLOSS_TO_APERTIUM = {
    GlossPoS.NOUN:                 "n",
    GlossPoS.PROPER_NOUN:          "np",
    GlossPoS.NOUN_PHRASE:          "n",
    GlossPoS.VERB:                 "vblex",     # overridden by verb_type
    GlossPoS.VERB_PHRASE:          "vblex",
    GlossPoS.ADJECTIVE:            "adj",
    GlossPoS.ADJECTIVE_PHRASE:     "adj",
    GlossPoS.PROPER_ADJECTIVE:     "adj",
    GlossPoS.POSSESSIVE_ADJECTIVE: "adj",
    GlossPoS.ADVERB:               "adv",
    GlossPoS.VERBAL_ADVERB:        "adv",
    GlossPoS.PHRASAL_ADVERB:       "adv",
    GlossPoS.INTERJECTION:         "ij",
    GlossPoS.PRONOUN:              "prn",
    GlossPoS.POSSESSIVE_PRONOUN:   "prn",
    GlossPoS.NUMBER:               "num",
    GlossPoS.PREPOSITION:          "pr",
    GlossPoS.PHRASAL_PREPOSITION:  "pr",
    GlossPoS.CONJUNCTION:          "cnjsub",
    GlossPoS.PHRASAL_CONJUNCTION:  "cnjsub",
    GlossPoS.DETERMINER:           "det",
}

FUNCTION_POS = {GlossPoS.PREPOSITION, GlossPoS.DETERMINER,
                GlossPoS.CONJUNCTION, GlossPoS.PARTICLE,
                GlossPoS.PRONOUN, GlossPoS.NUMBER}

NOUN_SYMBOLS = {"n", "np"}


def apertium_symbol(pg):
    if pg.affix_type is not None:
        return None
    if pg.pos == GlossPoS.VERB:
        if pg.verb_type == VerbType.AUXILIARY:
            return "vbmod"
        if pg.verb_type == VerbType.COPULAR:
            return "vbser"
        return "vblex"
    return GLOSS_TO_APERTIUM.get(pg.pos)


# ── Gloss text cleanup ──────────────────────────────────────────────────
GLOSS_RE_ITALIC = re.compile(r"\(_.*?_\)")
GLOSS_RE_PAREN  = re.compile(r"\(.*?\)")
GLOSS_RE_ANGLE  = re.compile(r"<.*?>")
# Defensive strip for English-style annotation prefixes that Lexilista_parser's
# translation map (Spanish/Esperanto-style: s:, tr:, intr:, …) doesn't yet
# recognise — French/Russian/Chinese columns in word-list.csv now use the
# English-style annotations (n:, v.tr:, adj:, …), and the parser leaves the
# prefix in `pg.gloss` when it falls back to positional alignment.
_LEADING_ANN_RE = re.compile(
    r"^(?:n|np|adj|adv|prep|conj|interj|num|det|prn|par|pfx|sfx|m|"
    r"v\.tr|v\.intr|v\.cop|v\.aux|prop\s+n|prop\s+adj|poss\s+(?:pron|adj)|"
    r"phrs|prep\s+phrs|adj\s+phrs|adv\s+phrs|conj\s+phrs|n\s+phrs|v\s+phrs)"
    r"(?:\s*\([^)]*\))?\s*:\s*",
    re.IGNORECASE,
)


def expand_gloss_tokens(raw):
    """Split a ParsedGloss text on ', ' and clean each token.
    Italic '(_x_)' annotations are stripped; non-italic '(x)' parens are emitted
    twice (compact + verbose) so both shapes appear in the dictionary."""
    if not raw:
        return []
    raw = _LEADING_ANN_RE.sub("", raw, count=1)
    out = []
    # Split on ', ' outside parentheses: an '(_x, y_)' annotation stays whole.
    for tok in re.split(r", (?![^()]*\))", raw):
        tok = GLOSS_RE_ITALIC.sub("", tok).strip()
        if not tok or tok.startswith("_"):
            continue
        compact = re.sub(r"\s+", " ", GLOSS_RE_PAREN.sub("", tok)).strip()
        if compact and compact != tok:
            verbose = re.sub(r"\s+", " ",
                             tok.replace("(", "").replace(")", "")).strip()
            out.append(compact)
            if verbose and verbose != compact:
                out.append(verbose)
        else:
            out.append(tok)
    return out


genderForeignDict = {"m": "m", "f": "f", "n": "nt"}
genderDict = {"te": "ut", "to": "nt", "mante": "m", "femte": "f"}


def split_foreign_gender(tok):
    """If tok ends with '<m>'/'<f>'/'<n>' (slash-list allowed, e.g. '<m>/<n>'),
    return (clean_tok, [apertium_gender, ...]). Else (tok, [])."""
    if not tok.endswith(">"):
        return tok, []
    last = tok.split(" ")[-1]
    if not (last.startswith("<") and last.endswith(">")):
        return tok, []
    genders = []
    for raw in last.split("/"):
        g = genderForeignDict.get(raw.strip("<>"))
        if g:
            genders.append(g)
    if not genders:
        return tok, []
    # Strip the entire trailing gender block ("<m>" or "<m>/<n>"), including
    # surrounding whitespace and the inter-marker slash — not just the angle
    # brackets, which would leave a stray "/".
    clean = re.sub(r"\s*<[^>]+>(?:\s*/\s*<[^>]+>)*\s*$", "", tok).strip()
    return clean, genders


# ── English synthetic-comparative detection ─────────────────────────────
# Marks English adjectives whose comparative is formed by inflection
# ("bigger") rather than analytically ("more beautiful"). Only the English
# bilingual dix uses this tag; Globasa itself does not inflect adjectives.
# Source of truth: apertium-eng.eng.dix — adjective entries that reference a
# paradigm whose body contains <s n="sint"/> are synthetic; anything routed
# through `expensive__adj` (or any other non-sint paradigm) is analytic.

APERTIUM_ENG_DIX = os.path.join(APERTIUM_ROOT, "apertium-eng",
                                "apertium-eng.eng.dix")
_PARDEF_RE = re.compile(r'<pardef\s+n="([^"]+)"\s*>(.*?)</pardef>', re.DOTALL)
_ADJ_ENTRY_RE = re.compile(
    r'<e\s+lm="([^"]+)"[^>]*>\s*<i>[^<]*</i>\s*<par\s+n="([^"]+)"\s*/>\s*</e>'
)


def _load_synthetic_adj_set():
    """Return frozenset of English lemmas whose comparative is synthetic
    (per apertium-eng.eng.dix paradigm classification). Empty if the file is
    missing — preprocess then falls back to never tagging anything as sint."""
    try:
        with open(APERTIUM_ENG_DIX, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"  ! apertium-eng dix not found at {APERTIUM_ENG_DIX} —"
              f" English adjective sint tags will be skipped")
        return frozenset()

    synthetic_paradigms = {
        name for name, body in _PARDEF_RE.findall(text)
        if name.endswith("__adj") and '<s n="sint"/>' in body
    }
    lemmas = {
        lm for lm, par in _ADJ_ENTRY_RE.findall(text)
        if par in synthetic_paradigms
    }
    return frozenset(lm.lower() for lm in lemmas)


SYNTHETIC_ADJ_EN = _load_synthetic_adj_set()
print(f"Loaded {len(SYNTHETIC_ADJ_EN)} synthetic English adjectives "
      f"from apertium-eng.eng.dix")


def is_synthetic_adj_en(word):
    """True if `word` is an English adjective whose comparative is synthetic
    (X→X-er) per apertium-eng. Conservative on multi-word glosses: returns
    False for anything that isn't a single space-free word."""
    if not word:
        return False
    w = word.strip().lower()
    if not w or " " in w or "\t" in w:
        return False
    return w in SYNTHETIC_ADJ_EN


# ── XML helpers ─────────────────────────────────────────────────────────
blank = "<b/>"


def lemma_repr(word):
    return blank.join(xml_escape(part) for part in word.split())


def bilingual_entry(lang_label, word, lemma_symbol, lemma_gender,
                    gloss, gloss_symbol, gloss_gender, restriction=None,
                    sint=None):
    """One glb-X <e> line. restriction: None (both ways), "LR" (glb→X only)
    or "RL" (X→glb only). sint: whether the English adjective is synthetic;
    None looks it up in apertium-eng.eng.dix (SYNTHETIC_ADJ_EN)."""
    l_tags = f'<s n="{lemma_symbol}"/>'
    if lemma_gender:
        l_tags += f'<s n="{lemma_gender}"/>'
    r_tags = f'<s n="{gloss_symbol}"/>'
    if sint is None:
        sint = (lang_label == "En" and gloss_symbol == "adj"
                and is_synthetic_adj_en(gloss))
    if sint:
        r_tags += '<s n="sint"/>'
    if gloss_gender:
        r_tags += f'<s n="{gloss_gender}"/>'
    e_open = f'<e r="{restriction}">' if restriction else '<e>'
    return (f'{e_open}<p><l>{lemma_repr(word)}{l_tags}</l>   '
            f'<r>{lemma_repr(gloss)}{r_tags}</r></p></e>')


# ── Merging generated entries into a dix ────────────────────────────────
# Everything between the marker and the closing </section> of section main
# is generated; everything above the marker is curated by hand.

APERTIUM_MARKER = "<!-- Autogenerated common words -->"

_MAIN_SECTION_OPEN_RE = re.compile(r'<section\s+id\s*=\s*"main"[^>]*>')


def merge_into_dix(dix_path, entries_path, require_marker=False):
    """require_marker: refuse a dix without the marker instead of appending
    one, so a curated part never silently absorbs generated entries."""
    if not os.path.exists(dix_path):
        print(f"  ! missing: {dix_path}")
        return
    if not os.path.exists(entries_path):
        print(f"  ! missing entries: {entries_path}")
        return

    with open(dix_path, "r", encoding="utf-8") as f:
        text = f.read()
    with open(entries_path, "r", encoding="utf-8") as f:
        entries = f.read().rstrip("\n")

    sec_open = _MAIN_SECTION_OPEN_RE.search(text)
    if not sec_open:
        print(f"  ! no <section id=\"main\"> in {dix_path}")
        return
    main_start = sec_open.end()
    sec_close = text.find("</section>", main_start)
    if sec_close == -1:
        print(f"  ! no </section> after main in {dix_path}")
        return

    main_body = text[main_start:sec_close]
    marker_idx = main_body.find(APERTIUM_MARKER)
    if marker_idx == -1 and require_marker:
        print(f"  ! no '{APERTIUM_MARKER}' in {dix_path}: not merged. Put the"
              f" marker below the curated entries (move old generated ones"
              f" under it) and rerun")
        return
    if marker_idx == -1:
        # Insert marker at the end of main, keep all existing entries above.
        new_main = (main_body.rstrip() + "\n\n"
                    + APERTIUM_MARKER + "\n" + entries + "\n  ")
    else:
        # Wipe everything from the marker through end-of-main, replace with
        # marker + fresh entries.
        new_main = (main_body[:marker_idx]
                    + APERTIUM_MARKER + "\n" + entries + "\n  ")

    new_text = text[:main_start] + new_main + text[sec_close:]
    if new_text == text:
        print(f"  · unchanged: {dix_path}")
        return

    shutil.copy(dix_path, dix_path + ".bak")
    with open(dix_path, "w", encoding="utf-8") as f:
        f.write(new_text)

    added = entries.count("<e ") + entries.count("<e>")
    print(f"  → wrote {added} entries to {dix_path} (backup: {dix_path}.bak)")
