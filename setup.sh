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
#
# The options read the English Wiktionary dump (~2.4 GB) from
# WIKTIONARY_DUMP=/path/to/raw-wiktextract-data.jsonl(.gz), else from kaikki.org:
# streamed for --extension and --vetter, downloaded once for --selector (which
# reads it several times) into word_selection_cache/, where the others reuse it.
#
# Safe to run again: it refreshes the word list from the Globasa CDN and, if
# the list changed, drops the viewer's cache so the next start rebuilds it.
set -euo pipefail
cd "$(dirname "$0")"

EXTENSION=0; VETTER=0; SELECTOR=0
for arg in "$@"; do
    case "$arg" in
        --extension) EXTENSION=1 ;;
        --vetter) VETTER=1 ;;
        --selector) SELECTOR=1 ;;
        *) echo "Unknown option $arg (use --extension, --vetter, --selector)" >&2; exit 1 ;;
    esac
done

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

echo "== Word list"
venv/bin/python - <<'EOF'
import hashlib, os, shutil, urllib.request

URL = "https://cdn.globasa.net/api2/word-list.csv"
old = open("word-list.csv", "rb").read() if os.path.exists("word-list.csv") else None
try:
    with urllib.request.urlopen(URL, timeout=60) as r:
        new = r.read()
except OSError as e:
    if old is None:
        raise SystemExit(f"Could not download {URL}: {e}")
    print(f"  Could not refresh the word list ({e}); keeping the current one.")
else:
    if new != old:
        with open("word-list.csv", "wb") as f:
            f.write(new)
        shutil.rmtree("WordViewerLMDB", ignore_errors=True)
        print("  Downloaded; the viewer rebuilds its cache on the next start.")
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

Optional, machine-specific extras (the viewer runs without them):
    WV_AUDIO_DIR=/path/to/clips       pronunciation recordings (<word>.ogg)
    WV_APERTIUM_DIR=/path/to/apertium-glb-eng   compiled pair, for /translate
EOF
