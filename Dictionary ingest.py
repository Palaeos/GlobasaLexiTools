"""Download and index extra dictionaries for the Word Selector.

    venv/bin/python "Dictionary ingest.py" cedict     CC-CEDICT (Mandarin-English, pinyin; CC BY-SA 4.0)
    venv/bin/python "Dictionary ingest.py" jmdict     JMdict_e (Japanese-English, kana readings; EDRDG licence)
    venv/bin/python "Dictionary ingest.py" omw        Open Multilingual Wordnet 1.4 + OEWN 2023 via `wn`

cedict/jmdict write Dictionaries/<name>/ (LMDB): sub-db `words` (headword -> [{roman, glosses}])
and `gloss` (English gloss, lowercased -> [headword]) for gathering by English sense.
"""

import gzip
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

import lmdb
import msgpack

ROOT = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(ROOT, "Dictionaries")
UA = {"User-Agent": "GlobasaLexiTools/dictionary_ingest"}
SOURCES = {
    "cedict": "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz",
    "jmdict": "http://ftp.edrdg.org/pub/Nihongo/JMdict_e.gz",
}


def download(name):
    os.makedirs(os.path.join(DIR, name), exist_ok=True)
    path = os.path.join(DIR, name, os.path.basename(SOURCES[name]))
    if not os.path.exists(path):
        print(f"downloading {SOURCES[name]}")
        req = urllib.request.Request(SOURCES[name], headers=UA)
        with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
            f.write(r.read())
    return path


def write(name, words):
    env = lmdb.open(os.path.join(DIR, name, "lmdb"), max_dbs=2, map_size=2 * 1024 ** 3)
    dw, dg = env.open_db(b"words"), env.open_db(b"gloss")
    gloss = {}
    with env.begin(write=True) as txn:
        for w, items in words.items():
            txn.put(w.encode(), msgpack.packb(items, use_bin_type=True), db=dw)
            for it in items:
                for g in it["glosses"]:
                    g = re.sub(r"\([^)]*\)", "", g).strip().lower()
                    g = re.sub(r"^to ", "", g)
                    if g and len(g.split()) <= 4:
                        gloss.setdefault(g, []).append(w)
        for g, ws in gloss.items():
            txn.put(g.encode(), msgpack.packb(list(dict.fromkeys(ws))[:50], use_bin_type=True), db=dg)
    env.close()
    print(f"{name}: {len(words)} headwords, {len(gloss)} gloss keys")


def cedict():
    words = {}
    line_re = re.compile(r"^(\S+) (\S+) \[([^\]]+)\] /(.+)/$")
    with gzip.open(download("cedict"), "rt", encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                continue
            m = line_re.match(line.strip())
            if not m:
                continue
            trad, simp, pin, gl = m.groups()
            glosses = [g for g in gl.split("/") if g and not g.startswith(("variant of", "old variant", "see "))]
            item = {"roman": numbered_to_marked(pin), "glosses": glosses, "trad": trad}
            for w in {simp, trad}:
                words.setdefault(w, []).append(item)
    write("cedict", words)


TONE = {"a": "āáǎà", "e": "ēéěè", "i": "īíǐì", "o": "ōóǒò", "u": "ūúǔù", "ü": "ǖǘǚǜ"}


def numbered_to_marked(pin):
    out = []
    for syl in pin.lower().replace("u:", "ü").split():
        m = re.match(r"^([a-zü]+)([1-5])$", syl)
        if not m:
            out.append(syl)
            continue
        s, t = m.group(1), int(m.group(2))
        if t == 5:
            out.append(s)
            continue
        for v in ("a", "e", "ou"):
            if v in s:
                i = s.index(v)
                break
        else:
            i = max(s.rfind(c) for c in "iouü")
        out.append(s[:i] + TONE[s[i]][t - 1] + s[i + 1:])
    return "".join(out)


def jmdict():
    words = {}
    with gzip.open(download("jmdict"), "rb") as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag != "entry":
                continue
            kebs = [k.text for k in el.iter("keb")]
            rebs = [r.text for r in el.iter("reb")]
            glosses = [g.text for s in el.iter("sense") for g in s.iter("gloss") if g.text]
            item = {"roman": "", "kana": rebs[0] if rebs else "", "glosses": glosses[:12]}
            for w in kebs + rebs:
                words.setdefault(w, []).append(item)
            el.clear()
    write("jmdict", words)


def omw():
    import wn
    for spec in ("oewn:2023", "omw:1.4"):
        print(f"wn.download({spec})")
        wn.download(spec)
    print(wn.lexicons())


{"cedict": cedict, "jmdict": jmdict, "omw": omw}[sys.argv[1]]()
