"""Globasa POS tagger CLI.

The actual tagger lives in globasa_pos.py — this file is a CLI shim that
re-exports the public symbols so existing importers
(`from PosTagger import tokenize, assign_pos, df, T_CLASS, lemmatize`) keep
working, then runs the test/stdin loop when executed directly.

Usage:
    python PosTagger.py                    # runs TEST_SENTENCES
    echo "Mi suki na lala." | python PosTagger.py
"""

import sys

from globasa_pos import (
    tokenize,
    assign_pos,
    format_output,
    lemmatize,
    strip_punct,
    df,
    POS_LABELS,
    POS_NAMES,
    TENSE_PARTICLES,
    PREPOSITIONS,
    DETERMINERS,
    POSSESSIVES,
    PRONOUNS,
    NUMBERS,
    CONJUNCTIONS,
    PARTICLES,
    ADVERBS,
    ADJ_ONLY,
    PURE_VERBS,
    INTERJECTIONS,
    B_CLASS,
    T_CLASS,
    DM_CLASS,
    COPULAS,
    ALWAYS_VERB,
    MULTI_WORD_PARTS,
    CLAUSE_BOUNDARIES,
    TEST_SENTENCES,
)

if sys.stdin.isatty():
    sentences = TEST_SENTENCES
else:
    sentences = [line.strip() for line in sys.stdin if line.strip()]

for sentence in sentences:
    tokens = tokenize(sentence)
    pos_list = assign_pos(tokens)
    print(format_output(tokens, pos_list))
