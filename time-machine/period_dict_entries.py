"""Loaders of the period bilingual dictionaries (OCR in cache/dicts/, fetched by period_dicts.py).

    load(all_entries=False)  {"rhodes", "oconnor", "velazquez"}: {headword: entry text}; with
                             all_entries=True {headword: [entry text, ...]} (a headword can have
                             several entries, e.g. Velázquez Remark s. and Remark va.)
    lookup(d, lemma)         (key, value) for the lemma or a simple variant of it
    fold(s), stem(w)         accent folding, 5-letter stems (OCR loses supersigns: baldaŭ ->
                             "baldat")
Sources: Rhodes 1908 and O'Connor & Hayes 1907 (English-Esperanto), Velázquez 1910 vol. 2
(English-Spanish); see period_dicts.py."""
import re
import unicodedata
from pathlib import Path

CACHE = Path(__file__).parent / "cache" / "dicts"


def fold(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def stem(w):
    w = fold(w)
    return w[:5] if len(w) > 5 else w


def _add(out, head, text, all_entries):
    if all_entries:
        out.setdefault(head, []).append(text)
    else:
        out.setdefault(head, text)


def blank_entries(text, all_entries=False):
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
            _add(out, head, " ".join(buf), all_entries)
        head, buf = m.group(1).strip(), [b[m.end():]]
    if head:
        _add(out, head, " ".join(buf), all_entries)
    return out


def entries(text, start, all_entries=False):
    """Split OCR text into {headword: entry text} at lines matching start."""
    out, head, buf = {}, None, []
    clean = lambda v: re.sub(r"-\s+", "", re.sub(r"\s+", " ", v)).strip()
    for ln in text.splitlines():
        m = start.match(ln)
        if m:
            if head:
                _add(out, head, clean(" ".join(buf)), all_entries)
            head, buf = m.group(1).lower().strip(), [ln[m.end():]]
        elif head and ln.strip():
            buf.append(ln.strip())
    if head:
        _add(out, head, clean(" ".join(buf)), all_entries)
    return out


OCONNOR_START = re.compile(r"^([A-Z][a-z' -]*?)\s*[,(]\s*")
# pronunciation token: OCR mangles its brackets, the stress mark ' survives
VELAZ_START = re.compile(r"^([A-Z][a-z'-]*)\s+\S*'\S*\s*")


def load(all_entries=False):
    read = lambda name: (CACHE / name).read_text(encoding="utf-8", errors="replace")
    return {"rhodes": blank_entries(read("rhodes1908.txt"), all_entries),
            "oconnor": entries(read("oconnor1907.txt"), OCONNOR_START, all_entries),
            "velazquez": entries(read("velazquez1910_v2.txt"), VELAZ_START, all_entries)}


def lookup(d, lemma):
    l = lemma.lower()
    cands = [l, l.rstrip("s"), re.sub(r"(ly|ed|ing)$", "", l)]
    if " " in l:
        cands.append(max(l.split(), key=len))
    for c in cands:
        if c in d:
            return c, d[c]
    return None, "" if not d or not isinstance(next(iter(d.values())), list) else []
