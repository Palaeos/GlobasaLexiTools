"""
POS-suffix compatibility matrix and stacking limits from Xwexi grammar §02 inharelexi
and §10 lexikostrui.

These constraints are consulted ONLY on the greedy fallback path (words not in lexicon)
and ONLY when with_pos=True. The default fast path (with_pos=False) skips them.

Suffix → required base POS class. Empty set means "any base POS is accepted."
"""

from __future__ import annotations

# Suffix (bare, without leading '-') → set of acceptable base POS tags
# POS tags as used by PosTagger: 'N', 'V', 'ADJ', 'ADV', 'NUM', etc.
SUFFIX_BASE_POS: dict[str, set[str]] = {
    # b-class suffixes (→ noun or noun-changing)
    "bol":   {"N"},
    "din":   {"N"},
    "dom":   {"N"},
    "fon":   {"N"},
    "gon":   {"N"},
    "ismo":  {"N"},
    "ista":  {"N"},
    "je":    {"N", "ADJ"},
    "kef":   {"N"},
    "mon":   {"N"},
    "pel":   {"N", "V"},
    "sa":    {"N"},
    "tim":   {"N"},
    "tul":   {"N"},
    "xey":   {"N", "ADJ", "V"},
    "ya":    {"ADJ", "N"},
    "yen":   {"N", "V"},
    "cu":    {"ADJ", "N", "V"},   # intransitive marker
    "gi":    {"ADJ", "N", "V"},   # causative/transitive marker
    # t-class suffixes (→ adjective/adverb)
    "mo":    {"ADJ", "ADV"},
    "bon":   {"N", "V", "ADJ"},
    "bur":   {"N", "V", "ADJ"},
    "day":   {"N"},
    "do":    {"V", "N"},
    "fil":   {"N", "V"},
    "kal":   {"N"},
    "li":    {"N"},
    "lil":   {"N"},
    "ne":    {"V"},
    "ple":   {"NUM"},
    "pul":   {"N"},
    "sim":   {"N"},
    "su":    set(),    # pronoun possessive marker — no POS constraint enforced here
    "yum":   {"NUM"},
}

# Stacking caps (greedy path only; LexiliAsel ground-truth overrides)
MAX_PREFIXES_PER_WORD = 1
MAX_SUFFIXES_PER_WORD = 1  # softened by -cu optionality rule below

# §02 inharelexi: -cu is optional before these suffixes on intransitive-capable verbs.
# So both "buka-ne" and "buka-cu-ne" are grammatical.
CU_OPTIONAL_BEFORE: frozenset[str] = frozenset({"ne", "do", "abil", "musi", "ingay"})


def suffix_pos_ok(suffix: str, base_pos: str) -> bool:
    """Return True if `suffix` is compatible with `base_pos` (or if no constraint exists)."""
    allowed = SUFFIX_BASE_POS.get(suffix)
    if allowed is None:
        # Unknown suffix — accept (no false rejections)
        return True
    if not allowed:
        # Empty set means any POS
        return True
    return base_pos in allowed
