"""Lute -> Anki: mark vocabulary cards by how Lute judges the word.

Reading in Lute (see lute_doxo_sync.py), every word you look up gets a status:
1-5 while you learn it, "well known" (99) or "ignored" (98). This script copies
those judgements onto the Anki notes of the same words (note type "Globasa lexi",
field Lexi) as tags, so Anki can be told to study what reading showed you
do not know yet:

    lute::1 .. lute::5, lute::known, lute::ignored   -- the Lute status
    lute::study                                       -- STUDY_STATUSES (1-4)

Study them with a filtered deck (Tools > Create Filtered Deck), search
    "note:Globasa lexi" tag:lute::study
which pulls in their new and due cards alike. Re-run after reading: tags follow
Lute's current statuses, and a word Lute no longer has loses its lute:: tags.

Anki must be running with the AnkiConnect add-on (code 2055492159), which
changes the open collection safely; Anki's own sync then carries the tags to
your other devices. Lute's database is only read (LuteGlobasa/data/lute.db, the
instance lute_doxo_sync.py sets up), so Lute may be running too.

Matching is exact: a Lute term marks the notes whose Lexi is that word (case and
surrounding spaces ignored; multi-word terms too, e.g. "fe ban mara"). A Lute
term with no vocabulary note is listed, never guessed at: derived words, names,
forms the deck spells differently.

    venv/bin/python lute_anki_marks.py
"""
import json
import os
import sqlite3
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
LUTE_DB = os.path.join(ROOT, "LuteGlobasa", "data", "lute.db")
LANGUAGE = "Globasa"
ANKICONNECT = "http://127.0.0.1:8765"
NOTETYPE = "Globasa lexi"
FIELD = "Lexi"
PREFIX = "lute::"
STATUS_TAGS = {1: "lute::1", 2: "lute::2", 3: "lute::3", 4: "lute::4", 5: "lute::5",
               99: "lute::known", 98: "lute::ignored"}
STUDY_TAG = "lute::study"
STUDY_STATUSES = {1, 2, 3, 4}   # still being learned in Lute
UNSUSPEND_STUDY = False         # True: also unsuspend the cards of study words
DRY_RUN = False                 # True: report the changes, make none
BATCH = 500


def lute_terms():
    """{word: status} of the language's terms, read-only."""
    con = sqlite3.connect(f"file:{LUTE_DB}?mode=ro", uri=True)
    try:
        row = con.execute("SELECT LgID FROM languages WHERE LgName = ?", (LANGUAGE,)).fetchone()
        if row is None:
            raise SystemExit(f"no {LANGUAGE} language in {LUTE_DB}: run lute_doxo_sync.py first")
        terms = {}
        for text, status in con.execute("SELECT WoTextLC, WoStatus FROM words WHERE WoLgID = ?", row):
            # Lute joins the words of a multi-word term with zero-width spaces.
            word = " ".join(text.replace("\u200b", "").split()).lower()
            if word:
                terms[word] = status
        return terms
    finally:
        con.close()


def anki(action, **params):
    body = json.dumps({"action": action, "version": 6, "params": params}).encode()
    req = urllib.request.Request(ANKICONNECT, body, {"Content-Type": "application/json"})
    # Straight to localhost: a system proxy must not see (or swallow) these calls.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=60) as r:
            reply = json.load(r)
    except OSError as e:
        raise SystemExit(f"AnkiConnect not reachable at {ANKICONNECT} ({e}). "
                         "Start Anki with the AnkiConnect add-on (code 2055492159).")
    if reply.get("error"):
        raise SystemExit(f"AnkiConnect {action}: {reply['error']}")
    return reply["result"]


def wanted_tags(status):
    tags = set()
    if status in STATUS_TAGS:
        tags.add(STATUS_TAGS[status])
    if status in STUDY_STATUSES:
        tags.add(STUDY_TAG)
    return tags


def main():
    terms = lute_terms()
    note_ids = anki("findNotes", query=f'"note:{NOTETYPE}"')
    notes = []
    for i in range(0, len(note_ids), BATCH):
        notes += anki("notesInfo", notes=note_ids[i:i + BATCH])

    to_add, to_remove = {}, {}          # tag -> [note ids]
    matched, by_status = set(), {}
    for n in notes:
        word = " ".join(n["fields"].get(FIELD, {}).get("value", "").split()).lower()
        status = terms.get(word)
        want = wanted_tags(status) if status is not None else set()
        have = {t for t in n["tags"] if t.lower().startswith(PREFIX)}
        have_lc = {t.lower() for t in have}
        for t in want:
            if t not in have_lc:
                to_add.setdefault(t, []).append(n["noteId"])
        for t in have:
            if t.lower() not in want:
                to_remove.setdefault(t, []).append(n["noteId"])
        if status is not None:
            matched.add(word)
            by_status[status] = by_status.get(status, 0) + 1

    unmatched = sorted(w for w in terms if w not in matched)
    print(f"Lute: {len(terms)} {LANGUAGE} terms; Anki: {len(notes)} '{NOTETYPE}' notes, "
          f"{sum(by_status.values())} of them match a Lute term")
    for status in sorted(by_status):
        print(f"  {STATUS_TAGS.get(status, f'status {status}'):14} {by_status[status]:5} note(s)"
              + ("   -> lute::study" if status in STUDY_STATUSES else ""))
    adds = sum(len(v) for v in to_add.values())
    removes = sum(len(v) for v in to_remove.values())
    print(f"tags to add: {adds}, to remove: {removes}" + ("  (dry run: nothing changed)" if DRY_RUN else ""))
    if not DRY_RUN:
        for tag, ids in to_remove.items():
            anki("removeTags", notes=ids, tags=tag)
        for tag, ids in to_add.items():
            anki("addTags", notes=ids, tags=tag)
        if UNSUSPEND_STUDY:
            cards = anki("findCards", query=f'"note:{NOTETYPE}" tag:{STUDY_TAG} is:suspended')
            if cards:
                anki("unsuspend", cards=cards)
            print(f"unsuspended {len(cards)} card(s) of study words")
    if unmatched:
        print(f"\n{len(unmatched)} Lute term(s) with no '{NOTETYPE}' note (left alone):")
        print("  " + ", ".join(unmatched[:60]) + (" ..." if len(unmatched) > 60 else ""))
    print(f'\nStudy them: a filtered deck searching  "note:{NOTETYPE}" tag:{STUDY_TAG}')


main()
