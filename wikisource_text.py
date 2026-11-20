# English Wikisource → plain text, shared by the per-work fetchers (time-machine/fetch_texts.py,
# war-of-the-worlds/fetch_texts.py). Functions only: safe to import.
#
#   chapter_titles(index)  subpages of an edition in table-of-contents (reading) order
#   plain(title)           one page as plain text, one paragraph per <p>
#   chapters_by_next(first)  subpages by following each header's "next" link (editions whose
#                          table of contents sits in transcluded scan pages without links)
#   fetch_edition(index, out_path, skip=(), first=None)  every chapter as "## <chapter>" + text;
#                          with first, chapters come from chapters_by_next(first)
import json
import posixpath
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from html import unescape

API = "https://en.wikisource.org/w/api.php"
UA = "GlobasaLexiTools/0.1 (text fetch)"


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


def chapter_titles(index, skip=("Advertisements",)):
    # rendered HTML keeps the table of contents in reading order (the link list is alphabetical)
    html = api(action="parse", page=index, prop="text", redirects=1)["parse"]["text"]["*"]
    out = []
    for href in re.findall(r'href="/wiki/([^"#]+)"', html):
        t = urllib.parse.unquote(href).replace("_", " ")
        if t.startswith(index + "/") and not any(s in t for s in skip) and t not in out:
            out.append(t)
    return out


def chapters_by_next(first, limit=500):
    out, title = [], first
    while title and title not in out and len(out) < limit:
        out.append(title)
        wikitext = api(action="parse", page=title, prop="wikitext", redirects=1)["parse"]["wikitext"]["*"]
        m = re.search(r"\|\s*next\s*=\s*\[\[([^|\]]+)", wikitext)
        if not m:
            break
        link = m.group(1).strip()
        if link.startswith("../") or link.startswith("/"):
            # "../Chapter 2" is relative to the page, "/Book 2" to the page as a folder
            base = title if link.startswith("/") else posixpath.dirname(title) + "/"
            link = posixpath.normpath(posixpath.join(base, link.lstrip("/") if link.startswith("/") else link[3:]))
        title = link
        time.sleep(1)
    return out


def plain(title):
    # TextExtracts returns nothing for ProofreadPage transclusions, so strip the rendered HTML:
    # one paragraph per <p>, header / navigation / page numbers dropped
    html = api(action="parse", page=title, prop="text", redirects=1, disableeditsection=1)["parse"]["text"]["*"]
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


def fetch_edition(index, out_path, skip=("Advertisements",), pause=2, first=None):
    parts = []
    titles = chapters_by_next(first) if first else chapter_titles(index, skip)
    # "next" can lead past the edition into the next work of a collected volume (Atlantic Edition:
    # The War of the Worlds -> A Dream of Armageddon); divider pages ("/Book 2") carry no chapter
    inside = [t for t in titles if t.startswith(index + "/")]
    titles = titles[:titles.index(inside[-1]) + 1] if inside else titles
    titles = [t for t in titles if t.startswith(index + "/") and not any(s in t for s in skip)]
    for t in titles:
        text = plain(t).strip()
        # heading relative to the edition (its index name can itself contain "/")
        head = t[len(index) + 1:] if t.startswith(index + "/") else t.split("/", 1)[1]
        parts.append("## " + head + "\n\n" + text)
        print(index, t, len(text), flush=True)
        time.sleep(pause)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    return len(parts)
