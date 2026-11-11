from .base import GrammarRule, GrammarMatch

TENSE_PARTICLES = {"le", "xa", "nun", "am", "ger", "jale", "jaxa", "u"}
# Words allowed between tense particle and verb
TRANSPARENT = {"no", "si", "daymo", "haji", "uje", "fori", "pimpan", "nadir",
               "hata", "pia", "sol", "kriban", "godomo", "lilmo", "kufi"}


class TenseParticleRule(GrammarRule):
    """Tense particle must be followed by a verb (possibly with no/adverbs between)."""
    rule_id = "GLOBASA_TENSE_PARTICLE"

    def check(self, tokens, pos_list, lemmas, text):
        matches = []
        n = len(tokens)
        for i in range(n):
            if pos_list[i] != "PAR" or lemmas[i] not in TENSE_PARTICLES:
                continue
            # Scan forward: skip transparent words and compound tense particles
            j = i + 1
            while j < n and (lemmas[j] in TRANSPARENT
                             or (pos_list[j] == "PAR" and lemmas[j] in TENSE_PARTICLES)):
                j += 1
            if j < n and pos_list[j] == "V":
                continue  # correct usage
            if j >= n:
                continue  # end of sentence, can't tell
            # Tense particle not followed by verb
            particle = tokens[i][0]
            next_word = tokens[j][0]
            offset = text.find(particle)
            matches.append(GrammarMatch(
                rule_id=self.rule_id,
                message=f"Tense particle '{particle}' should be followed by a verb, but found '{next_word}'.",
                offset=offset,
                length=len(particle),
                context=f"{particle} {next_word}",
            ))
        return matches
