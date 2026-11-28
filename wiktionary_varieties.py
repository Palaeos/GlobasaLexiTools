"""Language identity of Wiktionary translation items (functions only, safe to import).

wiktextract files a Wiktionary sub-line such as "*: Bavarian:" under German with the
parent code (lang_code "de") and keeps the variety only in the `lang` field
("Bavarian German"); older dumps also used dialect tags ("Alemannic-German") and
Wiktionary-only codes ("nds-de"). The parsers stored the code alone, so Bavarian
"Wossa" became German (found 2026-11-28 on sui).

resolve() gives every item the identity curated in translation_varieties.tsv
(user 2026-11-28: mutual intelligibility, following SIL's ISO 639-3 individual
languages):
  - an individual language of its own -> filed under that code (Bavarian -> bar)
  - a variety without an ISO code     -> kept under its language, tag view:<X>
                                         (Austrian German -> de + view:Austria)
  - misfiled / dialect group          -> None (set aside)
  - a name the list does not know under a code it covers -> None, and counted in
    UNKNOWN for the report: new names are decided in the list, never guessed.

Used by JSONL parser 2.py, wiktionary_extract.py and Wiktionary concept index.py.
"""
import csv
import os
from collections import Counter

VARIETIES_TSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "translation_varieties.tsv")
REPORT_TSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "translation_varieties_report.tsv")
VIEW_PREFIX = "view:"

UNKNOWN = Counter()   # (code, name) -> items set aside because the list has no row
OUTCOMES = Counter()  # (kind, code, name, target) -> items resolved by a row


def _load(path=VARIETIES_TSV):
    names, tags, codes = {}, {}, {}
    with open(path, encoding="utf-8", newline="") as f:
        rows = csv.reader((line for line in f if not line.startswith("#")), delimiter="\t")
        header = next(rows)
        if header[:4] != ["kind", "code", "name", "target"]:
            raise SystemExit(f"{path}: unexpected header {header}")
        for row in rows:
            if not row or not row[0].strip():
                continue
            kind, code, name, target = (c.strip() for c in row[:4])
            if kind == "name":
                names[(code, name)] = target
            elif kind == "tag":
                tags[name] = target
            elif kind == "code":
                codes[code] = target
            else:
                raise SystemExit(f"{path}: unknown kind {kind!r} in {row}")
    covered = frozenset(code for code, _ in names)
    return names, tags, codes, covered


_NAMES, _TAGS, _CODES, COVERED = _load()


def _apply(code, target, tags, parent=None):
    """(code, tags) for a target; None when set aside."""
    if target == "exclude":
        return None
    if target == "same":
        return code, tags
    if target.startswith(VIEW_PREFIX):
        return (parent or code), tags + [target]
    return target, tags


def resolve(code, lang, tags):
    """(code, tags) of a translation item after identity resolution, or None to drop it.

    code: lang_code / code of the item; lang: its `lang` name; tags: list of tags."""
    tags = list(tags or ())
    for tag in tags:
        if tag in _TAGS:
            # Old-style dialect tag: the tag *is* the identity, so it is consumed.
            target = _TAGS[tag]
            OUTCOMES[("tag", code, tag, target)] += 1
            return _apply(code, target, [t for t in tags if t != tag])
    if code in _CODES:
        target = _CODES[code]
        OUTCOMES[("code", code, "*", target)] += 1
        return _apply(code, target, tags, parent=code.split("-")[0])
    if code in COVERED:
        target = _NAMES.get((code, lang))
        if target is None:
            UNKNOWN[(code, lang)] += 1
            return None
        if target != "same":
            OUTCOMES[("name", code, lang, target)] += 1
        return _apply(code, target, tags)
    return code, tags


def write_report(path=REPORT_TSV):
    """What the list decided, and the names it does not know yet (set aside)."""
    with open(path, "w", encoding="utf-8") as f:
        f.write("status\tkind\tcode\tname\ttarget\titems\n")
        for (code, name), n in UNKNOWN.most_common():
            f.write(f"UNKNOWN (set aside: add a row)\tname\t{code}\t{name}\t\t{n}\n")
        for (kind, code, name, target), n in sorted(OUTCOMES.items()):
            f.write(f"resolved\t{kind}\t{code}\t{name}\t{target}\t{n}\n")
    return path
