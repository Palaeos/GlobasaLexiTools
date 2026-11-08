"""Ancestor-centred alignment for Sino-xenic clusters.

The plain multiple alignment (align.msa) takes the medoid source form as its
centre and aligns letters by phonetic similarity alone, so 級 jí / kyū / geup /
cấp are lined up as four unrelated strings. Here the centre is their common
ancestor, the Middle Chinese reading (Baxter, in Globasa letters), and the
alignment runs one syllable at a time:

  1. the cluster's Han spelling: the one shared by most Sinosphere languages,
     every character with a Middle Chinese reading (else a Cantonese one: 礁);
  2. each Sinosphere member spelt that way is cut into one piece per character
     (dynamic programming against the characters' readings, with the Sino-xenic
     correspondence costs: Japanese epenthetic -tsu/-ku/-ki, lost stops, ...;
     every piece has a vowel); so is any other Sinosphere member that fits the
     readings well (Korean 곤봉 with no hanja in the table);
  3. each character's reading is the one closest to all members' pieces;
  4. each piece is aligned to its character's reading, and the pieces are
     concatenated, so a coda can never be matched with the next syllable's
     initial;
  5. everything else (other spellings, non-Sinosphere members) is aligned to the
     whole reading; a Globasa root (learning precedent) is cut like a member;
  6. a cluster with more other languages than cut ones (emoji, tea) is not
     handled here.

The rows are merged centre-star fashion, as in align.msa, then neighbouring
complementary columns are merged; the reading itself is not a row, so it casts
no vote. None when the cluster has no usable spelling.
"""

import collections
from functools import lru_cache

from . import sinosphere
from .align import GAP, NASAL_POS, _sino_coda, align, sino_sub_cost

ENABLED = True
MAX_READINGS = 4
SEG_MAX = 0.3        # a member not spelt like the cluster is cut if it fits this well (per letter)
VOWELS = set("aeiou")
# Middle Chinese reading -> reflex, on top of the Sino-xenic costs: MC tr- is
# Mandarin zh/ch and Japanese ch (中 trjuwng ~ zhōng ~ chū)
ANCESTOR_COST = {frozenset(p): 0.2 for p in ("jt", "cd")}


@lru_cache(maxsize=None)
def ancestor_cost(a, b):
    c = sino_sub_cost(a, b)
    return min(c, ANCESTOR_COST.get(frozenset((a, b)), c))


@lru_cache(maxsize=4096)
def _reading_info(ch):
    """(readings, source): Middle Chinese, else (fallback) Cantonese, which keeps the
    stop codas too (礁 has no Middle Chinese reading in the table)."""
    mc = sinosphere.table()["mc"]
    out = [sinosphere.baxter_to_globasa(r) for t in sinosphere._trad(ch) for r in mc.get(t, [])]
    src = "mc"
    if not out:
        src = "cantonese"
        try:
            out = [g for t in sinosphere._trad(ch) for g in sinosphere._canto_readings(t)]
        except Exception:
            out = []
    return tuple(dict.fromkeys(r for r in out if r))[:MAX_READINGS], src


def _readings(ch):
    return _reading_info(ch)[0]


def fallback_notes(spelling):
    """Notes for the characters whose reading is a fallback."""
    return [f"{ch}: no Middle Chinese reading, aligned to its Cantonese reading (fallback)"
            for ch in spelling if _reading_info(ch)[1] == "cantonese" and _reading_info(ch)[0]]


def _epenthetic(s, k):
    """Japanese vowel after a Middle Chinese stop (shitsu, seki, gaku)."""
    return k == len(s) - 1 and k >= 1 and s[k] in "iu" and s[k - 1] in "tkc"


@lru_cache(maxsize=200000)
def _syl(reading, piece, lang):
    """(cost, pairs) aligning one character's reading (a) to a member's piece (b)."""
    def coda(s, k):
        if s is piece:
            return lang == "ja" and _epenthetic(s, k)
        # the reading's codas (lost in Mandarin) and medial glides (光 kwang ~ kō)
        return _sino_coda(s, k) or (0 < k < len(s) - 1 and s[k] in "yw")
    # within one syllable the edges are no word edges: the initial is no
    # epenthetic vowel and must not be dropped cheaply
    return align(reading, piece, sub=ancestor_cost, coda=coda, nasal_pos=NASAL_POS, edge_gap=GAP)


def _piece_cost(readings, piece, lang):
    return min(_syl(r, piece, lang)[0] for r in readings)


@lru_cache(maxsize=50000)
def segment(form, per_char, lang):
    """Cut form into len(per_char) non-empty pieces, one per character
    (per_char: tuple of reading tuples). Returns (cost, pieces) or None."""
    n, L = len(per_char), len(form)
    if not n or L < n:
        return None
    INF = float("inf")
    D = [[INF] * (L + 1) for _ in range(n + 1)]
    B = [[0] * (L + 1) for _ in range(n + 1)]
    D[0][0] = 0.0
    for i in range(1, n + 1):
        for j in range(i, L - (n - i) + 1):
            for s in range(i - 1, j):
                if D[i - 1][s] == INF or not VOWELS & set(form[s:j]):   # every syllable has a vowel
                    continue
                c = D[i - 1][s] + _piece_cost(per_char[i - 1], form[s:j], lang)
                if c < D[i][j]:
                    D[i][j], B[i][j] = c, s
    if D[n][L] == INF:
        return None
    pieces, j = [], L
    for i in range(n, 0, -1):
        s = B[i][j]
        pieces.append(form[s:j])
        j = s
    return D[n][L], pieces[::-1]


def spelling(members, idx):
    """The Han spelling most Sinosphere languages share (ties: longer), with a
    Middle Chinese reading for every character; and the member indices spelt so."""
    langs = collections.defaultdict(set)
    spelt = collections.defaultdict(list)
    for i in idx:
        m = members[i]
        for h in set(sinosphere.han_spellings(m["lang"], m.get("word", ""), m.get("form"))):
            langs[h].add(m["lang"])
            spelt[h].append(i)
    for h in sorted(langs, key=lambda h: (-len(langs[h]), -len(h), h)):
        if len(langs[h]) < 2:
            break
        if all(_readings(c) for c in h):
            return h, spelt[h]
    return None, []


def _merge(center, aligned):
    """Centre-star merge (as in align.msa): aligned = [[(center letter|'-', letter|'-')]]."""
    gaps = [0] * (len(center) + 1)
    for pairs in aligned:
        ins, k = [0] * (len(center) + 1), 0
        for x, y in pairs:
            if x == "-":
                ins[k] += 1
            else:
                k += 1
        gaps = [max(g, x) for g, x in zip(gaps, ins)]
    rows = []
    for pairs in aligned:
        row, k, pending = [], 0, []
        for x, y in pairs:
            if x == "-":
                pending.append(y)
            else:
                row += pending + ["-"] * (gaps[k] - len(pending))
                pending = []
                row.append(y)
                k += 1
        row += pending + ["-"] * (gaps[k] - len(pending))
        rows.append(row)
    return _compact(rows)


def _compact(rows):
    """Drop empty columns and merge neighbours no row fills both of, when their
    letters are all consonants or all vowels: the centre-star merge leaves cmn j and
    ja c (both MC tr-) in two columns when neither matched the reading's t."""
    cols = []
    for col in zip(*rows):
        if all(c == "-" for c in col):
            continue
        if cols:
            prev = cols[-1]
            kinds = {c in VOWELS for c in prev + list(col) if c != "-"}
            if len(kinds) == 1 and all(a == "-" or b == "-" for a, b in zip(prev, col)):
                cols[-1] = [a if a != "-" else b for a, b in zip(prev, col)]
                continue
        cols.append(list(col))
    return [list(r) for r in zip(*cols)] if cols else [[] for _ in rows]


def rows(members, extra=(), sino_idx=None):
    """Rows for members' forms (spaces removed), then for each `extra` Globasa form
    (a root, cut into syllables like a member). None without a usable spelling."""
    if not ENABLED:
        return None
    if sino_idx is None:
        from .precedent import _sino
        sino_idx = _sino(members)
    sp, spelt = spelling(members, sino_idx)
    if not sp:
        return None
    per_char = tuple(_readings(c) for c in sp)
    forms = [(m.get("form") or "").replace(" ", "") for m in members]
    cuts, spelt = {}, set(spelt)
    for i in sino_idx:     # spelt so, or (no hanja known: 곤봉) fitting the readings well
        got = segment(forms[i], per_char, members[i]["lang"])
        if got and (i in spelt or got[0] / len(forms[i]) <= SEG_MAX):
            cuts[i] = got[1]
    cut_langs = {members[i]["lang"] for i in cuts}
    other_langs = {m["lang"] for i, m in enumerate(members) if i not in cuts} - cut_langs
    # a cluster that is mostly not Sino-xenic (emoji, tea) keeps the plain alignment
    if len(cut_langs) < 2 or len(other_langs) > len(cut_langs):
        return None
    extra_cuts = [segment(e, per_char, "glb") for e in extra]
    # each character's reading: the one closest to every member's piece
    chosen = []
    for c, rs in enumerate(per_char):
        pieces = [(members[i]["lang"], p[c]) for i, p in cuts.items()]
        chosen.append(min(rs, key=lambda r: sum(_syl(r, p, l)[0] for l, p in pieces)))
    center = "".join(chosen)
    sino = set(sino_idx)
    aligned = []
    for i, f in enumerate(forms):
        if i in cuts:
            aligned.append([pr for c, p in enumerate(cuts[i]) for pr in _syl(chosen[c], p, members[i]["lang"])[1]])
        elif i in sino:
            aligned.append(align(center, f, sub=sino_sub_cost, coda=_sino_coda, nasal_pos=NASAL_POS)[1])
        else:
            aligned.append(align(center, f)[1])
    for e, cut in zip(extra, extra_cuts):
        if cut:
            aligned.append([pr for c, p in enumerate(cut[1]) for pr in _syl(chosen[c], p, "glb")[1]])
        else:
            aligned.append(align(center, e, sub=sino_sub_cost)[1])
    return _merge(center, aligned)
