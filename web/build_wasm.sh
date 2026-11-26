#!/usr/bin/env bash
# Build the multicall Apertium WebAssembly binary (web/wasm/CMakeLists.txt) into
# web/dist/wasm/. Sources are fetched at the commits of the Debian packages the
# Globasa pairs are compiled with, so compiled .bin files load unchanged.
#
#   WASM_WORK  work folder for emsdk, sources and build trees (several GB)
#              default: /media/paleos/Warehouse2/Language/Claude/wasm if it exists,
#              else ~/.cache/globasa-wasm
#   EMSDK_VERSION  default 7.0.0
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
if [ -z "${WASM_WORK:-}" ]; then
  if [ -d /media/paleos/Warehouse2/Language/Claude ]; then
    WASM_WORK=/media/paleos/Warehouse2/Language/Claude/wasm
  else
    WASM_WORK="$HOME/.cache/globasa-wasm"
  fi
fi
EMSDK_VERSION="${EMSDK_VERSION:-7.0.0}"
mkdir -p "$WASM_WORK/src" "$WASM_WORK/build"

# name  url  commit-or-tag
SOURCES=(
  "lttoolbox https://github.com/apertium/lttoolbox.git 76e6f6f0"
  "apertium https://github.com/apertium/apertium.git b0e6f61f"
  "apertium-lex-tools https://github.com/apertium/apertium-lex-tools.git 1ccefa62"
  "apertium-separable https://github.com/apertium/apertium-separable.git 18045e4d"
  "apertium-anaphora https://github.com/apertium/apertium-anaphora.git 55b1778e"
  "apertium-recursive https://github.com/apertium/apertium-recursive.git 4cfa84d7"
  "cg3 https://github.com/GrammarSoft/cg3.git 5f47afb6"
  "libxml2 https://github.com/GNOME/libxml2.git v2.13.8"
  "utfcpp https://github.com/nemtrif/utfcpp.git v4.0.6"
  "rapidjson https://github.com/Tencent/rapidjson.git 297637b"
)

if [ ! -d "$WASM_WORK/emsdk" ]; then
  git clone -q --depth 1 https://github.com/emscripten-core/emsdk.git "$WASM_WORK/emsdk"
fi
(cd "$WASM_WORK/emsdk" && ./emsdk install "$EMSDK_VERSION" >/dev/null && ./emsdk activate "$EMSDK_VERSION" >/dev/null)
# shellcheck disable=SC1091
source "$WASM_WORK/emsdk/emsdk_env.sh" >/dev/null 2>&1

for spec in "${SOURCES[@]}"; do
  read -r name url rev <<<"$spec"
  dir="$WASM_WORK/src/$name"
  [ -d "$dir" ] || git clone -q "$url" "$dir"
  (cd "$dir" && { git checkout -q "$rev" 2>/dev/null || { git fetch -q --tags origin && git checkout -q "$rev"; }; })
done

PREFIX="$WASM_WORK/prefix"
if [ ! -f "$PREFIX/lib/libxml2.a" ]; then
  mkdir -p "$WASM_WORK/build/libxml2"
  (cd "$WASM_WORK/build/libxml2" &&
   emcmake cmake "$WASM_WORK/src/libxml2" -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF \
     -DLIBXML2_WITH_ICONV=OFF -DLIBXML2_WITH_LZMA=OFF -DLIBXML2_WITH_ZLIB=OFF \
     -DLIBXML2_WITH_PYTHON=OFF -DLIBXML2_WITH_PROGRAMS=OFF -DLIBXML2_WITH_TESTS=OFF \
     -DLIBXML2_WITH_HTTP=OFF -DLIBXML2_WITH_FTP=OFF -DLIBXML2_WITH_THREADS=OFF \
     -DLIBXML2_WITH_MODULES=OFF -DCMAKE_INSTALL_PREFIX="$PREFIX" >/dev/null &&
   emmake make -j"$(nproc)" install >/dev/null)
fi

mkdir -p "$WASM_WORK/build/multicall"
(cd "$WASM_WORK/build/multicall" &&
 emcmake cmake "$HERE/wasm" -DCMAKE_BUILD_TYPE=Release -DSRC="$WASM_WORK/src" -DPREFIX="$PREFIX" >/dev/null &&
 emmake make -j"$(nproc)")

mkdir -p "$HERE/dist/wasm"
cp "$WASM_WORK/build/multicall/apertium.mjs" "$WASM_WORK/build/multicall/apertium.wasm" "$HERE/dist/wasm/"
# Synchronous tool calls (Pyodide's subprocess shim needs them): the module is built
# with WASM_ASYNC_COMPILATION=0, and its one instantiateSync() call is made to reuse a
# precompiled WebAssembly.Module passed as Module.wasmModule instead of recompiling
# 3.6 MB on every call. Checked for the pinned emsdk; fails loudly if the code changes.
python3 - "$HERE/dist/wasm/apertium.mjs" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
old = "var result=instantiateSync(wasmBinaryFile,info)"
new = ("var result=Module.wasmModule?[new WebAssembly.Instance(Module.wasmModule,info),"
       "Module.wasmModule]:instantiateSync(wasmBinaryFile,info)")
if s.count(old) != 1:
    sys.exit("apertium.mjs: instantiateSync pattern not found (emsdk changed?)")
open(p, "w", encoding="utf-8").write(s.replace(old, new))
PY

# Trimmed ICU data (the icu port links stub data): only the items in icu_items.txt,
# taken from the port's own icudt68l.dat. Needs icupkg (Debian: icu-devtools).
ICU_DAT="$(find "$EMSDK/upstream/emscripten/cache/ports/icu" -name icudt68l.dat -path '*data/in/*' | head -1)"
ICU_X="$WASM_WORK/build/icu-items"
rm -rf "$ICU_X" && mkdir -p "$ICU_X"
grep -v '^#' "$HERE/wasm/icu_items.txt" | grep . > "$ICU_X/items.lst"
rm -f "$HERE/dist/wasm/icudt68l.dat"
# icupkg resolves the list file against -d / -s, so run inside the item folder.
# --ignore-deps: brkitr/root.res names the Thai/Khmer/Lao/Burmese/CJK dictionaries,
# which no traced run opens (jpn is not in the browser yet).
(cd "$ICU_X" && icupkg -x items.lst -d . "$ICU_DAT" &&
 icupkg -tl --ignore-deps -s . -a items.lst new "$HERE/dist/wasm/icudt68l.dat")
# NFC normalisation data for apertium-normalize (from the installed apertium; it is
# gennorm2 output of apertium/nfcn.txt). Mounted at /icu/nfcn.nrm next to the ICU
# archive, because apertium-normalize points ICU's data directory at its folder.
cp /usr/share/apertium/nfcn.nrm "$HERE/dist/wasm/nfcn.nrm"
ls -la "$HERE/dist/wasm"
