"""English words borrowed or calqued from East Asian languages, and whether Globasa
covers them.

Tier: script (evidence list for vetting; it decides nothing). A borrowing or calque
into English is English admitting a gap (umami, kowtow, brainwash, long time no see);
a concept English took from East Asia that Globasa still lacks is an easy coining
candidate. Idea and method: concept-discovery discussion of 2026-11-21.

Inputs:
  English Wiktionary dump    (word_selection/dump.source('en')), English entries only,
                             streamed: bor/cal/der/... etymology templates whose source
                             is an East Asian language. Not the concept index: its
                             etym_links drops {{bor+|en|ja|-}} links, whose term sits in
                             a following {{ja-r}} (tsunami, karate, sushi; 2026-11-21).
  WiktionaryLMDB_concepts/   etym_reverse only, for the breadth column.
  word-list.csv              Word, TranslationEng, TranslationZho, LexiliAsel.
Coverage, strongest first:
  source  - the East Asian source term appears in a Globasa word's LexiliAsel
            (the word was selected from it: Niponsa (旨味 "umami") -> umami);
  zho     - the source term is in a Globasa word's TranslationZho;
  gloss   - the English headword is one of a Globasa word's English gloss items.
Output:
  concept_discovery/output/english_east_asian_borrowings.tsv  (one row per English
  word + PoS), missing first, then by breadth = how many of the other source
  languages borrowed the same term (concept_index etym_reverse), calques first.
Run:  venv/bin/python concept_discovery/english_east_asian_borrowings.py   (one pass over
      the 21 GB dump, ~20 min; ~0.5 GB)

Limits: only links Wiktionary encodes as templates (paper tiger, lose face have
none); 'der' links can pass through other languages (tea < Min Nan via Malay).
"""

import csv
import os
import re
import sys

import orjson

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from concept_discovery import lexicon
from word_selection import concept_index as ci
from word_selection.dump import open_lines, source

OUT_DIR = os.path.join(REPO, "concept_discovery", "output")
OUT = os.path.join(OUT_DIR, "english_east_asian_borrowings.tsv")

# Wiktionary language codes -> group, by code or code family (nan-hbl, zhx-tai...).
# Sinitic stages and varieties are one group: English often names a Cantonese or
# Min form of a word all of Chinese shares (ketchup < Hokkien 膎汁).
SOURCE_PREFIXES = {
    "Chinese": ("zh", "cmn", "yue", "nan", "hak", "wuu", "hsn", "gan", "cdo", "cpx", "cjy",
                "czh", "mnp", "ltc", "och", "lzh", "zhx", "csp", "cnp"),
    "Japanese": ("ja", "ojp", "jpx", "ryu", "xug"),
    "Korean": ("ko", "okm", "oko"),
    "Vietnamese": ("vi",), "Ainu": ("ain",), "Mongolian": ("mn", "cmg", "xng", "mvf"),
    "Manchu": ("mnc",), "Tibetan": ("bo", "xct", "otb"),
}
_CODE_GROUP = {p: g for g, prefixes in SOURCE_PREFIXES.items() for p in prefixes}


def source_group(code):
    """East Asian group of a Wiktionary language code, or None."""
    return _CODE_GROUP.get(code) or _CODE_GROUP.get(code.split("-")[0])


# Script templates that carry the term when the etymology template has '-'
TERM_TEMPLATES = {"ja-r": "ja", "ja-l": "ja", "ja-def": "ja", "zh-l": "zh", "zh-m": "zh",
                  "ko-l": "ko", "vi-l": "vi", "lang": None, "m": None, "l": None}
DUMP = source("en")
LANG_RE = re.compile(rb'"lang_code": "en"')
# Borrowing kinds, by how directly English took the concept. 'cog' is not a
# borrowing (tycoon is wrongly linked to Cantonese 大班 as a cognate).
CALQUES = {"cal", "calque", "clq", "psm", "sl"}
DIRECT = {"bor", "lbor", "ubor", "slbor", "obor"}
KIND_RANK = {**dict.fromkeys(CALQUES, 0), **dict.fromkeys(DIRECT, 1), "der": 2}
SKIP_POS = {"name", "character", "symbol", "romanization", "abbrev"}
SENSES_SHOWN = 3


def east_asian_links(templates):
    """[(kind, source_lang, term, how)] for East Asian borrowing links, best kind first.
    A '-' term is taken from the next script template ({{bor+|en|ja|-}} {{ja-r|津%波}});
    how = '' or '(fallback: term from {{ja-r}})'."""
    links = []
    for i, t in enumerate(templates or []):
        name, a = t.get("name", "").rstrip("+"), t.get("args", {})
        if name == "etymon":
            continue
        src = a.get("2", "")
        if name not in KIND_RANK or not source_group(src):
            continue
        term, how = a.get("3", "").strip(), ""
        if term in ("", "-"):
            term = ""
            for nxt in templates[i + 1:i + 3]:
                lang = TERM_TEMPLATES.get(nxt.get("name", ""), "?")
                if lang == "?":
                    continue
                args = nxt.get("args", {})
                cand = args.get("2", "") if lang is None and args.get("1") == src else (
                    args.get("1", "") if lang is not None else "")
                cand = cand.replace("%", "").strip()
                if cand:
                    term, how = cand, f"(fallback: term from {{{{{nxt['name']}}}}})"
                    break
        links.append((name, src, term, how))
    return sorted(dict.fromkeys(links), key=lambda link: KIND_RANK[link[0]])


GROUP_CODE = {"Chinese": "zh", "Japanese": "ja", "Korean": "ko", "Vietnamese": "vi"}
# A one-character Middle / Old / Literary Chinese link names a morpheme of the word,
# not the word (waka 和歌 < ltc 和 had matched Mandarin 和 'and' -> ji; 2026-11-21)
MORPHEME_STAGES = {"ltc", "och", "lzh"}


def lookup_code(src):
    return GROUP_CODE.get(source_group(src), src)


def coverage(eng, links, lex):
    """[(how, [Globasa words])]: LexiliAsel source form, Zho column, English gloss."""
    found = {}
    for _, src, term, _ in links:
        if len(term) == 1 and src in MORPHEME_STAGES:
            continue
        for glb, how in lex.covering(lookup_code(src), term).items():
            found.setdefault(glb, how)
    for glb, how in lex.glossed(eng).items():
        found.setdefault(glb, how)
    by_how = {}
    for glb, how in found.items():
        by_how.setdefault(how, []).append(glb)
    return [(how, sorted(by_how[how])) for how in ("source", "zho", "gloss") if how in by_how]


def borrowed_by(idx, links):
    """Other source languages (not English) whose words come from the same East Asian
    terms: the Sprachbund breadth of the borrowing (津波 -> de es fr hi ru sw tr)."""
    langs = set()
    for _, src, term, _ in links:
        for k in lexicon.keys(term, lookup_code(src)):
            langs.update(lang for lang, _ in idx.descendants(src, k))
    langs.discard("en")
    return sorted(langs)


def english_entries():
    """(word, pos, etymology templates, glosses) of English dump entries that have
    an East Asian etymology template, skipping form-of / alt-of senses."""
    with open_lines(DUMP, binary=True) as f:
        for n, line in enumerate(f, 1):
            if n % 2000000 == 0:
                print(f"  {n} dump lines", flush=True)
            if not LANG_RE.search(line):
                continue
            d = orjson.loads(line)
            if d.get("lang_code") != "en" or d.get("pos") in SKIP_POS:
                continue
            links = east_asian_links(d.get("etymology_templates"))
            if not links:
                continue
            glosses = [s["glosses"][-1] for s in d.get("senses", [])
                       if s.get("glosses") and not s.get("form_of") and not s.get("alt_of")]
            if glosses:
                yield d.get("word", ""), d.get("pos", ""), links, glosses


lex = lexicon.load()
print(f"word list: {len(lex.source)} source forms, {len(lex.gloss)} English gloss items", flush=True)

merged = {}      # (eng, pos) -> row; a word's etymology sections merge
idx = ci.ConceptIndex()
for eng, pos, links, glosses in english_entries():
    found = coverage(eng, links, lex)
    kind = links[0][0]
    others = borrowed_by(idx, links)
    row = {
        "eng": eng, "pos": pos,
        "kind": "calque" if kind in CALQUES else ("borrowing" if kind in DIRECT else "derived"),
        "groups": ", ".join(dict.fromkeys(source_group(s) for _, s, _, _ in links)),
        "sources": "; ".join(f"{s}:{t or '?'}{' ' + how if how else ''}" for _, s, t, how in links),
        "status": "covered" if found else "missing",
        "breadth": len(others), "borrowed_by": " ".join(others),
        "glb": "; ".join(f"{how}: {' '.join(words)}" for how, words in found),
        "senses": " | ".join(glosses[:SENSES_SHOWN]),
    }
    old = merged.get((eng, pos))
    if old is None or (row["status"], -row["breadth"]) < (old["status"], -old["breadth"]):
        merged[(eng, pos)] = row
idx.close()
rows = list(merged.values())

kind_order = {"calque": 0, "borrowing": 1, "derived": 2}
rows.sort(key=lambda r: (r["status"] != "missing", -r["breadth"], kind_order[r["kind"]], r["eng"].lower()))
os.makedirs(OUT_DIR, exist_ok=True)
tmp = OUT + ".tmp"
with open(tmp, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t", quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()
    writer.writerows(rows)
os.replace(tmp, OUT)

missing = sum(r["status"] == "missing" for r in rows)
print(f"{len(rows)} English word+PoS borrowed/calqued from East Asia: {missing} missing in Globasa "
      f"-> {os.path.relpath(OUT, REPO)}")
for kind in kind_order:
    part = [r for r in rows if r["kind"] == kind]
    print(f"  {kind}: {len(part)} ({sum(r['status'] == 'missing' for r in part)} missing)")
