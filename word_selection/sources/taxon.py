"""Candidates by taxon: a scientific name (concept key "taxa": ["Betula"]) is only a
search key for words with the same meaning in each language. The words found need
no Greco-Latin basis (birch, Birke, abedul, береза, huş).

Sources, all keyed by the taxon itself:
  Wikispecies   the taxon page's vernacular names ({{VN}}), by language
  Wikipedia     the interlanguage links of the taxon's article (Betula -> Birch)
  Wiktionary    English translation tables of the senses whose definition names
                the taxon ("a tree of the genus Betula")

Clean-up, each flagged on the word:
  rank markers  Japanese/Mandarin 属 科, Korean 속 과, Vietnamese chi/họ/bộ
                (カバノキ属 -> カバノキ, 자작나무속 -> 자작나무, chi bạch dương -> bạch dương)
  plurals       a genus or broader taxon is often named in the plural (German
                Birken): the singular from Wiktionary's noun forms (plurals.py)
  Latin titles  a Wikipedia title that is the scientific name itself is kept but
                flagged: it may or may not be the language's word
"""

import re
from functools import lru_cache

from ..languages import BY_CODE, CODES, LANGS, WIKI_TO_CODE

META = {"name": "taxon", "license": "CC BY-SA (Wikispecies, Wikipedia, Wiktionary)", "langs": CODES,
        "reliability": "medium"}
WS = "https://species.wikimedia.org/w/api.php"
CODE_OF = {**WIKI_TO_CODE, "zh-hans": "cmn", "zh-cn": "cmn", "zh-hant": "cmn", "zh-tw": "cmn"}
# Rank markers by rank (a marker is removed only when it names the taxon's own
# rank: Korean 서양주목 "European yew" ends in 목, which is part of 주목 "yew", not
# the order marker). Suffixes that tell a one-word taxon's rank (ICN / ICZN).
RANK_SUFFIX = [(r"aceae$|idae$", "family"), (r"oideae$|inae$", "subfamily"), (r"ales$|formes$", "order"),
               (r"eae$|ini$", "tribe")]
RANK_MARKERS = {
    "genus": {"ja": r"(属)$", "cmn": r"(属|屬)$", "ko": r"(속)$", "vi": r"^(chi)\s+"},
    # families: also the family-forming suffixes of Turkish (porsukgiller), German
    # (Eibengewächse), Russian (тисовые) and Persian (سرخداریان)
    "family": {"ja": r"(科)$", "cmn": r"(科)$", "ko": r"(과)$", "vi": r"^(họ)\s+", "tr": r"(giller|gil)$",
               "de": r"(gewächse)$", "ru": r"(овые|евые)$", "fa": r"(یان)$"},
    "subfamily": {"ja": r"(亜科)$", "cmn": r"(亚科|亞科)$", "ko": r"(아과)$", "vi": r"^(phân họ)\s+"},
    "order": {"ja": r"(目)$", "cmn": r"(目)$", "ko": r"(목)$", "vi": r"^(bộ)\s+"},
    "tribe": {"ja": r"(族)$", "cmn": r"(族)$", "ko": r"(족)$", "vi": r"^(tông)\s+"},
}


def rank(taxon):
    """'species' for a binomial (Taxus baccata), 'subspecies' beyond; for one word
    the rank its suffix shows (Taxaceae: family), else 'genus' (Taxus)."""
    words = taxon.split()
    if len(words) == 2:
        return "species"
    if len(words) > 2:
        return "subspecies"
    for rx, r in RANK_SUFFIX:
        if re.search(rx, words[0]):
            return r
    return "genus"


def _template(text, name):
    """Body of the first {{name ...}} in wikitext (braces matched), or ''."""
    m = re.search(r"\{\{\s*" + name + r"\b", text)
    if not m:
        return ""
    depth, i = 0, m.start()
    while i < len(text):
        if text.startswith("{{", i):
            depth += 1
            i += 2
            continue
        if text.startswith("}}", i):
            depth -= 1
            i += 2
            if depth == 0:
                return text[m.end():i - 2]
            continue
        i += 1
    return ""


def _top_split(body):
    """Split a template body at top-level pipes (not inside [[ ]] or {{ }})."""
    parts, depth, cur, i = [], 0, "", 0
    while i < len(body):
        two = body[i:i + 2]
        if two in ("[[", "{{"):
            depth += 1; cur += two; i += 2; continue
        if two in ("]]", "}}"):
            depth -= 1; cur += two; i += 2; continue
        if body[i] == "|" and depth == 0:
            parts.append(cur); cur = ""; i += 1; continue
        cur += body[i]; i += 1
    parts.append(cur)
    return parts


@lru_cache(maxsize=256)
def vernacular_names(taxon):
    """{our language code: [names]} from the Wikispecies page's {{VN}} template."""
    from .wikidata import api_get
    d = api_get(WS, {"action": "parse", "page": taxon, "prop": "wikitext", "redirects": 1})
    text = (d.get("parse") or {}).get("wikitext", "")
    out = {}
    for part in _top_split(_template(text, "VN")):
        kv = re.match(r"\s*([a-z-]+)\s*=\s*(.+?)\s*$", part, re.S)
        if not kv or kv.group(1) not in CODE_OF:
            continue
        code = CODE_OF[kv.group(1)]
        names = re.split(r"\s*(?:,|;|/|<br\s*/?>)\s*", re.sub(r"\[\[([^|\]]*\|)?([^\]]*)\]\]", r"\2", kv.group(2)))
        for n in names:
            n = re.sub(r"<[^>]+>|''+", "", n).strip()
            if n and n not in out.setdefault(code, []):
                out[code].append(n)
    return out


def _clean(code, word, taxon):
    """(word, flags): rank markers off, plurals of broad taxa to the singular."""
    from .. import plurals
    flags = []
    rx = RANK_MARKERS.get(rank(taxon), {}).get(code)
    if rx:
        bare = re.sub(rx, "", word, flags=re.I).strip()
        if bare and bare != word and len(bare) >= 2:
            flags.append(f"{rank(taxon)} marker removed: {word} -> {bare}")
            word = bare
    # vernacular names and article titles are capitalised; common nouns are not
    # (German nouns keep their capital; multi-word names keep theirs: European yew)
    if code != "de" and " " not in word and word[:1].isupper() and not word.isupper():
        word = word[:1].lower() + word[1:]
    if rank(taxon) != "species":
        sg = plurals.singular(code, word)
        if sg:
            flags.append(f"Wikispecies/Wikipedia names the {rank(taxon)} {taxon} in the plural ({word}); "
                         f"singular {sg[0]} (Wiktionary noun forms)")
            word = sg[0]
    return word, flags


def _word(code, word, prov, url, flags, sense=""):
    return {"lang": code, "word": word, "roman": "", "ipa": "", "provenance": [prov], "sense": sense,
            "url": url, "tags": [], "flags": list(flags)}


def _mentions(text, taxon):
    t = taxon.split()[0] if rank(taxon) == "genus or higher" else taxon
    return bool(re.search(rf"\b{re.escape(t)}\b", text or ""))


def gather(concept):
    from . import wiktionary
    from .wikidata import langlinks
    out = []
    for taxon in concept.get("taxa", []):
        taxon = taxon.strip()
        if not taxon:
            continue
        flag0 = f"found by taxon {taxon} ({rank(taxon)})"
        english = set()
        # Wikispecies vernacular names
        for code, names in vernacular_names(taxon).items():
            for n in names:
                w, fl = _clean(code, n, taxon)
                out.append(_word(code, w, f"wikispecies:{taxon}", f"https://species.wikimedia.org/wiki/{taxon.replace(' ', '_')}",
                                 [flag0] + fl))
                if code == "en":
                    english.add(w.lower())
        # Wikipedia interlanguage links of the taxon's article
        _, titles = langlinks("en", taxon)
        for l in LANGS:
            t = titles.get(l["wiki"])
            if not t:
                continue
            from . import strip_disambiguator
            bare = strip_disambiguator(t)
            fl = [flag0]
            if taxon.split()[0].lower() in bare.lower():
                fl.append(f"Wikipedia title is the scientific name ({bare}): check that it is the {l['basa']} word")
            w, more = _clean(l["code"], bare, taxon)
            x = _word(l["code"], w, f"wikipedia:{l['wiki']}:{t} (taxon {taxon})",
                      f"https://{l['wiki']}.wikipedia.org/wiki/{t.replace(' ', '_')}", fl + more)
            if len(fl) > 1:      # the scientific name as a title: no evidence of the language's word
                x["tags"] = ["scientific-name"]
                x["flags"].append("left out by default (tick it to include it)")
            out.append(x)
            if l["code"] == "en":
                english.add(w.lower())
        # English Wiktionary: the senses whose definition names the taxon
        for head in sorted(english):
            for s in wiktionary.senses_for(head):
                if not _mentions(s["definition"], taxon) and not _mentions(s["sense"], taxon):
                    continue
                prov = f"wiktionary:en:{head}/{s['pos']} (definition names {taxon})"
                for code, ts in wiktionary.table("en", head, s["pos"], s["sense"]).items():
                    lang = CODE_OF.get(code) or wiktionary.WIKT_TO_CODE.get(code)
                    if not lang or lang not in BY_CODE:
                        continue
                    for w, rom, tags in ts:
                        if wiktionary.nonstandard(tags):
                            continue
                        for v in wiktionary.split_variants(w):
                            v2, fl = _clean(lang, v, taxon)
                            x = _word(lang, v2, prov, f"https://en.wiktionary.org/wiki/{v2}", [flag0] + fl, s["sense"])
                            x["roman"] = rom if v2 == v else ""     # the table's roman was for the uncleaned word
                            out.append(x)
    # a title that is the scientific name is no candidate when the language has a
    # real word from another source (English taxus beside yew)
    has_word = {w["lang"] for w in out if not any("is the scientific name" in f for f in w["flags"])}
    return [w for w in out if w["lang"] not in has_word or not any("is the scientific name" in f for f in w["flags"])]
