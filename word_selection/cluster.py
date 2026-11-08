"""Group gathered source words into etymon clusters.

1. Etymology links (Wiktionary bor/inh/der/cog...) join words outright:
   A borrowed from B, or A and B borrowed from the same source term.
2. Average-linkage agglomerative clustering on normalised alignment distance
   between Globasa-letter forms, stopping at THRESHOLD.
   Sinosphere words are decided by their Han spelling where it is known
   (item["han"]: the word itself for cmn/ja, hanja for ko, chữ Hán for vi, all
   normalised to traditional characters): the same spelling joins outright
   (基质 = 基質 = 기질 [基質]); two different known spellings are different words, so
   only plain distance applies. Only when one side's spelling is unknown do
   Sino-xenic sound correspondences and Middle Chinese / Cantonese pivots apply.
   Arabic and Persian words join on the same normalised consonant skeleton
   (abjad.py) only as a fallback, when one of the two has no romanization: with both
   romanized, sound decides. A word with no usable reading at all can still join a
   cluster this way.
A language may sit in several clusters (synonyms); each cluster counts it once.
"""

import unicodedata

from . import abjad
from .align import distance, sino_distance
from .languages import BY_CODE

THRESHOLD = 0.30   # pairwise cognate F1 0.92 on LexiliAsel (prec 0.95, rec 0.90)
HAN_LANGS = {"cmn", "ja", "ko", "vi"}
# Sino-route distances (correspondences + MC/Cantonese pivots) carry a penalty: on
# LexiliAsel Sinosphere pairs @0.30, plain recall .791 / false-pos .052; Sino+pivots
# unpenalised .881 / .072; with this margin .860 / .055
SINO_MARGIN = 0.07
LINK_KINDS = {"bor", "lbor", "ubor", "slbor", "obor", "psm", "translit", "der"}


def _norm(w):
    d = unicodedata.normalize("NFD", w or "")
    return "".join(c for c in d if not unicodedata.combining(c)).lower().strip("-* ")


def item_distance(a, b):
    """Min normalised distance over the items' alternative renderings. Between a
    Han-spelt word and a Sinosphere word of unknown spelling (see _sino_ok),
    Sino-xenic sound correspondences count too."""
    if not (a["forms"] and b["forms"]):
        return 9.0   # an unreadable word joins only through its spelling
    d = min(distance(x, y, normalized=True) for x in a["forms"] for y in b["forms"])
    if _sino_ok(a, b):
        # Middle Chinese / Cantonese pivots (item["pivots"]) keep the codas and
        # velars Mandarin lost; they are compared only against the other word's
        # own readings (pivot vs pivot would just restate the spelling)
        fa = [(a["lang"], x) for x in a["forms"]] + [("zh-pivot", x) for x in a.get("pivots", ())]
        fb = [(b["lang"], y) for y in b["forms"]] + [("zh-pivot", y) for y in b.get("pivots", ())]
        d = min(d, SINO_MARGIN + min(sino_distance(lx, x, ly, y) for lx, x in fa for ly, y in fb
                                     if not (lx == ly == "zh-pivot")))
    return d


def _morphemes(item):
    """Morpheme count of a word that could be Sino-xenic: Han characters (cmn, ja),
    hangul syllables (ko), syllables (vi); None for anything else (kana, Latin loans)."""
    w, lang = (item.get("word") or "").strip().strip("-"), item.get("lang")
    if not w:
        return None
    if lang in ("cmn", "ja"):
        return len(w) if all(_is_han(c) for c in w) else None
    if lang == "ko":
        return len(w) if all("\uac00" <= c <= "\ud7a3" for c in w) else None
    if lang == "vi":
        return len(w.split()) if all(c.isalpha() or c == " " for c in w) else None
    return None


def _sino_ok(a, b):
    """The phonetic Sino-xenic route is a fallback: two Sinosphere languages, exactly
    one word with a known Han spelling and the same number of morphemes; or both
    known and differing in a single character (both known otherwise: the spelling
    has decided)."""
    la, lb = a.get("lang"), b.get("lang")
    if la == lb or la not in HAN_LANGS or lb not in HAN_LANGS:
        return False
    if a.get("native_reading") or b.get("native_reading"):   # kun'yomi: not Sino-xenic
        return False
    ha, hb = han(a), han(b)
    if ha and hb:
        # both spellings known and different: only a one-character variant may still
        # be the same word (Japanese substitute characters: 蒸留 for 蒸餾)
        return any(len(x) == len(y) >= 2 and sum(c != d for c, d in zip(x, y)) == 1
                   for x in ha for y in hb)
    if not (ha or hb):
        return False
    na, nb = _morphemes(a), _morphemes(b)
    return na is not None and na == nb


def _is_han(ch):
    return unicodedata.name(ch, "").startswith(("CJK UNIFIED IDEOGRAPH", "CJK COMPATIBILITY IDEOGRAPH"))


def han(item):
    """Known Han spellings of a Sinosphere item: item["han"] if the pipeline set it
    (normalised), else the word itself for a wholly Han-spelt cmn/ja word."""
    if item.get("lang") not in HAN_LANGS:
        return []
    if "han" in item:
        return item["han"]
    w = (item.get("word") or "").strip()
    return [w] if item.get("lang") in ("cmn", "ja") and w and all(_is_han(c) for c in w) else []


def _etym_keys(item):
    keys = {(item["lang_dump"], _norm(item["word"]))}
    for kind, src, term in item.get("etym", []):
        # borrowings only; inheritance from proto-languages links cognates whose
        # FORMS diverged (water ~ voda), which is not what the methodology counts
        if kind in LINK_KINDS and not src.endswith("-pro"):
            keys.add((src, _norm(term)))
    return keys


def cluster(items, threshold=THRESHOLD):
    """items: [{id, lang, lang_dump, word, forms: [str], etym: [[kind, src, term]]}].
    Returns [{members: [item], etym_links: [str]}]."""
    items = [it for it in items if it["forms"] or abjad.skeletons(it.get("lang"), it.get("word"))]
    parent = list(range(len(items)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    links = {}
    keyed = {}
    for i, it in enumerate(items):
        for k in _etym_keys(it):
            keyed.setdefault(k, []).append(i)
    for k, idxs in keyed.items():
        for j in idxs[1:]:
            a, b = find(idxs[0]), find(j)
            if a != b:
                parent[b] = a
                links.setdefault(a, []).append(
                    f"{items[idxs[0]]['word']} ({items[idxs[0]]['lang']}) ~ {items[j]['word']} "
                    f"({items[j]['lang']}) via {k[0]} {k[1]}")
    def romanized(it):
        return it.get("romanized", bool(it["forms"]))

    by_spelling = {}
    for i, it in enumerate(items):
        keys = [("Han spelling", k) for k in han(it)]
        keys += [("abjad spelling", k) for k in abjad.skeletons(it.get("lang"), it.get("word"))]
        for k in keys:
            by_spelling.setdefault(k, []).append(i)
    for (kind, k), idxs in by_spelling.items():
        for x, i in enumerate(idxs):
            for j in idxs[x + 1:]:
                if kind == "abjad spelling" and romanized(items[i]) and romanized(items[j]):
                    continue   # both romanized: the sounds decide
                a, b = find(i), find(j)
                if a != b:
                    parent[b] = a
                    links.setdefault(a, []).extend(links.pop(b, []))
                    links[a].append(f"{items[i]['word']} ({items[i]['lang']}) ~ {items[j]['word']} "
                                    f"({items[j]['lang']}) via {kind} {k}")
    groups = {}
    for i in range(len(items)):
        groups.setdefault(find(i), []).append(i)
    clusters = [{"idx": g, "links": links.get(r, [])} for r, g in groups.items()]
    # pairwise cache
    D = {}

    def d(i, j):
        if (i, j) not in D:
            D[(i, j)] = D[(j, i)] = item_distance(items[i], items[j])
        return D[(i, j)]

    while len(clusters) > 1:
        best = None
        for x in range(len(clusters)):
            for y in range(x + 1, len(clusters)):
                ds = [d(i, j) for i in clusters[x]["idx"] for j in clusters[y]["idx"]]
                avg = sum(ds) / len(ds)
                if best is None or avg < best[0]:
                    best = (avg, x, y)
        if best[0] > threshold:
            break
        _, x, y = best
        clusters[x]["idx"] += clusters[y]["idx"]
        clusters[x]["links"] += clusters[y]["links"]
        del clusters[y]
    return [{"members": [items[i] for i in c["idx"]], "etym_links": c["links"]} for c in clusters]
