from .base import GrammarRule, GrammarMatch

TENSE_PARTICLES = {"le", "xa", "nun", "jale", "jaxa"}


class ConditionalRule(GrammarRule):
    """In conditional mood (ger), the if-clause (eger) must use dictionary form.

    ERROR: Mi ger yam pingo eger mi le sen yamkal.
    CORRECT: Mi ger yam pingo eger mi sen yamkal.

    Non-conditional eger clauses (without ger in main clause) DO use tense markers.
    """
    rule_id = "GLOBASA_CONDITIONAL_EGER"

    def check(self, tokens, pos_list, lemmas, text):
        matches = []
        n = len(tokens)
        # Check if sentence has 'ger' (conditional) in main clause
        has_ger = any(lemmas[i] == "ger" for i in range(n))
        if not has_ger:
            return matches

        # Find 'eger' and check if a tense particle follows within its clause
        for i in range(n):
            if lemmas[i] != "eger":
                continue
            # Scan the eger-clause for tense particles
            for j in range(i + 1, n):
                # End of eger-clause at sentence end or next main-clause conjunction
                _, _, trail = tokens[j]
                if trail and any(c in trail for c in ".!?"):
                    break
                if lemmas[j] in TENSE_PARTICLES:
                    particle = tokens[j][0]
                    offset = text.find(particle, text.find("eger"))
                    matches.append(GrammarMatch(
                        rule_id=self.rule_id,
                        message=f"In conditional mood (ger), the if-clause after "
                                f"'eger' should use dictionary form. Remove '{particle}'.",
                        offset=offset if offset >= 0 else 0,
                        length=len(particle),
                        context=f"eger ... {particle}",
                        suggestions=[],
                    ))
                    break  # one error per eger-clause
        return matches
