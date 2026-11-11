"""Wiktionary concept index -- one pass over the raw wiktextract dump of English
Wiktionary, writing WiktionaryLMDB_concepts/ for the Word Selector.

Unlike the older WiktionaryLMDB/ (whose romanizations are all empty: the old
parser read `romanization`, the dump uses `roman`), this keeps:
  - translation tables of English headwords, WITH romanizations, for the 16
    source languages + Esperanto,
  - Wikidata QIDs of senses, linked to translation-table senses,
  - for every entry in those 17 languages: senses (gloss, tags, QID, 1 example),
    IPA, romanizations, and etymology links (bor/inh/der/cog/etymon).
Entries whose senses are all inflected forms are skipped (disk is tight).
Then the passes the Word Selector also reads: etymology reverse index,
compound parts, and word_selection_cache/sinosphere.json and plurals.json.

Run directly:  venv/bin/python "Wiktionary concept index.py"   (~1 h)
               venv/bin/python "Wiktionary concept index.py" 100000   (test: first
               100000 lines into WiktionaryLMDB_concepts_test/, main pass only)
The dump is WIKTIONARY_DUMP, else this machine's copy, else streamed from
kaikki.org (word_selection/dump.py); ./setup.sh --selector runs this.
"""

import os
import re
import shutil
import sys
import time

import orjson

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from word_selection import concept_index as ci, plurals, sinosphere
from word_selection.dump import open_lines, source
from word_selection.languages import LANGS, DOSSIER_LANGS

DUMP = source("en")
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else None   # optional line limit for testing
OUT = ci.DIR + ("_test" if LIMIT else "")

ENTRY_LANGS = {l["dump"] for l in LANGS} | set(DOSSIER_LANGS)
TRANS_LANGS = {w for l in LANGS for w in l["wikt"]} | set(DOSSIER_LANGS)
LANG_RE = re.compile(rb'"lang_code": "([a-z\-]+)"')

ETYM_TYPES = {"bor", "bor+", "lbor", "ubor", "slbor", "obor", "inh", "inh+", "der", "der+",
              "cog", "noncog", "psm", "calque", "cal", "sl", "translit", "clq", "learned borrowing"}


def etym_links(templates):
    out = []
    for t in templates or []:
        name, a = t.get("name", ""), t.get("args", {})
        if name in ETYM_TYPES:
            if name in ("cog", "noncog"):
                src, term = a.get("1", ""), a.get("2", "")
            else:
                src, term = a.get("2", ""), a.get("3", "")
            if src and term and term != "-":
                out.append([name.rstrip("+"), src, term])
        elif name == "etymon":
            # new style: {"1": "fa", "2": "bor", "3": "ar>أَب>father"}
            kind = a.get("2", "")
            for k in sorted(a, key=lambda x: (len(x), x)):
                v = a[k]
                if k.isdigit() and ">" in v:
                    parts = v.split(">")
                    if len(parts) >= 2 and parts[1]:
                        out.append([kind or "etymon", parts[0], parts[1]])
    return out


def romanizations(d):
    out = []
    for f in d.get("forms", []) or []:
        if "romanization" in (f.get("tags") or []) and f.get("form"):
            out.append(f["form"])
    for s in d.get("sounds", []) or []:
        tags = s.get("tags") or []
        if "zh-pron" in s and "Mandarin" in tags and ("Pinyin" in tags or "Hanyu-Pinyin" in tags):
            out.append(s["zh-pron"])
        if "hangeul" in s:
            out.append(s["hangeul"])
        if "other" in s and d.get("lang_code") == "ja":
            out.append(s["other"])
    return list(dict.fromkeys(out))


def ipas(d):
    out = []
    for s in d.get("sounds", []) or []:
        if "ipa" in s:
            out.append([s["ipa"], " ".join(s.get("tags") or [])])
    return out[:4]


def senses_of(d):
    out = []
    for s in d.get("senses", []) or []:
        if s.get("form_of") or "form-of" in (s.get("tags") or []):
            continue
        g = s.get("glosses") or []
        if not g:
            continue
        ex = []
        for e in (s.get("examples") or [])[:1]:
            ex.append([e.get("text", "")[:300], (e.get("english") or e.get("translation") or "")[:300]])
        out.append({"g": g, "raw": s.get("raw_glosses") or [], "tags": s.get("tags") or [],
                    "qid": s.get("wikidata") or [], "ex": ex})
    return out


def merge_put(txn, db, k, items):
    old = txn.get(k, db=db)
    val = (ci.unpack(old) if old else []) + items
    txn.put(k, ci.pack(val), db=db)


print(f"Reading {DUMP}", flush=True)
BUILDING = OUT + ".building"     # renamed to OUT when complete: a half-built index is never used
if os.path.exists(BUILDING):
    shutil.rmtree(BUILDING)
os.makedirs(BUILDING)
idx = ci.ConceptIndex(BUILDING, readonly=False)
dbs = idx.dbs

t0 = time.time()
n_lines = n_entries = n_trans = pending = 0
txn = idx.env.begin(write=True)
with open_lines(DUMP, binary=True) as f:
    for line in f:
        n_lines += 1
        if LIMIT and n_lines > LIMIT:
            break
        m = LANG_RE.search(line)
        if not m or m.group(1).decode() not in ENTRY_LANGS:
            continue
        d = orjson.loads(line)
        lang, word, pos = d.get("lang_code"), d.get("word"), d.get("pos", "")
        if not word or lang not in ENTRY_LANGS:
            continue
        senses = senses_of(d)
        if senses:
            entry = {"pos": pos, "senses": senses, "ipa": ipas(d), "roman": romanizations(d),
                     "etym": etym_links(d.get("etymology_templates"))}
            merge_put(txn, dbs["entries"], ci.key(lang, word), [entry])
            n_entries += 1
            for s in senses:
                for q in s["qid"]:
                    merge_put(txn, dbs["qid"], q.encode(), [[lang, word, pos, s["g"][-1], "g"]])

        if lang == "en" and d.get("translations"):
            table, qtable = {}, {}
            for t in d["translations"]:
                code = t.get("code") or t.get("lang_code")
                if code not in TRANS_LANGS or not t.get("word"):
                    continue
                sense = t.get("sense") or ""
                rom = t.get("roman") or t.get("romanization") or ""
                table.setdefault(sense, {}).setdefault(code, []).append(
                    [t["word"], rom, "\t".join(t.get("tags") or [])])
            if table:
                k = ci.key(word, pos)
                old = txn.get(k, db=dbs["translations"])
                merged = ci.unpack(old) if old else {}
                for sense, langs in table.items():
                    for code, ws in langs.items():
                        merged.setdefault(sense, {}).setdefault(code, []).extend(ws)
                    i = ci.match_sense(sense, senses) if sense else (0 if len(senses) == 1 else None)
                    if i is not None and senses[i]["qid"]:
                        qtable[sense] = senses[i]["qid"]
                        for q in senses[i]["qid"]:
                            merge_put(txn, dbs["qid"], q.encode(), [["en", word, pos, sense, "t"]])
                txn.put(k, ci.pack(merged), db=dbs["translations"])
                if qtable:
                    oldq = txn.get(k, db=dbs["trans_qid"])
                    mq = ci.unpack(oldq) if oldq else {}
                    mq.update(qtable)
                    txn.put(k, ci.pack(mq), db=dbs["trans_qid"])
                n_trans += 1

        pending += 1
        if pending >= 50000:
            pending = 0
            txn.commit()
            txn = idx.env.begin(write=True)
            print(f"{n_lines:>10} lines  {n_entries:>9} entries  {n_trans:>8} tables  "
                  f"{time.time() - t0:7.0f}s", flush=True)
txn.commit()
idx.close()
print(f"main pass: {n_lines} lines, {n_entries} entries, {n_trans} translation tables, "
      f"{time.time() - t0:.0f}s", flush=True)
print(f"reverse index: {ci.build_reverse(BUILDING)} words", flush=True)
print(f"etymology reverse index: {ci.build_etym_reverse(BUILDING)} etymons", flush=True)
if not LIMIT:
    print(f"compound parts: {ci.build_parts(DUMP, BUILDING)} words", flush=True)
if os.path.exists(OUT):
    shutil.rmtree(OUT)
os.replace(BUILDING, OUT)
print(f"done -> {OUT}  ({time.time() - t0:.0f}s)", flush=True)
if not LIMIT:
    print(f"sinosphere table: {sinosphere.build(DUMP)}", flush=True)
    print(f"plurals table: {plurals.build(DUMP)} forms", flush=True)
