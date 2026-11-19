# Fetch the two 1895 first editions of The Time Machine from English Wikisource
# as plain text, one file per edition, chapters in reading order.
#   text/heinemann.txt  (UK, Heinemann 1895) — base text
#   text/holt.txt       (US, Holt 1895)      — second witness
# Chapter order is read from the edition's rendered table of contents, not
# from the (alphabetical) link list.
import json
import re
import time
import urllib.parse
import urllib.error
import urllib.request
from html import unescape
from pathlib import Path

API = "https://en.wikisource.org/w/api.php"
UA = "GlobasaLexiTools/0.1 (text fetch)"
OUT = Path(__file__).parent / "text"
EDITIONS = {
    "heinemann": "The Time Machine (Heinemann text)",
    "holt": "The Time Machine (Holt text)",
}


def api(**params):
    params["format"] = "json"
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for wait in (0, 5, 15, 45, 90):
        time.sleep(wait)
        try:
            with urllib.request.urlopen(req) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code not in (429, 502, 503):
                raise
        except urllib.error.URLError:
            pass  # transient proxy/tunnel failure
    raise RuntimeError("rate-limited: " + url)


def chapter_titles(index):
    # rendered HTML keeps the table of contents in reading order
    d = api(action="parse", page=index, prop="text", redirects=1)
    html = d["parse"]["text"]["*"]
    out = []
    for href in re.findall(r'href="/wiki/([^"#]+)"', html):
        t = urllib.parse.unquote(href).replace("_", " ")
        if t.startswith(index + "/") and "Advertisements" not in t and t not in out:
            out.append(t)
    return out


def plain(title):
    # TextExtracts returns nothing for ProofreadPage transclusions, so strip
    # the rendered HTML: one paragraph per <p>, drop header/nav/page numbers.
    d = api(action="parse", page=title, prop="text", redirects=1, disableeditsection=1)
    html = d["parse"]["text"]["*"]
    html = re.sub(r'<(div|span) [^>]*(ws-noexport|wst-header|pagenum|ws-pagenum)[^>]*>.*?</\1>', "", html, flags=re.S)
    html = re.sub(r"<(style|script)[^>]*>.*?</\1>", "", html, flags=re.S)
    paras = []
    for p in re.findall(r"<p[^>]*>(.*?)</p>", html, flags=re.S):
        t = re.sub(r"<br\s*/?>", " ", p)
        t = re.sub(r"<[^>]+>", "", t)
        t = unescape(re.sub(r"\s+", " ", t)).strip()
        if t:
            paras.append(t)
    return "\n\n".join(paras)


OUT.mkdir(exist_ok=True)
for key, index in EDITIONS.items():
    chapters = chapter_titles(index)
    parts = []
    for t in chapters:
        text = plain(t).strip()
        parts.append("## " + t.split("/", 1)[1] + "\n\n" + text)
        print(key, t, len(text))
        time.sleep(2)
    (OUT / f"{key}.txt").write_text("\n\n".join(parts) + "\n", encoding="utf-8")
