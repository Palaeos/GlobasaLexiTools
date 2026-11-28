"""Wiktionary extension builder — reads the vetting decisions,
fetches translations from LMDB, writes menalariExtension.tsv.

Reads:
  - vetted_senses.tsv  (the decisions; re-exported from the senses
    spreadsheets first when those are newer, see vetted_senses.py)
  - WiktionaryLMDB/  (English; or an extract made by wiktionary_extract.py:
    WiktionaryLMDB_senses/, every word-list gloss, or WiktionaryLMDB_vetted/,
    just the vetted entries)
  - WiktionaryLMDB_{lang}/  (non-English, per source)
  - word-list.csv  (for annotation overlays and word ordering)

Writes:
  - menalariExtension.tsv
  - menalariExtension_clarifiers.tsv  (every guessed clarifier with how it was found, and the
    shared translations left without one; clarifiers.py)

A translation shared by two or more Globasa words in one language column gets a guessed
clarifier in that language, word-list style: martinet (_oiseau_) (clarifiers.py). The word
list's own Spa/Epo clarifiers still come first.
"""

import os
import re
import sys
import csv

from clarifiers import Clarifiers
from wiktionary_db import WiktionaryDB
from wiktionary_extract import VETTED_LMDB, SENSES_LMDB
import vetted_senses
from wiktionary_constants import (WIKT_POS_FALLBACKS, 
    EXTENSION_LANGS, DIALECT_LANGS, WIKTIONARY_SOURCES,
    lang_display_name, format_translation_word, _resolve_lang,
    build_annotation_map, entry_to_string, pos_groups,
)

# ---------------------------------------------------------------------------
# csv.field_size_limit fix
# ---------------------------------------------------------------------------

maxInt = sys.maxsize
while True:
    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt / 10)

# ---------------------------------------------------------------------------
# Load vetted senses (vetted_senses.tsv; re-exported from the spreadsheets
# first if they are newer)
# ---------------------------------------------------------------------------

all_senses = vetted_senses.load_vetted()
print(f"  {sum(s['source'] == 'en' for s in all_senses)} vetted English senses, "
      f"{sum(s['source'] != 'en' for s in all_senses)} from other Wiktionaries")

# ---------------------------------------------------------------------------
# Group senses by Globasa word
# ---------------------------------------------------------------------------

from collections import defaultdict

word_senses = defaultdict(list)
for s in all_senses:
    word_senses[s['glb']].append(s)

# ---------------------------------------------------------------------------
# Open LMDB databases
# ---------------------------------------------------------------------------

dbs = {}

# The full English database ("JSONL parser 2.py") when this machine has it;
# otherwise an extract (wiktionary_extract.py), which yields the same rows
# when both come from the same dump.
# EXTENSION_EN_LMDB=path picks one explicitly (2026-11-28: the full database
# lives on a disk that was read-only for the rebuild, so the extension was built
# from a fresh extract of the same dump).
if os.environ.get("EXTENSION_EN_LMDB"):
    dbs['en'] = WiktionaryDB(path=os.environ["EXTENSION_EN_LMDB"], readonly=True)
    print(f"  Opened English LMDB at {os.environ['EXTENSION_EN_LMDB']} (EXTENSION_EN_LMDB)")
elif os.path.exists("./WiktionaryLMDB"):
    dbs['en'] = WiktionaryDB(readonly=True)
    print("  Opened English LMDB")
elif os.path.exists(SENSES_LMDB):
    dbs['en'] = WiktionaryDB(path=SENSES_LMDB, readonly=True)
    print(f"  Opened English LMDB at {SENSES_LMDB} "
          f"(fallback: no full WiktionaryLMDB, extract of the word list's glosses)")
elif os.path.exists(VETTED_LMDB):
    dbs['en'] = WiktionaryDB(path=VETTED_LMDB, readonly=True)
    print(f"  Opened English LMDB at {VETTED_LMDB} "
          f"(fallback: no full WiktionaryLMDB, extract of the vetted entries)")
else:
    sys.exit("No English Wiktionary database: run wiktionary_extract.py first.")

for source_code, config in WIKTIONARY_SOURCES.items():
    lmdb_dir = config['lmdb_dir']
    if os.path.exists(lmdb_dir):
        dbs[source_code] = WiktionaryDB(path=lmdb_dir, readonly=True)
        print(f"  Opened {source_code} LMDB at {lmdb_dir}")

# ---------------------------------------------------------------------------
# Load word-list.csv for annotation overlays and word ordering
# ---------------------------------------------------------------------------

menalari_name = "word-list.csv"
if not os.path.exists("./" + menalari_name):
    import wget
    print("Downloading the Globasa word-list")
    wget.download("https://cdn.globasa.net/api2/word-list.csv", menalari_name)

wordlist_order = []  # ordered list of all Globasa words
wordlist_data = {}   # glb -> {eng_text, spa_text, epo_text}
wordlist_rows = []   # the rows as read, for the clarifiers

with open("./" + menalari_name, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        wordlist_rows.append(row)
        word = row['Word']
        wordlist_order.append(word)
        wordlist_data[word] = {
            'eng': row.get('TranslationEng', '').strip(),
            'spa': row.get('TranslationSpa', '').strip(),
            'epo': row.get('TranslationEpo', '').strip(),
            'wordclass': row.get('WordClass', '').strip(),
        }

# ---------------------------------------------------------------------------
# Build extension TSV
# ---------------------------------------------------------------------------

extension_lang_headers = [lang_display_name(c) for c in EXTENSION_LANGS]
ext_lang_idx = {code: i for i, code in enumerate(EXTENSION_LANGS)}

# Pass 1: every Globasa word's translations, each item remembering the vetted sense it came
# from, so that pass 2 can tell shared translations apart.
words_with_data = 0
# Decisions the dump cannot serve: a different dump than the one vetted
# against renames or drops senses. Reported, never silently lost.
unmatched = defaultdict(list)
relabelled = []   # (vetted sense, label in this dump): Wiktionary reworded the table label

# A vetted sense names its translation table by the label it had when it was vetted.
# Wiktionary edits labels (typo fixes, "4. " numbering, "— see also ..." tails, case,
# punctuation), so after a dump refresh 268 senses missed (2026-11-28). A label is
# followed to its new wording only when exactly one table label of the same word and
# part of speech normalises to the same text; real rewrites ("to become ready for
# eating" -> "to prepare food for eating") stay unmatched for re-vetting.
_LABEL_SEE_ALSO_RE = re.compile(r"\s*[—–]\s*see also\b.*$")
_LABEL_NUMBER_RE = re.compile(r"^\(?\d+[.)]\s*")
_LABEL_PUNCT_RE = re.compile(r"[^\w\s]")


def normalise_label(label):
    t = label.strip().lower().replace("(s)", "s")
    t = _LABEL_SEE_ALSO_RE.sub("", t)
    t = _LABEL_NUMBER_RE.sub("", t)
    t = _LABEL_PUNCT_RE.sub(" ", t.replace("-", ""))
    words = t.split()
    if words and words[0] == "the":
        words = words[1:]
    return " ".join(words)


def relabelled_sense(db, s):
    """(label in this dump, translations, how) when s's table was only reworded or moved, else None.

    Wiktionary also moved language and country names from Noun to Proper noun sections
    (Italian "language", Angola "country in Southern Africa", 2026-11-28): the same label under
    a fallback part of speech (PoSFallbacks sheet, noun <-> name) is the same table."""
    want = normalise_label(s['sense'])
    for pos in [s['pos']] + WIKT_POS_FALLBACKS.get(s['pos'], []):
        every = db.get_translations(s['lookup_word'], pos) or {}
        moved = f", moved from {s['pos']} to {pos}" if pos != s['pos'] else ""
        if s['sense'] in every:
            return s['sense'], every, f"same label{moved}"
        hits = [label for label in every if normalise_label(label) == want]
        if len(hits) == 1:
            return hits[0], every, f"reworded label{moved}"
    return None
built = []  # (globasa_word, eng_sense_output, items[j][group] = {formatted: (word, sense, annotated)}) or (word,)

for globasa_word in wordlist_order:
    senses = word_senses.get(globasa_word, [])

    if not senses:
        built.append((globasa_word,))
        continue

    # Build annotation maps from word-list.csv
    wl = wordlist_data.get(globasa_word, {})
    annotation_maps = {}
    if wl.get('spa'):
        annotation_maps['es'] = build_annotation_map(wl['spa'])
    if wl.get('epo'):
        annotation_maps['eo'] = build_annotation_map(wl['epo'])

    # Determine PoS groups from word-list.csv English glosses
    # The wordlist defines the group structure (via WordClass → VerbType).
    # The xlsx VerbType column tells us which group each sense belongs to.
    # build_bidix.py reads the groups back with the same pos_groups().
    group_key_to_idx = {
        (wikt_pos, vt_name): i for i, (wikt_pos, vt_name, _)
        in enumerate(pos_groups(wl.get('eng', ''), wl.get('wordclass', '')))}
    num_groups = max(len(group_key_to_idx), 1)

    # Accumulators: per-group items for each language
    eng_sense_dict = {}
    output_items = [[{} for _ in range(num_groups)] for _ in EXTENSION_LANGS]

    for s in senses:
        source = s['source']
        db = dbs.get(source)
        if db is None:
            unmatched['no database for this Wiktionary'].append(s)
            continue

        trans_entry = db.get_translations(s['lookup_word'], s['pos'], senses=(s['sense'],))
        sense_label = s['sense']
        if trans_entry is None or sense_label not in trans_entry:
            found = relabelled_sense(db, s)
            if found is None:
                unmatched['word/part of speech not in the dump' if trans_entry is None
                          else 'sense not in the dump'].append(s)
                continue
            sense_label, trans_entry, how = found
            relabelled.append((s, sense_label, how))

        lang_translations = trans_entry[sense_label]
        eng_sense_dict.setdefault(s['lookup_word'], set()).add(s['sense'])

        # Use xlsx VerbType to determine which transitivity group
        vt = s.get('verb_type', '')
        group_idx = group_key_to_idx.get((s['pos'], vt))
        if group_idx is None:
            # Fallback: first group matching this pos
            for (gp, gvt), gidx in group_key_to_idx.items():
                if gp == s['pos']:
                    group_idx = gidx
                    break
        if group_idx is None:
            group_idx = 0

        for j, lang_code in enumerate(EXTENSION_LANGS):
            resolved, found = _resolve_lang(lang_code, lang_translations)
            if not found:
                continue
            for t in resolved:
                formatted = format_translation_word(t, s['pos'])
                ann_key = DIALECT_LANGS[lang_code][0] if lang_code in DIALECT_LANGS else lang_code
                ann = annotation_maps.get(ann_key, {}).get(t.word, "")
                if ann:
                    formatted += f" (_{ann}_)"
                output_items[j][group_idx].setdefault(formatted, (t.word, s, bool(ann)))

        # For non-English sources, include the lookup word itself as a
        # translation for the source language (e.g. Lebewesen → German),
        # with gender tag if available from the entry's sense tags
        if s['source'] != 'en' and s['source'] in ext_lang_idx:
            j = ext_lang_idx[s['source']]
            pivot = s['lookup_word']
            if s['pos'] in ('noun', 'name'):
                sense_list = db.get_senses(s['lookup_word'], s['pos']) or []
                if sense_list:
                    stags = sense_list[0].tags
                    genders = []
                    if 'masculine' in stags:
                        genders.append('<m>')
                    if 'feminine' in stags:
                        genders.append('<f>')
                    if 'neuter' in stags:
                        genders.append('<n>')
                    if genders:
                        pivot += ' ' + '/'.join(genders)
            output_items[j][group_idx].setdefault(pivot, (s['lookup_word'], s, False))

    # Build eng_sense_output
    eng_sense_output = ', '.join(
        word + " [" + "|".join(sorted(senses_set)) + "]"
        for word, senses_set in eng_sense_dict.items()
    )
    built.append((globasa_word, eng_sense_output, output_items))
    if eng_sense_output:
        words_with_data += 1

# Pass 2: shared translations get a clarifier (clarifiers.py), then the rows are written.
first_sense = {}  # (lang, word, glb) -> the vetted sense that gave it
extension_words = defaultdict(list)  # (glb, lang) -> [(word, pos)], in order: how tags are written
for entry in built:
    if len(entry) == 1:
        continue
    for j, groups in enumerate(entry[2]):
        for group in groups:
            for word, sense, _ in group.values():
                if (EXTENSION_LANGS[j], word, entry[0]) not in first_sense:
                    first_sense[(EXTENSION_LANGS[j], word, entry[0])] = sense
                    extension_words[(entry[0], EXTENSION_LANGS[j])].append((word, sense['pos']))
clar = Clarifiers(wordlist_rows, dbs.get('en'), extension_words)
shared = clar.shared_index(first_sense.keys())
report = []

with open('menalariExtension.tsv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f, delimiter='\t', lineterminator='\n')
    writer.writerow(['Globasa', 'Eng with Senses'] + extension_lang_headers)
    for entry in built:
        if len(entry) == 1:
            writer.writerow([entry[0]])
            continue
        globasa_word, eng_sense_output, output_items = entry
        cells = []
        for j, groups in enumerate(output_items):
            lang_code = EXTENSION_LANGS[j]
            out_groups = []
            for group in groups:
                out = set()
                for formatted, (word, sense, annotated) in group.items():
                    sharers = shared.get((lang_code, word), set()) - {globasa_word}
                    if sharers and not annotated:
                        others = [(g, first_sense.get((lang_code, word, g))) for g in sorted(sharers)]
                        own = {w for grp in groups for w, _, _ in grp.values()}
                        text, how = clar.choose(lang_code, word, globasa_word, sense, others, own)
                        if text:
                            formatted += f" (_{text}_)"
                        report.append([globasa_word, lang_code, word, text or "", how,
                                       ", ".join(sorted(sharers))])
                    out.add(formatted)
                out_groups.append(out)
            cells.append(entry_to_string(out_groups))
        writer.writerow([globasa_word, eng_sense_output] + cells)

with open('menalariExtension_clarifiers.tsv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f, delimiter='\t', lineterminator='\n')
    writer.writerow(['Globasa', 'Language', 'Translation', 'Clarifier', 'How', 'Shared with'])
    writer.writerows(report)
given = sum(1 for r in report if r[3])
fallbacks = sum(1 for r in report if r[3] and "fallback" in r[4])
print(f"  Shared translations: {len(report)}; clarifier guessed for {given} "
      f"({fallbacks} of them by a fallback), see menalariExtension_clarifiers.tsv")

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

# Every skipped vetted sense, for re-vetting (sense_vetter.py): after a dump refresh
# these are mostly table labels Wiktionary rewrote.
with open("menalariExtension_unmatched.tsv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["reason", "Globasa", "lookup_word", "pos", "vetted label", "labels in this dump"])
    for reason, lst in unmatched.items():
        for s in lst:
            db = dbs.get(s['source'])
            labels = list((db.get_translations(s['lookup_word'], s['pos']) or {}) if db else ())
            w.writerow([reason, s['glb'], s['lookup_word'], s['pos'], s['sense'], " | ".join(labels)])
for db in dbs.values():
    db.close()

print(f"\nWrote menalariExtension.tsv: {words_with_data} words with translations, "
      f"{len(wordlist_order)} total rows")
if relabelled:
    with open("menalariExtension_relabelled.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["Globasa", "lookup_word", "pos", "vetted label", "label in this dump", "how"])
        for s, label, how in relabelled:
            w.writerow([s['glb'], s['lookup_word'], s['pos'], s['sense'], label, how])
    moved = sum("moved" in how for _, _, how in relabelled)
    print(f"  {len(relabelled)} vetted senses matched a reworded or moved table "
          f"(fallback: same label under the PoS fallback ({moved}), or the same text after "
          f"normalisation, a unique match), see menalariExtension_relabelled.tsv")
for reason, lst in unmatched.items():
    print(f"  {len(lst)} vetted senses skipped: {reason}, e.g. "
          + "; ".join(f"{s['glb']} / {s['lookup_word']} [{s['sense']}]" for s in lst[:3]))
