"""
Word-level segmenter (the hot path).

Pipeline order (per spec):
  1. Function word        (frozenset hit → single FUNCTION morpheme)
  2. Derived w/ LexiliAsel  (dict hit → cached tuple, ground truth)
  3. Root                 (set hit → single ROOT morpheme)
  4. Proper noun          (case-preserving set hit → single PROPER morpheme)
  5. Greedy native affix  (prefix trie + recursive suffix trie)
  6. Pseudo-morpheme tile (Aho-Corasick + DP cover; only if decompose_pseudo_morphemes=True)
  7. Fallback cascade     (mined stems → syllables → bigrams → chars)

The LRU cache keyed by (lowercased_word, id(lexicon)) ensures the cold path
(steps 5-7) is only computed once per distinct word form per process lifetime.
Offsets and word_index are added AFTER cache lookup, never stored in the cache.
"""

from __future__ import annotations

import functools
from typing import Optional, TYPE_CHECKING

from ._types import Morpheme, MorphKind
from .fallback_cascade import cascade as _cascade

if TYPE_CHECKING:
    from .lexicon import Lexicon

ROOT = MorphKind.ROOT
PREFIX = MorphKind.PREFIX
SUFFIX = MorphKind.SUFFIX
PSEUDO = MorphKind.PSEUDO_MORPHEME
SYLLABLE = MorphKind.SYLLABLE
FUNCTION = MorphKind.FUNCTION
PROPER = MorphKind.PROPER
FOREIGN = MorphKind.FOREIGN
UNK = MorphKind.UNK


def _looks_foreign(word: str, lex: "Lexicon") -> bool:
    """Heuristic: does this token look like an unadapted foreign loanword?

    Triggers:
      - CamelCase past first char  (ChatGPT, OpenAI, GitHub)
      - Contains a digit           (3, GPT4, COVID-19)
      - Contains a letter outside the Globasa alphabet (q, accented letters
        not used by Globasa, etc.)
      - All-uppercase token of length ≥ 2 (LLM, NASA, USA — acronyms)

    Capital-initial tokens (Claude, Anthropic, Discord) are NOT auto-flagged
    here — they're left for the standard pipeline first; only after every
    other lookup fails does segment_word fall back to FOREIGN as a catch-all
    for capitalised OOV tokens.
    """
    if not word:
        return False
    # CamelCase past position 0: any uppercase letter beyond the first char.
    if any(c.isupper() for c in word[1:]):
        return True
    # Contains a digit.
    if any(c.isdigit() for c in word):
        return True
    # Letters outside Globasa's alphabet (a-z, A-Z minus q; q is non-Globasa).
    for ch in word:
        if ch.isalpha() and not ('a' <= ch.lower() <= 'z'):
            return True
        if ch.lower() == 'q':
            return True
    # All-uppercase acronym (LLM, NASA, USA, EU)
    if len(word) >= 2 and word.isupper() and word.isalpha():
        return True
    return False

# Kind-string to MorphKind (for LexiliAsel-stored tuples + greedy-path tuples)
_KIND_MAP: dict[str, MorphKind] = {
    "ROOT": ROOT,
    "PREFIX": PREFIX,
    "SUFFIX": SUFFIX,
    "PROPER": PROPER,
}


def _shift(
    aligned: tuple,
    base_offset: int,
    word_index: int,
    original_word: str = "",
) -> list[Morpheme]:
    """Convert word-relative aligned tuples to Morpheme objects with sentence offsets.

    If original_word is provided, surface is taken from original_word[start:end]
    to preserve original casing (important for proper nouns and sentence-initial caps).
    """
    out = []
    for stored_surface, lemma, kind_str, start, end in aligned:
        if original_word:
            surface = original_word[start:end]
        else:
            surface = stored_surface
        out.append(Morpheme(
            surface=surface,
            lemma=lemma,
            kind=_KIND_MAP.get(kind_str, ROOT),
            start=start + base_offset,
            end=end + base_offset,
            word_index=word_index,
        ))
    return out


def _make_single(
    surface: str, lemma: str, kind: MorphKind,
    base_offset: int, word_index: int,
) -> list[Morpheme]:
    return [Morpheme(
        surface=surface,
        lemma=lemma,
        kind=kind,
        start=base_offset,
        end=base_offset + len(surface),
        word_index=word_index,
    )]


# ---------------------------------------------------------------------------
# Greedy affix segmentation (cold path — words not in lexicon)
# ---------------------------------------------------------------------------

def _greedy(
    word: str,
    lex: "Lexicon",
    decompose_pseudo: bool,
    depth: int = 0,
) -> Optional[list[tuple]]:
    """Try to segment `word` (lowercased) by stripping one prefix and/or one suffix.

    Returns a list of (surface, lemma, kind_str, start, end) word-relative tuples,
    or None if no affix matches (caller handles UNK/fallback).
    """
    if depth > 4:
        # Safety: avoid infinite recursion on pathological inputs
        return None

    # Try prefix match
    pfx_result = lex.prefix_trie.longest_match(word)
    if pfx_result:
        pfx, pfx_len = pfx_result
        stem = word[pfx_len:]
        if not stem:
            return None  # Can't strip the whole word as a prefix
        # Recurse on stem
        stem_morphs = _segment_stem(stem, pfx_len, lex, decompose_pseudo, depth + 1)
        if stem_morphs is not None:
            prefix_morph = (word[:pfx_len], pfx + "-", "PREFIX", 0, pfx_len)
            return [prefix_morph] + stem_morphs
        # Prefix didn't help — fall through to direct stem analysis
    # No prefix — try stem directly
    return _segment_stem(word, 0, lex, decompose_pseudo, depth)


def _segment_stem(
    word: str,
    base: int,
    lex: "Lexicon",
    decompose_pseudo: bool,
    depth: int,
) -> Optional[list[tuple]]:
    """Segment the stem (no more prefixes). Returns word-relative tuples or None."""
    if not word:
        return None

    # Check if stem is a known root / function / derived / proper noun.
    if word in lex.function_words:
        return [(word, word, "ROOT", base, base + len(word))]
    if word in lex.roots:
        return [(word, word, "ROOT", base, base + len(word))]
    if word in lex.derived:
        aligned = lex.derived[word]
        shifted = []
        for surface, lemma, kind_str, start, end in aligned:
            shifted.append((surface, lemma, kind_str, start + base, end + base))
        return shifted
    # Proper-noun lookup is case-preserving in the lexicon (e.g. 'Engli'); try
    # title-case so the recursion through 'englisali' → 'englisa' → 'engli'
    # can still resolve. Without this, 'Englisali' falls all the way through
    # to syllable cascade.
    if word and word[0].islower():
        titled = word[0].upper() + word[1:]
        if titled in lex.proper_nouns:
            return [(titled, titled, "PROPER", base, base + len(word))]

    # Try suffix match
    sfx_result = lex.suffix_trie.longest_match(word)
    if sfx_result:
        sfx, sfx_len = sfx_result
        inner = word[:-sfx_len]
        if inner:
            inner_morphs = _segment_stem(inner, base, lex, decompose_pseudo, depth + 1)
            if inner_morphs is not None:
                sfx_start = base + len(inner)
                sfx_end = sfx_start + sfx_len
                suffix_morph = (word[-sfx_len:], "-" + sfx, "SUFFIX", sfx_start, sfx_end)
                return inner_morphs + [suffix_morph]

    # Compound split: try to break the word at any internal position so that
    # both halves resolve to known morpheme sequences. This handles pure
    # root+root compounds like 'mambatexto' = mamba + texto that the
    # affix-stripping path can't see. Greedy: prefer the leftmost split that
    # yields a maximally-long resolved left half.
    #
    # When pseudo-morpheme decomposition is enabled AND the word ends with a
    # known pseudo-suffix (e.g. '-si', '-syon'), skip compound-split here so
    # step 6 in segment_word() can attach the canonical lemma ('-tion').
    # Otherwise the eager compound-split would resolve `informasi` → in+forma+si
    # before the pseudo-morpheme handler ever runs.
    if depth < 4:
        skip_compound = False
        if decompose_pseudo:
            cover = lex.pseudo_matcher.match(word)
            for _s, e, _surf, lemma in cover:
                if lemma != "__residue__" and e == len(word):
                    skip_compound = True
                    break
        if not skip_compound:
            for split_at in range(len(word) - 1, 1, -1):
                left = word[:split_at]
                right = word[split_at:]
                left_morphs = _segment_stem(left, base, lex, decompose_pseudo, depth + 1)
                if left_morphs is None:
                    continue
                right_morphs = _segment_stem(right, base + split_at, lex, decompose_pseudo, depth + 1)
                if right_morphs is None:
                    continue
                return left_morphs + right_morphs
    return None


@functools.lru_cache(maxsize=20_000)
def _segment_lower_cached(
    word: str,
    lex_id: int,
    decompose_pseudo: bool,
) -> Optional[tuple]:
    """Cache-safe inner segmentation (no offsets, no word_index).

    Returns tuple of (surface, lemma, kind_str, rel_start, rel_end) or None.
    The cache is keyed by lowercased word + lexicon id + decompose flag.
    NOTE: lex is NOT in the signature (not hashable); lex_id is id(lex).
    This function must look up the lexicon from a thread-local or closure.
    We work around this by passing lex explicitly to the wrapper.
    """
    # This function is called with the lexicon injected by the wrapper below.
    # The lru_cache signature doesn't include lex, so we use a module-level
    # registry to look it up.
    return None  # stub — see _cached_segment_impl


# We can't cache with lex in the signature (not hashable), so we use a different pattern:
# a module-level dict mapping id(lex) → lex for the duration of the process.
_LEX_REGISTRY: dict[int, "Lexicon"] = {}


def _cached_segment(
    word: str,
    lex: "Lexicon",
    decompose_pseudo: bool,
) -> Optional[tuple]:
    """Cached segmentation wrapper. Returns None or tuple of 5-tuples."""
    lex_id = id(lex)
    _LEX_REGISTRY[lex_id] = lex
    return _segment_cached_impl(word, lex_id, decompose_pseudo)


@functools.lru_cache(maxsize=20_000)
def _segment_cached_impl(word: str, lex_id: int, decompose_pseudo: bool) -> Optional[tuple]:
    """Actual cached impl. Retrieves lex from registry by id."""
    lex = _LEX_REGISTRY.get(lex_id)
    if lex is None:
        return None
    result = _greedy(word, lex, decompose_pseudo)
    if result is None:
        return None
    return tuple(result)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def segment_word(
    word: str,
    base_offset: int,
    word_index: int,
    lex: "Lexicon",
    decompose_pseudo_morphemes: bool = False,
    max_root_chars: Optional[int] = None,
) -> list[Morpheme]:
    """Segment a single word into morphemes with sentence-level offsets.

    word:          surface form as it appears in the sentence
    base_offset:   character offset of word[0] in the sentence
    word_index:    0-based index of this word in the sentence
    lex:           the frozen Lexicon
    decompose_pseudo_morphemes: if True, apply pseudo-morpheme tiling (step 6)
    max_root_chars: if set, apply fallback cascade to ROOT morphemes longer than this
    """
    # Handle affix entries (words that start or end with '-' in the word-list, like '-bol', 'be-')
    # These are affix dictionary entries, not surface word forms. Return them as-is.
    if word.startswith("-") and not word.endswith("-"):
        bare = word[1:]
        # Treat as a suffix entry: return single SUFFIX morpheme
        return [Morpheme(
            surface=word,
            lemma=word,
            kind=SUFFIX,
            start=base_offset,
            end=base_offset + len(word),
            word_index=word_index,
        )]
    if word.endswith("-") and not word.startswith("-"):
        bare = word[:-1]
        # Treat as a prefix entry: return single PREFIX morpheme
        return [Morpheme(
            surface=word,
            lemma=word,
            kind=PREFIX,
            start=base_offset,
            end=base_offset + len(word),
            word_index=word_index,
        )]

    # Handle hyphenated compounds: split on '-' and segment each part separately
    # (hyphens between alpha chars are kept inside the word by the scanner, so we
    # need to handle them here). Only split if '-' is present and not a prefix/suffix marker.
    if "-" in word and not word.startswith("-") and not word.endswith("-"):
        parts = word.split("-")
        if all(p for p in parts):  # no empty parts (no leading/trailing hyphen)
            result: list[Morpheme] = []
            pos = base_offset
            for i, part in enumerate(parts):
                part_morphs = segment_word(
                    part, pos, word_index, lex,
                    decompose_pseudo_morphemes=decompose_pseudo_morphemes,
                    max_root_chars=max_root_chars,
                )
                result.extend(part_morphs)
                pos += len(part)
                # Add a synthetic hyphen morpheme between parts
                if i < len(parts) - 1:
                    result.append(Morpheme(
                        surface="-",
                        lemma="-",
                        kind=MorphKind.PUNCT,
                        start=pos,
                        end=pos + 1,
                        word_index=word_index,
                    ))
                    pos += 1
            return result

    # Step 0: Obvious-foreign tokens (CamelCase, digits, non-Globasa letters,
    # all-uppercase acronyms) — emit as a single FOREIGN morpheme without any
    # morphological analysis. Catches things like 'ChatGPT', 'OpenAI', '3',
    # 'COVID-19', 'GitHub'.
    if _looks_foreign(word, lex):
        return _make_single(word, word, FOREIGN, base_offset, word_index)

    w = word.lower()

    # Step 1: Derived word (LexiliAsel ground truth) — wins over function-word
    # lookup so words like 'moyun' (Category=derived, WordClass=d) get their
    # 'moy- + un' breakdown rendered instead of being treated as one chip.
    if w in lex.derived:
        aligned = lex.derived[w]
        result = _shift(aligned, base_offset, word_index, original_word=word)
        if max_root_chars is not None:
            result = _apply_max_root(result, max_root_chars, base_offset, word_index, lex)
        return result

    # Step 2: Function word
    if w in lex.function_words:
        return _make_single(word, w, FUNCTION, base_offset, word_index)

    # Step 3: Root
    if w in lex.roots:
        if decompose_pseudo_morphemes:
            # Even lexicon roots get pseudo-morpheme tiling when the flag is on
            # (per spec: "Sinitic-origin roots become candidates for pseudo-morpheme tiling")
            pm_cover = lex.pseudo_matcher.match(w)
            has_pseudo = any(pm_lemma != "__residue__" for _, _, _, pm_lemma in pm_cover)
            if has_pseudo:
                morphs = []
                for start, end, surface, pm_lemma in pm_cover:
                    actual_surface = word[start:end]
                    if pm_lemma == "__residue__":
                        # Short residue → single SYLLABLE (skip the heavy cascade).
                        if (end - start) <= 3:
                            morphs.append(Morpheme(
                                surface=actual_surface,
                                lemma=actual_surface.lower(),
                                kind=SYLLABLE,
                                start=base_offset + start,
                                end=base_offset + end,
                                word_index=word_index,
                            ))
                        else:
                            sub_cover = _cascade(actual_surface, lex.mined_matcher)
                            for sc_start, sc_end, sc_surf, _ in sub_cover:
                                morphs.append(Morpheme(
                                    surface=word[start + sc_start: start + sc_end],
                                    lemma=word[start + sc_start: start + sc_end].lower(),
                                    kind=SYLLABLE,
                                    start=base_offset + start + sc_start,
                                    end=base_offset + start + sc_end,
                                    word_index=word_index,
                                ))
                    else:
                        morphs.append(Morpheme(
                            surface=actual_surface,
                            lemma=pm_lemma,
                            kind=PSEUDO,
                            start=base_offset + start,
                            end=base_offset + end,
                            word_index=word_index,
                        ))
                if morphs:
                    return morphs
        morphs = _make_single(word, w, ROOT, base_offset, word_index)
        if max_root_chars is not None:
            morphs = _apply_max_root(morphs, max_root_chars, base_offset, word_index, lex)
        return morphs

    # Step 4: Proper noun (case-preserving)
    if word in lex.proper_nouns:
        return _make_single(word, word, PROPER, base_offset, word_index)
    # Also try title-case lookup for proper nouns
    titled = word[0].upper() + word[1:].lower() if len(word) > 1 else word.upper()
    if titled in lex.proper_nouns:
        return _make_single(word, titled, PROPER, base_offset, word_index)

    # Step 5: Greedy native affix (cached). Pass decompose_pseudo through so
    # _segment_stem's compound-split gating can defer to step 6 when the word
    # ends with a known pseudo-morpheme.
    cached = _cached_segment(w, lex, decompose_pseudo_morphemes)
    if cached is not None:
        result = []
        for surface, lemma, kind_str, rel_start, rel_end in cached:
            result.append(Morpheme(
                surface=word[rel_start:rel_end],
                lemma=lemma,
                kind=_KIND_MAP.get(kind_str, ROOT),
                start=rel_start + base_offset,
                end=rel_end + base_offset,
                word_index=word_index,
            ))
        if max_root_chars is not None:
            result = _apply_max_root(result, max_root_chars, base_offset, word_index, lex)
        return result

    # Step 6: Pseudo-morpheme tile (opt-in)
    if decompose_pseudo_morphemes:
        cover = lex.pseudo_matcher.match(w)
        # Build morpheme list; residue pieces go to cascade (or single SYLLABLE if short)
        morphs: list[Morpheme] = []
        for start, end, surface, pm_lemma in cover:
            actual_surface = word[start:end]
            if pm_lemma == "__residue__":
                if (end - start) <= 3:
                    morphs.append(Morpheme(
                        surface=actual_surface,
                        lemma=actual_surface.lower(),
                        kind=SYLLABLE,
                        start=base_offset + start,
                        end=base_offset + end,
                        word_index=word_index,
                    ))
                    continue
                # Run cascade on the residue substring
                sub_cover = _cascade(actual_surface, lex.mined_matcher)
                for sc_start, sc_end, sc_surf, _ in sub_cover:
                    morphs.append(Morpheme(
                        surface=word[start + sc_start: start + sc_end],
                        lemma=word[start + sc_start: start + sc_end],
                        kind=SYLLABLE,
                        start=base_offset + start + sc_start,
                        end=base_offset + start + sc_end,
                        word_index=word_index,
                    ))
            else:
                morphs.append(Morpheme(
                    surface=actual_surface,
                    lemma=pm_lemma,
                    kind=PSEUDO,
                    start=base_offset + start,
                    end=base_offset + end,
                    word_index=word_index,
                ))
        if morphs:
            return morphs

    # Step 6.5: Capitalised OOV catch-all. If we got this far and the word
    # starts with an uppercase letter and isn't a known proper noun, it's
    # almost certainly an unadapted foreign loanword (Claude, Discord,
    # Anthropic). Emit as a single FOREIGN morpheme rather than syllabifying.
    if word and word[0].isupper():
        return _make_single(word, word, FOREIGN, base_offset, word_index)

    # Step 7: Fallback cascade (always succeeds)
    cover = _cascade(w, lex.mined_matcher)
    morphs = []
    for start, end, surface, _ in cover:
        morphs.append(Morpheme(
            surface=word[start:end],
            lemma=word[start:end].lower(),
            kind=SYLLABLE,
            start=base_offset + start,
            end=base_offset + end,
            word_index=word_index,
        ))
    return morphs


def _apply_max_root(
    morphs: list[Morpheme],
    max_root_chars: int,
    base_offset: int,
    word_index: int,
    lex: "Lexicon",
) -> list[Morpheme]:
    """Apply fallback cascade to ROOT morphemes longer than max_root_chars."""
    out: list[Morpheme] = []
    for m in morphs:
        if m.kind == ROOT and len(m.surface) > max_root_chars:
            sub_cover = _cascade(m.surface, lex.mined_matcher)
            for sc_start, sc_end, sc_surf, _ in sub_cover:
                out.append(Morpheme(
                    surface=m.surface[sc_start:sc_end],
                    lemma=m.surface[sc_start:sc_end].lower(),
                    kind=SYLLABLE,
                    start=m.start + sc_start,
                    end=m.start + sc_end,
                    word_index=word_index,
                ))
        else:
            out.append(m)
    return out
