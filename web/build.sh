#!/usr/bin/env bash
# Build the static browser translator into web/dist/ (served as is, e.g. GitHub Pages):
#   wasm/     multicall Apertium binary + trimmed ICU data     (build_wasm.sh)
#   pairs/    mode manifests and the compiled pair files       (build_modes.py)
#   pyodide/  Pyodide core, self-hosted (pinned in package.json)
#   ort/      onnxruntime-web, plain wasm build (pinned in package.json)
#   tagger/en/ the English PoS taggers and parser for the eng->glb neural steps
#             (tagger/export_stanza_pos.py, tagger/export_stanza_depparse.py;
#             TAGGER_EXPORT / PARSER_EXPORT, default on Warehouse2)
#   coref/en/ the LitBank mode's coreference model, only if exported
#             (tagger/export_litbank_coref.py; COREF_EXPORT, default on Warehouse2)
#   src/ py/  the pipeline runner;  index.html, worker.js      (site/)
#
#   web/build.sh            everything
#   web/build.sh --no-wasm  reuse web/dist/wasm (pairs or page changed only)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
PY="${PYTHON:-$ROOT/venv/bin/python}"
[ -x "$PY" ] || PY=python3

[ "${1:-}" = --no-wasm ] || "$HERE/build_wasm.sh"
"$PY" "$HERE/build_modes.py"

if [ ! -f "$HERE/node_modules/pyodide/pyodide.asm.wasm" ]; then
  (cd "$HERE" && npm ci --no-audit --no-fund)
fi
mkdir -p "$HERE/dist/pyodide" "$HERE/dist/src" "$HERE/dist/py"
for f in pyodide.mjs pyodide.asm.mjs pyodide.asm.wasm python_stdlib.zip pyodide-lock.json; do
  cp "$HERE/node_modules/pyodide/$f" "$HERE/dist/pyodide/"
done
mkdir -p "$HERE/dist/ort" "$HERE/dist/tagger/en"
for f in ort.wasm.min.mjs ort-wasm-simd-threaded.mjs ort-wasm-simd-threaded.wasm; do
  cp "$HERE/node_modules/onnxruntime-web/dist/$f" "$HERE/dist/ort/"
done
TAGGER_EXPORT="${TAGGER_EXPORT:-/media/paleos/Warehouse2/Language/Claude/browser_tagger/export_100000}"
if [ ! -f "$TAGGER_EXPORT/combined_nocharlm.sent.onnx" ]; then
  PRETRAIN_TOP=100000 python3 "$HERE/test/capped.py" "$PY" "$HERE/tagger/export_stanza_pos.py" "$TAGGER_EXPORT"
fi
cp "$TAGGER_EXPORT/"*.onnx "$TAGGER_EXPORT/"*.vocab.json "$TAGGER_EXPORT/"pretrain.* "$HERE/dist/tagger/en/"
PARSER_EXPORT="${PARSER_EXPORT:-/media/paleos/Warehouse2/Language/Claude/browser_tagger/export_parser}"
if [ ! -f "$PARSER_EXPORT/parser.sent.onnx" ]; then
  PRETRAIN_TOP=100000 python3 "$HERE/test/capped.py" "$PY" "$HERE/tagger/export_stanza_depparse.py" "$PARSER_EXPORT"
fi
cp "$PARSER_EXPORT/"parser.* "$PARSER_EXPORT/"lemma.dict.json "$HERE/dist/tagger/en/"
COREF_EXPORT="${COREF_EXPORT:-/media/paleos/Warehouse2/Language/Claude/browser_coref/export}"
rm -rf "$HERE/dist/coref"
if [ -f "$COREF_EXPORT/coref.json" ]; then
  mkdir -p "$HERE/dist/coref/en"
  cp "$COREF_EXPORT/"coref.json "$COREF_EXPORT/"coref.bert.onnx.* "$COREF_EXPORT/"coref.heads.onnx \
     "$COREF_EXPORT/"coref.consts.f32 "$COREF_EXPORT/"coref.vocab.txt "$HERE/dist/coref/en/"
else
  echo "no LitBank export in $COREF_EXPORT: the page is built without the LitBank mode" >&2
fi
cp "$HERE/src/"*.mjs "$HERE/dist/src/"
cp "$HERE/py/runner.py" "$HERE/dist/py/"
cp "$HERE/site/index.html" "$HERE/site/worker.js" "$HERE/models.json" "$HERE/dist/"
touch "$HERE/dist/.nojekyll"
du -sh "$HERE/dist"
