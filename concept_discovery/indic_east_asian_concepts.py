"""Indian concepts attested in Hindi and Telugu and loaned into East Asian languages,
and whether Globasa covers them.

Tier: script (evidence list for vetting; it decides nothing). Request of 2026-11-21:
concepts of Indian origin that both an Indo-Aryan (Hindi) and a Dravidian (Telugu)
language use, and that reached China, Japan, Korea or Vietnam (mostly with Buddhism:
涅槃 nirvana, 劫 kalpa, 阿羅漢 arhat; some modern, ヨガ yoga). Non-Abrahamic concepts on
the same footing as Abrahamic ones (project-religious-parity memory).

Method: for every Sanskrit / Pali / Prakrit etymon in the concept index's reverse
etymology table (Wiktionary bor/der/inh/... links), the source languages descending
from it. A row needs a Hindi or Telugu descendant and an East Asian one. Multi-character
Han spellings of the Chinese / Japanese words add their Sino-Xenic counterparts
(sinosphere.words_spelled), shown apart as via_han.
  tier   hi+te   both Hindi and Telugu attest it (the request);
         hi+te (by spelling)  one has the Wiktionary link, the other an entry spelt
                             like the Sanskrit etymon (tatsama; labelled fallback:
                             English Wiktionary has few Telugu etymology links);
         hi only / te only
  route  Han     an East Asian form is Han-spelt (classical, mostly Buddhist);
         modern  only kana / Hangul / Latin forms (ヨガ, 카르마)
Coverage (concept_discovery/lexicon.py): a descendant form in a Globasa word's
LexiliAsel or Zho column, or an English descendant as a gloss item. covered = one
Globasa word matched through two or more languages; possible = through one only.

Inputs:  WiktionaryLMDB_concepts/ (etym_reverse, entries), word_selection_cache/
         sinosphere.json, word-list.csv.
Output:  concept_discovery/output/indic_east_asian_concepts.tsv  (missing first,
         hi+te first, then by number of East Asian languages and of all languages).
Limits:  the reverse table inherits the concept index's gap: links written
         {{bor|..|sa|-}} + a script template have no term and are not indexed.
         Etymons are matched by spelling: Sanskrit and Pali forms of one word
         (nirvāṇa / nibbāna) stay separate rows.
Run:     venv/bin/python concept_discovery/indic_east_asian_concepts.py
"""

import csv
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from concept_discovery import lexicon
from word_selection import concept_index as ci, sinosphere

OUT_DIR = os.path.join(REPO, "concept_discovery", "output")
OUT = os.path.join(OUT_DIR, "indic_east_asian_concepts.tsv")

INDIC = {"sa": "Sanskrit", "pi": "Pali", "pra": "Prakrit", "inc-pra": "Prakrit",
         "inc-mid": "Middle Indo-Aryan", "pgd": "Gandhari", "inc-ash": "Ashokan Prakrit"}
INDIAN = ("hi", "te")
EAST_ASIAN = ("zh", "ja", "ko", "vi")
# sinosphere's language codes for the Han-spelling lookups
SINO_CODE = {"zh": "cmn", "ja": "ja", "ko": "ko", "vi": "vi"}
TIER_ORDER = {"hi+te": 0, "hi+te (by spelling)": 1, "hi only": 2, "te only": 3}
# Telugu tatsama nouns: stem + -ం / -ము (ధ్యానం, ధ్యానము) or -ుడు (ఆచార్యుడు)
TELUGU_ENDINGS = ("", "ం", "ము", "ుడు")
TELUGU_NASAL_CLUSTER = re.compile("[ఙఞణనమ]్(?=[క-హ])")
STATUS_ORDER = {"missing": 0, "possible": 1, "covered": 2}
MIN_COVER_LANGS = 2


def is_kana_or_hangul_only(word):
    return all("぀" <= c <= "ヿ" or "가" <= c <= "힯" or c in "ー・ " for c in word)


def han_counterparts(direct):
    """{lang: [word]} Sino-Xenic words sharing a multi-character Han spelling with the
    directly attested Chinese / Japanese / Korean / Vietnamese words."""
    spellings = set()
    for lang, words in direct.items():
        for w in words:
            spellings.update(s for s in sinosphere.han_spellings(SINO_CODE[lang], w) if len(s) > 1)
    out = {}
    for lang in EAST_ASIAN:
        found = [w for s in sorted(spellings) for w in sinosphere.words_spelled(s, SINO_CODE[lang])]
        found = [w for w in dict.fromkeys(found) if w not in direct.get(lang, [])]
        if found:
            out[lang] = found
    return out


def route(direct):
    """Han if any East Asian descendant has a Han spelling (劫 included), else modern."""
    han = any(sinosphere.han_spellings(SINO_CODE[lang], w) for lang, words in direct.items()
              for w in words if not is_kana_or_hangul_only(w) or lang in ("ko", "vi"))
    return "Han" if han else "modern"


def telugu_spellings(sanskrit):
    """Telugu spellings of a Sanskrit (Devanagari) form: the Unicode blocks share
    their layout; a nasal before a consonant is written ం (మంత్ర), final -ā drops
    (ప్రజ్ఞ)."""
    tel = "".join(chr(ord(c) + 0x300) if "\u0900" <= c <= "\u097f" and c not in "।॥" else c
                  for c in sanskrit)
    stems = {tel, TELUGU_NASAL_CLUSTER.sub("ం", tel)}
    stems |= {st[:-1] for st in stems if st.endswith("ా")}
    return [st + end for st in sorted(stems) for end in TELUGU_ENDINGS]


def by_spelling(idx, src, term, lang):
    """(fallback: tatsama by spelling) a Hindi or Telugu entry spelt like the Sanskrit
    etymon, when Wiktionary has no etymology link (its Telugu links are few)."""
    if src != "sa":
        return []
    forms = [term] if lang == "hi" else telugu_spellings(term)
    return [f for f in forms if idx.entries(lang, f)][:2]


def first_gloss(idx, by_lang):
    for lang in ("hi", "te", "zh", "ja", "en"):
        for w in by_lang.get(lang, []):
            for entry in idx.entries(lang, w):
                if entry["senses"]:
                    return entry["pos"], entry["senses"][0]["g"][-1]
    return "", ""


def coverage(by_lang, lex):
    """{Globasa word: [(how, lang)]}. One language's form alone is weak evidence:
    descendants drift (Hindi चक्कर 'whirl' < cakra) and forms coincide (Indonesian
    seri < śrī = seri 'series' in serye's LexiliAsel); 2026-11-21."""
    found = {}
    for lang, words in by_lang.items():
        for w in words:
            for glb, how in lex.covering(lang, w).items():
                found.setdefault(glb, set()).add((how, lang))
            if lang == "en":
                for glb in lex.glossed(w):
                    found.setdefault(glb, set()).add(("gloss", "en"))
    return found


def status(found):
    """covered: some Globasa word is matched through >= MIN_COVER_LANGS languages,
    the East Asian ones counting once (a shared Han spelling is one piece of evidence:
    梵語 'Sanskrit' < brahman matched Sanskritam in zh and ja); possible: through one
    only (shown, but the gap stays open); missing."""
    best = max((len({"east_asian" if lang in EAST_ASIAN else lang for _, lang in ev})
                 for ev in found.values()), default=0)
    return "covered" if best >= MIN_COVER_LANGS else ("possible" if best else "missing")


def indic_etymons(idx):
    with idx.env.begin() as txn:
        for k, v in txn.cursor(db=idx.dbs["etym_reverse"]):
            src, term = k.decode("utf-8").split("\x00", 1)
            if src in INDIC:
                yield src, term, ci.unpack(v)


lex = lexicon.load()
idx = ci.ConceptIndex()
rows = []
for src, term, refs in indic_etymons(idx):
    by_lang = {}
    for lang, word in refs:
        by_lang.setdefault(lang, []).append(word)
    indian = [l for l in INDIAN if l in by_lang]
    direct = {l: by_lang[l] for l in EAST_ASIAN if l in by_lang}
    if not indian or not direct:
        continue
    spelled = {}
    if len(indian) == 1:
        other = "te" if indian == ["hi"] else "hi"
        found_forms = by_spelling(idx, src, term, other)
        if found_forms:
            spelled[other] = found_forms
    via = han_counterparts(direct)
    all_langs = set(by_lang) | set(via)
    found = coverage({**by_lang, **{l: by_lang.get(l, []) + w for l, w in via.items()}}, lex)
    pos, gloss = first_gloss(idx, by_lang)
    rows.append({
        "etymon": f"{src}:{term}", "pos": pos,
        "tier": "hi+te" if len(indian) == 2 else ("hi+te (by spelling)" if spelled else f"{indian[0]} only"),
        "route": route(direct),
        "east_asian": " ".join(l for l in EAST_ASIAN if l in direct or l in via),
        "n_east_asian": sum(l in direct or l in via for l in EAST_ASIAN),
        "n_langs": len(all_langs),
        "status": status(found),
        "glb": "; ".join(f"{glb} ({', '.join(f'{h} {l}' for h, l in sorted(ev))})"
                         for glb, ev in sorted(found.items(), key=lambda kv: -len(kv[1]))),
        **{l: " ".join(by_lang.get(l, []) or [f"{w} (fallback: tatsama by spelling)" for w in spelled.get(l, [])])
           for l in INDIAN},
        **{l: " ".join(direct.get(l, [])) for l in EAST_ASIAN},
        "via_han": "; ".join(f"{l}: {' '.join(w)}" for l, w in via.items()),
        "others": " ".join(sorted(all_langs - set(INDIAN) - set(EAST_ASIAN))),
        "gloss": gloss,
    })
idx.close()

rows.sort(key=lambda r: (STATUS_ORDER[r["status"]], r["pos"] == "name", TIER_ORDER[r["tier"]],
                         -r["n_east_asian"], -r["n_langs"], r["etymon"]))
os.makedirs(OUT_DIR, exist_ok=True)
tmp = OUT + ".tmp"
with open(tmp, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
    writer.writeheader()
    writer.writerows(rows)
os.replace(tmp, OUT)

print(f"{len(rows)} Indic etymons with a Hindi/Telugu and an East Asian descendant "
      f"-> {os.path.relpath(OUT, REPO)}")
for tier in TIER_ORDER:
    part = [r for r in rows if r["tier"] == tier]
    print(f"  {tier}: {len(part)} ({sum(r['status'] == 'missing' for r in part)} missing, "
          f"{sum(r['status'] == 'possible' for r in part)} possible, "
          f"{sum(r['route'] == 'Han' for r in part)} via Han)")
