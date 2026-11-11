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
"""
import collections
import csv
import hashlib
import json
import os
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)  # every path here, and in the modules below, is relative to the repository

import sense_rows
import vetted_senses
from wiktionary_db import WiktionaryDB, LMDB_DIR
from wiktionary_extract import SENSES_LMDB

WORD_LIST = "word-list.csv"
TMX_FILE = "Doxo_passages.tmx"
RANKING_FILE = "Doxo_course_ranking.csv"
VERDICTS_FILE = vetted_senses.VETTING_LOG
EXPORT_FILE = "sense_vetting_export.tsv"
PAGE_FILE = "sense_vetter.html"
PORT = int(os.environ.get("SV_PORT", 8090))
HUMAN_TIERS = ("v", "e")  # vetted, expert

LLM_AUTHORED = "Thirty Short Stories in Globasa"
MAX_USAGES = 3
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
# Sheet column -> word-list column, with the two proofread languages first.
LANGUAGES = {"Epo": ("TranslationEpo", "Eo"), "Spa": ("TranslationSpa", "Es"),
             "French": ("TranslationFra", "Fr"), "German": ("TranslationDeu", "De"),
             "Russian": ("TranslationRus", "Ru"), "Mandarin": ("TranslationZho", "Zh"),
             "Hindi": ("TranslationHin", "Hi"), "Arabic": ("TranslationAra", "Ar")}
FIELD_LABEL = re.compile(r"^[a-z][a-z ,'-]{2,30}:")
REGISTER = re.compile(r"\b(slang|vulgar|archaic|obsolete|dated|dialect\w*|nonstandard|colloquial|derogatory)\b")
STOP = {"the", "and", "for", "with", "that", "this", "from", "which", "used", "not", "are", "was"}
BINOMIAL = re.compile(r"(?:(?<=[a-z,;:] )|(?<=\())([A-Z][a-z]{3,}) ([a-z]{3,})\b")
HIGHER_TAXON = re.compile(r"\b(?:genus|family|order|subfamily|class|species|tribe|subspecies|suborder|phylum)\s+([A-Z][a-z]{3,})\b"
                          r"|\b([A-Z][a-z]{3,}(?:idae|aceae|ales|inae|oidea|iformes|ineae))\b")
GLOSS_NOTE = re.compile(r"_([A-Z][a-z]+(?: [a-z]+)?)_")  # Panthera tigris, Aves; two letters would be element symbols
MIN_TAG_WORDS = 5  # a tag with fewer words cannot show which words of a definition are typical of it
NOT_A_GENUS = re.compile(r"(?:an|ish|ese|ic|ch)$|^(?:Latin|Greek|Thai|Swiss|Human)$")  # American marten, Latin plumbum
BIOLOGICAL_TAGS = {"hewan", "mamoyen", "piu", "mahi", "planta", "fruta", "sabzi", "flura", "bio"}  # a species name fits these


def text(value):
    return str(value).strip() if value is not None else ""


def content_tokens(value):
    normal = unicodedata.normalize("NFKC", value).lower()
    return {w for w in re.findall(r"[^\W\d_]+", normal) if len(w) > 2 and w not in STOP}


def terms(value):
    """Split a translation cell or gloss into comparable terms, without notes or PoS prefixes."""
    normal = unicodedata.normalize("NFKC", value).lower()
    normal = re.sub(r"<[^>]*>|\([^)]*\)|_[^_]*_", "", normal)
    normal = re.sub(r"(^|[;,])\s*[^\s,;:]{1,6}:", r"\1", normal)
    return [t.strip(" /") for t in re.split(r"[,;/、，；]", normal) if t.strip(" /")]


def load_glosses():
    if not os.path.exists(WORD_LIST):
        sys.exit(f"{WORD_LIST} is missing: run ./setup.sh --vetter first.")
    with open(WORD_LIST, encoding="utf-8") as f:
        return {r["Word"].strip().lower(): r for r in csv.DictReader(f)}


def load_ranks():
    ranks = {}
    if not os.path.exists(RANKING_FILE):
        print(f"  {RANKING_FILE} not found: senses with equal scores keep word-list order (fallback: no course order)")
        return ranks
    with open(RANKING_FILE, encoding="utf-8") as f:
        for rank, row in enumerate(csv.reader(f, delimiter="\t"), start=1):
            if row:
                ranks.setdefault(row[0].strip().lower(), rank)
    return ranks


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


def row_id(word, label):
    return hashlib.sha1(f"{word}|{label}".encode()).hexdigest()[:16]


def compare_translations(row, col, entry):
    """Return per-language comparisons of this sense's translations with the word's own glosses."""
    compared = []
    for column, (gloss_column, short) in LANGUAGES.items():
        # Slashes marked a mismatch against an older word list, so they are recomputed here.
        cell = text(row[col[column]]) if column in col else ""
        if not cell:
            continue
        own = set(terms(entry.get(gloss_column, "")))
        if not own:
            continue
        found = [{"t": t, "hit": t in own} for t in dict.fromkeys(terms(cell))]
        if found:
            compared.append({"lang": short, "terms": found, "hit": any(f["hit"] for f in found)})
    return compared


def score_row(sense, entry):
    """Higher means a more obvious match. Weights reflect the cues measured on vetted rows."""
    label = sense["label"].lower()
    full = f"{label} {sense['definition'].lower()}"
    hits = {c["lang"] for c in sense["translations"] if c["hit"]}
    score, why = 0, []
    if "Eo" in hits:
        score += 3
        why.append(("good", "Eo matches"))
    if "Es" in hits:
        score += 3
        why.append(("good", "Es matches"))
    others = len(hits - {"Eo", "Es"})
    if others:
        score += min(others, 3)
        why.append(("good", f"{others} other language{'s' if others > 1 else ''}"))
    if sense["first_listed"]:
        score += 1
        why.append(("good", "listed first"))
    if sense["glosses"] > 1:
        score += 1
        why.append(("good", "under 2+ glosses"))
    if sense["app"] == "s":
        score += 1
        why.append(("good", "script said yes"))
    elif sense["tier"] == "a" and sense["app"] == "n":
        score -= 2
        why.append(("bad", "script said no"))
    if FIELD_LABEL.match(label) or REGISTER.search(full):
        score -= 2
        why.append(("bad", "field or register label"))
    clarifier = content_tokens(sense["clarification"])
    if clarifier and not clarifier & content_tokens(full):
        score -= 2
        why.append(("bad", "gloss clarifier not mentioned"))
    if not sense["translations"]:
        score -= 1
        why.append(("bad", "nothing to compare"))
    return score, why


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
    col = {name: i for i, name in enumerate(sense_rows.HEADER)}
    sense_col = next(i for i, name in enumerate(sense_rows.HEADER) if name.startswith("Wiktionary Sense"))
    # The spreadsheet's and earlier decisions; the page's own verdicts are kept apart, so they stay undoable.
    markings = vetted_senses.load_markings("en", include_log=False)
    db = open_db()
    senses = {}
    per_gloss = collections.Counter()
    for row in sense_rows.rows(db, markings):
        if len(row) <= sense_col:
            continue
        word, label = text(row[col["Glb"]]), text(row[sense_col])
        if not word or not label:
            continue
        key = row_id(word.lower(), label)
        eng, pos = text(row[col["Eng"]]), text(row[col["Prt of Sp"]])
        per_gloss[(word.lower(), eng, pos)] += 1
        sense = senses.get(key)
        if sense is None:
            sense = senses[key] = {
                "id": key, "word": word, "label": label, "eng": eng, "pos": pos,
                "definition": text(row[col["Definition"]]),
                "example": text(row[col["Example"]]),
                "clarification": text(row[col["Clarification"]]),
                "keys": [], "tier": "", "app": "", "glosses": 0, "engs": set(),
                "first_listed": per_gloss[(word.lower(), eng, pos)] == 1,
                "translations": compare_translations(row, col, glosses.get(word.lower(), {})),
            }
        gloss_key = [eng, pos, text(row[col["VerbType"]])]
        if gloss_key not in sense["keys"]:
            sense["keys"].append(gloss_key)
        sense["glosses"] += 1
        sense["engs"].add(eng.lower())
        tier, app = text(row[col["Tier"]]), text(row[col["App?"]])
        # A human verdict outranks a script's when a label repeats.
        if tier in HUMAN_TIERS or not sense["tier"]:
            sense["tier"], sense["app"] = tier, app
    db.close()
    return senses


def word_tags(word):
    return [t.strip() for t in text(glosses.get(word, {}).get("Tags")).split(",") if t.strip()]


def sense_text(sense):
    return unicodedata.normalize("NFKC", f"{sense['label']} {sense['definition']}").lower()


def mentions(term, lowered):
    return re.search(rf"\b{re.escape(term)}(?:s|es)?\b", lowered) is not None


def plain_english_words(all_senses):
    """Words seen after a lowercase word are English: "Usage notes" is no species, "Felis catus" is."""
    plain = set()
    for sense in all_senses:
        words = sense["definition"].split()
        for before, word in zip(words, words[1:]):
            if before.islower() and word.islower():
                plain.add(word.strip(".,;:()[]\"'"))
    return plain


def find_taxa(sense, plain):
    found = {f"{genus} {species}" for genus, species in BINOMIAL.findall(sense["definition"])
             if species not in plain and not NOT_A_GENUS.search(genus)}
    for named, by_ending in HIGHER_TAXON.findall(sense["definition"]):
        found.add(named or by_ending)
    return found


def tag_profiles(words_with_senses):
    """Each tag's own English gloss, plus the definition words typical of its words. No verdicts used."""
    members = collections.defaultdict(set)
    tokens = {}
    for word, group in words_with_senses.items():
        tokens[word] = set().union(*(content_tokens(sense_text(s)) for s in group))
        for tag in word_tags(word):
            members[tag].add(word)
    spread = collections.Counter(token for found in tokens.values() for token in found)
    gloss_terms, typical = {}, {}
    for tag, words in members.items():
        if tag.lower() in glosses:
            gloss_terms[tag] = [t for t in terms(text(glosses[tag.lower()].get("TranslationEng"))) if len(t) > 2]
        if tag.lower() in glosses and len(words) >= MIN_TAG_WORDS:
            counted = collections.Counter(token for word in words for token in tokens[word])
            typical[tag] = {token for token, n in counted.items()
                            if n >= 3 and n / len(words) >= 0.2
                            and (n / len(words)) / (spread[token] / len(tokens)) >= 5}
    return members, gloss_terms, typical


def tag_fit(sense, tag, gloss_terms, typical):
    """2 for the tag's own gloss, two typical words or a species name on a biological tag; 1 for one typical word."""
    if tag in BIOLOGICAL_TAGS and sense["taxa"]:
        return 2
    lowered = sense_text(sense)
    if any(t not in sense["engs"] and mentions(t, lowered) for t in gloss_terms.get(tag, ())):
        return 2
    return min(len(typical.get(tag, set()) & content_tokens(lowered)), 2)


def score_against_siblings(word, group, plain, gloss_terms, typical):
    """Add the cues that need a word's other senses: glosses, taxa and tags."""
    entry = glosses.get(word, {})
    all_glosses = list(dict.fromkeys(terms(text(entry.get("TranslationEng")))))
    notes = [n for n in GLOSS_NOTE.findall(text(entry.get("TranslationEng"))) if len(n) > 2]
    for sense in group:
        lowered = sense_text(sense)
        sense["also_says"] = [t for t in all_glosses
                              if len(t) > 2 and not any(t in own or own in t for own in sense["engs"]) and mentions(t, lowered)]
        sense["taxa"] = find_taxa(sense, plain)
        sense["note_found"] = [n for n in notes if n.split()[0] in f"{sense['label']} {sense['definition']}"]
        sense["fits"] = {tag: fit for tag in word_tags(word) if (fit := tag_fit(sense, tag, gloss_terms, typical))}
    said_by = collections.Counter(t for s in group for t in s["also_says"])
    any_note = any(s["note_found"] for s in group)
    any_taxon = any(s["taxa"] for s in group)
    any_fit = any(s["fits"] for s in group)
    for sense in group:
        # A synonym that few senses share is what marks out this sense among the word's others.
        distinct = [t for t in sense["also_says"] if said_by[t] <= max(1, len(group) // 3)]
        if distinct:
            sense["score"] += 2
            sense["why"].append(("good", f'also says "{distinct[0]}"'))
        elif sense["also_says"]:
            sense["score"] += 1
            sense["why"].append(("good", f'also says "{sense["also_says"][0]}"'))
        if sense["note_found"]:
            sense["score"] += 3
            sense["why"].append(("good", f"gloss names {sense['note_found'][0]}"))
        elif any_note:
            sense["score"] -= 2
            sense["why"].append(("bad", "another sense has the gloss's name"))
        elif sense["taxa"]:
            sense["score"] += 1
            sense["why"].append(("good", f"names {min(sense['taxa'])}"))
        elif any_taxon:
            sense["score"] -= 1
            sense["why"].append(("bad", "another sense names a species"))
        if sense["fits"]:
            tag = max(sense["fits"], key=sense["fits"].get)
            sense["score"] += sense["fits"][tag]
            sense["why"].append(("good", f"fits tag {tag}"))
        elif any_fit:
            sense["score"] -= 2
            sense["why"].append(("bad", "another sense fits the tag"))


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
accepted_by_word = collections.defaultdict(list)
for sense in senses.values():
    entry = glosses.get(sense["word"].lower(), {})
    sense["score"], sense["why"] = score_row(sense, entry)
    if sense["tier"] in HUMAN_TIERS and sense["app"] == "s":
        accepted_by_word[sense["word"].lower()].append(sense["label"])
senses_by_word = collections.defaultdict(list)
for sense in senses.values():
    senses_by_word[sense["word"].lower()].append(sense)
tag_members, tag_gloss_terms, tag_typical = tag_profiles(senses_by_word)
plain_words = plain_english_words(senses.values())
for word, group in senses_by_word.items():
    score_against_siblings(word, group, plain_words, tag_gloss_terms, tag_typical)


def order_key(sense):
    return (-sense["score"], ranks.get(sense["word"].lower(), 10**6), sense["word"], sense["label"])


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
        "word_marked": word_is_marked(word),
        "other_count": len(senses_by_word[word]) - 1,
        "tags": word_tags(word),
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


def word_is_marked(word):
    """Any mark on any sense counts: applies, doesn't apply or unsure, from this page or the sheet."""
    return any(is_vetted(s) for s in senses_by_word[word])


def is_unsure(sense):
    return verdicts.get(sense["id"], {}).get("verdict") == "u"


def matching(scope, query, include_vetted=False, tag=""):
    query = query.strip().lower()
    for sense in tag_order(tag) if tag else ordered:
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
        if scope == "unmarked" and word_is_marked(word):
            continue
        yield sense


def counts(scope, query, include_vetted, tag=""):
    """How many senses this view lists, and how many of them still await a mark."""
    found = list(matching(scope, query, include_vetted, tag))
    return found, {"matched": len(found),
                   "remaining": len(found) if scope == "unsure" else sum(not is_vetted(s) for s in found)}


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
