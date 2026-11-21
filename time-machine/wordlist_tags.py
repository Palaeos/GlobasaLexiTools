"""Shared helpers of the Victorian word list (victorian_wordlist.tsv = source of truth).

Used by victorian_wordlist.py (sync/check) and period_glb.py (proposals --apply), so both write
rows the same way.

    read_tsv(path)                  (header, [row dicts])
    write_wordlist(rows)            rewrite victorian_wordlist.tsv in COLS order
    analyse(binary, words)          {word: [(lemma, [tags])]} via lt-proc
    inherent(tags)                  tags that belong to the lemma (not inflection)
    eng_lemma_tags(surface, eng)    (lemma, eng_tags) from the English analysis
    glb_tags_for(g, eng_tags, glb)  Globasa tags for a one-word rendering ("" for a phrase)"""
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
WL = HERE / "victorian_wordlist.tsv"
GLOSSARY = HERE / "obscure_resolved.tsv"
ENG_AN = ROOT / "GlobasaTranslation" / "apertium-glb-eng" / "eng-glb.automorf-untrimmed.bin"
GLB_AN = ROOT / "GlobasaTranslation" / "apertium-glb" / "glb.automorf.bin"
COLS = ["headword", "eng_tags", "sense", "glb", "glb_tags", "glb_how", "layer", "apertium", "reason",
        "attested", "notes"]
APERTIUM = {"pref", "add", "no", "pending"}
LAYERS = {"period", "rare", "technical"}
NOT_INHERENT = {"compound-R", "cmp", "compound-only-L", "sg", "pl", "past", "pp", "pres", "inf", "pprs",
                "ger", "p3", "comp", "sup", "subj", "obj"}


def read_tsv(path):
    lines = path.read_text(encoding="utf-8").rstrip("\n").split("\n")
    hdr = lines[0].split("\t")
    return hdr, [dict(zip(hdr, ln.split("\t"))) for ln in lines[1:] if ln.strip()]


def write_wordlist(rows):
    with open(WL, "w", encoding="utf-8") as f:
        f.write("\t".join(COLS) + "\n")
        for r in rows:
            f.write("\t".join((r.get(c) or "").replace("\t", " ").replace("\n", " ") for c in COLS) + "\n")


def analyse(binary, words):
    """{word: [(lemma, [tags])]} via lt-proc."""
    if not words or not binary.exists():
        return {}
    out = subprocess.run(["lt-proc", "-w", str(binary)], input="\n".join(words) + "\n",
                         capture_output=True, text=True).stdout.strip().split("\n")
    res = {}
    for w, line in zip(words, out):
        an = []
        for a in line.strip().strip("^$").split("/")[1:]:
            if a.startswith("*"):
                continue
            m = re.match(r"([^<]+)((?:<[^>]+>)*)", a)
            an.append((m.group(1), re.findall(r"<([^>]+)>", m.group(2))))
        res[w] = an
    return res


def inherent(tags):
    return [t for t in tags if t not in NOT_INHERENT]


def eng_lemma_tags(surface, eng):
    """(lemma, eng_tags): smote -> smite; 'mwe' for a multiword headword."""
    lemma = surface.lower()
    if " " in surface:
        return lemma, "mwe"
    an = eng.get(surface, [])
    if an and all(l.lower() != surface.lower() for l, _ in an):
        lemma = an[0][0].lower()
    pos = [t[0] for l, t in an if l.lower() == lemma and t]
    return lemma, pos[0] if pos else ""


def glb_tags_for(g, eng_tags, glb):
    if " " in g:
        return ""
    cands = [inherent(t) for l, t in glb.get(g, []) if inherent(t)]
    same = [t for t in cands if eng_tags and t[0] == eng_tags.split(".")[0]]
    pick = same or cands
    if pick and pick[0][0] == "n":
        nts = [t for t in pick if "nt" in t]
        gds = [t for t in pick if "GD" in t]
        pick = (gds if g.endswith("yen") and gds else nts) or pick
    return ".".join(pick[0]) if pick else ""
