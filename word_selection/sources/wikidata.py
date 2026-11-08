"""Wikipedia interlanguage links and Wikidata labels for a concept's QIDs.

Labels are preferred to article titles (titles carry disambiguators and are
often technical or multi-word). Aliases are kept at lower priority. Everything
is cached on disk (requests-cache), so repeated lookups are offline.
"""

import os
import re
import time
from functools import lru_cache

import requests

from ..languages import CODES, LANGS, WIKI_TO_CODE

META = {"name": "wikidata", "license": "CC0 (Wikidata) / CC BY-SA (Wikipedia)", "langs": CODES,
        "reliability": "medium"}
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, "word_selection_cache")
UA = "GlobasaLexiTools/word_selector (Globasa lexicography; python-requests)"
WD = "https://www.wikidata.org/w/api.php"
MAX_RETRIES, TIMEOUT = 4, 30
# Wikidata label codes to try per source language (Mandarin: simplified first)
LABEL_CODES = {l["code"]: [l["wiki"]] for l in LANGS}
LABEL_CODES["cmn"] = ["zh-hans", "zh-cn", "zh"]


@lru_cache(maxsize=1)
def session():
    try:
        import requests_cache
        s = requests_cache.CachedSession(CACHE, expire_after=60 * 60 * 24 * 30)
    except ImportError:
        s = requests.Session()
    s.headers["User-Agent"] = UA
    return s


def api_get(endpoint, params):
    """GET with retries for maxlag / 429 / transient errors (as resolve_commons_images.api_get)."""
    params = {"format": "json", "formatversion": 2, "maxlag": 5, **params}
    for attempt in range(MAX_RETRIES):
        try:
            r = session().get(endpoint, params=params, timeout=TIMEOUT)
            if r.status_code in (429, 503):
                time.sleep(2 ** attempt)
                continue
            r.raise_for_status()
            data = r.json()
            if "error" in data and data["error"].get("code") == "maxlag":
                time.sleep(2 ** attempt)
                continue
            return data
        except (requests.RequestException, ValueError):
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(2 ** attempt)
    return {}


def title_to_qid(lang, title):
    """Wikipedia article (any language) -> QID, following redirects."""
    d = api_get(f"https://{lang}.wikipedia.org/w/api.php",
                {"action": "query", "prop": "pageprops", "ppprop": "wikibase_item",
                 "titles": title, "redirects": 1})
    for p in d.get("query", {}).get("pages", []):
        q = p.get("pageprops", {}).get("wikibase_item")
        if q:
            return q
    return None


def search(text, lang="en", limit=8):
    """Wikidata entity search, for the concept builder."""
    d = api_get(WD, {"action": "wbsearchentities", "search": text, "language": lang,
                     "uselang": lang, "limit": limit, "type": "item"})
    return [{"qid": x["id"], "label": x.get("label", ""), "description": x.get("description", "")}
            for x in d.get("search", [])]


def entity(qid):
    langs = sorted({c for cs in LABEL_CODES.values() for c in cs} | {"eo"})
    d = api_get(WD, {"action": "wbgetentities", "ids": qid,
                     "props": "labels|aliases|sitelinks|descriptions|claims",
                     "languages": "|".join(langs), "sitefilter": "|".join(
                         f"{l['wiki']}wiki" for l in LANGS)})
    return d.get("entities", {}).get(qid, {})


def strip_title(t):
    return re.sub(r"\s*[(（][^)）]*[)）]\s*$", "", t).strip()


def langlinks(lang, title):
    """Wikipedia article -> (QID, {lang: title}) via the interlanguage links of
    that article (works without wikidata.org)."""
    d = api_get(f"https://{lang}.wikipedia.org/w/api.php",
                {"action": "query", "prop": "langlinks|pageprops", "titles": title, "lllimit": 500,
                 "redirects": 1, "ppprop": "wikibase_item"})
    pages = d.get("query", {}).get("pages", [])
    if not pages or "missing" in pages[0]:
        return None, {}
    p = pages[0]
    titles = {lang: p["title"]}
    for l in p.get("langlinks", []):
        titles[l["lang"]] = l["title"]
    return p.get("pageprops", {}).get("wikibase_item"), titles


def _from_entity(q, e):
    out = []
    labels, aliases, links = e.get("labels", {}), e.get("aliases", {}), e.get("sitelinks", {})
    for l in LANGS:
        code = l["code"]
        for lc in LABEL_CODES[code]:
            if lc in labels:
                out.append({"lang": code, "word": labels[lc]["value"], "provenance": [f"wikidata-label:{q}"],
                            "url": f"https://www.wikidata.org/wiki/{q}"})
                break
        for lc in LABEL_CODES[code]:
            for a in aliases.get(lc, [])[:2]:
                out.append({"lang": code, "word": a["value"], "provenance": [f"wikidata-alias:{q}"],
                            "url": f"https://www.wikidata.org/wiki/{q}", "tags": ["alias"]})
        sl = links.get(f"{l['wiki']}wiki")
        if sl:
            out.append(_title_word(code, l["wiki"], sl["title"]))
    return out


def _title_word(code, wiki, title):
    return {"lang": code, "word": strip_title(title), "provenance": [f"wikipedia:{wiki}"],
            "url": f"https://{wiki}.wikipedia.org/wiki/{title.replace(' ', '_')}"}


def gather(concept):
    """QIDs -> Wikidata labels/aliases + Wikipedia titles; articles -> interlanguage titles.
    If wikidata.org is unreachable, articles still work through Wikipedia alone."""
    out, errors = [], []
    for q in concept.get("qids", []):
        try:
            e = entity(q)
        except requests.RequestException as ex:
            errors.append(f"wikidata.org unreachable for {q} ({type(ex).__name__})")
            continue
        if e:
            out += _from_entity(q, e)
    for lang, title in concept.get("articles", []):
        _, titles = langlinks(lang, title)
        for l in LANGS:
            if l["wiki"] in titles:
                out.append(_title_word(l["code"], l["wiki"], titles[l["wiki"]]))
    if errors and not out:
        raise RuntimeError("; ".join(errors))
    return out


def concept_info(qid):
    """For the dossier: description, image (P18), Esperanto label, opening sentences."""
    e = entity(qid)
    if not e:
        return {}
    desc = {k: v["value"] for k, v in e.get("descriptions", {}).items()}
    img = None
    for c in e.get("claims", {}).get("P18", [])[:1]:
        img = c.get("mainsnak", {}).get("datavalue", {}).get("value")
    info = {"qid": qid, "descriptions": desc, "image": img,
            "image_url": f"https://commons.wikimedia.org/wiki/Special:FilePath/{img.replace(' ', '_')}?width=320" if img else None,
            "eo_label": e.get("labels", {}).get("eo", {}).get("value"), "leads": {}}
    for lang in ("en", "fa", "ja", "ar"):
        sl = e.get("sitelinks", {}).get(f"{lang}wiki")
        if not sl:
            continue
        try:
            d = api_get(f"https://{lang}.wikipedia.org/w/api.php",
                        {"action": "query", "prop": "extracts", "exsentences": 2, "explaintext": 1,
                         "titles": sl["title"], "redirects": 1})
            pages = d.get("query", {}).get("pages", [])
            if pages and pages[0].get("extract"):
                info["leads"][lang] = pages[0]["extract"]
        except requests.RequestException:
            pass
    return info
