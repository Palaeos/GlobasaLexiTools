"""End-to-end: concept -> source table -> clusters -> ranked proposals.
Also the leave-one-out evaluation over existing roots."""

import random

from . import abjad, blend, cluster as clustering, sinosphere, collision, form_rules, lexicon, select, sources, translit
from .align import distance, edit_count
from .languages import BY_CODE, CODES

SEV_RANK = {"CLEAR": 0, "NOTE": 0, "CAUTION": 1, "WARN": 2, "BLOCK": 3}
BLENDS_PER_CLUSTER = 8


def enrich(words):
    """Fill roman/ipa/etym/pos from the word's own Wiktionary entry; add Globasa forms."""
    from .sources import wiktionary
    for w in words:
        info = wiktionary.lookup(w["lang"], w["word"])
        if not w.get("roman") and info["roman"]:
            w["roman"] = info["roman"][0]
            w["roman_from"] = info["roman_from"]
            if info["roman_from"] == "table":
                w.setdefault("flags", []).append("romanization from a translation table "
                                                 "(fallback: the word's entry gives none)")
        if not w.get("ipa") and info["ipa"]:
            w["ipa"] = info["ipa"][0]
        w["etym"] = info["etym"]
        w["pos"] = w.get("pos") or (info["senses"][0]["pos"] if info["senses"] else "")
        w["lang_dump"] = BY_CODE[w["lang"]]["dump"]
        if not w.get("forms"):
            try:
                w["forms_how"] = translit.to_globasa(w["lang"], w["word"], w.get("roman", ""), w.get("ipa", ""))
            except Exception as e:   # a romanizer library failing must not sink the table
                w["forms_how"] = []
                w.setdefault("flags", []).append(f"transliteration failed: {e}")
            if w.get("roman_from") == "table":
                w["forms_how"] = [(f, "translation-table roman (fallback)" if how == "roman" else how)
                                  for f, how in w["forms_how"]]
            w["forms"] = [f for f, _ in w["forms_how"]]
        if w["lang"] in ("cmn", "ja", "ko", "vi"):        # clustering only
            w["han"] = sinosphere.han_spellings(w["lang"], w["word"], (w.get("forms") or [""])[0])
            w["native_reading"] = (w["lang"] == "ja" and not w["han"] and sinosphere.is_han_word(w["word"]))
            w["pivots"] = list(sinosphere.pivots(w["han"][0])) if w["han"] else []
        w["romanized"] = bool(w.get("roman")) and bool(w["forms"])
        if not w["forms"]:
            w.setdefault("flags", []).append("needs romanization")
        if any(p.startswith("wikipedia") for p in w["provenance"]) and len(w["provenance"]) == 1:
            w.setdefault("flags", []).append("Wikipedia title only")
        if len(w["word"].split()) > 2:
            w.setdefault("flags", []).append("multi-word")
    return words


def predict_vocalizations(words):
    """An Arabic or Persian word with no romanization takes readings predicted from a
    romanized word of the other language with the same spelling (abjad.predict_all:
    vowel length carries the correspondence; Arabic i/u ~ Persian e/o); failing
    that, from a cognate in another script that fits its spelling
    (abjad.vocalize_from_cognates: Turkish akademi -> آکادمی akademi)."""
    for w in words:
        if w["lang"] not in abjad.LANGS or w.get("romanized") or w.get("excluded"):
            continue
        sk = set(abjad.skeletons(w["lang"], w["word"]))
        preds, how = [], []
        for p in words:
            if p["lang"] in abjad.LANGS and p["lang"] != w["lang"] and p.get("romanized") \
                    and sk & set(abjad.skeletons(p["lang"], p["word"])):
                got = abjad.predict_all(p["lang"], p["word"], [p["roman"]], w["lang"], w["word"])
                if not got and p["forms"]:
                    one = abjad.predict(p["lang"], p["word"], p["forms"][0], w["lang"], w["word"])
                    got = [one] if one else []
                for f in got:
                    if f not in preds:
                        preds.append(f)
                        how.append((f, f"predicted from {BY_CODE[p['lang']]['basa']} {p['word']}"))
        if preds:
            w["forms"] = preds + [f for f in w["forms"] if f not in preds]
            w["forms_how"] = how + [x for x in w.get("forms_how", []) if x[0] not in preds]
            w.setdefault("flags", []).append("vocalization predicted from the "
                                             + ("Persian" if w["lang"] == "ar" else "Arabic")
                                             + " spelling (fallback: no romanization)")
            w["flags"] = [f for f in w["flags"] if f != "needs romanization"]
        elif not w.get("forms"):
            # no same-spelling partner: a cognate in another script (Turkish akademi
            # -> آکادمی) supplies the unwritten vowels, if it fits the spelling
            partners = {}
            for p in words:
                if p["lang"] in abjad.COGNATE_LANGS and p.get("forms") and not p.get("excluded"):
                    partners.setdefault((p["lang"], p["forms"][0]), p)
            got = abjad.vocalize_from_cognates(w["lang"], w["word"], list(partners))
            if got:
                form, cost, code = got
                src = next(p for (c, f), p in partners.items() if c == code)
                w["forms"] = [form]
                w["forms_how"] = [(form, f"vowels from {BY_CODE[code]['basa']} {src['word']} "
                                         f"(fallback, fit {cost})")]
                w.setdefault("flags", []).append(f"vocalization predicted from {BY_CODE[code]['basa']} "
                                                 f"{src['word']} (fallback: no romanization and no "
                                                 f"same-spelling Arabic/Persian partner); check it")
                w["flags"] = [f for f in w["flags"] if f != "needs romanization"]
    return words


def apply_overrides(words, overrides):
    """overrides: {"lang\\tword": "form"} (user-edited Globasa renderings)."""
    for w in words:
        k = f"{w['lang']}\t{w['word']}"
        if k in overrides and overrides[k]:
            w["forms"] = [overrides[k]] + [f for f in w["forms"] if f != overrides[k]]
            w.setdefault("flags", []).append("hand-edited rendering")
    return words


def statuses(words, no_word=()):
    have = {w["lang"] for w in words if not w.get("excluded")}
    return {c: ("found" if c in have else "no word" if c in no_word else "no data") for c in CODES}


def propose(members, word_class="", exclude=(), exclude_root=None):
    """Blend + shape + collision-check one cluster. members: [{lang, form, word, pos}].
    exclude_root: leave that root out of the LexiliAsel precedent (evaluation)."""
    out = {}
    for i, b in enumerate(blend.candidates(members, exclude_root=exclude_root)[:BLENDS_PER_CLUSTER]):
        for v in form_rules.shape(b["form"], members, word_class, coda=(i == 0)):
            f = v["form"]
            if f in out:
                continue
            rep = collision.check(f, exclude=exclude)
            n_pairs = len(rep["minimal_pairs"])
            total = b["score"] + v["penalty"] + 0.03 * min(n_pairs, 10)
            dists = []
            for m in members:
                n, close = edit_count(f, m["form"])
                dists.append({"lang": m["lang"], "word": m.get("word", ""), "form": m["form"],
                              "d": round(distance(f, m["form"], normalized=True), 3), "edits": n})
            out[f] = {"form": f, "blend": b, "trace": v["trace"], "shape_penalty": round(v["penalty"], 3),
                      "collision": rep, "severity": rep["severity"], "total": round(total, 4),
                      "distances": sorted(dists, key=lambda x: x["d"])}
    return sorted(out.values(), key=lambda p: (SEV_RANK[p["severity"]], p["total"]))


def add_han_cognates(words):
    """Sinosphere cognates by Han spelling that no source returned: a Mandarin seed
    基質 brings Japanese 基質 (kishitsu) and Korean 기질, if the dictionaries attest
    them in those languages. Compounds only (2+ characters); flagged for a meaning
    check (手紙 is "letter" in Japanese, "toilet paper" in Mandarin)."""
    sino = ("cmn", "ja", "ko", "vi")
    spellings = [(w, sinosphere.han_spellings(w["lang"], w["word"])) for w in words if w["lang"] in sino]
    langs_of = {}
    for w, sps in spellings:
        for sp in sps:
            langs_of.setdefault(sp, set()).add(w["lang"])
    have = {}
    for w, sps in spellings:
        # a Korean / Vietnamese homograph (기질: 氣質, 器質, 基質) passes on only the
        # spellings another language in the concept confirms (Mandarin 基質)
        if len(sps) > 1:
            sps = [sp for sp in sps if langs_of[sp] - {w["lang"]}]
        for sp in sps:
            have.setdefault(sp, {}).setdefault(w["lang"], w["word"])
    present = {(w["lang"], w["word"]) for w in words}
    added = []
    for sp, by_lang in have.items():
        if len(sp) < 2:
            continue
        src_lang, src_word = next(iter(by_lang.items()))
        for lang in sino:
            if lang in by_lang:
                continue
            for word in sinosphere.words_spelled(sp, lang):
                if (lang, word) not in present:
                    present.add((lang, word))
                    added.append({"lang": lang, "word": word, "roman": "", "ipa": "", "sense": "", "url": "",
                                  "tags": [], "provenance": ["han-cognate"],
                                  "flags": [f"same Han spelling as {BY_CODE[src_lang]['basa']} {src_word} "
                                            f"({sp}); check the meaning"]})
    words.extend(added)
    return words


MAX_DESCENDANTS = 40     # an etymon with more source-language descendants is too generic
MAX_PER_LANG = 3


ETYM_ROUNDS = 2          # a cognate's own etymons are followed once more


def add_etym_cognates(words, rounds=ETYM_ROUNDS):
    """Cognates by shared etymon that no source returned: a word's own etymons
    (borrowings, derivations, inheritance from Sanskrit/Pali), then the other
    source-language words from the same etymon (concept index `etym_reverse`):
    English dukkha / Hindi दुःख -> Telugu దుఃఖము, Indonesian duka (Sanskrit दुःख,
    Pali dukkha); English wu wei -> Mandarin 無為. An etymon in a source language is
    added itself. Flagged for a meaning check: an etymon's descendants can drift."""
    from .concept_index import ETYM_KINDS, INH_FROM
    from .languages import DUMP_TO_CODE
    from .sources.wiktionary import index, lookup
    ix = index()
    present = {(w["lang"], w["word"]) for w in words}
    seen, per_lang, frontier = set(), {}, list(words)
    for _ in range(rounds):          # English dukkha -> Pali dukkha -> Indonesian duka
        etymons = {}                 # -> Sanskrit दुःख -> Hindi दुःख, Telugu దుఃఖము
        for w in frontier:
            for kind, src, term in lookup(w["lang"], w["word"])["etym"]:
                if src.endswith("-pro") or not term or (src, term) in seen:
                    continue
                if kind in ETYM_KINDS or (kind == "inh" and src in INH_FROM):
                    etymons.setdefault((src, term), f"{BY_CODE[w['lang']]['basa']} {w['word']}")
        seen |= set(etymons)
        added = _etym_round(ix, etymons, present, per_lang, DUMP_TO_CODE)
        if not added:
            break
        words.extend(added)
        frontier = added
    return words


def _etym_round(ix, etymons, present, per_lang, DUMP_TO_CODE):
    added = []
    for (src, term), via in etymons.items():
        desc = ix.descendants(src, term)
        if len(desc) > MAX_DESCENDANTS:
            continue
        cands = ([[src, term]] if src in DUMP_TO_CODE else []) + desc
        for dl, word in cands:
            code = DUMP_TO_CODE.get(dl)
            if not code or code not in BY_CODE or (code, word) in present:
                continue
            if per_lang.get((src, term, code), 0) >= MAX_PER_LANG:
                continue
            per_lang[(src, term, code)] = per_lang.get((src, term, code), 0) + 1
            present.add((code, word))
            added.append({"lang": code, "word": word, "roman": "", "ipa": "", "sense": "", "url": "",
                          "tags": [], "provenance": ["etym-cognate"],
                          "flags": [f"shares the etymon {src} {term} with {via}; check the meaning"]})
    return added


def run(concept, overrides=None, only_sources=None):
    words, errors = sources.gather(concept, only=only_sources)
    add_etym_cognates(words)      # first: English wu wei brings Mandarin 無為 ...
    add_han_cognates(words)       # ... which the Han spelling extends to ja, ko, vi
    excluded = {tuple(x) for x in concept.get("excluded", [])}
    for w in words:
        w["excluded"] = (w["lang"], w["word"]) in excluded
    enrich(words)
    predict_vocalizations(words)
    apply_overrides(words, overrides or {})
    items = [dict(w, id=i) for i, w in enumerate(words)
             if not w["excluded"] and (w["forms"] or abjad.skeletons(w["lang"], w["word"]))]
    clusters = select.rank(clustering.cluster(items))
    word_class = concept.get("word_class", "")
    for c in clusters:
        members = [{"lang": m["lang"], "form": m["forms"][0], "word": m["word"], "pos": m.get("pos", "")}
                   for m in c["members"] if m["forms"]]   # spelling-only members have no form to blend
        c["proposals"] = propose(members, word_class)[:12] if members else []
        c["existing_roots"] = sorted({r for m in c["members"] for r in lexicon.roots_using(m["lang"], m["word"])})
    return {"words": words, "status": statuses(words, concept.get("no_word", [])),
            "clusters": clusters, "errors": errors}


def lexiliasel(cluster):
    """LexiliAsel string for a cluster, in source-list order."""
    by = {}
    for m in cluster["members"]:
        by.setdefault(m["lang"], []).append(m)
    parts = []
    for code in CODES:
        if code not in by:
            continue
        items = []
        for m in by[code]:
            if (BY_CODE[code]["latin"] and code != "vi") or not m["forms"]:
                items.append(m["word"])
            else:
                items.append(f"{m['word']} “{m['forms'][0]}”")
        parts.append(f"{BY_CODE[code]['basa']} ({', '.join(dict.fromkeys(items))})")
    return ", ".join(parts)


# ---------------------------------------------------------------------------
# Leave-one-out evaluation
# ---------------------------------------------------------------------------

# Languages whose oracle form is the Wiktionary pronunciation when there is one:
# LexiliAsel's Persian romanizations of European loans read the spelling (کبالت
# kabalat, کازینو kazinu) where Wiktionary has the pronunciation (kobâlt, kâzino).
# Arabic keeps LexiliAsel's: there Wiktionary's first reading is often another
# word of the same spelling (لفظ lafaza for lafẓ) or keeps a case ending.
PRONUNCIATION_ORACLE = {"fa"}


def _members_for_root(root, mode, ix):
    members, formless = [], []
    for e in root["etymons"]:
        if e["code"] not in BY_CODE:
            continue
        spoken = None
        if mode == "oracle" and e["code"] in PRONUNCIATION_ORACLE:
            from .sources.wiktionary import lookup
            info = lookup(e["code"], e["word"].lstrip("/ ").strip())
            if info["roman"] or info["ipa"]:
                fs = translit.to_globasa(e["code"], e["word"], info["roman"][0] if info["roman"] else "",
                                         info["ipa"][0] if info["ipa"] else "")
                spoken = fs[0][0] if fs else None
        form_from = "wiktionary pronunciation"
        if spoken:
            form = spoken
        elif mode == "oracle" and e["roman"]:
            form = translit.clean(e["roman"])
            form_from = ("LexiliAsel romanization (fallback: no Wiktionary pronunciation)"
                         if e["code"] in PRONUNCIATION_ORACLE else "LexiliAsel romanization")
        else:
            from .sources.wiktionary import lookup
            info = lookup(e["code"], e["word"])
            roman = info["roman"][0] if info["roman"] else ""
            ipa = info["ipa"][0] if info["ipa"] else ""
            try:
                fs = translit.to_globasa(e["code"], e["word"], roman, ipa)
            except Exception:
                fs = []
            form = fs[0][0] if fs else ""
        if form:
            members.append({"lang": e["code"], "form": form.replace(" ", ""), "word": e["word"], "pos": "",
                            "form_from": form_from if mode == "oracle" else "transliteration"})
        elif mode != "oracle" and e["code"] in abjad.LANGS:
            formless.append(e)
    for e in formless:            # as predict_vocalizations: vowels from a fitting cognate
        got = abjad.vocalize_from_cognates(e["code"], e["word"], [(m["lang"], m["form"]) for m in members])
        if got:
            members.append({"lang": e["code"], "form": got[0], "word": e["word"], "pos": "",
                            "form_from": f"vowels from {got[2]} cognate (fallback)"})
    return members


def evaluate_roots(mode="oracle", n=None, seed=0, verbose=True):
    from .concept_index import ConceptIndex
    ix = ConceptIndex()
    roots = [r for r in lexicon.roots() if sum(e["code"] in BY_CODE for e in r["etymons"]) >= 2
             and r["word"].isalpha() and r["word"].islower()]
    random.Random(seed).shuffle(roots)
    if n:
        roots = roots[:n]
    words = lexicon.words()
    top1 = top5 = 0
    dsum = 0.0
    misses = []
    for r in roots:
        gold = r["word"]
        members = _members_for_root(r, mode, ix)
        if len(members) < 2:
            continue
        exclude = {w for w in words if w.startswith(gold)}
        props = propose(members, r["cls"], exclude=exclude, exclude_root=gold)
        forms = [p["form"] for p in props]
        if forms and forms[0] == gold:
            top1 += 1
        if gold in forms[:5]:
            top5 += 1
        if forms:
            dsum += distance(forms[0], gold)
        if forms[:1] != [gold]:
            misses.append((gold, forms[:5], [m["form"] for m in members]))
    total = len(roots)
    print(f"mode={mode}  roots={total}  top1={top1 / total:.1%}  top5={top5 / total:.1%}  "
          f"mean dist(top1, gold)={dsum / total:.2f}")
    if verbose:
        for gold, forms, srcs in misses[:40]:
            print(f"  {gold:12} got {', '.join(forms):50}  src {' '.join(srcs)}")
    return {"top1": top1 / total, "top5": top5 / total, "n": total}
