"""Push the regenerated AnkiList.csv into Globasa__Vocabulary.apkg.

The deck is the distribution artefact, not the source of truth: glosses come
from word-list.csv through AnkiMaker3, images from menalariImages.jsonl. This
carries a fresh export back into the existing package rather than building a new
one, so the note type, its 31 templates, the styling and every note's GUID
survive. GUIDs are what let Anki match the re-import against a learner's
existing notes and keep their scheduling -- never regenerate them.

Anki's own library does the writing, so card generation follows the real
conditional-template rules: a word that gains an image gains its Imajeli
Rukone card, and one that loses its last image loses that card. Every card is
filed in a subdeck named after its card type (Globasa::Vocabulary::Produti...).

Fields are matched to columns BY NAME. The note type's ordinals have drifted
once already (see bug-184), and a silent off-by-one would write glosses into
image slots.
"""
import csv
import os
import shutil
import subprocess
import tempfile
import zipfile

from anki.collection import Collection, ExportAnkiPackageOptions
from anki import import_export_pb2 as pb
from anki.generic_pb2 import Empty

APKG = "Globasa__Vocabulary.apkg"
BACKUP = "Globasa__Vocabulary.apkg.bak"
EXPORT = "AnkiList.csv"
NOTETYPE = "Globasa lexi"
DECK = "Globasa::Vocabulary"

# Lexi is the key the update matches on, so it is never written back. The deck
# carries 24 notes whose Lexi has a trailing space -- twins of a clean note,
# left over from an import before word-list.csv indexes were stripped. Writing
# the trimmed form would silently turn each pair into two identical notes.
READ_ONLY_FIELDS = {"Lexi"}

# AnkiList.csv column order, as AnkiMaker3 writes it. Names must match the
# note type's fields exactly; the last column is tags, not a field.
COLUMNS = [
    "Lexi", "EnfasisdoLexi",
    "PoS1", "PoS2", "PoS3",
    "Mena1", "Mena2", "Mena3",
    "Animate Adjective", "Inanimate Adjective", "SlangMena",
    "Transitive", "EchoTransitive", "Intransitive", "IntransitiveCu",
    "Copula", "Auxiliary", "Feeling", "State",
    "VerbClass", "NoObjectForm",
    "Imajelinku", "ImajeAsel", "NSFW", "DuayumImaje", "DuayumImajeAsel",
    "Faleanimalinku", "Faleanimaasel",
    "Anaphor", "AloAnaphor", "AnaphorMena", "AloAnaphorMena",
    "AnaphorImaje", "AnaphorImajeAsel", "AloAnaphorImaje", "AloAnaphorImajeAsel",
    "Oposmenalexi",
    "GlobasaMisal", "MisalClozed", "MisalBasatayti",
    "FaleliMisal", "FaleliMisalClozed", "FaleliMisalBasatayti",
    "TigayumMisal", "TigayumMisalClozed", "TigayumMisalBasatayti",
    "Paladoawdio", "PaladoKodek",
    "Soti", "Sotiasel", "Sotikodek", "Sotilabel",
    "Maxpul Kostrui 1", "Maxpul Kostrui 1 Basatayti",
    "Maxpul Kostrui 2", "Maxpul Kostrui 2 Basatayti",
]
TAGS_COLUMN = len(COLUMNS)


def unpack(apkg, workdir):
    """An .apkg holds the collection zstd-compressed as collection.anki21b in
    current Anki, plain as collection.anki2 in older ones."""
    with zipfile.ZipFile(apkg) as z:
        z.extractall(workdir)
    packed = os.path.join(workdir, "collection.anki21b")
    db = os.path.join(workdir, "collection.anki2")
    if os.path.exists(packed):
        r = subprocess.run(["zstd", "-d", packed, "-o", db, "-f"],
                           capture_output=True)
        if r.returncode != 0:
            raise RuntimeError(f"zstd failed: {r.stderr.decode()}")
        os.remove(packed)
    if not os.path.exists(db):
        raise RuntimeError(f"no collection found in {apkg}")
    return db


def read_export(path):
    rows = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.reader(f, delimiter="\t"):
            if row and row[0]:
                rows[row[0]] = row
    return rows


export = read_export(EXPORT)
print(f"{EXPORT}: {len(export)} words")

workdir = tempfile.mkdtemp(prefix="vocab_update_")
db_path = unpack(APKG, workdir)
col = Collection(db_path)

notetype = col.models.by_name(NOTETYPE)
if notetype is None:
    raise SystemExit(f"note type {NOTETYPE!r} not in {APKG}")
ords = {f["name"]: f["ord"] for f in notetype["flds"]}
missing = [c for c in COLUMNS if c not in ords]
if missing:
    raise SystemExit(f"note type has no field(s): {missing}")
field_ords = [ords[c] for c in COLUMNS]

nids = col.find_notes(f'"note:{NOTETYPE}"')
print(f"{APKG}: {len(nids)} notes of type {NOTETYPE!r}")

updated = unchanged = 0
absent = []
changed_fields = {}
seen = {}
seen_raw = {}
duplicates = {}
cards_before = col.card_count()

for nid in nids:
    note = col.get_note(nid)
    lexi = note.fields[ords["Lexi"]].strip()
    raw = note.fields[ords["Lexi"]]
    if lexi in seen:
        duplicates.setdefault(lexi, [seen_raw[lexi]]).append(raw)
    else:
        seen[lexi] = nid
        seen_raw[lexi] = raw
    row = export.get(lexi)
    if row is None:
        absent.append(lexi)
        continue
    dirty = False
    for column, (name, ordinal) in enumerate(zip(COLUMNS, field_ords)):
        if name in READ_ONLY_FIELDS:
            continue
        value = row[column] if column < len(row) else ""
        if note.fields[ordinal] != value:
            note.fields[ordinal] = value
            changed_fields[name] = changed_fields.get(name, 0) + 1
            dirty = True
    tags = (row[TAGS_COLUMN] if len(row) > TAGS_COLUMN else "").split()
    # Anki stores tags in its own canonical order and treats them as a
    # case-insensitive set, so comparing the lists directly reports a change on
    # every run and needlessly re-stamps hundreds of notes.
    if {t.lower() for t in note.tags} != {t.lower() for t in tags}:
        note.tags = tags
        changed_fields["<tags>"] = changed_fields.get("<tags>", 0) + 1
        dirty = True
    if dirty:
        col.update_note(note)
        updated += 1
    else:
        unchanged += 1

print(f"\nupdated {updated} notes, {unchanged} already current, "
      f"{len(absent)} in the deck but not in the export")

print("\nfields written:")
for name, n in sorted(changed_fields.items(), key=lambda kv: -kv[1]):
    print(f"  {name:28s} {n}")

# Words the lexicon has gained since the deck was last built. New notes get a
# fresh GUID; every existing note keeps the one learners' scheduling hangs on.
deck_id = col.decks.id_for_name(DECK)
if deck_id is None:
    raise SystemExit(f"deck {DECK!r} not in {APKG}")

added = []
for lexi in sorted(set(export) - set(seen)):
    row = export[lexi]
    note = col.new_note(notetype)
    for column, (name, ordinal) in enumerate(zip(COLUMNS, field_ords)):
        note.fields[ordinal] = row[column] if column < len(row) else ""
    note.tags = (row[TAGS_COLUMN] if len(row) > TAGS_COLUMN else "").split()
    col.add_note(note, deck_id)
    added.append(lexi)
if added:
    print(f"\nadded {len(added)} new word(s) to {DECK}: {', '.join(added)}")

if duplicates:
    print(f"\n{len(duplicates)} word(s) have more than one note in the deck. "
          f"Only the first was updated; the rest are untouched so you can "
          f"decide whether to delete them in Anki:")
    for lexi, forms in sorted(duplicates.items()):
        print(f"  {' and '.join(repr(f) for f in forms)}")

if absent:
    print(f"\n{len(absent)} note(s) in the deck are not in the export "
          f"(prepositions live in their own deck, the rest are words the "
          f"lexicon has retired). Left untouched: "
          f"{', '.join(sorted(absent)[:10])}...")

# Anki generates the cards an edit calls for but never deletes one whose front
# the edit has emptied -- that waits for Tools > Empty Cards. Without this a
# word that loses its second pronoun or its last image keeps a blank card.
ours = set(nids)
empty = [cid for note in col.get_empty_cards().notes
         if not note.will_delete_note and note.note_id in ours
         for cid in note.card_ids]
if empty:
    col.remove_cards_and_orphaned_notes(empty)
    print(f"\nremoved {len(empty)} card(s) whose template the update left empty")

# One subdeck per card type, named after its template, so a learner can study
# or suspend a whole card type at once. The template's deck override sends cards
# generated later (a new word, a word gaining an image) straight there; the move
# below catches everything already in the package. Renaming a template in Anki
# moves its cards on the next run and drops the emptied subdeck.
notetype = col.models.get(notetype["id"])
subdecks = {}
for tmpl in notetype["tmpls"]:
    did = col.decks.id(f"{DECK}::{tmpl['name']}", create=True)
    subdecks[tmpl["ord"]] = did
    tmpl["did"] = did
col.models.update_dict(notetype)

moved = 0
for ordinal, did in subdecks.items():
    stray = col.find_cards(f'"note:{NOTETYPE}" card:{ordinal + 1} -did:{did}')
    if stray:
        col.set_deck(stray, did)
        moved += len(stray)
print(f"\nmoved {moved} card(s) into their card-type subdeck")

wanted = set(subdecks.values()) | {deck_id}
for d in col.decks.all_names_and_ids():
    if (d.name.startswith(DECK + "::") and d.id not in wanted
            and not col.find_cards(f"did:{d.id}")):
        col.decks.remove([d.id])
        print(f"removed empty subdeck {d.name!r}")

cards_after = col.card_count()
print(f"\ncards: {cards_before} -> {cards_after}")

# The export below drops scheduling. That is right for the distribution deck,
# but an .apkg exported from a study profile carries a learner's whole history
# (2026-10-25: 63k reviews), and only the backup would still hold it.
reviews = col.db.scalar("select count() from revlog")
if reviews:
    print(f"\nWARNING: {APKG} carries {reviews} reviews of study history. "
          f"The package written below has none; {BACKUP} keeps them.")

shutil.copyfile(APKG, BACKUP)
col.export_anki_package(
    out_path=os.path.abspath(APKG),
    options=ExportAnkiPackageOptions(
        with_scheduling=False,   # a distribution deck ships no review history
        with_deck_configs=True,
        with_media=True,
        legacy=False,
    ),
    limit=pb.ExportLimit(whole_collection=Empty()),
)
col.close()
shutil.rmtree(workdir, ignore_errors=True)
print(f"\nwrote {APKG} (previous kept as {BACKUP})")
