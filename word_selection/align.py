"""Weighted alignment of Globasa-letter forms.

Substitution costs come from phonetic classes (place, manner, voicing for
consonants; height/backness for vowels; vowel~glide), with the pairs that
`lesson_audio_labels.NEAR` found to blur in recordings made cheap too.
Gaps are cheaper at word edges (a-posteriori/a-priori vowels, initial e-).
"""

import re
from functools import lru_cache

VOWELS = set("aeiou")
# consonant: (place, manner, voiced)
CONS = {
    "p": ("lab", "stop", 0), "b": ("lab", "stop", 1), "m": ("lab", "nas", 1),
    "f": ("lab", "fric", 0), "v": ("lab", "fric", 1), "w": ("lab", "glide", 1),
    "t": ("alv", "stop", 0), "d": ("alv", "stop", 1), "n": ("alv", "nas", 1),
    "s": ("alv", "fric", 0), "z": ("alv", "fric", 1), "l": ("alv", "liq", 1),
    "r": ("alv", "liq", 1), "c": ("pal", "affr", 0), "j": ("pal", "affr", 1),
    "x": ("pal", "fric", 0), "y": ("pal", "glide", 1), "k": ("vel", "stop", 0),
    "g": ("vel", "stop", 1), "h": ("glot", "fric", 0),
}
VOWEL_COST = {
    frozenset("ae"): 0.3, frozenset("ei"): 0.3, frozenset("ou"): 0.3, frozenset("ao"): 0.4,
    frozenset("eo"): 0.45, frozenset("ai"): 0.5, frozenset("iu"): 0.5, frozenset("au"): 0.5,
    frozenset("eu"): 0.5, frozenset("io"): 0.55,
}
NEAR = {frozenset(p) for p in ("uw", "iy", "sx", "cx", "bv", "lr", "kg", "kh", "fp", "cs", "jz", "jy")}
GAP, EDGE_GAP = 0.6, 0.4
_GLIDES = set("yw")


@lru_cache(maxsize=None)
def sub_cost(a, b):
    if a == b:
        return 0.0
    pair = frozenset((a, b))
    if a in VOWELS and b in VOWELS:
        return VOWEL_COST.get(pair, 0.5)
    if pair in (frozenset("iy"), frozenset("uw")):
        return 0.2
    if a in CONS and b in CONS:
        pa, ma, va = CONS[a]
        pb, mb, vb = CONS[b]
        c = 0.3 * (pa != pb) + 0.3 * (ma != mb) + 0.15 * (va != vb)
        if pair in NEAR:
            c = min(c, 0.35)
        return min(max(c, 0.15), 0.9)
    return 1.0  # vowel vs consonant, or unknown symbol


# ---- Sino-xenic correspondences (between cmn / ja / ko / vi only) ----------
# Middle Chinese initials as they surface in the four readings: velars palatalised
# in Mandarin (基 ki/gi ~ jī), the sibilant series (質 shitsu/jil ~ zhì), labials
# (Mandarin f ~ Japanese h ~ Korean b/p), MC ny- (Mandarin r ~ Japanese j/n), -m ~ -n.
SINO_COST = {frozenset(p): c for p, c in (
    ("kg", 0.15), ("kh", 0.15), ("gh", 0.15),
    ("kj", 0.2), ("gj", 0.2), ("kc", 0.2), ("gc", 0.2), ("hx", 0.2),
    ("sj", 0.2), ("xj", 0.2), ("sc", 0.2), ("xc", 0.2), ("jz", 0.2), ("sx", 0.15), ("cj", 0.2),
    ("fh", 0.2), ("fb", 0.2), ("fp", 0.2), ("hp", 0.2), ("hb", 0.2),
    ("rj", 0.2), ("mn", 0.2),
    ("ct", 0.2), ("jd", 0.2),
    ("wg", 0.3))}   # MC ng- before u: Mandarin w- (悟 wù) ~ Japanese g- (go)   # palatalised MC dentals: Korean 체 / 전 ~ Japanese tai / den
SINO_FAR = {frozenset("xy"): 0.8}   # palatal glide vs sh: no MC initial gives both
# MC -n stays a coda in every reading and -ng becomes a Japanese long vowel, so a
# nasal coda never answers to the onset nasal of a following syllable (山 shān is
# san, not yama)
NASAL_POS = 0.3
CODA_GAP = 0.25   # MC -p/-t/-k (lost in Mandarin), and the g of -ng (Mandarin -n ~ -ng)
CONS_RE = "[^aeiouy]"


@lru_cache(maxsize=None)
def sino_sub_cost(a, b):
    if frozenset((a, b)) in SINO_FAR:
        return SINO_FAR[frozenset((a, b))]
    c = sub_cost(a, b)
    return min(c, SINO_COST.get(frozenset((a, b)), c))


def _sino_coda(s, k):
    """Is s[k] a coda consonant that a Sino-xenic reading may lack?"""
    nxt = s[k + 1] if k + 1 < len(s) else ""
    if nxt and nxt in "aeiouy":
        return False
    return s[k] in "tkp" or (s[k] == "g" and k and s[k - 1] == "n")


MAX_VARIANTS = 16
# Each rule undoes one reading-specific sound change; every occurrence is optional
# (the form alone cannot tell 基 ki, a whole syllable, from 石 seki, an old -k).
SINO_RULES = {
    "ja": [  # epenthetic vowels after MC -t / -k
        (re.compile(rf"(?:tsu|ci|cu)(?={CONS_RE}|$)"), "t"),
        (re.compile(rf"k[iu](?={CONS_RE}|$)"), "k"),
    ],
    "ko": [  # MC -t as -l; nasal assimilation (측면 cheungmyeon, 향신료 -sillyo)
        (re.compile(rf"l(?={CONS_RE}|$)"), "t"),
        (re.compile(r"ng(?=[mn])"), "k"),
        (re.compile(r"m(?=[mn])"), "p"),
        (re.compile(r"n(?=[mn])"), "t"),
        (re.compile(r"ll"), "nl"),
    ],
    "vi": [  # ng- for MC ng- (Japanese g-); o as the glide of oa/oe (góa ~ 寡 kwa)
        (re.compile(r"ng(?=[aeiou])"), "g"),
        (re.compile(r"o(?=[ae])"), "w"),
    ],
}
TENSE = re.compile(r"(jj|kk|ss|tt|pp|cc)")   # Korean tensing; Japanese geminates


def _variants(f, rules):
    out = {f}
    for rx, rep in rules:
        nxt = set()
        for v in out:
            nxt.add(v)
            nxt.add(rx.sub(rep, v))
            for m in rx.finditer(v):     # also each occurrence on its own
                nxt.add(v[:m.start()] + rep + v[m.end():])
        out = set(sorted(nxt, key=len)[:MAX_VARIANTS])
    return out


def sino_norm(lang, f):
    """Variants of a form with reading-specific sound changes undone (SINO_RULES)."""
    f = f.replace(" ", "")
    if lang in ("ja", "ko"):
        f = TENSE.sub(lambda m: m.group(1)[0], f)
    return _variants(f, SINO_RULES.get(lang, []))


# MC -ng against Japanese: kept as -ng in Mandarin, Korean, Vietnamese (and the
# MC / Cantonese pivots), it is a long vowel in Japanese (空 kōng ~ kū, 東 dōng ~ tō,
# 生 shēng ~ sei), which romanizations without length write as an open syllable
# (孫悟空 Sūn Wùkōng ~ Son Gokū ~ "songoku")
NG_VS_JA = [(re.compile(rf"ng(?={CONS_RE}|$)"), ""), (re.compile(rf"ng(?={CONS_RE}|$)"), "u")]
JA_LONG = [(re.compile(r"(?<=[ou])u|(?<=e)i|(?<=o)o"), "ng")]


def sino_distance(lang_a, a, lang_b, b):
    """Normalised distance under Sino-xenic correspondences (best coda variant)."""
    va, vb = sino_norm(lang_a, a), sino_norm(lang_b, b)
    if (lang_a == "ja") != (lang_b == "ja"):
        if lang_a == "ja":
            va = {w for v in va for w in _variants(v, JA_LONG)}
            vb = {w for v in vb for w in _variants(v, NG_VS_JA)}
        else:
            va = {w for v in va for w in _variants(v, NG_VS_JA)}
            vb = {w for v in vb for w in _variants(v, JA_LONG)}
    return min(align(x, y, sub=sino_sub_cost, coda=_sino_coda, nasal_pos=NASAL_POS)[0] / max(len(x), len(y), 1)
               for x in va for y in vb)


def _positions(s):
    """Per letter: 'c' coda (before a consonant or at the end), 'o' onset (before a
    vowel), '?' ambiguous (before a glide: Mandarin sun|wu vs nwan), '' vowel."""
    out = []
    for k, ch in enumerate(s):
        nxt = s[k + 1] if k + 1 < len(s) else ""
        if ch in VOWELS:
            out.append("")
        elif not nxt or (nxt not in VOWELS and nxt not in _GLIDES):
            out.append("c")
        elif nxt in _GLIDES:
            out.append("?")
        else:
            out.append("o")
    return out


def align(a, b, sub=None, coda=None, nasal_pos=0.0):
    """Global alignment. Returns (cost, [(x, y), ...]) with '-' for gaps.
    sub: substitution cost (default sub_cost); coda(s, k): if true, deleting s[k]
    costs at most CODA_GAP."""
    sub = sub or sub_cost
    n, m = len(a), len(b)
    pa, pb = _positions(a), _positions(b)

    D = [[0.0] * (m + 1) for _ in range(n + 1)]
    P = [[None] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        D[i][0] = D[i - 1][0] + EDGE_GAP
        P[i][0] = "u"
    for j in range(1, m + 1):
        D[0][j] = D[0][j - 1] + EDGE_GAP
        P[0][j] = "l"
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            c = sub(a[i - 1], b[j - 1])
            if nasal_pos and a[i - 1] in "mn" and b[j - 1] in "mn" and {pa[i - 1], pb[j - 1]} == {"c", "o"}:
                c += nasal_pos
            best, op = D[i - 1][j - 1] + c, "d"
            gu = EDGE_GAP if j in (0, m) else GAP
            gl = EDGE_GAP if i in (0, n) else GAP
            if coda:
                gu = min(gu, CODA_GAP) if coda(a, i - 1) else gu
                gl = min(gl, CODA_GAP) if coda(b, j - 1) else gl
            up = D[i - 1][j] + gu
            left = D[i][j - 1] + gl
            if up < best:
                best, op = up, "u"
            if left < best:
                best, op = left, "l"
            D[i][j], P[i][j] = best, op
    pairs, i, j = [], n, m
    while i or j:
        op = P[i][j]
        if op == "d":
            pairs.append((a[i - 1], b[j - 1])); i -= 1; j -= 1
        elif op == "u":
            pairs.append((a[i - 1], "-")); i -= 1
        else:
            pairs.append(("-", b[j - 1])); j -= 1
    return D[n][m], pairs[::-1]


def distance(a, b, normalized=False):
    a, b = a.replace(" ", ""), b.replace(" ", "")
    c = align(a, b)[0]
    return c / max(len(a), len(b), 1) if normalized else c


def edit_count(a, b):
    """Plain phoneme edits (for the methodology's 'differ by <=1/2 phonemes')
    and whether all substitutions are 'close' (cost <= 0.35)."""
    _, pairs = align(a, b)
    edits = [(x, y) for x, y in pairs if x != y]
    close = all(x != "-" and y != "-" and sub_cost(x, y) <= 0.35 for x, y in edits)
    return len(edits), close


def msa(forms):
    """Center-star multiple alignment. Returns (center_index, rows) where rows
    are equal-length lists of letters/'-' in input order."""
    forms = [f.replace(" ", "") for f in forms]
    if len(forms) == 1:
        return 0, [list(forms[0])]
    sums = [sum(distance(f, g) for g in forms) for f in forms]
    c = min(range(len(forms)), key=sums.__getitem__)
    center = forms[c]
    # master gap profile: gaps[k] = number of insert columns before center[k] (k == len -> end)
    gaps = [0] * (len(center) + 1)
    aligned = []
    for f in forms:
        _, pairs = align(center, f)
        ins, k = [0] * (len(center) + 1), 0
        for x, y in pairs:
            if x == "-":
                ins[k] += 1
            else:
                k += 1
        gaps = [max(g, x) for g, x in zip(gaps, ins)]
        aligned.append(pairs)
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
    return c, rows
