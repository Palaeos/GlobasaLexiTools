# Script tier: Wiktionary senses -> suggested Globasa words + HistWords trajectory per sense.
# Proposes, decides nothing: every glb suggestion and every date range needs vetting.
#
# For each TARGET (English form, Wiktionary PoS):
#   1. senses = Wiktionary glosses (../WiktionaryLMDB), with their tags (dated, archaic, slang ...).
#      Translation tables are attached to the gloss they share most content words with; a table
#      that matches no gloss becomes its own sense (its header as gloss).
#   2. Globasa suggestions, pivot vote: a word-list entry gets a vote for each language column
#      (Epo x2, then Spa Fra Deu Rus Zho Hin Ara) whose items, in the segment of the same PoS,
#      contain one of the sense's Wiktionary translations in that language. Score >= 2 is listed.
#      No pivot hit -> exact match of a short gloss part against TranslationEng items, marked
#      "(fallback: English gloss)".
#   3. probes = content words of the gloss and table header (not the target, not shared with another
#      sense of the target, >= 1 per million in the 1990s), and the mean cosine similarity of the
#      target to them in every decade 1800-1990 (histwords.py). One vector per form and decade mixes
#      senses, so the curves show which sense is gaining or losing ground in books, not per-sentence use.
#
# Output: histwords_senses.tsv (one row per sense, decades as columns) and
# histwords_senses_report.txt (per word: senses, tags, glb suggestions, trend 1890s->1990s).

import os
import re
import sys
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
from spacy.lang.en.stop_words import STOP_WORDS

import histwords as hw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from wiktionary_db import WiktionaryDB

TARGETS = [
    # in The Time Machine, not yet in the glossary
    ("race", "noun"), ("dumb", "adj"), ("awful", "adj"), ("dreadful", "adj"), ("terrible", "adj"),
    ("terribly", "adv"), ("fantastic", "adj"), ("weird", "adj"), ("cunning", "adj"), ("sick", "adj"),
    ("wanted", "verb"), ("straight", "adj"),
    # 20th-century shifts (queer/gay type)
    ("queer", "adj"), ("gay", "adj"), ("intercourse", "noun"), ("partner", "noun"), ("mistress", "noun"),
    ("sex", "noun"), ("camp", "adj"), ("closet", "noun"),
    # technology repurposing
    ("broadcast", "verb"), ("computer", "noun"), ("typewriter", "noun"), ("tank", "noun"), ("car", "noun"),
    ("wireless", "noun"), ("film", "noun"), ("record", "noun"), ("screen", "noun"),
    # intensifiers
    ("terrific", "adj"), ("tremendous", "adj"), ("awesome", "adj"),
    # politics and history
    ("holocaust", "noun"), ("liquidate", "verb"), ("propaganda", "noun"), ("camp", "noun"),
    ("liberal", "adj"), ("radical", "adj"),
    # earlier questions
    ("man", "noun"),
]
# form looked up in Wiktionary when the HistWords form is inflected
LEMMA = {"wanted": "want", "terribly": "terribly"}

LANG_COL = {"eo": ("TranslationEpo", 2), "es": ("TranslationSpa", 1), "fr": ("TranslationFra", 1),
            "de": ("TranslationDeu", 1), "ru": ("TranslationRus", 1), "zh": ("TranslationZho", 1),
            "hi": ("TranslationHin", 1), "ar": ("TranslationAra", 1)}
POS_OF = {"adj": "adj", "noun": "n", "verb": "v", "adv": "adv"}
MIN_SCORE = 2
PROBE_PER_MILLION = 1.0

ARABIC_MARKS = re.compile(r"[ً-ْٰ]")


def norm(s, lang=""):
    s = s.strip().lower()
    if lang == "ar":
        s = ARABIC_MARKS.sub("", s)
    return s


def segments(cell, keep_notes=False):
    """'adj: a, b (_x, y_); adv: c' -> [('adj', ['a', 'b']), ('adv', ['c'])]. Splits on commas outside
    parentheses (annotations contain commas). keep_notes=True returns (item, annotated) pairs:
    'tanque (_militar_)' is a restricted item (bug 2026-11-20: stripping the note let the military
    tanque vote tanke for the liquid-container sense)."""
    if not isinstance(cell, str):
        return []
    out = []
    for seg in cell.split(";"):
        m = re.match(r"\s*([^:(]{1,15}):\s*(.*)", seg)
        label, body = (m.group(1).strip(), m.group(2)) if m else ("", seg)
        items, depth, cur = [], 0, ""
        for ch in body + ",":
            depth += ch == "("
            depth -= ch == ")"
            if depth == 0 and ch in ",،、，":
                note = "(" in cur
                it = re.sub(r"\([^)]*\)", "", cur).strip()
                if it:
                    items.append((it, note) if keep_notes else it)
                cur = ""
            else:
                cur += ch
        out.append((label, items))
    return out


# --- word-list reverse index: (lang, item) -> {(globasa word, pos)} -------------------------------
wl = pd.read_csv(os.path.join(os.path.dirname(HERE), "word-list.csv"), index_col=0)
wl = wl[~wl.index.duplicated()]
rev = defaultdict(set)
eng_rev = defaultdict(set)
for word, row in wl.iterrows():
    eng = segments(row["TranslationEng"])
    pos_seq = [lab for lab, _ in eng]
    for lab, items in eng:
        for it in items:
            eng_rev[(lab.split(".")[0], norm(it))].add(word)
    for lang, (col, _) in LANG_COL.items():
        segs = segments(row[col], keep_notes=True)
        for i, (_, items) in enumerate(segs):
            pos = pos_seq[i].split(".")[0] if len(segs) == len(pos_seq) else "*"
            for it, note in items:
                rev[(lang, norm(it, lang))].add((word, pos, note))


def pos_ok(p, want):
    return p == "*" or p == want or (want == "v" and p.startswith("v"))


def suggest(trans, want_pos):
    # vote per language column; an annotated item ("tanque (_militar_)") counts half.
    # Epo veto: Globasa semantics are Esperanto-shaped, so when some candidate matches the sense's
    # Esperanto translation, candidates whose own (non-empty) Epo column does not match are dropped
    # (tank 'container': tanku matches eo:cisterno; tanke has Epo tanko -> dropped).
    votes = defaultdict(dict)
    for lang, (col, weight) in LANG_COL.items():
        for t in trans.get(lang, ()):
            for word, p, note in rev.get((lang, norm(t.word, lang)), ()):
                if pos_ok(p, want_pos):
                    w = weight / 2 if note else weight
                    if w > votes[word].get(lang, (None, 0))[1]:
                        votes[word][lang] = (t.word, w)
    if any("eo" in langs for langs in votes.values()):
        votes = {g: langs for g, langs in votes.items()
                 if "eo" in langs or not isinstance(wl.at[g, "TranslationEpo"], str)}
    scored = []
    for word, langs in votes.items():
        score = sum(w for _, w in langs.values())
        if score >= MIN_SCORE:
            scored.append((score, word, langs))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [f"{w} [{s:g}: " + " ".join(f"{l}:{t}" for l, (t, _) in sorted(langs.items())) + "]" for s, w, langs in scored[:4]]


def eng_fallback(gloss, want_pos, target):
    # only the definition proper: labels "(dated)", quoted examples and the target word are skipped
    # (first run: "deaf, dumb" inside quotes gave dumb 'mute' -> bobo; "awesome" gave terrible -> daybon)
    gloss = re.sub(r"\([^)]*\)|“[^”]*”|\"[^\"]*\"", " ", gloss)
    # only the head of the definition (first two parts), and never a word that itself shifted
    # (terrible: "...; awesome" gave the modern awesome -> daybon; man: "sentient being" -> elfu)
    shifted = {f for f, _ in TARGETS}
    out = []
    for part in re.split(r"[;,.:]", gloss)[:2]:
        part = re.sub(r"^(a|an|the|to)\s+", "", norm(part))
        if part in target or part in shifted or any(part.startswith(t[:4]) for t in target):
            continue
        if 0 < len(part.split()) <= 2:
            out += sorted(eng_rev.get((want_pos, part), ()))
    return [f"{w} (fallback: English gloss)" for w in dict.fromkeys(out)][:4]


def content(text):
    return [w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOP_WORDS and len(w) > 2]


db = WiktionaryDB(os.path.join(os.path.dirname(HERE), "WiktionaryLMDB"))
_, i90, _, c90 = hw.load(1990)
tot90 = sum(c90.values())

rows = []
for form, wpos in TARGETS:
    lemma = LEMMA.get(form, form)
    senses = db.get_senses(lemma, wpos) or []
    tables = db.get_translations(lemma, wpos) or {}
    units = []
    for s in senses:
        gloss = (s.raw_glosses or s.glosses or ("",))[0]
        units.append({"gloss": gloss, "tags": [t for t in s.tags if t not in ("form-of",)], "trans": {}, "header": ""})
    for header, trans in tables.items():
        hw_ = set(content(header))
        best, best_n = None, 0
        for u in units:
            n = len(hw_ & set(content(u["gloss"])))
            if n > best_n:
                best, best_n = u, n
        if best is None:
            units.append({"gloss": header, "tags": ["(table only)"], "trans": trans, "header": header})
        else:
            for lang, ts in trans.items():
                best["trans"].setdefault(lang, set()).update(ts)
            best["header"] = (best["header"] + " | " + header).strip(" |")
    # probes, minus words shared between senses
    stem = form[:4]
    for u in units:
        u["probes"] = [w for w in dict.fromkeys(content(u["gloss"] + " " + u["header"]))
                       if not w.startswith(stem) and not w.startswith(lemma[:4])
                       and w in i90 and c90.get(w, 0) / tot90 * 1e6 >= PROBE_PER_MILLION]
    shared = Counter(p for u in units for p in set(u["probes"]))
    for u in units:
        u["probes"] = [p for p in u["probes"] if shared[p] == 1][:8]
    want = POS_OF[wpos]
    for k, u in enumerate(units, 1):
        glb = suggest(u["trans"], want) or eng_fallback(u["gloss"], want, {form, lemma})
        sims = {}
        for d in hw.DECADES:
            vals = [hw.sim(d, form, p) for p in u["probes"]]
            vals = [v for v in vals if v is not None]
            sims[d] = float(np.mean(vals)) if len(vals) >= 2 else None
        rows.append({"form": form, "pos": wpos, "sense": k, "gloss": u["gloss"], "tags": ", ".join(u["tags"]),
                     "glb": "; ".join(glb), "probes": ", ".join(u["probes"]), "sims": sims})

with open(os.path.join(HERE, "histwords_senses.tsv"), "w", encoding="utf-8") as f:
    f.write("\t".join(["form", "pos", "sense", "gloss", "tags", "glb_suggested", "probes"] + [str(d) for d in hw.DECADES]) + "\n")
    for r in rows:
        f.write("\t".join([r["form"], r["pos"], str(r["sense"]), r["gloss"].replace("\t", " "), r["tags"], r["glb"], r["probes"]]
                          + ["" if r["sims"][d] is None else f"{r['sims'][d]:.3f}" for d in hw.DECADES]) + "\n")


def avg(r, ds):
    v = [r["sims"][d] for d in ds if r["sims"][d] is not None]
    return np.mean(v) if v else None


with open(os.path.join(HERE, "histwords_senses_report.txt"), "w", encoding="utf-8") as f:
    f.write("Per sense: similarity x100 to its probes, 1800-40 avg | 1890s | 1950s | 1990s; "
            "trend = 1990s - 1890s. Only senses with >= 2 probes in HistWords have numbers.\n")
    for form, wpos in dict.fromkeys(TARGETS):
        f.write(f"\n== {form} ({wpos})\n")
        for r in [r for r in rows if r["form"] == form and r["pos"] == wpos]:
            a, b, c, e = avg(r, range(1800, 1850, 10)), r["sims"][1890], r["sims"][1950], r["sims"][1990]
            nums = "  ".join("  ." if x is None else f"{x * 100:3.0f}" for x in (a, b, c, e))
            trend = f"{(e - b) * 100:+4.0f}" if e is not None and b is not None else "    "
            f.write(f"  {r['sense']:2d} {nums}  {trend}  {r['gloss'][:70]}"
                    + (f"  [{r['tags']}]" if r["tags"] else "") + "\n")
            if r["glb"]:
                f.write(f"       glb: {r['glb']}\n")
print(open(os.path.join(HERE, "histwords_senses_report.txt"), encoding="utf-8").read())
