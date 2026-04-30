import sys
import re
import pandas as pd
import wget
import os

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
    return None

# ── Multi-word matching ─────────────────────────────────────────────────────

MULTI_WORD_PARTS = {"kom", "fe", "xafe", "lefe", "leya", "xaya", "na", "hu",
                    "mara", "watu", "din", "noce", "leki", "xaki", "de"}

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
                        if tri in df.index:
                            surface = " ".join(raw_words[i:i+3])
                            tokens.append((surface, tri, trail3))
                            i += 3
                            matched_multi = True
                # 2-word
                if not matched_multi:
                    bi = lem + " " + lem2
                    if bi in df.index:
                        surface = raw_words[i] + " " + raw_words[i+1]
                        tokens.append((surface, bi, trail2))
                        i += 2
                        matched_multi = True
                    elif lem2 in MULTI_WORD_PARTS:
                        fe_bi = "(fe) " + lem + " " + lem2
                        if fe_bi in df.index:
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
    # Only commas and semicolons split clauses mid-sentence.
    # Sentence-ending punctuation (. ! ?) does not block resolution of
    # the word it's attached to — it marks sentence end, not clause split.
    # The infinitive particle "na" also starts a new phrase for SVO.
    def is_clause_boundary(j):
        if j < 0 or j >= n:
            return True
        if pos[j] == "CONJ":
            return True
        if pos[j] == "PAR" and lemmas[j] == "na":
            return True
        # Check if the PREVIOUS position has a comma/semicolon trailing
        if j > 0:
            _, _, prev_trail = tokens[j - 1]
            if prev_trail and any(c in prev_trail for c in ",;"):
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
            # Hit something else (resolved noun/verb/prep/etc.) — stop
            break

    # ── Stage 3, Step 2: SVO for remaining unresolved b ──
    # Per clause: 1st unresolved b → N, 2nd → V, 3rd+ → N.

    clause_start = 0
    while clause_start < n:
        # Find end of clause
        clause_end = clause_start
        while clause_end < n:
            if clause_end > clause_start and is_clause_boundary(clause_end):
                break
            clause_end += 1

        # Collect unresolved b positions in this clause
        b_positions = [j for j in range(clause_start, clause_end)
                       if ambig[j] == "b"]

        # Check if there's already a resolved noun/pronoun or verb in clause.
        # Exclude PP-internal nouns from has_nom (they're not subjects).
        has_nom = any(pos[j] in ("N", "PRON", "POSS")
                      and j not in prep_resolved
                      for j in range(clause_start, clause_end))
        has_verb = any(pos[j] == "V"
                       for j in range(clause_start, clause_end))

        if b_positions:
            if has_verb:
                # Verb already exists — all remaining b → noun
                for j in b_positions:
                    pos[j] = "N"
                    ambig[j] = None
            elif has_nom:
                # Noun/pronoun exists but no verb — first b → verb, rest → noun
                pos[b_positions[0]] = "V"
                ambig[b_positions[0]] = None
                for j in b_positions[1:]:
                    pos[j] = "N"
                    ambig[j] = None
            else:
                # Nothing resolved — N, V, N, N, ...
                if len(b_positions) == 1:
                    pos[b_positions[0]] = "V"
                    ambig[b_positions[0]] = None
                else:
                    pos[b_positions[0]] = "N"
                    ambig[b_positions[0]] = None
                    pos[b_positions[1]] = "V"
                    ambig[b_positions[1]] = None
                    for j in b_positions[2:]:
                        pos[j] = "N"
                        ambig[j] = None

        # Advance to next clause.
        # If boundary was a CONJ or PAR (na), skip it.
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

# ── Main ────────────────────────────────────────────────────────────────────

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

if sys.stdin.isatty():
    sentences = TEST_SENTENCES
else:
    sentences = [line.strip() for line in sys.stdin if line.strip()]

for sentence in sentences:
    tokens = tokenize(sentence)
    pos_list = assign_pos(tokens)
    print(format_output(tokens, pos_list))
