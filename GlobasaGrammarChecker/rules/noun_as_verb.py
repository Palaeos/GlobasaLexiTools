import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from PosTagger import df

from .base import GrammarRule, GrammarMatch

# Build set of noun-only b-class words: WordClass is exactly 'b' (no
# transitivity marker like b.oj, b.nenoj, b.oro, b.lin, b.oj.ru).
# These have only "n:" glosses and no established verb reading.
NOUN_ONLY_B = set()
for word, row in df.iterrows():
    wc = str(row.get("WordClass", "")).strip()
    # Accept plain 'b' and 'b; il' (noun + interjection), skip anything
    # with a dot (b.oj, b.nenoj, b.oro, b.lin, b.oj.ru) or 'xfik' (affix)
    if wc in ("b", "b; il"):
        NOUN_ONLY_B.add(word)


class NounAsVerbRule(GrammarRule):
    """Warn when a noun-only word (WordClass 'b', no verb transitivity) is used as a verb.

    Words marked 'b.oj', 'b.nenoj', 'b.oro', 'b.lin' have established verb
    readings. Plain 'b' words are nouns only — using them as verbs may be
    an error or require a derivational suffix (-gi, -cu).
    """
    rule_id = "GLOBASA_NOUN_AS_VERB"

    def check(self, tokens, pos_list, lemmas, text):
        matches = []
        n = len(tokens)
        for i in range(n):
            if pos_list[i] != "V":
                continue
            lem = lemmas[i]
            if not lem or lem not in NOUN_ONLY_B:
                continue
            surface = tokens[i][0].rstrip(".,;:!?")
            offset = text.find(surface)
            matches.append(GrammarMatch(
                rule_id=self.rule_id,
                message=f"'{surface}' is a noun (class 'b') with no established "
                        f"verb reading. Derive with '-gi' (transitive), "
                        f"'-cu' (intransitive), or '-li' (adjective/adverb).",
                offset=offset if offset >= 0 else 0,
                length=len(surface),
                context=surface,
                suggestions=[f"{lem}gi", f"{lem}cu", f"{lem}li"],
            ))
        return matches
