#!/usr/bin/env bash
# Build and test the browser translator, then commit web/dist to the gh-pages branch
# (GitHub Pages: Settings → Pages → Deploy from branch → gh-pages, / root).
#
# The bundle is built here, not in CI: the pairs need the whole Apertium toolchain and
# the monolingual checkouts, and the parity test needs the native tools to compare with.
#
#   web/deploy.sh            build, test, commit to gh-pages (local branch only)
#   web/deploy.sh --push     ... and push gh-pages to origin
#   SKIP_WASM=1              reuse web/dist/wasm
# Tests run under web/test/capped.py (GLOBASA_MEM_GB, default 40% of RAM).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
NODE="${NODE:-node}"

if [ -n "${SKIP_WASM:-}" ]; then "$HERE/build.sh" --no-wasm; else "$HERE/build.sh"; fi
(cd "$HERE" && python3 test/capped.py "$NODE" test/smoke_tools.mjs && python3 test/capped.py "$NODE" test/parity.mjs)

WT="$(mktemp -d)"
trap 'git -C "$ROOT" worktree remove --force "$WT" 2>/dev/null || true' EXIT
if git -C "$ROOT" show-ref --quiet refs/heads/gh-pages; then
  git -C "$ROOT" worktree add -q "$WT" gh-pages
else
  git -C "$ROOT" worktree add -q --detach "$WT"
  git -C "$WT" checkout -q --orphan gh-pages
  git -C "$WT" rm -rq --cached . 2>/dev/null || true
fi
find "$WT" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
cp -r "$HERE/dist/." "$WT/"
git -C "$WT" add -A
VERSION="$(python3 -c "import json;print(json.load(open('$HERE/dist/pairs/index.json'))['version'])")"
if git -C "$WT" diff --cached --quiet; then
  echo "gh-pages already has bundle $VERSION"
else
  git -C "$WT" commit -q -m "Browser translator bundle $VERSION (from $(git -C "$ROOT" rev-parse --short HEAD))"
  echo "committed bundle $VERSION to gh-pages"
fi
if [ "${1:-}" = --push ]; then git -C "$WT" push origin gh-pages; fi
