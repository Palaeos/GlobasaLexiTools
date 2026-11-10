"""Constructions: syntactic frames that carry a meaning the bare word does not.

`jixi` alone is "know"; "know how to" only exists as `▯ jixi na ▯`. Such glosses
belong on the construction, not on the word, so `Constructions.xlsx` pairs each
frame with a `to_exclude` list naming the gloss items to lift out of the plain
entry.

Two consumers share this module so the matching rules cannot drift:
`extract_constructions.py`, which lifts them out of `word-list.csv` after a
fresh download, and `AnkiMaker3.py`, which fills the Maxpul Kostrui note fields.
"""
import re

import pandas as pd

CONSTRUCTIONS_XLSX = "Constructions.xlsx"

# Gloss segments open with a part-of-speech annotation ("n: ", "v.tr: ",
# "prep phrs: ", "n (artificially divided): "). It is carried through
# untouched so exclusion never eats the annotation itself.
_ANNOTATION_PREFIX_RE = re.compile(
    r"^(?:n|v\.tr|v\.intr|v\.aux|v\.cop|adj|adv|interj|prep|conj|det|pron|"
    r"num|par|prop\s+\w+|poss\s+\w+|pfx|sfx)"
    r"(?:\s+phrs)?"
    r"(?:\s*\([^)]*\))?"          # optional qualifier in parens
    r"\s*:\s*",
    re.IGNORECASE,
)


def split_items(s):
    """Split on commas that are not inside parentheses. Returns trimmed items."""
    items, cur, depth = [], [], 0
    for ch in s:
        if ch == "(":
            depth += 1
            cur.append(ch)
        elif ch == ")":
            depth = max(0, depth - 1)
            cur.append(ch)
        elif ch == "," and depth == 0:
            items.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if cur:
        items.append("".join(cur).strip())
    return [i for i in items if i]


def split_annotation(seg):
    """Returns (annotation_prefix, body) where prefix includes trailing ': '."""
    s = seg.strip()
    m = _ANNOTATION_PREFIX_RE.match(s)
    if m:
        return s[:m.end()], s[m.end():]
    return "", s


def normalise_item(item):
    """Strip parentheticals (incl. markdown _italics_), collapse whitespace."""
    s = re.sub(r"\s*\([^)]*\)", "", item)
    s = re.sub(r"\s+", " ", s)
    return s.strip(" ,;").lower()


def apply_to_exclude(eng_text, exclude_text):
    """Within-segment item exclusion. For each `; `-separated segment, drop
    comma-separated items (parenthesis-aware) whose normalised form matches
    any item in `exclude_text`. If a segment has no items left, the segment is
    removed entirely; a word whose every gloss is construction-only (`hay`,
    `sengi`) is left with an empty string.

    Returns (new_text, matched). `matched` is False when the rule bit on
    nothing — either the wordlist already had the items lifted out, or
    Constructions.xlsx has gone stale. Callers decide which.
    """
    if not exclude_text or not exclude_text.strip():
        return eng_text, False
    _, excl_body = split_annotation(exclude_text)
    excl_items = {normalise_item(it) for it in split_items(excl_body)}
    excl_items.discard("")
    if not excl_items:
        return eng_text, False
    matched = False
    kept_segments = []
    for seg in eng_text.split("; "):
        prefix, body = split_annotation(seg)
        kept_items = []
        for item in split_items(body):
            if normalise_item(item) in excl_items:
                matched = True
                continue
            kept_items.append(item.strip())
        if kept_items:
            kept_segments.append(prefix + ", ".join(kept_items))
    return "; ".join(kept_segments).strip("; ,"), matched


def load_constructions(path=CONSTRUCTIONS_XLSX):
    """The frame table, indexed by headword. `na_values=False` keeps the
    literal string "NA" a gloss rather than a missing value."""
    frame = pd.read_excel(path, index_col=0, na_values=False)
    frame.fillna(False, inplace=True)
    return frame


def exclusions(frame):
    """headword -> to_exclude text, for the rows that carry one."""
    out = {}
    for lexi, row in frame.iterrows():
        excl = row.get("to_exclude")
        if isinstance(excl, str) and excl.strip():
            out[str(lexi).strip()] = excl
    return out
