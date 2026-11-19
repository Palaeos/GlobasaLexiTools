#!/bin/sh
# apertium-hbo-glb pipeline:  ./translate.sh [STREAM] > OUT
# FORMAT=tmx: the draft as TMX (Hebrew verse + Globasa, one <tu> per verse; tmx.py).
# STREAM: an apertium-hbo passage stream (default: ../data/Gen_1.hbo.txt).
# Rebuilds the bidix from curated/bidix.tsv and the rtx when they changed.
# GENDER=1 ./translate.sh: gendered second-person pronouns (manyu, femyu, femuyu).
# curated/pronouns.tsv (or PRONOUNS=file): pronoun gender per word, by interpretation;
# list a passage's pronouns with: python3 pronouns.py suggest STREAM
# curated/constructs.tsv (or CONSTRUCTS=file): construct chains de/fe and adjective
# attachment per word, by interpretation; list them with: python3 constructs.py suggest STREAM
# Treebank roles (syntax.py; UD PTNK cached in ../sources/ud, or TREEBANK=dir; TREEBANK=/nonexistent
# to translate by word order only)
# curated/punctuation.tsv (or PUNCTUATION=file): dashes, parentheses per word (punctuation.py)
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

# Pronoun gender and construct chains by interpretation (curated/), before prep_stream drops the ids
PRONOUNS=${PRONOUNS:-curated/pronouns.tsv}
[ -f "$PRONOUNS" ] || PRONOUNS=/dev/null
CONSTRUCTS=${CONSTRUCTS:-curated/constructs.tsv}
[ -f "$CONSTRUCTS" ] || CONSTRUCTS=/dev/null
PUNCTUATION=${PUNCTUATION:-curated/punctuation.tsv}
[ -f "$PUNCTUATION" ] || PUNCTUATION=/dev/null
TRANSFER=$(python3 syntax.py tag ${TREEBANK:+"$TREEBANK"} < "$IN" \
    | python3 pronouns.py tag "$PRONOUNS" | python3 constructs.py tag "$CONSTRUCTS" \
    | python3 punctuation.py tag "$PUNCTUATION" \
    | python3 prep_stream.py | apertium-pretransfer \
    | lt-proc -b hbo-glb.autobil.bin | rtx-proc -a "$RTX")
echo "$TRANSFER" | lt-proc -g "$GLB/glb.autogen.bin" | grep -o '#[^ ]*' | grep -v '^#[—():;,.“”¦]$' | sort | uniq -c \
    | sed 's/^/not in generator: /' >&2 || true
if [ "${FORMAT:-txt}" = tmx ]; then
    echo "$TRANSFER" | lt-proc -n "$GLB/glb.autogen.bin" | python3 postformat.py | python3 tmx.py "$IN"
else
    echo "$TRANSFER" | lt-proc -n "$GLB/glb.autogen.bin" | python3 postformat.py
fi
