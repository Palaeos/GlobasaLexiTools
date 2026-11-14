import contextlib
import os
import pandas as pd

from Lexilista_parser import parseWordEntry
from apertium_common import (
    FUNCTION_POS, NOUN_SYMBOLS, apertium_symbol, expand_gloss_tokens,
    genderDict, split_foreign_gender, lemma_repr, bilingual_entry,
    merge_into_dix, APERTIUM_ROOT,
)


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
]

# Pairs whose glb-X content entries come from build_bidix.py (word list plus
# Wiktionary extension, checked against the target analyser). This script
# still writes their *_fn drafts, an aid for the hand-curated part of each
# pair dix; nothing here merges into a pair dix any more.
BIDIX_LANGS = {"En", "De", "Fr"}


# ── XML output ──────────────────────────────────────────────────────────
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
    emit(handle, bilingual_entry(lang_label, word, lemma_symbol, lemma_gender,
                                 gloss, gloss_symbol, gloss_gender))


# ── Data loading ────────────────────────────────────────────────────────
df = pd.read_csv("word-list.csv", index_col=0, keep_default_na=False)
df.index = df.index.astype(str).str.strip()

gender_frame = pd.read_csv("menalariPronouns_edited.tsv", sep="\t",
                           index_col=0, keep_default_na=False)
# Duplicate WORDS, not duplicate rows: drop_duplicates() compares the columns only, so two
# words with the same English gloss and pronoun (medisdom/hospital "hospital", to) lost one of
# them, which then got the GD paradigm (55 words). build_bidix.py dedups the same way.
gender_frame = gender_frame[~gender_frame.index.duplicated(keep="first")]



# ── Main ────────────────────────────────────────────────────────────────
with contextlib.ExitStack() as stack:
    def open_dict(label, target):
        return stack.enter_context(
            open(f"dictionary_{label}_{target}.xml", "w", newline=""))

    handle_un = {t: open_dict("un", t) for t in ("fn", "content")}
    handle_lang = {(label, t): open_dict(label, t)
                   for label, _, _, _ in LANGS
                   for t in ("fn", "content")
                   if not (t == "content" and label in BIDIX_LANGS)}

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
                if not slot_glosses or (label, target) not in handle_lang:
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


# ── Second pass: merge the Globasa monolingual content entries ─────────
# Replaces everything between '<!-- Autogenerated common words -->' and the
# closing </section> of section main in apertium-glb.glb.dix (.bak kept).
# The glb-X bilingual dixes are built by build_bidix.py.


print("\nMerging content entries into apertium-glb…")
merge_into_dix(os.path.join(APERTIUM_ROOT, "apertium-glb/apertium-glb.glb.dix"),
               "dictionary_un_content.xml")
