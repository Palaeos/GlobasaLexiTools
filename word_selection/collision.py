"""Collision and form checks for candidate roots (moved from globasa_collision_check.py,
plus the methodology's minimal-pair tiers).

Minimal-pair tiers ("Methodology for Lexical Development", Caveats):
  NEVER        v/w, s/z; m/n word-finally
  LAST_RESORT  +/- a consonant or vowel at the beginning/end of the word
               (vowels are also listed under 'whenever possible avoid')
  AVOID        l/r, b/p, f/p, c/j, c/x, h/r
  ANY          any other minimal pair ('whenever possible, avoid any minimal pair')
Letter names (ibe, ice, ...) collide by design and are excluded from all counts.
"""

import collections
import re
from functools import lru_cache

from . import lexicon

VOWELS = set("aeiou")
STOPS = set("pbtdkg")
FINAL_CODA = set("flmnrswxy")  # word-final position only
ONSET2 = set("""bl fl gl kl pl vl
br dr fr gr kr pr tr vr
bw cw dw fw gw hw jw kw lw mw nw pw rw sw tw vw xw zw
by cy dy fy gy hy jy ky ly my ny py ry sy ty vy xy zy""".split())
ILLEGAL_FINAL = set("bcdghjkptvz")
LETTER_NAMES = {"i" + c + "e" for c in "bcdfghjklmnprstvwxyz"}
AVOID_PAIRS = {frozenset(p) for p in ("lr", "bp", "fp", "cj", "cx", "hr")}
NEVER_PAIRS = {frozenset("vw"), frozenset("sz")}
EXTRA_PREFIXES = {"pos", "nen", "wal", "ri", "ru", "be", "du", "aw", "day", "lil", "semi", "mal",
                  "ton", "har", "se", "bon", "bur", "fin", "xor", "ja", "nil", "no"}
SEVERITY = ["CLEAR", "NOTE", "CAUTION", "WARN", "BLOCK"]


def phonotactics(w):
    """Violations of the documented rules (xwexi gramati/abece-ji-lafuzu).
    Syllable structure (C)(C)V(C); word-final coda restricted to f l m n r s w x y."""
    out = []
    if not re.fullmatch(r"[a-z]+", w):
        return ["non-alphabetic"]
    if "q" in w:
        out.append("letter q unused in Globasa")
    if not (set(w) & VOWELS):
        return out + ["no vowel"]
    if w[-1] not in VOWELS:
        if w[-1] not in FINAL_CODA:
            out.append(f"illegal word-final '{w[-1]}'")
        if len(w) > 1 and w[-2] not in VOWELS:
            out.append("final consonant cluster (coda is max 1)")
    m = re.match(r"^([^aeiou]+)", w)
    if m:
        o = m.group(1)
        if len(o) > 2:
            out.append(f"initial onset '{o}' too long (max 2)")
        elif len(o) == 2 and o not in ONSET2:
            out.append(f"onset '{o}' not a permitted cluster")
    for m in re.finditer(r"(?=[aeiou]([^aeiou]+)[aeiou])", w):
        run = m.group(1)
        if len(run) > 3:
            out.append(f"medial run '{run}' too long (max coda1+onset2)")
            continue
        ok = False
        for cut in (0, 1):
            coda, onset = run[:cut], run[cut:]
            if not onset or len(onset) > 2 or (len(onset) == 2 and onset not in ONSET2):
                continue
            if coda and coda in STOPS and onset[0] in STOPS:
                continue
            ok = True
            break
        if not ok:
            why = "stop+stop cluster" if (len(run) == 2 and run[0] in STOPS and run[1] in STOPS) \
                else "no legal coda/onset split"
            out.append(f"medial '{run}': {why}")
    for bad in ("iy", "iw", "uy", "uw"):
        if re.search(bad + r"(?![aeiou])", w):
            out.append(f"nucleus-coda '{bad}' not allowed")
    if re.search(r"iy[aeiou]", w):
        out.append("nucleus-onset 'iy' not allowed")
    if re.search(r"uw[aeiou]", w):
        out.append("nucleus-onset 'uw' not allowed")
    if "wu" in w:
        out.append("onset-nucleus 'wu' not allowed")
    if "yi" in w:
        out.append("onset-nucleus 'yi' not allowed")
    return out


def key(w):
    """Glide/vowel alternations: y->i, w->u (catches tyan~tian, kwa~kua)."""
    return w.replace("y", "i").replace("w", "u")


@lru_cache(maxsize=1)
def _lex():
    words = {w: v for w, v in lexicon.words().items() if w not in LETTER_NAMES and re.fullmatch(r"[a-z]+", w)}
    keys = collections.defaultdict(list)
    for w in words:
        keys[key(w)].append(w)
    roots = {r["word"].lower() for r in lexicon.roots() if re.fullmatch(r"[a-z]+", r["word"].lower())}
    pre, suf = lexicon.affixes()
    return words, keys, roots, set(pre) | EXTRA_PREFIXES, set(suf)


def gloss(w):
    v = _lex()[0].get(w)
    return (v["eng"] if v else "")[:70]


def edits1(w):
    a = "abcdefghijklmnoprstuvwxyz"
    s = {w[:i] + w[i + 1:] for i in range(len(w))}
    s |= {w[:i] + c + w[i + 1:] for i in range(len(w)) for c in a}
    s |= {w[:i] + c + w[i:] for i in range(len(w) + 1) for c in a}
    return s - {w}


def pair_tier(cand, other):
    """Tier of a minimal pair (cand and other differ by exactly one edit)."""
    if len(cand) == len(other):
        i = next(k for k in range(len(cand)) if cand[k] != other[k])
        p = frozenset((cand[i], other[i]))
        if p in NEVER_PAIRS:
            return "NEVER", f"{'/'.join(sorted(p))} contrast"
        if p == frozenset("mn") and i == len(cand) - 1:
            return "NEVER", "word-final m/n"
        if p in AVOID_PAIRS:
            return "AVOID", f"{'/'.join(sorted(p))} contrast"
        return "ANY", f"{cand[i]}/{other[i]}"
    longer, shorter = (cand, other) if len(cand) > len(other) else (other, cand)
    if longer[1:] == shorter or longer[:-1] == shorter:
        seg = longer[0] if longer[1:] == shorter else longer[-1]
        where = "beginning" if longer[1:] == shorter else "end"
        kind = "vowel" if seg in VOWELS else "consonant"
        return "LAST_RESORT", f"+/- {kind} '{seg}' at the {where}"
    return "ANY", "medial +/- segment"


TIER_SEVERITY = {"NEVER": "BLOCK", "LAST_RESORT": "WARN", "AVOID": "CAUTION", "ANY": "NOTE"}


def check(cand, exclude=()):
    """Full report for a candidate. `exclude`: words to ignore (leave-one-out eval)."""
    cand = cand.lower()
    words, keys, roots, prefixes, suffixes = _lex()
    ex = set(exclude)
    rep = {"candidate": cand, "exact": [], "homophone": [], "minimal_pairs": [],
           "misparse_existing": [], "self_decomposes": [], "phonotactics": phonotactics(cand)}
    if cand in words and cand not in ex:
        rep["exact"].append((cand, gloss(cand)))
    for w in keys.get(key(cand), []):
        if w != cand and w not in ex:
            rep["homophone"].append((w, gloss(w)))
    for e in edits1(cand):
        if e in words and e not in ex:
            tier, why = pair_tier(cand, e)
            rep["minimal_pairs"].append({"word": e, "gloss": gloss(e), "tier": tier, "why": why})
    seen = {m["word"] for m in rep["minimal_pairs"]} | {h[0] for h in rep["homophone"]}
    for e in edits1(key(cand)):
        for w in keys.get(e, []):
            if w != cand and w not in seen and w not in ex:
                seen.add(w)
                rep["minimal_pairs"].append({"word": w, "gloss": gloss(w), "tier": "ANY",
                                             "why": "near pair via y~i / w~u"})
    for w in words:
        if w != cand and w not in ex and w.startswith(cand) and len(w) > len(cand):
            rest = w[len(cand):]
            if rest in roots or rest in suffixes:
                rep["misparse_existing"].append((w, gloss(w), f"{cand}+{rest}"))
    for p in sorted(prefixes, key=len, reverse=True):
        rest = cand[len(p):]
        if cand.startswith(p) and len(rest) >= 2 and rest in roots and rest not in ex:
            rep["self_decomposes"].append(f"{p}- + {rest}")
    for s in sorted(suffixes, key=len, reverse=True):
        stem = cand[:-len(s)]
        if cand.endswith(s) and len(stem) >= 2 and stem in roots and stem not in ex:
            rep["self_decomposes"].append(f"{stem} + -{s}")
    rep["severity"] = severity(rep)
    return rep


def severity(rep):
    tiers = {m["tier"] for m in rep["minimal_pairs"]}
    if rep["exact"] or rep["phonotactics"] or "NEVER" in tiers:
        return "BLOCK"
    if rep["homophone"] or rep["misparse_existing"] or "LAST_RESORT" in tiers:
        return "WARN"
    if "AVOID" in tiers or rep["self_decomposes"]:
        return "CAUTION"
    if tiers:
        return "NOTE"
    return "CLEAR"


def adapt(w):
    """Documented repair for an illegal word-final consonant: append -u (East Asian rule).
    form_rules.a_priori_vowel picks -e/-i/-u by source family."""
    if not w or w[-1] in VOWELS:
        return None
    if w[-1] in FINAL_CODA and not (len(w) > 1 and w[-2] not in VOWELS):
        return None
    return w + "u"


def show(rep):
    c = rep["candidate"]
    print(f"\n=== {c}  [{rep['severity']}] ===")
    for lbl, k in [("EXACT COLLISION", "exact"), ("NEAR-HOMOPHONE", "homophone")]:
        for w, g in rep[k]:
            print(f"   {lbl}: {w} — {g}")
    for w, g, how in rep["misparse_existing"]:
        print(f"   MISPARSE: existing '{w}' ({g}) could read as {how}")
    for d in rep["self_decomposes"]:
        print(f"   DECOMPOSES: candidate itself reads as {d}")
    order = {"NEVER": 0, "LAST_RESORT": 1, "AVOID": 2, "ANY": 3}
    mp = sorted(rep["minimal_pairs"], key=lambda m: order[m["tier"]])
    for m in mp[:8]:
        print(f"   minimal pair [{m['tier']}] {m['word']} ({m['gloss'][:30]}) — {m['why']}")
    if len(mp) > 8:
        print(f"   …+{len(mp) - 8} more minimal pairs")
    if rep["phonotactics"]:
        print("   phonotactics: " + "; ".join(rep["phonotactics"]))
        sug = adapt(c)
        if sug:
            print(f"   SUGGEST: {sug}  (Globasa repairs illegal word-final consonants with -u)")
    if rep["severity"] == "CLEAR":
        print("   no collisions found")
