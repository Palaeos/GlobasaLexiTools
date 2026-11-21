"""Does the translator's word pick the Wiktionary sense? (Time Machine dated-sense gold)

For every dated_sense occurrence of obscure_resolved.tsv that the aligned 1890s-1900s Spanish
and Esperanto translations cover (cache/evidence_{spa,epo}.tsv, align_translations.py), the
translator's linked word is looked up in the lemma's Wiktionary translation tables; each table
is tied to a definition with sense_rows.match_sense_to_definition. The senses whose table lists
the word (exact, or same first 5 letters for inflected forms) are the translation's candidates:
one = a pick, several = ambiguous, none = no evidence. Gold senses as in period_sense_probe.py
(content-word overlap with the gold gloss, ties all gold).

Then 'translation, else MacBERTh': the pick where there is one, otherwise condition B of
period_sense_probe_items.tsv, on the items both cover.

    ../venv/bin/python time-machine/translation_sense_probe.py"""
import csv
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
os.chdir(ROOT)
from sense_rows import match_sense_to_definition  # noqa: E402
from wiktionary_db import WiktionaryDB  # noqa: E402

WIKT_POS = ("adj", "adv", "noun", "verb", "prep", "conj", "intj")
LANGS = {"spa": "es", "epo": "eo"}
STOP = set("a an the of to in on for and or by with as at from that this be is are was it its "
           "one's someone something oneself who which what not no very more most into out up "
           "being having make made do done".split())
PAREN = re.compile(r"\(.*?\)")


def content(text):
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOP and len(w) > 2}


def norm_words(text):
    return {w for w in re.split(r"[\s,;/]+", PAREN.sub("", text.lower())) if len(w) > 1}


def same(a, b):
    return a == b or (len(a) >= 5 and len(b) >= 5 and a[:5] == b[:5])


gold_rows = {r["lemma"] + "|" + r["ref"] + "|" + r["quote"]: r
             for r in csv.DictReader(open(os.path.join(HERE, "obscure_resolved.tsv"), encoding="utf-8"),
                                     delimiter="\t") if r["verdict"] == "dated_sense"}
evidence = {lang: {r["key"]: r for r in csv.DictReader(
    open(os.path.join(HERE, "cache", f"evidence_{lang}.tsv"), encoding="utf-8"), delimiter="\t")}
    for lang in LANGS}

# B picks of period_sense_probe, by (lemma, normalised sentence)
probe = []
for r in csv.DictReader(open(os.path.join(HERE, "period_sense_probe_items.tsv"), encoding="utf-8"),
                        delimiter="\t"):
    if r["gold"]:
        probe.append(r)
strip = lambda g: re.sub(r" \[[^\]]*\]$", "", g.replace(" (fallback: gloss, no quotation)", "")).strip()
nsent = lambda s: " ".join(re.findall(r"\w+", s.lower()))

stats = {lang: Counter() for lang in (*LANGS, "either")}
combo = Counter()
with WiktionaryDB() as db:
    for key, g in gold_rows.items():
        lemma = g["lemma"].strip().lower()
        senses, by_pos = [], {}
        for pos in WIKT_POS:
            ss = db.get_senses(lemma, pos) or []
            by_pos[pos] = ss
            senses += [(pos, s) for s in ss]
        if not senses:
            continue
        overlap = [len(content(g["sense"]) & content(s.glosses[0] if s.glosses else "")) for _, s in senses]
        if not max(overlap):
            continue
        gold = {k for k, o in enumerate(overlap) if o == max(overlap)}
        index = {id(s): k for k, (_, s) in enumerate(senses)}
        table_words = {lang: {} for lang in LANGS}  # lang -> sense index -> words
        for pos in WIKT_POS:
            for tkey, langs in (db.get_translations(lemma, pos) or {}).items():
                m = match_sense_to_definition(tkey, by_pos[pos])
                if m is None:
                    continue
                for lang, code in LANGS.items():
                    for t in langs.get(code, ()):
                        table_words[lang].setdefault(index[id(m)], set()).update(norm_words(t.word))
        picks = {}
        for lang in LANGS:
            ev = evidence[lang].get(key)
            words = norm_words(ev[f"{lang}_words"]) if ev and ev.get(f"{lang}_words") else set()
            if not words:
                stats[lang]["no aligned word"] += 1
                continue
            if not table_words[lang]:
                stats[lang]["no table for the lemma"] += 1
                continue
            cand = {k for k, ws in table_words[lang].items() if any(same(a, b) for a in words for b in ws)}
            if not cand:
                stats[lang]["word in no table"] += 1
            elif len(cand) > 1:
                stats[lang]["ambiguous" + (" (gold among)" if cand & gold else "")] += 1
            else:
                k = next(iter(cand))
                picks[lang] = k
                stats[lang]["right" if k in gold else "wrong"] += 1
        vals = set(picks.values())
        if len(vals) == 1:
            k = vals.pop()
            stats["either"]["right" if k in gold else "wrong"] += 1
            pick = k
        else:
            stats["either"]["conflict" if vals else "no pick"] += 1
            pick = None
        # combine with B
        q = nsent(g["quote"])
        b = next((r for r in probe if r["lemma"] == lemma and q in nsent(r["sentence"].replace("**", ""))), None)
        if b:
            gold_txt = {strip(x) for x in b["gold"].split(" / ")}
            b_right = strip(b["B"]) in gold_txt
            combo["items"] += 1
            combo["B right"] += b_right
            if pick is not None:
                combo["translation picks"] += 1
                combo["translation right"] += pick in gold
                combo["B right where translation picks"] += b_right
            combo["translation else B right"] += (pick in gold) if pick is not None else b_right

for lang, c in stats.items():
    p = c["right"] + c["wrong"]
    print(f"{lang:6s} picks {p:3d}: right {c['right']:3d} ({100 * c['right'] / max(p, 1):4.1f}%)  "
          + ", ".join(f"{k} {v}" for k, v in sorted(c.items()) if k not in ("right", "wrong")))
n = combo["items"]
print(f"\non the {n} items period_sense_probe also covers:")
print(f"  B MacBERTh alone            {combo['B right']:3d}/{n} = {100 * combo['B right'] / max(n, 1):4.1f}%")
print(f"  translation picks           {combo['translation picks']:3d}: right {combo['translation right']}"
      f" (B right on those: {combo['B right where translation picks']})")
print(f"  translation, else B         {combo['translation else B right']:3d}/{n} = "
      f"{100 * combo['translation else B right'] / max(n, 1):4.1f}%")
