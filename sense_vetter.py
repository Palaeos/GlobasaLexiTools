"""
Browser page for quickly vetting Wiktionary senses, most obvious matches first. No model.

    python sense_vetter.py            then open http://localhost:8090
    python sense_vetter.py --check    how well the ordering matches past human verdicts
    python sense_vetter.py --export   write sense_vetting_export.tsv (your page scores,
                                      in the columns of vetted_senses.tsv)

On a fresh clone, ./setup.sh --vetter prepares everything it reads.

The senses are generated as the sense generator ("Wiktionary sense based translation
extender 3.py") generates the spreadsheet: sense_rows.py over word-list.csv and the English
Wiktionary database (WiktionaryLMDB/, or the extract WiktionaryLMDB_senses/ that
wiktionary_extract.py --senses streams from the dump). They start with the decisions in
vetted_senses.tsv.

You score senses 1-5 (5 applies, 3 unsure, 1 does not) in your own column, named by SV_VETTER or
"vetter" in .senses_config.json (default Paleos). Scores are appended to sense_vetting.jsonl as
you go, so nothing is lost by closing the page. vetted_senses.py lays that log over
vetted_senses.tsv, so the sense generator and the Menalari extension see your scores too, and
cards show the other vetters' scores from the shared sheet with the mean that decides
(>= 4 accepted, <= 2 rejected). "Rebuild" first writes your scores into the shared sheet
(vetted_senses.push_owner_scores), so the other vetters see them. Corpus examples (Doxo_passages.tmx) and the
course order (Doxo_course_ranking.csv) are optional.

The view "Queue" lists the senses of a queue file (SV_QUEUE, by default the one
parallel_lexsel/vetting_queue.py writes) in the queue's order, each with its evidence: the
French word of Le Petit Prince it would give the glb-fra pair, how often the text needs it, and
what the English and Chinese translations aligned to it.

The view "Relabel" lists the vetted senses the Menalari extension could not find any more
(menalariExtension_unmatched.tsv, SV_RELABEL) of words left with no sense at all: after a dump
refresh Wiktionary had reworded or replaced their table labels. Words that still have a matched
sense are not re-vetted. Each shows the senses its word now has for the same English word,
with a note naming the label vetted earlier; scoring the matching one carries the decision over
to the new label (the extension picks it up on Rebuild), and the word's other candidates leave
the view. It needs the senses of the refreshed dump: the rebuilt WiktionaryLMDB/, or SV_LMDB.

The view "Countries, languages and their adjectives" lists the senses of the words tagged dexa
(countries) or basa (languages) and of the proper adjectives (su t) derived from them, word by
word. Each card carries a proposal read from its label (a country sense for a country word, a
language sense for a language word, "of / relating to" for a country adjective such as Doycili,
a language sense for a language adjective such as Doycisali; senses such as a given name, a city
or a US state are proposed as not applying). The proposal is a script's guess: key A
scores it (5 or 1) once you have read the card; a card without a proposal needs 1-5 as usual.

The button "Rebuild viewer" does only what the Word Viewer needs: the Wiktionary extension,
then the viewer's own cache (its /rebuild route when it runs at WV_URL, default
http://127.0.0.1:5000; otherwise WordViewerLMDB/ is dropped and rebuilt at its next start).

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
from sense_ranking import row_id, senses_from_rows, text
from wiktionary_db import WiktionaryDB, LMDB_DIR
from wiktionary_extract import SENSES_LMDB
from wiktionary_constants import (WIKTIONARY_SOURCES, WIKT_POS_FALLBACKS, WIKT_POS_SINGLE_FALLBACKS,
                                  GLOSSPOS_TO_WIKT, extract_italic_annotation, pos_groups)
from Lexilista_parser import _expand_gloss_context

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
# Vetted senses the extension builder could not find in the current dump (its report).
RELABEL_FILE = os.environ.get("SV_RELABEL", "menalariExtension_unmatched.tsv")
EXTENSION_FILE = "menalariExtension.tsv"
HUMAN_TIERS = sense_ranking.HUMAN_TIERS
OWNER = vetted_senses.OWNER  # whose column this page scores in (SV_VETTER / .senses_config.json "vetter")

LLM_AUTHORED = "Thirty Short Stories in Globasa"
MAX_USAGES = 3
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


# Pivots (user 2026-11-28): a word's Spanish or Esperanto gloss looked up in that language's own
# Wiktionary (WiktionaryLMDB_es / _eo, "JSONL parser non-English.py"), for distinctions the English
# gloss cannot make: femete "they" (feminine) = es ellas, femkuzin "cousin" = es prima.
PIVOT_WIKTS = ("es", "eo")
PIVOT_COLUMNS = {"es": "TranslationSpa", "eo": "TranslationEpo"}
PIVOT_NAMES = {"es": "Spanish", "eo": "Esperanto"}
# Shown on a pivot card, and matched against the word's own glosses where it has them.
PIVOT_SHOWN = {"es": ["en", "eo", "fr", "de", "it", "pt"], "eo": ["en", "es", "fr", "de", "it", "pt"]}
GLOSS_COLUMNS = {"en": "TranslationEng", "eo": "TranslationEpo", "es": "TranslationSpa"}


def sense_id(source, word, label):
    """The id of a sense: English ones as always; a pivot sense prefixed with its Wiktionary."""
    key = row_id(word.lower(), label)
    return key if source == "en" else f"{source}-{key}"


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
    """The full English database when this machine has it, else the extract of the word list's glosses.
    SV_LMDB=path picks one explicitly (e.g. a fresh extract while the full one is not rebuilt yet)."""
    choices = ((LMDB_DIR, ""), (SENSES_LMDB, " (fallback: no full WiktionaryLMDB, extract of the word list's glosses)"))
    if os.environ.get("SV_LMDB"):
        choices = ((os.environ["SV_LMDB"], " (SV_LMDB)"),)
    for path, note in choices:
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
    if vetted_senses.entry_score(entry) is None:  # "clear"
        verdicts.pop(entry["id"], None)
    else:
        verdicts[entry["id"]] = entry


def logged_score(verdicts, key):
    """The owner's score for a sense from this page's log, or None."""
    return vetted_senses.entry_score(verdicts[key]) if key in verdicts else None


def load_verdicts():
    """Replay the log: the latest score for each sense wins, and each action stays undoable.
    Old entries carry verdicts (s 4, n 2, u 3); edits of the owner's sheet column are replayed
    but are not page actions to undo."""
    verdicts, undo_stack = {}, []
    for entry in vetted_senses.log_entries(VERDICTS_FILE):
        if (entry.get("vetter") or OWNER) != OWNER:
            continue
        batch = entry.get("batch") or entry["when"]
        if entry.get("undo"):
            if undo_stack and undo_stack[-1]["batch"] == batch:
                undo_stack.pop()
        elif entry.get("source") != "sheet":
            previous = logged_score(verdicts, entry["id"])
            if not undo_stack or undo_stack[-1]["batch"] != batch:
                undo_stack.append({"batch": batch, "changes": []})
            undo_stack[-1]["changes"].append((entry["id"], previous))
        apply_verdict(verdicts, entry)
    return verdicts, undo_stack


def load_base_scores():
    """{sense id: {vetter: score}} from vetted_senses.tsv (the sheet's scores, without this page's
    log). A sense listed under several glosses takes each vetter's first score."""
    base = collections.defaultdict(dict)
    for r in vetted_senses.load_rows(include_log=False):
        if r["scores"] and r["Source"] in ("en",) + PIVOT_WIKTS:
            found = base[sense_id(r["Source"], r["Glb"], r["Wiktionary Sense"])]
            for vetter, value in r["scores"].items():
                found.setdefault(vetter, value)
    return base


print("Loading the sense sheet, word list and corpus...")
glosses = load_glosses()
ranks = load_ranks()
usages = load_usages()
senses = load_senses(glosses)
senses_by_word, (tag_members, tag_gloss_terms, tag_typical) = sense_ranking.rank(senses, glosses)
base_scores = load_base_scores()
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


def words_with_senses():
    """Globasa words (lowercase) with at least one vetted sense found in the dump: the extension's
    'Eng with Senses' cell lists them."""
    if not os.path.exists(EXTENSION_FILE):
        return set()
    with open(EXTENSION_FILE, encoding="utf-8") as f:
        return {r["Globasa"].lower() for r in csv.DictReader(f, delimiter="\t")
                if r["Globasa"] and (r.get("Eng with Senses") or "").strip()}


def load_relabel():
    """Candidate senses for each unmatched vetted sense of a word that has no sense left (user
    2026-11-28: re-vet only words now missing a sense entirely; a word that still has a matched
    sense keeps it). Candidates are the senses the word now has for the same English word (other
    labels), in the report's order. Returns the candidate ids in order, each candidate's notes,
    and {candidate id: [units]} where a unit is the candidate ids standing for one unmatched sense."""
    order, evidence, units_of = [], collections.defaultdict(list), collections.defaultdict(list)
    if not os.path.exists(RELABEL_FILE):
        return order, evidence, units_of
    has_sense = words_with_senses()
    found = no_candidates = still_covered = 0
    with open(RELABEL_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            word, eng, old = row["Globasa"].lower(), row["lookup_word"], row["vetted label"]
            if word in has_sense:
                still_covered += 1
                continue
            # Every sense the word now has, through any of its glosses (user 2026-11-28: a word
            # can get its sense through another gloss, hwese "grey" for a lost "gray"), the
            # lost gloss's own first.
            candidates = [sn["id"] for sn in sorted(
                (sn for sn in senses_by_word.get(word, ()) if sn["label"] != old),
                key=lambda sn: not any(k[0].lower() == eng.lower() for k in sn["keys"]))]
            if not candidates:
                no_candidates += 1
                continue
            found += 1
            for key in candidates:
                if key not in evidence:
                    order.append(key)
                units_of[key].append(candidates)
                evidence[key].append({"note": (
                    f"{row['Globasa']} has no sense left: \u201c{old}\u201d ({eng}, {row['pos']}) is gone "
                    f"from Wiktionary. Score 5 if this sense fits the word, through this or another of its "
                    f"glosses.")})
    print(f"  Relabel {RELABEL_FILE}: {found} unmatched senses of words with no sense left have candidates"
          + (f", {no_candidates} without (word or part of speech gone, or no other sense)" if no_candidates else "")
          + f"; {still_covered} skipped (their word still has a sense)")
    return order, evidence, units_of


relabel_order, relabel_evidence, relabel_units_of = load_relabel()


def relabel_done(key):
    """Every unmatched sense this candidate stands for has found its new label (a candidate accepted)."""
    return all(any(current_verdict(senses[k]) == "s" for k in unit) for unit in relabel_units_of[key])


def order_key(sense):
    return sense_ranking.order_key(sense, ranks)


ordered = sorted(senses.values(), key=order_key)
for group in senses_by_word.values():
    group.sort(key=order_key)
orders_by_tag = {}

# Countries (dexa), languages (basa) and the proper adjectives (su t) derived from them.
COUNTRY_TAGS = {"dexa": "country", "basa": "language"}
_COUNTRY_RE = re.compile(r"\b(country|nation|republic|kingdom|empire|emirate|principality|microstate|"
                         r"sultanate|federation|island country|archipelago)\b")
_LANGUAGE_RE = re.compile(r"\blanguages?\b")
_RELATING_RE = re.compile(r"\b(of|from|relating|pertaining|related|characteristic)\b")
_NOT_COUNTRY_RE = re.compile(r"\b(given name|surname|city|capital|town|river|province|county|"
                             r"state of the united states|u\.s\. state|porcelain|bird|ware|dish)\b")
# An ancient kingdom or a former state is not the modern country: no proposal, the vetter decides.
_HISTORICAL_RE = re.compile(r"\b(ancient|historical|former|formerly|obsolete|archaic|biblical)\b")
_PEOPLE_RE = re.compile(r"\b(people|person|inhabitants?|natives?|citizens?)\b")


def load_country_words():
    """{word (lowercase): 'country' | 'language' | 'country adjective' | 'language adjective'}.
    An adjective takes the kind of its base, the longest one it is built on (user 2026-11-28:
    Doycili 'pertaining to Germany' comes from Doyci, Doycisali 'pertaining to the German
    language' from Doycisa)."""
    kinds = {}
    for word, entry in glosses.items():
        tags = {t.strip() for t in (entry.get("Tags") or "").split(",")}
        for tag, kind in COUNTRY_TAGS.items():
            if tag in tags:
                kinds[word] = kind
    bases = dict(kinds)
    for word, entry in glosses.items():
        if (entry.get("WordClass") or "").strip() != "su t" or word in kinds:
            continue
        first = (entry.get("LexiliAsel") or "").split("+")[0].strip().lower()
        base = first if first in bases else max(
            (b for b in bases if len(b) >= 3 and word.startswith(b)), key=len, default=None)
        if base:
            kinds[word] = f"{bases[base]} adjective"
    return kinds


country_kinds = load_country_words()


def proposal(sense):
    """'s' / 'n' / None: the script's guess for a country, language or adjective sense."""
    kind = country_kinds.get(sense["word"].lower())
    label = f"{sense['label']} {sense['definition']}".lower()
    if kind == "country":
        if _NOT_COUNTRY_RE.search(label):
            return "n"
        if _HISTORICAL_RE.search(label):
            return None
        return "s" if _COUNTRY_RE.search(label) else None
    if kind == "language":
        if _LANGUAGE_RE.search(sense["label"].lower()):
            return "s"
        return "n" if _PEOPLE_RE.search(label) else None
    own = sense["label"].lower()
    if kind == "language adjective":       # Doycisali: of the German language
        if _LANGUAGE_RE.search(own):
            return "s"
        return "n" if _RELATING_RE.search(own) else None
    if kind == "country adjective":        # Doycili: of Germany, its people or culture
        if _LANGUAGE_RE.search(own) and not re.search(r"\b(country|people|culture|nation)\b", own):
            return "n"
        return "s" if _RELATING_RE.search(own) else None
    return None


country_order = sorted(
    (sn for word in country_kinds for sn in senses_by_word.get(word, ())),
    key=lambda sn: (["country", "language", "country adjective", "language adjective"].index(
                        country_kinds[sn["word"].lower()]),
                    sn["word"].lower(), {"s": 0, None: 1, "n": 2}[proposal(sn)], order_key(sn)))
print(f"  Countries, languages, adjectives: {len(country_kinds)} words, {len(country_order)} senses")


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
        writer.writerow(vetted_senses.COLUMNS + [OWNER, "When"])
        for key, entry in verdicts.items():
            sense = senses.get(key)
            for eng, pos, vt in entry.get("keys") or (sense["keys"] if sense else ()):
                writer.writerow([entry["word"], "en", eng, pos, vt, entry["label"], "", "",
                                 vetted_senses.entry_score(entry), entry["when"]])
    print(f"Wrote {len(verdicts)} scores of {OWNER} to {EXPORT_FILE}")
    sys.exit()

verdicts, undo_stack = load_verdicts()


def wikt_field(sense):
    """{"wikt": "es"} for a log entry of a pivot sense (vetted_senses reads it as the Source)."""
    return {"wikt": sense["wikt"]} if sense.get("wikt") else {}


_pivot_dbs, pivot_cache = {}, {}
_POS_PREFIX = re.compile(r"^[a-z][a-z./ -]*(?:\([^)]*\))?\s*:\s*")
# Parts of speech tried for a pivot term: every one the English side uses, plus the usual others.
_PIVOT_POS = list(dict.fromkeys(list(GLOSSPOS_TO_WIKT.values()) + [
    "noun", "name", "verb", "adj", "adv", "pron", "det", "num", "prep", "conj", "intj",
    "particle", "article", "phrase", "prefix", "suffix", "contraction"]))


def pivot_db(wikt):
    if wikt not in _pivot_dbs:
        path = WIKTIONARY_SOURCES.get(wikt, {}).get("lmdb_dir", "")
        _pivot_dbs[wikt] = WiktionaryDB(path=path, readonly=True) if path and os.path.exists(path) else None
    return _pivot_dbs[wikt]


def pivot_note(wikt, word):
    if wikt not in PIVOT_WIKTS:
        return f"Unknown pivot {wikt!r}"
    if pivot_db(wikt) is None:
        path = WIKTIONARY_SOURCES.get(wikt, {}).get("lmdb_dir", f"WiktionaryLMDB_{wikt}")
        return (f"No {path}: build it with  python \"JSONL parser non-English.py\" {wikt}  "
                f"(the {PIVOT_NAMES[wikt]} Wiktionary dump from kaikki.org)")
    if not word.strip():
        return f"Type one word to look up its {PIVOT_NAMES[wikt]} glosses in the {PIVOT_NAMES[wikt]} Wiktionary"
    if word.strip().lower() not in glosses:
        return f"{word} is not in the word list"
    if not pivot_senses(word, wikt):
        terms = ", ".join(t for t, _ in pivot_terms(word, wikt)) or "none"
        return f"The {PIVOT_NAMES[wikt]} Wiktionary has no translation table for {terms}"
    return ""


def pivot_terms(word, wikt):
    """[(term, segment)] of the word's gloss in that language: segments split on ';', the
    part-of-speech prefix dropped ('pron (femenino): ellas, las' -> ellas, las), commas outside
    parentheses, italic notes stripped, '(...)' context expanded like the English glosses."""
    entry = glosses.get(word.strip().lower(), {})
    found = []
    for segment in text(entry.get(PIVOT_COLUMNS[wikt])).split(";"):
        body = _POS_PREFIX.sub("", segment.strip())
        for part in sense_rows._split_top_commas(body):
            stripped, _ = extract_italic_annotation(part.strip())
            for term in _expand_gloss_context(stripped) if stripped else ():
                if term and (term, segment.strip()) not in found:
                    found.append((term, segment.strip()))
    return found


def _gloss_words(entry, lang):
    words = set()
    for segment in text(entry.get(GLOSS_COLUMNS.get(lang, ""))).split(";"):
        for part in sense_rows._split_top_commas(_POS_PREFIX.sub("", segment.strip())):
            stripped, _ = extract_italic_annotation(part.strip())
            words |= {w.lower() for w in _expand_gloss_context(stripped)} if stripped else set()
    return words


def pivot_senses(word, wikt):
    """The pivot cards of one word: every table of the word's {wikt} glosses in that Wiktionary,
    built once and added to the senses (so scores, undo and the tally treat them as any other)."""
    word = word.strip()
    entry = glosses.get(word.lower())
    if entry is None or wikt not in PIVOT_WIKTS:
        return []
    cache_key = (wikt, word.lower())
    if cache_key in pivot_cache:
        return pivot_cache[cache_key]
    db = pivot_db(wikt)
    if db is None:
        return []
    glb = entry["Word"].strip()
    # The word's own parts of speech (its English glosses) and their fallbacks: a table of
    # another part of speech is still shown, labelled.
    own_pos = set()
    for wpos, _, _ in pos_groups(text(entry.get("TranslationEng")), text(entry.get("WordClass"))):
        own_pos |= {wpos, *WIKT_POS_FALLBACKS.get(wpos, ()), *WIKT_POS_SINGLE_FALLBACKS.get(wpos, ())}
    own_words = {lang: _gloss_words(entry, lang) for lang in GLOSS_COLUMNS}
    built = []
    for term, segment in pivot_terms(word, wikt):
        for pos in _PIVOT_POS:
            tables = db.get_translations(term, pos)
            if not tables:
                continue
            sense_list = db.get_senses(term, pos) or []
            for label, by_lang in tables.items():
                if not label:
                    continue    # an untitled table names no sense to vet
                key = sense_id(wikt, glb, label)
                if key in senses and senses[key] in built:
                    if [term, pos, ""] not in senses[key]["keys"]:
                        senses[key]["keys"].append([term, pos, ""])
                    continue
                translations, why = [], [("pivot", f"{PIVOT_NAMES[wikt]} Wiktionary: {term}")]
                for lang in PIVOT_SHOWN[wikt]:
                    terms = sorted({t.word for t in by_lang.get(lang, ())})
                    if not terms:
                        continue
                    hits = own_words.get(lang, set())
                    marked = [{"t": t, "hit": t.lower() in hits} for t in terms]
                    hit = any(m["hit"] for m in marked)
                    translations.append({"lang": lang.capitalize(), "terms": marked, "hit": hit})
                    if hit:
                        why.append(("good", f"{lang.capitalize()} matches"))
                if pos not in own_pos:
                    why.append(("bad", f"(fallback: {pos}, not a part of speech of {glb})"))
                example = next((ex.text for sn in sense_list if label in sn.glosses for ex in sn.examples), "")
                sense = senses.get(key) or {
                    "id": key, "word": glb, "label": label, "eng": term, "pos": pos, "gloss_pos": pos,
                    "definition": label, "example": example, "clarification": segment,
                    "keys": [], "tier": "", "app": "", "score": 0, "why": why,
                    "translations": translations, "wikt": wikt}
                if [term, pos, ""] not in sense["keys"]:
                    sense["keys"].append([term, pos, ""])
                senses[key] = sense
                built.append(sense)
    pivot_cache[cache_key] = built
    return built


# Pivot senses scored before (this page's log): rebuilt at start, so undo and the tally know them.
for _word, _wikt in {(v["word"], v["wikt"]) for v in verdicts.values() if v.get("wikt")}:
    pivot_senses(_word, _wikt)


def owner_score(sense):
    """The owner's score: this page's latest, else the sheet's (vetted_senses.tsv)."""
    logged = logged_score(verdicts, sense["id"])
    return logged if logged is not None or sense["id"] in verdicts else base_scores.get(sense["id"], {}).get(OWNER)


def all_scores(sense):
    scores = {v: s for v, s in base_scores.get(sense["id"], {}).items() if v != OWNER}
    mine = owner_score(sense)
    if mine is not None:
        scores[OWNER] = mine
    return scores


def decision(sense):
    """'s'/'n' decided, '' undecided, None unscored; an expert's Tier e decides outright."""
    if sense["tier"] == "e":
        return "s" if sense["app"] == "s" else "n"
    return vetted_senses.decide(all_scores(sense))


def mark_class(score):
    return "" if score is None else "s" if score >= 4 else "n" if score <= 2 else "u"


def sheet_verdict(sense):
    """The mark of the sheet's scores alone (vetted_senses.tsv), as the page shows it."""
    mine = base_scores.get(sense["id"], {}).get(OWNER)
    if mine is not None:
        return mark_class(mine)
    decided = vetted_senses.decide(base_scores.get(sense["id"], {}))
    return decided if decided in ("s", "n") else ""


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
        "verdict": current_verdict(sense), "mine": owner_score(sense), "owner": OWNER,
        "others": {v: s for v, s in all_scores(sense).items() if v != OWNER},
        "mean": vetted_senses.mean(all_scores(sense)), "undecided": decision(sense) == "",
        "word_marked": word_is_marked(word, sense["gloss_pos"]), "gloss_pos": sense["gloss_pos"],
        "other_count": 0 if sense.get("wikt") else len(senses_by_word[word]) - 1,
        "wikt": sense.get("wikt", ""),
        "tags": word_tags(word),
        "proposal": proposal(sense),
        "queue": (queue_evidence.get(sense["id"], [])[:QUEUE_EVIDENCE]
                  + relabel_evidence.get(sense["id"], [])),
    }


def current_verdict(sense):
    """The card's mark: the owner's own score (4-5 s, 3 u, 1-2 n), else what the others' scores
    decided (s or n). Non-empty exactly when is_vetted(), so the page can mirror the listing."""
    mine = owner_score(sense)
    if mine is not None:
        return mark_class(mine)
    decided = decision(sense)
    return decided if decided in ("s", "n") else ""


def peek(word):
    """Every sense of a word for comparing before deciding: those accepted first, then the
    unjudged most obvious first, then the rejected (sense_ranking.judged_key, current scores)."""
    group = sorted(senses_by_word[word.strip().lower()],
                   key=lambda s: (s["gloss_pos"], sense_ranking.judged_key(all_scores(s)), order_key(s)))
    return [{"id": s["id"], "label": s["label"], "definition": s["definition"], "pos": s["pos"], "eng": s["eng"],
             "verdict": current_verdict(s), "mine": owner_score(s), "mean": vetted_senses.mean(all_scores(s)),
             "undecided": decision(s) == "", "why": s["why"]} for s in group]


def tag_list():
    """Every tag with its English gloss, so a tag can be chosen without knowing the Globasa word."""
    listed = []
    for tag, words in tag_members.items():
        gloss = tag_gloss_terms.get(tag, [])
        listed.append({"tag": tag, "gloss": ", ".join(gloss[:2]), "words": len(words)})
    return sorted(listed, key=lambda t: t["tag"].lower())


def is_vetted(sense):
    """Scored by the owner, or decided by the scores (or an expert). Undecided senses stay to vet."""
    return sense["tier"] == "e" or owner_score(sense) is not None or decision(sense) in ("s", "n")


def word_is_marked(word, pos):
    """Whether the word is vetted in this part of speech (gloss_pos): any mark on any of its senses
    of that part of speech counts (applies, doesn't apply or unsure, from this page or the sheet).
    A word vetted as a noun still waits to be vetted as a verb."""
    return any(is_vetted(s) for s in senses_by_word[word] if s["gloss_pos"] == pos)


def is_unsure(sense):
    """The owner scored 3, or the vetters' scores leave it undecided."""
    return owner_score(sense) == 3 or (owner_score(sense) is None and decision(sense) == "")


def matching(scope, query, include_vetted=False, tag=""):
    query = query.strip().lower()
    if scope == "queue":
        source = [senses[key] for key in queue_order]
    elif scope == "relabel":
        source = [senses[key] for key in relabel_order]
    elif scope == "countries":
        source = country_order
    elif scope.startswith("pivot-"):
        source = pivot_senses(query, scope[len("pivot-"):]) if query else []
    else:
        source = tag_order(tag) if tag else ordered
    for sense in source:
        if scope == "unsure":
            if not is_unsure(sense):
                continue
        elif scope == "relabel" and not include_vetted and relabel_done(sense["id"]):
            continue    # its unmatched senses found their new labels
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
    global queue_order, queue_evidence, relabel_order, relabel_evidence, relabel_units_of
    result = {"extension": "", "bidix": {}, "pairs": {}, "lpp": None}
    # The owner's scores into the shared sheet first, so the other vetters see them.
    rebuild["step"] = "shared sheet"
    rebuild["log"].append("== shared sheet")
    try:
        result["sheet"] = vetted_senses.push_owner_scores()
    except Exception as e:  # the sheet is optional; the rebuild goes on
        result["sheet"] = f"not updated ({e})"
    rebuild["log"].append(result["sheet"])
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
    # The extension rewrote its unmatched list: senses carried over to a new label leave it.
    relabel_order, relabel_evidence, relabel_units_of = load_relabel()
    rebuild.update(running=False, ok=ok, step="", result=result,
                   finished=datetime.now().isoformat(timespec="seconds"))


WV_URL = os.environ.get("WV_URL", "http://127.0.0.1:5000")
WV_LMDB = "WordViewerLMDB"


def run_viewer_rebuild():
    """The extension, then the Word Viewer's cache; nothing else (bidixes, pairs, sheet)."""
    global relabel_order, relabel_evidence, relabel_units_of
    result = {"extension": "", "viewer": ""}
    ok, out = run_step("Wiktionary extension", [sys.executable, "-u", "Wiktionary extension builder.py"])
    result["extension"] = next((l.strip() for l in out if l.startswith("Wrote menalariExtension")), "")
    if ok:
        rebuild["step"] = "Word Viewer"
        rebuild["log"].append("== Word Viewer")
        import urllib.error
        import urllib.request
        # No proxy for the local viewer: through the HTTP proxy a local URL answered
        # "Bad Gateway", which read as "not running" and dropped a live cache (2026-11-28).
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(WV_URL.rstrip("/") + "/rebuild", timeout=900) as r:
                reply = json.loads(r.read() or b"{}")
            result["viewer"] = f"rebuilt in the running viewer ({reply.get('entries', '?')} words)"
        except urllib.error.HTTPError as e:
            # Something answered: never drop the cache under a running viewer.
            ok = False
            result["viewer"] = f"the viewer at {WV_URL} answered {e.code} {e.reason}; its cache is unchanged"
        except (urllib.error.URLError, OSError) as e:
            if isinstance(getattr(e, "reason", e), ConnectionRefusedError) or isinstance(e, ConnectionRefusedError):
                import shutil
                shutil.rmtree(WV_LMDB, ignore_errors=True)
                result["viewer"] = (f"not running at {WV_URL}: its cache was dropped, "
                                    f"it rebuilds at its next start")
            else:
                ok = False
                result["viewer"] = f"could not reach the viewer at {WV_URL} ({getattr(e, 'reason', e)}); its cache is unchanged"
        rebuild["log"].append(result["viewer"])
    relabel_order, relabel_evidence, relabel_units_of = load_relabel()
    rebuild.update(running=False, ok=ok, step="", result=result,
                   finished=datetime.now().isoformat(timespec="seconds"))


def start_rebuild(target=None):
    target = target or run_rebuild
    with rebuild_lock:
        if rebuild["running"]:
            return False
        rebuild.update(running=True, ok=None, log=[], result=None, step="starting",
                       started=datetime.now().isoformat(timespec="seconds"), finished="")
    threading.Thread(target=target, daemon=True).start()
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
            scope = params.get("scope", ["all"])[0]
            note = pivot_note(scope[len("pivot-"):], params.get("q", [""])[0]) if scope.startswith("pivot-") else ""
            self.send_tally(rows=[card(s) for s in found[offset:offset + limit]], note=note, **view)
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
        tally = collections.Counter(mark_class(vetted_senses.entry_score(v)) for v in verdicts.values())
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
            {"id": key, "word": senses[key]["word"], "label": senses[key]["label"], "score": previous,
             "vetter": OWNER, "when": when, "batch": action["batch"], "undo": True, "keys": senses[key]["keys"],
             **wikt_field(senses[key])}
            for key, previous in reversed(action["changes"]) if key in senses
        ])
        self.send_changed(request, [key for key, _ in action["changes"] if key in senses])

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/rebuild":
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(length) or b"{}") if length else {}
            what = run_viewer_rebuild if body.get("what") == "viewer" else run_rebuild
            self.send_json({"started": start_rebuild(what), "running": True})
            return
        if path not in ("/api/undo", "/api/verdict"):
            self.send_error(404)
            return
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if path == "/api/undo":
            self.undo_last(request)
            return
        # A score 1-5, "clear", or an old verdict letter (y/n/m keys send s/n/u: 4/2/3).
        verdict = str(request.get("score", request.get("verdict")))
        if verdict == "clear":
            score = None
        elif verdict in vetted_senses.VERDICT_SCORES:
            score = vetted_senses.VERDICT_SCORES[verdict]
        elif verdict in ("1", "2", "3", "4", "5"):
            score = int(verdict)
        else:
            self.send_json({"error": "unknown score"}, 400)
            return
        when = datetime.now().isoformat(timespec="seconds")
        batch = f"{when}-{time.time_ns()}"
        keys = [key for key in request["ids"] if key in senses]
        if keys:
            undo_stack.append({"batch": batch, "changes": [
                (key, logged_score(verdicts, key)) for key in keys]})
        self.write_entries([
            {"id": key, "word": senses[key]["word"], "label": senses[key]["label"], "score": score,
             "vetter": OWNER, "when": when, "batch": batch, "keys": senses[key]["keys"],
             **wikt_field(senses[key])} for key in keys
        ])
        self.send_changed(request, keys)


print(f"Ready: open http://localhost:{PORT}  ({len(verdicts)} scores of {OWNER} loaded)")
ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
