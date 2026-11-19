#!/usr/bin/env python3
"""Pronoun gender by interpretation, for apertium-hbo-glb.

    python3 pronouns.py tag curated/pronouns.tsv < STREAM > STREAM   (pipeline, before prep_stream.py)
    python3 pronouns.py suggest [STREAM]                              (for the translator)

Hebrew grammar marks gender in the second and third person, but which Globasa pronoun a
person deserves is often interpretation: a masculine plural also addresses mixed groups
(Gen 1:28, to humanity "male and female"), and third-person gender is grammatical (הוּא is
also "it": לְמִינֵהוּ "its kind"). The rtx therefore renders pronouns as te/ete/uyu… by default,
with only the second-person singular and the feminine plural gendered automatically
(GENDER=1, rules "p_gender"). Every other choice is the translator's, made per occurrence:

curated/pronouns.tsv, one line per word, '#' comments:

    WORD-ID<TAB>Globasa pronoun<TAB>note

  WORD-ID   the <id:N> of the Hebrew word in the passage stream (`suggest` lists them)
  pronoun   mante femte te to · manete femete ete oto · manyu femyu yu · manuyu femuyu uyu
            · manmi femmi mi · imi (only its gender is used; person and number come from the
            Hebrew, and a mismatch is reported on stderr)
            · sesu: a possessive suffix whose possessor is the clause subject (rendering.md
            "Possessives": Gen 1:27 בְּצַלְמוֹ, God created … in his own image)
  note      free text: the reason (e.g. "Gen 1:27 humanity, generic → te")

The entry applies to the word's pronoun part (suffix or independent pronoun), or, when the
word has none, to its verb: the subject pronoun the rtx inserts from verb agreement
(Gen 1:5 ל-X קרא Y → "te namegi X Y"). te/ete stay right for concise prose and generic
statements; to/oto mark an inanimate referent.
"""

import re
import sys
import unicodedata

UNIT = re.compile(r"\^([^/$]+)/([^$]+)\$")
ID = re.compile(r"<id:(\d+)>")
VERSE = re.compile(r"\[([A-Za-z0-9]+\.\d+\.\d+)\]")

# Globasa pronoun → (gender tag the rtx reads, person, number)
PRONOUNS = {
    "mante": ("igm", "p3", "sg"), "femte": ("igf", "p3", "sg"),
    "te": ("igut", "p3", "sg"), "to": ("ignt", "p3", "sg"),
    "manete": ("igm", "p3", "pl"), "femete": ("igf", "p3", "pl"),
    "ete": ("igut", "p3", "pl"), "oto": ("ignt", "p3", "pl"),
    "manyu": ("igm", "p2", "sg"), "femyu": ("igf", "p2", "sg"), "yu": ("igut", "p2", "sg"),
    "manuyu": ("igm", "p2", "pl"), "femuyu": ("igf", "p2", "pl"), "uyu": ("igut", "p2", "pl"),
    "manmi": ("igm", "p1", "sg"), "femmi": ("igf", "p1", "sg"), "mi": ("igut", "p1", "sg"),
    "imi": ("igut", "p1", "pl"),
    "sesu": ("igse", None, None),
}


def load(path):
    table = {}
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) < 2 or cols[1].strip() not in PRONOUNS:
            print(f"{path}:{n}: not 'WORD-ID<TAB>pronoun' with a known pronoun: {line!r}",
                  file=sys.stderr)
            continue
        table[cols[0].strip()] = cols[1].strip()
    return table


def parts_of(analysis):
    return analysis.split("+")


def tag_unit(m, table):
    surface, analysis = m.group(1), m.group(2)
    ids = ID.findall(analysis)
    if not ids or ids[0] not in table:
        return m.group(0)
    word_id, glb = ids[0], table[ids[0]]
    gtag, person, number = PRONOUNS[glb]
    readings = analysis.split("/")
    out = []
    for reading in readings:
        parts = parts_of(reading)
        target = next((i for i, p in enumerate(parts) if "<prn>" in p), None)
        if target is None and person is None:
            print(f"pronouns: {word_id} {surface}: {glb} needs a pronoun suffix", file=sys.stderr)
        elif target is None:
            target = next((i for i, p in enumerate(parts) if "<v>" in p), None)
        if target is not None:
            p = parts[target]
            tags = re.findall(r"<([^>]+)>", p)
            if (person and person in tags and number not in tags and "<prn>" in p
                    and not (number == "pl" and "du" in tags)):
                print(f"pronouns: {word_id} {surface}: {glb} is {number}, the Hebrew is not",
                      file=sys.stderr)
            parts[target] = ID.sub(lambda i: f"<{gtag}>" + i.group(0), p, count=1) \
                if ID.search(p) else p + f"<{gtag}>"
        out.append("+".join(parts))
    return f"^{surface}/{'/'.join(out)}$"


def tag(table_path):
    table = load(table_path)
    for line in sys.stdin:
        sys.stdout.write(UNIT.sub(lambda m: tag_unit(m, table), line))


def suggest(path):
    text = open(path, encoding="utf-8").read() if path else sys.stdin.read()
    print("# WORD-ID\tGlobasa pronoun\tnote    (fill the second column; the default is te/ete/yu…)")
    verse = ""
    for line in text.splitlines():
        pos = 0
        for m in re.finditer(r"\[[^\]]*\]|\^[^$]*\$", line):
            tok = m.group(0)
            vm = VERSE.search(tok)
            if vm:
                verse = vm.group(1)
                continue
            um = UNIT.match(tok)
            if not um:
                continue
            surface, analysis = um.group(1), um.group(2).split("/")[0]
            for p in parts_of(analysis):
                if "<prn>" in p and "<pers>" in p:
                    tags = re.findall(r"<([^>]+)>", p)
                    pgn = " ".join(t for t in tags if t in ("p1", "p2", "p3", "m", "f", "sg", "pl", "du"))
                    wid = ID.search(p)
                    print(f"#{wid.group(1) if wid else '?'}\t\t{verse} "
                          f"{unicodedata.normalize('NFC', surface)} ({pgn})")


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
