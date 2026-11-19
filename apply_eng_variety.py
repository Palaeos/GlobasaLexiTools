"""British / American views of the English glosses in word-list.csv.

Pipeline: CDN download -> extract_constructions.py -> apply_eng_variety.py
-> AnkiMaker3.py (ENG_VARIETY=GB|US). Re-run this whenever TranslationEng
changes (e.g. after extract_constructions.py), since the variety columns are
derived from it.

`word-list.csv` is re-downloaded from the CDN, and its English glosses list
both varieties side by side ("blue color, blue colour, color blue, colour
blue"; "lift, elevator"). Run this after each download, after
extract_constructions.py: it (re)writes two derived columns,

    TranslationEngGB   the gloss as a British learner should see it
    TranslationEngUS   the gloss as an American learner should see it

in the same format as TranslationEng (PoS prefixes, "; " segments, ", "
items), so AnkiMaker3 (ENG_VARIETY=GB|US) and other readers need no new
parsing. TranslationEng itself is never changed.

Sources, in order:
  1. VarCon (en-wl/wordlist, permissive licence; cached in
     eng_variety_cache/varcon.txt): spelling. A token's variety is where
     VarCon marks it as the *preferred* spelling (A = American, B = British,
     Z = British -ize/Oxford). Recomputed every run, so new glosses in an
     updated word list are handled without patch rows.
  2. eng_variety_patch.tsv (the source of truth for what VarCon cannot
     know; edit by hand). Columns: Word, item, variety, group, note.
       variety GB|US + group  a vocabulary pair: items of the same Word with
                              the same group are counterparts (lift GB /
                              elevator US, group "elevator")
       variety both           never drop this item (overrides VarCon)
     Rows are keyed by Word + item text, so they survive updates; a row whose
     item is no longer in that word's gloss is reported STALE and skipped.

Slash pairs inside an item ("light (of color/colour)") are resolved to
the view's spelling when both words share a VarCon line.

Safety rule: an item is dropped from a view only when a counterpart for that
view is in the same "; " segment. check (verify) is never touched; check is
dropped from the GB view only where "cheque" stands next to it. A segment is
never emptied. Items that exist in one variety only (cookie with no biscuit)
are kept and listed in eng_variety_report.tsv as suggestions.

Idempotent: a run that would change nothing writes nothing. The file as
downloaded (before the variety columns were first added) is kept as
word-list.csv.pre-variety.
"""
import csv
import re
import shutil
import urllib.request
from collections import defaultdict
from pathlib import Path

import constructions

WORDLIST = "word-list.csv"
BACKUP = "word-list.csv.pre-variety"
PATCH = Path("eng_variety_patch.tsv")
REPORT = Path("eng_variety_report.tsv")
VARCON = Path("eng_variety_cache/varcon.txt")
VARCON_URL = "https://raw.githubusercontent.com/en-wl/wordlist/master/varcon/varcon.txt"
SRC, VIEWS = "TranslationEng", {"GB": "TranslationEngGB", "US": "TranslationEngUS"}
PREFERRED = {"GB": {"B"}, "US": {"A"}}


# ---- word-list round trip (same facts as extract_constructions.py: CRLF,
# no terminator on the final line, newlines inside quoted fields)
def read_wordlist(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    with open(path, "rb") as f:
        head = f.read(65536)
        f.seek(-1, 2)
        tail = f.read()
    return rows, ("\r\n" if b"\r\n" in head else "\n"), tail.endswith(b"\n")


def write_wordlist(path, rows, terminator, final_newline):
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f, lineterminator=terminator).writerows(rows)
    if not final_newline:
        with open(path, "rb+") as f:
            f.seek(-len(terminator), 2)
            f.truncate()


# ---- VarCon: token -> [(line id, preferred regions)]
def load_varcon():
    if not VARCON.exists():
        VARCON.parent.mkdir(exist_ok=True)
        VARCON.write_bytes(urllib.request.urlopen(VARCON_URL, timeout=120).read())
    index = defaultdict(list)
    for n, line in enumerate(VARCON.read_text(encoding="utf-8", errors="replace").splitlines()):
        if not line or line.startswith("#"):
            continue
        body = line.split("|")[0]
        for part in body.split("/"):
            if ":" not in part:
                continue
            tags, word = part.split(":", 1)
            word = word.strip().lower()
            # "A", "B", "Z" without a suffix = preferred in that region
            pref = {t for t in tags.split() if t in ("A", "B", "Z", "C", "D")}
            index[word].append((n, pref))
    return index


varcon = load_varcon()
TOK = re.compile(r"[A-Za-z]+(?:'[a-z]+)?")


def item_tokens(item):
    """[(token, {VarCon line: preferred regions})] for one gloss item."""
    out = []
    for t in TOK.findall(constructions.normalise_item(item)):
        out.append((t.lower(), {n: p for n, p in varcon.get(t.lower(), [])}))
    return out


def counterpart_regions(a, b):
    """If items a and b are spelling variants of each other (same length; at
    each position the same word, or two words on one shared VarCon line),
    return the regions where a's differing words are preferred on those shared
    lines; else None. Regions are read per shared line, never pooled across a
    word's other lines (check is A-only on the check/cheque bank line even
    though "check" is also a verb)."""
    if len(a) != len(b) or a == b:
        return None
    regions = None
    for (ta, la), (tb, lb) in zip(a, b):
        if ta == tb:
            continue
        shared = set(la) & set(lb)
        if not shared:
            return None
        r = set().union(*(la[n] for n in shared))
        regions = r if regions is None else regions & r
    return regions


# ---- patch
patch = defaultdict(dict)   # Word -> {normalised item: row}
if PATCH.exists():
    with open(PATCH, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r.get("Word", "").strip() and r.get("item", "").strip():
                patch[r["Word"].strip()][constructions.normalise_item(r["item"])] = r


def views_of(word, text, report, used):
    """{'GB': text, 'US': text}: the original text where a view drops nothing,
    otherwise the segments rebuilt as '<prefix>item, item' joined by '; '."""
    segs, dropped_any = {v: [] for v in VIEWS}, {v: False for v in VIEWS}
    for seg in text.split(";"):
        prefix, body = constructions.split_annotation(seg)
        items = constructions.split_items(body) if body.strip() else []
        norms = [constructions.normalise_item(it) for it in items]
        toks = [item_tokens(it) for it in items]
        prow = [patch.get(word, {}).get(n) for n in norms]
        for n, p in zip(norms, prow):
            if p:
                used.add((word, n))
        # counterparts[i] = [(j, regions of i, regions of j)]
        counterparts = defaultdict(list)
        for i in range(len(items)):
            for j in range(len(items)):
                if i == j:
                    continue
                pi, pj = prow[i], prow[j]
                if (pi and pi.get("variety") == "both") or (pj and pj.get("variety") == "both"):
                    continue
                if pi and pj and pi.get("variety") in VIEWS and pj.get("variety") in VIEWS:
                    if (pi.get("group") or norms[i]) == (pj.get("group") or norms[j]) and pi["variety"] != pj["variety"]:
                        counterparts[i].append((j, {pi["variety"]}, {pj["variety"]}))
                    continue
                ri, rj = counterpart_regions(toks[i], toks[j]), counterpart_regions(toks[j], toks[i])
                if ri is None or rj is None:
                    continue
                vi = {v for v, pref in PREFERRED.items() if ri & pref}
                vj = {v for v, pref in PREFERRED.items() if rj & pref}
                if vi != vj:
                    counterparts[i].append((j, vi, vj))
        for v in VIEWS:
            kept = []
            for i, it in enumerate(items):
                # slash pairs inside an item, e.g. "light (of color/colour)":
                # keep the view's spelling when both share a VarCon line
                def pick(m, v=v):
                    a, b = m.group(1), m.group(2)
                    la = {n: p for n, p in varcon.get(a.lower(), [])}
                    lb = {n: p for n, p in varcon.get(b.lower(), [])}
                    shared = set(la) & set(lb)
                    if not shared:
                        return m.group(0)
                    ra = set().union(*(la[n] for n in shared)) & PREFERRED[v]
                    rb = set().union(*(lb[n] for n in shared)) & PREFERRED[v]
                    return a if ra and not rb else b if rb and not ra else m.group(0)
                new_it = re.sub(r"(?<![A-Za-z])([A-Za-z]+)/([A-Za-z]+)(?![A-Za-z])", pick, it)
                if new_it != it:
                    report.append((word, it, v, f"slash pair resolved: {new_it}"))
                    dropped_any[v] = True
                    it = new_it
                better = [items[j] for j, vi, vj in counterparts[i] if v in vj and v not in vi]
                if better:
                    report.append((word, it, v, "dropped: counterpart " + " / ".join(better)))
                    dropped_any[v] = True
                    continue
                kept.append(it)
            segs[v].append(prefix + ", ".join(kept or items))   # never empty a segment
        for i, it in enumerate(items):
            if counterparts[i]:
                continue
            p = prow[i]
            if p and p.get("variety") in VIEWS:
                report.append((word, it, p["variety"], "suggestion: no counterpart for the other variety"))
                continue
            regions = None
            for t, lines in toks[i]:
                if lines:
                    r = set().union(*lines.values())
                    regions = r if regions is None else regions & r
            if regions is not None:
                vs = {v for v, pref in PREFERRED.items() if regions & pref}
                if len(vs) == 1:
                    report.append((word, it, next(iter(vs)), "suggestion: no counterpart for the other variety"))
    return {v: ("; ".join(segs[v]) if dropped_any[v] else text) for v in VIEWS}


rows, terminator, final_newline = read_wordlist(WORDLIST)
header = rows[0]
word_col, src_col = header.index("Word"), header.index(SRC)
cols = {}
for v, name in VIEWS.items():
    if name not in header:
        header.append(name)
    cols[v] = header.index(name)

report, used, changed = [], set(), 0
for row in rows[1:]:
    if len(row) <= src_col:
        continue
    while len(row) < len(header):
        row.append("")
    word, text = row[word_col].strip(), row[src_col]
    views = views_of(word, text, report, used) if text.strip() else {v: "" for v in VIEWS}
    for v in VIEWS:
        new = views[v]
        if row[cols[v]] != new:
            row[cols[v]] = new
            changed += 1

stale = [(w, r["item"]) for w, items in patch.items() for n, r in items.items() if (w, n) not in used]
with open(REPORT, "w", encoding="utf-8") as f:
    f.write("Word\titem\tvariety\tnote\n")
    for w, it, v, note in sorted(report):
        f.write(f"{w}\t{it}\t{v}\t{note}\n")
    for w, it in stale:
        f.write(f"{w}\t{it}\t\tSTALE patch row: item not in the current gloss\n")

differs = sum(1 for r in rows[1:] if len(r) > max(cols.values()) and r[cols['GB']] != r[cols['US']])
dropped = sum(1 for x in report if x[3].startswith("dropped"))
sugg = sum(1 for x in report if x[3].startswith("suggestion"))
print(f"{len(rows) - 1} entries; GB and US views differ in {differs}; {dropped} items dropped from a view; "
      f"{sugg} single-variety suggestions; {len(stale)} stale patch rows (see {REPORT})")
if changed:
    # back up the file as downloaded (no variety columns yet); later re-runs
    # only refresh derived columns, TranslationEng is never touched
    with open(WORDLIST, newline="", encoding="utf-8") as f:
        fresh = not any(name in next(csv.reader(f)) for name in VIEWS.values())
    if fresh or not Path(BACKUP).exists():
        shutil.copyfile(WORDLIST, BACKUP)
    write_wordlist(WORDLIST, rows, terminator, final_newline)
    print(f"rewrote {WORDLIST}: {changed} cells changed (original kept as {BACKUP})")
else:
    print(f"{WORDLIST} unchanged — the variety columns are up to date")
