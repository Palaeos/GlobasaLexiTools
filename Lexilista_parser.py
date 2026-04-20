import fastenum
import re
from typing import NamedTuple, Optional


class GlossPoS(fastenum.Enum):
    NOUN = 0
    PROPER_NOUN = 1
    VERB = 2
    VERB_PHRASE = 3
    ADJECTIVE = 4
    PROPER_ADJECTIVE = 5
    VERBAL_ADVERB = 6
    ADVERB = 7
    INTERJECTION = 8
    PRONOUN = 9
    NUMBER = 10
    PREPOSITION = 11
    PHRASAL_PREPOSITION = 12
    PREPOSITIONAL_PHRASE = 13
    POSTPOSITION = 14
    CONJUNCTION = 15
    DETERMINER = 16
    PARTICLE = 17
    PREFIX = 19
    PHRASE = 23
    POSSESSIVE_PRONOUN = 24
    POSSESSIVE_ADJECTIVE = 25
    PHRASAL_ADVERB = 28
    NOUN_PHRASE = 29
    CONJUNCTION_PHRASE = 30
    ADJECTIVE_PHRASE = 32
    PHRASAL_CONJUNCTION = 33


class VerbType(fastenum.Enum):
    INTRANSITIVE = 0
    TRANSITIVE = 1
    ECHO_TRANSITIVE = 2
    COPULAR = 3
    AUXILIARY = 4
    INTRANSITIVE_CU = 5  # b.oro/b.oro.harka — optional -cu
    FEELING = 6           # b.oro.hisi — stative feeling verb
    STATE = 7             # b.oro.jotay — stative condition verb


class AffixType(fastenum.Enum):
    PREFIX = 0
    SUFFIX = 1


class ParsedGloss(NamedTuple):
    gloss: str
    pos: GlossPoS
    verb_type: Optional[VerbType] = None
    qualifier: Optional[str] = None
    affix_type: Optional[AffixType] = None


# Maps annotation prefix -> list of (GlossPoS, Optional[VerbType], Optional[AffixType])
# For compound suffixes, the list has multiple entries (one ParsedGloss per element).
ANNOTATION_MAP = {
    # Nouns
    "n": [(GlossPoS.NOUN, None, None)],
    "n phrs": [(GlossPoS.NOUN_PHRASE, None, None)],
    "n sfx": [(GlossPoS.NOUN, None, AffixType.SUFFIX)],
    # Verbs
    "v.tr": [(GlossPoS.VERB, VerbType.TRANSITIVE, None)],
    "v.intr": [(GlossPoS.VERB, VerbType.INTRANSITIVE, None)],
    "v.intr (optional -cu)": [(GlossPoS.VERB, VerbType.INTRANSITIVE_CU, None)],
    "v.cop": [(GlossPoS.VERB, VerbType.COPULAR, None)],
    "v.aux": [(GlossPoS.VERB, VerbType.AUXILIARY, None)],
    "v phrs": [(GlossPoS.VERB_PHRASE, None, None)],
    "v.tr sfx": [(GlossPoS.VERB, VerbType.TRANSITIVE, AffixType.SUFFIX)],
    # Compound suffixes (produce TWO entries)
    "n/v.tr sfx": [(GlossPoS.NOUN, None, AffixType.SUFFIX), (GlossPoS.VERB, VerbType.TRANSITIVE, AffixType.SUFFIX)],
    "n/v.intr sfx": [(GlossPoS.NOUN, None, AffixType.SUFFIX), (GlossPoS.VERB, VerbType.INTRANSITIVE, AffixType.SUFFIX)],
    "adj/adv sfx": [(GlossPoS.ADJECTIVE, None, AffixType.SUFFIX), (GlossPoS.VERBAL_ADVERB, None, AffixType.SUFFIX)],
    # Adjectives
    "adj": [(GlossPoS.ADJECTIVE, None, None)],
    "adj phrs": [(GlossPoS.ADJECTIVE_PHRASE, None, None)],
    "adj sfx": [(GlossPoS.ADJECTIVE, None, AffixType.SUFFIX)],
    # Adverbs
    "adv": [(GlossPoS.ADVERB, None, None)],
    "adv phrs": [(GlossPoS.PHRASAL_ADVERB, None, None)],
    "adv sfx": [(GlossPoS.ADVERB, None, AffixType.SUFFIX)],
    # Globasa-specific adverb marker (manerlexi)
    "m": [(GlossPoS.ADVERB, None, None)],
    # Interjections
    "interj": [(GlossPoS.INTERJECTION, None, None)],
    # Prepositions
    "prep": [(GlossPoS.PREPOSITION, None, None)],
    "prep phrs": [(GlossPoS.PHRASAL_PREPOSITION, None, None)],
    "prep phrase": [(GlossPoS.PREPOSITIONAL_PHRASE, None, None)],
    # Conjunctions
    "conj": [(GlossPoS.CONJUNCTION, None, None)],
    "conj phrs": [(GlossPoS.PHRASAL_CONJUNCTION, None, None)],
    # Copula + preposition phrases
    "cop plus prep": [(GlossPoS.VERB, VerbType.COPULAR, None)],
    # Determiners
    "det": [(GlossPoS.DETERMINER, None, None)],
    # Pronouns
    "pron": [(GlossPoS.PRONOUN, None, None)],
    # Numbers
    "num": [(GlossPoS.NUMBER, None, None)],
    # Particles
    "par": [(GlossPoS.PARTICLE, None, None)],
    # Proper nouns/adjectives
    "prop n": [(GlossPoS.PROPER_NOUN, None, None)],
    "prop adj": [(GlossPoS.PROPER_ADJECTIVE, None, None)],
    # Possessives
    "poss pron": [(GlossPoS.POSSESSIVE_PRONOUN, None, None)],
    "poss adj": [(GlossPoS.POSSESSIVE_ADJECTIVE, None, None)],
    # Prefixes
    "pfx": [(GlossPoS.PREFIX, None, AffixType.PREFIX)],
    "root pfx": [(GlossPoS.PREFIX, None, AffixType.PREFIX)],
    # Bound roots
    "bound root": [(GlossPoS.PREFIX, None, AffixType.PREFIX)],
    # Root suffix
    "root sfx (attached to nouns)": [(GlossPoS.NOUN, None, AffixType.SUFFIX)],
    # Generic phrase
    "phrs": [(GlossPoS.PHRASE, None, None)],
}

# Pre-sorted longest-first for prefix matching
_SORTED_PREFIXES = sorted(ANNOTATION_MAP.keys(), key=len, reverse=True)

# Translation-language annotation prefixes (Esperanto, Spanish, etc.)
_TRANSLATION_ANNOTATION_MAP = {
    "s": [(GlossPoS.NOUN, None, None)],
    "v.tr": [(GlossPoS.VERB, VerbType.TRANSITIVE, None)],
    "v.ntr": [(GlossPoS.VERB, VerbType.INTRANSITIVE, None)],
    "tr": [(GlossPoS.VERB, VerbType.TRANSITIVE, None)],
    "intr": [(GlossPoS.VERB, VerbType.INTRANSITIVE, None)],
    "adj": [(GlossPoS.ADJECTIVE, None, None)],
    "adv": [(GlossPoS.ADVERB, None, None)],
    "interj": [(GlossPoS.INTERJECTION, None, None)],
    "prop n": [(GlossPoS.PROPER_NOUN, None, None)],
}

_SORTED_TRANSLATION_PREFIXES = sorted(_TRANSLATION_ANNOTATION_MAP.keys(), key=len, reverse=True)


# Regex for detecting gloss-internal parentheticals (optional context)
# Excludes (_italic_) markdown clarifications (contain underscores)
_GLOSS_CONTEXT_RE = re.compile(r'^(\([^_)]+\)\s*)+')


def _expand_gloss_context(gloss: str) -> list[str]:
    """Returns [compact, verbose] if leading parens found, else [gloss].
    E.g. '(have a particular) smell' -> ['smell', 'have a particular smell']
    """
    m = _GLOSS_CONTEXT_RE.match(gloss)
    if m:
        compact = gloss[m.end():].strip()
        verbose = re.sub(r'[()]', '', gloss).strip()
        verbose = re.sub(r'\s+', ' ', verbose)
        if compact and verbose and compact != verbose:
            return [compact, verbose]
    return [gloss]


def _parse_annotation_prefix(segment: str, annotation_map=None, sorted_prefixes=None):
    """Match segment against known annotation prefixes (longest-first).
    Returns (prefix_key, gloss_text, qualifier_or_None).
    If no match, returns (None, segment, None).
    """
    if annotation_map is None:
        annotation_map = ANNOTATION_MAP
    if sorted_prefixes is None:
        sorted_prefixes = _SORTED_PREFIXES

    seg_stripped = segment.strip()
    seg_lower = seg_stripped.lower()

    # Try exact match against known prefixes (longest first)
    for prefix in sorted_prefixes:
        if seg_lower.startswith(prefix + ": ") or seg_lower.startswith(prefix + ":"):
            colon_pos = seg_lower.index(":", len(prefix))
            gloss = seg_stripped[colon_pos + 1:].strip()
            # Extract qualifier from parenthetical in the matched prefix
            qual_match = re.search(r'\(([^)]+)\)', prefix)
            qualifier = qual_match.group(1) if qual_match else None
            return (prefix, gloss, qualifier)

    # Try stripping parenthetical from the segment and matching base
    paren_match = re.match(r'^([a-z][a-z./]*)\s*\(([^)]+)\)\s*:', seg_lower)
    if paren_match:
        base = paren_match.group(1).strip()
        qualifier = paren_match.group(2).strip()
        if base in annotation_map:
            colon_pos = seg_lower.index(":", paren_match.start())
            gloss = seg_stripped[colon_pos + 1:].strip()
            return (base, gloss, qualifier)

    # Try multi-word base with parenthetical: "poss adj (relative clause):"
    paren_match2 = re.match(r'^([a-z][a-z./ ]+?)\s*\(([^)]+)\)\s*:', seg_lower)
    if paren_match2:
        base = paren_match2.group(1).strip()
        qualifier = paren_match2.group(2).strip()
        if base in annotation_map:
            colon_pos = seg_lower.index(":", paren_match2.start())
            gloss = seg_stripped[colon_pos + 1:].strip()
            return (base, gloss, qualifier)

    return (None, seg_stripped, None)


# WordClass suffix -> VerbType mapping for refinement
transDict = {
    "nenoj": VerbType.INTRANSITIVE,
    "oj": VerbType.TRANSITIVE,
    "lin": VerbType.COPULAR,
    "ru": VerbType.ECHO_TRANSITIVE,
    "sah": VerbType.AUXILIARY,
    "hisi": VerbType.FEELING,
    "jotay": VerbType.STATE,
    "harka": VerbType.INTRANSITIVE_CU,
}


def _get_verb_semantic_class(lexiklase: str) -> Optional[VerbType]:
    """Extract verb semantic class from WordClass string.
    Returns the VerbType refinement for v.intr annotations, or None.
    """
    parts = lexiklase.replace(";", ".").split(".")
    for part in reversed(parts):
        part = part.strip()
        if part in transDict:
            return transDict[part]
    return None


def _refine_verb_type(base_verb_type: VerbType, lexiklase: str, annotation_prefix: str) -> VerbType:
    """Refine VerbType based on WordClass when annotation alone is ambiguous."""
    if base_verb_type == VerbType.INTRANSITIVE:
        # v.intr: -> check WordClass for hisi/jotay
        semantic = _get_verb_semantic_class(lexiklase)
        if semantic == VerbType.FEELING:
            return VerbType.FEELING
        elif semantic == VerbType.STATE:
            return VerbType.STATE
        return base_verb_type
    elif base_verb_type == VerbType.TRANSITIVE:
        # v.tr: -> check WordClass for .ru (echo transitive)
        if ".ru" in lexiklase:
            return VerbType.ECHO_TRANSITIVE
        return base_verb_type
    return base_verb_type


def _parseAnnotatedEnglish(englishText: str, lexiklase: str) -> list[ParsedGloss]:
    """Parse English gloss text using explicit PoS annotations.
    Returns list of ParsedGloss with PoS inferred from annotations + WordClass.
    """
    segments = englishText.strip().split("; ")
    output = []

    for seg in segments:
        prefix_key, gloss, qualifier = _parse_annotation_prefix(seg)

        if prefix_key is None:
            # Unannotated segment — use WordClass fallback
            if lexiklase in PoSDict:
                pos_list = PoSDict[lexiklase]
                idx = len(output)
                if idx < len(pos_list):
                    pos = pos_list[idx]
                    output.append(ParsedGloss(gloss, pos))
                else:
                    output.append(ParsedGloss(gloss, pos_list[-1]))
            else:
                output.append(ParsedGloss(gloss, GlossPoS.PHRASE))
            continue

        if prefix_key not in ANNOTATION_MAP:
            # Should not happen since _parse_annotation_prefix only returns keys in the map
            output.append(ParsedGloss(gloss, GlossPoS.PHRASE, None, qualifier))
            continue

        entries = ANNOTATION_MAP[prefix_key]

        for pos, vtype, afx in entries:
            # Refine verb type using WordClass
            if vtype is not None:
                vtype = _refine_verb_type(vtype, lexiklase, prefix_key)

            # Expand gloss-internal parentheticals
            gloss_variants = _expand_gloss_context(gloss)
            for g in gloss_variants:
                output.append(ParsedGloss(g, pos, vtype, qualifier, afx))

    return output


def _parseTranslation(translationText: str, englishGlosses: list[ParsedGloss],
                      lexiklase: str) -> list[ParsedGloss]:
    """Parse a non-English translation, inferring PoS from English annotations.

    Strategy:
    1. If segment has its own PoS annotation, use it.
    2. Otherwise, align positionally with English.
    3. Fewer segments: use WordClass defaults.
    4. More segments: use PoSDict for extras.
    """
    text = translationText.strip()
    if not text:
        return []

    trans_segments = text.split("; ")
    # Filter out compact/verbose duplicates from English for alignment
    # Use only unique-pos entries for alignment (skip verbose duplicates)
    eng_alignment = []
    seen_pos_indices = set()
    for g in englishGlosses:
        key = (g.pos, g.verb_type, g.affix_type)
        if key not in seen_pos_indices:
            seen_pos_indices.add(key)
            eng_alignment.append(g)

    output = []

    for i, seg in enumerate(trans_segments):
        seg = seg.strip()
        if not seg:
            continue

        # Try parsing annotation from this segment (Esperanto/Spanish annotations)
        prefix_key, gloss, qualifier = _parse_annotation_prefix(
            seg, _TRANSLATION_ANNOTATION_MAP, _SORTED_TRANSLATION_PREFIXES
        )

        if prefix_key is not None:
            entries = _TRANSLATION_ANNOTATION_MAP[prefix_key]
            for pos, vtype, afx in entries:
                output.append(ParsedGloss(gloss, pos, vtype, qualifier, afx))
        elif i < len(eng_alignment):
            # Positional alignment with English
            eng = eng_alignment[i]
            output.append(ParsedGloss(seg, eng.pos, eng.verb_type, eng.qualifier, eng.affix_type))
        else:
            # Extra segments beyond English — use PoSDict for WordClass defaults
            if lexiklase in PoSDict:
                pos_list = PoSDict[lexiklase]
                if i < len(pos_list):
                    output.append(ParsedGloss(seg, pos_list[i]))
                else:
                    output.append(ParsedGloss(seg, pos_list[-1]))
            else:
                output.append(ParsedGloss(seg, GlossPoS.PHRASE))

    # Handle fewer segments: assign default PoS based on WordClass
    if len(trans_segments) == 1 and len(eng_alignment) > 1 and not output:
        default_pos = _get_default_pos(lexiklase)
        output.append(ParsedGloss(trans_segments[0].strip(), default_pos[0], default_pos[1]))

    return output


def _get_default_pos(lexiklase: str) -> tuple[GlossPoS, Optional[VerbType]]:
    """Get default PoS for a WordClass when translation has only one segment.
    - 'b' -> NOUN (plain noun/verb defaults to noun)
    - 'b.oj', 'b.oro', etc. -> VERB with appropriate type
    - 't' -> ADJECTIVE
    """
    if lexiklase == "b":
        return (GlossPoS.NOUN, None)
    elif lexiklase == "t" or lexiklase.startswith("tabl: t"):
        return (GlossPoS.ADJECTIVE, None)
    elif lexiklase.startswith("b.") or lexiklase.startswith("f."):
        # Verbal WordClass — default to verb
        semantic = _get_verb_semantic_class(lexiklase)
        if semantic:
            return (GlossPoS.VERB, semantic)
        return (GlossPoS.VERB, VerbType.TRANSITIVE)
    elif lexiklase in PoSDict:
        pos_list = PoSDict[lexiklase]
        return (pos_list[0], None)
    return (GlossPoS.PHRASE, None)


# Primary API
LANG_CODES = ["Eng", "Spa", "Fra", "Deu", "Rus", "Zho", "Epo"]


class ParsedWordEntry(NamedTuple):
    translations: dict  # lang_code -> list[ParsedGloss]


def parseWordEntry(english: str, wordclass: str,
                   translations: dict) -> ParsedWordEntry:
    """Parse a full word list row. Returns PoS-tagged translations for all languages.

    Args:
        english: TranslationEng column value
        wordclass: WordClass column value
        translations: dict of {lang_code: translation_text} for non-English languages

    Returns:
        ParsedWordEntry with all languages PoS-tagged.
    """
    result = {}

    # Parse English (primary, with annotations)
    eng_glosses = _parseAnnotatedEnglish(english, wordclass) if english.strip() else []
    result["Eng"] = eng_glosses

    # Parse each non-English translation
    for lang, text in translations.items():
        if text and text.strip():
            result[lang] = _parseTranslation(text, eng_glosses, wordclass)
        else:
            result[lang] = []

    return ParsedWordEntry(translations=result)


# Backward-compatible API
def parseEntry(englishText: str, lexiklase: str) -> list[ParsedGloss]:
    """Parse English gloss entry. Detects new annotation format and dispatches.
    Backward-compatible: returns list of ParsedGloss (tuple-accessible).
    """
    text = englishText.strip()
    if not text:
        return []

    # Detect new format: check if first segment has a recognized annotation prefix
    first_seg = text.split("; ")[0]
    prefix_key, _, _ = _parse_annotation_prefix(first_seg)

    if prefix_key is not None:
        return _parseAnnotatedEnglish(text, lexiklase)
    else:
        return _parseLegacyEntry(text, lexiklase)


def _parseLegacyEntry(englishText: str, lexiklase: str) -> list[ParsedGloss]:
    """Legacy parser for old-format entries (tr:, intr:, etc.)."""
    englishGlosses = englishText.strip().split("; ")
    outputGlosses = []
    PoSs = lexiklase.split("; ")
    PoSlist = []
    transitivity = ""

    for part in PoSs:
        PoSKey = None
        if part == "b.oro" or part == "f.oro":
            transitivity = part.split(".")[-1]
            PoSKey = part
        elif part.startswith("b.") or part.startswith("f."):
            transitivity = part.split(".")[-1]
            PoSKey = part[0]
        else:
            PoSKey = part

        if PoSKey in PoSDict:
            if PoSKey == "b" and len(englishGlosses) == len(PoSs):
                PoSlist += [GlossPoS.NOUN]
            else:
                PoSlist += PoSDict[PoSKey]
        else:
            pass  # Unknown WordClass

    if len(englishGlosses) == 1:
        if transitivity == "oj":
            outputGlosses = [ParsedGloss(englishGlosses[0].removeprefix("tr: "), GlossPoS.VERB, VerbType.TRANSITIVE)]
        elif transitivity == "nenoj":
            outputGlosses = [ParsedGloss(englishGlosses[0].removeprefix("intr (optional -cu): "), GlossPoS.VERB, VerbType.INTRANSITIVE_CU)]
        elif transitivity == "oro":
            if "tr/intr (optional -cu):" in englishGlosses[0]:
                g = englishGlosses[0].removeprefix("tr/intr (optional -cu):")
                outputGlosses = [ParsedGloss(g, GlossPoS.VERB, VerbType.INTRANSITIVE_CU),
                                 ParsedGloss(g, GlossPoS.VERB, VerbType.TRANSITIVE)]
        elif transitivity == "lin":
            outputGlosses = [ParsedGloss(englishGlosses[0], GlossPoS.VERB, VerbType.COPULAR)]
        elif transitivity == "ru":
            outputGlosses = [ParsedGloss(englishGlosses[0], GlossPoS.VERB, VerbType.ECHO_TRANSITIVE)]
        else:
            if PoSlist:
                outputGlosses = [ParsedGloss(englishGlosses[0], PoSlist[0])]
    else:
        transitiveCounter = 0
        for i in range(len(englishGlosses)):
            if transitivity == "" and i >= len(PoSlist):
                break
            elif englishGlosses[i] != "":
                output_PoS = PoSlist[min(i, len(PoSlist) - 1)] if PoSlist else GlossPoS.PHRASE

                if PoSlist and i < len(PoSlist) and PoSlist[i] == GlossPoS.VERB:
                    if transitivity != "oro":
                        if transitivity in transDict:
                            outputGlosses.append(ParsedGloss(englishGlosses[i], GlossPoS.VERB, transDict[transitivity]))
                    else:
                        if "tr:" in englishGlosses[i] and "intr:" not in englishGlosses[i]:
                            outputGlosses.append(ParsedGloss(englishGlosses[i].removeprefix("tr: "), GlossPoS.VERB, VerbType.TRANSITIVE))
                        elif "tr/intr (optional -cu):" in englishGlosses[i]:
                            g = englishGlosses[i].removeprefix("tr/intr (optional -cu):")
                            outputGlosses.append(ParsedGloss(g, GlossPoS.VERB, VerbType.INTRANSITIVE_CU))
                            outputGlosses.append(ParsedGloss(g, GlossPoS.VERB, VerbType.TRANSITIVE))
                        elif "tr/intr:" in englishGlosses[i]:
                            g = englishGlosses[i].removeprefix("tr/intr:")
                            outputGlosses.append(ParsedGloss(g, GlossPoS.VERB, VerbType.INTRANSITIVE))
                            outputGlosses.append(ParsedGloss(g, GlossPoS.VERB, VerbType.TRANSITIVE))
                        elif "intr (optional -cu): " in englishGlosses[i]:
                            outputGlosses.append(ParsedGloss(englishGlosses[i].removeprefix("intr (optional -cu): "), GlossPoS.VERB, VerbType.INTRANSITIVE_CU))
                        elif "intr: " in englishGlosses[i]:
                            outputGlosses.append(ParsedGloss(englishGlosses[i].removeprefix("intr: "), GlossPoS.VERB, VerbType.INTRANSITIVE))
                else:
                    outputGlosses.append(ParsedGloss(englishGlosses[i], output_PoS))

    return outputGlosses


# PoSDict maps WordClass codes to expected PoS lists (used for fallback and translation alignment)
PoSDict = {
    "n": [GlossPoS.NOUN],
    "f": [GlossPoS.VERB],
    "f.sah": [GlossPoS.VERB],
    "f.oro": [GlossPoS.VERB, GlossPoS.VERB],
    "f.lin": [GlossPoS.VERB],
    "b": [GlossPoS.NOUN, GlossPoS.VERB],
    "b.oj": [GlossPoS.NOUN, GlossPoS.VERB],
    "b.oj.ru": [GlossPoS.NOUN, GlossPoS.VERB],
    "b.nenoj": [GlossPoS.NOUN, GlossPoS.VERB],
    "b.lin": [GlossPoS.NOUN, GlossPoS.VERB],
    "b.oro": [GlossPoS.NOUN, GlossPoS.VERB, GlossPoS.VERB],
    "b.oro.hisi": [GlossPoS.NOUN, GlossPoS.VERB, GlossPoS.VERB],
    "b.oro.jotay": [GlossPoS.NOUN, GlossPoS.VERB, GlossPoS.VERB],
    "b.oro.harka": [GlossPoS.NOUN, GlossPoS.VERB, GlossPoS.VERB],
    "t": [GlossPoS.ADJECTIVE, GlossPoS.VERBAL_ADVERB],
    "s": [GlossPoS.ADJECTIVE],
    "m": [GlossPoS.ADVERB],
    "p jm": [GlossPoS.PREPOSITIONAL_PHRASE],
    "n jm": [GlossPoS.NOUN_PHRASE],
    "t jm": [GlossPoS.ADJECTIVE_PHRASE],
    "m jm": [GlossPoS.PHRASAL_ADVERB],
    "s jm": [GlossPoS.ADJECTIVE_PHRASE],
    "lfik": [GlossPoS.PREFIX],
    "xfik": [GlossPoS.NOUN],  # suffix → induced PoS
    "b xfik": [GlossPoS.NOUN, GlossPoS.VERB],
    "b.oj xfik": [GlossPoS.NOUN, GlossPoS.VERB],
    "b.nenoj xfik": [GlossPoS.NOUN, GlossPoS.VERB],
    "m xfik": [GlossPoS.ADVERB],
    "t xfik": [GlossPoS.ADJECTIVE, GlossPoS.VERBAL_ADVERB],
    "su n": [GlossPoS.PROPER_NOUN],
    "su t": [GlossPoS.PROPER_ADJECTIVE],
    "su s": [GlossPoS.POSSESSIVE_ADJECTIVE],
    "su pn": [GlossPoS.POSSESSIVE_PRONOUN],
    "il": [GlossPoS.INTERJECTION],
    "l": [GlossPoS.CONJUNCTION],
    "num": [GlossPoS.NUMBER],
    "p": [GlossPoS.PREPOSITION],
    "xp": [GlossPoS.POSTPOSITION],
    "pn": [GlossPoS.PRONOUN],
    "jm p": [GlossPoS.PHRASAL_PREPOSITION],
    "jm l": [GlossPoS.PHRASAL_CONJUNCTION],
    "jm t": [GlossPoS.PHRASAL_ADVERB],
    "f jm": [GlossPoS.VERB_PHRASE],
    "l jm": [GlossPoS.CONJUNCTION_PHRASE],
    "jm": [GlossPoS.PHRASE],
    "d": [GlossPoS.DETERMINER],
    "par": [GlossPoS.PARTICLE],
    "f par": [GlossPoS.PARTICLE],
    # Compound WordClasses
    "b; il": [GlossPoS.NOUN, GlossPoS.INTERJECTION],
    "b.oj; il": [GlossPoS.NOUN, GlossPoS.VERB, GlossPoS.INTERJECTION],
    "b.oj.ru; il": [GlossPoS.NOUN, GlossPoS.VERB, GlossPoS.INTERJECTION],
    "b.nenoj; il": [GlossPoS.NOUN, GlossPoS.VERB, GlossPoS.INTERJECTION],
    "b.oro.hisi; il": [GlossPoS.NOUN, GlossPoS.VERB, GlossPoS.VERB, GlossPoS.INTERJECTION],
    "b.oj; b.nenoj.p": [GlossPoS.NOUN, GlossPoS.VERB, GlossPoS.VERB],
    "b.oj.ru; b.nenoj.p": [GlossPoS.NOUN, GlossPoS.VERB, GlossPoS.VERB],
    "t; f.sah": [GlossPoS.ADJECTIVE, GlossPoS.VERBAL_ADVERB, GlossPoS.VERB],
    "t; il": [GlossPoS.ADJECTIVE, GlossPoS.VERBAL_ADVERB, GlossPoS.INTERJECTION],
    "d; m": [GlossPoS.DETERMINER, GlossPoS.ADVERB],
    "num; d": [GlossPoS.NUMBER, GlossPoS.DETERMINER],
    "p; lfik": [GlossPoS.PREPOSITION, GlossPoS.PREFIX],
    # Table words (correlatives)
    "tabl: pn": [GlossPoS.PRONOUN],
    "tabl: m": [GlossPoS.ADVERB],
    "tabl: d": [GlossPoS.DETERMINER],
    "tabl: t": [GlossPoS.ADJECTIVE, GlossPoS.VERBAL_ADVERB],
    "tabl: l": [GlossPoS.CONJUNCTION],
    "tabl: su s": [GlossPoS.POSSESSIVE_ADJECTIVE],
    "tabl: d; m": [GlossPoS.DETERMINER, GlossPoS.ADVERB],
    "tabl: m; l": [GlossPoS.ADVERB, GlossPoS.CONJUNCTION],
    "tabl: num; d": [GlossPoS.NUMBER, GlossPoS.DETERMINER],
    # Bound roots
    "nenhuru genu": [GlossPoS.PREFIX],
}
