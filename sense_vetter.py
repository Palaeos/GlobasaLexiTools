"""
Browser page for quickly vetting Wiktionary senses, most obvious matches first. No model.

    python sense_vetter.py            then open http://localhost:8090
    python sense_vetter.py --check    how well the ordering matches past human verdicts
    python sense_vetter.py --export   write sense_vetting_export.tsv (the page's decisions,
                                      in the columns of vetted_senses.tsv)

On a fresh clone, ./setup.sh --vetter prepares everything it reads.

The senses are generated as the sense generator ("Wiktionary sense based translation
extender 3.py") generates the spreadsheet: sense_rows.py over word-list.csv and the English
Wiktionary database (WiktionaryLMDB/, or the extract WiktionaryLMDB_senses/ that
wiktionary_extract.py --senses streams from the dump). They start with the decisions in
vetted_senses.tsv.

Verdicts are appended to sense_vetting.jsonl as you go, so nothing is lost by closing the
page. vetted_senses.py lays that log over vetted_senses.tsv, so the sense generator and the
Menalari extension see the page's verdicts too. Corpus examples (Doxo_passages.tmx) and the
course order (Doxo_course_ranking.csv) are optional.

The view "Queue" lists the senses of a queue file (SV_QUEUE, by default the one
parallel_lexsel/vetting_queue.py writes) in the queue's order, each with its evidence: the
French word of Le Petit Prince it would give the glb-fra pair, how often the text needs it, and
what the English and Chinese translations aligned to it.

The button "Rebuild" reruns the Wiktionary extension with the page's verdicts, build_bidix.py (every
glb-X bidix) and make in every configured GlobasaTranslation/apertium-glb-X pair. Only when the
Le Petit Prince data exists does it then run parallel_lexsel/resolution.py (which of the book's
French words the glb-fra pair knows now) and vetting_queue.py (resolved words leave the queue).
"""
import collections
import csv
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
import subprocess
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)  # every path here, and in the modules below, is relative to the repository

import sense_ranking
import sense_rows
import vetted_senses
from sense_ranking import senses_from_rows, text
from wiktionary_db import WiktionaryDB, LMDB_DIR
from wiktionary_extract import SENSES_LMDB

WORD_LIST = "word-list.csv"
TMX_FILE = "Doxo_passages.tmx"
RANKING_FILE = "Doxo_course_ranking.csv"
VERDICTS_FILE = vetted_senses.VETTING_LOG
EXPORT_FILE = "sense_vetting_export.tsv"
PAGE_FILE = "sense_vetter.html"
PORT = int(os.environ.get("SV_PORT", 8090))
# Optional queue of senses proposed by another tool, shown as the view "queue" in its own order
# with its evidence: by default parallel_lexsel/vetting_queue.py's senses that would give the
# glb-fra pair the French words of Le Petit Prince it lacks.
QUEUE_FILE = os.environ.get("SV_QUEUE", os.path.join("parallel_lexsel_cache", "lpp", "fra_glb",
                                                     "vetting_queue.tsv"))
QUEUE_EVIDENCE = 3  # French words shown per queued sense
HUMAN_TIERS = sense_ranking.HUMAN_TIERS

LLM_AUTHORED = "Thirty Short Stories in Globasa"
MAX_USAGES = 3
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def load_glosses():
    return sense_ranking.load_glosses(WORD_LIST)


def load_ranks():
    return sense_ranking.load_ranks(RANKING_FILE)


def load_usages():
    """Return {word: [usage]}, English-paired first and independently written texts before the LLM-assisted one."""
    usages = collections.defaultdict(list)
    if not os.path.exists(TMX_FILE):
        print(f"  {TMX_FILE} not found: no corpus examples (fallback: no corpus)")
        return usages
    for tu in ET.parse(TMX_FILE).getroot().find("body").findall("tu"):
        segs = {t.get(XML_LANG): t.find("seg").text for t in tu.findall("tuv")}
        usage = {"glb": segs["glb"], "en": segs.get("en", ""), "text": tu.find("prop").text}
        for word in set(re.findall(r"[a-z]+(?:-[a-z]+)*", segs["glb"].lower())):
            usages[word].append(usage)
    for found in usages.values():
        found.sort(key=lambda u: (not u["en"], u["text"] == LLM_AUTHORED, len(u["glb"])))
    return usages


def open_db():
    """The full English database when this machine has it, else the extract of the word list's glosses."""
    for path, note in ((LMDB_DIR, ""), (SENSES_LMDB, " (fallback: no full WiktionaryLMDB, extract of the word list's glosses)")):
        if os.path.exists(path):
            print(f"  Wiktionary: {path}{note}")
            return WiktionaryDB(path=path, readonly=True)
    sys.exit("No English Wiktionary database: run ./setup.sh --vetter first "
             "(it streams the word list's entries from the dump into WiktionaryLMDB_senses/).")


def load_senses(glosses):
    """One sense per word and Wiktionary label, gathered from every gloss row that lists it."""
    # The spreadsheet's and earlier decisions; the page's own verdicts are kept apart, so they stay undoable.
    markings = vetted_senses.load_markings("en", include_log=False)
    db = open_db()
    senses = senses_from_rows(sense_rows.rows(db, markings), glosses)
    db.close()
    return senses


def word_tags(word):
    return sense_ranking.word_tags(glosses, word)


def apply_verdict(verdicts, entry):
    if entry["verdict"] == "clear":
        verdicts.pop(entry["id"], None)
    else:
        verdicts[entry["id"]] = entry


def load_verdicts():
    """Replay the log: the latest verdict for each sense wins, and each action stays undoable."""
    verdicts, undo_stack = {}, []
    if os.path.exists(VERDICTS_FILE):
        with open(VERDICTS_FILE, encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                batch = entry.get("batch") or entry["when"]
                if entry.get("undo"):
                    if undo_stack and undo_stack[-1]["batch"] == batch:
                        undo_stack.pop()
                else:
                    previous = verdicts.get(entry["id"], {}).get("verdict", "clear")
                    if not undo_stack or undo_stack[-1]["batch"] != batch:
                        undo_stack.append({"batch": batch, "changes": []})
                    undo_stack[-1]["changes"].append((entry["id"], previous))
                apply_verdict(verdicts, entry)
    return verdicts, undo_stack


print("Loading the sense sheet, word list and corpus...")
glosses = load_glosses()
ranks = load_ranks()
usages = load_usages()
senses = load_senses(glosses)
senses_by_word, (tag_members, tag_gloss_terms, tag_typical) = sense_ranking.rank(senses, glosses)
accepted_by_word = collections.defaultdict(list)
for sense in senses.values():
    if sense["tier"] in HUMAN_TIERS and sense["app"] == "s":
        accepted_by_word[sense["word"].lower()].append(sense["label"])


def load_queue():
    """Queued sense ids in queue order, and each one's evidence (one entry per French word, or a
    note for a sense queued only so that its word gets vetted completely)."""
    order, evidence = [], collections.defaultdict(list)
    if not os.path.exists(QUEUE_FILE):
        return order, evidence
    with open(QUEUE_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            if row["id"] not in evidence:
                order.append(row["id"])
            if not row.get("fr_lemma"):
                # A queue of whole words (vetting_queue.py): this sense lists no French word itself,
                # it is queued so the word gets vetted completely in this part of speech.
                evidence[row["id"]].append({"note": (
                    f"Other sense of {row.get('unit', row['glb'])}, {row.get('unit_status', '')}: "
                    f"vet the whole word; the pivots tie {row.get('unit_tokens', '?')} French "
                    f"occurrences to it")})
                continue
            evidence[row["id"]].append({
                "unit": row.get("unit", ""), "unit_status": row.get("unit_status", ""),
                "fr": row["fr_lemma"], "freq": row["fr_freq"], "support": row["support"],
                "flag": row["flag"], "en": row["en_aligned"], "zh": row["zh_aligned"],
                "ex_fr": row["example_fr"], "ex_en": row["example_en"], "ex_zh": row["example_zh"]})
    missing = [key for key in order if key not in senses]
    print(f"  Queue {QUEUE_FILE}: {len(order)} senses"
          + (f" ({len(missing)} not among this sheet's senses, left out)" if missing else ""))
    return [key for key in order if key in senses], evidence


queue_order, queue_evidence = load_queue()


def order_key(sense):
    return sense_ranking.order_key(sense, ranks)


ordered = sorted(senses.values(), key=order_key)
for group in senses_by_word.values():
    group.sort(key=order_key)
orders_by_tag = {}


def tag_order(tag):
    """A tag's senses with those fitting it first, so browsing a tag leads with the senses it favours."""
    if tag not in orders_by_tag:
        orders_by_tag[tag] = sorted((s for w in tag_members.get(tag, ()) for s in senses_by_word[w]),
                                    key=lambda s: (-s["fits"].get(tag, 0), *order_key(s)))
    return orders_by_tag[tag]


if "--check" in sys.argv:
    bands = collections.defaultdict(lambda: [0, 0, 0])
    for sense in ordered:
        band = "7+" if sense["score"] >= 7 else "5-6" if sense["score"] >= 5 else "3-4" if sense["score"] >= 3 else "1-2" if sense["score"] >= 1 else "0 or less"
        if sense["tier"] in HUMAN_TIERS:
            bands[band][0 if sense["app"] == "s" else 1] += 1
        elif not sense["tier"] or sense["tier"] == "a":
            bands[band][2] += 1
    print(f"{'score':10}{'accepted':>10}{'rejected':>10}{'accept %':>10}{'to vet':>9}")
    for band in ("7+", "5-6", "3-4", "1-2", "0 or less"):
        a, r, todo = bands[band]
        print(f"{band:10}{a:10}{r:10}{100 * a / max(a + r, 1):10.1f}{todo:9}")
    sys.exit()

if "--export" in sys.argv:
    verdicts, _ = load_verdicts()
    with open(EXPORT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(vetted_senses.COLUMNS + ["When"])
        # Unsure is a note to come back, not a judgement, so it never reaches the master sheet.
        decided = {key: entry for key, entry in verdicts.items() if entry["verdict"] != "u"}
        for key, entry in decided.items():
            sense = senses.get(key)
            for eng, pos, vt in entry.get("keys") or (sense["keys"] if sense else ()):
                writer.writerow([entry["word"], "en", eng, pos, vt, entry["label"], entry["verdict"], "v",
                                 entry["when"]])
    print(f"Wrote {len(decided)} verdicts to {EXPORT_FILE} ({len(verdicts) - len(decided)} unsure left out)")
    sys.exit()

verdicts, undo_stack = load_verdicts()


def sheet_verdict(sense):
    if sense["tier"] not in HUMAN_TIERS:
        return ""
    return "s" if sense["app"] == "s" else "n"


def card(sense):
    word = sense["word"].lower()
    entry = glosses.get(word, {})
    return {
        "id": sense["id"], "word": sense["word"], "pos": sense["pos"], "eng": sense["eng"],
        "label": sense["label"], "definition": sense["definition"], "example": sense["example"],
        "score": sense["score"], "why": sense["why"], "translations": sense["translations"],
        "gloss_en": text(entry.get("TranslationEng")), "gloss_eo": text(entry.get("TranslationEpo")),
        "gloss_es": text(entry.get("TranslationSpa")), "parts": text(entry.get("LexiliAsel")),
        "accepted": accepted_by_word[word][:6], "usage_count": len(usages.get(word, ())),
        "usages": usages.get(word, [])[:MAX_USAGES], "script": sense["app"] if sense["tier"] == "a" else "",
        "sheet_verdict": sheet_verdict(sense),
        "verdict": current_verdict(sense),
        "word_marked": word_is_marked(word, sense["gloss_pos"]), "gloss_pos": sense["gloss_pos"],
        "other_count": len(senses_by_word[word]) - 1,
        "tags": word_tags(word),
        "queue": queue_evidence.get(sense["id"], [])[:QUEUE_EVIDENCE],
    }


def current_verdict(sense):
    return verdicts[sense["id"]]["verdict"] if sense["id"] in verdicts else sheet_verdict(sense)


def peek(word):
    """Every sense of a word, most obvious first, for comparing before deciding."""
    return [{"id": s["id"], "label": s["label"], "definition": s["definition"], "pos": s["pos"], "eng": s["eng"],
             "verdict": current_verdict(s), "why": s["why"]} for s in senses_by_word[word.strip().lower()]]


def tag_list():
    """Every tag with its English gloss, so a tag can be chosen without knowing the Globasa word."""
    listed = []
    for tag, words in tag_members.items():
        gloss = tag_gloss_terms.get(tag, [])
        listed.append({"tag": tag, "gloss": ", ".join(gloss[:2]), "words": len(words)})
    return sorted(listed, key=lambda t: t["tag"].lower())


def is_vetted(sense):
    return sense["tier"] in HUMAN_TIERS or sense["id"] in verdicts


def word_is_marked(word, pos):
    """Whether the word is vetted in this part of speech (gloss_pos): any mark on any of its senses
    of that part of speech counts (applies, doesn't apply or unsure, from this page or the sheet).
    A word vetted as a noun still waits to be vetted as a verb."""
    return any(is_vetted(s) for s in senses_by_word[word] if s["gloss_pos"] == pos)


def is_unsure(sense):
    return verdicts.get(sense["id"], {}).get("verdict") == "u"


def matching(scope, query, include_vetted=False, tag=""):
    query = query.strip().lower()
    if scope == "queue":
        source = [senses[key] for key in queue_order]
    else:
        source = tag_order(tag) if tag else ordered
    for sense in source:
        if scope == "unsure":
            if not is_unsure(sense):
                continue
        elif is_vetted(sense) and not include_vetted:
            continue
        word = sense["word"].lower()
        if query and query != word:
            continue
        if scope == "corpus" and word not in usages:
            continue
        if scope == "noncorpus" and word in usages:
            continue
        if scope == "unmarked" and word_is_marked(word, sense["gloss_pos"]):
            continue
        yield sense


def counts(scope, query, include_vetted, tag=""):
    """How many senses this view lists, and how many of them still await a mark."""
    found = list(matching(scope, query, include_vetted, tag))
    return found, {"matched": len(found),
                   "remaining": len(found) if scope == "unsure" else sum(not is_vetted(s) for s in found)}


# "Rebuild": rerun the Wiktionary extension (with this page's verdicts), every glb-X bidix
# (build_bidix.py) and every built pair (make), so the verdicts reach the translators. When the
# Le Petit Prince data exists (parallel_lexsel), it then checks which French words of the book the
# glb-fra pair knows now and rebuilds the queue: that part concerns only the book's vocabulary.
# About a minute (pairs whose dix changed recompile); one run at a time, in a thread, polled by
# the page. A pair that fails to build is reported and the others still build.
PAIRS_ROOT = "GlobasaTranslation"
LPP_DIR = os.path.join("parallel_lexsel_cache", "lpp", "fra_glb")
RESOLUTION_FILE = os.path.join(LPP_DIR, "resolution_status.json")
rebuild = {"running": False, "step": "", "ok": None, "log": [], "started": "", "finished": "",
           "result": None}
rebuild_lock = threading.Lock()


def built_pairs():
    """The glb-X pair checkouts that have been configured (a Makefile), e.g. apertium-glb-fra."""
    if not os.path.isdir(PAIRS_ROOT):
        return []
    return sorted(d for d in os.listdir(PAIRS_ROOT)
                  if d.startswith("apertium-glb-") and os.path.exists(os.path.join(PAIRS_ROOT, d, "Makefile")))


def lpp_summary():
    """Le Petit Prince vocabulary: which French words the glb-fra pair lacked it knows now."""
    if not os.path.exists(RESOLUTION_FILE):
        return None
    with open(RESOLUTION_FILE, encoding="utf-8") as f:
        status = json.load(f)
    words = status["words"]
    return {"when": status["when"], "resolved": status["resolved"], "missing": status["missing"],
            "tokens_resolved": status["tokens_resolved"], "tokens_missing": status["tokens_missing"],
            "first_run": status.get("first_run", False),
            "new": [{"fr": k.split(" / ")[0].split("<")[0], "freq": words[k]["freq"], "glb": words[k]["glb"]}
                    for k in status["new"][:60]], "new_count": len(status["new"])}


def bidix_counts():
    counts = collections.Counter()
    if os.path.exists("bidix_entries.tsv"):
        with open("bidix_entries.tsv", encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                counts[row["lang"]] += 1
    return dict(counts)


def run_step(name, cmd, cwd="."):
    rebuild["step"] = name
    rebuild["log"].append(f"== {name}")
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    out = (proc.stdout + proc.stderr).strip().splitlines()
    rebuild["log"].extend(out[-6:])
    if proc.returncode != 0:
        rebuild["log"].append(f"{name} failed (exit {proc.returncode})")
    return proc.returncode == 0, out


def run_rebuild():
    global queue_order, queue_evidence
    result = {"extension": "", "bidix": {}, "pairs": {}, "lpp": None}
    ok, out = run_step("Wiktionary extension", [sys.executable, "-u", "Wiktionary extension builder.py"])
    result["extension"] = next((l.strip() for l in out if l.startswith("Wrote menalariExtension")), "")
    if ok:
        ok, _ = run_step("bidixes (build_bidix.py)", [sys.executable, "-u", "build_bidix.py"])
        result["bidix"] = bidix_counts()
    if ok:
        for pair in built_pairs():
            built, out = run_step(f"build {pair}", ["make"], os.path.join(PAIRS_ROOT, pair))
            result["pairs"][pair] = "built" if built else (out[-1] if out else "failed")
        # Le Petit Prince vocabulary, only where that data exists
        if os.path.exists(os.path.join(LPP_DIR, "resolve_list.tsv")):
            lpp_ok, _ = run_step("Le Petit Prince: check the French words",
                                 [sys.executable, "-u", os.path.join("parallel_lexsel", "resolution.py")])
            if lpp_ok:
                lpp_ok, _ = run_step("Le Petit Prince: rebuild the queue",
                                     [sys.executable, "-u", os.path.join("parallel_lexsel", "vetting_queue.py")])
            if lpp_ok:
                queue_order, queue_evidence = load_queue()
                result["lpp"] = lpp_summary()
    rebuild.update(running=False, ok=ok, step="", result=result,
                   finished=datetime.now().isoformat(timespec="seconds"))


def start_rebuild():
    with rebuild_lock:
        if rebuild["running"]:
            return False
        rebuild.update(running=True, ok=None, log=[], result=None, step="starting",
                       started=datetime.now().isoformat(timespec="seconds"), finished="")
    threading.Thread(target=run_rebuild, daemon=True).start()
    return True


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/":
            with open(PAGE_FILE, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif url.path == "/api/rows":
            params = parse_qs(url.query)
            limit = min(int(params.get("limit", ["50"])[0]), 200)
            offset = int(params.get("offset", ["0"])[0])
            found, view = counts(params.get("scope", ["all"])[0], params.get("q", [""])[0],
                                 params.get("vetted", ["0"])[0] == "1", params.get("tag", [""])[0])
            self.send_tally(rows=[card(s) for s in found[offset:offset + limit]], **view)
        elif url.path == "/api/tags":
            self.send_json({"tags": tag_list()})
        elif url.path == "/api/rebuild":
            # Before any rebuild in this session, the last Le Petit Prince check (if any) is shown.
            last = None if rebuild["running"] or rebuild["result"] else {"lpp": lpp_summary()}
            self.send_json(dict(rebuild, log=rebuild["log"][-40:], result=rebuild["result"] or last))
        elif url.path == "/api/senses":
            self.send_json({"senses": peek(parse_qs(url.query).get("word", [""])[0])})
        else:
            self.send_error(404)

    def write_entries(self, entries):
        with open(VERDICTS_FILE, "a", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                apply_verdict(verdicts, entry)

    def send_tally(self, **extra):
        tally = collections.Counter(v["verdict"] for v in verdicts.values())
        self.send_json({"accepted": tally["s"], "rejected": tally["n"], "unsure": tally["u"],
                        "undoable": len(undo_stack), **extra})

    def send_changed(self, request, keys):
        """Report changed senses and the client's view counts, since one mark can drop a whole word."""
        _, view = counts(request.get("scope", "all"), request.get("q", ""), request.get("vetted", False),
                         request.get("tag", ""))
        self.send_tally(cards=[card(senses[key]) for key in keys], **view)

    def undo_last(self, request):
        """Put every sense in the last action back to what it was before, restarts included."""
        if not undo_stack:
            self.send_changed(request, [])
            return
        action = undo_stack.pop()
        when = datetime.now().isoformat(timespec="seconds")
        self.write_entries([
            {"id": key, "word": senses[key]["word"], "label": senses[key]["label"], "verdict": previous,
             "when": when, "batch": action["batch"], "undo": True, "keys": senses[key]["keys"]}
            for key, previous in reversed(action["changes"]) if key in senses
        ])
        self.send_changed(request, [key for key, _ in action["changes"] if key in senses])

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/rebuild":
            self.send_json({"started": start_rebuild(), "running": True})
            return
        if path not in ("/api/undo", "/api/verdict"):
            self.send_error(404)
            return
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if path == "/api/undo":
            self.undo_last(request)
            return
        verdict = request["verdict"]
        if verdict not in ("s", "n", "u", "clear"):
            self.send_json({"error": "unknown verdict"}, 400)
            return
        when = datetime.now().isoformat(timespec="seconds")
        batch = f"{when}-{time.time_ns()}"
        keys = [key for key in request["ids"] if key in senses]
        if keys:
            undo_stack.append({"batch": batch, "changes": [
                (key, verdicts.get(key, {}).get("verdict", "clear")) for key in keys]})
        self.write_entries([
            {"id": key, "word": senses[key]["word"], "label": senses[key]["label"],
             "verdict": verdict, "when": when, "batch": batch, "keys": senses[key]["keys"]} for key in keys
        ])
        self.send_changed(request, keys)


print(f"Ready: open http://localhost:{PORT}  ({len(verdicts)} verdicts loaded)")
ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
