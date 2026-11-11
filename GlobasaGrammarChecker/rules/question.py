from .base import GrammarRule, GrammarMatch

# ke-correlative interrogatives and question particles
INTERROGATIVES = {"keto", "kete", "keoto", "keete", "kesu", "kepul", "kemo",
                  "kekwanti", "kenumer", "keloka", "kewatu", "keseba", "kemaner",
                  "kam", "kama", "ke"}


class QuestionRule(GrammarRule):
    """Yes/no question (ends with '?') should start with 'kam'.

    Exceptions: WH-questions (ke-correlatives), colon questions ('X: A or B?').
    """
    rule_id = "GLOBASA_QUESTION_KAM"

    def check(self, tokens, pos_list, lemmas, text):
        matches = []
        stripped = text.rstrip()
        if not stripped.endswith("?"):
            return matches
        # Colon questions: "Yu suki keto: kafe or cay?" — no kam needed
        if ":" in text:
            return matches
        # Check if any interrogative correlative is present
        for lem in lemmas:
            if lem and lem in INTERROGATIVES:
                return matches
        # No interrogative — suggest 'kam'
        first_word = tokens[0][0] if tokens else ""
        question_body = stripped.rstrip("?").strip()
        matches.append(GrammarMatch(
            rule_id=self.rule_id,
            message="Yes/no questions should begin with 'kam'.",
            offset=0,
            length=len(first_word),
            context=first_word,
            suggestions=[f"Kam {question_body[0].lower() + question_body[1:]}?"],
        ))
        return matches
