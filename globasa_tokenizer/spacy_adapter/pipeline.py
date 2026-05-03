"""
'globasa_morph' spaCy pipeline component.

Writes Token._.morphs (list of Morpheme) on each token using the pre-computed
morpheme groups stored in doc.user_data by the GlobasaLanguage tokenizer.
"""

from __future__ import annotations

try:
    from spacy.language import Language
    from spacy.tokens import Token

    if not Token.has_extension("morphs"):
        Token.set_extension("morphs", default=None)

    @Language.factory("globasa_morph")
    def morph_component(nlp, name):
        def _component(doc):
            groups = doc.user_data.get(("globasa_morphs",), [])
            for tok, morphs in zip(doc, groups):
                tok._.morphs = morphs
            return doc
        return _component

except ImportError:
    # spaCy not available — define a no-op so the import doesn't fail
    def morph_component(nlp=None, name=None):
        raise ImportError(
            "spaCy is not installed. Install it with: pip install spacy"
        )
