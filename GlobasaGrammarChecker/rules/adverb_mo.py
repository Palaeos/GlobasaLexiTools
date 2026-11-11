import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from PosTagger import df, T_CLASS

from .base import GrammarRule, GrammarMatch

# Known standalone -mo adverbs that don't require a following adj/adv.
# These function as sentence/VP adverbs, not adj-modifying adverbs.
STANDALONE_MO = {"daymo", "godomo", "lilmo", "kufimo"}


def _is_mo_adverb(surface, lemma):
    """Check if word is a -mo adjective/adverb-modifying adverb."""
    word = surface.lower().rstrip(".,;:!?")
    if not word.endswith("mo"):
        return False
    if lemma in STANDALONE_MO:
        return False
    # Check that the base (without -mo) is a known t-class word
    base = word.removesuffix("mo")
    if base and base in T_CLASS:
        return True
    if base and base in df.index:
        return True
    return False


class AdverbMoRule(GrammarRule):
    """-mo adverbs modify adjectives/adverbs, not verbs or nouns.

    CORRECT: perfetomo syahe (perfectly black)
    ERROR:   perfetomo yam (perfectly eat) — use 'perfeto yam' instead
    """
    rule_id = "GLOBASA_MO_ADVERB"

    def check(self, tokens, pos_list, lemmas, text):
        matches = []
        n = len(tokens)
        for i in range(n):
            if not _is_mo_adverb(tokens[i][0], lemmas[i]):
                continue
            # Scan forward: skip other -mo adverbs, expect ADJ or ADV
            j = i + 1
            while j < n and _is_mo_adverb(tokens[j][0], lemmas[j]):
                j += 1
            if j >= n:
                continue  # end of sentence, can't tell
            target_pos = pos_list[j]
            # ADJ or ADV (including other t-class resolved words) is correct
            if target_pos in ("ADJ", "ADV"):
                continue
            # V or N means the -mo form is wrong — should use bare t-class form
            if target_pos in ("V", "N", "PRON"):
                mo_surface = tokens[i][0]
                bare = mo_surface.rstrip(".,;:!?").removesuffix("mo")
                target_surface = tokens[j][0]
                offset = text.find(mo_surface)
                matches.append(GrammarMatch(
                    rule_id=self.rule_id,
                    message=f"'-mo' adverbs modify adjectives/adverbs, not verbs "
                            f"or nouns. Use '{bare}' to modify '{target_surface}'.",
                    offset=offset if offset >= 0 else 0,
                    length=len(mo_surface),
                    context=f"{mo_surface} {target_surface}",
                    suggestions=[bare],
                ))
        return matches
