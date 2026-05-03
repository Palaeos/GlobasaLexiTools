"""
tools/build_pseudo_morpheme_inventory.py — Bootstrap pseudo_morphemes.tsv.

One-shot script. Run from the project root:
  venv/bin/python3 tools/build_pseudo_morpheme_inventory.py

Produces: globasa_tokenizer/data/pseudo_morphemes.tsv

Three passes:
  1. Sinitic seed (data-driven): Scan Etymological support column for CJK characters.
     For each Globasa word whose etymology contains a CJK character, record the
     character as lemma and the Globasa word fragment as surface.
  2. European seed (rule-driven): From the official Globasa methodology:
     - -syon: 2-syllable words ending in -syon (> 1 occurrence)
     - -si: longer words ending in -si (> 1 occurrence)
     - viu: words containing 'viu' that aren't standalone 'viu'
     - -tika: words ending in -tika
     - -fobi: words ending in -fobi
  3. Discovery pass: n-grams (2-4 chars) at word ends appearing in >= 3 entries
     (candidate rows for human review, tagged origin=candidate).

Existing seed rows in pseudo_morphemes.tsv are preserved (not overwritten).
New rows are appended; duplicates (same surface+lemma) are skipped.
"""

import os
import re
import sys

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORDLIST = os.path.join(PROJECT_ROOT, "globasa_tokenizer", "data", "word-list.csv")
TSV_OUT = os.path.join(PROJECT_ROOT, "globasa_tokenizer", "data", "pseudo_morphemes.tsv")


def load_existing(path):
    """Load existing TSV, return set of (surface, lemma) already present."""
    existing = set()
    if not os.path.exists(path):
        return existing
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2:
                existing.add((parts[0].strip(), parts[1].strip()))
    return existing


def is_cjk(char):
    """Return True if char is in a CJK Unicode block."""
    cp = ord(char)
    return (
        0x4E00 <= cp <= 0x9FFF   # CJK Unified Ideographs
        or 0x3400 <= cp <= 0x4DBF  # Extension A
        or 0x20000 <= cp <= 0x2A6DF  # Extension B
        or 0x2A700 <= cp <= 0x2CEAF  # Extensions C-F
        or 0xF900 <= cp <= 0xFAFF   # Compatibility Ideographs
    )


def count_vowels(word):
    return sum(1 for c in word.lower() if c in "aeiou")


def count_syllables_approx(word):
    """Rough syllable count (vowel runs)."""
    return len(re.findall(r'[aeiou]+', word.lower()))


def mine_sinitic(df):
    """Pass 1: extract CJK character → Globasa word fragment mappings."""
    rows = []
    for word, row in df.iterrows():
        etym = str(row.get("Etymological support", "")).strip()
        if not etym or etym == "nan":
            continue
        cjk_chars = [c for c in etym if is_cjk(c)]
        if not cjk_chars:
            continue
        # Use the whole word as the surface (simplified: in production you'd
        # try to identify the sub-fragment corresponding to each character)
        word_str = str(word).strip().lower()
        if not word_str or len(word_str) < 2:
            continue
        for char in cjk_chars:
            rows.append({
                "surface": word_str,
                "lemma": char,
                "origin": "sinitic",
                "gloss": f"(from {char})",
                "notes": f"auto-mined from word '{word_str}'",
            })
    return rows


def mine_european(df):
    """Pass 2: rule-driven European pseudo-morphemes from methodology page."""
    rows = []
    words = [str(w).strip().lower() for w in df.index]

    def count_occurrences(pattern, words):
        return sum(1 for w in words if w.endswith(pattern) and len(w) > len(pattern))

    # -syon: 2-syllable words ending in -syon
    syon_count = count_occurrences("syon", words)
    if syon_count >= 2:
        rows.append({
            "surface": "syon",
            "lemma": "-tion",
            "origin": "romance",
            "gloss": "nominalization suffix (2-syllable base)",
            "notes": f"auto-mined; {syon_count} occurrences",
        })

    # -si: longer words ending in -si
    si_count = count_occurrences("si", words)
    if si_count >= 2:
        rows.append({
            "surface": "si",
            "lemma": "-tion",
            "origin": "romance",
            "gloss": "nominalization suffix (longer base → -si)",
            "notes": f"auto-mined; {si_count} occurrences; see also -syon",
        })

    # viu: view-derived borrowings
    viu_words = [w for w in words if "viu" in w and w != "viu"]
    if len(viu_words) >= 2:
        rows.append({
            "surface": "viu",
            "lemma": "view",
            "origin": "romance",
            "gloss": "view/look (bound loanword form)",
            "notes": f"auto-mined; occurs in {', '.join(viu_words[:5])}",
        })

    # -tika: Greek -tics field/study words
    tika_count = count_occurrences("tika", words)
    if tika_count >= 2:
        rows.append({
            "surface": "tika",
            "lemma": "-tics",
            "origin": "greek",
            "gloss": "field/study (from Greek -tike)",
            "notes": f"auto-mined; {tika_count} occurrences",
        })

    # -fobi: phobia words
    fobi_count = count_occurrences("fobi", words)
    if fobi_count >= 2:
        rows.append({
            "surface": "fobi",
            "lemma": "-phobia",
            "origin": "greek",
            "gloss": "fear of (from Greek phobia)",
            "notes": f"auto-mined; {fobi_count} occurrences",
        })

    return rows


def mine_candidates(df, existing_surfaces, min_freq=3, min_len=2, max_len=4):
    """Pass 3: discover high-frequency terminal n-grams as candidates."""
    from collections import Counter
    words = [str(w).strip().lower() for w in df.index
             if str(df.loc[w, 'Category']).strip() in ('root', 'derived')]
    ngram_counts = Counter()
    ngram_examples = {}
    for w in words:
        for n in range(min_len, max_len + 1):
            if len(w) > n:
                ng = w[-n:]
                # Filter: must be alphabetic, not already in inventory
                if ng.isalpha() and ng not in existing_surfaces:
                    ngram_counts[ng] += 1
                    ngram_examples.setdefault(ng, []).append(w)
    rows = []
    for ng, cnt in ngram_counts.most_common(50):
        if cnt >= min_freq:
            examples = ", ".join(ngram_examples[ng][:5])
            rows.append({
                "surface": ng,
                "lemma": f"?{ng}",
                "origin": "candidate",
                "gloss": "(for human review)",
                "notes": f"freq={cnt}; e.g. {examples}",
            })
    return rows


df = pd.read_csv(WORDLIST, index_col="Word", dtype=str)
df.index = df.index.astype(str).str.strip()

existing = load_existing(TSV_OUT)
existing_surfaces = {s for s, _ in existing}

print("Pass 1: Sinitic...")
sinitic_rows = mine_sinitic(df)
print(f"  Found {len(sinitic_rows)} raw Sinitic entries")

print("Pass 2: European (rule-driven)...")
euro_rows = mine_european(df)
print(f"  Found {len(euro_rows)} European entries")

print("Pass 3: Discovery candidates...")
cand_rows = mine_candidates(df, existing_surfaces)
print(f"  Found {len(cand_rows)} candidate entries")

all_new = sinitic_rows + euro_rows + cand_rows
to_add = []
seen_in_run = set()
for r in all_new:
    key = (r["surface"], r["lemma"])
    if key not in existing and key not in seen_in_run:
        to_add.append(r)
        seen_in_run.add(key)

print(f"\nAdding {len(to_add)} new rows to {TSV_OUT}")

# Write header if file doesn't exist
write_header = not os.path.exists(TSV_OUT)
with open(TSV_OUT, "a", encoding="utf-8") as f:
    if write_header:
        f.write("surface\tlemma\torigin\tgloss\tnotes\n")
    for r in to_add:
        line = "\t".join([
            r["surface"], r["lemma"], r["origin"], r["gloss"], r["notes"]
        ])
        f.write(line + "\n")

print("Done.")
