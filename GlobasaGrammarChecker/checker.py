import sys
import os

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PosTagger import tokenize, assign_pos
from .rules import ALL_RULES


class GrammarChecker:
    """Globasa grammar checker using POS tagger and rule engine."""

    def __init__(self, rules=None):
        self.rules = [R() for R in (rules or ALL_RULES)]

    def check(self, text):
        """Check a single sentence/text. Returns list of GrammarMatch."""
        tokens = tokenize(text)
        pos_list = assign_pos(tokens)
        lemmas = [t[1] for t in tokens]
        all_matches = []
        for rule in self.rules:
            all_matches.extend(rule.check(tokens, pos_list, lemmas, text))
        return all_matches

    def check_text(self, text):
        """Check multi-sentence text. Returns list of GrammarMatch."""
        sentences = []
        current = []
        for ch in text:
            current.append(ch)
            if ch in '.!?':
                sentences.append(''.join(current).strip())
                current = []
        if current:
            remainder = ''.join(current).strip()
            if remainder:
                sentences.append(remainder)

        all_matches = []
        offset = 0
        for sentence in sentences:
            start = text.find(sentence, offset)
            matches = self.check(sentence)
            for m in matches:
                m.offset += start
            all_matches.extend(matches)
            offset = start + len(sentence)
        return all_matches

    def check_to_lt_json(self, text, language="glb"):
        """Check text and return LanguageTool-compatible JSON response."""
        matches = self.check_text(text)
        return {
            "software": {
                "name": "GlobasaGrammarChecker",
                "version": "0.1.0",
                "apiVersion": 1,
            },
            "language": {
                "name": "Globasa",
                "code": language,
            },
            "matches": [m.to_lt_dict() for m in matches],
        }
