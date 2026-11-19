# Webster's Revised Unabridged Dictionary (1913; Gutenberg #29765) lookups
# for the Victorian word list: numbered senses with their [Archaic]/[Obs.]/
# [Poetic] labels. Text cached by fetch_sources.py in cache/sources/.
import re
from pathlib import Path

WEBSTER = Path(__file__).parent / "cache" / "sources" / "webster_1913.txt"
_entries = None
LABEL = re.compile(r"\[(Archaic|Obs\.?|Poetic|R\.|Colloq\.|Prov\. Eng\.|Eng\.)\]")


def _load():
    global _entries
    if _entries is not None:
        return _entries
    _entries = {}
    if not WEBSTER.exists():
        return _entries
    head, buf = None, []
    for ln in WEBSTER.read_text(encoding="latin-1").splitlines():
        s = ln.strip()
        if re.fullmatch(r"[A-Z][A-Z' -]+", s) and len(s) > 1:
            if head and head not in _entries:
                _entries[head] = " ".join(buf)
            head, buf = s.lower(), []
        elif head:
            buf.append(s)
    if head and head not in _entries:
        _entries[head] = " ".join(buf)
    return _entries


def senses(lemma):
    """[{n, label, gloss}] for the headword (longest word of a phrase), at most 5,
    numbered 1, 2, 3... (numbers inside quotations are verses, not senses)."""
    e = _load()
    l = lemma.lower()
    text = e.get(l) or e.get(max(l.split(), key=len), "")
    if not text:
        return []
    found = []
    for m in re.finditer(r"(?:^|\s)(\d{1,2})\.\s+(.*?)(?=\s\d{1,2}\.\s|\sSyn\.|\sNote:|$)", text):
        g = m.group(2).strip()
        gloss = re.sub(r"\s+", " ", re.split(r"\s[A-Z][a-z]+\.?\s(?:[a-z]+\.)?\s*$", g)[0])[:140]
        found.append({"n": m.group(1), "label": ", ".join(LABEL.findall(g)), "gloss": gloss})
    run = []
    for s in found:
        if s["n"] == str(len(run) + 1):
            run.append(s)
    if not run:
        m = re.search(r"Defn:\s*(.*?)(?=\s[A-Z][a-z]+\.$|$)", text)
        if m:
            run = [{"n": "", "label": ", ".join(LABEL.findall(m.group(1))), "gloss": m.group(1)[:140]}]
    return run[:5]


def is_period(lemma):
    """Webster marks some sense of the headword archaic, obsolete or poetic."""
    return any(re.search(r"Archaic|Obs|Poetic", s["label"]) for s in senses(lemma))
