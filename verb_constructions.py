"""Verb constructions -> Globasa: proposals from the Wiktionary senses, decisions in one list.

verb_constructions.tsv is the source of truth (one row per source-language sense that
governs a preposition or is reflexive). Each row carries a proposal, worked out here from
the sense's English gloss and the word list, and the decision columns:

    sense_status  stage 1 (user, 2026-11-20: "first vet senses from Wiktionary"): is the
                  Wiktionary sense and its preposition right? "" undecided, "ok", "no"
    kind      how Globasa renders the construction (KINDS below)
    glb       the Globasa verb (or "ganjon <adj>" for a feeling state)
    glb_prep  the Globasa preposition for the governed one ("" = none: the object is direct)
    status    stage 2, by a fluent speaker of the source language: "" undecided, "ok", "no"
    reviewer  who set status (the speaker vetting that language)
    note      free text

Rebuilding keeps every decision: rows already in the list keep kind/glb/glb_prep/status/note,
only the "proposed" column is refreshed; new senses arrive undecided with the proposal
copied into the decision columns. Rows whose sense left Wiktionary stay, marked in "proposed".
verb_constructions_to_apertium.py reads only rows with sense_status ok AND status ok.
Spanish keeps only senses with a governed preposition (user, 2026-11-20): Spanish reflexives
are left to the rules taken from the Spanish-language Xwexi.

Globasa side (Xwexi 03.gramati/02 Verb categories, 03 Function words; Doxo usage):
    obj      the preposition disappears, the Globasa verb is transitive (warten auf -> intizar X)
    prep     a Globasa preposition (denken an -> fikir tem X)
    se       true reflexive, V se (sich waschen -> woxa se; Doxo sangu se, imanugi se)
    soho     reciprocal, V soho (sich lieben "love one another" -> lubi soho)
    cu       intransitive -cu: non-agentive, posture, get/become (sich öffnen -> bukacu,
             sich setzen -> sidecu, zich belgen -> gadibucu)
    xor      xor- inchoative of a feeling (sich verlieben -> xorlubi)
    state    feeling from an adjective root: ganjon + adj (user 2026-11-20: Mi ganjon gadibu tem X)
    lexical  the reflexive is lexical; plain Globasa verb, sich dropped (sich baden -> banyo)

Run:    python verb_constructions.py
Reads:  constructions_cache/wiktionary_constructions.tsv (wiktionary_constructions.py),
        word-list.csv (Word, TranslationEng), menalariExtension.tsv (vetted Wiktionary)
Writes: verb_constructions.tsv
"""
import csv
import os
import re
from collections import defaultdict

import wiktionary_constructions

LIST_TSV = "verb_constructions.tsv"
KEY = ["lang", "verb", "reflexive", "prep", "case", "gloss"]
DECISION = ["kind", "glb", "glb_prep", "status", "reviewer", "note"]
COLUMNS = KEY + ["sense", "sense_status"] + DECISION + ["proposed"]
KINDS = ("obj", "prep", "se", "soho", "cu", "xor", "state", "lexical")
EXT_COLUMN = {"de": "German", "nl": "Dutch", "fr": "French", "es": "Spanish"}

# English preposition of the gloss -> Globasa (Xwexi 03); "obj" = drop it when the Globasa
# verb is transitive (wait for, look at, count on, look forward to).
EN_PREP = {"about": "tem", "of": "tem", "on": "obj", "for": "obj", "at": "obj", "to": "tas",
           "with": "ton", "from": "of", "against": "anti", "after": "tem", "in": "tem",
           "into": "cel in", "over": "tem", "towards": "hoy", "toward": "hoy"}
POSTURE = {"sit", "lie", "stand", "move", "turn", "bend", "lean", "kneel", "settle", "approach",
           "withdraw", "retire", "hurry", "hasten", "stir", "budge"}
ANTICAUSATIVE = {"open", "close", "change", "increase", "decrease", "improve", "worsen", "spread",
                 "develop", "divide", "split", "break", "dissolve", "fill", "empty", "extend",
                 "unfold", "repeat", "happen", "occur", "end", "finish", "begin", "start", "form",
                 "vary", "clear", "calm"}


def word_list_index():
    """English gloss item -> Globasa words, by PoS section: ("vt"|"vi"|"adj", item)."""
    idx = defaultdict(set)
    sections = {}
    with open("word-list.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            w, e = r["Word"], r["TranslationEng"]
            if " " in w:
                continue
            for part in e.split(";"):
                m = re.match(r"\s*(adj|v\.intr[^:]*|v\.tr|v\.cop)\s*:\s*(.*)", part.strip())
                if not m:
                    continue
                pos = "adj" if m[1] == "adj" else "vi" if m[1].startswith(("v.intr", "v.cop")) else "vt"
                sections.setdefault(w, set()).add(pos)
                text = re.sub(r"\(_[^)]*_\)", "", m[2])
                for item in re.split(r",\s*(?![^()]*\))", text):
                    full = re.sub(r"[()]", "", item).strip().lower()
                    bare = re.sub(r"\s*\([^)]*\)", "", item).strip().lower()   # "wait (for)" -> "wait"
                    for k in {full, bare}:
                        if k:
                            idx[(pos, k)].add(w)
    return idx, sections


def extension_index():
    """(lang, source word) -> Globasa words whose vetted Wiktionary sense lists it."""
    idx = defaultdict(set)
    if not os.path.exists("menalariExtension.tsv"):
        return idx
    with open("menalariExtension.tsv", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            for lang, col in EXT_COLUMN.items():
                for item in re.split(r"[;,]\s*", r.get(col) or ""):
                    item = re.sub(r"\s*<[^>]*>", "", item).strip()
                    if item:
                        idx[(lang, item)].add(r["Globasa"])
    return idx


def parse_gloss(gloss):
    """(head phrase, English preposition, adjective) of "to wait (for)", "to be annoyed",
    "to look forward to", "to get used to"."""
    g = gloss.lower().split(";")[0].split(",")[0].strip()
    g = re.sub(r"^to\s+", "", g)
    m = re.match(r"(be|feel|get|become|grow)\s+(?:very\s+)?([a-z\-]+)(?:\s+(\w+))?", g)
    if m:
        return m[1], (m[3] if m[3] in EN_PREP else ""), m[2]
    words = re.sub(r"[()]", " ", g).split()
    if not words:
        return "", "", ""
    head = words[0]
    prep = next((w for w in words[1:4] if w in EN_PREP), "")
    return head, prep, ""


def propose(row, idx, sections, ext):
    """(kind, glb, glb_prep, evidence) for one construction sense."""
    lang, verb, gloss = row["lang"], row["verb"], row["gloss"]
    refl = row["reflexive"] == "1"
    g = gloss.lower()
    head, en_prep, adj = parse_gloss(gloss)
    vetted = sorted(ext.get((lang, verb), set()) | ext.get((lang, "sich " + verb), set()))
    ev = []

    def verbs(item, pos=("vt", "vi")):
        return sorted(set().union(*(idx.get((p, item), set()) for p in pos)))

    kind, glb = "", ""
    if refl and re.search(r"\b(each other|one another)\b", g):
        kind, cands = "soho", verbs(head)
    elif adj and head in ("be", "feel"):
        adjs = sorted(idx.get(("adj", adj), ()))
        feel = verbs(f"be feel {adj}", ("vi",)) or verbs(f"be {adj}", ("vi",))
        if adjs:
            kind, cands = "state", [f"ganjon {a}" for a in adjs]
        else:
            kind, cands = "lexical", feel
    elif adj and head in ("get", "become", "grow"):
        cands = verbs(f"get {adj}", ("vi",)) or verbs(f"become {adj}", ("vi",))
        if not cands:
            cands = [a + "cu" for a in sorted(idx.get(("adj", adj), ()))]
            if cands:
                ev.append("(derived -cu, not in the word list)")
        kind = "cu"
    elif "fall in love" in g:
        kind, cands = "xor", ["xorlubi"]
    elif refl and (head in POSTURE or head in ANTICAUSATIVE):
        cu = [w for w in verbs(head, ("vi",)) if w.endswith("cu")]
        kind, cands = "cu", cu or [w + "cu" for w in verbs(head, ("vt",))]
    elif refl and re.search(r"\b(oneself|himself|herself|itself|themselves)\b", g):
        kind, cands = "se", verbs(head, ("vt",))
    else:
        kind, cands = ("lexical" if refl else "obj"), verbs(head)
    both = [c for c in cands if c in vetted]
    if both:
        glb = both[0]
        ev.append("word list + vetted Wiktionary")
    elif cands:
        glb = cands[0]
        ev.append("English gloss -> word list" + (f" ({len(cands)} candidates)" if len(cands) > 1 else ""))
    elif vetted:
        glb = vetted[0]
        ev.append("vetted Wiktionary only")
    else:
        ev.append("(no Globasa verb found)")
    glb_prep = ""
    if row["prep"]:
        p = EN_PREP.get(en_prep, "")
        root = glb.split()[-1] if glb else ""
        if p == "obj":
            if "vt" in sections.get(root, ()):
                glb_prep, kind = "", ("obj" if kind in ("obj", "lexical") else kind)
            else:
                glb_prep = {"for": "tas", "at": "fe", "on": "per"}.get(en_prep, "")
                ev.append("(intransitive Globasa verb: preposition kept)")
        elif p:
            glb_prep = p
            if kind == "obj":
                kind = "prep"
        elif "vt" in sections.get(root, ()) and kind in ("obj", "lexical", "prep"):
            # no English preposition ("to wait", "to look"): a transitive Globasa verb takes
            # the governed object directly
            glb_prep, kind = "", "obj"
            ev.append(f"(no English preposition for {row['prep']}: transitive Globasa verb)")
        else:
            ev.append(f"(no English preposition in the gloss for {row['prep']})")
            if kind == "obj":
                kind = "prep"
    return kind, glb, glb_prep, "; ".join(ev)


def untouched(r):
    """Are the row's decision columns still its previous proposal ("kind | glb | prep | ...")?"""
    parts = [p.strip() for p in r.get("proposed", "").split("|")]
    if len(parts) < 3:
        return False
    return (r.get("kind", ""), r.get("glb", ""), r.get("glb_prep", "") or "-") == (parts[0], parts[1], parts[2])


def load_list():
    if not os.path.exists(LIST_TSV):
        return []
    with open(LIST_TSV, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        return [dict(zip(header, line.rstrip("\n").split("\t"))) for line in f if line.strip()]


def build():
    idx, sections = word_list_index()
    ext = extension_index()
    old = {tuple(r.get(k, "") for k in KEY): r for r in load_list()}
    out, seen = [], set()
    for row in wiktionary_constructions.rows():
        if row["lang"] == "es" and not row["prep"]:
            continue                    # Spanish: governed prepositions only
        key = tuple(row.get(k, "") for k in KEY)
        if key in seen:
            continue
        seen.add(key)
        kind, glb, glb_prep, ev = propose(row, idx, sections, ext)
        proposed = f"{kind} | {glb} | {glb_prep or '-'} | {ev}"
        r = old.get(key)
        if r is None or (not r.get("status") and not r.get("sense_status") and not r.get("note")
                         and untouched(r)):
            # new, or undecided and unedited (decision columns still equal the old proposal)
            r = dict(zip(KEY, key), sense=row["sense"], sense_status="", kind=kind, glb=glb,
                     glb_prep=glb_prep, status="", reviewer="", note="")
        r["proposed"] = proposed
        out.append(r)
    for key, r in old.items():          # decisions whose sense left Wiktionary are kept
        if key not in seen:
            r["proposed"] = "(not in the current Wiktionary dump)"
            out.append(r)
    out.sort(key=lambda r: (r["lang"], r["verb"], r["reflexive"], r["prep"], r["gloss"]))
    tmp = LIST_TSV + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:     # plain joins: glosses contain quotes
        f.write("\t".join(COLUMNS) + "\n")
        for r in out:
            f.write("\t".join(str(r.get(c, "")).replace("\t", " ") for c in COLUMNS) + "\n")
    os.replace(tmp, LIST_TSV)
    senses = sum(1 for r in out if r.get("sense_status"))
    decided = sum(1 for r in out if r.get("status"))
    print(f"{len(out)} rows in {LIST_TSV}: {senses} senses vetted (stage 1), "
          f"{decided} proposals decided (stage 2)")


build()
