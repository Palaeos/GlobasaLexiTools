"""One-shot: build menalariImages.jsonl from the legacy single-image sources.

Reads the old `menalariImages_edited.csv` (TSV despite the name) *and* the live
Anki deck, converts every URL to a canonical Commons file title where possible,
and seeds one sense per word.

Idempotent and re-runnable: an existing JSONL is loaded first and merged into,
so hand-curated senses, labels and extra images are never clobbered. Images are
deduplicated on their canonical identity.

`pos` is assigned only where it is unambiguous — a word whose English gloss has
exactly one annotated segment provably has its image on that part of speech.
Words with two or more PoS groups are left with `"pos": ""` for a human to
assign; guessing which of two glosses an old single image illustrated is exactly
the judgement this migration must not make. Those words are printed as the
initial curation queue.
"""
import csv
import os
import shutil
import sqlite3
import subprocess
import tempfile
import zipfile

import images_store as S

TSV_PATH = "menalariImages_edited.csv"
APKG_PATH = "Globasa__Vocabulary.apkg"
WORDLIST = "word-list.csv"
OUT_PATH = S.IMAGES_JSONL
UNPARSED_REPORT = "images_migration_unparsed.tsv"
QUEUE_REPORT = "images_migration_queue.tsv"

# Anki fields we pull, in the order they should land in the seeded sense.
APKG_FIELDS = [("Imajelinku", "ImajeAsel"),
               ("DuayumImaje", "DuayumImajeAsel"),
               ("Faleanimalinku", "Faleanimaasel")]


def open_apkg(apkg_path):
    """Extract an .apkg and return (sqlite_path, tempdir). Modern decks ship the
    collection zstd-compressed as collection.anki21b."""
    tmp = tempfile.mkdtemp(prefix="images_migrate_")
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


def apkg_image_rows(apkg_path):
    """{lexi: [(url, source_page), ...]} pulled from the deck.

    Field ordinals are resolved from the deck's own `fields` table BY NAME. The
    previous hardcoded indices (img=14) silently pointed at `IntransitiveCu`
    after the v3 verb-type fields were added.
    """
    db, tmp = open_apkg(apkg_path)
    try:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        cur = conn.cursor()

        # ntid -> {field name: ord}, for every notetype carrying image fields.
        ords = {}
        cur.execute("SELECT ntid, name, ord FROM fields")
        for ntid, name, ord_ in cur.fetchall():
            ords.setdefault(ntid, {})[name] = ord_
        wanted = {n for pair in APKG_FIELDS for n in pair} | {"Lexi"}
        image_nts = {ntid: m for ntid, m in ords.items()
                     if "Lexi" in m and wanted & set(m)}

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
            for url_field, src_field in APKG_FIELDS:
                url = get(url_field)
                if url:
                    rows.setdefault(lexi, []).append((url, get(src_field)))
        conn.close()
        return rows
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def tsv_image_rows(path):
    """{word: [(url, source_page), ...]} from the legacy TSV."""
    rows = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader, None)  # header
        for row in reader:
            if len(row) > 2 and row[0].strip() and row[2].strip():
                src = row[3].strip() if len(row) > 3 else ""
                rows.setdefault(row[0].strip(), []).append((row[2].strip(), src))
    return rows


def load_pos_keys(path):
    """{word: [annotation key, ...]} from the word list."""
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            word = (row.get("Word") or "").strip()
            if word:
                out[word] = S.word_pos_keys(row.get("TranslationEng") or "")
    return out


def to_image(url, src_page, unparsed):
    """Canonical image record, or a literal-URL one for what can't be resolved."""
    parsed = S.parse_commons_url(url)
    if parsed:
        wiki, file = parsed
        return S.make_image(file=file, wiki=wiki, src_page=src_page or None)
    unparsed.append((url, src_page))
    return S.make_image(url=url, src_page=src_page or None)


# ---------- run ----------

print(f"loading {OUT_PATH} (merge target) ...")
store = S.load_images(OUT_PATH)
print(f"  {len(store)} existing records")

print(f"loading {TSV_PATH} ...")
sources = tsv_image_rows(TSV_PATH)
print(f"  {len(sources)} words with a URL")

print(f"loading {APKG_PATH} ...")
apkg = apkg_image_rows(APKG_PATH)
print(f"  {len(apkg)} words with image fields")
for word, entries in apkg.items():
    sources.setdefault(word, []).extend(entries)

print(f"loading {WORDLIST} ...")
pos_keys = load_pos_keys(WORDLIST)
print(f"  {len(pos_keys)} headwords")

unparsed = []
added = merged = 0
auto_pos = blank_pos = 0
queue = []

for word in sorted(sources):
    rec = store.get(word)
    if rec is None:
        rec = {"word": word, "senses": []}
        store[word] = rec
        added += 1
    else:
        merged += 1

    keys = pos_keys.get(word, [])
    pos = keys[0] if len(keys) == 1 else ""

    if not rec["senses"]:
        rec["senses"] = [S.make_sense(pos=pos)]
    target = rec["senses"][0]
    # Fill in a PoS on a still-unassigned sense, but never overwrite a human's.
    if not target.get("pos") and pos:
        target["pos"] = pos

    have = {S.image_key(i) for i in S.all_images(rec)}
    for url, src_page in sources[word]:
        img = to_image(url, src_page, unparsed)
        key = S.image_key(img)
        if key in have:
            continue
        have.add(key)
        target.setdefault("images", []).append(img)

    if target.get("pos"):
        auto_pos += 1
    else:
        blank_pos += 1
        if len(keys) > 1:
            queue.append((word, ", ".join(keys)))

S.save_images(store, OUT_PATH)

with open(UNPARSED_REPORT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["url", "source_page"])
    w.writerows(sorted(set(unparsed)))

with open(QUEUE_REPORT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["word", "pos_groups"])
    w.writerows(queue)

print()
print(f"wrote {OUT_PATH}: {len(store)} words "
      f"({added} new, {merged} merged into existing)")
print(f"  pos auto-assigned: {auto_pos}   left blank: {blank_pos}")
print(f"  unresolvable URLs kept verbatim: {len(set(unparsed))} -> {UNPARSED_REPORT}")
print(f"  multi-PoS curation queue: {len(queue)} -> {QUEUE_REPORT}")
