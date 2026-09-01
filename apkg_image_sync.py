"""Pull image links out of the live Anki deck into menalariImages.jsonl.

You curate images in Anki; this carries them back into the store, which is the
source of truth for everything else (Word Viewer's gallery, AnkiMaker3's export,
extra senses and images 3+ that the two card slots cannot hold).

Every URL is converted to its canonical Commons file title on the way in, so the
store never inherits a thumbnail URL that can rot. New entries land as
`status: "unresolved"`; run `resolve_commons_images.py` afterwards to fill in a
working `direct_url`.

Slot mapping is `images_store.anki_slots` inverted:
    Imajelinku     -> PoS group 1
    DuayumImaje    -> PoS group 2
    Faleanimalinku -> the animation for the word
A second still on a word with only one PoS group has nowhere to go, so it is
appended as a new sense with an empty `pos` and listed in the run report for you
to assign.

This script no longer HTTP-checks anything: the MediaWiki API tells us
authoritatively whether a file exists, in 50-title batches, which is what
`resolve_commons_images.py` uses. Checking ~1800 URLs against a rate-limiting
CDN was both slower and less reliable.
"""
import csv
import os
import shutil
import sqlite3
import subprocess
import tempfile
import zipfile

import images_store as S

APKG_PATH = "Globasa__Vocabulary.apkg"
REPORT = "apkg_image_sync_report.tsv"

# (url field, source field, which slot it maps back to)
SLOTS = [("Imajelinku", "ImajeAsel", 0),
         ("DuayumImaje", "DuayumImajeAsel", 1),
         ("Faleanimalinku", "Faleanimaasel", "gif")]

FIELD_NAMES = {n for pair in SLOTS for n in pair[:2]} | {"Lexi"}


def open_apkg(apkg_path):
    """Extract an .apkg, returning (sqlite path, tempdir to clean up)."""
    tmp = tempfile.mkdtemp(prefix="apkg_sync_")
    with zipfile.ZipFile(apkg_path) as z:
        z.extractall(tmp)
    src = os.path.join(tmp, "collection.anki21b")
    db = os.path.join(tmp, "collection.anki21")
    if os.path.exists(src):
        r = subprocess.run(["zstd", "-d", src, "-o", db, "-f"], capture_output=True)
        if r.returncode != 0:
            raise RuntimeError(f"zstd failed: {r.stderr.decode()}")
    else:
        db = os.path.join(tmp, "collection.anki2")
        if not os.path.exists(db):
            raise RuntimeError("no collection.anki21b or collection.anki2 in apkg")
    return db, tmp


def extract_apkg_images(apkg_path):
    """{lexi: {slot: (url, source_page)}} from the deck.

    Field ordinals come from the deck's own `fields` table BY NAME. They used to
    be hardcoded (img=14, src=15, gif=19) and silently drifted: after the v3
    verb-type fields were added, ordinal 14 is `IntransitiveCu` and the image
    fields moved to 19/20/24/25, so the sync had been reading the wrong columns.
    """
    db, tmp = open_apkg(apkg_path)
    try:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        cur = conn.cursor()

        ords = {}
        cur.execute("SELECT ntid, name, ord FROM fields")
        for ntid, name, ord_ in cur.fetchall():
            if name in FIELD_NAMES:
                ords.setdefault(ntid, {})[name] = ord_
        image_nts = {n: m for n, m in ords.items() if "Lexi" in m and len(m) > 1}
        if not image_nts:
            raise RuntimeError("no notetype with Lexi + image fields found")

        rows = {}
        cur.execute("SELECT mid, flds FROM notes")
        for mid, flds in cur.fetchall():
            fmap = image_nts.get(mid)
            if not fmap:
                continue
            parts = flds.split("\x1f")

            def get(name):
                i = fmap.get(name)
                return parts[i].strip() if i is not None and i < len(parts) else ""

            lexi = get("Lexi")
            if not lexi:
                continue
            for url_field, src_field, slot in SLOTS:
                url = get(url_field)
                if url:
                    rows.setdefault(lexi, {})[slot] = (url, get(src_field))
        conn.close()
        return rows, image_nts
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def target_sense(rec, slot):
    """The sense a deck slot maps back onto, or None if there is nowhere to put
    it (a second still on a word with only one PoS group)."""
    groups = S.pos_groups(rec)
    if slot == "gif":
        return groups[0][1][0] if groups else None
    if slot < len(groups):
        return groups[slot][1][0]
    return None


# ---------- run ----------

print(f"reading {APKG_PATH} ...")
apkg, notetypes = extract_apkg_images(APKG_PATH)
print(f"  {len(notetypes)} notetype(s) with image fields; "
      f"{len(apkg)} words carrying images")
for ntid, fmap in notetypes.items():
    named = ", ".join(f"{n}={o}" for n, o in sorted(fmap.items(), key=lambda kv: kv[1]))
    print(f"    ntid {ntid}: {named}")

store = S.load_images()
print(f"{len(store)} words in {S.IMAGES_JSONL}")

added_word = added_image = unchanged = 0
orphaned = []

for lexi in sorted(apkg):
    rec = store.get(lexi)
    if rec is None:
        rec = {"word": lexi, "senses": [S.make_sense()]}
        store[lexi] = rec
        added_word += 1
    if not rec["senses"]:
        rec["senses"] = [S.make_sense()]

    have = set()
    for existing in S.all_images(rec):
        have |= S.image_keys(existing)
    for _url_field, _src_field, slot in SLOTS:
        entry = apkg[lexi].get(slot)
        if not entry:
            continue
        url, src_page = entry
        parsed = S.parse_commons_url(url)
        if parsed:
            wiki, file = parsed
            img = S.make_image(file=file, wiki=wiki, src_page=src_page or None)
        else:
            img = S.make_image(url=url, src_page=src_page or None)

        if S.image_key(img) in have:
            unchanged += 1
            continue

        sense = target_sense(rec, slot)
        if sense is None:
            sense = S.make_sense()
            rec["senses"].append(sense)
            orphaned.append((lexi, url))
        sense.setdefault("images", []).append(img)
        have.add(S.image_key(img))
        added_image += 1

S.save_images(store)

with open(REPORT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["word", "url", "note"])
    for word, url in orphaned:
        w.writerow([word, url, "no PoS group for this slot; added as a new unassigned sense"])

print()
print(f"new words {added_word}   new images {added_image}   already present {unchanged}")
if orphaned:
    print(f"{len(orphaned)} image(s) had no PoS group to land on -> {REPORT}")
    print("  assign a `pos` to those senses, then re-run")
if added_image:
    print("\nrun resolve_commons_images.py to fill direct_url for the new entries")
