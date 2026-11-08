"""Proper nouns and culture-specific words: their form follows the source, not a blend.

The grammar (xwexi gramati/abece-ji-lafuzu) gives proper nouns and culture-specific
words their own phonotactics (Madrid, Budapest; teriyaki, koktel, blakjaku, jazu,
vodka, yinyangu), and its examples take the form of the culture the word comes
from. A blend of every language's adaptation of such a word (Unix: Japanese
yunikkusu, Korean yuniksu, Mandarin 尤内克斯 yowneykosi) is the wrong target.

Detection, conservative (anything else stays an ordinary word):
  proper    the English headword is capitalised and English Wiktionary lists it
            as a name (Unix). Origin: the language English borrowed it from, if a
            source language, else English.
  cultural  English borrowed the word from a source language (sushi < ja 寿司),
            and words of at least two other languages borrow from the same word.
A concept can set it by hand: "cultural": {"kind": "proper"|"cultural",
"origin": [lang, word]}, or turn it off with "cultural": false.
"""

import re

from .languages import BY_CODE, DUMP_TO_CODE

BORROW = {"bor", "lbor", "slbor", "obor", "ubor", "translit", "psm"}
MIN_SUPPORT = 2          # other languages that borrow from the same word


def _norm(w):
    from .vocalization import key
    return key(w).lower()


def _borrowed_from(etym):
    for kind, src, term in etym or []:
        if kind in BORROW and src in DUMP_TO_CODE and DUMP_TO_CODE[src] != "en" and term:
            return DUMP_TO_CODE[src], term
    return None


def detect(concept, words):
    """{kind, lang, word, why, support} or None."""
    from .sources.wiktionary import lookup
    manual = concept.get("cultural")
    if manual is False:
        return None
    if isinstance(manual, dict) and manual.get("origin"):
        lang, word = manual["origin"]
        return {"kind": manual.get("kind", "cultural"), "lang": lang, "word": word,
                "why": "set by hand for this concept", "support": []}
    for wiki, head, pos, sense in concept.get("wikt_senses", []):
        if wiki != "en":
            continue
        info = lookup("en", head)
        src = _borrowed_from(info["etym"])
        is_name = head[:1].isupper() and any(s["pos"] == "name" for s in info["senses"])
        lang, word = src if src else ("en", head)
        # other languages' words borrowed from the origin (or from the English word)
        targets = {(lang, _norm(word)), ("en", _norm(head))}
        support = sorted({w["lang"] for w in words if w["lang"] not in ("en", lang)
                          and (lambda b: b and (b[0], _norm(b[1])) in targets)(_borrowed_from(w.get("etym")))})
        # what the name was formed on (Unix: Multics, and the pun on eunuch)
        # (the index stores some etymology links shifted: [Multics>Q739186, Multics, Q739186])
        formed_on = list(dict.fromkeys(
            (s if re.fullmatch(r"Q\d+", term or "") else term) for kind, s, term in info["etym"] or []
            if kind not in BORROW and (re.fullmatch(r"Q\d+", term or "") or (term and s not in DUMP_TO_CODE))))
        if is_name:
            why = (f"English Wiktionary lists {head} as a proper noun"
                   + (f", borrowed from {BY_CODE[lang]['basa']} {word}" if src else "")
                   + (f"; formed on {', '.join(formed_on)}" if formed_on else ""))
            return {"kind": "proper", "lang": lang, "word": word, "why": why, "support": support}
        if src and len(support) >= MIN_SUPPORT:
            why = (f"English {head} is borrowed from {BY_CODE[lang]['basa']} {word}, as are the words of "
                   f"{', '.join(BY_CODE[l]['basa'] for l in support)}")
            return {"kind": "cultural", "lang": lang, "word": word, "why": why, "support": support}
    return None


def origin_member(info, words):
    """The source word among the gathered words (by spelling), or None."""
    target = _norm(info["word"])
    for w in words:
        if w["lang"] == info["lang"] and _norm(w["word"]) == target and w.get("forms") and not w.get("excluded"):
            return w
    return None


def checked_pronunciations(origin_form, members):
    """Each member's checked reading against the source form: [(lang, form, agrees)]."""
    from .align import edit_count
    out = []
    for m in members:
        if m["form"]:
            out.append((m["lang"], m["form"], edit_count(m["form"], origin_form)[0] <= 1))
    return out
