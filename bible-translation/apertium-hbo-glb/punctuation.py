#!/usr/bin/env python3
"""Punctuation by interpretation, for apertium-hbo-glb.

    python3 punctuation.py tag curated/punctuation.tsv < STREAM > STREAM   (pipeline, before prep_stream.py)

Quotation marks are inferred (rendering.md "Speech": `loga: “…”`, draft Gen 1):
  - open after a wayyiqtol of אמר and its subject and addressee, in either order
    (וַיֹּאמֶר לָהֶם אֱלֹהִים → `Teo loga tas ete: “`), or after לֵאמֹר (`, loga: “`);
  - close before the next wayyiqtol (narrative resumes: וַיְהִי־אוֹר → `….” Ji hay lumin`),
    with a full stop inside; when that wayyiqtol starts a verse, after the previous verse
    (speech across verses: 1:14-15, 1:29-30); else at the end of the passage.
  Speech uses jussives, imperatives, weqatal, yiqtol; a wayyiqtol inside speech (a story
  retold, Gen 24:34-48) closes it too early. Corrections in punctuation.tsv: a curated ”
  before the next speech opener replaces the inferred close (add your own `.` before it); `noquote` (position after, on the אמר
  word) drops the inferred quote.

Dashes and parentheses mark structure the stream does not tag: a parenthesis inside a
host clause, an apposition that spells out what precedes (rendering.md "Relative
clauses, parenthesis": short insertions `( … )`, mid-clause insertions dashes). Where
they go is the translator's reading, so they are curated per word, like pronoun gender:

curated/punctuation.tsv, one line per mark, '#' comments:

    WORD-ID<TAB>before|after<TAB>mark<TAB>note

  WORD-ID   the <id:N> of the Hebrew word the mark stands next to (pronouns.py suggest and
            constructs.py suggest list ids; any word of the stream works, also one that is
            not rendered, such as the object marker את)
  mark      —  (  )  :  ;  ,  .  “  ”  , or noquote (see above)
  note      free text: the reason

The mark goes into the stream as its own unit ^—/—<punct>$, which keeps its place
through transfer (a superblank does not: the rtx moves blanks inside chunks), and is a
constituent boundary for the rules. postformat.py spaces it: `X — Y`, `(X)`, `X: Y`; a
dash at the end of a verse replaces the full stop, and the next verse goes on in
lower case (Gen 1:1-2 read as one sentence).
"""

import re
import sys

UNIT = re.compile(r"\^([^/$]+)/([^$]+)\$")
ID = re.compile(r"<id:(\d+)>")
MARKS = "—():;,.“”"


def load(path):
    table = {}
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) < 3 or cols[1].strip() not in ("before", "after") or (cols[2].strip() not in MARKS and cols[2].strip() != "noquote"):
            print(f"{path}:{n}: not 'WORD-ID<TAB>before|after<TAB>mark': {line!r}", file=sys.stderr)
            continue
        table.setdefault(cols[0].strip(), []).append((cols[1].strip(), cols[2].strip()))
    return table


def tag_unit(m, table):
    ids = ID.findall(m.group(2))
    if not ids or ids[0] not in table:
        return m.group(0)
    unit = lambda c: f"^{c}/{c}<punct>$"
    before = [unit(c) for pos, c in table[ids[0]] if pos == "before" and c != "noquote"]
    after = [unit(c) for pos, c in table[ids[0]] if pos == "after" and c != "noquote"]
    return " ".join(before + [m.group(0)] + after)


def first_parts(analysis):
    return [ID.sub("", p) for p in analysis.split("/")[0].split("+")]


def is_wayyiqtol(parts):
    return any("<v>" in p and "<impf>" in p and "<consec>" in p for p in parts)


def infer_quotes(lines, table):
    """{(line, unit index): (before, after)} quotation-mark units, by the rule above."""
    units = []                       # (line, k, parts, word id, verse-first)
    for li, line in enumerate(lines):
        for k, m in enumerate(UNIT.finditer(line)):
            ids = ID.findall(m.group(2))
            parts = first_parts(m.group(2))
            if all(re.match(r"[^<]*<hyph>", p) for p in parts):
                continue
            units.append((li, k, parts, ids[0] if ids else "", not any(
                u[0] == li for u in units)))
    curated_close = {wid for wid, marks in table.items() if any(c == "”" for _, c in marks)}
    no_quote = {wid for wid, marks in table.items() if any(c == "noquote" for _, c in marks)}
    ins = {}
    add = lambda key, side, text: ins.setdefault(key, ([], []))[side].append(text)
    unit = lambda c: f"^{c}/{c}<punct>$"
    i, n = 0, len(units)
    while i < n:
        li, k, parts, wid, _ = units[i]
        said = any(p.startswith("אמר<v>") for p in parts)
        inf = said and any("<inf>" in p for p in parts) and parts[0].startswith("ל<pr>")
        if not said or wid in no_quote or not (inf or is_wayyiqtol(parts)):
            i += 1
            continue
        j = i + 1
        if inf:
            add((li, k), 0, unit(","))
        else:                        # subject and addressee, in either order
            noun = lambda u: re.match(r"[^<]*<n>", u[2][-1]) and not any(
                "<cnjcoo>" in p or "<pr>" in p for p in u[2])
            to = lambda u: u[2][0].startswith("ל<pr>") and any(
                "<prn>" in p or "<n>" in p for p in u[2])
            for _ in range(2):
                if j < n and (noun(units[j]) or to(units[j])):
                    j += 1
                    while j < n and "<cons>" in units[j - 1][2][-1] and noun(units[j]):
                        j += 1       # rest of a construct chain
                else:
                    break
        last = units[j - 1]
        add((last[0], last[1]), 1, unit(":") + " " + unit("“"))
        # close: before the next wayyiqtol, unless the translator placed a ” before the
        # next speech opener (a curated close also spans wayyiqtols: a story retold)
        opener = lambda u: any(p.startswith("אמר<v>") for p in u[2]) and (
            is_wayyiqtol(u[2]) or u[2][0].startswith("ל<pr>"))
        c = next((x for x in range(j, n) if units[x][3] in curated_close), None)
        o = next((x for x in range(j, n) if opener(units[x])), n)
        if c is not None and c < o:
            i = c + 1
            continue
        e = j
        while e < n and not is_wayyiqtol(units[e][2]):
            e += 1
        if e < n and not units[e][4]:
            add((units[e][0], units[e][1]), 0, unit(".") + " " + unit("”"))
        else:                        # speech ended with the previous verse, or the passage
            prev = units[e - 1]
            add((prev[0], prev[1]), 1, unit("”"))
        i = e
    return ins


def tag(table_path):
    table = load(table_path)
    lines = sys.stdin.read().split("\n")
    quotes = infer_quotes(lines, table)
    out = []
    for li, line in enumerate(lines):
        k = iter(range(10 ** 9))

        def sub(m):
            idx = next(k)
            before, after = quotes.get((li, idx), ([], []))
            core = tag_unit(m, table)
            return " ".join(before + [core] + after)
        out.append(UNIT.sub(sub, line))
    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) > 2 and sys.argv[1] == "tag":
        tag(sys.argv[2])
    else:
        sys.exit(__doc__)
