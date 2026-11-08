"""Source adapters. Each module provides:

  META = {name, license, langs, reliability}      reliability: "high" | "medium" | "low"
  gather(concept) -> [SourceWord]
  lookup(lang, word) -> {senses, pron, etym}       (optional; used by the dossier)
  concept_ids(concept) -> {qids: [...], cili: [...]}   (optional)

SourceWord = {lang, word, roman, ipa, provenance: [str], sense, url, tags}

A concept = {label, wikt_senses: [[wiki, word, pos, sense]], qids: [...],
             seeds: [[lang, word]], cili: [...]}
Adding a dictionary = adding a module and listing it in REGISTRY.
"""

import importlib

from ..languages import BY_CODE

REGISTRY = ["wiktionary", "wikidata", "seeds"]   # next: "omw", "cedict", "jmdict" (see Dictionary ingest.py)


def modules():
    out = []
    for name in REGISTRY:
        try:
            out.append(importlib.import_module(f"{__name__}.{name}"))
        except ImportError as e:   # optional dictionaries may not be installed
            print(f"[sources] {name} unavailable: {e}")
    return out


def gather(concept, only=None):
    """Union of all sources, merged on (lang, word). Returns (words, errors)."""
    merged, errors = {}, []
    for mod in modules():
        if only and mod.META["name"] not in only:
            continue
        try:
            got = mod.gather(concept)
        except Exception as e:   # one failing source (e.g. offline API) must not sink the rest
            errors.append(f"{mod.META['name']}: {e}")
            continue
        for sw in got:
            if sw["lang"] not in BY_CODE or not sw["word"]:
                continue
            k = (sw["lang"], sw["word"])
            if k in merged:
                m = merged[k]
                m["provenance"] = sorted(set(m["provenance"]) | set(sw["provenance"]))
                for f in ("roman", "ipa", "sense", "url"):
                    m[f] = m.get(f) or sw.get(f, "")
                m["tags"] = sorted(set(m.get("tags", [])) | set(sw.get("tags", [])))
            else:
                merged[k] = {"roman": "", "ipa": "", "sense": "", "url": "", "tags": [], **sw}
    return list(merged.values()), errors
