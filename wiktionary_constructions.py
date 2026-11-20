"""Verb constructions from the English Wiktionary dump: the governed prepositions and the
reflexive senses of German, Dutch, French and Spanish verbs, sense by sense.

English Wiktionary marks a governed preposition on the sense itself, with {{+obj}}:
    warten  (intransitive) to wait (for) [+ auf (accusative)]
and reflexive senses with a tag, often naming the preposition in the label:
    freuen  (reflexive, + auf) to look forward to
These are what the Apertium pairs need for "warten auf -> intizar X" and
"sich ärgern über X -> Mi ganjon gadibu tem X" (verb_constructions.py turns them into
proposals, verb_constructions.tsv holds the decisions).

    rows()          the cached constructions (dicts), building the cache if needed
    build(source)   one streaming pass over the dump -> CACHE_TSV

Run directly to (re)build the cache:
    python wiktionary_constructions.py [dump path or URL]

The dump is streamed line by line and never stored; only matching senses are kept
(.wolf/optimizations.md). The cache is rebuilt only when the dump is newer.
"""
import os
import re
import sys

try:
    import orjson
    _loads = orjson.loads
except ImportError:
    import json
    _loads = json.loads

from word_selection import dump

CACHE_DIR = "constructions_cache"
CACHE_TSV = os.path.join(CACHE_DIR, "wiktionary_constructions.tsv")
COLUMNS = ["lang", "verb", "sense", "reflexive", "prep", "case", "gloss", "label"]
LANGS = ("de", "nl", "fr", "es")

# Prepositions recognised in sense labels ("(reflexive, + auf)", "often with um (about)").
PREPS = {
    "de": ["an", "auf", "aus", "bei", "durch", "für", "gegen", "in", "mit", "nach", "um",
           "über", "unter", "von", "vor", "zu", "zwischen"],
    "nl": ["aan", "achter", "bij", "door", "in", "met", "na", "naar", "om", "onder", "op",
           "over", "tegen", "tot", "uit", "van", "voor"],
    "fr": ["à", "avec", "contre", "dans", "de", "en", "envers", "par", "pour", "sur", "vers",
           "chez", "entre"],
    "es": ["a", "con", "contra", "de", "en", "entre", "hacia", "para", "por", "sin", "sobre",
           "tras", "desde", "hasta"],
}
CASES = r"(accusative|dative|genitive)"
# {{+obj}} renders as "[+ auf (accusative)]", "[+ dative]", "[+ bei (“to”), + für (“for”)]"
MARKING = re.compile(r"\[\+([^\]]*)\]")
PLUS = {lang: re.compile(r"\+\s*(" + "|".join(map(re.escape, ps)) + r")\b(?:\s*\(?" + CASES + r"\)?)?")
        for lang, ps in PREPS.items()}
WITH = {lang: re.compile(r"\bwith\s+(" + "|".join(map(re.escape, ps)) + r")\b")
        for lang, ps in PREPS.items()}
LOCAL_COPY = os.path.join(dump.LOCAL_DIR, "raw-wiktextract-data.json.gz")   # this machine's name


def default_source():
    """dump.source("en"), but this machine's copy under its own name before the URL."""
    src = dump.source("en")
    if src.startswith(("http://", "https://")) and os.path.exists(LOCAL_COPY):
        return LOCAL_COPY
    return src


CASE_ABBR = {"acc": "accusative", "dat": "dative", "gen": "genitive"}
OBJ_ARG = re.compile(r"^:?([^(<]*?)\s*(?:\(([a-z]+)\))?\s*(?:<.*)?$")


def _obj_template(sense):
    """(prep, case) pairs from the sense's {{+obj}} templates (wiktextract 2025: info_templates,
    args {"2": ":auf(acc)", "3": ":für"}; a bare "acc"/"dat" is a case without a preposition)."""
    out = []
    for t in sense.get("info_templates") or ():
        if t.get("name") != "+obj":
            continue
        args = t.get("args") or {}
        for k in sorted((k for k in args if k.isdigit() and int(k) >= 2), key=int):
            m = OBJ_ARG.match(str(args[k]).strip())
            if not m:
                continue
            word, case = m[1].strip(), CASE_ABBR.get(m[2] or "", m[2] or "")
            if word in CASE_ABBR:                       # {{+obj|de|dat}}: a dative object
                word, case = "", CASE_ABBR[word]
            if word and not args[k].startswith(":") and " " in word:
                continue                                # free text, not a preposition
            out.append((word, case))
    return out


def _preps(lang, gloss, label, sense=None):
    """(prep, case) pairs a sense names: its {{+obj}} templates (2025 dumps), else {{+obj}}
    markings left in the gloss (older dumps), then the label's "+ auf" / "with um". A marking
    with a case but no preposition (a dative object) is kept with an empty prep."""
    out = _obj_template(sense) if sense else []
    if out:
        return list(dict.fromkeys(out))
    for m in MARKING.finditer(gloss):
        body = m[1]
        found = PLUS[lang].findall("+" + body.replace(",", ", +"))
        if found:
            out += [(p, c) for p, c in found]
        else:
            c = re.search(CASES, body)
            out.append(("", c[1] if c else ""))
    if not out:
        head = label.split(")", 1)[0] if label.startswith("(") else ""
        out = PLUS[lang].findall(head) or [(p, "") for p in WITH[lang].findall(head)]
    return list(dict.fromkeys(out))


def build(source=None):
    """One pass over the dump: every verb sense of LANGS that names a governed preposition
    or is reflexive. Written to CACHE_TSV via a temporary file."""
    source = source or default_source()
    os.makedirs(CACHE_DIR, exist_ok=True)
    tmp = CACHE_TSV + ".building"
    n_lines = n_rows = 0
    lang_re = re.compile(r'"lang_code": "(' + "|".join(LANGS) + r')"')
    with open(tmp, "w", encoding="utf-8") as out, dump.open_lines(source) as lines:
        out.write("\t".join(COLUMNS) + "\n")
        for line in lines:
            n_lines += 1
            if n_lines % 2_000_000 == 0:
                print(f"  {n_lines // 1_000_000}M lines, {n_rows} senses kept", flush=True)
            if '"pos": "verb"' not in line or not lang_re.search(line):
                continue
            if "+obj" not in line and "[+" not in line and "reflexive" not in line and "+ " not in line:
                continue
            d = _loads(line)
            lang = d.get("lang_code")
            if lang not in LANGS or d.get("pos") != "verb":
                continue
            for i, s in enumerate(d.get("senses", []), 1):
                gloss = (s.get("glosses") or [""])[0]
                label = (s.get("raw_glosses") or [gloss])[0]
                reflexive = "reflexive" in (s.get("tags") or ())
                preps = _preps(lang, gloss, label, s)
                if not preps and not reflexive:
                    continue
                clean = re.sub(r"\s*\[\+[^\]]*\]", "", gloss).strip()
                for prep, case in preps or [("", "")]:
                    row = [lang, d["word"], str(i), "1" if reflexive else "", prep, case,
                           clean, label[:300]]
                    out.write("\t".join(x.replace("\t", " ").replace("\n", " ") for x in row) + "\n")
                    n_rows += 1
    os.replace(tmp, CACHE_TSV)
    print(f"{n_rows} construction senses from {n_lines} dump lines -> {CACHE_TSV}")
    return n_rows


def rows(source=None):
    """The cached constructions as dicts; builds the cache when it is missing or older than
    a local dump."""
    source = source or default_source()
    stale = not os.path.exists(CACHE_TSV) or (
        os.path.exists(source) and os.path.getmtime(source) > os.path.getmtime(CACHE_TSV))
    if stale:
        build(source)
    with open(CACHE_TSV, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        for line in f:
            yield dict(zip(header, line.rstrip("\n").split("\t")))


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else None)
