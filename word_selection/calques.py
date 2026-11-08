"""Calques: Globasa compounds that render a concept the way the source languages
build their own words for it.

Milky Way: Spanish Vía Láctea, French Voie lactée, German Milchstraße, Russian
Млечный Путь and Persian راه شیری say "milk + way"; Arabic and Turkish "straw +
way"; Telugu "star + street"; Mandarin, Korean, Vietnamese "silver + river";
Japanese and Hindi "heaven/sky + river". Globasa took the head most widely shared
(way: Europe, Persian, Arabic, Turkish, Telugu) and the modifier it carries in
the largest group: milko + dao = milkodao.

Steps:
  1. split each source word into parts: Wiktionary compound/affix templates
     (concept index `parts`), single Han characters for Han-spelled Sinosphere
     words, the words of a phrase; function words (の, de, of, al-) dropped;
  2. gloss each part (the template's gloss, else its first English sense; Han
     characters as Chinese characters) and map it to Globasa roots through the
     word list's English column (milky -> milk -> milko);
  3. find the head: last part in head-final languages, first in head-initial ones;
  4. count independent coinages (not languages: Sinosphere borrowings of one
     Chinese compound count once, a marked calque counts with its model) per head,
     and per modifier + head pair as one word uses them;
  5. propose modifier + head, concatenated (986 of 987 two-root compounds in the
     word list are plain concatenation, modifier first: acidi + krimu = acidikrimu).
"""

import re
from functools import lru_cache

from .languages import BY_CODE

HEAD_FINAL = {"en", "de", "ru", "cmn", "ja", "ko", "hi", "te", "tr"}
HEAD_INITIAL = {"es", "fr", "ar", "fa", "id", "sw", "vi"}
STOP_PARTS = {"の", "之", "的", "de", "del", "la", "le", "les", "el", "los", "las", "of", "the", "a", "an",
              "des", "du", "d", "ya", "wa", "za", "cha", "la", "von", "der", "die", "das", "-",
              "ال", "و", "ی", "e", "i", "ning"}
SINO = ("cmn", "ja", "ko", "vi")


def _ix():
    from .sources.wiktionary import index
    return index()


def _is_han(c):
    return "㐀" <= c <= "鿿" or "豈" <= c <= "﫿"


def split(lang, word):
    """[(part, gloss)] for one source word; [] if it is a single morpheme."""
    from . import sinosphere
    w = (word or "").strip()
    if not w:
        return []
    got = _ix().parts(BY_CODE[lang]["dump"], w)
    if got:
        return [(p, g) for p, g in got]
    if lang in SINO:
        hs = sinosphere.han_spellings(lang, w)
        han = hs[0] if hs else (w if all(_is_han(c) for c in w) else "")
        if len(han) >= 2:
            return [(c, "") for c in han]
    toks = [t for t in re.split(r"[\s\-‌]+", w) if t]
    if lang in ("ar", "fa"):
        toks = [re.sub(r"^(ال|اَل|اَلْ)", "", t) for t in toks]
    return [(t, "") for t in toks] if len(toks) >= 2 else []


def _lemmas(lang, part):
    """Dictionary forms to try for an inflected part: French feminine/plural
    (lactée -> lacté), Spanish -a/-as/-os -> -o (láctea -> lácteo), Russian without
    stress marks, Persian adjectival -ی (شیری -> شیر), Arabic article and -ة."""
    import unicodedata
    p = unicodedata.normalize("NFC", unicodedata.normalize("NFD", part).replace("\u0301", ""))
    out = [p, p.lower()]
    lw = p.lower()
    if lang == "fr":
        out += [re.sub(r"(e|es|s)$", "", lw)]
    elif lang == "es":
        out += [re.sub(r"(a|as|os)$", "o", lw), re.sub(r"s$", "", lw)]
    elif lang == "fa":
        out += [re.sub(r"ی$", "", p)]
    elif lang == "ar":
        q = re.sub(r"[\u064b-\u0652\u0670\u0640]", "", p)
        q = re.sub(r"^ال", "", q)
        out += [q, re.sub(r"ة$", "", q), re.sub(r"انة$", "ن", q)]
    return list(dict.fromkeys(x for x in out if x))


@lru_cache(maxsize=20000)
def gloss(lang, part, given=""):
    """English gloss items for a part: the template's gloss; an English part is its
    own gloss; else the first senses of the part (or of its dictionary form; a Han
    character as a Chinese character)."""
    from .sources.wiktionary import lookup
    if given:
        texts = [given]
    elif lang == "en":
        texts = [part.lower()]
    else:
        code = "cmn" if (lang in SINO and len(part) == 1 and _is_han(part)) else lang
        texts = []
        for cand in _lemmas(code, part):
            try:
                texts = [s["gloss"] for s in lookup(code, cand)["senses"][:4]]
            except Exception:
                texts = []
            if texts:
                break
    items = []
    for t in texts:
        t = re.sub(r"\([^)]*\)", "", t)
        for it in re.split(r"[;,/]| or ", t):
            it = re.sub(r"^(to|a|an|the)\s+", "", it.strip().lower()).strip(" .")
            if it and len(it.split()) <= 2 and it not in items:
                items.append(it)
    return tuple(items[:10])


def _forms(item):
    """milky -> milk, silvery -> silver, heavenly -> heaven, golden -> gold."""
    out = [item]
    for suf, rep in (("ily", "y"), ("ly", ""), ("y", ""), ("ery", "er"), ("en", ""), ("ous", ""), ("ic", ""),
                     ("ish", ""), ("ian", ""), ("al", "")):
        if item.endswith(suf) and len(item) - len(suf) >= 3:
            out.append(item[: len(item) - len(suf)] + rep)
    return out


@lru_cache(maxsize=1)
def _gloss_rank():
    """{(root, English item): position of the item in the root's own English gloss}:
    almasi is 'diamond' first, rombo is 'rhombus' first and 'diamond' second."""
    from .contrasts import _wl_key
    from .lexicon import load
    out = {}
    for r in load().itertuples(index=False):
        text = re.sub(r"\([^)]*\)", "", r.TranslationEng or "")
        items = []
        for chunk in re.split(r"[;|]", text):
            chunk = re.sub(r"^\s*[^:,]{1,12}:\s*", "", chunk)
            items += [_wl_key("en", it) for it in chunk.split(",") if it.strip()]
        for i, it in enumerate(items):
            out.setdefault((r.Word.lower(), it), i)
    return out


@lru_cache(maxsize=1)
def _root_set():
    from .lexicon import load
    df = load()
    return {w.lower() for w in df[df["Category"] == "root"]["Word"]}


@lru_cache(maxsize=20000)
def concept(lang, part, given=""):
    """(label, (Globasa roots)) for a part: every root some gloss item maps to
    (dao is glossed "path, way, route", so way, path and route parts all support
    it); roots first, then other words. Without any, the first gloss item."""
    from .contrasts import _globasa_index, _wl_key
    en = _globasa_index().get("en", {})
    roots = _root_set()
    items = gloss(lang, part, given)
    found, label = [], ""
    roots_only = [it for it in items if any(w.lower() in roots for f in _forms(it)
                                             for w in en.get(_wl_key("en", f), []))]
    for it in roots_only or items:
        for f in _forms(it):
            for w in en.get(_wl_key("en", f), []):
                w = w.lower()
                if w not in found:
                    found.append(w)
                    label = label or f
    found = [w for w in found if w in roots and " " not in w]   # parts are roots
    # the root whose own gloss leads with the item: almasi (diamond) before rombo
    # (rhombus, diamond)
    rank = _gloss_rank()
    keys = [_wl_key("en", f) for it in items for f in _forms(it)]
    found.sort(key=lambda w: (min((rank.get((w, k), 99) for k in keys), default=99), len(w)))
    if found:
        return label, tuple(found[:4])
    return (items[0] if items else part), ()


def decompose(lang, word):
    """{lang, word, parts: [(part, concept, roots)], head, modifier} or None."""
    parts = [(p, g) for p, g in split(lang, word) if p.lower() not in STOP_PARTS and p not in STOP_PARTS]
    if len(parts) < 2:
        return None
    rows = [(p,) + concept(lang, p, g) for p, g in parts]
    from . import sinosphere
    head_final = lang in HEAD_FINAL or (lang == "vi" and sinosphere.han_spellings("vi", word))
    h = len(rows) - 1 if head_final else 0
    m = h - 1 if head_final else 1
    return {"lang": lang, "word": word, "parts": rows, "head": rows[h], "modifier": rows[m]}


CALQUE_LINKS = {"calque", "bor", "lbor", "slbor", "psm", "translit", "der"}


def coinages(decs):
    """{id(decomposition): coinage label}: one label per independent coinage, as the
    Sprachbund criterion counts (areally diffused attestations are not independent).
    Starts from the language family; Sinosphere words sharing a Han spelling are one
    coinage (Japanese 銀河, Korean 은하, Vietnamese Ngân Hà borrow Chinese 銀河); a
    word Wiktionary marks as a calque or borrowing of a language present joins that
    language's coinage (Persian راه شیری, a calque of French Voie lactée)."""
    from . import sinosphere
    from .languages import DUMP_TO_CODE, family
    from .sources.wiktionary import lookup
    parent = {id(d): id(d) for d in decs}
    by_id = {id(d): d for d in decs}

    def root(x):
        while parent[x] != x:
            x = parent[x]
        return x

    def join(a, b):
        parent[root(a)] = root(b)
    fam = {}
    for d in decs:                                   # one family, one coinage
        fam.setdefault(family(d["lang"]), []).append(id(d))
    for ids in fam.values():
        for x in ids[1:]:
            join(x, ids[0])
    spell = {}
    for d in decs:                                   # shared Han spelling
        if d["lang"] in SINO:
            for sp in sinosphere.han_spellings(d["lang"], d["word"]):
                spell.setdefault(sp, []).append(id(d))
    for ids in spell.values():
        for x in ids[1:]:
            join(x, ids[0])
    langs_present = {d["lang"]: id(d) for d in decs}
    for d in decs:                                   # marked calques and borrowings
        try:
            ety = lookup(d["lang"], d["word"])["etym"]
        except Exception:
            ety = []
        for kind, src, _ in ety:
            code = DUMP_TO_CODE.get(src)
            if kind in CALQUE_LINKS and code in langs_present and code != d["lang"]:
                join(id(d), langs_present[code])
    labels = {}
    for x in parent:
        r = root(x)
        members = sorted({by_id[y]["lang"] for y in parent if root(y) == r})
        labels[x] = "+".join(members)
    return labels


def propose(words, max_out=8):
    """Calque candidates from a concept's source words ({lang, word, excluded}).
    [{form, modifier, head, pair_families, head_families, langs, roots_ok, why}],
    best first; and the per-word decompositions."""
    from .languages import family
    decs = []
    for w in words:
        if w.get("excluded") or w["lang"] not in BY_CODE:
            continue
        d = decompose(w["lang"], w["word"])
        if d:
            decs.append(d)
    # support counted per Globasa root (a part supports every root its glosses map
    # to); a part with no root counts under its gloss label
    def keys(row):
        return list(row[2]) or [f"({row[1]})"]
    area = coinages(decs)
    head_fam, pair_fam, pair_langs = {}, {}, {}
    for d in decs:
        fam = area[id(d)]
        for hk in keys(d["head"]):
            head_fam.setdefault(hk, set()).add(fam)
            for mk in keys(d["modifier"]):
                pair_fam.setdefault((mk, hk), set()).add(fam)
                pair_langs.setdefault((mk, hk), set()).add(d["lang"])
    order = ["cmn", "ja", "ko", "vi", "ar", "hi", "en", "es", "fr", "de", "ru", "fa", "tr"]

    def tiebreak(langs):
        east = sum(l in ("cmn", "ja", "ko", "vi") for l in langs)
        return (-(east >= 2), -("ar" in langs and len(langs) > 1), -("hi" in langs and len(langs) > 1),
                -(any(l in ("en", "es", "fr", "de", "ru") for l in langs) and len(langs) > 1))

    out = []
    for (mk, hk), fams in pair_fam.items():
        ok = not mk.startswith("(") and not hk.startswith("(")
        langs = sorted(pair_langs[(mk, hk)], key=lambda l: order.index(l) if l in order else 99)
        out.append({"form": mk + hk if ok else "", "modifier": mk, "head": hk,
                    "pair_families": sorted(fams), "head_families": sorted(head_fam[hk]),
                    "langs": langs, "roots_ok": ok,
                    "why": (f"{mk} + {hk}: {len(fams)} independent coinage{'' if len(fams) == 1 else 's'} "
                            f"({'; '.join(sorted(fams))}); head {hk} in {len(head_fam[hk])} "
                            f"({'; '.join(sorted(head_fam[hk]))})")})
    out.sort(key=lambda c: (not c["roots_ok"], -len(c["head_families"]), -len(c["pair_families"]),
                            -len(c["langs"]), tiebreak(c["langs"])))
    return out[:max_out], decs
