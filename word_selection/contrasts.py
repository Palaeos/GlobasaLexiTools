"""Lexical contrasts the source languages make inside one English sense, found
through other Wiktionary editions.

English "brother" is one word; Japanese Wiktionary has separate entries 兄 (older)
and 弟 (younger), each with its own translation table, and Korean answers 형 vs
동생, Mandarin 哥哥 vs 弟弟, Turkish ağabey vs kardeş. German Wiktionary splits
Reis into the grain and the plant (Japanese 米 vs 稲, Indonesian beras vs padi).
So a foreign edition's sense divisions, checked against its translations into
the other source languages, show contrasts English collapses.

  1. Pivots: the concept's source words in a language whose Wiktionary edition is
     indexed (WiktionaryLMDB_<edition>). Each sense of a pivot there, with its
     translation table, is a "foreign sense".
  2. A foreign sense belongs to the concept if its translations share words with
     the concept's sources in at least MIN_OVERLAP languages (Bruder "monk" does not).
  3. Two foreign senses contrast where languages give them disjoint words; the
     contrast counts if those languages span at least MIN_FAMILIES families.
     Languages using one word for both are listed as not making it. Foreign
     senses that more languages share a word between than tell apart are one
     sense seen from two editions (Bruder ~ frère; tables differ only in which
     words they happen to list) and merge into one side; a contrast needs the
     languages telling the sides apart to outnumber those that do not.
"""

import os
from functools import lru_cache
from itertools import combinations

from .languages import BY_CODE, WIKT_TO_CODE

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Wiktionary edition -> the source language its own entries are in
EDITIONS = {"de": "de", "fr": "fr", "es": "es", "ru": "ru", "zh": "cmn", "ja": "ja", "ko": "ko"}
MIN_OVERLAP = 2
MIN_FAMILIES = 2
# Isolating languages: a word is noun and adjective alike (Vietnamese hạnh phúc
# "happiness; happy", Mandarin 幸福), so the part of speech of the English table it
# came from says nothing; a cross-part-of-speech verdict is a real verdict.
ISOLATING = {"vi", "cmn"}


@lru_cache(maxsize=None)
def edition_db(edition):
    from .sources.wiktionary import other_wiki
    try:
        return other_wiki(edition)
    except Exception:
        return None


def available():
    return [e for e in EDITIONS if edition_db(e) is not None]


def _variants(w):
    """Spelling variants, without bracketed annotations (zh.wiktionary writes 형(兄))
    or stress marks (сестра́)."""
    import re
    import unicodedata
    from .sources.wiktionary import split_variants
    out = []
    for x in split_variants(w):
        x = re.sub(r"\s*[(（][^)）]*[)）]", "", x).strip()
        x = unicodedata.normalize("NFC", unicodedata.normalize("NFD", x).replace("\u0301", ""))
        if x:
            out.append(x)
    return out


def _lexical(mine, other, general=frozenset()):
    """Drop phrases composed from a word the language already has for this concept
    plus a modifier (младшая сестра, younger sister, छोटी बहन): a language making a
    contrast that way does not make it lexically. A phrase whose words are all new
    (Indonesian adik perempuan: adik is itself "younger sibling") stays."""
    singles = {w for w in mine | other | set(general) if " " not in w}
    return {w for w in mine if " " not in w or not (set(w.split()) & singles)}


def foreign_senses(edition, word):
    """Every sense of `word` in that edition that has translations:
    [{edition, word, pos, sense, trans: {lang: set(words)}}]."""
    db = edition_db(edition)
    if db is None:
        return []
    prefix = f"{word}\x00".encode("utf-8")
    out = []
    with db.env.begin(db=db.db_translations) as txn:
        cur = txn.cursor()
        if not cur.set_range(prefix):
            return []
        keys = []
        for k, _ in cur:
            if not bytes(k).startswith(prefix):
                break
            keys.append(bytes(k).decode("utf-8").split("\x00", 1)[1])
    for pos in keys:
        for sense, langs in (db.get_translations(word, pos) or {}).items():
            trans = {}
            for code, ts in langs.items():
                lang = WIKT_TO_CODE.get(code)
                if lang:
                    for t in ts:
                        trans.setdefault(lang, set()).update(_variants(t.word))
            if trans:
                out.append({"edition": edition, "word": word, "pos": pos, "sense": sense, "trans": trans})
    return out


# ---------------------------------------------------------------------------
# Same root across parts of speech (Glück ~ glücklich, bonheur ~ heureux,
# 행복 ~ 행복하다, 幸福 ~ 幸福な, سعادة ~ سعيد): such words are one word for a contrast
# ---------------------------------------------------------------------------

def _han_core(w):
    return "".join(c for c in w if "\u3400" <= c <= "\u9fff" or "\uf900" <= c <= "\ufaff")


def _jamo(w):
    import unicodedata
    w = w.removesuffix("하다").removesuffix("다")
    return unicodedata.normalize("NFD", w)


def _ar_root(w):
    from . import abjad
    sk = (abjad.skeletons("ar", w) or abjad.skeletons("fa", w) or [w])[0]
    sk = sk.replace(" ", "")
    sk = sk[1:] if sk.startswith("ا") else sk
    sk = sk.rstrip("هتة")
    return "".join(c for c in sk if c not in "اوی")


def _plain(w):
    import unicodedata
    d = unicodedata.normalize("NFD", w.lower())
    return "".join(c for c in d if not unicodedata.combining(c))


def _lcs(a, b):
    best = 0
    for i in range(len(a)):
        for j in range(len(b)):
            k = 0
            while i + k < len(a) and j + k < len(b) and a[i + k] == b[j + k]:
                k += 1
            best = max(best, k)
    return best


@lru_cache(maxsize=200000)
def related(lang, a, b):
    """Same word or same root, across parts of speech."""
    if a == b:
        return True
    ha, hb = _han_core(a), _han_core(b)
    if ha or hb:                                     # Han: the same characters
        return bool(ha) and ha == hb
    if any("\uac00" <= c <= "\ud7a3" for c in a + b):   # Hangul: a shared jamo stem
        ja, jb = _jamo(a), _jamo(b)
        short, long_ = sorted((ja, jb), key=len)
        return len(short) >= 4 and long_.startswith(short[:max(4, len(short) - 1)])
    if any("\u0600" <= c <= "\u06ff" for c in a + b):   # Arabic script: consonant root
        ra, rb = _ar_root(a), _ar_root(b)
        return len(ra) >= 3 and ra == rb
    if lang == "vi":                                 # Vietnamese: whole syllables, tones kept
        import unicodedata                           # (vui ~ niềm vui, but not vú, u, ừ)
        sa = unicodedata.normalize("NFC", a.lower()).split()
        sb = unicodedata.normalize("NFC", b.lower()).split()
        if not sa or not sb:
            return False
        short, long_ = sorted((sa, sb), key=len)
        return any(long_[i:i + len(short)] == short for i in range(len(long_) - len(short) + 1))
    pa, pb = _plain(a), _plain(b)                    # alphabetic: a long common stretch
    k = _lcs(pa, pb)
    return k >= 4 and k >= 0.55 * min(len(pa), len(pb))


def _shares(lang, xs, ys):
    return any(related(lang, x, y) for x in xs for y in ys)


def neighbour_tables(concept_words, own=()):
    """English translation tables that list the concept's source words (reverse
    index): the senses its words also carry, e.g. 嬉しい -> glad, joyful; 幸福 /
    행복 -> happiness, welfare. As foreign senses with edition "en"."""
    from .sources.wiktionary import index
    ix = index()
    seen = {}
    for lang, ws in concept_words.items():
        if lang == "en":
            continue
        codes = BY_CODE[lang]["wikt"]
        for w in ws:
            for code in codes:
                for en_word, pos, sense in ix.tables_listing(code, w):
                    seen.setdefault((en_word, pos, sense), None)
    out = []
    for en_word, pos, sense in seen:
        trans = {}
        for code, ts in ix.translations(en_word, pos).get(sense, {}).items():
            lang = WIKT_TO_CODE.get(code)
            if lang:
                for t in ts:
                    trans.setdefault(lang, set()).update(_variants(t[0]))
        trans.setdefault("en", set()).add(en_word)
        out.append({"edition": "en", "word": en_word, "pos": pos, "sense": sense, "trans": trans,
                    "own": [en_word, pos, sense] in [list(x)[1:] for x in own]})
    return out


def find(words, concept_def=None, pivot=None):
    """words: the run's source words ({lang, word, excluded}). Returns contrasts,
    most widely made first:
    [{sides: [{label, senses: [str], words: {lang: [word]}}], general: [str],
      made_by: {family: [lang]}, not_made_by: [lang], english: str}]
    made_by never counts English: the concept is English's own sense.
    concept_def: the concept (its wikt_senses are its own tables). pivot: (lang,
    word) -- only contrasts with a side containing that word (or a word of the same
    Han spelling in another Sinosphere language), that side first."""
    concept = {}
    for w in words:
        if not w.get("excluded"):
            concept.setdefault(w["lang"], set()).update(_variants(w["word"]))

    def overlap(s, skip):
        return sum(1 for l, ws in s["trans"].items()
                   if l not in (skip, "en") and _shares(l, ws, concept.get(l, set())))
    # 1-2: foreign senses of the pivots that belong to the concept: per pivot, only
    # the sense(s) sharing most words with the concept (frère "sibling", not
    # frère "comrade", which many languages also call brother)
    fs = []
    for edition in available():
        lang = EDITIONS[edition]
        for pw in sorted(concept.get(lang, ())):
            scored = []
            for s in foreign_senses(edition, pw):
                s["trans"].setdefault(lang, set()).add(pw)
                o = overlap(s, lang)
                if o >= MIN_OVERLAP:
                    scored.append((o, s))
            if scored:
                best = max(o for o, _ in scored)
                fs += [s for o, s in scored if o == best]
    # neighbouring English tables, one sense per English headword
    by_head = {}
    for s in neighbour_tables(concept, (concept_def or {}).get("wikt_senses", [])):
        o = overlap(s, "en")
        if o >= MIN_OVERLAP:
            by_head.setdefault(s["word"], []).append((o, s))
    for lst in by_head.values():
        best = max(o for o, _ in lst)
        fs += [s for o, s in lst if o == best]
    if len(fs) < 2:
        return []

    def split(a, b):
        apart, same = [], []
        for l in set(a["trans"]) & set(b["trans"]):
            g = concept.get(l, set())
            x, y = _lexical(a["trans"][l], b["trans"][l], g), _lexical(b["trans"][l], a["trans"][l], g)
            if x and y:
                (same if _shares(l, x, y) else apart).append(l)
        return apart, same

    def distinct(a, b):
        apart, same = split(a, b)
        return len(apart) > len(same)

    def alike(a, b):
        apart, same = split(a, b)
        return bool(same) and len(same) >= len(apart)

    # a general sense (Bruder, frère) shares words with specific senses that are
    # distinct from each other (兄 vs 弟): it is the general term, not a side
    general = {g for g in range(len(fs))
               if any(alike(fs[g], fs[a]) and alike(fs[g], fs[b]) and distinct(fs[a], fs[b])
                      for a, b in combinations([k for k in range(len(fs)) if k != g], 2))}
    general_senses = [fs[g] for g in sorted(general)]
    fs = [x for k, x in enumerate(fs) if k not in general]
    if len(fs) < 2:
        return []

    # merge foreign senses no language tells apart into sides
    parent = list(range(len(fs)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i, j in combinations(range(len(fs)), 2):
        if alike(fs[i], fs[j]):
            parent[root(j)] = root(i)
    sides = {}
    for i, s in enumerate(fs):
        sides.setdefault(root(i), []).append(s)
    side_list = []
    for members in sides.values():
        trans = {}
        for s in members:
            for l, ws in s["trans"].items():
                trans.setdefault(l, set()).update(ws)
        side_list.append({"senses": members, "trans": trans})
    # contrasts between sides
    edges = {}
    for a, b in combinations(range(len(side_list)), 2):
        apart, same = split(side_list[a], side_list[b])
        fams = {}
        for l in apart:
            if l != "en":           # the concept is English's; count the others
                fams.setdefault(BY_CODE[l]["family"], []).append(l)
        if len(fams) >= MIN_FAMILIES and len(apart) > len(same):
            edges[(a, b)] = (fams, same)
    if not edges:
        return []
    group = list(range(len(side_list)))

    def groot(i):
        while group[i] != i:
            i = group[i]
        return i
    for a, b in edges:
        group[groot(b)] = groot(a)
    out = {}
    for (a, b), (fams, same) in edges.items():
        g = out.setdefault(groot(a), {"sides": set(), "made_by": {}, "not_made_by": set()})
        g["sides"] |= {a, b}
        for f, ls in fams.items():
            g["made_by"].setdefault(f, set()).update(ls)
        g["not_made_by"] |= set(same)
    result = []
    for g in out.values():
        made = {l for ls in g["made_by"].values() for l in ls}
        english = "makes it" if any("en" in apart for apart in [split(side_list[a], side_list[b])[0] for a, b in edges if groot(a) == groot(next(iter(g["sides"])))]) else "does not make it"
        sides_out = []
        for i in sorted(g["sides"]):
            sd = side_list[i]
            labels = [f"{s['word']} ({s['edition']}.wiktionary, {s['pos']}): {s['sense']}" for s in sd["senses"]]
            sides_out.append({"label": labels[0], "senses": labels,
                              "words": {l: sorted(ws) for l, ws in sorted(sd["trans"].items())}})
        result.append({"sides": sides_out,
                       "general": [f"{s['word']} ({s['edition']}.wiktionary): {s['sense']}" for s in general_senses],
                       "made_by": {f: sorted(ls) for f, ls in sorted(g["made_by"].items())},
                       "not_made_by": sorted(g["not_made_by"] - made - {"en"}),
                       "english": english})
    result.sort(key=lambda c: -len(c["made_by"]))
    if pivot:
        result = [_pivot_first(c, pivot) for c in result]
        result = [c for c in result if c]
    return result


def _side_has(side, pivot):
    """Does a side contain the pivot word, or a Sinosphere word of the same Han
    spelling (幸福 ~ 행복 ~ hạnh phúc)?"""
    from . import sinosphere
    plang, pword = pivot
    phan = set(sinosphere.han_spellings(plang, pword))
    for l, ws in side["words"].items():
        for w in ws:
            if l == plang and related(l, w, pword):
                return True
            if phan and l in ("cmn", "ja", "ko", "vi") and phan & set(sinosphere.han_spellings(l, w)):
                return True
    return False


def _pivot_first(contrast, pivot):
    hits = [i for i, sd in enumerate(contrast["sides"]) if _side_has(sd, pivot)]
    if not hits:
        return None
    sides = [contrast["sides"][i] for i in hits] + \
            [sd for i, sd in enumerate(contrast["sides"]) if i not in hits]
    return {**contrast, "sides": sides, "pivot_sides": len(hits)}


# Globasa word-list translation columns, by source language
WL_COLUMNS = {"en": "TranslationEng", "es": "TranslationSpa", "fr": "TranslationFra",
              "de": "TranslationDeu", "ru": "TranslationRus", "cmn": "TranslationZho",
              "hi": "TranslationHin", "ar": "TranslationAra"}


def _wl_key(lang, w):
    import re
    w = re.sub(r"[(（][^)）]*[)）]", "", w).strip().strip(".…!?")
    if lang == "ar":
        from . import abjad
        sk = abjad.skeletons("ar", w)
        return sk[0] if sk else w
    return _plain(w)


@lru_cache(maxsize=1)
def _globasa_index():
    """{lang: {normalised translation: [Globasa word]}} from word-list.csv."""
    import re
    from .lexicon import load
    idx = {}
    for r in load().itertuples(index=False):
        word = r.Word.strip()
        for lang, col in WL_COLUMNS.items():
            text = getattr(r, col, "") or ""
            for chunk in re.split(r"[;|]", text):
                chunk = re.sub(r"^\s*[^:：,，、،]{1,8}[:：]\s*", "", chunk)   # "n: ", "名: ", "сущ: "
                for item in re.split(r"[,，、،/]", chunk):
                    k = _wl_key(lang, item)
                    if k:
                        idx.setdefault(lang, {}).setdefault(k, []).append(word)
    return idx


def globasa_coverage(sides):
    """Existing Globasa words whose translations already cover words of each side:
    sides = {name: {lang: [words]}} -> [{word, eng, covers: {name: {lang: [words]}}}],
    widest coverage first. A word covering two sides merges the contrast."""
    from .lexicon import words as lex
    idx = _globasa_index()
    found = {}
    for name, side in sides.items():
        for lang, ws in side.items():
            for w in ws:
                for g in idx.get(lang, {}).get(_wl_key(lang, w), []):
                    found.setdefault(g, {}).setdefault(name, {}).setdefault(lang, []).append(w)
    lx = lex()
    out = [{"word": g, "eng": lx.get(g.lower(), {}).get("eng", ""), "covers": cv,
            "merges": len(cv) > 1} for g, cv in found.items()]
    return sorted(out, key=lambda x: -sum(len(v) for v in x["covers"].values()))


MAX_SAME_ROOT = 12


def _stem(lang, w):
    """Strip inflection only, not derivation: Japanese 幸せな -> 幸せ, Korean
    행복하다 -> 행복 (but 기쁘다 stays apart from 기쁨)."""
    if lang == "ja":
        return w[:-1] if len(w) > 1 and w[-1] in "なだに" and _han_core(w) else w
    if lang == "ko":
        return w.removesuffix("하다") if w.endswith("하다") and len(w) > 2 else w
    return w


def _inflected_in(lang, w, listed):
    """Is w, or w without its inflection, among the listed words?"""
    return w in listed or _stem(lang, w) in {_stem(lang, x) for x in listed}


@lru_cache(maxsize=None)
def _listed_words(lang):
    """Every word of a source language that some English translation table lists
    (the reverse index's keys)."""
    from .sources.wiktionary import index
    ix = index()
    out = []
    with ix.env.begin() as txn:
        for code in BY_CODE[lang]["wikt"]:
            prefix = f"{code}\x00".encode("utf-8")
            cur = txn.cursor(db=ix.dbs["reverse"])
            if not cur.set_range(prefix):
                continue
            for k, _ in cur:
                k = bytes(k)
                if not k.startswith(prefix):
                    break
                out.append(k[len(prefix):].decode("utf-8"))
    return tuple(dict.fromkeys(out))


def _bucket_keys(lang, w):
    """Cheap keys that root relatives share, to avoid comparing against every word:
    each Han character, the first Hangul syllable, each Vietnamese syllable, else the
    first three letters."""
    import unicodedata
    core = _han_core(w)
    if core:
        return set(core)
    if any("\uac00" <= c <= "\ud7a3" for c in w):
        return {w[0]}
    if lang == "vi":
        return set(unicodedata.normalize("NFC", w.lower()).split())
    return {_plain(w)[:3]}


@lru_cache(maxsize=None)
def _buckets(lang):
    out = {}
    for x in _listed_words(lang):
        for k in _bucket_keys(lang, x):
            out.setdefault(k, []).append(x)
    return out


@lru_cache(maxsize=None)
def _same_root_of(lang, w):
    """Root relatives of one word that some table lists (cached across pivots)."""
    fits = ((lambda x: len(x.split()) <= len(w.split()) + 1) if lang == "vi"
            else (lambda x: " " not in x))
    b = _buckets(lang)
    cands = {x for k in _bucket_keys(lang, w) for x in b.get(k, ())}
    found = [x for x in cands if x != w and fits(x) and related(lang, x, w)]
    return tuple(sorted(found, key=len)[:MAX_SAME_ROOT])


def same_root_forms(ix, lang, words, exclude=()):
    """Other forms of the words' roots that translation tables list: 嬉しい -> 嬉しさ,
    기쁘다 -> 기쁨, vui -> niềm vui. Single words only (Vietnamese at most one
    syllable more: niềm vui, not niềm vui sống or sinh nhật vui vẻ nhé). Words
    related to `exclude` (the pivot's own cognates) are left out."""
    out = set()
    for w in words:
        if w:
            out.update(x for x in _same_root_of(lang, w) if not any(related(lang, x, e) for e in exclude))
    return out


def compare_to_pivot(words, concept_def, pivot):
    """Does the pivot's meaning separate from the concept's other words, language
    by language? (幸福 inside "happy": lasting happiness vs the glad of the moment.)

    pivot set: the pivot and its same-spelling Sinosphere cognates in the concept
      (幸福 ~ 幸福 ~ 행복 ~ hạnh phúc); foil set: the concept's other words in those
      languages (嬉しい, 高兴, 기쁘다, vui).
    Each side's tables: English translation tables listing a pivot (resp. foil)
    word, sharing words with the concept in MIN_OVERLAP languages; a table listing
    both (happy itself) belongs to neither.
    Each other language: its words scored over each side's tables, weighted by how
    much each table shares with the concept; the core is the words within half of
    the best score. It separates if the two cores share no root.
    Verdicts are made within each part of speech both sides have (felicidad, noun,
    vs alegre, adjective, proves nothing): separates / same word / phrase only
    (older brother, arroz crudo: a phrase on the general word) / no data; with no
    shared part of speech, the cross-POS verdict carries "(across parts of
    speech)" and does not count toward the families.
    globasa: existing Globasa words whose translations already cover words of
    either side (hoxya "happiness, joy" covers both: Globasa merges the contrast).
    covered: neighbouring tables another Globasa word already renders (cheerful,
    merry -> kweho); verdicts are computed on the remaining tables only. umbrella:
    the words under scrutiny (for the concept's own headword, or covering both sides).
    marked: a language whose pivot-side word also covers the foil meaning but which
    has a word of its own for the foil side (German glücklich covers both, froh is
    momentary only): the shape of a general word plus a marked one.
    Returns {pivot_words, foil_words, pivot_tables, foil_tables, globasa, umbrella, covered, marked,
             languages: {lang: {verdict, by_pos, pivot_core, foil_core}}, separates: {family: [lang]}}"""
    from collections import Counter
    from . import sinosphere
    from .sources.wiktionary import index
    ix = index()
    concept = {}
    for w in words:
        if not w.get("excluded"):
            concept.setdefault(w["lang"], set()).update(_variants(w["word"]))
    plang, pword = pivot
    phan = set(sinosphere.han_spellings(plang, pword)) or {pword}
    vi_cognates = {_plain(w) for w, hs in sinosphere.table()["vi"].items()
                   if phan & {n for h in hs for n in sinosphere.normalise(h, "vi")}}

    def cognate(l, w):
        """Same Han spelling as the pivot, allowing inflection (幸福な, 행복하다) and
        unmarked tones (hạnh phuc)."""
        if l == plang and related(l, w, pword):
            return True
        if l in ("cmn", "ja") and _han_core(w) in phan:
            return True
        if l == "ko":
            stem = w.removesuffix("하다").removesuffix("되다")
            return bool(phan & set(sinosphere.han_spellings("ko", stem)))
        if l == "vi":
            return _plain(w) in vi_cognates
        return False

    def trans(t):
        en_word, pos, sense = t
        out = {}
        for code, ts in ix.translations(en_word, pos).get(sense, {}).items():
            l = WIKT_TO_CODE.get(code)
            if l:
                for x in ts:
                    out.setdefault(l, set()).update(_variants(x[0]))
        out.setdefault("en", set()).add(en_word)
        return out

    def weight(tr):
        """Languages in which the table shares a word with the concept, not counting
        the pivot's own cognates (米 also spells 米国 "America")."""
        return sum(1 for l, ws in tr.items() if l != "en" and
                   _shares(l, ws, concept.get(l, set()) - cognates.get(l, set())))

    def tables_of(side):
        out = set()
        for l, ws in side.items():
            for w in ws:
                for code in BY_CODE[l]["wikt"]:
                    out |= {tuple(t) for t in ix.tables_listing(code, w)}
        return out

    own = {tuple(x[1:]) for x in (concept_def or {}).get("wikt_senses", []) if x and x[0] == "en"}
    # languages whose concept words are sorted onto the two sides: the Sinosphere
    # (where Han spelling finds cognates) and the pivot's own (froh vs glücklich)
    sino = ("cmn", "ja", "ko", "vi") + ((plang,) if plang not in ("cmn", "ja", "ko", "vi") else ())
    cognates = {l: {w for w in concept.get(l, ()) if cognate(l, w)} for l in sino}
    cognates.setdefault(plang, set()).add(pword)
    # pivot tables: those listing the pivot or a cognate (not the concept's own table)
    tp = {t: trans(t) for t in tables_of(cognates) - own}
    tp = {t: tr for t, tr in tp.items() if weight(tr) >= MIN_OVERLAP}
    # sides by the tables: a concept word those tables list means what the pivot
    # means (哥哥, 오빠 with 兄); the rest are the foil (弟, 남동생)
    pivot_set, foil_set = {}, {}
    for l in sino:
        for w in concept.get(l, ()):
            # the word itself must be listed (哥哥, 오빠 in "older brother"); a root
            # relative in a mixed table (기쁨 under happiness) does not take 기쁘다
            listed = cognate(l, w) or any(_inflected_in(l, w, tr.get(l, ())) for tr in tp.values())
            (pivot_set if listed else foil_set).setdefault(l, set()).add(w)
    pivot_set.setdefault(plang, set()).add(pword)
    # The foil words are often one part of speech only (嬉しい, 高兴, 기쁘다, vui are
    # adjectives), so their tables bring no nouns and a noun like Turkish mutluluk
    # has nothing to be compared with. Same-root forms (嬉しさ, 기쁨, niềm vui) reach
    # the foil's other parts of speech (joy).
    foil_reach = {l: set(ws) | same_root_forms(ix, l, ws, exclude=cognates.get(l, set()))
                  for l, ws in foil_set.items()}
    tf = {t: trans(t) for t in tables_of(foil_reach) - own - set(tp)}
    tf = {t: tr for t, tr in tf.items() if weight(tr) >= MIN_OVERLAP}

    def core(tables, l):
        """A language's words on one side, each scored by the summed weight of the
        tables listing it (cooked rice outweighs food, meal); those within half of
        the best score."""
        score = Counter()
        for tr in tables.values():
            for w in tr.get(l, ()):
                score[w] += weight(tr)
        if not score:
            return []
        top = max(score.values())
        return sorted((w for w, n in score.items() if 2 * n >= top), key=lambda w: -score[w])

    # Existing Globasa words for each side, and the neighbouring tables they already
    # cover. The umbrella words under scrutiny (those for the concept's own English
    # headword, and any word covering both sides) cover nothing; another word that
    # lists a table's headword as a gloss item (cheerful, merry -> kweho; pleased ->
    # furahado) takes that table out, and the verdicts use what is left.
    side_words = {"pivot": {}, "foil": {}}
    for name, tables in (("pivot", tp), ("foil", tf)):
        for tr in tables.values():
            for l, ws in tr.items():
                side_words[name].setdefault(l, set()).update(ws)
    side_words["pivot"].setdefault(plang, set()).add(pword)
    globasa = globasa_coverage({k: {l: sorted(v) for l, v in d.items()} for k, d in side_words.items()})
    en_idx = _globasa_index().get("en", {})
    umbrella = {g["word"] for g in globasa if g["merges"]}
    for x in (concept_def or {}).get("wikt_senses", []):
        if x and x[0] == "en":
            umbrella |= set(en_idx.get(_wl_key("en", x[1]), []))
    covered = {}
    for t in list(tp) + list(tf):
        gs = [g for g in en_idx.get(_wl_key("en", t[0]), []) if g not in umbrella]
        if gs:
            covered[t] = sorted(set(gs))
    all_tp, all_tf = tp, tf
    tp = {t: tr for t, tr in tp.items() if t not in covered} or tp
    tf = {t: tr for t, tr in tf.items() if t not in covered} or tf

    def judge(l, ta, tb):
        """Verdict for one language between two sets of tables."""
        a0, b0 = core(ta, l), core(tb, l)
        # a word listed on both sides (радость under happiness and under joy) is no
        # evidence for either: drop it from both cores; nothing left means one word
        on_a = {w for tr in ta.values() for w in tr.get(l, ())}
        on_b = {w for tr in tb.values() for w in tr.get(l, ())}
        both = on_a & on_b
        if a0 and b0 and (not [w for w in a0 if w not in both] or not [w for w in b0 if w not in both]):
            return "same word", a0, b0
        a0, b0 = [w for w in a0 if w not in both], [w for w in b0 if w not in both]
        g = concept.get(l, set())       # arroz crudo, older brother: phrases, not words
        a = [w for w in a0 if w in _lexical(set(a0), set(b0), g)]
        b = [w for w in b0 if w in _lexical(set(b0), set(a0), g)]
        if a0 and b0 and not (a and b):
            return "phrase only", a0, b0     # expressed, but not with a word of its own
        if not a or not b:
            return "no data", a, b
        return ("same word" if _shares(l, a, b) else "separates"), a, b

    def by_pos(tables, pos):
        return {t: tr for t, tr in tables.items() if t[1] == pos}

    # Compare within one part of speech: a noun on one side and adjectives on the
    # other (felicidad vs alegre) says nothing about the contrast; Spanish has
    # felicidad on both noun sides and feliz among the glad adjectives.
    langs, sep, marked = {}, {}, {}
    shared_pos = sorted({t[1] for t in tp} & {t[1] for t in tf})
    for l in sorted({l for tr in list(tp.values()) + list(tf.values()) for l in tr}):
        per = {}
        for pos in shared_pos:
            v, a, b = judge(l, by_pos(tp, pos), by_pos(tf, pos))
            if v != "no data":
                per[pos] = {"verdict": v, "pivot_core": a[:5], "foil_core": b[:5]}
        vs = [x["verdict"] for x in per.values()]
        # the pivot's word reappearing in another part of speech among the foil's
        # words (bonheur ~ heureux "glad", felicidad ~ feliz): the language uses
        # its pivot word for the foil meaning too
        foil_all = {w for tr in tf.values() for w in tr.get(l, ())}
        pa = [w for w in core(tp, l) if w not in foil_all]    # shared words prove nothing
        # single words only: hermano mayor ~ hermano, anh ~ anh em are phrases and
        # compounds on the word, not the word in another part of speech
        single = (lambda w: True) if l == "vi" else (lambda w: " " not in w)
        same_root = (lambda x, y: x == y) if l == "vi" else (lambda x, y: related(l, x, y))
        leak = sorted({f"{x} ~ {y}" for x in pa if single(x)
                       for y in foil_all if single(y) and same_root(x, y)})
        if leak and l != "en":
            vs.append("same word")
            per["across parts of speech"] = {"verdict": "same word", "pivot_core": pa[:5],
                                             "foil_core": leak[:5]}
        own = []
        if "same word" in vs:
            # privative contrast: the pivot-side word also covers the foil meaning
            # (glücklich "both momentarily and generally"), yet the language has a
            # word of its own for the foil side (froh "(momentarily) happy"). That
            # is the shape of a general word plus a marked derived one.
            pivot_all = {w for tr in tp.values() for w in tr.get(l, ())}
            foil_all = {w for tr in tf.values() for w in tr.get(l, ())}
            # relatedness only to words exclusive to the pivot side: радость sits on
            # both sides and must not take рад with it (счастье is the pivot's word)
            pivot_own = pivot_all - foil_all
            fc = core(tf, l)
            g = concept.get(l, set())
            own = [w for w in fc if w not in pivot_all and " " not in w
                   and not any(related(l, w, x) for x in pivot_own)
                   and w in _lexical({w}, set(), g)]
            verdict = "marked" if own else "same word"
        elif "separates" in vs:
            verdict = "separates"
        elif "phrase only" in vs:
            verdict = "phrase only"
        else:                           # no part of speech on both sides
            v, a, b = judge(l, tp, tf)
            if v in ("no data", "phrase only") or l in ISOLATING:
                verdict = v
            else:
                verdict = v + " (across parts of speech)"
        if l == "en" and verdict == "separates":
            # the concept's own English headword is the conflating word by
            # definition: if it shares the pivot side's root (happy ~ happiness), it
            # covers the foil meaning too (happy to see you), so English is marked
            heads = [x[1] for x in (concept_def or {}).get("wikt_senses", []) if x and x[0] == "en"]
            pivot_en = {w for tr in tp.values() for w in tr.get("en", ())}
            if any(related("en", h, w) for h in heads for w in pivot_en):
                verdict = "marked"
        if verdict == "separates" and l != "en":
            sep.setdefault(BY_CODE[l]["family"], []).append(l)
        if verdict == "marked" and l != "en":
            marked.setdefault(BY_CODE[l]["family"], []).append(l)
        allv, a, b = judge(l, tp, tf)
        langs[l] = {"verdict": verdict, "by_pos": per, "pivot_core": a[:5], "foil_core": b[:5],
                    "foil_own_words": own[:5]}
    return {"pivot_words": {l: sorted(v) for l, v in pivot_set.items()},
            "globasa": globasa,
            "foil_words": {l: sorted(v) for l, v in foil_set.items()},
            "pivot_tables": sorted(" / ".join(t[:2]) + ": " + t[2] for t in tp),
            "foil_tables": sorted(" / ".join(t[:2]) + ": " + t[2] for t in tf),
            "umbrella": sorted(umbrella),
            "covered": {f"{t[0]} / {t[1]}: {t[2]}": gs for t, gs in sorted(covered.items())},
            "languages": langs, "separates": sep, "marked": marked}


SUGGEST_MAX_SENSES = 2      # an English headword with this few substantial senses may lump
SUBSTANTIAL_LANGS = 5       # a sense table counts if it covers this many source languages


def suggestion(concept_def):
    """Should the page suggest an automatic pivot sweep? Yes when the concept's English
    headword has few substantial translation senses (happy: 2, rice: 2): English is
    then likely to lump distinctions other languages make.
    {suggest, headwords: [{word, pos, substantial, total}], reason}"""
    from .sources.wiktionary import index
    ix = index()
    heads = []
    for x in (concept_def or {}).get("wikt_senses", []):
        if not x or x[0] != "en":
            continue
        tables = ix.translations(x[1], x[2])
        sub = sum(1 for langs in tables.values()
                  if len({WIKT_TO_CODE.get(c) for c in langs} - {None, "en"}) >= SUBSTANTIAL_LANGS)
        heads.append({"word": x[1], "pos": x[2], "substantial": sub, "total": len(tables)})
    if not heads:
        return {"suggest": False, "headwords": [], "reason": "no English Wiktionary sense in the concept"}
    few = [h for h in heads if h["substantial"] <= SUGGEST_MAX_SENSES]
    if few:
        h = few[0]
        return {"suggest": True, "headwords": heads,
                "reason": f"English “{h['word']}” ({h['pos']}) has only {h['substantial']} substantial "
                          f"translation sense(s); other languages may draw distinctions inside it"}
    return {"suggest": False, "headwords": heads,
            "reason": "the English headword already has several substantial senses"}


def summarize(found):
    """auto_pivot output, trimmed for the page."""
    out = []
    for f in found:
        r = f["result"]
        out.append({
            "pivot": list(f["pivot"]), "also_pivots": [list(p) for p in f.get("also_pivots", [])],
            "separates": f["separates"], "marked": f["marked"],
            "pivot_tables": r["pivot_tables"], "foil_tables": r["foil_tables"],
            "pivot_words": r["pivot_words"], "foil_words": r["foil_words"],
            "covered": r["covered"], "umbrella": r["umbrella"],
            "globasa": [{"word": g["word"], "eng": g["eng"], "merges": g["merges"],
                         "sides": sorted(g["covers"])} for g in r["globasa"][:8]],
            "languages": {l: {"verdict": v["verdict"], "pivot": v["pivot_core"][:3], "foil": v["foil_core"][:3],
                              "own": v.get("foil_own_words", [])[:3]} for l, v in r["languages"].items()},
        })
    return out


def auto_pivot(words, concept_def, min_families=MIN_FAMILIES, progress=None):
    """Try every source word of the concept as the pivot (Sinosphere words of one
    Han spelling once: 幸福 / 幸福 / 행복 / hạnh phúc) and keep the contrasts made in
    at least min_families families, separating or marked. A pivot and its mirror
    (幸福 vs 嬉しい, 嬉しい vs 幸福) are one contrast. Best-attested first:
    [{pivot: (lang, word), separates: [family], marked: [family], result}]."""
    from . import sinosphere
    seen_spelling, pivots = set(), []
    order = {"cmn": 0, "ja": 1, "ko": 2, "vi": 3}
    cands = sorted({(w["lang"], v) for w in words if not w.get("excluded") and w["lang"] != "en"
                    for v in _variants(w["word"])}, key=lambda x: (order.get(x[0], 9), x))
    for lang, word in cands:
        if lang in order:
            hs = sinosphere.han_spellings(lang, word)
            if hs:
                if set(hs) & seen_spelling:
                    continue
                seen_spelling |= set(hs)
        pivots.append((lang, word))
    found = []
    for i, pv in enumerate(pivots):
        if progress:
            progress(i, len(pivots), pv)
        try:
            r = compare_to_pivot(words, concept_def, pv)
        except Exception as e:      # one odd word must not sink the sweep
            if progress:
                progress(i, len(pivots), (pv, f"failed: {e}"))
            continue
        if not r["pivot_tables"] or not r["foil_tables"]:
            continue
        sep, mk = set(r["separates"]), set(r["marked"]) - set(r["separates"])
        if len(sep | mk) < min_families:
            continue
        found.append({"pivot": pv, "separates": sorted(sep), "marked": sorted(mk), "result": r})
    found.sort(key=lambda x: (-len(x["separates"]), -len(x["marked"])))
    # one contrast per split: a later pivot whose two sides mostly repeat an earlier
    # one's (same or swapped) is the same contrast
    def overlap(a, b):
        a, b = set(a), set(b)
        return len(a & b) / max(1, min(len(a), len(b)))
    kept = []
    for f in found:
        p, q = f["result"]["pivot_tables"], f["result"]["foil_tables"]
        dup = any((overlap(p, k["result"]["pivot_tables"]) >= 0.5 and overlap(q, k["result"]["foil_tables"]) >= 0.5)
                  or (overlap(p, k["result"]["foil_tables"]) >= 0.5 and overlap(q, k["result"]["pivot_tables"]) >= 0.5)
                  for k in kept)
        if dup:
            for k in kept:
                if k is not f and (overlap(p, k["result"]["pivot_tables"]) >= 0.5 or overlap(p, k["result"]["foil_tables"]) >= 0.5):
                    k.setdefault("also_pivots", []).append(f["pivot"])
                    break
            continue
        kept.append(f)
    return kept


def focus(contrast, side_index, words):
    """(lang, word) pairs to exclude to run the concept for one side only: words that
    appear on another side of the contrast but not on this one."""
    keep = contrast["sides"][side_index]["words"]
    drop = set()
    for i, s in enumerate(contrast["sides"]):
        if i == side_index:
            continue
        for l, ws in s["words"].items():
            for w in ws:
                if w not in keep.get(l, []):
                    drop.add((l, w))
    return sorted((w["lang"], w["word"]) for w in words
                  if any((w["lang"], v) in drop for v in _variants(w["word"])))
