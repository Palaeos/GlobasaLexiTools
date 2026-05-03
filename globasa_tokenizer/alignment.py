"""
Alignment helpers for awesome-align / SimAlign / eflomal / GIZA++.

These functions bridge the morpheme tokenizer to bitext alignment tools.
The key problem: mBERT/XLM-R (used by awesome-align and SimAlign) fragments
Globasa into meaningless BPE pieces because Globasa isn't in their training data.
By feeding the aligner morpheme tokens instead, alignments become linguistically
meaningful and projectable.

API:
  to_aligner_text(text, lex)           → (morph_string, flat_morpheme_list)
  to_awesome_align_pair(glb, eng_toks) → "glb_morph1 ... ||| eng_tok1 ..."
  project_to_words(alignments, morphs) → [(glb_word_idx, other_idx), ...]
  project_to_morphs(alignments, morphs) → [(Morpheme, other_idx), ...]
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import Morpheme
    from .lexicon import Lexicon


def to_aligner_text(text: str, lex: "Lexicon") -> tuple[str, list["Morpheme"]]:
    """Tokenize text and return space-separated morpheme string + flat morpheme list.

    Example:
      'Mi le yam kitabudom.' →
        ('mi le yam kitabu dom .', [morph_mi, morph_le, morph_yam, morph_kitabu, morph_dom, morph_dot])

    The morpheme string is ready for awesome-align/eflomal stdin.
    The flat list lets callers project aligner output back to character spans.
    """
    from .tokenizer import _GlobasaTokenizerImpl
    from .lexicon import get_lexicon
    impl = _GlobasaTokenizerImpl()
    impl.lex = lex
    tokens = impl.tokenize(text)
    flat: list["Morpheme"] = [m for group in tokens for m in group]
    morph_str = " ".join(m.surface for m in flat)
    return morph_str, flat


def to_awesome_align_pair(
    glb_text: str,
    other_tokens: list[str],
    lex: "Lexicon",
) -> str:
    """Return one line in awesome-align's input format.

    Format: 'glb_morph1 glb_morph2 ... ||| other_tok1 other_tok2 ...'
    `other_tokens` is already-tokenized (e.g. spaCy English tokens).
    """
    morph_str, _ = to_aligner_text(glb_text, lex)
    other_str = " ".join(other_tokens)
    return f"{morph_str} ||| {other_str}"


def project_to_words(
    subword_alignments: list[tuple[int, int]],
    glb_morphs: list["Morpheme"],
) -> list[tuple[int, int]]:
    """Project (glb_morph_idx, other_idx) alignments to (glb_word_idx, other_idx).

    Multiple morphemes that share the same word_index are collapsed.
    Duplicate (word_idx, other_idx) pairs are removed.
    """
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, int]] = []
    for glb_idx, other_idx in subword_alignments:
        if 0 <= glb_idx < len(glb_morphs):
            word_idx = glb_morphs[glb_idx].word_index
            pair = (word_idx, other_idx)
            if pair not in seen:
                seen.add(pair)
                result.append(pair)
    return result


def project_to_morphs(
    subword_alignments: list[tuple[int, int]],
    glb_morphs: list["Morpheme"],
) -> list[tuple["Morpheme", int]]:
    """Like project_to_words but returns (Morpheme, other_idx) pairs.

    Useful for rendering alignment in the annotators using Morpheme.start/end.
    """
    result: list = []
    for glb_idx, other_idx in subword_alignments:
        if 0 <= glb_idx < len(glb_morphs):
            result.append((glb_morphs[glb_idx], other_idx))
    return result
