#!/usr/bin/env python3
"""Globasa candidates for a source-side lemma table.

    python3 build_glb_candidates.py LEMMA_TABLE.tsv [--wordlist word-list.csv]
                                    [--extension menalariExtension.tsv] [-o OUT.tsv]

Reads a lemma table produced by the Hebrew/Greek project
(tools/build_lexicon.py: columns main_en / main_es / main_fr = glosses of the
lemma's SDBH sense for the passage; optional main_zh, pos, curated) and matches it
against two Globasa sources:

- the word list's TranslationEng / Spa / Fra / Zho columns (official glosses);
- the Wiktionary extension (menalariExtension.tsv, built by
  "Wiktionary extension builder.py" from vetted Wiktionary senses): its
  English, Spanish, French, Mandarin columns, and its Hebrew column, which is matched
  against the Biblical Hebrew lemma itself (language "he").  That column is
  MODERN Hebrew: it only corroborates (see match()).

A candidate's score is the number of SDBH gloss languages (en, es, fr, zh =
zh-hans + zh-hant merged) that reach it; Modern Hebrew support breaks ties.  Notation in glb_candidates:  word(en+es+fr*+he*)
    *  reached only through the Wiktionary extension (provisional: Wiktionary)
    ~  inexact match (fallback: plural stripped, phrase head, or Hebrew
       plene/defective spelling)

Provisional by design:
- SDBH's language versions localise ONE analysis, so en/es/fr/zh agreement pins
  down the concept, not an independent judgement; "he" is independent of
  SDBH but matches the consonantal form only, against Modern Hebrew (any
  sense, modern meanings, homographs);
- English gloss overlap is not synonymy (Globasa semantics are
  Esperanto-shaped);
- fallbacks are labelled in the "how" column.
"""

import argparse
import collections
import csv
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DEFAULT_WORDLIST = os.path.join(REPO, "word-list.csv")
DEFAULT_EXTENSION = os.path.join(REPO, "menalariExtension.tsv")
LANGS = ("en", "es", "fr", "zh", "he")
WL_COLUMNS = {"en": "TranslationEng", "es": "TranslationSpa", "fr": "TranslationFra",
              "zh": "TranslationZho"}
EXT_COLUMNS = {"en": "Eng with Senses", "es": "Spanish", "fr": "French",
               "zh": "Mandarin", "he": "Hebrew"}
FLAG_WIKT, FLAG_INEXACT = "*", "~"

ARTICLES = re.compile(r"^(to|be|a|an|the|el|la|los|las|un|una|se|le|les|une|l'|d'|s')\s*")
POS_PREFIX = re.compile(r"^([^:;,]{1,40}):\s+")


# ---------------------------------------------------------------- text helpers

def clean(s):
    """Drop notes that can contain separators: (...), [...], <...>, _..._"""
    s = re.sub(r"\([^)]*\)|（[^）]*）|\[[^\]]*\]|<[^>]*>|_[^_]*_", "", s or "")
    return s


def norm_term(t):
    t = t.strip().lower().strip(" .!?¡¿\"'“”")
    for _ in range(2):                      # "to be", "se le"
        t = ARTICLES.sub("", t).strip()
    return t


def terms(s):
    """Gloss terms of a cell, in order (no PoS labels)."""
    out = []
    for t in re.split(r"[;,>/；，、]", clean(s)):
        t = norm_term(t)
        if t and t != "-" and t not in out:
            out.append(t)
    return out


def pos_class(label):
    """Word-list PoS label (any language) -> coarse class."""
    l = label.lower().strip()
    first = l.split()[0] if l else ""
    zh = {"名": "n", "形": "adj", "副": "adv", "介": "prep", "连": "conj", "代": "pron",
          "数": "num", "叹": "interj"}
    if first and not first.isascii():                       # Chinese labels
        if "缀" in first:
            return "affix"
        return "v" if "动" in first else zh.get(first[0], "other")
    if first in ("pfx", "pfj") or "sfx" in l or l.startswith("sfj"):
        return "affix"
    if first in ("n", "s") or l in ("prop n", "n prop"):
        return "n"
    if first.startswith("v."):
        return "v"
    if "adj" in l:
        return "adj"
    for c in ("adv", "prep", "conj", "num", "det", "pron", "interj"):
        if first == c or l.startswith("sintagma " + c[:4]):
            return c
    if l.startswith("sintagma prep"):
        return "prep"
    return "other"


def wl_terms(cell):
    """New word-list format: 'n: water; v.tr: water, irrigate'.
    Old format has no labels.  Returns [(term, posclass or None)]."""
    out, pos = [], None
    for seg in (cell or "").split(";"):
        seg = seg.strip()
        m = POS_PREFIX.match(seg)
        if m:
            pos = pos_class(m.group(1))
            seg = seg[m.end():]
        out += [(t, pos) for t in terms(seg)]
    return out


SDBH_POS = {"noun": "n", "verb": "v", "adjective": "adj", "adverb": "adv",
            "preposition": "prep", "conjunction": "conj", "pronoun": "pron",
            "numeral": "num", "interjection": "interj", "particle": "other",
            "adj": "adj", "adv": "adv", "prep": "prep", "conj": "conj",
            "pron": "pron", "num": "num", "interj": "interj"}


def sdbh_pos(s):
    first = (s or "").lower().split()
    return SDBH_POS.get(first[0], "other") if first else ""


HEB_LETTERS = re.compile(r"[^א-ת ]")


def heb(s):
    """Consonantal skeleton: strip niqqud, cantillation, shin/sin dots, maqaf."""
    return HEB_LETTERS.sub("", s.replace("־", " ")).strip()


def heb_plene(s):
    """Ignore internal matres lectionis (ו, י) for the plene/defective fallback."""
    return s[:1] + re.sub("[וי]", "", s[1:]) if len(s) > 1 else s


def heb_terms(cell):
    out = []
    for t in re.split(r"[;,\\/]", clean(cell)):
        t = heb(t)
        if t and t not in out:
            out.append(t)
    return out


def inexact_forms(t, lang):
    """Fallback forms of an SDBH gloss: plural stripped, phrase head."""
    forms = []
    if lang == "zh":
        return forms
    words = t.split()
    if len(words) > 1:
        forms.append(words[-1] if lang == "en" else words[0])
    for w in [t] + forms[:]:
        if lang == "en" and w.endswith("ies") and len(w) > 4:
            forms.append(w[:-3] + "y")
        elif w.endswith("s") and not w.endswith("ss") and len(w) > 3:
            forms.append(w[:-1])
    return [f for f in forms if f != t]


# ---------------------------------------------------------------- indexes

def read_table(path):
    with open(path, encoding="utf-8") as f:
        delim = "\t" if "\t" in f.readline() else ","
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=delim))


class Index:
    """term -> {glb word: (source, posclass, place of the term in the word's
    cell)} per language, plus each word's PoS classes."""

    def __init__(self, wordlist, extension):
        self.idx = {lang: collections.defaultdict(dict) for lang in LANGS}
        self.plene = collections.defaultdict(set)       # he skeleton -> words
        self.word_pos = collections.defaultdict(set)
        self.filled = collections.Counter()
        for r in read_table(wordlist):
            w = (r.get("Word") or "").strip()
            if not w:
                continue
            for lang, col in WL_COLUMNS.items():
                ts = wl_terms(r.get(col))
                self.filled["wl:" + lang] += bool(ts)
                for k, (t, pos) in enumerate(ts):
                    self.idx[lang][t].setdefault(w, ("wl", pos, k))
                    if pos:
                        self.word_pos[w].add(pos)
        if not extension or not os.path.exists(extension):
            print(f"warning: no Wiktionary extension at {extension} "
                  "(fallback: word list only)")
            return
        for r in read_table(extension):
            w = (r.get("Globasa") or "").strip()
            if not w:
                continue
            for lang, col in EXT_COLUMNS.items():
                ts = heb_terms(r.get(col)) if lang == "he" else terms(r.get(col))
                self.filled["wikt:" + lang] += bool(ts)
                for k, t in enumerate(ts):
                    self.idx[lang][t].setdefault(w, ("wikt", None, k))
                    if lang == "he" and len(heb_plene(t)) >= 3:
                        self.plene[heb_plene(t)].add(w)

    def usable(self):
        return [l for l in LANGS
                if self.filled["wl:" + l] > 1000 or self.filled["wikt:" + l] > 500]

    def lookup(self, lang, glosses):
        """{word: (SDBH gloss position, source, exact, place in the word's
        cell)} for one language: exact matches first; inexact forms only if
        nothing matched exactly."""
        hits = {}
        for exact in (True, False):
            for i, g in enumerate(glosses):
                forms = [g] if exact else inexact_forms(g, lang)
                for f in forms:
                    for w, (src, _, k) in self.idx[lang].get(f, {}).items():
                        old = hits.get(w)
                        if old is None:
                            hits[w] = (i, src, exact, k)
                        else:
                            hits[w] = (min(i, old[0]), "wl" if "wl" in (src, old[1])
                                       else src, exact, min(k, old[3]))
            if hits:
                break
        return hits

    def lookup_he(self, lemma):
        t = heb(lemma)
        hits = {w: (0, "wikt", True, h[2]) for w, h in self.idx["he"].get(t, {}).items()}
        if not hits and len(heb_plene(t)) >= 3:
            hits = {w: (0, "wikt", False, 9) for w in self.plene.get(heb_plene(t), ())}
        return hits


# ---------------------------------------------------------------- matching

def match(glosses_by_lang, lemma, pos, index, usable, n):
    """Ranked candidates.  "he" is Modern Hebrew (homographs and semantic
    shifts: את 'you', קרא 'read'), so it never counts as a language reached:
    it only corroborates (tie-break) candidates the SDBH glosses found, and
    proposes candidates on its own only when the glosses find nothing.
    Rank: tier (>= 2 of en/es/fr/zh agree / one / none); common words
    before proper names, PoS fit, affixes last; en/es/fr reached; Modern
    Hebrew support; earliest SDBH gloss in en/es/fr (SDBH orders its glosses;
    English alone lets homonyms win: 'heaven' -> janatu 'paradise'); Chinese support; official before Wiktionary;
    the gloss as the word's primary meaning; shorter (root before
    derivative); alphabetical.  Chinese counts for the tier but otherwise only
    corroborates: TranslationZho and the extension's Mandarin cover about
    half the words, and unevenly per PoS (bija has Chinese only for 'sow'),
    so ranking by it rewards coverage, not meaning (bija 'seed' lost to
    danyam 'grain')."""
    per = collections.defaultdict(dict)       # word -> lang -> (pos, src, exact)
    for lang in usable:
        hits = (index.lookup_he(lemma) if lang == "he"
                else index.lookup(lang, terms(glosses_by_lang.get(lang, ""))))
        for w, h in hits.items():
            per[w][lang] = h

    if any(set(v) - {"he"} for v in per.values()):
        per = {w: v for w, v in per.items() if set(v) - {"he"}}

    def key(w):
        langs = per[w]
        sdbh = len(set(langs) - {"he"})
        wpos = index.word_pos.get(w, set())
        pos_miss = bool(pos and wpos and pos not in wpos)
        affix = w.startswith("-") or w.endswith("-")
        first = min((h[0] for l, h in langs.items() if l in ("en", "es", "fr")), default=99)
        official = sum(h[1] == "wl" for h in langs.values())
        primary = min(h[3] for h in langs.values())
        core = len(set(langs) & {"en", "es", "fr"})
        return (sdbh < 2, sdbh < 1, w[:1].isupper(), pos_miss, affix, -core,
                "he" not in langs, first, "zh" not in langs, -official, primary,
                len(w), w.casefold())

    ranked = sorted(per, key=key)[:n]
    out = []
    for w in ranked:
        tags = [l + (FLAG_WIKT if per[w][l][1] == "wikt" else "")
                + ("" if per[w][l][2] else FLAG_INEXACT)
                for l in LANGS if l in per[w]]
        out.append((w, per[w], f"{w}({'+'.join(tags)})"))
    return out


def describe(cands, has_gloss):
    if not cands:
        return "(fallback: no SDBH gloss matched; choose from bdb/klein)"
    langs = cands[0][1]
    sdbh = len(set(langs) - {"he"})
    notes = []
    if not sdbh:
        how = ("(fallback: no SDBH gloss" + ("" if not has_gloss else " matched")
               + "; Modern Hebrew homograph via Wiktionary only, check the sense)")
    elif sdbh >= 2:
        how = "glosses agree"
    else:
        how = "(provisional: one language only)"
    if sdbh and "he" in langs:
        how += "; Modern Hebrew corroborates"
    official = sum(h[1] == "wl" for l, h in langs.items() if l != "he")
    if sdbh and official < min(sdbh, 2):      # the verdict rests on Wiktionary
        notes.append("(provisional: Wiktionary)")
    if any(not h[2] for h in langs.values()):
        notes.append("(fallback: inexact match: plural/phrase head/plene spelling)")
    return " ".join([how] + notes)


def alternatives(curated, index, usable, n):
    """Map the source side's curated readings ("status: en; es; fr [basis]",
    separated by " | ") to Globasa candidates (no Hebrew: the lemma is the
    same for every reading)."""
    out = []
    for item in filter(None, (s.strip() for s in (curated or "").split(" | "))):
        m = re.match(r"(\w+): (.*?)(?: \[.*\])?$", item)
        if not m:
            continue
        parts = [p.strip() for p in m.group(2).split(";")]
        by_lang = dict(zip(("en", "es", "fr"), parts))
        cands = match(by_lang, "", "", index, [l for l in usable if l != "he"], n)
        out.append(f"{m.group(1)} '{by_lang.get('en', '')}': "
                   f"{' '.join(c[2] for c in cands) or '(no match)'}")
    return " | ".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("table")
    ap.add_argument("--wordlist", default=DEFAULT_WORDLIST)
    ap.add_argument("--extension", default=DEFAULT_EXTENSION,
                    help="Wiktionary extension TSV ('' to disable)")
    ap.add_argument("-o", "--out")
    ap.add_argument("-n", type=int, default=4, help="candidates per lemma")
    a = ap.parse_args()
    out = a.out or os.path.join(HERE, "data", os.path.basename(a.table)
                                .replace(".tsv", "_glb.tsv"))
    index = Index(a.wordlist, a.extension)
    usable = index.usable()
    if not usable:
        raise SystemExit(f"no usable translation columns in {a.wordlist} / {a.extension}")
    rows = read_table(a.table)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    stats = collections.Counter()
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["strongs", "lemma", "freq", "pos", "main_en", "glb_candidates", "how",
                    "glb_alternatives", "bdb", "klein", "source_flags"])
        for r in rows:
            glosses = {l: r.get(f"main_{l}", "") for l in LANGS if l != "he"}
            has_gloss = any(terms(g) for g in glosses.values())
            pos = sdbh_pos(r.get("pos"))
            cands = match(glosses, r.get("lemma", ""), pos, index, usable, a.n)
            how = describe(cands, has_gloss)
            top = len(set(cands[0][1]) - {"he"}) if cands else -1
            stats[{-1: "none", 0: "hebrew-only", 1: "single"}.get(top, "agree")] += 1
            stats["wikt"] += "(provisional: Wiktionary)" in how
            stats["he"] += any("he" in c[1] for c in cands)
            w.writerow([r.get("strongs", ""), r.get("lemma", ""), r.get("freq", ""),
                        r.get("pos", ""), r.get("main_en", ""),
                        " ".join(c[2] for c in cands), how,
                        alternatives(r.get("curated"), index, usable, a.n),
                        r.get("bdb", ""), r.get("klein", ""), r.get("flags", "")])
    print(f"{len(rows)} lemmas -> {out}\n  languages: {', '.join(usable)}; "
          f"agree {stats['agree']}, single {stats['single']}, Modern-Hebrew-only "
          f"{stats['hebrew-only']}, none {stats['none']}; "
          f"Wiktionary-dependent {stats['wikt']}; Hebrew lemma matched {stats['he']}")


if __name__ == "__main__":
    main()
