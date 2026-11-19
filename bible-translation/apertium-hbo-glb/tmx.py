#!/usr/bin/env python3
"""Machine draft as TMX: Hebrew source verse + Globasa output, one <tu> per verse.

    ./translate.sh STREAM | python3 tmx.py STREAM [CONTEXT] > OUT.tmx
    FORMAT=tmx ./translate.sh STREAM > OUT.tmx                          (the same)

STREAM is the apertium-hbo passage stream given to translate.sh; the Hebrew text is
rebuilt from its surface forms (spacing as in the stream: maqaf and sof pasuq attached,
paseq ׀ kept, petucha/setuma [פ]/[ס] as the TU's x-paragraph prop). The Globasa side is
translate.sh's output, matched by verse reference. CONTEXT (default: the book and
chapter of the first verse, e.g. "Genesis 1") goes into x-context, as in the project's
other TMX files (make_tmx.py: TMX 1.4, creationtool GlobasaLexiTools).
"""

import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

REF = re.compile(r"^\[([A-Za-z0-9]+)\.(\d+)\.(\d+)\]\s*")
UNIT = re.compile(r"\^([^/$]+)/[^$]*\$")
BOOKS = {"Gen": "Genesis", "Exod": "Exodus", "Lev": "Leviticus", "Num": "Numbers",
         "Deut": "Deuteronomy", "Ruth": "Ruth"}


def hebrew_verses(path):
    """{ref: (hebrew text, paragraph mark or '')} from the stream."""
    out = {}
    for line in open(path, encoding="utf-8"):
        m = REF.match(line)
        if not m:
            continue
        ref = f"{m.group(1)}.{m.group(2)}.{m.group(3)}"
        rest = line[m.end():].rstrip("\n")
        para = "petucha" if "[פ]" in rest else "setuma" if "[ס]" in rest else ""
        rest = re.sub(r"\s*\[[פס]\]", "", rest)
        rest = re.sub(r"\[(׀)\]", r"\1", rest)                   # paseq: kept as a character
        text = UNIT.sub(lambda u: u.group(1), rest)
        text = re.sub(r"\s+", " ", text).strip()
        out[ref] = (text, para)
    return out


def glb_verses(lines):
    out = {}
    for line in lines:
        m = REF.match(line)
        if m:
            out[f"{m.group(1)}.{m.group(2)}.{m.group(3)}"] = line[m.end():].strip()
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    heb = hebrew_verses(sys.argv[1])
    glb = glb_verses(sys.stdin)
    refs = list(heb)
    if not refs:
        sys.exit(f"tmx: no verses in {sys.argv[1]}")
    book, chap = refs[0].split(".")[:2]
    context = sys.argv[2] if len(sys.argv) > 2 else f"{BOOKS.get(book, book)} {chap}"

    tmx = ET.Element("tmx", version="1.4")
    ET.SubElement(tmx, "header", creationtool="GlobasaLexiTools", creationtoolversion="1.0",
                  datatype="plaintext", segtype="sentence", srclang="hbo", adminlang="en",
                  creationdate=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
                  **{"o-tmf": "GlobasaLexiTools"})
    body = ET.SubElement(tmx, "body")
    missing = []
    for ref in refs:
        text, para = heb[ref]
        tu = ET.SubElement(body, "tu", tuid=ref)
        ET.SubElement(tu, "prop", type="x-context").text = context
        ET.SubElement(tu, "prop", type="x-ref").text = ref
        ET.SubElement(tu, "prop", type="x-origin").text = "apertium-hbo-glb machine draft"
        if para:
            ET.SubElement(tu, "prop", type="x-paragraph").text = para
        for lang, seg in (("hbo", text), ("glb", glb.get(ref))):
            if seg is None:
                missing.append(ref)
                continue
            tuv = ET.SubElement(tu, "tuv", {"xml:lang": lang})
            ET.SubElement(tuv, "seg").text = seg
    if missing:
        print(f"tmx: no Globasa for {', '.join(missing)}", file=sys.stderr)
    ET.indent(tmx, space="  ")
    sys.stdout.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    sys.stdout.write(ET.tostring(tmx, encoding="unicode") + "\n")


if __name__ == "__main__":
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    main()
