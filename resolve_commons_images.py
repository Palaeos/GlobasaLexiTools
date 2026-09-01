"""Refill every image's `direct_url` from the MediaWiki API.

The store keeps canonical file titles; this turns them back into URLs that
actually load. Wikimedia stopped rendering arbitrary thumbnail widths on
upload.wikimedia.org — it serves only widths already in cache — so the URLs
inherited from the old TSV 400 en masse. The API's `thumburl` is always a valid
rendering at a width it is willing to serve, on whichever host is current.

Cheap: 50 titles per request, so ~1800 images cost ~36 calls, versus ~1800 HEAD
requests against a CDN that rate-limits hard.

Usage:
    venv/bin/python3 resolve_commons_images.py            # skip fresh entries
    venv/bin/python3 resolve_commons_images.py --force    # re-resolve everything
"""
import re
import sys
import time
from datetime import date, datetime, timedelta

import requests

import images_store as S

FORCE = "--force" in sys.argv
TTL = timedelta(days=30)
BATCH = 50
SLEEP = 0.5
USER_AGENT = "GlobasaLexiTools/resolve_commons_images (paleos@paleos.me)"
TIMEOUT = (5, 30)
MAX_RETRIES = 4

_TAG_RE = re.compile(r"<[^>]+>")
_UTM_RE = re.compile(r"[?&]utm_[^&]*")


def strip_utm(url):
    """Drop the API's tracking params. Verified: the stripped URL still 200s."""
    if not url:
        return url
    cleaned = _UTM_RE.sub("", url)
    return cleaned.replace("?&", "?").rstrip("?&")


def plain(html):
    return _TAG_RE.sub("", html or "").strip()


def is_fresh(img):
    if FORCE or img.get("status") != "ok" or not img.get("direct_url"):
        return False
    try:
        return datetime.fromisoformat(img["resolved"]).date() > (date.today() - TTL)
    except (KeyError, TypeError, ValueError):
        return False


def api_get(endpoint, params, session):
    """GET with retries for maxlag / 429 / transient network errors."""
    for attempt in range(MAX_RETRIES):
        try:
            r = session.get(endpoint, params=params, timeout=TIMEOUT)
            if r.status_code in (429, 503):
                time.sleep(2 ** attempt)
                continue
            r.raise_for_status()
            data = r.json()
            if "error" in data and data["error"].get("code") == "maxlag":
                time.sleep(2 ** attempt)
                continue
            return data
        except (requests.RequestException, ValueError):
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(2 ** attempt)
    return {}


def resolve_batch(wiki, files, session):
    """{our_file_title: page dict or None}. None means the file is gone."""
    params = {
        "action": "query", "format": "json", "formatversion": "2",
        "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata",
        "iiurlwidth": str(S.DEFAULT_WIDTH),
        "iiextmetadatafilter": "LicenseShortName|Artist",
        "redirects": "1", "maxlag": "5",
        "titles": "|".join(f"File:{f}" for f in files),
    }
    data = api_get(S.api_endpoint(wiki), params, session)
    query = data.get("query") or {}

    # The API normalises titles and follows file redirects, so the page that
    # comes back may be titled differently from what we asked for. Walk the
    # chains forward from each request to find its page.
    hops = {}
    for key in ("normalized", "redirects"):
        for entry in query.get(key) or []:
            hops[entry["from"]] = entry["to"]
    pages = {p.get("title"): p for p in query.get("pages") or []}

    out = {}
    for f in files:
        title = f"File:{f}"
        seen = set()
        while title in hops and title not in seen:
            seen.add(title)
            title = hops[title]
        out[f] = pages.get(title)
    return out


def apply_page(img, page):
    """Write the API's answer onto an image record."""
    if page is None or page.get("missing"):
        img["status"] = "missing"
        img["resolved"] = date.today().isoformat()
        img.pop("direct_url", None)
        return "missing"

    info = (page.get("imageinfo") or [{}])[0]
    url = strip_utm(info.get("thumburl") or info.get("url") or "")
    if not url:
        img["status"] = "missing"
        img["resolved"] = date.today().isoformat()
        return "missing"

    # The API followed a redirect: adopt the new canonical title, but remember
    # the old one. The Anki deck still holds the pre-rename URL, and without
    # this the next sync would import the same picture again under its old name.
    renamed = False
    new_file = (page.get("title") or "").split("File:", 1)[-1].replace(" ", "_")
    if new_file and new_file != img.get("file"):
        if img.get("file"):
            aka = img.setdefault("aka", [])
            if img["file"] not in aka:
                aka.append(img["file"])
        img["file"] = new_file
        renamed = True

    img["direct_url"] = url
    img["width"] = info.get("thumbwidth") or info.get("width") or S.DEFAULT_WIDTH
    img["status"] = "ok"
    img["resolved"] = date.today().isoformat()
    if info.get("mime") == "image/gif" or info.get("duration"):
        img["kind"] = "gif"

    meta = info.get("extmetadata") or {}
    lic = plain((meta.get("LicenseShortName") or {}).get("value"))
    artist = plain((meta.get("Artist") or {}).get("value"))
    if lic:
        img["license"] = lic
    if artist:
        img["artist"] = artist
    return "renamed" if renamed else "ok"


# ---------- run ----------

store = S.load_images()
print(f"{len(store)} words in {S.IMAGES_JSONL}")

todo = {}   # wiki -> {file: [img, ...]}
fresh = literal = 0
for rec in store.values():
    for img in S.all_images(rec):
        if not img.get("file"):
            literal += 1           # Giphy and friends: nothing to resolve
            continue
        if is_fresh(img):
            fresh += 1
            continue
        todo.setdefault(img.get("wiki", "commons"), {}).setdefault(img["file"], []).append(img)

total = sum(len(v) for v in todo.values())
print(f"to resolve: {total} distinct files across {len(todo)} wiki(s)"
      f"   (skipping {fresh} fresh, {literal} unresolvable-by-design)")
if FORCE:
    print("  --force: ignoring the 30-day freshness window")

session = requests.Session()
session.headers["User-Agent"] = USER_AGENT

counts = {"ok": 0, "missing": 0, "renamed": 0}
done = 0
for wiki, by_file in todo.items():
    files = sorted(by_file)
    print(f"\n{wiki}: {len(files)} files")
    for i in range(0, len(files), BATCH):
        chunk = files[i:i + BATCH]
        pages = resolve_batch(wiki, chunk, session)
        for f in chunk:
            page = pages.get(f)
            for img in by_file[f]:
                counts[apply_page(img, page)] += 1
        done += len(chunk)
        print(f"  {done}/{total}")
        time.sleep(SLEEP)

S.save_images(store)

print()
print(f"resolved ok {counts['ok']}   renamed {counts['renamed']}   missing {counts['missing']}")
if counts["missing"]:
    print("\nfiles the API says are gone (kept in the store, not deleted):")
    for word, rec in sorted(store.items()):
        for img in S.all_images(rec):
            if img.get("status") == "missing":
                print(f"  {word:<20} {img.get('file', img.get('url', ''))[:70]}")
