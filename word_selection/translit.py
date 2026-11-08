"""Source word -> Globasa-letter rendering, per language.

`to_globasa(lang, word, roman="", ipa="")` returns a list of renderings (most
trusted first). Non-Latin scripts use the romanization (Wiktionary's own, else
a library: pypinyin, cutlet, korean_romanizer); English and French prefer IPA,
with a spelling-based rendering kept as an alternative, as the methodology
favours spelling for some European features.

The target is the semi-phonetic style of the LexiliAsel romanizations
(e.g. Rusisa "frustratsiya", Putunhwa "dwey lyow", Koreasa "dokyumantu"), which
`word_selection_eval.py translit` measures against.

Engine: each language is an ordered list of (regex, replacement) rules. At each
position the first rule whose regex matches (anchored there, lookbehind sees the
whole string) consumes its match, so outputs are never re-rewritten.
"""

import re
import unicodedata

ALPHABET = set("abcdefghijklmnoprstuvwxyz ")


def rules(*pairs):
    return [(re.compile(p), r) for p, r in pairs]


def apply(rule_list, s):
    out, i = [], 0
    while i < len(s):
        for rx, rep in rule_list:
            m = rx.match(s, i)
            if m and m.end() > i:
                out.append(m.expand(rep) if "\\" in rep else rep)
                i = m.end()
                break
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


def strip_marks(s, keep=""):
    """Remove combining marks except those listed in `keep` (as combining chars)."""
    d = unicodedata.normalize("NFD", s)
    d = "".join(c for c in d if not unicodedata.combining(c) or c in keep)
    return unicodedata.normalize("NFC", d)


_APOS = re.compile(r"[ʹʺ'’ʼʻʿʾʔˀ`´\-‐·.ˈˌ]")


def clean(s):
    """Final pass: lowercase, drop marks/apostrophes, keep Globasa letters + spaces."""
    s = _APOS.sub("", s.lower())
    s = strip_marks(s)
    s = s.replace("q", "k").replace("ß", "s").replace("ø", "o").replace("æ", "e").replace("œ", "e")
    s = "".join(c for c in s if c in ALPHABET)
    s = re.sub(r"(.)\1\1+", r"\1\1", s)
    return re.sub(r"\s+", " ", s).strip()


V = "aeiouâêôơưăyáàảãạéèẻẽẹíìỉĩịóòỏõọúùủũụ"   # vowel class used in lookarounds

# ---------------------------------------------------------------------------
# Rule tables
# ---------------------------------------------------------------------------

RU = rules(  # Wiktionary scientific-style romanization, stress marks removed first
    ("šč", "xc"), ("šč", "xc"), ("č", "c"), ("š", "x"), ("ž", "j"), ("x", "h"),
    ("c", "ts"), ("ë", "yo"), ("ju", "yu"), ("ja", "ya"), ("je", "ye"), ("jo", "yo"),
    ("j", "y"), ("y", "i"), ("[ʹʺ]", ""),
)

PINYIN = rules(  # tone marks removed first; ü kept as 'ü'
    ("zh", "j"), ("ch", "c"), ("sh", "x"), ("z", "dz"), ("c", "ts"), ("q", "c"),
    ("yi", "i"), ("wu", "u"), ("you", "yow"), ("yu", "yu"), ("ye", "ye"),
    ("iang", "yang"), ("iong", "yong"), ("uang", "wang"), ("ueng", "weng"),
    ("ian", "yen"), ("iao", "yaw"), ("iu", "yow"), ("ie", "ye"), ("ia", "ya"),
    ("uai", "way"), ("uan", "wan"), ("uo", "wo"), ("ua", "wa"), ("ui", "wey"),
    ("ai", "ay"), ("ei", "ey"), ("ao", "aw"), ("ou", "ow"),
    ("eng", "ong"), ("er(?![" + V + "])", "ar"),
    ("(?<![" + V + "])e(?!n|[" + V + "])", "o"),
    ("ü", "yu"),
)

HEPBURN = rules(  # macrons removed first
    ("ei", "e"), ("ou", "o"), ("sh", "x"), ("tch", "c"), ("ch", "c"),
    ("([bcdfghjkmprstz])(?=\\1)", ""),
    ("n'", "n"),
)

KOREAN = rules(  # Revised Romanization
    ("eo", "a"), ("eu", "u"), ("wae", "we"), ("oe", "we"), ("ae", "e"), ("ui", "ui"),
    ("ch", "c"), ("kk", "k"), ("tt", "t"), ("pp", "p"), ("jj", "j"),
)

VIET = rules(  # tones removed first, quality marks (â ă ê ô ơ ư đ) kept; LexiliAsel conventions
    ("ngh", "ng"), ("nh", "n"), ("ph", "f"), ("th", "t"), ("tr", "c"), ("ch", "c"), ("kh", "h"),
    ("gh", "g"), ("gi(?=[" + V + "])", "z"), ("gi", "zi"), ("qu", "kw"), ("đ", "d"), ("d", "z"),
    ("r", "z"), ("x", "s"), ("s", "x"), ("c", "k"), ("q", "k"),
    ("ươ", "ue"), ("iêu", "iu"), ("yêu", "iew"), ("iê", "ie"), ("yê", "ye"), ("uô", "uo"),
    ("uâ", "we"), ("oa", "oe"), ("uy", "wi"), ("âu", "ew"), ("ây", "ey"), ("ao", "au"),
    ("eo", "eu"), ("ưu", "uw"), ("ơ", "e"), ("â", "e"), ("ư", "u"), ("ô", "o"), ("ê", "e"),
    ("ă", "a"), ("ay", "ai"), ("y", "i"),
)

INDIC = rules(  # Wiktionary Hindi / Telugu romanization (IAST-like)
    ("kh", "k"), ("gh", "g"), ("ch", "c"), ("jh", "j"), ("ṭh", "t"), ("ḍh", "d"),
    ("th", "t"), ("dh", "d"), ("ph", "f"), ("bh", "b"), ("ṛh", "r"), ("q", "k"),
    ("ḵh", "h"), ("x", "h"), ("ġ", "g"), ("[śṣ]", "x"), ("ai", "e"), ("au", "o"),
    ("[ṅñṇṃṁ]", "n"), ("[ṛṟ]", "r"), ("ḻ", "l"), ("ŕ", "r"),
)

ARABIC = rules(  # Wiktionary Arabic romanization (LexiliAsel: ʕ -> h, ō -> u, ē -> i, p -> b)
    ("ʔ|ʾ|'", ""), ("[ʕʿ]", "h"), ("ō", "u"), ("ē", "i"), ("p", "b"), ("aw(?![" + V + "])", "aw"), ("[ḥh]", "h"), ("[ḵx]", "h"), ("kh", "h"),
    ("š", "x"), ("sh", "x"), ("ṯ", "t"), ("ḏ", "d"), ("ṣ", "s"), ("ḍ", "d"), ("ṭ", "t"),
    ("ẓ", "z"), ("[ğġḡ]", "g"), ("gh", "g"), ("q", "k"), ("ŷ", "y"),
)

PERSIAN = rules(  # Wiktionary Persian romanization (Iranian reading: ow -> o, w -> v, final -a -> -e)
    ("[ʔʕʿʾ']", ""), ("â", "a"), ("ā(?=$| )", "e"), ("ā", "a"), ("ō", "u"), ("ē", "i"), ("ī", "i"), ("ū", "u"),
    ("ow(?![" + V + "])", "o"), ("w", "v"), ("iy(?=[" + V + "])", "i"),
    ("š", "x"), ("sh", "x"), ("č", "c"), ("ch", "c"), ("ž", "j"), ("zh", "j"),
    ("[xḵ]", "h"), ("kh", "h"), ("[ğġq]", "g"), ("gh", "g"),
)

TURKISH = rules(
    ("c", "j"), ("ç", "c"), ("ş", "x"), ("(?<=[" + V + "ıöü])ğ(?=[" + V + "ıöü])", ""), ("ğ", ""),
    ("ı", "i"), ("ö", "o"), ("ü", "u"),
)

SPANISH = rules(
    ("ch", "c"), ("ll", "y"), ("ñ", "ny"), ("qu", "k"), ("gu(?=[eiéí])", "g"), ("gü", "gw"),
    ("g(?=[eiéí])", "h"), ("j", "h"), ("c(?=[eiéí])", "s"), ("c", "k"), ("z", "s"),
    ("h", ""), ("x", "ks"), ("y(?![" + V + "])", "i"),
)

GERMAN = rules(
    ("tsch", "c"), ("dsch", "j"), ("sch", "x"), ("^sp", "xp"), ("^st", "xt"),
    ("(?<=[aou])ch", "h"), ("ch", "h"), ("chs", "ks"), ("ck", "k"), ("ph", "f"), ("th", "t"),
    ("tz", "ts"), ("z", "ts"), ("qu", "kv"), ("ei", "ay"), ("ai", "ay"), ("eu", "oy"), ("äu", "oy"),
    ("ie", "i"), ("(?<=[" + V + "äöü])h", ""), ("ä", "e"), ("ö", "o"), ("ü", "u"),
    ("ß", "s"), ("j", "y"), ("w", "v"), ("v", "f"), ("y", "u"),
)

FRENCH = rules(
    ("eaux?$", "o"), ("eau", "o"), ("aux?$", "o"), ("au", "o"), ("oi", "wa"), ("oî", "wa"),
    ("ou", "u"), ("où", "u"), ("ai", "e"), ("ei", "e"), ("tion", "syon"),
    ("(?<=[" + V + "])ill", "y"), ("ill", "iy"), ("gn", "ny"), ("ch", "x"), ("ph", "f"),
    ("th", "t"), ("qu", "k"), ("gu(?=[eiéèê])", "g"), ("g(?=[eiyéèê])", "j"),
    ("c(?=[eiyéèê])", "s"), ("ç", "s"), ("c", "k"), ("er$", "e"), ("ez$", "e"),
    ("[stdxzp]$", ""), ("es$", ""), ("e$", ""), ("[éèêë]", "e"), ("[âà]", "a"),
    ("[îï]", "i"), ("[ûü]", "u"), ("ô", "o"), ("h", ""), ("y", "i"), ("x", "ks"),
)

ENGLISH_SPELL = rules(
    ("tion$", "xon"), ("sion$", "jon"), ("sh", "x"), ("tch", "c"), ("ch", "c"), ("th", "t"),
    ("ph", "f"), ("ck", "k"), ("qu", "kw"), ("dge", "j"), ("ee", "i"), ("ea", "i"),
    ("oo", "u"), ("ou", "aw"), ("ow$", "o"), ("ai", "ey"), ("ay", "ey"), ("oa", "o"),
    ("g(?=[eiy])", "j"), ("c(?=[eiy])", "s"), ("c", "k"), ("x", "ks"),
    ("y$", "i"), ("(?<=[^" + V + "])e$", ""), ("wh", "w"),
)

SWAHILI = rules(
    ("ch", "c"), ("sh", "x"), ("ng'", "ng"), ("dh", "z"), ("th", "t"), ("gh", "g"), ("kh", "h"),
)

INDONESIAN = rules(
    ("sy", "x"), ("kh", "h"), ("ai(?![" + V + "])", "ay"), ("au(?![" + V + "])", "aw"),
    ("oi(?![" + V + "])", "oy"), ("x", "ks"),
)

IPA = rules(
    ("t͡ʃ|tʃ|ʧ", "c"), ("d͡ʒ|dʒ|ʤ", "j"), ("t͡s|ts", "ts"), ("ʃ|ɕ|ʂ", "x"), ("ʒ|ʑ|ʐ", "j"),
    ("θ", "t"), ("ð", "d"), ("ŋ", "ng"), ("ɲ", "ny"), ("j", "y"), ("[ɹɾʁʀɻr]", "r"),
    ("[xχħ]", "h"), ("ɡ", "g"), ("ɫ|ɬ", "l"), ("ʋ", "v"), ("ɸ", "f"), ("β", "b"),
    ("eɪ|ei", "ey"), ("aɪ|ai", "ay"), ("ɔɪ|oi", "oy"), ("aʊ|au", "aw"), ("oʊ|əʊ|ou", "o"),
    ("ɜː?ɹ?|ɝ|ɚ", "er"), ("iː|ɪ|i", "i"), ("uː|ʊ|u|ʉ", "u"), ("ɑː?|æ|a|ɐ|ʌ", "a"),
    ("ɒ|ɔː?|o", "o"), ("ɛ|e|œ|ø", "e"), ("ə", "a"), ("ɨ|ɯ", "i"), ("y", "u"), ("ɥ", "w"),
    ("[ːˑˈˌ.\\u0303\\u0329\\u032f\\u02b0\\u02b2]", ""), ("ʔ", ""),
)


# Vocalised Arabic script -> Globasa letters (preferred over a looked-up
# romanization, which may belong to a different entry of the same spelling).
AR_CONS = {"ب": "b", "ت": "t", "ث": "s", "ج": "j", "ح": "h", "خ": "h", "د": "d", "ذ": "z", "ر": "r",
           "ز": "z", "س": "s", "ش": "x", "ص": "s", "ض": "d", "ط": "t", "ظ": "z", "ع": "h", "غ": "g",
           "ف": "f", "ق": "k", "ك": "k", "ک": "k", "ل": "l", "م": "m", "ن": "n", "ه": "h", "ة": "a",
           "پ": "b", "گ": "g", "چ": "c", "ژ": "j", "ڤ": "v"}
AR_MARKS = {"\u064e": "a", "\u0650": "i", "\u064f": "u", "\u0670": "a"}
AR_SILENT = set("\u0652\u0651\u064b\u064c\u064d\u0640ءئؤ")
AR_VOWELS_MARKED = re.compile("[\u064e\u064f\u0650]")


def arabic_script(word):
    """Only for vocalised words; returns '' if the word carries no short-vowel marks."""
    if not AR_VOWELS_MARKED.search(word):
        return ""
    out = []
    chars = list(word)
    for i, ch in enumerate(chars):
        prev = out[-1] if out else ""
        nxt = chars[i + 1] if i + 1 < len(chars) else ""
        if ch == "ة":
            if not prev or prev[-1] != "a":
                out.append("a")
        elif ch in AR_CONS:
            out.append(AR_CONS[ch])
        elif ch in AR_MARKS:
            out.append(AR_MARKS[ch])
        elif ch in AR_SILENT:
            continue
        elif ch in "اأإآى":
            if nxt in AR_MARKS and ch != "آ":
                continue           # the vowel mark on the alif supplies the vowel
            if ch == "إ":
                out.append("i")
            elif not prev or prev[-1] not in "aiu" or ch == "آ":
                out.append("a")
        elif ch in "وي":
            glide = "w" if ch == "و" else "y"
            vowel = "u" if ch == "و" else "i"
            if nxt in AR_MARKS or nxt == "\u0651":
                out.append(glide)
            elif prev and prev[-1] == vowel:
                continue
            elif prev and prev[-1] == "a":
                out.append(glide)
            else:
                out.append(vowel)
        elif ch == " ":
            out.append(" ")
    s = re.sub(r"([bcdfghjklmnprstvxyz])\1", r"\1", "".join(out))
    return re.sub(r"iy(?= |$)", "i", s)   # nisba -iyy -> -i


# ---------------------------------------------------------------------------
# Library romanizers (lazy)
# ---------------------------------------------------------------------------

_cutlet = None


def _ja_romaji(word):
    global _cutlet
    if _cutlet is None:
        import cutlet
        import unidic_lite
        _cutlet = cutlet.Cutlet("hepburn", mecab_args='-d "{}" -r /dev/null'.format(unidic_lite.DICDIR))
        _cutlet.use_foreign_spelling = False
    return _cutlet.romaji(word)


def _ko_rr(word):
    from korean_romanizer.romanizer import Romanizer
    return Romanizer(word).romanize()


def _pinyin(word):
    import pypinyin
    return " ".join(pypinyin.lazy_pinyin(word, style=pypinyin.Style.TONE))


def _ru_translit(word):
    from transliterate import translit
    return translit(word, "ru", reversed=True)


HAN = re.compile(r"[㐀-鿿豈-﫿]")
KANA = re.compile(r"[぀-ヿ]")
HANGUL = re.compile(r"[가-힯ᄀ-ᇿ]")
LATIN = re.compile(r"^[\sA-Za-zÀ-ɏḀ-ỿ'’\-]+$")


def _pick_roman(roman, lang):
    """Wiktionary romanizations can list alternatives ('lī-tián / jī-tián')."""
    if not roman:
        return ""
    return re.split(r"\s*[/,;]\s*", roman)[0]


def ipa_to_globasa(ipa):
    s = ipa.strip("/[] ").split(",")[0]
    s = re.sub(r"[()]", "", s)
    return clean(apply(IPA, unicodedata.normalize("NFC", s)))


def to_globasa(lang, word, roman="", ipa=""):
    """Return [(form, method)] -- renderings in Globasa letters, best first."""
    w = unicodedata.normalize("NFC", word.strip())
    lw = w.lower()
    r = _pick_roman(roman, lang).lower()
    out = []

    def add(form, how):
        f = clean(form)
        if f and f not in [x[0] for x in out]:
            out.append((f, how))

    if lang == "ru":
        src = r or _ru_translit(w).lower()
        add(apply(RU, strip_marks(src, keep="̌̈")), "roman" if r else "translit-lib")
    elif lang == "cmn":
        src = r or (_pinyin(w) if HAN.search(w) else lw)
        add(apply(PINYIN, strip_marks(src, keep="̈").replace("ü", "ü")), "roman" if r else "pypinyin")
    elif lang == "ja":
        src = r or (_ja_romaji(w).lower() if (HAN.search(w) or KANA.search(w)) else lw)
        add(apply(HEPBURN, strip_marks(src)), "roman" if r else "cutlet")
    elif lang == "ko":
        src = r or (_ko_rr(w) if HANGUL.search(w) else lw)
        add(apply(KOREAN, strip_marks(src)), "roman" if r else "korean_romanizer")
    elif lang == "vi":
        add(apply(VIET, strip_marks(lw, keep="̛̂̆")), "spelling")
    elif lang in ("hi", "te"):
        if r:
            add(apply(INDIC, unicodedata.normalize("NFC", r)), "roman")
        elif ipa:
            add(ipa_to_globasa(ipa), "ipa")
    elif lang == "ar":
        sc = arabic_script(w)
        if sc:
            add(sc, "vocalised script")
        if r:
            add(re.sub(r"([bcdfghjklmnprstvxyz])\1", r"\1", apply(ARABIC, unicodedata.normalize("NFC", r))), "roman")
        elif ipa:
            add(ipa_to_globasa(ipa), "ipa")
    elif lang == "fa":
        if r:
            add(apply(PERSIAN, unicodedata.normalize("NFC", r)), "roman")
        elif ipa:
            add(ipa_to_globasa(ipa), "ipa")
    elif lang == "tr":
        add(apply(TURKISH, lw), "spelling")
    elif lang == "es":
        add(apply(SPANISH, strip_marks(lw, keep="̃̈").replace("ñ", "ñ").replace("ü", "ü")), "spelling")
    elif lang == "de":
        add(apply(GERMAN, lw), "spelling")
    elif lang == "fr":
        if ipa:
            add(ipa_to_globasa(ipa), "ipa")
        add(apply(FRENCH, lw), "spelling")
    elif lang == "en":
        if ipa:
            add(ipa_to_globasa(ipa), "ipa")
        add(apply(ENGLISH_SPELL, lw), "spelling")
    elif lang == "sw":
        add(apply(SWAHILI, lw), "spelling")
    elif lang == "id":
        add(apply(INDONESIAN, lw), "spelling")
    else:
        if r:
            add(r, "roman")
        elif LATIN.match(w):
            add(lw, "spelling")
        elif ipa:
            add(ipa_to_globasa(ipa), "ipa")
    return out
