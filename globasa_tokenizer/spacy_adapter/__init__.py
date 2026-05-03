"""
spaCy adapter for Globasa tokenizer.

Registers the 'glb' language with spaCy and provides a 'globasa_morph' pipeline
component that writes Token._.morphs on each token.

Usage:
    import spacy
    import globasa_tokenizer.spacy_adapter  # registers 'glb'
    nlp = spacy.blank('glb')
    nlp.add_pipe('globasa_morph')
    doc = nlp('Mi le yam kitabudom.')
    for tok in doc:
        print(tok.text, tok._.morphs)

The spaCy import is wrapped in try/except so this module can be imported without
spaCy installed — it will raise an informative ImportError only at use time.
"""

from __future__ import annotations

try:
    from spacy.language import Language
    from spacy.tokens import Doc
    _SPACY_AVAILABLE = True
except ImportError:
    _SPACY_AVAILABLE = False
    Language = None
    Doc = None

from .pipeline import morph_component  # noqa: F401 — registers the factory


def _require_spacy():
    if not _SPACY_AVAILABLE:
        raise ImportError(
            "spaCy is not installed. Install it with: pip install spacy\n"
            "Or: pip install 'globasa-tokenizer[spacy]'"
        )


if _SPACY_AVAILABLE:
    try:
        from spacy.language import BaseDefaults
        from spacy.util import registry

        _STOP_WORDS = {
            "le", "xa", "na", "no", "fe", "ki", "hu", "da", "nun", "am", "ger",
            "jale", "jaxa", "u", "mi", "yu", "te", "to", "fe", "ye", "xen",
        }

        class GlobasaDefaults(BaseDefaults):
            stop_words = _STOP_WORDS
            writing_system = {"direction": "ltr", "has_case": True, "has_letters": True}

        @registry.languages("glb")
        class GlobasaLanguage(Language):
            lang = "glb"
            Defaults = GlobasaDefaults

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # Wire up our tokenizer
                from .. import GlobasaTokenizer
                self._glb_core = GlobasaTokenizer()

            def make_doc(self, text: str) -> Doc:
                token_groups = self._glb_core.tokenize(text)
                words = ["".join(m.surface for m in tg) for tg in token_groups]
                # Infer spaces: a token has a trailing space if the next token
                # doesn't start immediately after it.
                spaces = []
                for i, tg in enumerate(token_groups):
                    if i + 1 < len(token_groups):
                        this_end = tg[-1].end
                        next_start = token_groups[i + 1][0].start
                        spaces.append(next_start > this_end)
                    else:
                        spaces.append(False)
                doc = Doc(self.vocab, words=words, spaces=spaces)
                doc.user_data[("globasa_morphs",)] = token_groups
                return doc

    except Exception:
        GlobasaLanguage = None
        GlobasaDefaults = None
else:
    GlobasaLanguage = None
    GlobasaDefaults = None


__all__ = ["GlobasaLanguage", "GlobasaDefaults", "morph_component"]
