"""Check menalariImages.jsonl against word-list.csv. Warnings only, never edits.

Reports, in order of how much they matter:
  1. senses whose `pos` is not a part of speech the word actually has
  2. senses still carrying `"pos": ""` on a word with several PoS groups
  3. sense labels that appear in none of that PoS's glosses
  4. images the API reported as gone
  5. words that are no longer in the word list at all

Anything marked `illustratable: false` — on a word or on a single sense — is
excluded from the "needs work" reports and counted separately. The queue has to
reflect real work or it gets ignored: much of the vocabulary (`jixi` "know",
`konceto` "concept", every conjunction) simply cannot be pictured.

Usage:
    venv/bin/python3 validate_images.py           # summary + first 20 of each
    venv/bin/python3 validate_images.py --all     # every row
"""
import csv
import re
import sys

import images_store as S

WORDLIST = "word-list.csv"
SHOW_ALL = "--all" in sys.argv
LIMIT = None if SHOW_ALL else 20

_WORD_RE = re.compile(r"[a-z]+")


def load_wordlist(path):
    """({word: {"gloss", "pos_keys"}}, {tag: [word, ...]})"""
    out = {}
    tags = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            word = (row.get("Word") or "").strip()
            if not word:
                continue
            gloss = row.get("TranslationEng") or ""
            out[word] = {"gloss": gloss, "pos_keys": S.word_pos_keys(gloss)}
            for tag in (row.get("Tags") or "").split(","):
                tag = tag.strip()
                if tag:
                    tags.setdefault(tag, []).append(word)
    return out, tags


def gloss_for_pos(gloss, pos):
    """The gloss text of the segments carrying this annotation."""
    from Lexilista_parser import _parse_annotation_prefix

    parts = []
    for seg in gloss.split("; "):
        if not seg.strip():
            continue
        prefix, text, _q = _parse_annotation_prefix(seg)
        if (prefix or "") == pos:
            parts.append(text)
    return "; ".join(parts)


def report(title, rows, note=""):
    if not rows:
        return 0
    print(f"\n{title}: {len(rows)}{note}")
    for row in rows[:LIMIT]:
        print(f"   {row}")
    if LIMIT and len(rows) > LIMIT:
        print(f"   ... and {len(rows) - LIMIT} more (--all to list)")
    return len(rows)


store = S.load_images()
wl, tag_index = load_wordlist(WORDLIST)
print(f"{len(store)} words in {S.IMAGES_JSONL}; {len(wl)} headwords in {WORDLIST}")

bad_pos, unassigned, odd_label, missing, absent, thin_derive = [], [], [], [], [], []


def check_derive(word, sense):
    """A `derive` spec is only useful if its tag names real, illustrated words."""
    spec = sense.get("derive") or {}
    tag = spec.get("tag")
    if not tag:
        return
    members = tag_index.get(tag)
    if members is None:
        thin_derive.append(f"{word:<20} derive.tag={tag!r} matches no tag in the word list")
        return
    imaged = [m for m in members if S.all_images(store.get(m) or {})]
    if len(imaged) < 2:
        thin_derive.append(f"{word:<20} derive.tag={tag!r}: {len(members)} hyponyms "
                           f"but only {len(imaged)} illustrated")
skipped_words = skipped_senses = 0
n_images = n_senses = 0

for word in sorted(store):
    rec = store[word]
    entry = wl.get(word)
    word_ok = S.is_illustratable(rec)
    if not word_ok:
        skipped_words += 1

    if entry is None:
        absent.append(f"{word:<24} {len(S.all_images(rec))} image(s)")
        continue

    keys = entry["pos_keys"]
    for sense in S.senses_of(rec):
        n_senses += 1
        n_images += len(sense.get("images") or [])
        if not S.is_illustratable(sense):
            skipped_senses += 1
        if not (word_ok and S.is_illustratable(sense)):
            continue

        pos = sense.get("pos", "") or ""
        if pos and pos not in keys:
            bad_pos.append(f"{word:<20} pos={pos!r:<10} word has: {', '.join(keys) or '(none)'}")
        elif not pos and len(keys) > 1:
            unassigned.append(f"{word:<20} choose from: {', '.join(keys)}")

        check_derive(word, sense)

        label = (sense.get("label") or "").strip()
        if label and pos:
            hay = gloss_for_pos(entry["gloss"], pos).lower()
            if not any(t in hay for t in _WORD_RE.findall(label.lower())):
                odd_label.append(f"{word:<20} [{pos}] label={label!r} not in gloss "
                                 f"{gloss_for_pos(entry['gloss'], pos)[:44]!r}")

    for img in S.all_images(rec):
        if img.get("status") == "missing":
            missing.append(f"{word:<20} {img.get('file') or img.get('url', '')[:60]}")

print(f"{n_senses} senses, {n_images} images")

problems = 0
problems += report("PoS not present on this word", bad_pos)
problems += report("PoS unassigned on a multi-PoS word", unassigned,
                   "  (the curation queue)")
problems += report("Sense label found in no gloss for its PoS", odd_label)
problems += report("Derived galleries with too few illustrated hyponyms", thin_derive)
problems += report("Images the API reports as gone", missing,
                   "  (kept in the store, never auto-deleted)")
problems += report("Words no longer in the word list", absent)

print()
print(f"marked illustratable=false: {skipped_words} word(s), {skipped_senses} sense(s)"
      "  — excluded from the reports above")
print(f"total flagged: {problems}")
