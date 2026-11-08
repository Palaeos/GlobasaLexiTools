"""Vocalization dictionaries for Arabic and Persian: an unvocalized spelling ->
its vowelled lemmas, from an open lexicon, so the real pronunciation does not
depend on a Wiktionary romanization (or on a prediction).

Arabic: Camel Morph MSA v1.0 (CAMeL Lab, NYU Abu Dhabi; data CC BY 4.0,
Khairallah et al. 2024, LREC-COLING), downloaded on first use into
word_selection_cache/camel_morph/ (never committed). Its STEMS section gives,
per undiacritized stem, the diacritized stem and lemma (lex), part of speech,
English gloss and a lemma log-probability. Every entry is indexed by its bare
lemma (stems of one lemma collapse); lemmas without vowel marks (some proper
names) are left out.

Persian: KaamelDict (Fetrat et al.; 116,630 entries in Iranian pronunciation,
merged from Tihu-Dict, ipa-dict, Wiktionary, the Jame' glossary and others),
GPL: downloaded on first use into word_selection_cache/kaameldict/ and read as
data, never committed to this MIT repository.

Attribution (CC BY 4.0): Christian Khairallah, Salam Khalifa, Reham Marzouk,
Mayar Nassar and Nizar Habash. 2024. Camel Morph MSA: A Large-Scale Open-Source
Morphological Analyzer for Modern Standard Arabic. LREC-COLING 2024, 2683-2691.
"""

import json
import os
import re
import unicodedata
from functools import lru_cache

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMEL_DIR = os.path.join(ROOT, "word_selection_cache", "camel_morph")
CAMEL_DB = os.path.join(CAMEL_DIR, "camel_morph_msa_v1.0.db")
CAMEL_URL = ("https://github.com/CAMeL-Lab/camel_morph/raw/main/official_releases/"
             "lrec-coling2024_release/databases/camel-morph-msa/camel_morph_msa_v1.0.db")
CAMEL_INDEX = os.path.join(CAMEL_DIR, "lemmas.json")

_HARAKAT = re.compile("[ً-ْٰـ]")
_KEY = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ی": "ي", "ک": "ك",
                      "\u200c": None, "\u200d": None, "ۀ": "ه", "ة": "ه"})
# lemma part of speech: nouns first (LexiliAsel cites nouns and verbal nouns), verbs last
POS_RANK = {"noun": 0, "adj": 1, "adj_comp": 1, "noun_num": 2, "adv": 2, "noun_prop": 3, "verb": 4}


def key(word):
    """Lookup key: no vowel marks or tatweel, alef/ya/kaf variants merged."""
    w = unicodedata.normalize("NFC", (word or "").strip())
    return _HARAKAT.sub("", w).translate(_KEY).replace(" ", "")


def _download():
    import urllib.request
    os.makedirs(CAMEL_DIR, exist_ok=True)
    tmp = CAMEL_DB + ".part"
    urllib.request.urlretrieve(CAMEL_URL, tmp)
    os.replace(tmp, CAMEL_DB)


def build_arabic(db=CAMEL_DB, out=CAMEL_INDEX):
    """Index the Camel Morph STEMS section: bare lemma -> [[lex, pos, gloss, logprob]]."""
    if not os.path.exists(db):
        _download()
    index = {}
    section = None
    with open(db, encoding="utf-8") as f:
        for line in f:
            if line.startswith("###"):
                section = line.strip("#\n")
                continue
            if section != "STEMS":
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            feats = dict(kv.split(":", 1) for kv in parts[2].split(" ") if ":" in kv)
            lex, diac, pos = feats.get("lex", ""), feats.get("diac", ""), feats.get("pos", "")
            lex = re.sub(r"[_-][^ ]*$", "", lex)       # sense numbers: شَاهِد_1, شَاهِد_2
            if not lex or not pos or pos.startswith(("part", "pron", "conj", "prep", "punc", "digit")):
                continue
            if not _HARAKAT.search(lex):          # unvocalized lemma (proper names): nothing to learn
                continue
            try:
                lp = float(feats.get("lex_logprob", "-99"))
            except ValueError:
                lp = -99.0
            row = [lex, pos, feats.get("gloss", "").replace("_", " "), lp]
            rows = index.setdefault(key(lex), [])
            same = next((r for r in rows if r[0] == lex and r[1] == pos), None)
            if same is None:
                rows.append(row)
            elif row[2] and row[2] not in same[2]:    # another sense of the lemma: keep its gloss
                same[2] = f"{same[2]};{row[2]}" if same[2] else row[2]
                same[3] = max(same[3], lp)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False)
    return len(index)


@lru_cache(maxsize=1)
def _arabic_index():
    if not os.path.exists(CAMEL_INDEX):
        build_arabic()
    with open(CAMEL_INDEX, encoding="utf-8") as f:
        return json.load(f)


def _gloss_overlap(gloss, context):
    g = set(re.findall(r"[a-z]+", gloss.lower()))
    return len(g & context)


def arabic(word, context=()):
    """Vowelled lemmas of an Arabic spelling, best first: [{lex, pos, gloss, logprob,
    article}]. context: English words of the concept (a gloss that shares one wins);
    then nouns before verbs; then frequency. A leading al- is split off when the
    whole word is not a lemma (القبة -> al + قُبَّة)."""
    idx = _arabic_index()
    k = key(word)
    rows, article = idx.get(k), False
    if not rows and k.startswith("ال") and len(k) > 3:
        rows, article = idx.get(k[2:]), True
    if not rows:
        return []
    ctx = {w.lower() for c in context for w in re.findall(r"[A-Za-z]+", c)}
    ranked = sorted(rows, key=lambda r: (-_gloss_overlap(r[2], ctx), POS_RANK.get(r[1], 3), -r[3]))
    return [{"lex": r[0], "pos": r[1], "gloss": r[2], "logprob": r[3], "article": article,
             "matched_context": _gloss_overlap(r[2], ctx) > 0} for r in ranked]


def arabic_form(entry):
    """Globasa letters of a dictionary entry: the vowelled lemma read as script;
    a verb in its citation form faʕala (Camel Morph writes no final fatha:
    بَارَك -> baraka, as LexiliAsel cites verbs); al- restored."""
    from . import translit
    lex = entry["lex"]
    if entry["pos"] == "verb" and not re.search("[\u064e\u064f\u0650\u0652]$", lex) and not lex.endswith(("ى", "ا")):
        lex += "\u064e"
    f = translit.arabic_script(lex)
    return ("al" + f) if (f and entry["article"]) else f


def arabic_forms(word, context=(), roman_form=""):
    """[(form, how)] for an unvocalized Arabic word from the dictionary, best first,
    and a flag (or ''). roman_form: the word's romanization in Globasa letters (a
    translation table's is sense-specific), used only to choose among the
    dictionary's readings. [] if the dictionary does not have the word."""
    cands = arabic(word, context)
    out, seen = [], set()
    for c in cands:
        f = arabic_form(c).replace(" ", "")
        if f and f not in seen:
            seen.add(f)
            out.append((f, c))
    if not out:
        return [], ""
    flag = ""
    pick = next((i for i, (f, _) in enumerate(out) if roman_form and f == roman_form), None)
    if pick is not None:
        why = "the romanization picks this reading"
    elif out[0][1]["matched_context"]:
        pick, why = 0, "gloss matches the concept"
    else:
        pick, why = 0, "part of speech and frequency"
        if len(out) > 1:
            flag = (f"Camel Morph has {len(out)} readings of this spelling; "
                    f"chosen by part of speech and frequency (no gloss matched)")
    out.insert(0, out.pop(pick))
    return [(f, f"Camel Morph: {c['lex']} ({c['pos']}: {c['gloss'][:40]}; {why if i == 0 else 'other reading'})")
            for i, (f, c) in enumerate(out)], flag


# ---------------------------------------------------------------------------
# Persian: KaamelDict
# ---------------------------------------------------------------------------
KAAMEL_DIR = os.path.join(ROOT, "word_selection_cache", "kaameldict")
KAAMEL_CSV = os.path.join(KAAMEL_DIR, "KaamelDict.csv")
KAAMEL_URL = "https://huggingface.co/datasets/MahtaFetrat/KaamelDict/resolve/main/KaamelDict.csv"
KAAMEL_INDEX = os.path.join(KAAMEL_DIR, "index.json")
# KaamelDict phonemes -> Globasa letters (as translit.PERSIAN renders Iranian
# romanizations: â a, š x, x h, q/ğ g, č c, ž j; the glottal stop is dropped)
KAAMEL_LETTERS = {"A": "a", "S": "x", "x": "h", "q": "g", "C": "c", "Z": "j", "?": "", " ": " "}


def _kaamel_form(phones):
    from . import translit
    return translit.clean("".join(KAAMEL_LETTERS.get(p, p) for p in phones))


def build_persian(csv_path=KAAMEL_CSV, out=KAAMEL_INDEX):
    """Index KaamelDict: lookup key -> [[spelling, [forms], [pos], [prob]]]."""
    import ast
    import csv
    import urllib.request
    if not os.path.exists(csv_path):
        os.makedirs(KAAMEL_DIR, exist_ok=True)
        urllib.request.urlretrieve(KAAMEL_URL, csv_path + ".part")
        os.replace(csv_path + ".part", csv_path)
    index = {}
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                variants = ast.literal_eval(row["phoneme"])
                pos = ast.literal_eval(row["POS"]) if row["POS"] else []
                prob = ast.literal_eval(row["prob"]) if row["prob"] else []
            except (ValueError, SyntaxError):
                continue
            forms = list(dict.fromkeys(f for f in (_kaamel_form(v) for v in variants) if f))
            if forms:
                index.setdefault(key(row["grapheme"]), []).append([row["grapheme"], forms, pos, prob])
    with open(out, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False)
    return len(index)


@lru_cache(maxsize=1)
def _persian_index():
    if not os.path.exists(KAAMEL_INDEX):
        build_persian()
    with open(KAAMEL_INDEX, encoding="utf-8") as f:
        return json.load(f)


def persian(word):
    """Pronunciations of a Persian spelling (Globasa letters), in KaamelDict's order;
    an exact spelling first, then spellings that differ only in ZWNJ/letter variants."""
    rows = _persian_index().get(key(word), [])
    w = unicodedata.normalize("NFC", (word or "").strip())
    rows = sorted(rows, key=lambda r: r[0] != w)
    return list(dict.fromkeys(f for r in rows for f in r[1]))


def persian_forms(word, roman_form=""):
    """[(form, how)] for a Persian word from KaamelDict, best first, and a flag (or
    ''). roman_form: the word's Wiktionary reading in Globasa letters; it only picks
    among the dictionary's variants (formal kabab / colloquial kebab). On 1179
    LexiliAsel Persian etymons with both: first variant = Wiktionary 82%, some
    variant 91%, within one edit 95%."""
    forms = [f.replace(" ", "") for f in persian(word)]
    if not forms:
        return [], ""
    flag = ""
    if roman_form in forms:
        forms.insert(0, forms.pop(forms.index(roman_form)))
        why = "Wiktionary's reading picks this variant"
    else:
        why = "first listed"
        if len(forms) > 1:
            flag = f"KaamelDict lists {len(forms)} pronunciations; the first listed is taken"
    return [(f, f"KaamelDict ({why if i == 0 else 'other variant'})") for i, f in enumerate(forms)], flag
