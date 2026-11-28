# SPDX-License-Identifier: GPL-3.0-or-later
"""Upload the browser translator's neural models to Hugging Face and pin them in models.json.

For each folder in web/models.json (tagger/en, coref/en): create the public model repo if
missing, commit the folder's files from web/dist/<folder> together with its model card
(web/model_cards/<repo name>.md as README.md) in one commit, check that every file arrived
with its local size, and write that commit's id into models.json as the folder's revision.
The page then fetches https://huggingface.co/<repo>/resolve/<revision>/<file>, and
web/deploy.sh leaves the folder out of the Pages bundle.

The token comes from huggingface_hub's own login store (`hf auth login`, or HF_TOKEN); this
script never reads, prints or writes it. Files are streamed from disk, never held in memory.

    venv/bin/python web/upload_models.py            show what would be uploaded
    venv/bin/python web/upload_models.py --upload   upload and pin
    venv/bin/python web/upload_models.py --upload coref/en   one folder only

Build web/dist first (web/build.sh). Re-uploading unchanged files makes no new commit; the
revision then stays the repo's current head.
"""
import json
import os
import sys

from huggingface_hub import CommitOperationAdd, HfApi

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(HERE, "models.json")
DIST = os.path.join(HERE, "dist")
CARDS = os.path.join(HERE, "model_cards")

upload = "--upload" in sys.argv
only = [a for a in sys.argv[1:] if not a.startswith("--")]

with open(MODELS, encoding="utf-8") as f:
    models = json.load(f)
folders = [k for k, v in models.items() if isinstance(v, dict) and "repo" in v]
if only:
    unknown = sorted(set(only) - set(folders))
    if unknown:
        sys.exit(f"not in models.json: {', '.join(unknown)}")
    folders = [k for k in folders if k in only]

plan = []
for folder in folders:
    repo = models[folder]["repo"]
    src = os.path.join(DIST, folder)
    card = os.path.join(CARDS, repo.split("/")[-1] + ".md")
    if not os.path.isdir(src):
        sys.exit(f"{src} missing: run web/build.sh first")
    if not os.path.isfile(card):
        sys.exit(f"{card} missing: every repo gets a model card")
    files = sorted(n for n in os.listdir(src) if os.path.isfile(os.path.join(src, n)))
    size = sum(os.path.getsize(os.path.join(src, n)) for n in files)
    plan.append((folder, repo, src, card, files))
    print(f"{folder} -> https://huggingface.co/{repo}  ({len(files)} files, {size / 1e6:.1f} MB + README.md)")
    for n in files:
        print(f"    {n:32} {os.path.getsize(os.path.join(src, n)):>12,}")

if not upload:
    print("\ndry run: add --upload to create the repos, upload and pin the revisions")
    sys.exit(0)

api = HfApi()
user = api.whoami()["name"]             # fails here, before any upload, when not logged in
print(f"\nlogged in as {user}")
for folder, repo, src, card, files in plan:
    api.create_repo(repo, repo_type="model", private=False, exist_ok=True)
    ops = [CommitOperationAdd("README.md", card)]
    ops += [CommitOperationAdd(n, os.path.join(src, n)) for n in files]
    info = api.create_commit(repo, ops, commit_message=f"Upload {folder} from GlobasaLexiTools web/dist")
    revision = info.oid or api.model_info(repo).sha
    remote = {p.path: p.size for p in api.get_paths_info(repo, files, revision=revision)}
    bad = [n for n in files if remote.get(n) != os.path.getsize(os.path.join(src, n))]
    if bad:
        sys.exit(f"{repo}@{revision}: size mismatch or missing: {', '.join(bad)} (models.json not changed)")
    models[folder]["revision"] = revision
    with open(MODELS, "w", encoding="utf-8") as f:
        json.dump(models, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"{folder}: {repo}@{revision} pinned in models.json ({len(files)} files checked)")
print("rebuild (web/build.sh --no-wasm) so dist/models.json carries the revisions")
