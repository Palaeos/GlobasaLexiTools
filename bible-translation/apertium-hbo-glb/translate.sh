#!/bin/sh
# apertium-hbo-glb pipeline:  ./translate.sh [STREAM] > OUT
# STREAM: an apertium-hbo passage stream (default: ../data/Gen_1.hbo.txt).
# Rebuilds the bidix from curated/bidix.tsv and the rtx when they changed.
# Unknown-to-generator words are listed on stderr (generated with lt-proc -n,
# so regular derivations like luminkalya pass through without '#').
set -e
cd "$(dirname "$0")"
GLB=${APERTIUM_GLB:-/usr/local/old-apertium-2024/share/apertium/apertium-glb}
IN=${1:-../data/Gen_1.hbo.txt}

if [ curated/bidix.tsv -nt hbo-glb.autobil.bin ] || [ make_bidix.py -nt hbo-glb.autobil.bin ]; then
    python3 make_bidix.py >&2
    lt-comp lr apertium-hbo-glb.hbo-glb.dix hbo-glb.autobil.bin >/dev/null
fi
if [ apertium-hbo-glb.hbo-glb.rtx -nt hbo-glb.rtx.bin ]; then
    rtx-comp apertium-hbo-glb.hbo-glb.rtx hbo-glb.rtx.bin
fi

TRANSFER=$(python3 prep_stream.py < "$IN" | apertium-pretransfer \
    | lt-proc -b hbo-glb.autobil.bin | rtx-proc -a hbo-glb.rtx.bin)
echo "$TRANSFER" | lt-proc -g "$GLB/glb.autogen.bin" | grep -o '#[^ ]*' | sort | uniq -c \
    | sed 's/^/not in generator: /' >&2 || true
echo "$TRANSFER" | lt-proc -n "$GLB/glb.autogen.bin" | python3 postformat.py
