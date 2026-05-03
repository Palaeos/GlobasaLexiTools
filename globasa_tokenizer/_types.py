"""
Core data types for globasa_tokenizer.

Separated from __init__.py to avoid circular imports:
  - __init__.py re-exports these
  - segmenter.py, tokenizer.py, etc. import from here directly
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class MorphKind(Enum):
    ROOT = "root"
    PREFIX = "prefix"
    SUFFIX = "suffix"
    PSEUDO_MORPHEME = "pseudo_morpheme"
    SYLLABLE = "syllable"
    FUNCTION = "function"
    PROPER = "proper"
    FOREIGN = "foreign"        # unadapted loanword (CamelCase, brand names, English etc.)
    PUNCT = "punct"
    UNK = "unk"


@dataclass(frozen=True, slots=True)
class Morpheme:
    surface: str        # exact substring from input (no '-' markers)
    lemma: str          # canonical key with '-' markers ('-yen', 'be-', 'kitabu')
    kind: MorphKind
    start: int          # inclusive character offset into the sentence string
    end: int            # exclusive character offset into the sentence string
    word_index: int     # 0-based index of the owning word token in the sentence
    pos: Optional[str] = None   # contextual POS (only head morpheme, with_pos=True)
