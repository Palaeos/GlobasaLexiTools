from .base import GrammarRule, GrammarMatch

TENSE_PARTICLES = {"le", "xa", "nun", "am", "ger", "jale", "jaxa", "u"}


class NegationRule(GrammarRule):
    """Detect 'no' at end of clause with nothing to negate.

    Globasa allows scope-flexible negation: 'no' immediately precedes the
    word/phrase being negated. 'Mi yam no pingo' = 'I eat non-apple' is valid.
    This rule only flags 'no' with nothing following it (dangling negation).
    """
    rule_id = "GLOBASA_NEGATION"

    def check(self, tokens, pos_list, lemmas, text):
        matches = []
        n = len(tokens)
        for i in range(n):
            if lemmas[i] != "no":
                continue
            # 'no' at end of sentence (before punctuation only)
            _, _, trail = tokens[i]
            is_final = (i == n - 1) or (i == n - 1 and trail)
            # Also check if next token is just punctuation / clause boundary
            if i + 1 < n:
                next_lem = lemmas[i + 1]
                next_pos = pos_list[i + 1]
                # 'no' followed by content word is fine (scope negation)
                if next_lem and next_pos != "UNK":
                    continue
            if is_final or (i + 1 >= n):
                offset = text.rfind("no")
                matches.append(GrammarMatch(
                    rule_id=self.rule_id,
                    message="'no' at end of sentence has nothing to negate. "
                            "Place 'no' before the verb: 'S no V O'.",
                    offset=offset if offset >= 0 else 0,
                    length=2,
                    context="no",
                ))
        return matches
