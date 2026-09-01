import re
import contextlib
from xml.sax.saxutils import escape as xml_escape
import pandas as pd

from Lexilista_parser import parseWordEntry, GlossPoS, VerbType


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


# ── Languages emitted ───────────────────────────────────────────────────
# (apertium label, Lexilista code, wordlist column, foreign-gender markers?)
# TODO: Rus / Zho / Hin / Ara are now in word-list.csv — add a row here when
# downstream is ready.
LANGS = [
    ("En", "Eng", "TranslationEng", False),
    ("Es", "Spa", "TranslationSpa", True),
    ("Eo", "Epo", "TranslationEpo", False),
    ("De", "Deu", "TranslationDeu", True),
    ("Fr", "Fra", "TranslationFra", True),
    ("Nl", "Nl",  None,              True),   # only in menalariExtension
]


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
    for tok in raw.split(", "):
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

APERTIUM_ENG_DIX = (
    "/home/paleos/ApplicationSource/GlobasaTranslation/apertium-eng/"
    "apertium-eng.eng.dix"
)
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


def emit(handle, line):
    handle.write(line + "\n")
    print(line)


def write_un_noun(handle, word, gender):
    par = f"__n_{gender}" if gender != "GD" else "__n"
    emit(handle, f'<e lm="{word}">       <i>{lemma_repr(word)}</i><par n="{par}"/></e>')


def write_un_other(handle, word, symbol):
    emit(handle, f'<e><p><l>{lemma_repr(word)}</l>       '
                 f'<r>{lemma_repr(word)}<s n="{symbol}"/></r></p></e>')


def write_bilingual(handle, lang_label, word, lemma_symbol, lemma_gender,
                    gloss, gloss_symbol, gloss_gender):
    l_tags = f'<s n="{lemma_symbol}"/>'
    if lemma_gender:
        l_tags += f'<s n="{lemma_gender}"/>'
    r_tags = f'<s n="{gloss_symbol}"/>'
    if (lang_label == "En" and gloss_symbol == "adj"
            and is_synthetic_adj_en(gloss)):
        r_tags += '<s n="sint"/>'
    if gloss_gender:
        r_tags += f'<s n="{gloss_gender}"/>'
    emit(handle, f'<e><p><l>{lemma_repr(word)}{l_tags}</l>   '
                 f'<r>{lemma_repr(gloss)}{r_tags}</r></p></e>')


# ── Data loading ────────────────────────────────────────────────────────
df = pd.read_csv("word-list.csv", index_col=0, keep_default_na=False)
df.index = df.index.astype(str).str.strip()

gender_frame = pd.read_csv("menalariPronouns_edited.tsv", sep="\t",
                           index_col=0, keep_default_na=False)
gender_frame.drop_duplicates(inplace=True)

translation_ext_frame = pd.read_csv("menalariExtension_edited.tsv", sep="\t",
                                    index_col=0, keep_default_na=False)
translation_ext_frame.drop_duplicates(inplace=True)


# ── Main ────────────────────────────────────────────────────────────────
with contextlib.ExitStack() as stack:
    def open_dict(label, target):
        return stack.enter_context(
            open(f"dictionary_{label}_{target}.xml", "w", newline=""))

    handle_un = {t: open_dict("un", t) for t in ("fn", "content")}
    handle_lang = {(label, t): open_dict(label, t)
                   for label, _, _, _ in LANGS
                   for t in ("fn", "content")}

    for word, row in df.iterrows():
        if not isinstance(word, str) or word.startswith("-"):
            continue
        wordclass = str(row.get("WordClass", ""))
        eng_text = str(row.get("TranslationEng", ""))
        if not eng_text.strip():
            continue

        # Build non-English translations dict for parseWordEntry
        non_eng = {}
        for _, code, col, _ in LANGS[1:]:
            if col is None:
                continue
            if col in df.columns:
                v = str(row.get(col, ""))
                if v and v != "False":
                    non_eng[code] = v
        # Dutch only exists in menalariExtension
        if word in translation_ext_frame.index:
            dutch = translation_ext_frame.at[word, "Dutch"]
            if isinstance(dutch, str) and dutch and dutch != "False":
                non_eng["Nl"] = dutch

        parsed = parseWordEntry(eng_text, wordclass, non_eng).translations

        eng_glosses = parsed.get("Eng", [])
        if not eng_glosses:
            continue

        # Function-word vs content-word routing (based on English head PoS)
        head_pos = eng_glosses[0].pos
        target = "fn" if head_pos in FUNCTION_POS else "content"
        un_h = handle_un[target]

        # Build PoS slots from English: (symbol, verb_type) preserving order.
        slot_keys = []
        seen = set()
        for g in eng_glosses:
            sym = apertium_symbol(g)
            if sym is None:
                continue
            key = (sym, g.verb_type)
            if key not in seen:
                seen.add(key)
                slot_keys.append(key)

        if not slot_keys:
            continue

        # Resolve Globasa-side genders for noun-headed entries.
        if word in gender_frame.index and isinstance(
                gender_frame.loc[word].Pronoun, str) and gender_frame.loc[word].Pronoun:
            globasa_genders = [genderDict[a]
                               for a in gender_frame.loc[word].Pronoun.split(", ")
                               if a in genderDict]
            if not globasa_genders:
                globasa_genders = ["GD"]
        else:
            globasa_genders = ["GD"]

        # Track which (symbol, gender) monolingual noun entries have been
        # emitted (a row with two pronoun-anaphors should still emit once
        # per gender, but only once per gender).
        un_noun_emitted = set()
        un_other_emitted = set()

        for slot_symbol, slot_verb_type in slot_keys:
            is_noun_slot = slot_symbol in NOUN_SYMBOLS

            # Monolingual entry
            if is_noun_slot:
                for g in globasa_genders:
                    if (slot_symbol, g) not in un_noun_emitted:
                        un_noun_emitted.add((slot_symbol, g))
                        write_un_noun(un_h, word, g)
            else:
                if slot_symbol not in un_other_emitted:
                    un_other_emitted.add(slot_symbol)
                    write_un_other(un_h, word, slot_symbol)

            # Bilingual entries — one per language, per matching ParsedGloss,
            # per cleaned token.
            for label, code, _, has_foreign_gender in LANGS:
                lang_glosses = parsed.get(code, [])
                # Match this slot
                slot_glosses = [pg for pg in lang_glosses
                                if apertium_symbol(pg) == slot_symbol
                                and pg.verb_type == slot_verb_type]
                if not slot_glosses:
                    continue
                handle = handle_lang[(label, target)]

                for pg in slot_glosses:
                    for tok in expand_gloss_tokens(pg.gloss):
                        if is_noun_slot:
                            # Strip foreign gender marker if present and
                            # emit once per (globasa_gender × foreign_gender).
                            clean_tok, foreign_genders = (
                                split_foreign_gender(tok)
                                if has_foreign_gender else (tok, []))
                            if not clean_tok:
                                continue
                            for gg in globasa_genders:
                                if foreign_genders:
                                    for fg in foreign_genders:
                                        write_bilingual(handle, label, word,
                                                        slot_symbol, gg,
                                                        clean_tok, slot_symbol, fg)
                                else:
                                    write_bilingual(handle, label, word,
                                                    slot_symbol, gg,
                                                    clean_tok, slot_symbol, None)
                        else:
                            write_bilingual(handle, label, word,
                                            slot_symbol, None,
                                            tok, slot_symbol, None)


# ── Second pass: merge content entries into apertium-glb dictionaries ───
# For each target dix, replace everything between the
# '<!-- Autogenerated common words -->' marker and the closing `</section>`
# of section main with the freshly-generated content entries.
# A .bak file is written next to each dix before overwriting.

import os
import shutil

APERTIUM_ROOT = "/home/paleos/ApplicationSource/GlobasaTranslation"
APERTIUM_MARKER = "<!-- Autogenerated common words -->"

APERTIUM_TARGETS = [
    ("apertium-glb/apertium-glb.glb.dix",              "dictionary_un_content.xml"),
    ("apertium-glb-eng/apertium-glb-eng.glb-eng.dix",  "dictionary_En_content.xml"),
    ("apertium-glb-deu/apertium-glb-deu.glb-deu.dix",  "dictionary_De_content.xml"),
    ("apertium-glb-fra/apertium-glb-fra.glb-fra.dix",  "dictionary_Fr_content.xml"),
    ("apertium-glb-nld/apertium-glb-nld.glb-nld.dix",  "dictionary_Nl_content.xml"),
]

_MAIN_SECTION_OPEN_RE = re.compile(r'<section\s+id\s*=\s*"main"[^>]*>')


def merge_into_dix(dix_path, entries_path):
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


print("\nMerging content entries into apertium dictionaries…")
for rel_dix, entries_file in APERTIUM_TARGETS:
    merge_into_dix(os.path.join(APERTIUM_ROOT, rel_dix), entries_file)

