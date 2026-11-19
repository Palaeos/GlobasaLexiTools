# Public-domain primary sources for curated readings of The Time Machine's
# terms of art (see README "Scholarly sources"). Page numbers are kept as
# "[p. N]" markers so readings can be cited with pages.
#
#   python3 time-machine/fetch_sources.py
#
# -> sources/ (committed; all public domain):
#   tylor_primitive_culture.txt   Tylor, Primitive Culture (Wikisource; 1920
#                                 printing of the 1871 work) — "survivals"
#   huxley_evolution_ethics.txt   Huxley, Evolution and Ethics (Romanes
#                                 Lecture 1893; Wikisource)
#   wells_zoological_retrogression.txt  Wells, Gentleman's Magazine 271
#                                 (Sept 1891; Wikisource)
#   wells_certain_personal_matters.txt  Wells 1898 (Gutenberg #17508 via IA);
#                                 contains "Of a Book Unwritten" = "The Man
#                                 of the Year Million" (Pall Mall Budget 1893)
#   lankester_degeneration.txt    Lankester, Degeneration: A Chapter in
#                                 Darwinism (1880; IA djvu OCR)
# -> cache/sources/ (git-ignored, 29 MB):
#   webster_1913.txt              Webster's Revised Unabridged (Gutenberg
#                                 #29765 via IA) — period senses
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from html import unescape
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "sources"
CACHE = HERE / "cache" / "sources"
UA = "GlobasaLexiTools/0.1 (source fetch)"
WS = "https://en.wikisource.org/w/api.php"


def get(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for wait in (0, 5, 15, 45):
        time.sleep(wait)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
                return data if binary else data.decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code not in (429, 502, 503):
                raise
        except urllib.error.URLError:
            pass
    raise RuntimeError("failed: " + url)


def ws_parse(title, prop="text"):
    q = urllib.parse.urlencode({"action": "parse", "page": title, "prop": prop, "format": "json",
                                "redirects": 1, "disableeditsection": 1})
    return json.loads(get(WS + "?" + q))["parse"]


def ws_text(title):
    """Rendered Wikisource page -> paragraphs with [p. N] page markers."""
    html = ws_parse(title)["text"]["*"]
    html = re.sub(r'<span[^>]*class="pagenum[^"]*"[^>]*data-page-number="([^"]+)"[^>]*>',
                  lambda m: f" [p. {m.group(1)}] <span>", html)
    html = re.sub(r'<(div|span) [^>]*(wst-header|ws-header|ws-noexport)[^>]*>.*?</\1>', "", html, flags=re.S)
    html = re.sub(r"<(style|script|sup)[^>]*>.*?</\1>", "", html, flags=re.S)
    paras = []
    for p in re.findall(r"<p[^>]*>(.*?)</p>", html, flags=re.S):
        t = re.sub(r"<br\s*/?>", " ", p)
        t = re.sub(r"<[^>]+>", "", t)
        t = unescape(re.sub(r"\s+", " ", t)).replace("​", "").strip()
        if t:
            paras.append(t)
    return "\n\n".join(paras)


def ws_book(index, sub_prefix=None):
    """A Wikisource work: its subpages in link order (Chapter N sorted
    numerically), or the page itself when it has none."""
    links = [l["*"] for l in ws_parse(index, "links")["links"] if l["*"].startswith(index + "/")]
    if not links:
        return ws_text(index)
    key = lambda t: [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", t)]
    parts = []
    for t in sorted(set(links), key=key):
        parts.append("## " + t.split("/", 1)[1] + "\n\n" + ws_text(t))
        print("  ", t)
        time.sleep(1.5)
    return "\n\n".join(parts)


def ia(identifier, name):
    return get(f"https://archive.org/download/{identifier}/{urllib.parse.quote(name)}")


SRC.mkdir(exist_ok=True)
CACHE.mkdir(parents=True, exist_ok=True)
jobs = [
    ("tylor_primitive_culture.txt", lambda: ws_book("Primitive Culture")),
    ("huxley_evolution_ethics.txt", lambda: ws_book("Evolution and Ethics")),
    ("wells_zoological_retrogression.txt",
     lambda: ws_text("The Gentleman's Magazine/Volume 271/September 1891/Zoological Retrogression")),
    ("wells_certain_personal_matters.txt", lambda: ia("certainpersonalm17508gut", "17508.txt")),
    ("lankester_degeneration.txt", lambda: ia("degenerationchap00lank", "degenerationchap00lank_djvu.txt")),
]
for name, fn in jobs:
    out = SRC / name
    if out.exists() and out.stat().st_size > 1000:
        print("have", name)
        continue
    text = fn()
    out.write_text(text, encoding="utf-8")
    print(name, len(text.split()), "words")

web = CACHE / "webster_1913.txt"
if not web.exists():
    web.write_bytes(get("https://archive.org/download/webstersunabridg29765gut/29765-8.txt", binary=True))
print("webster_1913.txt", web.stat().st_size // 1_000_000, "MB")
