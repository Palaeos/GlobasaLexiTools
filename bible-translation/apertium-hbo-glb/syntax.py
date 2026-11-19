#!/usr/bin/env python3
"""Treebank syntax for apertium-hbo-glb: UD Ancient Hebrew PTNK merged into the stream.

    python3 syntax.py tag [UD_DIR] < STREAM > STREAM      (pipeline, first step)
    python3 syntax.py check [UD_DIR] < STREAM             (alignment report)

UD_DIR (default ../sources/ud, gitignored) holds hbo_ptnk-ud-*.conllu from
https://github.com/UniversalDependencies/UD_Ancient_Hebrew-PTNK (CC BY-SA 4.0; its
morphology is ETCBC BHSA, CC BY-NC 4.0: cached, never committed). It covers Genesis,
Exodus, Leviticus, Numbers, Deuteronomy and Ruth. Without it, or outside its books,
the stream passes unchanged and the rules fall back to word order (labelled in the rtx).

Alignment: the stream's <id:BCCCVVVWW> is MACULA's oBBCCCVVVWWWP without the part P;
the treebank tokens of a word, in order, are its + parts (Gen 1: 434 of 434 words).
A word whose part count differs is left untagged and reported by `check`.

Tags added to a part (before <id>, so later tags keep their adjacency):
  role of the word in its clause, for the rtx clause rules (srole):
    <Snsubj> subject, <Sobj> object, <Sobl> oblique, <Siobj> indirect object,
    <Sxcomp> predicative complement (1:27 זָכָר וּנְקֵבָה בָּרָא אֹתָם, fronted)
    (Gen 1:17 וַיִּתֵּן אֹתָם אֱלֹהִים: אֹתָם obj, אֱלֹהִים nsubj -> `Teo gibe ete`)
  a boundary unit ^¦/¦<punct>$ before a clause that starts with a fronted constituent
  (parataxis/conj/ccomp/advcl clause whose verb is not its first word): the rules do
  not match across it, so the clause before it closes (postformat.py drops it)
  adjective after a construct chain, on the chain's head (cadj, as constructs.py):
    <ahd> the adjective's tree head is the construct head, <adp> it is the dependent
    (replaces the agreement fallback; curated/constructs.tsv still overrides)
"""

import glob
import os
import re
import sys
import unicodedata

UNIT = re.compile(r"\^([^/$]+)/([^$]+)\$")
ID = re.compile(r"<id:(\d+)>")
MACULA = re.compile(r"Ref\[MACULA\]=o(\d{2})(\d{3})(\d{3})(\d{3})")
HERE = os.path.dirname(os.path.abspath(__file__))
UD_DIR = os.path.join(HERE, "..", "sources", "ud")
ROLES = {"nsubj": "Snsubj", "obj": "Sobj", "obl": "Sobl", "iobj": "Siobj", "xcomp": "Sxcomp"}


def load(ud_dir):
    """{stream word id: [token dict, …]} with tokens linked to their sentence."""
    words = {}
    for path in sorted(glob.glob(os.path.join(ud_dir, "*.conllu"))):
        sent = {}
        for line in open(path, encoding="utf-8"):
            line = line.rstrip("\n")
            if not line:
                sent = {}
                continue
            if line.startswith("#"):
                continue
            c = line.split("\t")
            if "-" in c[0] or "." in c[0]:
                continue
            tok = {"id": int(c[0]), "lemma": unicodedata.normalize("NFC", c[2]), "upos": c[3],
                   "head": int(c[6]) if c[6].isdigit() else 0, "rel": c[7], "sent": sent}
            sent[tok["id"]] = tok
            m = MACULA.search(c[9])
            if m:
                wid = f"{int(m.group(1))}{m.group(2)}{m.group(3)}{int(m.group(4)):02d}"
                tok["wid"] = wid
                words.setdefault(wid, []).append(tok)
    return words


def head_of(tok):
    return tok["sent"].get(tok["head"])


def tags_for(tok):
    """Tags for one treebank token (the part of the stream word it aligns with)."""
    out = []
    rel = tok["rel"].split(":")[0]
    if rel in ROLES:
        out.append(ROLES[rel])
    if tok["upos"] == "NOUN":
        # an adjective after this noun's construct chain: does it modify this noun?
        sent = tok["sent"]
        deps = [t for t in sent.values() if t["head"] == tok["id"]]
        smixut = [t for t in deps if t["rel"] == "compound:smixut"]
        if smixut:
            dep = smixut[0]
            after = [t for t in sent.values() if t["upos"] == "ADJ" and t["rel"] == "amod"
                     and t["id"] > dep["id"]]
            if any(t["head"] == tok["id"] for t in after):
                out.append("ahd")
            elif any(t["head"] == dep["id"] for t in after):
                out.append("adp")
    return out


CLAUSE = {"parataxis", "conj", "ccomp", "advcl"}


def subtree(tok):
    """Ids of tok's subtree."""
    sent, ids, todo = tok["sent"], {tok["id"]}, [tok["id"]]
    while todo:
        h = todo.pop()
        for t in sent.values():
            if t["head"] == h and t["id"] not in ids:
                ids.add(t["id"])
                todo.append(t["id"])
    return ids


def fronted_clause_start(tok):
    """True if tok is the first word of a clause (parataxis, conj …) whose verb comes later:
    a fronted constituent. The rtx cannot see where such a clause begins (1:27 בָּרָא אֹתוֹ |
    זָכָר וּנְקֵבָה בָּרָא אֹתָם), so a boundary unit goes before it."""
    sent = tok["sent"]
    for t in sent.values():
        if t["upos"] not in ("VERB", "AUX") or t["rel"] not in CLAUSE or t["id"] <= tok["id"]:
            continue
        ids = sorted(subtree(t))
        if ids[0] != tok["id"]:
            continue
        # skip the conjunction, subordinator and punctuation the clause starts with
        # and the verb's own word (prefixes: וּלְהַבְדִּיל)
        first = next((i for i in ids if i < t["id"] and sent[i]["rel"] not in ("cc", "mark", "punct")
                      and sent[i].get("wid") != t.get("wid")), t["id"])
        if first != t["id"] and sent[first]["upos"] not in ("VERB", "AUX"):
            return True
    return False


BOUNDARY = "^¦/¦<punct>$ "                 # dropped by postformat.py


def tag_unit(m, words, report=None):
    surface, analysis = m.group(1), m.group(2)
    ids = ID.findall(analysis)
    if not ids or ids[0] not in words:
        return m.group(0)
    toks = words[ids[0]]
    out = []
    for reading in analysis.split("/"):
        parts = reading.split("+")
        if len(parts) != len(toks):
            if report is not None:
                report.append(f"{ids[0]} {surface}: {len(parts)} parts, treebank {len(toks)}")
            return m.group(0)
        new = []
        for p, t in zip(parts, toks):
            add = "".join(f"<{x}>" for x in tags_for(t))
            new.append(ID.sub(lambda i: add + i.group(0), p, count=1) if ID.search(p) else p + add)
        out.append("+".join(new))
    unit = f"^{surface}/{'/'.join(out)}$"
    return (BOUNDARY if fronted_clause_start(toks[0]) else "") + unit


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    ud_dir = sys.argv[2] if len(sys.argv) > 2 else UD_DIR
    if cmd not in ("tag", "check"):
        sys.exit(__doc__)
    words = load(ud_dir) if os.path.isdir(ud_dir) else {}
    if not words:
        print(f"syntax: no treebank in {ud_dir}; stream passed unchanged", file=sys.stderr)
    report = []
    text = sys.stdin.read()
    tagged = UNIT.sub(lambda m: tag_unit(m, words, report), text)
    if cmd == "tag":
        sys.stdout.write(tagged)
    else:
        n = len(UNIT.findall(text))
        print(f"{n} units, {len(report)} not aligned")
        print("\n".join(report))


if __name__ == "__main__":
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    main()
