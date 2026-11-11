from .base import GrammarRule, GrammarMatch

# Minimum consecutive nouns to flag (3+ is suspicious;
# 2 is common in apposition: "doste Mark", "Hotel Kaliforni")
MIN_PILE = 3


class NounPileRule(GrammarRule):
    """Warn when 3+ nouns appear consecutively without a verb, preposition, or particle.

    In Globasa, compound nouns are written as one word or hyphenated.
    A pile of space-separated nouns likely means a missing preposition,
    verb, or an intended compound.

    OK:  misu doste Mark (N N — apposition with proper noun)
    WARN: kitabu baytu oda (N N N — missing preposition or compound?)
    """
    rule_id = "GLOBASA_NOUN_PILE"

    def check(self, tokens, pos_list, lemmas, text):
        matches = []
        n = len(tokens)
        i = 0
        while i < n:
            # Find start of a noun run
            if pos_list[i] != "N":
                i += 1
                continue
            # Count consecutive nouns
            j = i
            while j < n and pos_list[j] in ("N", "PROPN"):
                j += 1
            run_len = j - i
            if run_len >= MIN_PILE:
                surfaces = [tokens[k][0].rstrip(".,;:!?") for k in range(i, j)]
                span = " ".join(surfaces)
                offset = text.find(surfaces[0])
                matches.append(GrammarMatch(
                    rule_id=self.rule_id,
                    message=f"{run_len} consecutive nouns: '{span}'. "
                            f"Consider a compound (written as one word), "
                            f"a preposition (fe, de, in), or a verb between them.",
                    offset=offset if offset >= 0 else 0,
                    length=len(span),
                    context=span,
                ))
            i = j
        return matches
