import csv
import re
import markdown

from Lexilista_parser import (GlossPoS, VerbType, parseEntry,
                              SLANG_NOUN_QUALIFIERS as _SLANG_NOUN_QUALIFIERS)
import images_store
from GlobasaTransliterators import globasaCountSyllables, globasaStressSentence

import pandas as pd


class AnkiFields:
    """Fields of the v3 card template — same as v2 plus dedicated slots for
    every VerbType so no gloss is silently dropped."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.Lexi = ""
        self.EnfasisdoLexi = ""
        self.PoS = ["", "", ""]
        self.Mena = ["", "", ""]
        self.AnimateAdjective = ""
        self.InanimateAdjective = ""
        self.SlangMena = ""
        self.Imajelinku = ""
        self.ImajeAsel = ""
        self.Faleanimalinku = ""
        self.Faleanimaasel = ""
        self.NSFW = ""
        self.DuayumImaje = ""
        self.DuayumImajeAsel = ""
        self.Anaphor = ""
        self.AloAnaphor = ""
        self.Oposmenalexi = ""
        self.GlobasaMisal = ""
        self.MisalClozed = ""
        self.MisalBasatayti = ""
        self.FaleliMisal = ""
        self.FaleliMisalClozed = ""
        self.FaleliMisalBasatayti = ""
        self.TigayumMisal = ""
        self.TigayumMisalClozed = ""
        self.TigayumMisalBasatayti = ""
        self.Transitive = ""
        self.Intransitive = ""
        self.IntransitiveCu = ""
        self.Copula = ""
        self.EchoTransitive = ""
        self.Auxiliary = ""
        self.Feeling = ""
        self.State = ""
        self.Paladoawdio = ""
        self.PaladoKodek = ""
        self.Soti = ""
        self.Sotiasel = ""
        self.Sotikodek = ""
        self.Sotilabel = ""
        self.MaxpulKostrui1 = ""
        self.MaxpulKostrui1Basatayti = ""
        self.MaxpulKostrui2 = ""
        self.MaxpulKostrui2Basatayti = ""
        # Preposition-deck example slots: up to four generic examples per
        # preposition (no part-of-speech split — prepositions are mono-PoS).
        self.PrepMisal1 = ""
        self.PrepMisal1Clozed = ""
        self.PrepMisal1Basatayti = ""
        self.PrepMisal2 = ""
        self.PrepMisal2Clozed = ""
        self.PrepMisal2Basatayti = ""
        self.PrepMisal3 = ""
        self.PrepMisal3Clozed = ""
        self.PrepMisal3Basatayti = ""
        self.PrepMisal4 = ""
        self.PrepMisal4Clozed = ""
        self.PrepMisal4Basatayti = ""
        self.tags = ""


PoS_display_dict_Eng = {
    GlossPoS.NOUN: "Noun",
    GlossPoS.VERB: "Verb",
    GlossPoS.ADJECTIVE: "Adjective",
    GlossPoS.VERBAL_ADVERB: "Verbal-Adverb",
    GlossPoS.ADVERB: "Adverb",
    GlossPoS.INTERJECTION: "Interjection",
    GlossPoS.PREFIX: "Prefix",
    GlossPoS.PRONOUN: "Pronoun",
    GlossPoS.PROPER_NOUN: "Proper noun",
    GlossPoS.PROPER_ADJECTIVE: "Proper adjective",
    GlossPoS.DETERMINER: "Determiner",
    GlossPoS.CONJUNCTION: "Conjunction",
    GlossPoS.NUMBER: "Number",
    GlossPoS.PARTICLE: "Particle",
    GlossPoS.PREPOSITION: "Preposition",
    GlossPoS.POSTPOSITION: "Postposition",
    GlossPoS.PHRASE: "Phrase",
    GlossPoS.VERB_PHRASE: "Verb phrase",
    GlossPoS.NOUN_PHRASE: "Noun phrase",
    GlossPoS.ADJECTIVE_PHRASE: "Adjective phrase",
    GlossPoS.CONJUNCTION_PHRASE: "Conjunction phrase",
    GlossPoS.PHRASAL_PREPOSITION: "Phrasal preposition",
    GlossPoS.PHRASAL_CONJUNCTION: "Phrasal conjunction",
    GlossPoS.PREPOSITIONAL_PHRASE: "Prepositional phrase",
    GlossPoS.POSSESSIVE_PRONOUN: "Possessive pronoun",
    GlossPoS.POSSESSIVE_ADJECTIVE: "Possessive adjective",
    GlossPoS.PHRASAL_ADVERB: "Phrasal adverb",
}


menalari_name = "word-list.csv"
ranking_name = "Doxo_course_ranking.csv"

df = pd.read_csv(menalari_name, index_col=0)
df.index = df.index.astype(str).str.strip()
df = df[~df.index.duplicated(keep="first")]
df = df[df.index != "nan"]
prnf = pd.read_csv("menalariPronouns_edited.tsv", sep="\t", index_col=0)
image_store = images_store.load_images()
gfcf = pd.read_csv("graphic_blacklist", index_col=0, sep=",")
prnf.fillna(False, inplace=True)
construction_frame = pd.read_excel("Constructions.xlsx", index_col=0, na_values=False)
construction_frame.fillna(False, inplace=True)
try:
    lexi_misal_frame = pd.read_excel("LexiMisal.xlsx", index_col=0, dtype=str)
    lexi_misal_frame = lexi_misal_frame.fillna("")
except FileNotFoundError:
    lexi_misal_frame = pd.DataFrame(columns=[
        "NameliMisal", "NameliMisalEng",
        "FaleliMisal", "FaleliMisalEng",
        "TigayumMisal", "TigayumMisalEng",
    ])
    lexi_misal_frame.index.name = "Lexi"

try:
    prep_misal_frame = pd.read_excel("PrepMisal.xlsx", index_col=0, dtype=str)
    prep_misal_frame = prep_misal_frame.fillna("")
except FileNotFoundError:
    prep_misal_frame = pd.DataFrame(columns=[
        "Misal1", "Misal1Eng", "Misal2", "Misal2Eng",
        "Misal3", "Misal3Eng", "Misal4", "Misal4Eng",
    ])
    prep_misal_frame.index.name = "Lexi"


_ANNOTATION_PREFIX_RE = re.compile(
    r"^(?:n|v\.tr|v\.intr|v\.aux|v\.cop|adj|adv|interj|prep|conj|det|pron|"
    r"num|par|prop\s+\w+|poss\s+\w+|pfx|sfx)"
    r"(?:\s+phrs)?"
    r"(?:\s*\([^)]*\))?"          # optional qualifier in parens
    r"\s*:\s*",
    re.IGNORECASE,
)


def _split_items(s):
    """Split on commas that are not inside parentheses. Returns trimmed items."""
    items, cur, depth = [], [], 0
    for ch in s:
        if ch == "(":
            depth += 1
            cur.append(ch)
        elif ch == ")":
            depth = max(0, depth - 1)
            cur.append(ch)
        elif ch == "," and depth == 0:
            items.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if cur:
        items.append("".join(cur).strip())
    return [i for i in items if i]


def _split_annotation(seg):
    """Returns (annotation_prefix, body) where prefix includes trailing ': '."""
    s = seg.strip()
    m = _ANNOTATION_PREFIX_RE.match(s)
    if m:
        return s[:m.end()], s[m.end():]
    return "", s


def _normalise_item(item):
    """Strip parentheticals (incl. markdown _italics_), collapse whitespace."""
    s = re.sub(r"\s*\([^)]*\)", "", item)
    s = re.sub(r"\s+", " ", s)
    return s.strip(" ,;").lower()


def _apply_to_exclude(eng_text, exclude_text, lexi=""):
    """Within-segment item exclusion. For each `; `-separated segment, drop
    comma-separated items (parenthesis-aware) whose normalised form matches
    any item in `exclude_text`. If a segment has no items left, the segment
    is removed entirely. Warns when `exclude_text` matched nothing."""
    if not exclude_text or not exclude_text.strip():
        return eng_text
    _, excl_body = _split_annotation(exclude_text)
    excl_items = {_normalise_item(it) for it in _split_items(excl_body)}
    excl_items.discard("")
    if not excl_items:
        return eng_text
    matched = False
    kept_segments = []
    for seg in eng_text.split("; "):
        prefix, body = _split_annotation(seg)
        kept_items = []
        for item in _split_items(body):
            if _normalise_item(item) in excl_items:
                matched = True
                continue
            kept_items.append(item.strip())
        if kept_items:
            kept_segments.append(prefix + ", ".join(kept_items))
    if not matched:
        print(f"WARN: to_exclude={exclude_text!r} did not match any gloss "
              f"segment of {lexi!r} (Constructions.xlsx may be stale)")
    return "; ".join(kept_segments).strip("; ,")


PREPOSITION_HEAD_PARTS = {"p", "p jm", "jm p"}

# Shared with Word Viewer, which gives these their own table row.
SLANG_NOUN_QUALIFIERS = _SLANG_NOUN_QUALIFIERS


def _is_preposition_wordclass(wc):
    """True when the WordClass head segment is a preposition class. Routes
    prepositions to a separate deck whose template focuses on example
    sentences (the dictionary gloss alone rarely conveys the spatial /
    semantic distinction between Globasa prepositions)."""
    if not wc:
        return False
    head = str(wc).split(";")[0].strip()
    return head in PREPOSITION_HEAD_PARTS


def _is_t_class_wordclass(wc):
    """True if the WordClass declares the word as a t-class adjective in any
    of its compound parts. An adverb-style gloss on a t-class word is a
    verbal adverb (no -mo suffix; same surface form as the adjective)."""
    if not wc:
        return False
    if wc.startswith("tabl: "):
        wc = wc[len("tabl: "):]
    for part in wc.split(";"):
        part = part.strip()
        if part == "t" or part.startswith("t "):
            return True
    return False


def _assign_verb_gloss(fields, gloss):
    """Route a parsed verb gloss into the correct AnkiFields slot."""
    html = markdown.markdown(gloss.gloss)
    match gloss.verb_type:
        case VerbType.TRANSITIVE:
            fields.Transitive = html
        case VerbType.INTRANSITIVE:
            fields.Intransitive = html
        case VerbType.INTRANSITIVE_CU:
            fields.IntransitiveCu = html
        case VerbType.COPULAR:
            fields.Copula = html
        case VerbType.ECHO_TRANSITIVE:
            fields.EchoTransitive = html
        case VerbType.AUXILIARY:
            fields.Auxiliary = html
        case VerbType.FEELING:
            fields.Feeling = html
        case VerbType.STATE:
            fields.State = html
        case _:
            raise AssertionError(
                f"Unhandled VerbType {gloss.verb_type!r} for {fields.Lexi!r}"
            )


with open("./" + ranking_name, newline="") as ranking_file, \
        open("AnkiList.csv", "w", newline="") as AnkiList, \
        open("AnkiList_Prepositions.csv", "w", newline="") as AnkiListPrep:
    AnkiWriter = csv.writer(AnkiList, delimiter="\t", lineterminator="\n")
    AnkiPrepWriter = csv.writer(AnkiListPrep, delimiter="\t", lineterminator="\n")
    rankingReader = csv.reader(ranking_file, delimiter="\t", quotechar="'")
    fields = AnkiFields()
    n_main = n_prep = 0

    for row in rankingReader:
        if not row:
            continue
        fields.reset()
        if row[0] not in df.index or str(row[0]).lower() == "devtest":
            continue
        print(row[0])
        fields.Lexi = row[0]
        if globasaCountSyllables(row[0]) > 1:
            fields.EnfasisdoLexi = globasaStressSentence(row[0]).strip()
        selected_rows = df.loc[row[0]]

        if row[0] in prnf.index and isinstance(prnf.loc[row[0]].Pronoun, str):
            pronouns = prnf.loc[row[0]].Pronoun.split(",")
            fields.Anaphor = pronouns[0]
            if len(pronouns) > 1:
                fields.AloAnaphor = pronouns[1]

        antonyms = selected_rows["Antonyms"]
        if isinstance(antonyms, str) and antonyms:
            fields.Oposmenalexi = str(antonyms)

        englishRawGlosses = str(selected_rows["TranslationEng"])
        if row[0] in construction_frame.index:
            excl = construction_frame.loc[row[0]]["to_exclude"]
            if isinstance(excl, str):
                englishRawGlosses = _apply_to_exclude(englishRawGlosses, excl, row[0])

        if row[0] in construction_frame.index:
            crow = construction_frame.loc[row[0]]
            for src_col, dst in (("construction1", "MaxpulKostrui1"),
                                  ("construction1basatayti", "MaxpulKostrui1Basatayti"),
                                  ("construction2", "MaxpulKostrui2"),
                                  ("construction2basatayti", "MaxpulKostrui2Basatayti")):
                val = crow.get(src_col)
                if isinstance(val, str) and val.strip():
                    setattr(fields, dst, markdown.markdown(val.strip()))

        if englishRawGlosses:
            wordclass = str(selected_rows["WordClass"])
            glosses = parseEntry(englishRawGlosses, wordclass)
            print(str(glosses))
            is_t_class = _is_t_class_wordclass(wordclass)
            # Walk every gloss in order, consuming one PoS slot each. Verb
            # glosses ALSO get a "Verb" PoS label so the card template can show
            # e.g. "Noun: bed | Verb" with the actual transitive/intransitive
            # text rendered from the dedicated verb-type field. "Verb" only
            # gets one slot regardless of how many verb-type meanings the word
            # has — the per-type fields carry the actual content.
            slot = 0
            verb_label_set = False
            pos_to_slot = {}

            def _append_mena(slot_i, gloss_text):
                rendered = markdown.markdown(gloss_text)
                existing = fields.Mena[slot_i]
                if not existing:
                    fields.Mena[slot_i] = rendered
                    return
                prev_inner = re.sub(r"^<p>|</p>$", "", existing).strip()
                new_inner = re.sub(r"^<p>|</p>$", "", rendered).strip()
                fields.Mena[slot_i] = f"<p>{prev_inner}; {new_inner}</p>"

            def _append_slang(gloss_text):
                rendered = markdown.markdown(gloss_text)
                if not fields.SlangMena:
                    fields.SlangMena = rendered
                    return
                prev_inner = re.sub(r"^<p>|</p>$", "", fields.SlangMena).strip()
                new_inner = re.sub(r"^<p>|</p>$", "", rendered).strip()
                fields.SlangMena = f"<p>{prev_inner}; {new_inner}</p>"

            for gloss in glosses:
                effective_pos = gloss.pos
                if effective_pos == GlossPoS.ADVERB and is_t_class:
                    effective_pos = GlossPoS.VERBAL_ADVERB

                qual = (gloss.qualifier or "").lower()
                if effective_pos == GlossPoS.ADJECTIVE and "animate noun" in qual:
                    if "inanimate" in qual:
                        fields.InanimateAdjective = markdown.markdown(gloss.gloss)
                    else:
                        fields.AnimateAdjective = markdown.markdown(gloss.gloss)
                    continue

                if effective_pos == GlossPoS.NOUN and qual in SLANG_NOUN_QUALIFIERS:
                    _append_slang(gloss.gloss)
                    continue

                if effective_pos != GlossPoS.VERB:
                    existing = pos_to_slot.get(effective_pos)
                    if existing is not None:
                        _append_mena(existing, gloss.gloss)
                    elif slot < len(fields.PoS):
                        _append_mena(slot, gloss.gloss)
                        fields.PoS[slot] = PoS_display_dict_Eng[effective_pos]
                        pos_to_slot[effective_pos] = slot
                        slot += 1
                    else:
                        slot += 1
                else:
                    if gloss.verb_type is None:
                        existing = pos_to_slot.get(GlossPoS.VERB)
                        if existing is not None:
                            _append_mena(existing, gloss.gloss)
                        elif slot < len(fields.PoS):
                            _append_mena(slot, gloss.gloss)
                            fields.PoS[slot] = PoS_display_dict_Eng[GlossPoS.VERB]
                            pos_to_slot[GlossPoS.VERB] = slot
                            slot += 1
                        else:
                            slot += 1
                        verb_label_set = True
                        continue
                    _assign_verb_gloss(fields, gloss)
                    if not verb_label_set:
                        if slot < len(fields.PoS):
                            fields.PoS[slot] = PoS_display_dict_Eng[GlossPoS.VERB]
                        slot += 1
                        verb_label_set = True

        is_prep_row = _is_preposition_wordclass(selected_rows["WordClass"])

        if is_prep_row:
            # Prep deck: up to four generic example slots, sourced from
            # PrepMisal.xlsx (curated). The corpus first-occurrence falls back
            # into Misal1 if the prep has no curated examples. No image/audio
            # fields — spatial prepositions live in PrepositionAnkiMaker.py.
            misal_curated = row[0] in prep_misal_frame.index
            if misal_curated:
                prow = prep_misal_frame.loc[row[0]]
                for i in range(1, 5):
                    g = str(prow.get(f"Misal{i}", "") or "").strip()
                    if not g:
                        continue
                    setattr(fields, f"PrepMisal{i}", markdown.markdown(g))
                    setattr(fields, f"PrepMisal{i}Clozed",
                            markdown.markdown(re.sub(r"\*\*.*?\*\*", "[...]", g)))
                    e = str(prow.get(f"Misal{i}Eng", "") or "").strip()
                    if e:
                        setattr(fields, f"PrepMisal{i}Basatayti",
                                markdown.markdown(e))
            else:
                if len(row) > 1 and row[1]:
                    fields.PrepMisal1 = markdown.markdown(str(row[1]))
                    fields.PrepMisal1Clozed = markdown.markdown(
                        re.sub(r"\*\*.*?\*\*", "[...]", str(row[1]))
                    )
                if len(row) > 3 and row[3]:
                    fields.PrepMisal1Basatayti = markdown.markdown(str(row[3]))

            tags = []
            if selected_rows["Tags"] == selected_rows["Tags"]:
                tags += str(selected_rows["Tags"]).replace(" ", "_").split(",_")
            if not misal_curated and len(row) > 2 and row[2]:
                tags += [str(row[2]).replace(" ", "_")]
            fields.tags = " ".join(tags)

            AnkiPrepWriter.writerow([
                fields.Lexi, fields.EnfasisdoLexi,
                fields.PoS[0],
                fields.Mena[0],
                fields.PrepMisal1, fields.PrepMisal1Clozed, fields.PrepMisal1Basatayti,
                fields.PrepMisal2, fields.PrepMisal2Clozed, fields.PrepMisal2Basatayti,
                fields.PrepMisal3, fields.PrepMisal3Clozed, fields.PrepMisal3Basatayti,
                fields.PrepMisal4, fields.PrepMisal4Clozed, fields.PrepMisal4Basatayti,
                fields.Oposmenalexi,
                fields.tags,
            ])
            n_prep += 1
            continue

        misal_curated = row[0] in lexi_misal_frame.index
        if misal_curated:
            mrow = lexi_misal_frame.loc[row[0]]
            for src_glb, src_eng, dst_glb, dst_cloze, dst_eng in (
                ("NameliMisal", "NameliMisalEng",
                 "GlobasaMisal", "MisalClozed", "MisalBasatayti"),
                ("FaleliMisal", "FaleliMisalEng",
                 "FaleliMisal", "FaleliMisalClozed", "FaleliMisalBasatayti"),
                ("TigayumMisal", "TigayumMisalEng",
                 "TigayumMisal", "TigayumMisalClozed", "TigayumMisalBasatayti"),
            ):
                g = str(mrow.get(src_glb, "") or "").strip()
                if not g:
                    continue
                setattr(fields, dst_glb, markdown.markdown(g))
                setattr(fields, dst_cloze,
                        markdown.markdown(re.sub(r"\*\*.*?\*\*", "[...]", g)))
                e = str(mrow.get(src_eng, "") or "").strip()
                if e:
                    setattr(fields, dst_eng, markdown.markdown(e))
        else:
            if len(row) > 1 and row[1]:
                fields.GlobasaMisal = markdown.markdown(str(row[1]))
                fields.MisalClozed = markdown.markdown(
                    re.sub(r"\*\*.*?\*\*", "[...]", str(row[1]))
                )
            if len(row) > 3 and row[3]:
                fields.MisalBasatayti = markdown.markdown(str(row[3]))

        tags = []
        if selected_rows["Tags"] == selected_rows["Tags"]:
            tags += str(selected_rows["Tags"]).replace(" ", "_").split(",_")
        if not misal_curated and len(row) > 2 and row[2]:
            tags += [str(row[2]).replace(" ", "_")]
        fields.tags = " ".join(tags)

        # One still per PoS group, in PoS-group order, so the card's two images
        # line up with the PoS1/Mena1 and PoS2/Mena2 glosses printed beside them.
        # Still and animation are independent now: a word can have both.
        img_rec = image_store.get(row[0])
        if img_rec:
            slots = images_store.anki_slots(img_rec)
            fields.Imajelinku = slots["Imajelinku"]
            fields.ImajeAsel = slots["ImajeAsel"]
            fields.DuayumImaje = slots["DuayumImaje"]
            fields.DuayumImajeAsel = slots["DuayumImajeAsel"]
            fields.Faleanimalinku = slots["Faleanimalinku"]
            fields.Faleanimaasel = slots["Faleanimaasel"]
            if any(slots.values()) and str(row[0]) in gfcf.index:
                fields.NSFW = "y"

        out_row = [
            fields.Lexi, fields.EnfasisdoLexi,
            fields.PoS[0], fields.PoS[1], fields.PoS[2],
            fields.Mena[0], fields.Mena[1], fields.Mena[2],
            fields.AnimateAdjective, fields.InanimateAdjective, fields.SlangMena,
            fields.Transitive, fields.EchoTransitive, fields.Intransitive,
            fields.IntransitiveCu, fields.Copula, fields.Auxiliary,
            fields.Feeling, fields.State,
            fields.Imajelinku, fields.ImajeAsel, fields.NSFW,
            fields.DuayumImaje, fields.DuayumImajeAsel,
            fields.Faleanimalinku, fields.Faleanimaasel,
            fields.Anaphor, fields.Oposmenalexi,
            fields.GlobasaMisal, fields.MisalClozed, fields.MisalBasatayti,
            fields.FaleliMisal, fields.FaleliMisalClozed, fields.FaleliMisalBasatayti,
            fields.TigayumMisal, fields.TigayumMisalClozed, fields.TigayumMisalBasatayti,
            fields.Paladoawdio, fields.PaladoKodek,
            fields.Soti, fields.Sotiasel, fields.Sotikodek, fields.Sotilabel,
            fields.MaxpulKostrui1, fields.MaxpulKostrui1Basatayti,
            fields.MaxpulKostrui2, fields.MaxpulKostrui2Basatayti,
            fields.tags,
        ]
        AnkiWriter.writerow(out_row)
        n_main += 1

print(f"wrote AnkiList.csv: {n_main} rows; AnkiList_Prepositions.csv: {n_prep} rows")
