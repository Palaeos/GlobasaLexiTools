"""
LexiliAsel breakdown parser.

Format examples observed in word-list.csv:
  aboneyen     → "abone + -yen"
  acidihamir   → "acidi + hamir"          (compound, no affix marker)
  adolapulya   → "adola + -pul + -ya"
  Akiletendon  → "Akile + tendon"         (capitalised root)
  be- + ...    → prefix piece
  ... + -ya    → suffix piece

Exception patterns encountered during spike (all handled):
  - Parenthetical notes like "(see also)" → strip and skip
  - Multiple forms separated by ";" or "/" → take first alternative
  - Empty or whitespace-only LexiliAsel → skip
  - Bare "-" entries or single-dash pieces → skip

All unrecognised patterns are logged via warnings at load time and excluded from
`derived` (falls through to greedy/fallback). See SKIPPED_LEXILIASEL_PATTERNS below.
"""

from __future__ import annotations

import re
import warnings
from dataclasses import dataclass
from typing import Optional


# Regex to strip parenthetical notes
_PAREN_RE = re.compile(r'\(.*?\)')

# Strip trailing etymology/comparison notes:
#   ". LangName (alternative)" — e.g. "barix + ababil. Turkisa (ebabil)."
#   ". Am kompara: ..." — Globasa cross-reference notes
_ETYM_SUFFIX_RE = re.compile(r'\.\s+(?:\w+sa\b|\bAm\b).*$')

# Strip standalone language notes starting from "Am " (Globasa etymology note pattern)
_AM_NOTE_RE = re.compile(r'^Am\s+.*?[,\.]\s*')

# Patterns we take the first alternative from
_MULTI_ALT_RE = re.compile(r'[;/]')


@dataclass
class RawMorpheme:
    """Intermediate: a LexiliAsel piece before offset assignment."""
    surface: str     # bare form (no '-' markers)
    lemma: str       # form with '-' markers as appropriate
    kind: str        # "ROOT" | "PREFIX" | "SUFFIX"


def parse_lexiliasel(lexiliasel_str: str, word: str) -> Optional[list[RawMorpheme]]:
    """Parse a LexiliAsel string into a list of RawMorpheme entries.

    Returns None if the string cannot be parsed or is empty/malformed.
    The caller is responsible for running offset alignment on the result.
    """
    if not lexiliasel_str or not isinstance(lexiliasel_str, str):
        return None

    raw = lexiliasel_str.strip()
    if not raw:
        return None

    # Strip "Am X, Y" style etymology preambles (e.g. "Am oko melodi, drama.")
    raw = _AM_NOTE_RE.sub("", raw).strip()
    if not raw:
        return None

    # Strip trailing etymology notes from the whole string (". LangName ...")
    raw = _ETYM_SUFFIX_RE.sub("", raw).strip()
    if not raw:
        return None

    # Strip parenthetical notes
    raw = _PAREN_RE.sub("", raw).strip()
    if not raw:
        return None

    # Take first alternative if multiple forms given (e.g. "form1 / form2")
    if _MULTI_ALT_RE.search(raw):
        raw = _MULTI_ALT_RE.split(raw)[0].strip()
        if not raw:
            return None

    # Split on '+'
    pieces = [p.strip() for p in raw.split("+")]
    pieces = [p for p in pieces if p and p != "-"]

    if not pieces:
        return None

    result: list[RawMorpheme] = []
    for piece in pieces:
        if not piece or piece == "-":
            continue

        if piece.startswith("-") and piece.endswith("-"):
            # Double-dash (infix?) — treat as root, strip dashes
            bare = piece.strip("-")
            if not bare:
                continue
            result.append(RawMorpheme(surface=bare, lemma=bare, kind="ROOT"))
        elif piece.startswith("-"):
            # Suffix: "-ya", "-yen", "-li" etc.
            bare = piece[1:]
            if not bare:
                continue
            result.append(RawMorpheme(surface=bare, lemma=piece, kind="SUFFIX"))
        elif piece.endswith("-"):
            # Prefix: "be-", "du-" etc.
            bare = piece[:-1]
            if not bare:
                continue
            result.append(RawMorpheme(surface=bare, lemma=piece, kind="PREFIX"))
        else:
            # Root or compound piece (no '-' markers)
            result.append(RawMorpheme(surface=piece, lemma=piece, kind="ROOT"))

    if not result:
        return None

    # Basic sanity: verify that all surfaces concatenate to the word (case-insensitive).
    # If they don't, the breakdown is mismatched and we return None.
    concat = "".join(m.surface for m in result)
    if concat.lower() != word.lower():
        warnings.warn(
            f"LexiliAsel mismatch: '{lexiliasel_str}' → concat='{concat}' ≠ word='{word}'",
            stacklevel=2,
        )
        return None

    return result
