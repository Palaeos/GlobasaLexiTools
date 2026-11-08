"""Sinosphere support for Sino-xenic cognate detection (clustering only; nothing
here reaches proposals).

Han spellings decide first: Korean hanja and Vietnamese chữ Hán (from Wiktionary),
normalised with Japanese shinjitai -> kyūjitai and simplified -> traditional maps,
so 기질 (基質), 基质 and 基質 are recognisably one word. Middle Chinese (Baxter) and
Cantonese readings are the phonetic fallback pivots: both keep the MC stop codas
(-p/-t/-k), -m, and unpalatalised velars (基 kij / gei) that Mandarin lost.

  build()                one pass over the raw dump -> word_selection_cache/sinosphere.json
  han_spellings(lang, w) Han spellings of a word, normalised to traditional characters
  pivots(word)           Globasa-letter MC and Cantonese renderings of a Han-spelt word
"""

import json
import os
import re
import unicodedata
from functools import lru_cache

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUMP = "/media/paleos/Warehouse2/Language/raw-wiktextract-data.jsonl"
TABLE = os.path.join(ROOT, "word_selection_cache", "sinosphere.json")


def _is_han(c):
    return unicodedata.name(c, "").startswith(("CJK UNIFIED IDEOGRAPH", "CJK COMPATIBILITY IDEOGRAPH"))


def is_han_word(w):
    return bool(w) and all(_is_han(c) for c in w)


def _add(d, k, v):
    if v not in d.setdefault(k, []):
        d[k].append(v)


def _etym_sino(d, name, n):
    """Han spelling from a ko-etym-Sino / vi-etym-sino template: either the whole word
    in arg 1, or one character per odd-numbered arg (even args are glosses)."""
    out = []
    for t in d.get("etymology_templates", []) or []:
        if t.get("name") != name:
            continue
        args = t.get("args", {})
        whole = (args.get("1") or "").strip()
        if is_han_word(whole) and len(whole) == n:
            out.append(whole)
            continue
        chars = [(args.get(str(k)) or "").strip() for k in range(1, 2 * n, 2)]
        if all(len(c) == 1 and _is_han(c) for c in chars) and len(chars) == n:
            out.append("".join(chars))
    return out


def build(dump=DUMP, out=TABLE):
    """One pass over the dump:
      mc        zh char -> [Baxter MC readings]
      s2t       simplified char -> [traditional chars] (from the traditional entry's forms)
      j2t       shinjitai char -> [kyūjitai chars] (Japanese character entries)
      ko        Korean word -> [hanja spellings] (hanja forms / ko-etym-Sino)
      vi        Vietnamese word -> [chữ Hán spellings], from vi-etym-sino only: the
                entry's plain CJK forms mix in chữ Nôm spellings of native words"""
    mc, s2t, j2t, ko, vi = {}, {}, {}, {}, {}
    with open(dump, encoding="utf-8") as f:
        for line in f:
            if '"lang_code": "zh"' in line:
                if '"Middle-Chinese"' not in line:
                    continue
            elif '"lang_code": "ko"' in line:
                if '"hanja"' not in line:
                    continue
            elif '"lang_code": "ja"' in line:
                if "kyūjitai" not in line:
                    continue
            elif '"lang_code": "vi"' in line:
                if "vi-etym-sino" not in line:
                    continue
            else:
                continue
            d = json.loads(line)
            w, lc = d.get("word", ""), d.get("lang_code")
            forms = d.get("forms", []) or []
            if lc == "zh" and len(w) == 1:
                for snd in d.get("sounds", []) or []:
                    if "Middle-Chinese" in (snd.get("tags") or []) and snd.get("zh-pron"):
                        for r in re.split(r"[,/、]\s*", snd["zh-pron"]):
                            if r.strip():
                                _add(mc, w, r.strip())
                for fm in forms:
                    tags = (fm.get("tags") or []) + (fm.get("raw_tags") or [])
                    sc = fm.get("form", "")
                    if "Simplified-Chinese" in tags and len(sc) == 1 and sc != w:
                        _add(s2t, sc, w)
            elif lc == "ja" and len(w) == 1 and _is_han(w):
                for fm in forms:
                    k = fm.get("form", "")
                    if "kyūjitai" in (fm.get("tags") or []) and len(k) == 1 and k != w and _is_han(k):
                        _add(j2t, w, k)
            elif lc == "ko":
                hs = [fm.get("form", "") for fm in forms if "hanja" in (fm.get("tags") or [])]
                hs += [h.get("args", {}).get("hanja", "") for h in d.get("head_templates", []) or []]
                hs += _etym_sino(d, "ko-etym-Sino", len(w.replace(" ", "")))
                for h in hs:
                    h = h.strip()
                    if is_han_word(h) and len(h) == len(w.replace(" ", "")):
                        _add(ko, w, h)
            elif lc == "vi":
                for h in _etym_sino(d, "vi-etym-sino", len(w.split())):
                    _add(vi, w, h)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    data = {"mc": mc, "s2t": s2t, "j2t": j2t, "ko": ko, "vi": vi}
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    return {k: len(v) for k, v in data.items()}


@lru_cache(maxsize=1)
def table():
    try:
        with open(TABLE, encoding="utf-8") as f:
            t = json.load(f)
    except FileNotFoundError:
        t = {}
    for k in ("mc", "s2t", "j2t", "ko", "vi"):
        t.setdefault(k, {})
    return t


def _trad(c):
    """A character and its traditional counterparts."""
    t = table()
    return [c] + [x for x in t["s2t"].get(c, []) + t["j2t"].get(c, []) if x != c]


MAX_SPELLINGS = 8


def normalise(w, lang="cmn"):
    """Han spelling -> canonical traditional spellings (several when a character is
    ambiguous: shinjitai 弁 stands for 辨/辯/瓣). Japanese shinjitai map to kyūjitai; a
    simplified character maps to its traditional counterparts only if it has no
    readings of its own (面 is both a character and the simplification of 麵)."""
    t = table()
    combos = [""]
    for c in w:
        if lang == "ja" and c in t["j2t"]:
            alts = t["j2t"][c]
        elif lang in ("cmn", "ja") and c not in t["mc"] and c in t["s2t"]:
            alts = t["s2t"][c]
        else:
            alts = [c]
        combos = [x + y for x in combos for y in alts][:MAX_SPELLINGS]
    return combos


ON_MAX = 0.45     # an undocumented single-kanji reading counts as on'yomi within this of its pivots
# One on'yomi = one Middle Chinese syllable: onset, optional y, vowel, and at most one
# of -i/-u/-n/-ku/-ki/-tsu/-chi, or a geminate coda before the next syllable
# (gakkō, jissai). Globasa letters: shi=xi, chi=ci, j=dj.
ON_SYLLABLE = r"(?:ts|[kgsztdnhbpmyrwfjcxv])?y?[aeiou](?:[iu]|n(?![aeiouy])|ku|ki|tsu|ci|cu|k(?=k)|t(?=[tc])|s(?=s)|p(?=p))?"


def on_shaped(word, form):
    """Can `form` be read as one on'yomi syllable per character of `word`?"""
    return re.fullmatch(f"(?:{ON_SYLLABLE}){{{len(word)}}}", form) is not None
SINO_SRC = {"ltc", "och", "zh", "cmn", "yue", "lzh", "zhx-sic"}


@lru_cache(maxsize=20000)
def ja_reading_kind(word, form):
    """'native' (kun'yomi, inherited from Old Japanese), 'sino' (on'yomi) or 'unknown'
    for a Han-spelt Japanese word read as `form` (Globasa letters). The entry whose
    romanization gives `form` decides by its etymology; failing that, the reading
    must answer to the characters' Middle Chinese / Cantonese pivots.
    Documented etymology decides first (the reading's own entry; failing that, every
    documented entry of the word being inherited). Undocumented: the reading must
    split into one on'yomi syllable per character (on_shaped), and a single kanji must
    also answer to its MC / Cantonese pivots."""
    from . import translit
    from .align import sino_distance
    from .sources.wiktionary import index
    kinds, others, matched = set(), set(), False
    for e in index().entries("ja", word):
        fs = set()
        for r in [r for r in e["roman"] if r and r.isascii()][:3]:
            try:
                fs |= {f.replace(" ", "") for f, _ in translit.to_globasa("ja", word, r)}
            except Exception:
                pass
        matched |= form in fs
        target = kinds if form in fs else others
        for kind, src, _ in e["etym"]:
            if kind == "inh" and (src == "ojp" or src.startswith("jpx")):
                target.add("native")
            elif kind in ("bor", "der", "lbor") and src in SINO_SRC:
                target.add("sino")
    if "sino" in kinds:
        return "sino"
    if "native" in kinds or (others == {"native"} and not matched):
        return "native"
    if not on_shaped(word, form):
        return "native"
    if len(word) > 1:
        return "sino"
    piv = pivots(word)
    if not piv:
        return "unknown"
    near = min(sino_distance("ja", form, "zh-pivot", p) for p in piv) <= ON_MAX
    return "sino" if near else "native"


def han_spellings(lang, word, form=None):
    """Normalised Han spellings of a word: itself (cmn; ja unless `form` is a native
    reading), its hanja (ko) or chữ Hán (vi). Empty when none is known."""
    w = (word or "").strip()
    if lang == "ja" and form and is_han_word(w) and ja_reading_kind(w, form.replace(" ", "")) == "native":
        return []
    if lang in ("cmn", "ja"):
        hs = [w] if is_han_word(w) else []
    elif lang in ("ko", "vi"):
        hs = table()[lang].get(w, [])
    else:
        hs = []
    return list(dict.fromkeys(n for h in hs for n in normalise(h, lang)))


# Baxter (1992) ASCII -> Globasa letters. Initials first (longest match), then finals.
_INITIALS = [
    ("tsyh", "c"), ("dzy", "j"), ("tsy", "c"), ("tsrh", "c"), ("dzr", "j"), ("tsr", "c"),
    ("tsh", "ts"), ("dz", "dz"), ("ts", "ts"), ("sy", "x"), ("zy", "j"), ("sr", "x"), ("zr", "j"),
    ("trh", "t"), ("tr", "t"), ("dr", "d"), ("nr", "n"), ("ny", "n"), ("ng", "g"),
    ("kh", "k"), ("th", "t"), ("ph", "p"), ("x", "h"), ("h", "h"), ("'", ""),
]
_FINAL_RULES = [("ae", "a"), ("ea", "e"), ("+", "i"), ("ij", "i"), ("jw", "w"), ("j", "y"), ("ng", "ng")]


def baxter_to_globasa(r):
    r = r.strip().lower()
    r = re.sub(r"[xh]$", "", r) if len(r) > 2 else r   # tone letters X (rising), H (departing)
    ini = ""
    for a, b in _INITIALS:
        if r.startswith(a):
            ini, r = b, r[len(a):]
            break
    for a, b in _FINAL_RULES:
        r = r.replace(a, b)
    r = re.sub(r"^y(?=[iy])", "", r).replace("yy", "y")
    if ini in ("c", "j", "x"):        # palatal initials absorb the medial y
        r = re.sub(r"^y", "", r)
    return re.sub(r"[^a-z]", "", ini + r)


MAX_PIVOTS = 8


def _canto_readings(w):
    from .sources.wiktionary import index
    from .translit import ipa_to_globasa
    out = []
    for e in index().entries("zh", w):
        for ipa, tags in e["ipa"]:
            if "Cantonese" in tags:
                g = ipa_to_globasa(ipa).replace(" ", "")
                if g and g not in out:
                    out.append(g)
    return out


def _combine(per_char):
    """Concatenate per-character alternatives, capped at MAX_PIVOTS combinations."""
    combos = [""]
    for alts in per_char:
        if not alts:
            return []
        combos = [x + y for x in combos for y in alts[:3]][:MAX_PIVOTS]
    return combos


@lru_cache(maxsize=20000)
def pivots(word):
    """Pivot renderings of a wholly Han-spelt word: Middle Chinese (every reading of
    every character, capped) and Cantonese (the word's own entry, else per character).
    Empty for anything not spelt wholly in Han characters."""
    w = (word or "").strip()
    if not w or not all(_is_han(c) for c in w):
        return ()
    mc = table()["mc"]
    out = _combine([[baxter_to_globasa(r) for t in _trad(c) for r in mc.get(t, [])] for c in w])
    try:
        whole = _canto_readings(w)
        if not whole:
            trad = "".join(_trad(c)[-1] for c in w)
            whole = _canto_readings(trad) if trad != w else []
        out += whole or _combine([[g for t in _trad(c) for g in _canto_readings(t)] for c in w])
    except Exception:
        pass
    return tuple(dict.fromkeys(f for f in out if f))
