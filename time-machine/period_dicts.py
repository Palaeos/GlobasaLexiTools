# Period bilingual dictionaries as sense evidence for obscure_resolved.tsv:
# how English words were rendered into Esperanto and Spanish around 1900,
# i.e. with their 1890s senses (Velázquez even labels old senses "(Ant.)").
#
#   python3 time-machine/period_dicts.py
#
# Sources (Internet Archive OCR, published before 1929 → public domain in the
# US; kept in git-ignored cache/dicts/, only per-row excerpts are committed):
#   rhodes    J. Rhodes, The English-Esperanto Dictionary (1908)
#             englishesperanto0000jose — OCR loses supersigns (baldaŭ →
#             "baldat"), absorbed by the 5-letter stem comparison
#   oconnor   J. C. O'Connor & C. F. Hayes, English-Esperanto Dictionary
#             (1907) englishesperanto00oconuoft
#   velazquez M. Velázquez de la Cadena et al., A New Pronouncing Dictionary
#             of the Spanish and English Languages, vol. 2 English–Spanish
#             (1910) b24860700_0002
#
# Columns added/replaced in obscure_resolved.tsv:
#   dict_epo   Rhodes (+ O'Connor) entry for the lemma, trimmed
#   dict_spa   Velázquez entry, trimmed (sense numbers and "(Ant.)" kept)
#   dict_check epo:agree|differ|none spa:agree|differ|none — does any word
#              of the entry share a 5-letter stem with the Esperanto/Spanish
#              gloss of the row's Globasa word (derived words split into
#              listed parts)? Script tier: "agree" means the Globasa sense is
#              among the period renderings (any sense), "differ" = review.
import re
import unicodedata
import urllib.request
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
CACHE = HERE / "cache" / "dicts"
SOURCES = {
    "rhodes1908.txt": "englishesperanto0000jose/englishesperanto0000jose_djvu.txt",
    "oconnor1907.txt": "englishesperanto00oconuoft/englishesperanto00oconuoft_djvu.txt",
    "velazquez1910_v2.txt": "b24860700_0002/b24860700_0002_djvu.txt",
}
CACHE.mkdir(parents=True, exist_ok=True)
for name, path in SOURCES.items():
    f = CACHE / name
    if not f.exists() or f.stat().st_size < 10000:
        req = urllib.request.Request("https://archive.org/download/" + path, headers={"User-Agent": "GlobasaLexiTools/0.1"})
        f.write_bytes(urllib.request.urlopen(req, timeout=300).read())
        if f.stat().st_size < 10000:
            raise SystemExit(f"{name}: download failed (archive.org error page); re-run")


def blank_entries(text):
    """Rhodes: an entry is a block after a blank line; blocks starting with a
    dash (—— of, to have a, ...) continue the previous headword. Headword =
    text before the first comma or "(" ."""
    out, head, buf = {}, None, []
    for block in re.split(r"\n\s*\n", text):
        b = " ".join(block.split())
        if not b:
            continue
        if b.startswith(("—", "-")) and head:
            buf.append(b)
            continue
        m = re.match(r"([a-z][a-z' -]*?)\s*[,(]\s*", b)
        if not m:
            if head:
                buf.append(b)
            continue
        if head:
            out.setdefault(head, " ".join(buf))
        head, buf = m.group(1).strip(), [b[m.end():]]
    if head:
        out.setdefault(head, " ".join(buf))
    return out


def entries(text, start):
    """Split OCR text into {headword: entry text} at lines matching start."""
    out, head, buf = {}, None, []
    for ln in text.splitlines():
        m = start.match(ln)
        if m:
            if head:
                out.setdefault(head, " ".join(buf))
            head, buf = m.group(1).lower().strip(), [ln[m.end():]]
        elif head and ln.strip():
            buf.append(ln.strip())
    if head:
        out.setdefault(head, " ".join(buf))
    return {k: re.sub(r"-\s+", "", re.sub(r"\s+", " ", v)).strip() for k, v in out.items()}


rhodes = blank_entries((CACHE / "rhodes1908.txt").read_text(encoding="utf-8", errors="replace"))
oconnor = entries((CACHE / "oconnor1907.txt").read_text(encoding="utf-8", errors="replace"),
                  re.compile(r"^([A-Z][a-z' -]*?)\s*[,(]\s*"))
velaz = entries((CACHE / "velazquez1910_v2.txt").read_text(encoding="utf-8", errors="replace"),
                re.compile(r"^([A-Z][a-z'-]*)\s+\S*'\S*\s*"))  # pronunciation token: OCR mangles its brackets, the stress mark ' survives
print(f"entries: rhodes {len(rhodes)}, oconnor {len(oconnor)}, velazquez {len(velaz)}")


def fold(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def stem(w):
    w = fold(w)
    return w[:5] if len(w) > 5 else w


TOK = re.compile(r"[^\W\d_]+", re.U)
STOP = {"kaj", "por", "est", "esti", "the", "que", "del", "los", "las", "una", "con", "para", "ant", "adv",
        "prep", "conj", "pron", "fig", "tre", "pri", "sin", "mas"}
wl = pd.read_csv(HERE.parent / "word-list.csv", dtype=str).set_index("Word")


def parts(word):
    if word in wl.index:
        return [word]
    for i in range(len(word) - 1, 2, -1):
        if word[:i] in wl.index:
            return [word[:i]] + (parts(word[i:]) if len(word) - i > 2 else [])
    return []


def gloss_stems(glb, col):
    out = set()
    for word in re.findall(r"[a-zñA-ZÑ\-]+", glb or ""):
        for key in parts(word if word in wl.index else word.lower()):
            g = wl.loc[key, col]
            g = " ".join(g.dropna()) if isinstance(g, pd.Series) else str(g)
            g = re.sub(r"\b(n|v|adj|adv|s|v\.tr|v\.intr|v\.ntr|prep|conj|interj)\s*:", " ", g)
            g = re.sub(r"_[^_]*_|\([^)]*\)", " ", g)
            out |= {stem(t) for t in TOK.findall(g) if len(t) > 2 and fold(t) not in STOP}
    return out


def lookup(d, lemma):
    l = lemma.lower()
    cands = [l, l.rstrip("s"), re.sub(r"(ly|ed|ing)$", "", l)]
    if " " in l:
        cands.append(max(l.split(), key=len))
    for c in cands:
        if c in d:
            return c, d[c]
    return None, ""


def check(entry, stems):
    if not entry:
        return "none"
    if not stems:
        return "none(no gloss)"
    words = {stem(t) for t in TOK.findall(entry) if len(t) > 2 and fold(t) not in STOP}
    return "agree" if words & stems else "differ"


path = HERE / "obscure_resolved.tsv"
lines = path.read_text(encoding="utf-8").rstrip("\n").split("\n")
hdr = [h for h in lines[0].split("\t") if h not in ("dict_epo", "dict_spa", "dict_check")]
rows = [dict(zip(lines[0].split("\t"), ln.split("\t"))) for ln in lines[1:]]
from collections import Counter

stats = Counter()
for r in rows:
    r["dict_epo"] = r["dict_spa"] = r["dict_check"] = ""
    if r["verdict"] == "transparent":
        continue
    _, e1 = lookup(rhodes, r["lemma"])
    _, e2 = lookup(oconnor, r["lemma"])
    _, s = lookup(velaz, r["lemma"])
    epo = "; ".join(x for x in (e1 and "Rhodes: " + e1[:120], e2 and "O'Connor: " + e2[:80]) if x)
    spa = s[:200]
    ce = check(e1 + " " + e2 if (e1 or e2) else "", gloss_stems(r["glb"], "TranslationEpo"))
    cs = check(spa, gloss_stems(r["glb"], "TranslationSpa"))
    r["dict_epo"], r["dict_spa"] = epo.replace("\t", " "), spa.replace("\t", " ")
    r["dict_check"] = f"epo:{ce.replace(' ', '_')} spa:{cs.replace(' ', '_')}"
    stats["epo:" + ce] += 1
    stats["spa:" + cs] += 1

cols = hdr + ["dict_epo", "dict_spa", "dict_check"]
with open(path, "w", encoding="utf-8") as f:
    f.write("\t".join(cols) + "\n")
    for r in rows:
        f.write("\t".join(r.get(c, "") for c in cols) + "\n")
print(dict(sorted(stats.items())))
