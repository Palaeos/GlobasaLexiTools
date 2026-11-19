# Siri-Logane Tutum as an existing witness for rendering 19th-century English
# in Globasa: Poe, "The Tell-Tale Heart" (1843) was translated into Globasa
# via a modernized English rewrite. The chain
#     Poe 1843  ->  modernized English  ->  Globasa
# shows (a) which old words a human modernizer judged opaque and what he
# replaced them with, (b) how the Globasa translator then rendered that
# plain sense. It calibrates the Time Machine pipeline:
#   - scanner check: Zipf < 3 flags (scan_obscure.py's rule) on Poe vs the
#     words the modernizer actually changed;
#   - shared vocabulary: Poe words that are also Time Machine glossary
#     lemmas, with both Globasa renderings side by side.
#
# Inputs (all in the repo): the Globasawiki page (paragraph table: 1843 text |
# modernized English), Doxo_passages.tmx (Siri-Logane Tutum TUs: modernized
# English <-> Globasa sentences, from fill_telltale_english.py), word-list.csv,
# time-machine/obscure_resolved.tsv.
#
# Output: telltale_witness.tsv
#   para, poe, modern, kind (substitution | deletion), zipf (min over the
#   Poe words), flagged (Zipf<3 rule), glb_sentence, glb_words (Globasa words
#   in the TU whose Eng gloss shares a stem with a modern content word),
#   tm_lemma, tm_glb (Time Machine glossary rows with the same lemma)
# and a calibration summary on stdout.
import difflib
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

import pandas as pd
from wordfreq import zipf_frequency

HERE = Path(__file__).parent
ROOT = HERE.parent
HTML = ROOT / "Globasawiki_Basataytilari_The Tell-Tale Heart - Globasawiki.html"
TMX = ROOT / "Doxo_passages.tmx"
TOK = re.compile(r"[A-Za-z]+(?:'[a-z]+)?")
STOP = set("""a an the and or but of to in on at by for with from as is was were be been am are i me my
you your he him his she her it its we us our they them their that this these those which who whom what
not no so very then than there here have has had do did does will would shall should can could may might
must all any some one just too also up down out over into upon""".split())


class Table(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self.row, self.cell, self.inc, self.tab = [], [], "", False, False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table" and "wikitable" in (a.get("class") or ""):
            self.tab = True
        if self.tab and tag == "tr":
            self.row = []
        if self.tab and tag in ("td", "th"):
            self.inc, self.cell = True, ""
            self.span = "colspan" in a

    def handle_endtag(self, tag):
        if self.tab and tag in ("td", "th"):
            self.inc = False
            self.row.append((re.sub(r"\s+", " ", self.cell).strip(), self.span))
        if self.tab and tag == "tr" and self.row:
            self.rows.append(self.row)
        if tag == "table":
            self.tab = False

    def handle_data(self, d):
        if self.inc:
            self.cell += d


t = Table()
t.feed(HTML.read_text(encoding="utf-8"))
pairs = [(r[0][0], r[1][0]) for r in t.rows
         if len(r) == 2 and not r[0][1] and not r[1][1] and r[0][0] not in ("Englisa", "The Tell-Tale Heart")]

X = "{http://www.w3.org/XML/1998/namespace}lang"
tus = []
for tu in ET.parse(TMX).iter("tu"):
    ctx = [p.text for p in tu.findall("prop") if p.get("type") == "x-context"]
    if ctx and "Siri-Logane" in (ctx[0] or ""):
        seg = {v.get(X): (v.find("seg").text or "") for v in tu.findall("tuv")}
        tus.append((seg.get("en", ""), seg.get("glb", "")))

wl = pd.read_csv(ROOT / "word-list.csv", dtype=str)
eng_of = {}
for w, g in zip(wl["Word"].str.lower(), wl["TranslationEng"].fillna("")):
    g = re.sub(r"\b(n|v|adj|adv|v\.tr|v\.intr|prep|conj|interj)\s*:", " ", g)
    eng_of.setdefault(w, set()).update(x.lower() for x in TOK.findall(g) if x.lower() not in STOP)


def stem(w):
    w = w.lower()
    return w[:5] if len(w) > 5 else w


def glb_evidence(modern_words, glb):
    want = {stem(w) for w in modern_words if w.lower() not in STOP}
    out = []
    for tok in re.findall(r"[a-zA-Z\-]+", glb):
        k = tok.lower()
        cands = [k] + [k[:i] for i in range(len(k) - 1, 2, -1)]  # inflected/derived: try listed prefixes
        for c in cands:
            if c in eng_of and want & {stem(g) for g in eng_of[c]}:
                out.append(tok)
                break
    return out


def best_tu(sentence):
    best, bt = 0.0, ("", "")
    for en, glb in tus:
        r = difflib.SequenceMatcher(None, sentence.lower(), en.lower()).ratio()
        if r > best:
            best, bt = r, (en, glb)
    return bt if best >= 0.5 else ("", "")


def spellish(a, b):
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio() >= 0.8


tm = {}
tm_path = HERE / "obscure_resolved.tsv"
lines = tm_path.read_text(encoding="utf-8").rstrip("\n").split("\n")
hdr = lines[0].split("\t")
for ln in lines[1:]:
    r = dict(zip(hdr, ln.split("\t")))
    if r["verdict"] != "transparent" and r["glb"]:
        tm.setdefault(r["lemma"].lower(), set()).add(r["glb"])

rows = []
changed_words, poe_words = set(), set()
for p, (poe, mod) in enumerate(pairs, 1):
    pw, mw = poe.split(), mod.split()
    msents = re.split(r"(?<=[.!?])\s+", mod)
    for op, a, b, c, d in difflib.SequenceMatcher(None, pw, mw, autojunk=False).get_opcodes():
        if op not in ("replace", "delete"):
            continue
        old, new = " ".join(pw[a:b]), " ".join(mw[c:d])
        oldw = [w.lower() for w in TOK.findall(old)]
        content = [w for w in oldw if w not in STOP]
        if not content or len(pw[a:b]) > 6 or (new and spellish(old, new)):
            continue
        changed_words.update(content)
        z = min(zipf_frequency(w, "en") for w in content)
        # the modern sentence holding the replacement
        pos = len(" ".join(mw[:c]))
        acc, sent = 0, msents[-1]
        for s in msents:
            acc += len(s) + 1
            if acc > pos:
                sent = s
                break
        en, glb = best_tu(sent) if new else ("", "")
        gw = glb_evidence(TOK.findall(new), glb) if new else []
        tm_l = [w for w in content if w in tm]
        rows.append({"para": p, "poe": old, "modern": new or "—", "kind": "substitution" if new else "deletion",
                     "zipf": f"{z:.2f}", "flagged": "yes" if z < 3 else "",
                     "glb_sentence": glb, "glb_words": " ".join(gw),
                     "tm_lemma": " ".join(tm_l), "tm_glb": " / ".join(sorted(tm[tm_l[0]])) if tm_l else ""})
    poe_words.update(w.lower() for w in TOK.findall(poe))

with open(HERE / "telltale_witness.tsv", "w", encoding="utf-8") as f:
    cols = list(rows[0].keys())
    f.write("\t".join(cols) + "\n")
    for r in rows:
        f.write("\t".join(str(r[c]).replace("\t", " ") for c in cols) + "\n")

# calibration: which Poe content words does the Zipf rule flag, and how many
# of those did the modernizer change?
flag = {w for w in poe_words if w not in STOP and zipf_frequency(w, "en") < 3}
hit = flag & changed_words
print(f"{len(pairs)} paragraph pairs, {len(tus)} TUs, {len(rows)} modernizations")
print(f"Zipf<3 flags in Poe: {len(flag)}; changed by the modernizer: {len(hit)} "
      f"({100 * len(hit) / max(len(flag), 1):.0f}%)")
print("  flagged, kept by modernizer:", ", ".join(sorted(flag - changed_words)))
common = sorted(w for w in changed_words - flag if w.isalpha())
print(f"changed but NOT flagged (Zipf>=3; dated-sense / register candidates): {len(common)}")
print("  ", ", ".join(common))
print("shared with the Time Machine glossary:", sum(1 for r in rows if r["tm_lemma"]))
