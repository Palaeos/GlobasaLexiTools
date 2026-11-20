# Script tier: propose Globasa words for archaic / obsolete / dated English senses, built on the
# vetted English senses (vetted_senses.tsv + sense_vetter's sense_vetting.jsonl, via
# vetted_senses.load_rows). Proposes, decides nothing: every row is for vetting.
#
#   venv/bin/python archaic_senses.py      (ranks by 1800-1890s frequency from HISTWORDS_DIR,
#                                          default Warehouse2/Language/Claude/histwords/eng-all, if present)
#
# A vetted sense = (Globasa word, English word, PoS, Wiktionary translation-table label), App? s,
# vetted by a person (Tier v/e). Two bridges carry it to the period senses of other English words:
#
#   table   the period sense has its own translation table (matched to the sense as sense_rows
#           does, tiers 1-2 only: the table label must occur in the definition; the overlap tier
#           gave obsolete 'morning' the main 166-language table): its translations are compared language by language with the tables of the
#           vetted senses of the same PoS; a Globasa word needs >= TABLE_MIN_LANGS shared
#           languages and TABLE_LEAD x the runner-up. Only ~6% of period senses have a table.
#   gloss   period senses are mostly defined by their modern equivalents ("(obsolete) To curb;
#           restrain"): each head item of the definition (one word, or "to X" for verbs) that has
#           vetted senses of the same PoS votes for their Globasa words. 'unique' = every head
#           that has vetted senses points to one and the same Globasa word; 'choice' = several.
#
# Vetoes: a Globasa word vetted n on this very sense is never proposed; a period sense whose own
# table is already vetted s is reported as 'done'.
#
# Output: archaic_senses.tsv (one row per period sense with a proposal), archaic_senses_report.txt
import os
import pickle
import re
from collections import Counter, defaultdict

import vetted_senses
from sense_rows import match_sense_strict
from wiktionary_db import WiktionaryDB, decode_key, deserialize_senses

HERE = os.path.dirname(os.path.abspath(__file__))
PERIOD_TAGS = ("archaic", "obsolete", "dated", "historical", "poetic", "literary")
PERIOD_LABEL = re.compile(r"\((?:[^)]*?\b)?(archaic|obsolete|dated|now rare|poetic|literary|historical)\b", re.I)
POS = ("noun", "verb", "adj", "adv")
TABLE_MIN_LANGS = 4
TABLE_LEAD = 2.0
STOP = set("a an the of or and in for to is are was were be been by with at on from as it its that this "
           "which who one something someone some any very".split())

db = WiktionaryDB(os.path.join(HERE, "WiktionaryLMDB"))


def norm(t):
    return re.sub(r"\s+", " ", t.strip().lower())


# --- vetted senses ------------------------------------------------------------------------------
yes = defaultdict(set)          # (eng, pos) -> {glb}
yes_label = {}                  # (eng, pos, label) -> {glb}
no_label = defaultdict(set)     # (eng, pos, label) -> {glb} vetted n
for r in vetted_senses.load_rows():
    if r["Source"] != "en" or r["Prt of Sp"] not in POS or not r["Glb"]:
        continue
    key = (r["Eng"], r["Prt of Sp"], r["Wiktionary Sense"])
    if r["App?"] == "s" and r["Tier"] in ("v", "e"):
        yes[key[:2]].add(r["Glb"])
        yes_label.setdefault(key, set()).add(r["Glb"])
    elif r["App?"] == "n":
        no_label[key].add(r["Glb"])

# fingerprint index: (pos, lang, translation) -> {(glb, eng)}; the period word's own vetted senses
# are left out when it is scored (hour 'the time' shared satu's table languages by polysemy)
finger = defaultdict(set)
for (eng, pos, label), glbs in yes_label.items():
    table = (db.get_translations(eng, pos) or {}).get(label, {})
    for lang, ts in table.items():
        for t in ts:
            for g in glbs:
                finger[(pos, lang, norm(t.word))].add((g, eng))


def table_bridge(word, pos, table):
    langs = defaultdict(set)                                    # glb -> {lang}
    for lang, ts in table.items():
        for t in ts:
            for g, eng in finger.get((pos, lang, norm(t.word)), ()):
                if eng != word:
                    langs[g].add(lang)
    ranked = sorted(langs.items(), key=lambda x: -len(x[1]))
    if not ranked or len(ranked[0][1]) < TABLE_MIN_LANGS:
        return None
    runner = len(ranked[1][1]) if len(ranked) > 1 else 0
    if len(ranked[0][1]) < TABLE_LEAD * runner:
        return None
    return ranked[0][0], len(ranked[0][1])


def heads(gloss, pos):
    # definition head items: parentheticals and quotes out; whole ; , segments that are one word
    # (after 'to' for verbs, an article for nouns), or "X or Y" with single words on both sides
    g = re.sub(r"\([^)]*\)|\"[^\"]*\"|“[^”]*”", " ", gloss)
    g = re.split(r"[.:]\s", g + " ")[0]
    out = []
    for part in re.split(r"[;,]", g):
        p = norm(part).strip(" .")
        # serial lists "festive, bright, or colourful" / "to X, or to Y": last item starts "or"
        p = re.sub(r"^(?:or|and)\s+", "", p)
        if pos == "verb":
            if not p.startswith("to "):
                continue
            p = p[3:]
        else:
            p = re.sub(r"^(a|an|the)\s+", "", p)
        alts = [a.strip() for a in p.split(" or ")]
        if all(a and len(a.split()) == 1 and a not in STOP for a in alts):
            out += alts
    return out


def n_senses(word, pos):
    return len(db.get_senses(word, pos) or [])


def gloss_bridge(word, pos, gloss):
    votes = Counter()
    via = defaultdict(list)
    used = []
    for h in heads(gloss, pos):
        if h == word or (h, pos) not in yes:
            continue
        used.append(h)
        for g in yes[(h, pos)]:
            votes[g] += 1
            via[g].append(h)
    if not votes:
        return None
    glbs = sorted(votes, key=lambda g: (-votes[g], g))
    top = glbs[0]
    backed = len(via[top]) >= 2 or (len(via[top]) == 1 and n_senses(via[top][0], pos) == 1)
    unique = backed and (len(glbs) == 1 or votes[top] > votes[glbs[1]])
    return ("unique" if unique else "choice"), [(g, via[g]) for g in glbs[:5]]


# --- optional 19th-century frequency ------------------------------------------------------------
freq = Counter()
hw_dir = os.environ.get("HISTWORDS_DIR", "/media/paleos/Warehouse2/Language/Claude/histwords/eng-all")
if hw_dir:
    for d in range(1800, 1900, 10):
        p = os.path.join(hw_dir, f"{d}-counts.pkl")
        if os.path.exists(p):
            with open(p, "rb") as f:
                freq.update(pickle.load(f, encoding="latin1"))

# --- scan ---------------------------------------------------------------------------------------
rows = []
stats = Counter()
with db.env.begin(db=db.db_senses) as txn:
    for k, v in txn.cursor():
        word, pos = decode_key(bytes(k))
        if pos not in POS or not re.fullmatch(r"[a-z][a-z' -]*", word):
            continue
        senses = deserialize_senses(bytes(v))
        period = []
        for s in senses:
            raw = " ".join(s.raw_glosses)
            m = PERIOD_LABEL.search(raw)
            tag = next((t for t in PERIOD_TAGS if t in s.tags), None) or (m.group(1).lower() if m else None)
            if tag:
                period.append((s, tag))
        if not period:
            continue
        tables = db.get_translations(word, pos) or {}
        table_of = {}
        for label, table in tables.items():
            s = match_sense_strict(label, senses)
            if s is not None:
                table_of.setdefault(id(s), (label, table))
        for s, tag in period:
            stats["period senses"] += 1
            gloss = s.glosses[-1] if s.glosses else ""
            label, table = table_of.get(id(s), ("", {}))
            vetoed = no_label.get((word, pos, label), set())
            done = yes_label.get((word, pos, label))
            row = {"eng": word, "pos": pos, "period": tag, "gloss": gloss, "label": label,
                   "freq_1800s": freq.get(word, 0), "done": "/".join(sorted(done)) if done else ""}
            if done:
                stats["already vetted (own table)"] += 1
            tb = table_bridge(word, pos, table) if table else None
            if tb and tb[0] in vetoed:
                tb = None
            gb = gloss_bridge(word, pos, gloss)
            if gb:
                gb = (gb[0], [(g, h) for g, h in gb[1] if g not in vetoed])
                gb = gb if gb[1] else None
            if not tb and not gb:
                continue
            row["table"] = f"{tb[0]} ({tb[1]} langs)" if tb else ""
            row["gloss_kind"] = gb[0] if gb else ""
            row["gloss_glb"] = "; ".join(f"{g} ({'/'.join(h)})" for g, h in gb[1]) if gb else ""
            agree = tb and gb and tb[0] in [g for g, _ in gb[1]]
            if agree:
                row["strength"] = "A table+gloss"
            elif tb:
                row["strength"] = "B table"
            elif gb[0] == "unique":
                row["strength"] = "C gloss unique"
            else:
                row["strength"] = "D gloss choice"
            stats[row["strength"]] += 1
            rows.append(row)

rows.sort(key=lambda r: (r["strength"], -r["freq_1800s"], r["eng"]))
cols = ["strength", "eng", "pos", "period", "freq_1800s", "gloss", "table", "gloss_kind", "gloss_glb", "label", "done"]
with open(os.path.join(HERE, "archaic_senses.tsv"), "w", encoding="utf-8") as f:
    f.write("\t".join(cols) + "\n")
    for r in rows:
        f.write("\t".join(str(r.get(c, "")).replace("\t", " ") for c in cols) + "\n")

rep = [f"{k}: {v}" for k, v in sorted(stats.items())]
rep.append(f"vetted senses used: {sum(len(g) for g in yes_label.values())} (s, Tier v/e); n-vetoes: {len(no_label)}")
by_tag = Counter((r["period"], r["strength"][0]) for r in rows)
rep.append("by period tag (A/B/C/D): " + "; ".join(
    f"{t} " + "/".join(str(by_tag[(t, s)]) for s in "ABCD") for t in sorted({t for t, _ in by_tag})))
rep.append("\n== top 1800s-frequent proposals per strength")
for s in ("A", "B", "C", "D"):
    top = sorted([r for r in rows if r["strength"][0] == s], key=lambda r: -r["freq_1800s"])[:25]
    rep.append(f"-- {s}")
    for r in top:
        rep.append(f"   {r['eng']} ({r['pos']}, {r['period']}) “{r['gloss'][:70]}” -> "
                   f"{r['table'] or ''}{' | ' if r['table'] and r['gloss_glb'] else ''}{r['gloss_glb']}")
open(os.path.join(HERE, "archaic_senses_report.txt"), "w", encoding="utf-8").write("\n".join(rep) + "\n")
print("\n".join(rep))
