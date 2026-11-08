"""Arabic-script consonant skeletons, so Arabic and Persian words cluster by spelling.

A Persian loan from Arabic keeps the Arabic spelling while its pronunciation shifts
(ث/س/ص all s, ذ/ز/ض/ظ all z, ح/ه h, ع/ء silent, ق/غ gh, short vowels i->e, u->o), so
romanizations drift apart (عضلة hadala ~ عضله azole, عقيق hakik ~ عقیق agig) while
the skeleton stays put. Clustering joins words whose normalised skeletons match,
the abjad counterpart of joining Sinosphere words by Han spelling.
"""

import re

LANGS = {"ar", "fa"}
_MARKS = re.compile("[ً-ٰٟـۖ-ۭ‌‍\u200E\u200F]")
_LETTERS = str.maketrans({
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
    "ي": "ی", "ى": "ی", "ئ": "ی", "ك": "ک", "ؤ": "و", "ۀ": "ه",
})


def is_arabic_script(w):
    return bool(w) and all("؀" <= c <= "ۿ" or c in " ‌" or "ﭐ" <= c <= "﻿" for c in w)


def skeletons(lang, word):
    """Normalised skeletons of an Arabic or Persian word. Arabic final ة is written ه
    or ت in Persian (عضله, آفت), so it yields both."""
    w = (word or "").strip()
    if lang not in LANGS or not is_arabic_script(w):
        return []
    w = _MARKS.sub("", w).translate(_LETTERS)
    w = re.sub(r"\s+", " ", w).replace("ء", "")
    if not w:
        return []
    if "ة" in w:
        return list(dict.fromkeys([w.replace("ة", "ه"), w.replace("ة", "ت")]))
    return [w]


# ---------------------------------------------------------------------------
# Vocalization prediction: one language's romanization -> the other's reading
# ---------------------------------------------------------------------------
# Vowel length carries the correspondence: Arabic long ā ī ū are written (alef,
# ی, و) and keep their quality in Persian (â i u); unwritten short a i u become
# Persian a e o. Persian â i u are long, a e o short. Diphthongs: Arabic aw/ay ~
# Persian ow/ey. Long vowels are carried as capitals A I U through the alignment.

import unicodedata

# Consonant value of each letter in Globasa letters, per language (LexiliAsel
# conventions: Arabic ع h, ق k, ض d; Persian ع silent, ق/غ g, ض/ظ/ذ z, ث/ص s).
_COMMON = {"ب": "b", "پ": "p", "ت": "t", "ج": "j", "چ": "c", "ح": "h", "خ": "h", "د": "d",
           "ر": "r", "ز": "z", "ژ": "j", "س": "s", "ش": "x", "ط": "t", "ف": "f", "ک": "k",
           "گ": "g", "ل": "l", "م": "m", "ن": "n", "ه": "h", "غ": "g"}
CONS = {
    "ar": {**_COMMON, "ث": "t", "ذ": "z", "ص": "s", "ض": "d", "ظ": "z", "ع": "h", "ق": "k", "پ": "b", "و": "w", "ی": "y"},
    "fa": {**_COMMON, "ث": "s", "ذ": "z", "ص": "s", "ض": "z", "ظ": "z", "ع": "", "ق": "g", "و": "v", "ی": "y"},
}
# Long vowels a mater lectionis can write
MATRES = {"ا": "A", "و": "U", "ی": "I"}
# Persian diphthong reflexes written with و / ی (howz ~ Arabic hawd)
DIPH = {"fa": {"و": "o", "ی": "e"}, "ar": {}}
# Unwritten short vowels: Arabic i/u are Persian e/o
SHORT = {("ar", "fa"): {"a": "a", "i": "e", "u": "o", "e": "e", "o": "o"},
         ("fa", "ar"): {"a": "a", "e": "i", "o": "u", "i": "i", "u": "u"}}
_V = "aeiou"


def length_form(lang, roman):
    """A Wiktionary romanization -> Globasa letters with long vowels as A I U.
    Persian: prefer an Iranian romanization (â, e, o), where i u are long."""
    from . import translit
    r = unicodedata.normalize("NFC", (roman or "").strip().lower())
    if not r:
        return ""
    if lang == "fa":
        iranian = "â" in r or (re.search("[eo]", r) and not re.search("[āīū]", r))
        r = re.sub(r"ā(?=$| )", "e", r)
        r = r.replace("â", "A").replace("ā", "A").replace("ī", "I").replace("ū", "U")
        if iranian:
            r = re.sub(r"i(?![aeiouAIU])", "I", r)   # Iranian i, u are long (not as glides)
            r = re.sub(r"u(?![aeiouAIU])", "U", r)
        r = re.sub(r"ow(?![aeiouAIU])", "o", r)        # diphthongs: the reflex rides on و / ی
        r = re.sub(r"ey(?![aeiouAIU])", "e", r)
        rules = translit.PERSIAN
    else:
        r = r.replace("ā", "A").replace("ī", "I").replace("ū", "U").replace("ē", "I").replace("ō", "U")
        rules = translit.ARABIC
    out = translit.apply(rules, r)
    out = re.sub(r"[ʹʺ'’ʼʻʿʾʔˀ`´\-‐·.ˈˌ ]", "", out)
    out = unicodedata.normalize("NFD", out)
    out = "".join(c for c in out if not unicodedata.combining(c))
    return "".join(c for c in out if c in "abcdefghijklmnoprstuvwxyzAIU")


def _letters(lang, word):
    """Normalised letters of the word, keeping ة (the skeleton turns it into ه/ت)."""
    w = _MARKS.sub("", (word or "").strip()).translate(_LETTERS).replace("ء", "").replace(" ", "")
    return list(w)


def _realizations(lang, letter, first, last, lengthed):
    """(sound, kind) options for one letter: 'c' consonant, 'L' long vowel written
    by a mater, 'D' diphthong reflex, '0' silent (initial alef carrying a short
    vowel, Persian ع), 'F' feminine ending."""
    def vow(v):
        return v if lengthed else v.lower()
    if letter == "ة":
        return [("a", "F"), ("e", "F"), ("at", "F")]
    out = []
    if letter == "ا":
        out.append((vow("A"), "L"))
        if first:
            out.append(("", "0"))
        return out
    if letter in MATRES:
        out.append((vow(MATRES[letter]), "L"))
        if letter == "ی" and last:
            out.append((vow("A"), "L"))       # alif maqsura
    if letter in DIPH[lang]:
        out.append((DIPH[lang][letter], "D"))
    if letter == "ه" and last:
        out += [("e", "F"), ("a", "F")]
    c = CONS[lang].get(letter)
    if c is not None:
        out.append((c, "c" if c else "0"))
        if c:
            out.append((c + c, "c"))   # shadda / geminate
    return out


def parse(lang, word, form):
    """Align a romanized form (Globasa letters; long vowels A I U if known) to its
    script: per letter (letter, sound, kind, unwritten short vowel after it)."""
    L = _letters(lang, word)
    F = form.replace(" ", "")
    lengthed = any(c in "AIU" for c in F)
    n, m = len(L), len(F)
    best = {(0, 0): (0.0, None)}
    for i in range(n):
        for j in range(m + 1):
            if (i, j) not in best:
                continue
            cost0 = best[(i, j)][0]
            for snd, kind in _realizations(lang, L[i], i == 0, i == n - 1, lengthed):
                if F[j:j + len(snd)] != snd:
                    continue
                j2 = j + len(snd)
                for v in [""] + ([F[j2]] if j2 < m and F[j2] in _V else []):
                    j3 = j2 + len(v)
                    c = cost0 + (0.1 if v else 0) + (0.05 if kind in "LD" else 0)
                    if c < best.get((i + 1, j3), (float("inf"),))[0]:
                        best[(i + 1, j3)] = (c, (i, j, snd, kind, v))
    if (n, m) not in best:
        return None
    out, key = [], (n, m)
    while key != (0, 0):
        i, j, snd, kind, v = best[key][1]
        out.append((L[i], snd, kind, v))
        key = (i, j)
    return out[::-1]


def _predict_raw(src_lang, src_word, src_form, tgt_lang, tgt_word):
    """Prediction with geminates kept and Persian diphthong reflexes as placeholders:
    Ë = ey or i, Ö = o or u (Arabic ay/aw: Iranian ey/ow, or the old majhūl ē/ō,
    now i/u: hayl ~ hil, ḥawḍ ~ huz)."""
    p = parse(src_lang, src_word, src_form)
    T = _letters(tgt_lang, tgt_word)
    if p is None or len(T) != len(p):
        return None
    short = SHORT[(src_lang, tgt_lang)]
    out = []
    for k, ((sl, snd, kind, v), tl) in enumerate(zip(p, T)):
        nxt = p[k + 1] if k + 1 < len(p) else None
        vv = short.get(v, v)
        if tgt_lang == "fa" and v == "i" and nxt and nxt[0] == "ی" and nxt[2] == "c":
            vv = "i"                                # i stays i before a consonantal y (kimiya, imtiyaz)
        if kind == "F" or tl == "ة":              # ar -a ~ fa -e (ه) / -at (ت)
            s = {"ه": "e" if tgt_lang == "fa" else "a", "ت": "at", "ة": "a"}.get(tl, snd.lower())
        elif kind == "L":
            s = snd.lower()
        elif kind == "D":                          # Persian ow/ey -> Arabic aw/ay
            s = {"o": "w", "e": "y"}[snd]
            if out and out[-1].endswith(("o", "e")):
                out[-1] = out[-1][:-1] + "a"
            else:
                s = "a" + s
        elif kind == "0":
            s = "" if sl == "ا" else CONS[tgt_lang].get(tl, "")
        else:
            c = CONS[tgt_lang].get(tl, snd[:1])
            s = c * len(snd) if (c and len(snd) == 2) else c
            # Arabic consonantal w/y after short a before a consonant: a Persian diphthong
            if tgt_lang == "fa" and tl in ("و", "ی") and out and out[-1].endswith("a") \
                    and not v and (nxt is None or nxt[2] in "c0F"):
                out[-1] = out[-1][:-1] + ("Ö" if tl == "و" else "Ë")
                s = ""
        out.append(s + vv)
    res = "".join(out)
    if tgt_lang == "fa":
        res = re.sub(r"iy+$", "i", res)            # Arabic -iyy: Persian -i (kursiyy ~ korsi)
        res = re.sub(r"iy(?=[aeiou])", "i", res) if res.endswith("ya") else res
    return res


def _expand(raw):
    """All readings of a raw prediction, the usual one first: ey/ow before i/u, and
    geminates collapsed before kept (LexiliAsel keeps 38 of 1679 Persian geminates)."""
    import itertools
    opts = [{"Ë": ("ey", "i"), "Ö": ("o", "u")}.get(part, (part,)) for part in re.split("([ËÖ])", raw)]
    out = []
    for c in ("".join(x) for x in itertools.product(*opts)):
        for f in (re.sub(r"([bcdfghjklmnprstvxyz])\1", r"\1", c), c):
            if f not in out:
                out.append(f)
    return out


def predict(src_lang, src_word, src_form, tgt_lang, tgt_word):
    """The most likely reading of tgt_word (same skeleton) from src_word's
    romanization (length_form, or plain Globasa letters when length is unknown)."""
    raw = _predict_raw(src_lang, src_word, src_form, tgt_lang, tgt_word)
    return _expand(raw)[0] if raw else None


def predict_all(src_lang, src_word, romans, tgt_lang, tgt_word):
    """Readings of tgt_word predicted from each of src_word's romanizations, most
    likely first; an Arabic case ending (-un/-in/-an) is tried stripped too."""
    out = []
    for r in romans:
        lf = length_form(src_lang, r)
        if not lf:
            continue
        variants = [lf]
        if src_lang == "ar":
            variants.append(re.sub(r"(?<=[^aeiouAIU])[uia]n$", "", lf))
        for v in variants:
            raw = _predict_raw(src_lang, src_word, v, tgt_lang, tgt_word)
            for f in (_expand(raw) if raw else []):
                if f not in out:
                    out.append(f)
    return out


# ---------------------------------------------------------------------------
# Vocalization from a cognate in another script (Turkish akademi -> آکادمی)
# ---------------------------------------------------------------------------
# Most Arabic/Persian words with no romanization anywhere are loans whose cluster
# also holds a Latin-script (or romanized) cognate: Turkish, which spells its
# loans phonemically, or a European source. The script supplies the consonants;
# the cognate supplies the unwritten vowels and the quality of a mater (Persian
# و is o or u, ی is i or e). The fit cost is the cognate test.

# Vowels a script can leave unwritten, per language (Iranian Persian a e o;
# Arabic a i u), and how a cognate's other vowels map onto them
UNWRITTEN = {"fa": {"a": "a", "e": "e", "o": "o", "i": "e", "u": "o"},
             "ar": {"a": "a", "i": "i", "u": "u", "e": "i", "o": "u"}}
# Vowel qualities a mater may stand for in loans
MATER_VOWELS = {"fa": {"ا": ("a",), "و": ("u", "o"), "ی": ("i", "e")},
                "ar": {"ا": ("a",), "و": ("u",), "ی": ("i",)}}     # Arabic has no e, o
SKIP_PARTNER = 0.8      # a cognate consonant the script does not write
SKIP_LETTER = 1.0       # a written letter the cognate lacks
INSERT_VOWEL = 0.1      # an unwritten vowel taken from the cognate
# accepted cost per written letter. Leave-one-out on LexiliAsel etymons with a
# Wiktionary reading: 0.15 keeps 84% (fa) / 71% (ar) of true cognates while a
# random other root's words fit 0.1% / 0.0% of the time (0.35: 94/90% vs 6.7/5.0%)
FIT_MAX = 0.15


def _options(lang, letter, first, last, madda=False):
    """(sound to match, sound to output, cost) for one letter; madda: an initial
    آ, which is always â (the normalised letters write it ا)."""
    opts = []
    for snd, kind in _realizations(lang, letter, first, last, False):
        if madda and kind == "0":
            continue
        if kind == "F":                      # the ending is the language's own: fa ه -e, ar ة -a
            for v in ("a", "e"):
                opts.append((v, "e" if (lang == "fa" and letter == "ه") else "a" if letter == "ة" else snd, 0.0))
            continue
        if kind == "L" and letter in MATER_VOWELS[lang]:
            for k, v in enumerate(MATER_VOWELS[lang][letter]):
                opts.append((v, v, 0.05 * k))
        else:
            opts.append((snd, snd, 0.0))
    if letter == "ی":                                  # i plus glide (آکسیوم âksiyom)
        opts.append(("iy", "iy", 0.0))
    if letter in ("و", "ی"):                          # consonantal w/v, y
        opts.append(("w" if letter == "و" and lang == "ar" else ("v" if letter == "و" else "y"),) * 2 + (0.0,))
        if letter == "و":
            opts.append(("w", "v" if lang == "fa" else "w", 0.1))
    return list(dict.fromkeys(opts))


def vocalize_from(lang, word, partner_form):
    """Reading of an unvocalized Arabic/Persian word from a cognate's form in Globasa
    letters: (form, cost per written letter), or None if it does not fit (FIT_MAX)."""
    from .align import sub_cost
    L = _letters(lang, word)
    P = (partner_form or "").replace(" ", "")
    if not L or not P or lang not in UNWRITTEN:
        return None
    n, m = len(L), len(P)
    INF = float("inf")
    best = {(0, 0): (0.0, None)}
    unwritten = UNWRITTEN[lang]
    madda = _MARKS.sub("", word.strip()).startswith("آ")

    def relax(state, cost, back):
        if cost < best.get(state, (INF,))[0]:
            best[state] = (cost, back)

    for i in range(n + 1):
        for j in range(m + 1):
            if (i, j) not in best:
                continue
            c0 = best[(i, j)][0]
            if j < m:                                  # unwritten vowel / unwritten consonant
                if P[j] in _V:
                    # only between letters: a vowel-initial word starts with alef or
                    # ع, and a final vowel is always written (ه -e; Arabic case vowels drop)
                    if 0 < i < n:
                        relax((i, j + 1), c0 + INSERT_VOWEL, (i, j, unwritten[P[j]]))
                    else:
                        relax((i, j + 1), c0 + SKIP_PARTNER, (i, j, ""))
                else:
                    relax((i, j + 1), c0 + SKIP_PARTNER, (i, j, ""))
            if i == n:
                continue
            for match, out, extra in _options(lang, L[i], i == 0, i == n - 1, madda and i == 0):
                k = len(match)
                if k == 0:
                    relax((i + 1, j), c0 + extra, (i, j, ""))
                    continue
                if j + k > m:
                    continue
                seg = P[j:j + k]
                sc = sum(0 if a == b else (sub_cost(a, b) if (a in _V) == (b in _V) else 1.0)
                         for a, b in zip(match, seg))
                if sc <= 0.6:
                    relax((i + 1, j + k), c0 + sc + extra, (i, j, out))
            # a written letter the cognate lacks: keep its sound
            snd = next((s for s, _k in _realizations(lang, L[i], i == 0, i == n - 1, False) if _k == "c"), "")
            relax((i + 1, j), c0 + SKIP_LETTER, (i, j, snd))
    if (n, m) not in best:
        return None
    cost = best[(n, m)][0] / n
    if cost > FIT_MAX:
        return None
    out, key = [], (n, m)
    while key != (0, 0):
        i, j, s = best[key][1]
        out.append(s)
        key = (i, j)
    form = "".join(out[::-1])
    form = re.sub(r"([bcdfghjklmnprstvxyz])\1", r"\1", form)
    return form, round(cost, 3)


EUROPEAN = ("fr", "en", "es", "de", "ru")
COGNATE_LANGS = ("tr",) + EUROPEAN + ("hi", "id", "sw")


def vocalize_from_cognates(lang, word, partners):
    """Best reading of an unvocalized ar/fa word from cognates [(code, form)]:
    (form, cost, code) or None. A European fit marks a European loan, read from
    Turkish (whose spelling of such loans is phonemic) or the European form;
    otherwise Turkish is passed over (its vowel harmony: edeb, elmas for adab,
    almas). Held out on 950 fa / 843 ar etymons with a Wiktionary reading
    (FIT_MAX 0.35): 52.7% / 51.9% exact, 83.9% / 78.8% within one edit."""
    fits = []
    for code, form in partners:
        if code not in COGNATE_LANGS or not form:
            continue
        got = vocalize_from(lang, word, form)
        if got:
            fits.append((got[1], got[0], code))
    if not fits:
        return None
    if any(c in EUROPEAN for _, _, c in fits):
        pool = [x for x in fits if x[2] in EUROPEAN + ("tr",)]
        best = min(pool, key=lambda x: x[0] - (0.02 if x[2] == "tr" else 0))
    else:
        best = min([x for x in fits if x[2] != "tr"] or fits)
    return best[1], best[0], best[2]
