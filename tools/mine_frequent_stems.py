"""
tools/mine_frequent_stems.py — Mine frequently recurring 3-5 char substrings.

One-shot script. Run from the project root:
  venv/bin/python3 tools/mine_frequent_stems.py

Algorithm:
  1. For each word-list entry, strip known affixes and pseudo-morphemes using the
     same segmenter machinery (producing residues).
  2. Count character n-grams (length 3-5) in those residues that appear in >= 3
     distinct word-list entries.
  3. Filter out anything already a known affix, pseudo-morpheme surface, function
     word, or a short root (len <= 3).
  4. Write data/mined_stems.tsv sorted by frequency descending.

Output format: surface\tfrequency\texample_words
"""

import os
import sys
import warnings
from collections import Counter, defaultdict

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

WORDLIST = os.path.join(PROJECT_ROOT, "globasa_tokenizer", "data", "word-list.csv")
TSV_OUT = os.path.join(PROJECT_ROOT, "globasa_tokenizer", "data", "mined_stems.tsv")
MIN_FREQ = 3
MIN_LEN = 3
MAX_LEN = 5

print("Loading lexicon...")
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from globasa_tokenizer.lexicon import build_lexicon
    lex = build_lexicon(WORDLIST)

print(f"  Roots: {lex.n_roots}, Prefixes: {lex.n_prefixes}, Suffixes: {lex.n_suffixes}")

# Build blacklist: affixes + pseudo-morpheme surfaces + function words + short roots
blacklist = set()
blacklist.update(lex.prefixes)
blacklist.update(lex.suffixes)
blacklist.update(lex.function_words)
# Pseudo-morpheme surfaces from TSV
from globasa_tokenizer.pseudo_morphemes import load_inventory as load_pseudo
pseudo_path = os.path.join(PROJECT_ROOT, "globasa_tokenizer", "data", "pseudo_morphemes.tsv")
for entry in load_pseudo(pseudo_path):
    blacklist.add(entry.surface)

print(f"  Blacklist: {len(blacklist)} entries")

df = pd.read_csv(WORDLIST, index_col="Word", dtype=str)
df.index = df.index.astype(str).str.strip()

# Build residues: strip one prefix and/or one suffix from each word
def get_residue(word, lex):
    """Strip known affixes from word, return the stem residue."""
    w = word.lower()
    # Try prefix strip
    pfx_match = lex.prefix_trie.longest_match(w)
    if pfx_match:
        pfx, pfx_len = pfx_match
        stem = w[pfx_len:]
    else:
        stem = w
    # Try suffix strip
    sfx_match = lex.suffix_trie.longest_match(stem)
    if sfx_match:
        sfx, sfx_len = sfx_match
        inner = stem[:-sfx_len]
        if inner:
            return inner
    return stem

print("Computing residues...")
ngram_counts: Counter = Counter()
ngram_examples: dict = defaultdict(list)

for word in df.index:
    w = str(word).strip()
    if not w or len(w) < 4:
        continue
    residue = get_residue(w, lex)
    if len(residue) < MIN_LEN:
        continue
    # Extract all n-grams from residue
    for n in range(MIN_LEN, MAX_LEN + 1):
        for i in range(len(residue) - n + 1):
            ng = residue[i:i+n]
            if ng.isalpha() and ng not in blacklist:
                ngram_counts[ng] += 1
                if len(ngram_examples[ng]) < 5:
                    ngram_examples[ng].append(w)

print(f"  Total n-gram types: {len(ngram_counts)}")

# Filter by frequency
frequent = [(ng, cnt) for ng, cnt in ngram_counts.items() if cnt >= MIN_FREQ]
frequent.sort(key=lambda x: -x[1])

print(f"  N-grams with freq >= {MIN_FREQ}: {len(frequent)}")

print(f"Writing {TSV_OUT}...")
with open(TSV_OUT, "w", encoding="utf-8") as f:
    f.write("surface\tfrequency\texample_words\n")
    for ng, cnt in frequent:
        examples = ", ".join(ngram_examples[ng][:5])
        f.write(f"{ng}\t{cnt}\t{examples}\n")

print(f"Done. {len(frequent)} stems written.")
