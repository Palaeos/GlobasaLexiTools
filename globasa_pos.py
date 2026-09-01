"""Globasa POS tagger library.

Lifted from PosTagger.py: data loading, lemmatizer, tokenizer, POS assignment.
PosTagger.py is now a thin CLI shim that imports from this module, so that the
tagger can be reused by Flask views (Word Viewer.py /pos) and other consumers
without the script's stdin-reading side effect.

Public API:
    tokenize(sentence)        -> [(surface, lemma_or_None, trailing_punct), ...]
    assign_pos(tokens)        -> [pos_label, ...]                (parallel to tokens)
    format_output(tokens, ps) -> "word/POS word/POS..."
    lemmatize(word)           -> dict-form lemma or None
    POS_LABELS                -> GlossPoS -> short tag dict
    POS_NAMES                 -> short tag -> human name dict
    TEST_SENTENCES            -> the 21 Xwexi test cases
    df, T_CLASS, B_CLASS, ... -> word-list dataframe + WordClass sets
"""

import re
import os
import pandas as pd
import wget

from Lexilista_parser import GlossPoS

# ── Download word list ──────────────────────────────────────────────────────

menalari_name = "word-list.csv"
if not os.path.exists(menalari_name):
    wget.download("https://cdn.globasa.net/api2/word-list.csv", menalari_name)

df = pd.read_csv(menalari_name, index_col="Word")
df.index = df.index.str.strip()

# ── Build word sets from WordClass column ───────────────────────────────────

TENSE_PARTICLES = {"le", "xa", "nun", "am", "na", "ger", "jale", "jaxa", "u"}

def _wc_set(*patterns):
    """Collect index values whose WordClass matches any of the given patterns."""
    mask = pd.Series(False, index=df.index)
    for p in patterns:
        mask |= df["WordClass"].str.strip().eq(p)
    return set(df.index[mask])

def _wc_startswith(*prefixes):
    mask = pd.Series(False, index=df.index)
    for p in prefixes:
        mask |= df["WordClass"].str.strip().str.startswith(p)
    return set(df.index[mask])

PREPOSITIONS = _wc_set("p", "jm p")
DETERMINERS = _wc_set("d", "tabl: d")
POSSESSIVES = _wc_set("su s", "tabl: su s", "su pn")
PRONOUNS = _wc_set("pn", "tabl: pn")
NUMBERS = _wc_startswith("num")
CONJUNCTIONS = (_wc_set("l", "jm l", "l jm")
                | _wc_startswith("tabl: l", "tabl: m; l"))

# Coordinating conjunctions connect parallel constituents at the same syntactic
# level (X ji Y both nouns, or both verbs). They are TRANSPARENT to SVO clause
# boundaries — a `b` after `ji` should inherit the role of the conjunct on the
# other side rather than start a fresh SVO frame. Subordinating conjunctions
# (ki, hu, ku, kwas, eger, kom, harki, folki, anything containing `ki`, etc.)
# stay opaque: they introduce a new clause and reset SVO.
COORD_CONJ_LEMMAS = {
    "ji",                # and
    "or", "nor",         # or, nor
    "mas",               # but
    "iji",               # both ... and ...
    "kam",               # whether (yes/no question)
    "ji pia",            # and also, as well as
    "ji max ete", "ji max oto", "ji max te", "ji max to",  # etc.
    "mas fe hataya",     # but nevertheless
    "mas fe tayti",      # but rather/instead
    "mas sol eger",      # provided that
}
PARTICLES = _wc_set("par", "f par")
ADVERBS = _wc_set("m") | _wc_startswith("tabl: m")
ADJ_ONLY = _wc_set("s", "s jm", "tabl: t")  # non-ambiguous adjectives
PURE_VERBS = _wc_startswith("f")  # f, f.sah, f.lin, f.oro (no noun reading)
INTERJECTIONS = _wc_set("il")

# Ambiguous classes
B_CLASS = _wc_startswith("b")  # noun/verb
T_CLASS = _wc_set("t") | _wc_set("t; il", "t; f.sah")  # adj/adv
DM_CLASS = _wc_set("d; m", "tabl: d; m", "tabl: num; d", "num; d")  # det/adv

# Special words
COPULAS = {"sen"}  # b.lin — always verb
ALWAYS_VERB = {"hay"}  # b.nenoj — always verb

# ── POS labels ──────────────────────────────────────────────────────────────

POS_LABELS = {
    GlossPoS.NOUN: "N", GlossPoS.VERB: "V",
    GlossPoS.ADJECTIVE: "ADJ", GlossPoS.VERBAL_ADVERB: "ADV",
    GlossPoS.ADVERB: "ADV", GlossPoS.PRONOUN: "PRON",
    GlossPoS.PREPOSITION: "PREP", GlossPoS.DETERMINER: "DET",
    GlossPoS.PARTICLE: "PAR", GlossPoS.CONJUNCTION: "CONJ",
    GlossPoS.NUMBER: "NUM", GlossPoS.INTERJECTION: "INTJ",
    GlossPoS.POSSESSIVE_ADJECTIVE: "POSS",
    GlossPoS.POSSESSIVE_PRONOUN: "POSS",
    GlossPoS.PROPER_NOUN: "PROPN",
    GlossPoS.PROPER_ADJECTIVE: "PROPN",
    GlossPoS.PHRASAL_PREPOSITION: "PREP",
    GlossPoS.PREPOSITIONAL_PHRASE: "PREP",
    GlossPoS.NOUN_PHRASE: "N", GlossPoS.VERB_PHRASE: "V",
    GlossPoS.ADJECTIVE_PHRASE: "ADJ",
    GlossPoS.PHRASAL_ADVERB: "ADV",
    GlossPoS.CONJUNCTION_PHRASE: "CONJ",
    GlossPoS.PHRASAL_CONJUNCTION: "CONJ",
    GlossPoS.PHRASE: "PHRS", GlossPoS.PREFIX: "PFX",
    GlossPoS.POSTPOSITION: "POSTP",
}

# Short tag -> human-readable name (used by the /pos viewer legend tooltips).
POS_NAMES = {
    "N":     "Noun",
    "V":     "Verb",
    "ADJ":   "Adjective",
    "ADV":   "Adverb",
    "PRON":  "Pronoun",
    "PROPN": "Proper noun",
    "PREP":  "Preposition",
    "POSTP": "Postposition",
    "DET":   "Determiner",
    "POSS":  "Possessive",
    "NUM":   "Number",
    "PAR":   "Particle",
    "CONJ":  "Conjunction",
    "INTJ":  "Interjection",
    "PHRS":  "Phrase",
    "PFX":   "Prefix",
    "SFX":   "Suffix",
    "UNK":   "Unknown",
}

# ── Lemmatizer ──────────────────────────────────────────────────────────────

PUNCT_RE = re.compile(r'^([^\w]*)(.+?)([^\w]*)$')

def strip_punct(token):
    """Split token into (leading_punct, core, trailing_punct)."""
    m = PUNCT_RE.match(token)
    if m:
        return m.group(1), m.group(2), m.group(3)
    return "", token, ""

def lemmatize(word):
    """Find dictionary lemma for a Globasa word. Returns lemma or None."""
    c = word.lower().strip()
    if not c:
        return None
    if c in df.index:
        return c
    # Try original case (proper nouns are capitalized in the index)
    original = word.strip()
    if original in df.index:
        return original
    # Try title case
    titled = original[0].upper() + original[1:] if len(original) > 1 else original.upper()
    if titled in df.index:
        return titled
    # Prefix stripping
    for pfx in ("be", "du"):
        stripped = c.removeprefix(pfx)
        if stripped != c and stripped in df.index:
            return stripped
    # Suffix stripping (single)
    for sfx in ("li", "ya", "ne", "do"):
        stripped = c.removesuffix(sfx)
        if stripped != c and stripped in df.index:
            return stripped
    # Check again after prefix+suffix
    if c in df.index:
        return c
    # Longer suffixes
    for sfx in ("lari", "cu", "gi", "mo"):
        stripped = c.removesuffix(sfx)
        if stripped != c and stripped in df.index:
            return stripped
    # Prefix + suffix combos
    for pfx in ("be", "du"):
        stem = c.removeprefix(pfx)
        if stem == c:
            continue
        for sfx in ("li", "ya", "ne", "do", "lari", "cu", "gi", "mo"):
            stripped = stem.removesuffix(sfx)
            if stripped != stem and stripped in df.index:
                return stripped
        if stem in df.index:
            return stem
    # Hyphenated-compound fallback: in Globasa the rightmost component is
    # the head, so an unknown compound like "Globasa-leksika" inherits its
    # PoS from the last segment ("leksika"). Recurse on that segment so
    # affix-stripping etc. still applies to it.
    if "-" in word and not word.startswith("-"):
        last = word.rsplit("-", 1)[1]
        if last and last != word:
            inner = lemmatize(last)
            if inner is not None:
                return inner
    return None

# ── Multi-word matching ─────────────────────────────────────────────────────

MULTI_WORD_PARTS = {"kom", "fe", "xafe", "lefe", "leya", "xaya", "na", "hu",
                    "mara", "watu", "din", "noce", "leki", "xaki", "de"}

def _multi_word_collapsible(lemma):
    """A multi-word lexicon entry is safe to collapse only if its WordClass
    carries a usable PoS tag. Pure-phrasal entries (`WordClass == "jm"`)
    like `cel na`, `imi am`, `sen anti` mix categories that don't map to a
    single tag — collapsing them produces an UNK token and blocks the
    constituents' own resolution (e.g. `na` losing its verb-signal effect).
    Keep those split so the per-word tagger handles them."""
    if lemma in df.index:
        wc = str(df.loc[lemma, "WordClass"]).strip()
        if wc == "jm":
            return False
    return True

def tokenize(sentence):
    """Tokenize sentence into list of (surface, lemma, trailing_punct) tuples."""
    raw_words = sentence.split()
    tokens = []
    i = 0
    while i < len(raw_words):
        lead, core, trail = strip_punct(raw_words[i])
        lem = lemmatize(core)

        # Try multi-word matching (conservative: only when second word is a
        # known multi-word part, or first word is "fe"/"cel"/"he"/"no").
        matched_multi = False
        if lem and i + 1 < len(raw_words):
            _, core2, trail2 = strip_punct(raw_words[i + 1])
            lem2 = lemmatize(core2)
            if lem2 and (lem in ("fe", "cel", "he", "no")
                         or lem2 in MULTI_WORD_PARTS):
                # 3-word (only for "fe X Y" patterns)
                if lem == "fe" and i + 2 < len(raw_words):
                    _, core3, trail3 = strip_punct(raw_words[i + 2])
                    lem3 = lemmatize(core3)
                    if lem3:
                        tri = lem + " " + lem2 + " " + lem3
                        if tri in df.index and _multi_word_collapsible(tri):
                            surface = " ".join(raw_words[i:i+3])
                            tokens.append((surface, tri, trail3))
                            i += 3
                            matched_multi = True
                # 2-word
                if not matched_multi:
                    bi = lem + " " + lem2
                    if bi in df.index and _multi_word_collapsible(bi):
                        surface = raw_words[i] + " " + raw_words[i+1]
                        tokens.append((surface, bi, trail2))
                        i += 2
                        matched_multi = True
                    elif lem2 in MULTI_WORD_PARTS:
                        fe_bi = "(fe) " + lem + " " + lem2
                        if fe_bi in df.index and _multi_word_collapsible(fe_bi):
                            surface = raw_words[i] + " " + raw_words[i+1]
                            tokens.append((surface, fe_bi, trail2))
                            i += 2
                            matched_multi = True

        if not matched_multi:
            tokens.append((lead + core + trail if not lem else raw_words[i],
                           lem, trail))
            i += 1

    return tokens

# ── POS assignment ──────────────────────────────────────────────────────────

CLAUSE_BOUNDARIES = CONJUNCTIONS | {",", ";", ":", ".", "!", "?", "…", "..."}

def assign_pos(tokens):
    """Assign POS to each token. Returns list of (surface, pos_label, trail)."""

    n = len(tokens)
    pos = [None] * n        # resolved POS string
    lemmas = [t[1] for t in tokens]
    ambig = [None] * n      # 'b', 't', 'dm', or None

    # ── Stage 2: Unambiguous POS assignment ──
    for i, (surface, lem, trail) in enumerate(tokens):
        if lem is None:
            # Unknown word: tag capitalized non-sentence-initial words as PROPN
            _, core, _ = strip_punct(surface)
            if i > 0 and core and core[0].isupper():
                pos[i] = "PROPN"
            else:
                pos[i] = "UNK"
            continue
        # Check WordClass for proper nouns before anything else
        if lem in df.index:
            wc = str(df.loc[lem, "WordClass"]).strip()
            if wc.startswith("su n") or wc.startswith("su t"):
                pos[i] = "PROPN"
                continue
        if lem in ALWAYS_VERB or lem in COPULAS:
            pos[i] = "V"
            continue
        if lem in PRONOUNS:
            pos[i] = "PRON"
        elif lem in PREPOSITIONS:
            pos[i] = "PREP"
        elif lem in TENSE_PARTICLES:
            pos[i] = "PAR"
        elif lem in PARTICLES:
            pos[i] = "PAR"
        elif lem in CONJUNCTIONS:
            pos[i] = "CONJ"
        elif lem in NUMBERS and lem not in DM_CLASS:
            pos[i] = "NUM"
        elif lem in ADVERBS and lem not in T_CLASS and lem not in DM_CLASS:
            pos[i] = "ADV"
        elif lem in ADJ_ONLY:
            pos[i] = "ADJ"
        elif lem in INTERJECTIONS and lem not in B_CLASS:
            pos[i] = "INTJ"
        elif lem in PURE_VERBS:
            pos[i] = "V"
        elif lem in POSSESSIVES:
            pos[i] = "POSS"
        elif lem in DETERMINERS and lem not in DM_CLASS:
            pos[i] = "DET"
        elif lem in B_CLASS:
            ambig[i] = "b"
        elif lem in T_CLASS:
            # -mo suffix forces ADV (adverb-modifying adverb, e.g. perfetomo)
            _, core_word, _ = strip_punct(surface)
            if core_word.lower().endswith("mo") and not core_word.lower() == lem:
                pos[i] = "ADV"
            else:
                ambig[i] = "t"
        elif lem in DM_CLASS:
            ambig[i] = "dm"
        else:
            # Fallback: try WordClass lookup
            if lem in df.index:
                wc = str(df.loc[lem, "WordClass"]).strip()
                if "lfik" in wc:
                    pos[i] = "PFX"
                elif "xfik" in wc:
                    pos[i] = "SFX"
                else:
                    pos[i] = "UNK"
            else:
                pos[i] = "UNK"

    # ── Helper: is a position a clause boundary? ──
    # Sentence-ending punctuation (. ! ?) does not block resolution of
    # the word it's attached to — it marks sentence end, not clause split.
    # The infinitive particle "na" also starts a new phrase for SVO.
    # Subordinating conjunctions (ki, hu, eger, ...) split clauses;
    # coordinating conjunctions (ji, mas, or, ...) are transparent and let
    # SVO see a wider span so that parallel `b`-words on either side
    # propagate their POS instead of mis-resolving as lone-b → V.
    def is_coord_conj(j):
        return 0 <= j < n and pos[j] == "CONJ" and lemmas[j] in COORD_CONJ_LEMMAS

    # Pre-pass: identify "list commas" — commas (and semicolons) that act as
    # ellipsis of a coordinating conjunction in a list like `A, B, C, ji D`.
    # A comma at position k qualifies only when ALL of:
    #   (1) Both sides of the comma look like NP coord-items: the left side
    #       walks back through modifiers to an NP head (b-class / N / PRON /
    #       PROPN / POSS); the right side walks forward to an NP head OR is
    #       itself a coord CONJ.
    #   (2) A coord CONJ is reachable forward without crossing a hard
    #       boundary (subord CONJ, `na`, or sentence-ending punctuation).
    # This excludes sentence-initial topical commas like `Xali, oto ...`
    # where the left side is a bare t-class adverbial with no NP head.
    def _is_np_head(j):
        if 0 <= j < n:
            if ambig[j] == "b":
                return True
            if pos[j] in ("N", "PRON", "PROPN", "POSS"):
                return True
        return False

    def _is_np_modifier(j):
        if 0 <= j < n:
            if ambig[j] in ("t", "dm"):
                return True
            if pos[j] in ("ADJ", "ADV", "DET", "POSS", "NUM"):
                return True
        return False

    def _ends_coord_item(k):
        j = k
        while j >= 0 and not _is_np_head(j):
            if _is_np_modifier(j):
                j -= 1
                continue
            return False
        return j >= 0

    def _starts_coord_item(p):
        if p >= n:
            return False
        if is_coord_conj(p):
            return True
        j = p
        while j < n and not _is_np_head(j):
            if _is_np_modifier(j):
                j += 1
                continue
            return False
        return j < n

    def _check_list_comma(k):
        _, _, trail_k = tokens[k]
        if not trail_k or not any(c in trail_k for c in ",;"):
            return False
        if not _ends_coord_item(k):
            return False
        if not _starts_coord_item(k + 1):
            return False
        j = k + 1
        while j < n:
            if is_coord_conj(j):
                return True
            if pos[j] == "CONJ":
                return False
            if pos[j] == "PAR" and lemmas[j] == "na":
                return False
            _, _, t = tokens[j]
            if t and any(c in t for c in ".!?…"):
                return False
            j += 1
        return False

    list_comma_positions = {k for k in range(n) if _check_list_comma(k)}

    def is_clause_boundary(j):
        if j < 0 or j >= n:
            return True
        if pos[j] == "CONJ" and not is_coord_conj(j):
            return True
        if pos[j] == "PAR" and lemmas[j] == "na":
            return True
        # Check if the PREVIOUS position has a comma/semicolon trailing.
        # List commas (within a coord span) act as elided coord CONJs and
        # are handled by the segment splitter instead of bounding the clause.
        if j > 0:
            _, _, prev_trail = tokens[j - 1]
            if prev_trail and any(c in prev_trail for c in ",;"):
                if (j - 1) not in list_comma_positions:
                    return True
        return False

    # ── Stage 3, Step 1: Resolve b via preposition/particle/det/poss/num ──
    # Scan left-to-right. When we find a resolver (prep/particle/det/poss/num),
    # project forward through t/dm words to the next b.
    # Track which nouns were resolved by prepositions (PP-internal) so SVO
    # doesn't count them as subjects.
    prep_resolved = set()

    for i in range(n):
        if pos[i] not in ("PREP", "PAR", "DET", "POSS", "NUM"):
            continue

        is_noun_signal = pos[i] in ("PREP", "DET", "POSS", "NUM")
        is_verb_signal = pos[i] == "PAR" and lemmas[i] in TENSE_PARTICLES
        is_prep = pos[i] == "PREP"

        if not is_noun_signal and not is_verb_signal:
            continue

        # Project forward through t, dm, and (for verb signals) adverbs
        j = i + 1
        while j < n:
            if is_clause_boundary(j):
                break
            if ambig[j] == "t":
                if is_noun_signal:
                    pos[j] = "ADJ"
                    ambig[j] = None
                elif is_verb_signal:
                    pos[j] = "ADV"
                    ambig[j] = None
                j += 1
                continue
            if ambig[j] == "dm":
                if is_noun_signal:
                    pos[j] = "DET"
                    ambig[j] = None
                elif is_verb_signal:
                    pos[j] = "ADV"
                    ambig[j] = None
                j += 1
                continue
            if pos[j] == "ADV":
                # Pure adverbs (no, si, daymo, etc.) are transparent
                j += 1
                continue
            if ambig[j] == "b":
                if is_noun_signal:
                    pos[j] = "N"
                    if is_prep:
                        prep_resolved.add(j)
                elif is_verb_signal:
                    pos[j] = "V"
                ambig[j] = None
                break
            # An already-resolved PROPN / PRON / N right after a PREP
            # (possibly after transparent t/dm/ADV) is that PREP's object —
            # mark PP-internal so SVO doesn't mistake it for a subject.
            # Extend the marking through immediately-following PROPN tokens
            # to cover appositional / multi-token names like
            # `yon ChatGPT-4o (OpenAI)` or `yon Claude Opus (Anthropic)` —
            # the parenthesised tag is still part of the PP, not a subject.
            if is_prep and pos[j] in ("PROPN", "PRON", "N"):
                prep_resolved.add(j)
                k = j + 1
                while k < n and pos[k] == "PROPN":
                    prep_resolved.add(k)
                    k += 1
            break

    # ── Stage 3, Step 2: SVO for remaining unresolved b ──
    # Per clause: 1st unresolved b → N, 2nd → V, 3rd+ → N. Coordinating
    # conjunctions (ji, mas, or, ...) are transparent to the clause walk
    # (handled by is_clause_boundary), so an extended clause may span
    # `X ji Y ji Z`. Within an extended clause we split into segments
    # separated by coord CONJ and propagate POS across each `ji`: the first
    # unresolved `b` of segment k+1 is forced to match the rightmost
    # nominal/verbal anchor of segment k. This prevents the lone-b → V
    # fallback from turning coordinated nouns like `kitabu ji muziki` into
    # `N CONJ V`, and lets `Patre mwa ji care matre` resolve as N V (CONJ) V N.

    def _anchor_pos(start, end, default):
        """Rightmost nominal/verbal POS in [start, end), else `default`."""
        for j in range(end - 1, start - 1, -1):
            if pos[j] in ("N", "PRON", "PROPN", "POSS"):
                return "N"
            if pos[j] == "V":
                return "V"
        return default

    def _apply_svo(b_positions, has_nom, has_verb):
        """Run the N / V / N+ fallback on b_positions. Returns updated
        (has_nom, has_verb) so callers can chain segments without
        recomputing across the whole extended clause."""
        if not b_positions:
            return has_nom, has_verb
        if has_verb:
            for j in b_positions:
                pos[j] = "N"
                ambig[j] = None
            return True, True
        if has_nom:
            pos[b_positions[0]] = "V"
            ambig[b_positions[0]] = None
            for j in b_positions[1:]:
                pos[j] = "N"
                ambig[j] = None
            return True, True
        if len(b_positions) == 1:
            pos[b_positions[0]] = "V"
            ambig[b_positions[0]] = None
            return has_nom, True
        pos[b_positions[0]] = "N"
        ambig[b_positions[0]] = None
        pos[b_positions[1]] = "V"
        ambig[b_positions[1]] = None
        for j in b_positions[2:]:
            pos[j] = "N"
            ambig[j] = None
        return True, True

    clause_start = 0
    while clause_start < n:
        # Find end of extended clause (coord CONJ is NOT a boundary).
        clause_end = clause_start
        while clause_end < n:
            if clause_end > clause_start and is_clause_boundary(clause_end):
                break
            clause_end += 1

        # Global has_verb across the extended clause: a verb anywhere
        # (e.g. copula `sen` past a `ji`) tells coord-continuation segments
        # that any lone-b they contain should resolve to N rather than V.
        has_verb_global = any(pos[j] == "V"
                              for j in range(clause_start, clause_end))

        # Identify coord CONJ split points + list-comma split points (a
        # list comma between k and k+1 splits segments without consuming a
        # token). Each split is recorded as ('conj', j)  -- ji at index j,
        # which is dropped from segments -- or ('comma', j) -- elided ji
        # immediately before index j, so j starts the next segment.
        splits = []
        for j in range(clause_start, clause_end):
            if is_coord_conj(j):
                splits.append(("conj", j))
            elif j > clause_start and not is_coord_conj(j - 1):
                # Avoid double-counting when a comma directly precedes ji.
                if (j - 1) in list_comma_positions:
                    splits.append(("comma", j))

        if not splits:
            b_positions = [j for j in range(clause_start, clause_end)
                           if ambig[j] == "b"]
            has_nom = any(pos[j] in ("N", "PRON", "POSS")
                          and j not in prep_resolved
                          for j in range(clause_start, clause_end))
            _apply_svo(b_positions, has_nom, has_verb_global)
        else:
            # Build segment bounds [s, e) from the split points.
            segments = []
            s = clause_start
            for kind, j in splits:
                if kind == "conj":
                    segments.append((s, j))
                    s = j + 1
                else:  # comma: elided CONJ between j-1 and j
                    segments.append((s, j))
                    s = j
            segments.append((s, clause_end))

            anchor = None  # 'N' or 'V', from the previous segment
            for s, e in segments:
                b_positions = [j for j in range(s, e) if ambig[j] == "b"]
                # A segment with its own PRON/PROPN/POSS is an independent
                # clause-fragment (e.g. `... ji Yu dawa filme`): it should
                # NOT inherit the previous segment's verb signal or anchor.
                # Otherwise it's a coordinate continuation and we propagate.
                has_local_subj = any(pos[j] in ("PRON", "PROPN", "POSS")
                                     and j not in prep_resolved
                                     for j in range(s, e))
                if has_local_subj:
                    seg_has_verb = any(pos[j] == "V" for j in range(s, e))
                    seg_has_nom = True
                else:
                    seg_has_verb = has_verb_global
                    seg_has_nom = any(pos[j] == "N"
                                      and j not in prep_resolved
                                      for j in range(s, e))
                    if anchor and b_positions:
                        pos[b_positions[0]] = anchor
                        ambig[b_positions[0]] = None
                        if anchor == "N":
                            seg_has_nom = True
                        else:
                            seg_has_verb = True
                        b_positions = b_positions[1:]
                _, post_verb = _apply_svo(b_positions, seg_has_nom, seg_has_verb)
                # Once a verb has been resolved anywhere, every later coord
                # continuation should treat the clause as having a verb.
                if post_verb:
                    has_verb_global = True
                anchor = _anchor_pos(s, e, anchor)

        # Advance to next clause.
        # If boundary was a (subordinating) CONJ or PAR (na), skip it.
        # If boundary was a comma (prev token trail), include this position.
        if clause_end < n and (pos[clause_end] == "CONJ"
                               or (pos[clause_end] == "PAR"
                                   and lemmas[clause_end] == "na")):
            clause_start = clause_end + 1
        else:
            clause_start = clause_end

    # ── Stage 3, Step 3: Resolve remaining t and dm ──
    for i in range(n):
        if ambig[i] not in ("t", "dm"):
            continue

        # Look right for next connected b (not interrupted by prep/particle/clause)
        found_pos = None
        for j in range(i + 1, n):
            if is_clause_boundary(j):
                break
            if pos[j] == "PREP" or (pos[j] == "PAR" and lemmas[j] in TENSE_PARTICLES):
                break
            if pos[j] in ("N", "PRON"):
                found_pos = "N"
                break
            if pos[j] == "V":
                found_pos = "V"
                break

        if found_pos == "N":
            pos[i] = "ADJ" if ambig[i] == "t" else "DET"
        elif found_pos == "V":
            pos[i] = "ADV"
        else:
            # No connected b — check if after copula
            after_copula = False
            for j in range(i - 1, -1, -1):
                if is_clause_boundary(j):
                    break
                if pos[j] == "V" and lemmas[j] in COPULAS:
                    after_copula = True
                    break
                if pos[j] in ("N", "V"):
                    break
            pos[i] = "ADJ" if after_copula else "ADV"

        ambig[i] = None

    # ── Finalize any remaining ──
    for i in range(n):
        if pos[i] is None:
            if ambig[i] == "b":
                pos[i] = "N"
            elif ambig[i] == "t":
                pos[i] = "ADJ"
            elif ambig[i] == "dm":
                pos[i] = "DET"
            else:
                pos[i] = "UNK"

    return pos

# ── Output formatting ──────────────────────────────────────────────────────

def format_output(tokens, pos_list):
    """Format tokens with POS annotations inline."""
    parts = []
    for (surface, lem, trail), p in zip(tokens, pos_list):
        # Separate trailing punctuation from the surface
        if trail and surface.endswith(trail):
            word = surface[:-len(trail)]
            parts.append(f"{word}/{p}{trail}")
        else:
            parts.append(f"{surface}/{p}")
    return " ".join(parts)

# ── Test sentences (used by the PosTagger.py CLI) ──────────────────────────

TEST_SENTENCES = [
    # SVO (Sentence Structure §SVO)
    "Patre mwa matre.",
    # Direct object marker (Sentence Structure §Direct Object Marker)
    "Patre el matre mwa.",
    # Copula (Sentence Structure §Copula)
    "Nini sen misu bete.",
    "Uma sen perfetomo syahe.",
    "Myaw sen in sanduku.",
    # Infinitive (Sentence Structure §Infinitive)
    "Mi suki na lala.",
    "Cele sen na triunfa.",
    # Prepositional phrases (Sentence Structure §Prepositional Phrases)
    "Myaw in sanduku somno.",
    "In sanduku, myaw yam maux.",
    # hay (Sentence Structure §hay)
    "Hay multi kitabu in kitabudom.",
    "Multi kitabu hay in kitabudom.",
    # Conjunction ki (Sentence Structure §ki)
    "Mi jixi ki yu le xuli mobil.",
    # Questions (Sentence Structure §Questions)
    "Kam yu yam mahimaso?",
    # Noun phrase (Phrase Structure §Noun Phrases)
    "Day manyen ergo velosi.",
    # Verb phrase (Phrase Structure §Verb Phrases)
    "Le velosi yam pingo.",
    "Femyen danse meli.",
    "Velosi, bwaw glu sui.",
    # Tense + preposition + adj + noun
    "In day baytu, myaw somno.",
    "Mi le yam pingo.",
    "Mi ger yam pingo.",
    # Complex noun phrase (Phrase Structure §Noun Phrases)
    "Hin misu care daymo lama kitabu.",
]
