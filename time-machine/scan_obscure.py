# Find words in The Time Machine that a present-day Anglophone reader is
# unlikely to know, so the Globasa translation can render their sense in plain
# words. Script tier only proposes; the sense in context is decided in
# obscure_resolved.tsv (LLM/human tier).
#
# Candidate = alphabetic, non-proper-noun token whose lemma AND surface form
# are both below ZIPF_MAX in wordfreq's modern English frequency (Zipf scale:
# 3 = once per million words). Words coined in the novel are excluded.
#
# Output obscure_candidates.tsv:
#   lemma, pos (all tags seen), zipf, count, editions (H=Heinemann, U=Holt),
#   base_hint (a common base word if the form looks like a regular
#   derivative — a hint only, never a filter), first_ref, context (first
#   Heinemann sentence, else Holt), wikt_senses (tagged)
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

import spacy
from wordfreq import zipf_frequency

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from wiktionary_db import WiktionaryDB

HERE = Path(__file__).parent
ZIPF_MAX = 3.0
COINED = {"eloi", "morlock", "morlocks", "weena", "eloi's", "filby"}
WIKT_POS = {"NOUN": "noun", "VERB": "verb", "ADJ": "adj", "ADV": "adv"}

nlp = spacy.load("en_core_web_sm")
nlp.max_length = 400000
db = WiktionaryDB(str(HERE.parent / "WiktionaryLMDB"))


LIG = str.maketrans({"œ": "oe", "æ": "ae", "Œ": "Oe", "Æ": "Ae"})
PREFIXES = ("un", "in", "dis", "up", "under", "over", "out", "fore", "re")
SUFFIXES = ("ness", "ly", "ful", "less", "like", "ish", "y", "er", "est", "ed", "ing", "s")


def zipf(w):
    return zipf_frequency(w, "en")


def base_hint(w):
    # a common word inside a rare form: unheeded -> heed, tableful -> table,
    # hearthrug -> hearth+rug. Hint only.
    for p in PREFIXES:
        if w.startswith(p) and zipf(w[len(p):]) >= 3.5:
            return p + "-+" + w[len(p):]
    for suf in SUFFIXES:
        if w.endswith(suf):
            stem = w[: -len(suf)]
            for cand in (stem, stem + "e", stem[:-1] + "y" if stem.endswith("i") else stem):
                if len(cand) > 2 and zipf(cand) >= 3.5:
                    return cand + "+-" + suf
    for i in range(3, len(w) - 2):
        if zipf(w[:i]) >= 4 and zipf(w[i:]) >= 4:
            return w[:i] + "+" + w[i:]
    return ""


def chapters(path):
    text = path.read_text(encoding="utf-8").translate(LIG)
    for block in re.split(r"^## ", text, flags=re.M)[1:]:
        title, _, body = block.partition("\n")
        yield title.strip(), body


hits = defaultdict(lambda: {"count": 0, "eds": set(), "ref": "", "ctx": "", "zipf": 9.0})
for ed, fname in (("H", "heinemann.txt"), ("U", "holt.txt")):
    for title, body in chapters(HERE / "text" / fname):
        for sent in nlp(body).sents:
            for tok in sent:
                w = tok.text.lower()
                if not tok.is_alpha or tok.pos_ in ("PROPN", "NUM") or w in COINED:
                    continue
                if tok.pos_ not in WIKT_POS:
                    continue
                lemma = tok.lemma_.lower()
                z = max(zipf(w), zipf(lemma))
                if z >= ZIPF_MAX:
                    continue
                h = hits[lemma]
                h.setdefault("pos", set()).add(WIKT_POS[tok.pos_])
                h.setdefault("forms", set()).add(w)
                h["count"] += 1
                h["zipf"] = min(h["zipf"], z)
                h["eds"].add(ed)
                if not h["ctx"] or (ed == "H" and h["ref"].startswith("U")):
                    if not (h["ctx"] and h["ref"].startswith("H")):
                        h["ref"] = f"{ed}:{title}"
                        h["ctx"] = re.sub(r"\s+", " ", sent.text).strip()


def wikt(lemma, poses):
    out = []
    for pos in sorted(poses):
        for s in db.get_senses(lemma, pos) or []:
            g = s.glosses[-1] if s.glosses else ""
            tag = "[" + ",".join(s.tags) + "] " if s.tags else ""
            out.append(f"{pos}: {tag}{g}")
    return " | ".join(out)


rows = sorted(hits.items(), key=lambda kv: kv[1]["zipf"])
with open(HERE / "obscure_candidates.tsv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["lemma", "pos", "zipf", "count", "editions", "base_hint", "first_ref", "context", "wikt_senses"])
    for lemma, h in rows:
        hint = base_hint(lemma) or next((base_hint(f) for f in sorted(h["forms"]) if base_hint(f)), "")
        w.writerow([lemma, ",".join(sorted(h["pos"])), f"{h['zipf']:.2f}", h["count"], "".join(sorted(h["eds"])),
                    hint, h["ref"], h["ctx"], wikt(lemma, h["pos"])])
print(len(rows), "candidates")
