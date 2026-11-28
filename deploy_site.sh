#!/usr/bin/env bash
# Build the static Word Viewer site and commit it to a local checkout of
# Palaeos/globasa-tools (GitHub Pages: Settings → Pages → Deploy from branch → main, / root).
#
#   ./deploy_site.sh           export + audit + one fresh commit in the site checkout (no push)
#   ./deploy_site.sh --push    ... and force-push it to origin/main
#   SITE_DIR=path              site checkout (default: ../globasa-tools next to this repo)
#   SKIP_EXPORT=1              reuse site_build/ (it is still audited by the export run that made it)
#
# Each deploy is a single orphan commit (history is not kept: the site is rebuilt
# from this repo, whose commit SOURCES.json records). translator/ in the site
# checkout is left alone, for the browser translator's own deploy.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
SITE_DIR="${SITE_DIR:-$(dirname "$ROOT")/globasa-tools}"
SITE_REMOTE="https://github.com/Palaeos/globasa-tools.git"
BUILD="$ROOT/site_build"

if [ -z "${SKIP_EXPORT:-}" ]; then
  "$ROOT/venv/bin/python" -u "$ROOT/export_word_viewer_site.py"
fi
[ -f "$BUILD/index.html" ] && [ -f "$BUILD/.site_build" ] || { echo "no site_build/: run the export first" >&2; exit 1; }

if [ ! -d "$SITE_DIR/.git" ]; then
  if ! git clone -q "$SITE_REMOTE" "$SITE_DIR" 2>/dev/null; then
    echo "($SITE_REMOTE not reachable or not created yet: starting a local repository)"
    git init -q -b main "$SITE_DIR"
    git -C "$SITE_DIR" remote add origin "$SITE_REMOTE"
  fi
fi

# Replace everything except .git and translator/.
find "$SITE_DIR" -mindepth 1 -maxdepth 1 ! -name .git ! -name translator -exec rm -rf {} +
cp -r "$BUILD/." "$SITE_DIR/"
rm -f "$SITE_DIR/.site_build"

COMMIT="$(git -C "$ROOT" rev-parse --short HEAD)"
cd "$SITE_DIR"
# No git identity configured (fresh site checkout, sandboxed shells): commit as
# the author of this repo's HEAD.
if [ -z "$(git config user.email || true)" ]; then
  export GIT_AUTHOR_NAME="$(git -C "$ROOT" log -1 --format=%an)" GIT_AUTHOR_EMAIL="$(git -C "$ROOT" log -1 --format=%ae)"
  export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME" GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"
fi
git checkout -q --orphan deploy-tmp
git add -A
git commit -q -m "Word Viewer site from GlobasaLexiTools $COMMIT"
git branch -D main -q 2>/dev/null || true
git branch -m main
echo "committed site to $SITE_DIR (main, $(git rev-parse --short HEAD))"

if [ "${1:-}" = --push ]; then
  git push -f origin main
fi
