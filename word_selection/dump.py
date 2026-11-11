"""Where the raw wiktextract dumps (kaikki.org format) are read from.

    source("en")    WIKTIONARY_DUMP, else this machine's copy, else kaikki.org
    source("de")    WIKTIONARY_DUMP_DE, ..., likewise for the other editions
    open_lines(src) its lines (a path or URL, .gz decompressed on the fly)

A URL is streamed, never stored; ./setup.sh --selector downloads the English
dump once instead, because the Word Selector's build reads it several times.
"""

import gzip
import io
import os
import urllib.request

LOCAL_DIR = "/media/paleos/Warehouse2/Language"     # the maintainer's copies, used when present


def _name(edition):
    return "raw-wiktextract-data.jsonl" if edition == "en" else f"raw-wiktextract-data-{edition}.jsonl"


def url(edition="en"):
    site = "dictionary" if edition == "en" else f"{edition}wiktionary"
    return f"https://kaikki.org/{site}/raw-wiktextract-data.jsonl.gz"


def source(edition="en"):
    env = os.environ.get("WIKTIONARY_DUMP" if edition == "en" else f"WIKTIONARY_DUMP_{edition.upper()}")
    if env:
        return env
    for name in (_name(edition), _name(edition) + ".gz"):
        local = os.path.join(LOCAL_DIR, name)
        if os.path.exists(local):
            return local
    return url(edition)


def open_lines(src, binary=False):
    """Lines of a dump path or URL: str lines, or bytes lines if binary."""
    if src.startswith(("http://", "https://")):
        print(f"  Streaming {src} (not stored)", flush=True)
        raw = urllib.request.urlopen(src, timeout=120)
    else:
        raw = open(src, "rb")
    if src.endswith(".gz"):
        raw = gzip.GzipFile(fileobj=raw)
    return raw if binary else io.TextIOWrapper(raw, encoding="utf-8")
