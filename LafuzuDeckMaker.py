"""Globasa__Lafuzu.apkg: match written and spoken Globasa with Hector's own
recordings from the course (xwexi).

Each note pairs a written form with its recording. Two card types, each in its
own subdeck:
  Written -> Spoken   the text; say it, then hear Hector.
  Spoken -> Written   the recording; write or picture the text. Optional: made
                      only when the SpokenToWritten field is non-empty, which
                      SPOKEN_TO_WRITTEN sets for every note (blank it on a note
                      in Anki to drop just that card).

Sources, in course order (the first source of a text wins; a later recording
of the same text is kept as an alternative):
  1. Lessons: the word-list clips cut from darsu_NN_lexilista.mp3 into CLIPS_DIR
     (lessons 1-7 by hand; later lessons via lesson_audio_labels.py + Audacity),
     plus clips of headwords Hector reads from the lesson text.
     Lessons in xwexi_lessons.SYNTHESIZED_LESSONS (17) are a synthesized voice.
     Their notes are kept apart: never merged with Hector's recording of the
     same text (barix has both), tagged "synthesized", marked so on the card,
     and filed under Globasa::Lafuzu::Synthesized::<card type>.
  2. Common Phrases and Expressions (04.pimpan-logaxey): one mp3 per phrase.
  3. Alphabet and Pronunciation (03.gramati/01.abece-ji-lafuzu): the example
     words, and the pronunciation section with its permitted variants ("asif
     [a'sif] or [a'sifa]") -- the first is the recording, the rest alternatives.
     Its .ogg/.wav files are Wikimedia IPA samples, not Hector, and are skipped.

A recording is used only when its filename spells exactly the text it sits
beside; anything else (placeholders like "Mi sen lao fe... nyan.") is reported
and left out, since a card pairing text with the wrong audio teaches the wrong
thing.

Re-running updates the package in place: notes keep their GUIDs (derived from
the text), so a learner's re-import keeps their progress.
"""
import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import unicodedata
import zipfile

import pandas as pd
from anki.collection import Collection, ExportAnkiPackageOptions
from anki import import_export_pb2 as pb
from anki.generic_pb2 import Empty

from xwexi_lessons import SYNTHESIZED_LESSONS, clip_name, lesson_entries, spoken_forms

APKG = "Globasa__Lafuzu.apkg"
DECK = "Globasa::Lafuzu"
NOTETYPE = "Globasa lafuzu"
XWEXI = "xwexi-pages-grav"
CLIPS_DIR = "/media/paleos/Warehouse2/Applications/Segmentation/Ektor_su_Lafuzu_processed"
SPOKEN_TO_WRITTEN = True
SYNTH_DECK = f"{DECK}::Synthesized"
SYNTH_TAG = "synthesized"
SYNTH_NOTE = "synthesized voice, not Hector"

FIELDS = ["Globasa", "Basatayti", "Lafuzu", "AloLafuzu", "Asel", "SpokenToWritten"]

CSS = """.card { font-family: arial; font-size: 20px; line-height: 1.5; text-align: center; }
.lexi { font-family: Open Sans; font-size: 30px; }
.mena { font-family: Libre Baskerville; font-size: 20px; }
.alo, .asel { font-size: 15px; color: grey; }"""

WRITTEN_FRONT = """<div class= "lexi"><h2>{{Globasa}}</h2></div>"""
WRITTEN_BACK = """{{FrontSide}}
<hr id=answer>
{{Lafuzu}}
<div class= "mena">{{Basatayti}}</div>
{{#AloLafuzu}}<div class= "alo">{{AloLafuzu}}</div>{{/AloLafuzu}}
<div class= "asel">{{Asel}}</div>"""
SPOKEN_FRONT = """{{#SpokenToWritten}}
{{Lafuzu}}
<div class= "lexi"><h2>?</h2></div>
{{/SpokenToWritten}}"""
SPOKEN_BACK = """{{Lafuzu}}
<hr id=answer>
<div class= "lexi"><h2>{{Globasa}}</h2></div>
<div class= "mena">{{Basatayti}}</div>
<div class= "asel">{{Asel}}</div>"""
TEMPLATES = [("Written → Spoken", WRITTEN_FRONT, WRITTEN_BACK),
             ("Spoken → Written", SPOKEN_FRONT, SPOKEN_BACK)]


def spelling(text):
    """What a recording's filename and its text must agree on: letters only."""
    return re.sub(r"[^a-z]", "", unicodedata.normalize("NFKD", text.lower()))


def md(text):
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    return re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"<i>\1</i>", text).strip()


# ---------- sources: (text, gloss, [(audio path, label)], asel) ----------

def lesson_items():
    """Clips cut from the lesson recordings. A list entry's clip is named by
    what Hector says (kenumer_te, pala for "pala (yon/in)"); a clip no list
    explains -- he also reads forms from the lesson text, fe_ban_mara in lesson
    18 -- is kept when it names a headword, with the lexicon's gloss."""
    items = []
    if not os.path.isdir(CLIPS_DIR):
        print(f"{CLIPS_DIR} not mounted: no lesson recordings")
        return items
    clips = {f.rsplit(".", 1)[0]: f for f in os.listdir(CLIPS_DIR)}
    # A synthesized lesson's clips share the folder with Hector's, named the
    # same way; they are told apart only by which lesson lists the word.
    used = set()
    for n in range(1, 21):
        asel = f"Lesson {n} — {SYNTH_NOTE}" if n in SYNTHESIZED_LESSONS else f"Lesson {n}"
        for entry, gloss in lesson_entries(n):
            for spoken in spoken_forms(entry):
                name = clip_name(spoken)
                if name in clips:
                    used.add(name)
                    items.append((spoken, md(gloss),
                                  [(f"{CLIPS_DIR}/{clips[name]}", "")], asel))
                    break
    lexicon = pd.read_csv("word-list.csv", index_col=0, dtype=str).fillna("")
    lexicon.index = lexicon.index.astype(str).str.strip()
    by_clip = {clip_name(f): (f, w) for w in lexicon.index for f in spoken_forms(w)}
    for name in sorted(set(clips) - used):
        if name in by_clip:
            spoken, word = by_clip[name]
            gloss = lexicon.loc[word, "TranslationEng"]
            gloss = gloss.iloc[0] if isinstance(gloss, pd.Series) else gloss
            items.append((spoken, md(gloss), [(f"{CLIPS_DIR}/{clips[name]}", "")],
                          "Lesson recordings"))
        else:
            print(f"clip {clips[name]} names no lesson entry or headword: left out")
    return items


def phrase_items(skipped):
    path = f"{XWEXI}/04.pimpan-logaxey/default.eng.md"
    items, recent = [], []
    for line in open(path, encoding="utf-8").read().splitlines():
        bolds = re.findall(r"\*\*(.+?)\*\*", line)
        if bolds and "<" not in line:
            gloss = line.split(" - ", 1)[1] if " - " in line else ""
            recent = (recent + [[bolds, gloss]])[-3:]
        elif recent and not recent[-1][1] and line.strip() and "<" not in line:
            # Later sections gloss on the next line: "**Yukwe.**" / "It's
            # pleasant."
            recent[-1][1] = line.strip()
        a = re.search(r'src="[^"]*/([^"/]+\.mp3)"', line)
        if not a:
            continue
        name = a.group(1)
        want = spelling(name.rsplit(".", 1)[0])
        hit = next(((b, g, k, len(bs)) for bs, g in reversed(recent)
                    for k, b in enumerate(bs) if spelling(b) == want), None)
        if hit is None:
            skipped.append(f"Common Phrases: {name}")
            continue
        text = hit[0].replace("(", "").replace(")", "")
        gloss = hit[1] or next((g for _, g in reversed(recent) if g), "")
        # "**(To sen) yukwe, ...** _or_ **Yukwe.**" glossed "It's nice meeting
        # you. or It's pleasant.": each form takes its own half.
        halves = gloss.split(" or ")
        if len(halves) == hit[3] > 1:
            gloss = halves[hit[2]]
        items.append((text, md(gloss), [(f"{XWEXI}/04.pimpan-logaxey/{name}", "")],
                      "Common Phrases and Expressions"))
    return items


def alphabet_items(skipped):
    folder = f"{XWEXI}/03.gramati/01.abece-ji-lafuzu"
    page = open(f"{folder}/default.eng.md", encoding="utf-8").read()
    items = []
    for word, name, gloss in re.findall(
            r"\[\*\*(.+?)\*\*\]\(([^)\s]+\.mp3)\)\s*([^|\n]*)", page):
        items.append((word, md(gloss), [(f"{folder}/{name}", "")],
                      "Alphabet and Pronunciation"))
    for line in page.splitlines():
        m = re.match(r"\*\*_?([^*]+?)_?\*\*\s*(?:\(([^)]*)\))?,?\s*pronounced(.*)", line)
        if not m:
            continue
        audio = re.findall(r"\[((?:\[[^\]]*\]/?)+)\]\(([^)\s]+\.mp3)\)", m.group(3))
        if not audio:
            continue
        if spelling(audio[0][1].rsplit(".", 1)[0]) != spelling(m.group(1)):
            skipped.append(f"Alphabet: {audio[0][1]} beside {m.group(1)!r}")
            continue
        items.append((m.group(1).strip(), md(m.group(2) or ""),
                      [(f"{folder}/{f}", ipa) for ipa, f in audio],
                      "Alphabet and Pronunciation"))
    return items


# ---------- package ----------

def unpack(apkg, workdir):
    with zipfile.ZipFile(apkg) as z:
        z.extractall(workdir)
    packed = os.path.join(workdir, "collection.anki21b")
    db = os.path.join(workdir, "collection.anki2")
    if os.path.exists(packed):
        r = subprocess.run(["zstd", "-d", packed, "-o", db, "-f"], capture_output=True)
        if r.returncode != 0:
            raise RuntimeError(f"zstd failed: {r.stderr.decode()}")
        os.remove(packed)
    return db


def ensure_notetype(col):
    mm = col.models
    nt = mm.by_name(NOTETYPE)
    if nt is None:
        nt = mm.new(NOTETYPE)
        for name in FIELDS:
            mm.add_field(nt, mm.new_field(name))
        for name, front, back in TEMPLATES:
            t = mm.new_template(name)
            t["qfmt"], t["afmt"] = front, back
            mm.add_template(nt, t)
        nt["css"] = CSS
        mm.add(nt)
        nt = mm.by_name(NOTETYPE)
    for t in nt["tmpls"]:
        t["did"] = col.decks.id(f"{DECK}::{t['name']}", create=True)
    mm.update_dict(nt)
    return mm.by_name(NOTETYPE)


def sound(col, path, prefix):
    """Copy a recording into the collection under a source-prefixed name (two
    sources both have a doste.mp3) and return its [sound:] tag."""
    name = f"lafuzu_{prefix}_{os.path.basename(path)}".replace(" ", "_")
    target = os.path.join(col.media.dir(), name)
    if not os.path.exists(target):
        shutil.copyfile(path, target)
    return f"[sound:{name}]"


skipped = []
sources = lesson_items() + phrase_items(skipped) + alphabet_items(skipped)

workdir = tempfile.mkdtemp(prefix="lafuzu_")
db = unpack(APKG, workdir) if os.path.exists(APKG) else os.path.join(workdir, "collection.anki2")
col = Collection(db)
nt = ensure_notetype(col)
deck_id = col.decks.id(DECK, create=True)
existing = {col.get_note(nid).guid: nid for nid in col.find_notes(f'"note:{NOTETYPE}"')}

notes = {}   # spelling -> field values, in source order
for text, gloss, audio, asel in sources:
    synthetic = asel.endswith(SYNTH_NOTE)
    prefix = {"Common Phrases and Expressions": "logaxey",
              "Alphabet and Pronunciation": "abece"}.get(asel, "synth" if synthetic else "darsu")
    tags = [sound(col, p, prefix) for p, _ in audio]
    # A synthesized recording gets a note of its own, so no card ever plays it
    # as one of Hector's alternatives.
    key = ("synth:" if synthetic else "") + spelling(text)
    if key not in notes:
        notes[key] = {"Globasa": text, "Basatayti": gloss, "Lafuzu": tags[0],
                      "AloLafuzu": [f"{ipa} {t}".strip() for (_, ipa), t
                                    in zip(audio[1:], tags[1:])],
                      "Asel": asel,
                      "SpokenToWritten": "y" if SPOKEN_TO_WRITTEN else ""}
    else:
        # "bonaxam" beside "bon axam": label the recording with its own
        # spelling; a second recording of the same spelling, with its source.
        label = text if text != notes[key]["Globasa"] else asel
        have = notes[key]["Lafuzu"] + " ".join(notes[key]["AloLafuzu"])
        notes[key]["AloLafuzu"] += [f"{ipa or label} {t}" for (_, ipa), t
                                    in zip(audio, tags) if t not in have]
        notes[key]["Basatayti"] = notes[key]["Basatayti"] or gloss

added = updated = 0
for key, values in notes.items():
    values = dict(values, AloLafuzu=" · ".join(values["AloLafuzu"]))
    tags = [SYNTH_TAG] if key.startswith("synth:") else []
    guid = "glb-lafuzu-" + hashlib.sha1(key.encode()).hexdigest()[:12]
    if guid in existing:
        note = col.get_note(existing[guid])
        if [note[f] for f in FIELDS] != [values[f] for f in FIELDS] or \
                {t.lower() for t in note.tags} != set(tags):
            for f in FIELDS:
                note[f] = values[f]
            note.tags = tags
            col.update_note(note)
            updated += 1
    else:
        note = col.new_note(nt)
        note.guid = guid
        for f in FIELDS:
            note[f] = values[f]
        note.tags = tags
        col.add_note(note, deck_id)
        added += 1

# File every card by card type, the synthesized ones in a branch of their own.
# Runs every time: cards an update generates ignore the template's deck
# override, and the override cannot tell a synthesized note from Hector's.
for t in nt["tmpls"]:
    synth_did = col.decks.id(f"{SYNTH_DECK}::{t['name']}", create=True)
    for did, query in ((t["did"], f"-tag:{SYNTH_TAG}"), (synth_did, f"tag:{SYNTH_TAG}")):
        stray = col.find_cards(f'"note:{NOTETYPE}" "card:{t["name"]}" {query} -did:{did}')
        if stray:
            col.set_deck(stray, did)

by_source = {}
for k, v in notes.items():
    src = "Synthesized" if k.startswith("synth:") else v["Asel"].split()[0]
    by_source[src] = by_source.get(src, 0) + 1
print(f"{len(notes)} notes ({added} new, {updated} updated): {by_source}")
print(f"cards: {col.card_count()}")
if skipped:
    print(f"\n{len(skipped)} recording(s) left out, text and filename disagree:")
    for s in skipped:
        print(f"  {s}")

col.export_anki_package(
    out_path=os.path.abspath(APKG),
    options=ExportAnkiPackageOptions(with_scheduling=False, with_deck_configs=True,
                                     with_media=True, legacy=False),
    limit=pb.ExportLimit(whole_collection=Empty()),
)
col.close()
shutil.rmtree(workdir, ignore_errors=True)
print(f"\nwrote {APKG}")
