#!/usr/bin/env bash
# Set up the Word Viewer on a fresh clone, then start it with:
#     venv/bin/python "Word Viewer.py"      (http://localhost:5000)
#
#     ./setup.sh --extension   also builds menalariExtension.tsv (translations
#                              in ~50 more languages) from the Wiktionary dump
#     ./setup.sh --vetter      also prepares the Wiktionary sense vetter:
#                              venv/bin/python sense_vetter.py  (http://localhost:8090)
#     ./setup.sh --selector    also prepares the Word Selector (about an hour):
#                              venv/bin/python "Word Selector.py"  (http://localhost:8092)
#     ./setup.sh --fast        also builds the optional Rust extension rust/globasa_fast
#                              (needs Rust: https://rustup.rs); without it everything runs,
#                              only slower
#
# The options read the English Wiktionary dump (~2.4 GB) from
# WIKTIONARY_DUMP=/path/to/raw-wiktextract-data.jsonl(.gz), else from kaikki.org:
# streamed for --extension and --vetter, downloaded once for --selector (which
# reads it several times) into word_selection_cache/, where the others reuse it.
#
# Safe to run again: it refreshes the word list from the Globasa CDN and, if
# the list changed, drops the viewer's cache so the next start rebuilds it.
# The CDN may refuse scripted downloads; the script then prints where to get
# the list in a browser, and
#     ./setup.sh --word-list ~/Downloads/word-list.csv
# installs that file instead of downloading.
set -euo pipefail
cd "$(dirname "$0")"

EXTENSION=0; VETTER=0; SELECTOR=0; FAST=0; WORD_LIST_FILE=""
while [ $# -gt 0 ]; do
    case "$1" in
        --extension) EXTENSION=1 ;;
        --vetter) VETTER=1 ;;
        --selector) SELECTOR=1 ;;
        --fast) FAST=1 ;;
        --word-list)
            [ $# -ge 2 ] || { echo "--word-list needs a file" >&2; exit 1; }
            WORD_LIST_FILE=$2; shift ;;
        *) echo "Unknown option $1 (use --extension, --vetter, --selector, --fast, --word-list FILE)" >&2; exit 1 ;;
    esac
    shift
done
export WORD_LIST_FILE

PY=${PYTHON:-python3}
if ! "$PY" -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; then
    echo "Python 3.10 or newer is needed (set PYTHON=/path/to/python3 to choose one)." >&2
    exit 1
fi

echo "== Lessons (xwexi) and reader texts (doxo)"
git submodule update --init xwexi-pages-grav doxo-pages-grav

echo "== Python environment (venv/)"
[ -d venv ] || "$PY" -m venv venv
venv/bin/python -m pip install --quiet --upgrade pip
venv/bin/python -m pip install --quiet -r requirements-viewer.txt
if [ "$SELECTOR" = 1 ]; then
    venv/bin/python -m pip install --quiet -r requirements-selector.txt
fi
# memory guard for every script (memlimit.py; limit GLOBASA_MEM_GB, default 40% of RAM)
venv/bin/python -c "import memlimit; memlimit.install()"

if [ "$FAST" = 1 ]; then
    # Rust versions of the hot loops (word alignment, edition diffs, dependency-tree decoding),
    # identical results; tests/test_globasa_fast.py compares them with the Python originals
    echo "== Rust extension (rust/globasa_fast)"
    if command -v cargo >/dev/null 2>&1; then
        venv/bin/python -m pip install --quiet -r requirements-fast.txt
        VIRTUAL_ENV="$PWD/venv" venv/bin/maturin develop --release -m rust/globasa_fast/Cargo.toml
        venv/bin/python -c "import globasa_fast" && echo "globasa_fast installed"
    else
        echo "cargo not found, so the Rust extension was not built (everything runs without it,"
        echo "only slower). Install Rust from https://rustup.rs, then run ./setup.sh --fast again."
    fi
fi

echo "== Word list"
venv/bin/python - <<'EOF'
import os, shutil, sys, urllib.request

URL = "https://cdn.globasa.net/api2/word-list.csv"
DEST = os.path.abspath("word-list.csv")
HOW_TO = f"""
  The Globasa CDN refuses some automated downloads. To get the list by hand:
    1. Open {URL} in a web browser.
    2. Save it, e.g. to ~/Downloads/word-list.csv.
    3. Run:  ./setup.sh --word-list ~/Downloads/word-list.csv
       (or save it directly as {DEST}
        and delete WordViewerLMDB/ so the viewer rebuilds its cache)."""


def looks_like_word_list(data):
    # A block page arrives as HTML, sometimes with status 200.
    head = data[:200].lstrip(b"\xef\xbb\xbf")
    return head.startswith(b"Word,") and b"<html" not in data[:2000].lower()


old = open(DEST, "rb").read() if os.path.exists(DEST) else None
given = os.environ.get("WORD_LIST_FILE")
if given:
    path = os.path.expanduser(given)
    try:
        new = open(path, "rb").read()
    except OSError as e:
        sys.exit(f"  Cannot read {path}: {e}")
    if not looks_like_word_list(new):
        sys.exit(f"  {path} is not the word list (it should begin with 'Word,')." + HOW_TO)
else:
    new, problem = None, None
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "GlobasaLexiTools-setup"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
    except OSError as e:
        problem = str(e)
    else:
        if looks_like_word_list(data):
            new = data
        else:
            problem = "the server answered with a page instead of the word list"
    if new is None:
        if old is None:
            sys.exit(f"  Could not download the word list: {problem}." + HOW_TO)
        print(f"  Could not refresh the word list ({problem}); keeping the current one." + HOW_TO)
        new = old

if new != old:
    with open(DEST, "wb") as f:
        f.write(new)
    shutil.rmtree("WordViewerLMDB", ignore_errors=True)
    print("  Word list updated; the viewer rebuilds its cache on the next start.")
else:
    print("  Already up to date.")
EOF

if [ -z "${WIKTIONARY_DUMP:-}" ] && [ -f word_selection_cache/raw-wiktextract-data.jsonl.gz ]; then
    export WIKTIONARY_DUMP=word_selection_cache/raw-wiktextract-data.jsonl.gz
fi

if [ "$SELECTOR" = 1 ]; then
    DUMP=$(venv/bin/python -c 'from word_selection.dump import source; print(source("en"))')
    case "$DUMP" in
        http*)
            echo "== English Wiktionary dump (~2.4 GB, kept in word_selection_cache/)"
            mkdir -p word_selection_cache
            curl -fL -C - -o word_selection_cache/raw-wiktextract-data.jsonl.gz.part "$DUMP"
            mv word_selection_cache/raw-wiktextract-data.jsonl.gz.part \
               word_selection_cache/raw-wiktextract-data.jsonl.gz
            export WIKTIONARY_DUMP=word_selection_cache/raw-wiktextract-data.jsonl.gz ;;
    esac
    if [ -d WiktionaryLMDB_concepts ]; then
        echo "== Word Selector: WiktionaryLMDB_concepts/ exists (delete it to rebuild)"
    else
        echo "== Word Selector: Wiktionary concept index (about an hour)"
        venv/bin/python "Wiktionary concept index.py"
    fi
fi

if [ "$VETTER" = 1 ] && [ ! -d WiktionaryLMDB ]; then
    # Every English gloss of the word list (and every vetted entry), so it
    # also serves the extension. Not needed where the full WiktionaryLMDB/
    # ("JSONL parser 2.py") exists.
    echo "== English Wiktionary entries of the word list's glosses (takes a while)"
    venv/bin/python wiktionary_extract.py --senses
fi

if [ "$EXTENSION" = 1 ]; then
    # Translations beyond the word list: the vetted senses (vetted_senses.tsv
    # and sense_vetting.jsonl) looked up in the English Wiktionary; only the
    # vetted entries are kept.
    echo "== Menalari extension from the Wiktionary dump (takes a while)"
    if [ ! -d WiktionaryLMDB ] && [ ! -d WiktionaryLMDB_senses ]; then
        venv/bin/python wiktionary_extract.py
    fi
    venv/bin/python "Wiktionary extension builder.py"
    rm -rf WordViewerLMDB
fi

cat <<'EOF'

Done. Start the viewer with
    venv/bin/python "Word Viewer.py"
and open http://localhost:5000

Translations beyond the word list: ./setup.sh --extension
Wiktionary sense vetter (port 8090): ./setup.sh --vetter, then
    venv/bin/python sense_vetter.py
Word Selector (port 8092): ./setup.sh --selector, then
    venv/bin/python "Word Selector.py"
Faster alignment, edition diffs and parsing (needs Rust): ./setup.sh --fast

Optional, machine-specific extras (the viewer runs without them):
    WV_AUDIO_DIR=/path/to/clips       pronunciation recordings (<word>.ogg)
    WV_APERTIUM_DIR=/path/to/apertium-glb-eng   compiled pair, for /translate
EOF
