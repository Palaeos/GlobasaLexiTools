from .base import GrammarRule, GrammarMatch


class NPStructureRule(GrammarRule):
    """Determiner not followed by a noun/pronoun → suggest closing with te/to."""
    rule_id = "GLOBASA_NP_CLOSURE"

    def check(self, tokens, pos_list, lemmas, text):
        matches = []
        n = len(tokens)
        for i in range(n):
            if pos_list[i] != "DET":
                continue
            # Scan forward: expect at least one noun/pronoun before clause end
            found_noun = False
            j = i + 1
            while j < n:
                if pos_list[j] in ("N", "PRON", "PROPN"):
                    found_noun = True
                    break
                if pos_list[j] in ("ADJ", "ADV", "NUM", "DET", "POSS"):
                    j += 1
                    continue
                # Hit something else (verb, prep, conj, etc.) — NP ended
                break
            if not found_noun and j < n and pos_list[j] == "V":
                det = tokens[i][0]
                offset = text.find(det)
                matches.append(GrammarMatch(
                    rule_id=self.rule_id,
                    message=f"Determiner '{det}' not followed by a noun. "
                            f"Use '{det} te' (person) or '{det} to' (thing) if the noun is understood.",
                    offset=offset,
                    length=len(det),
                    context=det,
                    suggestions=[f"{det} te", f"{det} to"],
                ))
        return matches
