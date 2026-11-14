#!/bin/sh
# apertium-hbo-glb pipeline:  ./translate.sh [STREAM] > OUT
# STREAM: an apertium-hbo passage stream (default: ../data/Gen_1.hbo.txt).
# Rebuilds the bidix from curated/bidix.tsv and the rtx when they changed.
# GENDER=1 ./translate.sh: gendered second-person pronouns (manyu, femyu, femuyu).
# curated/pronouns.tsv (or PRONOUNS=file): pronoun gender per word, by interpretation;
# list a passage's pronouns with: python3 pronouns.py suggest STREAM
# Unknown-to-generator words are listed on stderr (generated with lt-proc -n,
# so regular derivations like luminkalya pass through without '#').
set -e
cd "$(dirname "$0")"
# Globasa generator: the in-repo apertium-glb when built, else the old system install.
REPO_GLB="$(cd ../.. && pwd)/GlobasaTranslation/apertium-glb"
if [ -f "$REPO_GLB/glb.autogen.bin" ]; then DEFAULT_GLB=$REPO_GLB
else DEFAULT_GLB=/usr/local/old-apertium-2024/share/apertium/apertium-glb; fi
GLB=${APERTIUM_GLB:-$DEFAULT_GLB}
# GENDER=1: gendered second-person pronouns (manyu, femyu, femuyu); see the rtx.
RTX=hbo-glb.rtx.bin
[ "${GENDER:-0}" = 1 ] && RTX=hbo-glb.gender.rtx.bin
IN=${1:-../data/Gen_1.hbo.txt}

if [ curated/bidix.tsv -nt hbo-glb.autobil.bin ] || [ make_bidix.py -nt hbo-glb.autobil.bin ]; then
    python3 make_bidix.py >&2
    lt-comp lr apertium-hbo-glb.hbo-glb.dix hbo-glb.autobil.bin >/dev/null
fi
if [ ! -f hbo-glb.rtx.bin ] || [ apertium-hbo-glb.hbo-glb.rtx -nt hbo-glb.rtx.bin ]; then
    rtx-comp -e p_gender apertium-hbo-glb.hbo-glb.rtx hbo-glb.rtx.bin
fi
if [ ! -f hbo-glb.gender.rtx.bin ] || [ apertium-hbo-glb.hbo-glb.rtx -nt hbo-glb.gender.rtx.bin ]; then
    rtx-comp apertium-hbo-glb.hbo-glb.rtx hbo-glb.gender.rtx.bin
fi

# Pronoun gender by interpretation (curated/pronouns.tsv), before prep_stream drops the ids
PRONOUNS=${PRONOUNS:-curated/pronouns.tsv}
[ -f "$PRONOUNS" ] || PRONOUNS=/dev/null
TRANSFER=$(python3 pronouns.py tag "$PRONOUNS" < "$IN" | python3 prep_stream.py | apertium-pretransfer \
    | lt-proc -b hbo-glb.autobil.bin | rtx-proc -a "$RTX")
echo "$TRANSFER" | lt-proc -g "$GLB/glb.autogen.bin" | grep -o '#[^ ]*' | sort | uniq -c \
    | sed 's/^/not in generator: /' >&2 || true
echo "$TRANSFER" | lt-proc -n "$GLB/glb.autogen.bin" | python3 postformat.py
