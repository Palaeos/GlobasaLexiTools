class GrammarMatch:
    """A single grammar error found in the text."""
    def __init__(self, rule_id, message, offset, length, context, suggestions=None):
        self.rule_id = rule_id
        self.message = message
        self.offset = offset       # character offset in original text
        self.length = length       # character length of the error span
        self.context = context     # the matched text
        self.suggestions = suggestions or []

    def to_lt_dict(self):
        """Convert to LanguageTool-compatible JSON dict."""
        return {
            "message": self.message,
            "shortMessage": self.rule_id,
            "replacements": [{"value": s} for s in self.suggestions],
            "offset": self.offset,
            "length": self.length,
            "rule": {
                "id": self.rule_id,
                "description": self.message,
                "issueType": "grammar",
                "category": {"id": "GLOBASA_GRAMMAR", "name": "Globasa Grammar"},
            },
            "context": {
                "text": self.context,
                "offset": 0,
                "length": len(self.context),
            },
        }


class GrammarRule:
    """Base class for grammar rules."""
    rule_id = "GLOBASA_BASE"

    def check(self, tokens, pos_list, lemmas, text):
        """Check tokens for errors. Returns list of GrammarMatch."""
        raise NotImplementedError
