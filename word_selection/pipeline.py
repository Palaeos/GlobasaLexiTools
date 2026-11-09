"""End-to-end: concept -> source table -> clusters -> ranked proposals.
Also the leave-one-out evaluation over existing roots."""

import random

from . import abjad, blend, cluster as clustering, sinosphere, collision, form_rules, lexicon, select, sources, translit, vocalization
from .align import distance, edit_count
from .languages import BY_CODE, CODES

SEV_RANK = {"CLEAR": 0, "NOTE": 0, "CAUTION": 1, "WARN": 2, "BLOCK": 3}
BLENDS_PER_CLUSTER = 8


def _arabic_dictionary(w, context):
    """An unvocalized Arabic word: the Camel Morph vocalization dictionary first, its
    Wiktionary-based forms after it as marked fallbacks."""
    # only a romanization the source gave with this sense (a translation table's) may
    # choose among readings; the entry's first one may belong to another homograph
    roman_form = (w["forms"][0] if w["forms"] and w.get("roman") and not w.get("roman_from") else "")
    got, flag = vocalization.arabic_forms(w["word"], context, roman_form)
    if not got:
        return
    rest = [(f, how if "fallback" in how else f"{how} (fallback: after the vocalization dictionary)")
            for f, how in w["forms_how"] if f not in {g for g, _ in got}]
    w["forms_how"] = got + rest
    w["forms"] = [f for f, _ in w["forms_how"]]
    w["vocalized_by"] = "camel_morph"
    if flag:
        w.setdefault("flags", []).append(flag)


def _persian_dictionary(w):
    """A Persian word: KaamelDict first, Wiktionary-based forms after it as marked
    fallbacks (Wiktionary's reading still picks among the dictionary's variants)."""
    roman_form = w["forms"][0].replace(" ", "") if w["forms"] and w.get("roman") else ""
    got, flag = vocalization.persian_forms(w["word"], roman_form)
    if not got:
        return
    rest = [(f, how if "fallback" in how else f"{how} (fallback: after the vocalization dictionary)")
            for f, how in w["forms_how"] if f not in {g for g, _ in got}]
    w["forms_how"] = got + rest
    w["forms"] = [f for f, _ in w["forms_how"]]
    w["vocalized_by"] = "kaameldict"
    if flag:
        w.setdefault("flags", []).append(flag)


def enrich(words, context=()):
    """Fill roman/ipa/etym/pos from the word's own Wiktionary entry; add Globasa forms.
    context: English words of the concept (to choose among dictionary readings)."""
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
            if w["lang"] == "ar" and not translit.arabic_script(w["word"]):
                _arabic_dictionary(w, context)
            elif w["lang"] == "fa":
                _persian_dictionary(w)
        if w["lang"] in ("cmn", "ja", "ko", "vi"):        # clustering only
            w["han"] = sinosphere.han_spellings(w["lang"], w["word"], (w.get("forms") or [""])[0])
            w["native_reading"] = (w["lang"] == "ja" and not w["han"] and sinosphere.is_han_word(w["word"]))
            w["pivots"] = list(sinosphere.pivots(w["han"][0])) if w["han"] else []
        w["romanized"] = (bool(w.get("roman")) or bool(w.get("vocalized_by"))) and bool(w["forms"])
        if not w["forms"]:
            w.setdefault("flags", []).append("needs romanization")
        if any(p.startswith("wikipedia") for p in w["provenance"]) and len(w["provenance"]) == 1:
            w.setdefault("flags", []).append("Wikipedia title only")
        if len(w["word"].split()) > 2:
            w.setdefault("flags", []).append("multi-word")
    return words


def foreign_reading(lang, word, forms_how, en_form, ipa="", roman=""):
    """A word spelt like an English word (Unix) may be read as in English, or not:
    German says [ˈjuːnɪks], French \\y.niks\\. The language's own pronunciation is
    checked (its entry's IPA, its own Wiktionary edition: pronunciation.py, a
    Turkish table romanization) and replaces the spelling reading when it is closer
    to the English reading than to the spelling reading (a loan read as in English
    or near it); native words that merely look English (German Hand) keep their
    spelling. With no pronunciation found: the language's spelling reading
    (Latin-script languages) or the English reading (a Latin-script spelling in
    another script), as a marked fallback, with the other reading offered too.
    Returns (forms_how, flag or '')."""
    from . import pronunciation
    from .languages import LANGS
    latin = {l["code"] for l in LANGS if l["latin"]}
    basa = BY_CODE[lang]["basa"]
    spelt = [f for f, how in forms_how if how.startswith("spelling")]
    spelling = spelt[0] if spelt else ""
    own, own_how = "", ""
    if ipa:
        own, own_how = translit.ipa_to_globasa(ipa).replace(" ", ""), f"{basa} pronunciation [{ipa}]"
    elif pronunciation.ipa(lang, word):
        p = pronunciation.ipa(lang, word)[0]
        own, own_how = translit.ipa_to_globasa(p).replace(" ", ""), f"{basa} Wiktionary pronunciation [{p}]"
    elif roman and forms_how and "pronunciation" in forms_how[0][1]:
        own, own_how = forms_how[0]
    if own:
        if spelling and distance(own, en_form) < distance(own, spelling):
            return [(own, f"{own_how}: a loan read as in English or near it, not as spelt")] + \
                [(f, h) for f, h in forms_how if f != own], ""
        return forms_how, ""
    if lang in latin:
        if not spelling or spelling == en_form:
            return forms_how, ""
        out = [(f, h if "fallback" in h else f"{h} (fallback: no {basa} pronunciation found)") for f, h in forms_how]
        out.append((en_form, f"as the English word (fallback: no {basa} pronunciation found)"))
        return out, (f"spelt like English {word}, no {basa} pronunciation found: read by {basa} "
                     f"spelling (fallback); the English reading is offered too")
    out = [(en_form, f"as the English word (fallback: Latin-script spelling, no {basa} pronunciation found)")]
    out += [(f, h if "fallback" in h else f"{h} (fallback)") for f, h in forms_how if f != en_form]
    return out, f"written in Latin script in {basa}; no {basa} pronunciation found: read as the English word (fallback)"


def check_meanings(words, concept):
    """sense_fit for every source word: does its own entry attest the concept's
    meaning? A shifted or unattested meaning is flagged and creates no agreement
    (nicode < Hindi निचोड़ना "to extract by squeezing, squeeze out" was replaced by
    bopu < Vietnamese bóp "to press (with hands)")."""
    from . import sense_fit
    if not sense_fit.concept_words(concept)[0]:
        return words              # no English sense to check against (a taxon is its own key)
    for w in words:
        # English words come from the concept itself, except those found by etymology
        if (w["lang"] == "en" and w.get("provenance") != ["etym-cognate"]) or w.get("excluded"):
            continue
        f = sense_fit.fit(w["lang"], w["word"], concept)
        w["sense_fit"] = f
        if f["fit"] == "shifted":
            w.setdefault("flags", []).append(f"meaning shifted in its own entry: \"{f['gloss']}\" (the concept's word "
                                             f"only with a particle or as the means); not counted as agreement")
        if "etym-cognate" in w.get("provenance", []) and len(w["provenance"]) == 1 \
                and f["fit"] in ("homonym", "shifted", "unattested") \
                and (w["lang"], w["word"]) not in {tuple(x) for x in concept.get("included", [])}:
            # a cognate found by etymology whose own entry gives another meaning
            w["excluded"] = True
            w["tags"] = sorted(set(w.get("tags", [])) | {"default-out"})
            w.setdefault("flags", []).append("left out by default: an etymology cognate whose own entry does not "
                                             "carry the meaning (tick it to include it)")
        if f["fit"] == "homonym":
            w.setdefault("flags", []).append(f"another sense of the English word: its own entry says \"{f['gloss']}\" "
                                             f"(as miza leaned on Greek μάζα, physical mass, for the Mass); "
                                             f"not counted as agreement")
        elif f["fit"] == "ambiguous":
            w.setdefault("flags", []).append(f"check which sense: its own entry gives only the English word "
                                             f"(\"{f['gloss'][:60]}\"), which has other senses")
        elif f["fit"] == "unattested":
            w.setdefault("flags", []).append(f"check the meaning: its own entry does not name the concept "
                                             f"(\"{f['gloss'][:80]}\"; a synonym may say the same)")
    return words


def check_foreign_spellings(words, latin_languages=False):
    """foreign_reading() for non-English words spelt in Latin letters that are also
    English words (in the concept, or with an English Wiktionary IPA). In a
    Latin-script language only for proper nouns and culture-specific words
    (latin_languages): for ordinary words Globasa favours the European spelling
    (rum, not ram), and checking every German/French pronunciation cost 4 roots
    (parti, vaselin, sabotaje lost to paati, vaslin, sabotas)."""
    from .languages import LANGS
    from .sources.wiktionary import lookup
    latin = {l["code"] for l in LANGS if l["latin"]}
    english = {w["word"].lower(): w for w in words if w["lang"] == "en" and w.get("forms")}
    for w in words:
        if w["lang"] == "en" or w.get("excluded") or not translit.LATIN.match(w["word"]):
            continue
        if w["lang"] in latin and not latin_languages:
            continue
        en = english.get(w["word"].lower())
        if en:
            en_form = en["forms"][0]
        else:
            info = lookup("en", w["word"])
            en_form = translit.ipa_to_globasa(info["ipa"][0]).replace(" ", "") if info["ipa"] else ""
        if not en_form:
            continue
        fh, flag = foreign_reading(w["lang"], w["word"], w.get("forms_how", []), en_form,
                                   w.get("ipa", ""), w.get("roman", ""))
        w["forms_how"] = fh
        w["forms"] = list(dict.fromkeys(f for f, _ in fh))
        if flag:
            w.setdefault("flags", []).append(flag)
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


def _reading_support(readings, members):
    """For each candidate reading of the source word, the languages whose checked
    form is closest to it and within one phoneme of it."""
    from .align import edit_count
    support = {r: set() for r in readings}
    for m in members:
        if not m["form"] or m.get("fallback"):     # a fallback reading is no evidence
            continue
        d = {r: distance(m["form"], r) for r in readings}
        best = min(d.values())
        near = [r for r in readings if d[r] == best and edit_count(m["form"], r)[0] <= 1]
        if len(near) == 1:
            support[near[0]].add(m["lang"])
    return support


def propose_cultural(info, origin, members, word_class="", exclude=()):
    """Proposals for a proper noun / culture-specific word: the source word's form
    under the grammar's phonotactics for its kind (a proper noun is also offered as
    a culture-specific common noun), not a blend.

    A source in Latin script has two candidate readings: its pronunciation (Unix
    yuniks) and its spelling (uniks; Globasa leans on spelling for Latin-script
    recognizability: rum, not ram). They are ranked by the languages whose checked
    readings match them: loans in other scripts carry the pronunciation (Russian
    Юникс, Arabic يونكس yuniks), Latin-script languages may keep the spelling
    (Spanish, French uniks). On a tie the spelling wins."""
    from . import cultural
    pron = origin["forms"][0].replace(" ", "")
    spelt = next((f.replace(" ", "") for f, how in origin.get("forms_how", []) if how.startswith("spelling")), "")
    readings = [pron] + ([spelt] if spelt and spelt != pron and translit.LATIN.match(origin["word"]) else [])
    support = _reading_support(readings, members)
    order = sorted(readings, key=lambda r: (-len(support[r]), r != spelt))
    basa = BY_CODE[origin["lang"]]["basa"]
    checked = cultural.checked_pronunciations(pron, members)
    differ = [f"{l} {f}" for l, f, ok in checked if not ok]
    head = (f"{'proper noun' if info['kind'] == 'proper' else 'culture-specific word'}: "
            f"form follows {basa} {origin['word']} ({info['why']})")
    out = []
    kinds = [info["kind"]] + (["cultural"] if info["kind"] == "proper" else [])
    for src in order:
        which = "pronunciation" if src == pron else "spelling (Latin-script recognizability)"
        backing = ", ".join(sorted(support[src])) or "no language"
        note = f"{which} reading {src}: matched by {backing}" + (
            f"; other readings: {', '.join(differ)}" if src == pron and differ else "")
        # Methodology, words sourced from English: long vowels follow the pronunciation
        # (Yuta for Utah), so spelt u- read /juː/ is yu-
        if origin["lang"] == "en" and src == pron and src.startswith("yu") and spelt.startswith("u"):
            note += "; methodology (words sourced from English): long vowels follow the pronunciation, as Yuta for Utah"
        for kind in kinds:
            for v in form_rules.shape(src, members, word_class, coda=False, kind=kind)[:1 if kind == "proper" else 2]:
                f = v["form"]
                shown = f[:1].upper() + f[1:] if kind == "proper" else f
                if any(p["form"] == shown for p in out):
                    continue
                rep = collision.check(f, exclude=exclude, kind=kind)
                dists = [{"lang": m["lang"], "word": m.get("word", ""), "form": m["form"],
                          "d": round(distance(f, m["form"], normalized=True), 3), "edits": edit_count(f, m["form"])[0]}
                         for m in members]
                label = "proper noun" if kind == "proper" else "culture-specific word"
                out.append({"form": shown, "kind": kind, "reading": which, "support": sorted(support[src]),
                            "blend": {"form": src, "score": 0.0, "origin": f"{label}: {basa} {origin['word']}",
                                      "notes": [head, note], "closest": None,
                                      "precedent": {"columns": 0, "departs": 0}},
                            "trace": [f"{label} phonotactics (grammar)", f"{which} reading"] + v["trace"],
                            "shape_penalty": round(v["penalty"], 3), "collision": rep, "severity": rep["severity"],
                            "total": round(v["penalty"], 4), "distances": sorted(dists, key=lambda x: x["d"])})
    # proper nouns first, then the culture-specific forms, each in reading order
    return sorted(out, key=lambda p: (p["kind"] != info["kind"], order.index(p["blend"]["form"])))


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


def add_etym_cognates(words, rounds=ETYM_ROUNDS, concept=None):
    """Cognates by shared etymon that no source returned: a word's own etymons
    (borrowings, derivations, inheritance from Sanskrit/Pali), then the other
    source-language words from the same etymon (concept index `etym_reverse`):
    English dukkha / Hindi दुःख -> Telugu దుఃఖము, Indonesian duka (Sanskrit दुःख,
    Pali dukkha); English wu wei -> Mandarin 無為. An etymon in a source language is
    added itself. Flagged for a meaning check: an etymon's descendants can drift.
    Only the etymology of the entries that carry the concept's meaning is followed
    (sense_fit.etymology_for_meaning: English mass the liturgy < missa, not
    physical mass < massa < Greek μᾶζα, the confusion behind Globasa's miza)."""
    from . import sense_fit
    from .concept_index import ETYM_KINDS, INH_FROM
    from .languages import DUMP_TO_CODE
    from .sources.wiktionary import index, lookup
    ix = index()
    present = {(w["lang"], w["word"]) for w in words}
    seen, per_lang, frontier = set(), {}, list(words)
    for _ in range(rounds):          # English dukkha -> Pali dukkha -> Indonesian duka
        etymons = {}                 # -> Sanskrit दुःख -> Hindi दुःख, Telugu దుఃఖము
        for w in frontier:
            etym = (sense_fit.etymology_for_meaning(w["lang"], w["word"], concept) if concept
                    else lookup(w["lang"], w["word"])["etym"])
            for kind, src, term in etym:
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


def run(concept, overrides=None, only_sources=None, progress=None):
    """progress(stage): called at each stage, for a waiting user (the page shows it)."""
    say = progress or (lambda stage: None)
    say("Gathering source words (Wiktionary, Wikidata, Wikispecies, seeds)")
    words, errors = sources.gather(concept, only=only_sources)
    say(f"Following etymologies and Han spellings ({len(words)} words so far)")
    if concept.get("etym_cognates"):   # opt-in (user: not by default): English wu wei brings Mandarin 無為 ...
        add_etym_cognates(words, concept=concept)
    add_han_cognates(words)       # ... which the Han spelling extends to ja, ko, vi
    excluded = {tuple(x) for x in concept.get("excluded", [])}
    included = {tuple(x) for x in concept.get("included", [])}
    for w in words:
        # a taxon's scientific name used as an article title is left out unless ticked
        w["excluded"] = (w["lang"], w["word"]) in excluded or (
            "scientific-name" in w.get("tags", []) and (w["lang"], w["word"]) not in included)
    context = [x for s in concept.get("wikt_senses", []) for x in (s[1], s[3]) if s[0] == "en"]
    context += [w["word"] for w in words if w["lang"] == "en"]
    say(f"Reading pronunciations and vocalizing {len(words)} words")
    enrich(words, context)
    say("Checking each word's meaning in its own dictionary entry")
    check_meanings(words, concept)
    from . import cultural
    culture = cultural.detect(concept, words)
    # proper nouns / culture-specific words: every language's pronunciation is checked
    say("Checking how each language pronounces loans; predicting missing vowels")
    check_foreign_spellings(words, latin_languages=bool(culture))
    predict_vocalizations(words)
    apply_overrides(words, overrides or {})
    items = [dict(w, id=i) for i, w in enumerate(words)
             if not w["excluded"] and (w["forms"] or abjad.skeletons(w["lang"], w["word"]))]
    say(f"Clustering {len(items)} words by sound and spelling")
    clusters = select.rank(clustering.cluster(items))
    word_class = concept.get("word_class", "")
    origin = cultural.origin_member(culture, words) if culture else None
    for k, c in enumerate(clusters):
        say(f"Blending and checking proposals: cluster {k + 1} of {len(clusters)}")
        members = [{"lang": m["lang"], "form": m["forms"][0], "word": m["word"], "pos": m.get("pos", "")}
                   for m in c["members"] if m["forms"]]   # spelling-only members have no form to blend
        c["proposals"] = propose(members, word_class)[:12] if members else []
        for mm, m in zip([m for m in c["members"] if m["forms"]], members):
            m["fallback"] = "fallback" in ((mm.get("forms_how") or [("", "")])[0][1])
        if origin and any(m is origin or (m["lang"], m["word"]) == (origin["lang"], origin["word"])
                          for m in c["members"]):
            # proper noun / culture-specific word: the source's form leads (unless blocked)
            cult = [p for p in propose_cultural(culture, origin, members, word_class) if p["severity"] != "BLOCK"]
            c["cultural"] = dict(culture, form=origin["forms"][0])
            c["proposals"] = (cult + [p for p in c["proposals"] if p["form"] not in {q["form"] for q in cult}])[:12]
        c["existing_roots"] = sorted({r for m in c["members"] for r in lexicon.roots_using(m["lang"], m["word"])})
    say("Ranking clusters by real agreement")
    if any([agreement(c, word_class) for c in clusters]):   # every cluster assessed; re-rank if support changed
        clusters = select.rank(clusters)
    questions = team_questions(clusters)
    return {"words": words, "status": statuses(words, concept.get("no_word", [])),
            "clusters": clusters, "errors": errors, "cultural": culture, "team_questions": questions}


SUPPORT_MAX = 0.30   # a member supports a form within this distance: 95% of LexiliAsel's cited
                     # etymons are (median 0.11; baru ~ beruang 0.21), as the cluster threshold
SUPPORT_BORDER = 0.258   # beyond the 90th percentile: a resemblance at the edge of what roots accept


def _support(form, members):
    """(supporting languages, loose members, unverified members, {borderline lang:
    (label, distance)}) of a form; a language is borderline when its closest member
    lies between SUPPORT_BORDER and SUPPORT_MAX."""
    sup, loose, unver, near = set(), [], [], {}
    for m in members:
        fs = [f.replace(" ", "") for f in m.get("forms") or []]
        if not fs:
            continue
        label = f"{m['lang']} {m['word']} ({fs[0]})"
        if m.get("provenance") == ["etym-cognate"]:      # an unverified guess creates no agreement
            unver.append(label)
        elif (m.get("sense_fit") or {}).get("fit") in ("shifted", "homonym"):
            unver.append(f"{label}: own entry \"{m['sense_fit']['gloss'][:60]}\"")
        else:
            d = min(distance(form, f, normalized=True) for f in fs)
            if d <= SUPPORT_MAX:
                sup.add(m["lang"])
                near[m["lang"]] = min(near.get(m["lang"], (label, 9.0)), (label, round(d, 3)), key=lambda x: x[1])
            else:
                loose.append(label)
    border = {l: v for l, v in near.items() if v[1] > SUPPORT_BORDER}
    return sup, [x for x in loose if x.split()[0] not in sup], unver, border


def agreement(c, word_class=""):
    """Which of a cluster's languages its proposal really stands for: members within
    SUPPORT_MAX of the form (sound decides, not etymology: false friends count, as
    baru < Hindi balu, Indonesian beruang, English bear, German Bär), judged against
    the best proposal only: a blend built to bridge two families
    (zarnar between Arabic zarnab and Persian sorhdar) sits as close to both as
    baru to balu and bear, so distance cannot tell a false pair from a false
    friend, and bridging would manufacture agreement.
    Sets c["support"], c["loose"], c["unverified"]; True if anything was set aside."""
    props = c.get("proposals") or []
    if not props:
        c["support"] = None
        return False
    best = props[0]
    sup, loose, unver, border = _support(best["form"].lower(), c["members"])
    c.update(support=sorted(sup), support_form=best["form"], support_tolerance=SUPPORT_MAX,
             loose=loose, unverified=unver, borderline=border)
    return bool(loose or unver)


def team_questions(clusters):
    """When the winner's agreement rests on a resemblance at the edge of what
    existing roots accept (SUPPORT_BORDER..SUPPORT_MAX) and the ranking changes
    without it, that is the development team's call: both outcomes are returned
    (yew: English yew ~ Korean 주목 as false friends gives yumoke; without them the
    fallback order gives Mandarin 紫杉)."""
    import copy
    if not clusters or not clusters[0].get("borderline"):
        return []
    top = clusters[0]
    border = top["borderline"]
    alt = []
    for i, c in enumerate(clusters):
        a = copy.copy(c)
        a["_i"] = i
        if c.get("support") is not None:
            a["support"] = [l for l in c["support"] if l not in border]
        alt.append(a)
    alt = select.rank(alt)
    if alt[0]["_i"] == 0 and len(alt[0]["families"]) == len(top["families"]):
        return []
    other = clusters[alt[0]["_i"]]
    pairs = ", ".join(f"{lbl} at {d}" for lbl, d in border.values())
    form = (top["proposals"] or [{"form": "?"}])[0]["form"]
    alt_form = (other.get("proposals") or [{"form": "(no proposal)"}])[0]["form"]
    return [{
        "question": f"Do {pairs} resemble {form} closely enough to count as agreement (false friends)?",
        "basis": (f"distance {SUPPORT_BORDER}-{SUPPORT_MAX} is the top 10% of what LexiliAsel's roots accept "
                  f"(baru ~ beruang 0.21 is below it); the methodology leaves such resemblance to judgement"),
        "if_yes": {"cluster": 0, "form": form, "why": top["why"]},
        "if_no": {"cluster": alt[0]["_i"], "form": alt_form, "why": alt[0]["why"]},
    }]


HISTORICAL_HAN = ("ko", "vi")   # Sino-xenic words no longer written in Han characters


def display_han(m, cluster=None):
    """Historical Han spelling to show beside a Korean/Vietnamese word (기질 基質,
    vô vi 無爲), or "". With a cluster, prefer the spellings its other Sinosphere
    members share (the one the word was clustered by)."""
    if m.get("lang") not in HISTORICAL_HAN:
        return ""
    hs = list(m.get("han") if "han" in m else sinosphere.han_spellings(m["lang"], m.get("word", "")))
    if not hs:
        return ""
    if cluster:
        others = set()
        for o in cluster["members"]:
            if o is not m and o["lang"] in ("cmn", "ja", "ko", "vi"):
                others.update(o.get("han") or [])
        shared = [h for h in hs if h in others]
        hs = shared or hs
    return " / ".join(hs)


def lexiliasel(cluster):
    """LexiliAsel string for a cluster, in source-list order. Korean/Vietnamese
    Sino-xenic words carry their historical Han spelling: 기질 基質 “giji”."""
    by = {}
    for m in cluster["members"]:
        by.setdefault(m["lang"], []).append(m)
    parts = []
    for code in CODES:
        if code not in by:
            continue
        items = []
        for m in by[code]:
            word = " ".join(x for x in (m["word"], display_han(m, cluster)) if x)
            if (BY_CODE[code]["latin"] and code != "vi") or not m["forms"]:
                items.append(word)
            else:
                items.append(f"{word} “{m['forms'][0]}”")
        parts.append(f"{BY_CODE[code]['basa']} ({', '.join(dict.fromkeys(items))})")
    return ", ".join(parts)


# ---------------------------------------------------------------------------
# Leave-one-out evaluation
# ---------------------------------------------------------------------------

# Languages whose oracle form is the real pronunciation when there is one (the
# vocalization dictionary, else Wiktionary):
# LexiliAsel's Persian romanizations of European loans read the spelling (کبالت
# kabalat, کازینو kazinu) where Wiktionary has the pronunciation (kobâlt, kâzino).
# Arabic keeps LexiliAsel's: there Wiktionary's first reading is often another
# word of the same spelling (لفظ lafaza for lafẓ) or keeps a case ending.
PRONUNCIATION_ORACLE = {"fa"}
# Latin-script spellings in a non-Latin-script language, spelt like the root's
# English etymon: read by foreign_reading, as the pipeline does (ordinary roots:
# Latin-script languages keep their spelling)
FOREIGN_CHECK = True


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
            got, _ = vocalization.persian_forms(e["word"].lstrip("/ ").strip(), (spoken or "").replace(" ", ""))
            if got:
                spoken = got[0][0]
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
            if e["code"] == "ar" and not translit.arabic_script(e["word"]):
                got, _ = vocalization.arabic_forms(e["word"], [root.get("eng", "")] + [
                    x["word"] for x in root["etymons"] if x["code"] == "en"])
                form = got[0][0] if got else form
            elif e["code"] == "fa":
                got, _ = vocalization.persian_forms(e["word"].lstrip("/ ").strip(), form.replace(" ", "") if (roman or ipa) else "")
                form = got[0][0] if got else form
        if form and FOREIGN_CHECK and e["code"] != "en" and not BY_CODE[e["code"]]["latin"] \
                and translit.LATIN.match(e["word"]) and not e["roman"]:
            en = next((x for x in root["etymons"] if x["code"] == "en"
                       and x["word"].lower() == e["word"].lower()), None)
            if en:
                from .sources.wiktionary import lookup
                ei = lookup("en", en["word"])
                en_form = translit.ipa_to_globasa(ei["ipa"][0]).replace(" ", "") if ei["ipa"] else ""
                if en_form:
                    wi = lookup(e["code"], e["word"])
                    fh = translit.to_globasa(e["code"], e["word"], wi["roman"][0] if wi["roman"] else "",
                                             wi["ipa"][0] if wi["ipa"] else "")
                    fh, _ = foreign_reading(e["code"], e["word"], fh, en_form,
                                            wi["ipa"][0] if wi["ipa"] else "", wi["roman"][0] if wi["roman"] else "")
                    form = fh[0][0] if fh else form
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
