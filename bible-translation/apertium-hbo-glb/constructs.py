#!/usr/bin/env python3
"""Construct chains by interpretation, for apertium-hbo-glb.

    python3 constructs.py tag curated/constructs.tsv < STREAM > STREAM   (pipeline, before prep_stream.py)
    python3 constructs.py suggest [STREAM]                                (for the translator)

Hebrew's construct state (סְמִיכוּת) does not say how the two nouns relate; Globasa does
(rendering.md "Construct chains"): `X de Y` "X belonging to Y" (possession), `X fe Y` "X
relating to Y" (kind, category, material, place, part: grammar 03 § Fe). The rtx default:
`de` when the dependent is a person (the `persons` list in the rtx: God, humans, kin,
office holders), `fe` otherwise — `fe` claims only a relation, so it is the safe default.
An adjective after a chain attaches by agreement: to the head when it agrees with the
head only (`day vento de Teo`), otherwise to the dependent (`vento de day Teo`).

curated/constructs.tsv, one line per construct head, '#' comments:

    WORD-ID<TAB>options<TAB>note

  WORD-ID   the <id:N> of the head noun (the one in the construct state; `suggest` lists them)
  options   comma-separated: de | fe (the relation), head | dep (where a following adjective
            attaches, when agreement leaves it open). de/fe on a noun the source tagged
            absolute also makes it a construct head (a reading: segolates look the same in
            both states; ETCBC and UD read Gen 1:30 יֶרֶק עֵשֶׂב as absolute + apposition).
  note      free text: the reason

`suggest` prints every construct head with the rtx default, plus two kinds of candidates
for an entry: noun + noun pairs not tagged construct whose first noun could still be a
construct head (no article, no disjunctive accent: Gen 1:30 יֶ֥רֶק עֵ֖שֶׂב; the filter
drops Gen 1:11 דֶּ֔שֶׁא עֵ֚שֶׂב, an apposition), and adjectives after a chain that agree with both
nouns (attached to the dependent by default).
"""

import os
import re
import sys
import unicodedata

UNIT = re.compile(r"\^([^/$]+)/([^$]+)\$")
ID = re.compile(r"<id:(\d+)>")
VERSE = re.compile(r"\[([A-Za-z0-9]+\.\d+\.\d+)\]")
HERE = os.path.dirname(os.path.abspath(__file__))
RTX = os.path.join(HERE, "apertium-hbo-glb.hbo-glb.rtx")

# option -> tag the rtx reads
OPTIONS = {"de": "rde", "fe": "rfe", "head": "ahd", "dep": "adp"}


def nfc(s):
    return unicodedata.normalize("NFC", s)


def persons():
    """The rtx `persons` lemma list, so `suggest` shows the default the rtx applies."""
    m = re.search(r"^persons\s*=\s*([^;]*);", open(RTX, encoding="utf-8").read(), re.M)
    return set(nfc(m.group(1)).split()) if m else set()


def load(path):
    table = {}
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        cols = line.split("\t")
        opts = [o.strip() for o in cols[1].split(",")] if len(cols) > 1 else []
        if not opts or any(o not in OPTIONS for o in opts) \
                or ("de" in opts and "fe" in opts) or ("head" in opts and "dep" in opts):
            print(f"{path}:{n}: not 'WORD-ID<TAB>de|fe[,head|dep]': {line!r}", file=sys.stderr)
            continue
        table[cols[0].strip()] = opts
    return table


def tag_unit(m, table):
    surface, analysis = m.group(1), m.group(2)
    ids = ID.findall(analysis)
    if not ids or ids[0] not in table:
        return m.group(0)
    opts = table[ids[0]]
    out = []
    for reading in analysis.split("/"):
        parts = reading.split("+")
        i = next((i for i, p in enumerate(parts) if re.match(r"[^<]*<n>", p)), None)
        if i is None:
            print(f"constructs: {ids[0]} {surface}: no noun in {reading!r}", file=sys.stderr)
        else:
            p = parts[i]
            if {"head", "dep"} & set(opts):          # curated attachment replaces the treebank's
                p = p.replace("<ahd>", "").replace("<adp>", "")
            add = ("" if "<cons>" in p or not ({"de", "fe"} & set(opts)) else "<cons>") \
                + "".join(f"<{OPTIONS[o]}>" for o in opts)
            parts[i] = ID.sub(lambda x: add + x.group(0), p, count=1) if ID.search(p) else p + add
        out.append("+".join(parts))
    return f"^{surface}/{'/'.join(out)}$"


def tag(table_path):
    table = load(table_path)
    for line in sys.stdin:
        sys.stdout.write(UNIT.sub(lambda m: tag_unit(m, table), line))


# Masoretic disjunctive accents (U+0591-U+05A2 except the conjunctives, U+05AE zarqa): a
# construct head is normally joined to its dependent by a conjunctive accent or maqaf
DISJUNCTIVE = set(map(chr, [*range(0x0591, 0x05A3), 0x05AE])) - {"\u05A3", "\u05A4", "\u05A5",
                                                                "\u05A6", "\u05A7", "\u05A8"}


def words(text):
    """(verse, surface, word id, first-reading parts, has article) per unit, maqaf and
    article dropped from the parts."""
    verse = ""
    for line in text.splitlines():
        for m in re.finditer(r"\[[^\]]*\]|\^[^$]*\$", line):
            tok = m.group(0)
            vm = VERSE.search(tok)
            if vm:
                verse = vm.group(1)
                continue
            um = UNIT.match(tok)
            if not um:
                continue
            reading = nfc(um.group(2).split("/")[0])
            wid = ID.search(reading)
            parts = [ID.sub("", p) for p in reading.split("+")
                     if not re.match(r"[^<]*<(det|hyph)>", p)]
            if parts:
                yield (verse, nfc(um.group(1)), wid.group(1) if wid else "?", parts,
                       "<det><def>" in reading)


def lemma_tags(part):
    m = re.match(r"([^<]*)((?:<[^>]+>)*)", part)
    return m.group(1), re.findall(r"<([^>]+)>", m.group(2))


def agree(a, b):
    """Hebrew adjective agreement in gender and number (dual nouns take plural adjectives)."""
    num = lambda t: "pl" if "du" in t else next((x for x in ("sg", "pl") if x in t), "")
    gen = lambda t: next((x for x in ("m", "f") if x in t), "")
    return gen(a) == gen(b) and num(a) == num(b)


def treebank_reading(wid, next_wid, tb):
    """How UD PTNK relates the next word's noun to this word: smixut, appos, amod …"""
    a, b = tb.get(wid, []), tb.get(next_wid, [])
    na = [t for t in a if t["upos"] in ("NOUN", "PROPN")]
    nb = [t for t in b if t["upos"] in ("NOUN", "PROPN", "ADJ")]
    if not na or not nb:
        return ""
    t = nb[-1]
    head = t["sent"].get(t["head"])
    if head is na[-1]:
        return f"; treebank: {t['rel']}"
    return f"; treebank: {t['rel']} of {head['lemma'] if head else 'root'}"


def suggest(path):
    text = open(path, encoding="utf-8").read() if path else sys.stdin.read()
    pers = persons()
    try:
        import syntax
        tb = syntax.load(syntax.UD_DIR) if os.path.isdir(syntax.UD_DIR) else {}
    except ImportError:
        tb = {}
    ws = list(words(text))
    print("# WORD-ID\toptions\tnote    (de | fe, and head | dep for a following adjective; "
          "blank = the rtx default shown)")
    for k, (verse, surf, wid, parts, art) in enumerate(ws):
        last = parts[-1]
        lem, tags = lemma_tags(last)
        if "n" not in tags or k + 1 >= len(ws):
            continue
        nxt = ws[k + 1]
        nlem, ntags = lemma_tags(nxt[3][0])
        if "cons" in tags and lem != "כל":
            if "prn" in ntags or "n" not in ntags and "np" not in ntags:
                continue
            default = "de" if nlem in pers else "fe"
            why = f"dependent {nlem} is a person" if nlem in pers else "dependent not in persons"
            line = f"#{wid}\t\t{verse} {surf} {nxt[1]}: default {default} ({why})"
            if k + 2 < len(ws):
                alem, atags = lemma_tags(ws[k + 2][3][0])
                if "adj" in atags and agree(atags, tags) and agree(atags, ntags):
                    line += (f"; adjective {ws[k + 2][1]} agrees with both nouns: "
                             f"dep (fallback: agreement leaves it open)")
            print(line + treebank_reading(wid, nxt[2], tb))
        elif "cons" not in tags and len(parts) == 1 and "n" in ntags and len(nxt[3]) == 1 \
                and lem != "כל" and not art and not DISJUNCTIVE & set(surf):
            print(f"#{wid}\t\t{verse} {surf} {nxt[1]}: noun + noun, not tagged construct: "
                  f"apposition by default; de/fe makes it a chain"
                  + treebank_reading(wid, nxt[2], tb))


if __name__ == "__main__":
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "tag" and len(sys.argv) > 2:
        tag(sys.argv[2])
    elif cmd == "suggest":
        suggest(sys.argv[2] if len(sys.argv) > 2 else "")
    else:
        sys.exit(__doc__)
