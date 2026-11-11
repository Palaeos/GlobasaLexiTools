import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from PosTagger import lemmatize

from .base import GrammarRule, GrammarMatch


class PassiveAgentRule(GrammarRule):
    """In passive voice (be- prefix), the agent is a direct object — no 'fal'.

    ERROR: Pingo beyam fal mi.
    CORRECT: Pingo beyam mi.
    """
    rule_id = "GLOBASA_PASSIVE_FAL"

    def check(self, tokens, pos_list, lemmas, text):
        matches = []
        n = len(tokens)
        for i in range(n):
            if pos_list[i] != "V":
                continue
            # Check if verb has be- prefix (passive)
            surface = tokens[i][0].lower()
            lem = lemmas[i]
            is_passive = surface.startswith("be") and lem and not lem.startswith("be")
            if not is_passive:
                # Also check if lemma lookup stripped be-
                stripped = surface.removeprefix("be")
                if stripped and lemmatize(stripped):
                    is_passive = True
            if not is_passive:
                continue
            # Check if 'fal' follows the passive verb (possibly after object)
            for j in range(i + 1, min(i + 4, n)):
                if lemmas[j] == "fal":
                    fal_surface = tokens[j][0]
                    offset = text.find(fal_surface, text.find(surface))
                    matches.append(GrammarMatch(
                        rule_id=self.rule_id,
                        message="In passive voice (be-), the agent is expressed as "
                                "direct object without 'fal'. Remove 'fal'.",
                        offset=offset if offset >= 0 else 0,
                        length=len(fal_surface),
                        context=f"{surface} ... fal",
                        suggestions=[],
                    ))
                    break
                # Stop at clause boundaries
                _, _, trail = tokens[j]
                if trail and any(c in trail for c in ".,;!?"):
                    break
        return matches
