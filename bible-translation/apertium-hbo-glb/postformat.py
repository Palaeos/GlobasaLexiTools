#!/usr/bin/env python3
"""Typography only: attach punctuation, capitalise sentence starts, drop
Masoretic marks except the paragraph sign [פ] (-> blank line).

Quotes (inferred by punctuation.py): `loga: “Am …” Ji …`, capital after “ and
after a closing stop. Curated marks (punctuation.py): `X — Y` spaced, `(X)`
attached inside; a dash before the verse's full stop replaces it, and the next
verse then goes on in lower case (one sentence across verses: Gen 1:1-2 in the
draft)."""

import re
import sys

cont = False                     # the previous verse ended in a dash
for line in sys.stdin:
    line = line.rstrip("\n")
    para = "[פ]" in line or "[ס]" in line
    line = re.sub(r"\s*\[[׀פס]\]", "", line)
    line = line.replace("¦", "")                      # clause boundary (syntax.py)
    line = re.sub(r"\s+([.,;:!?)])", r"\1", line)
    line = re.sub(r"([(“])\s+", r"\1", line)
    line = re.sub(r"\s+”", "”", line)
    line = re.sub(r"\s*—\s*", " — ", line)
    line = re.sub(r" — ([.,;:])", r" —", line)          # a dash replaces a following stop
    line = re.sub(r"\s+", " ", line).strip()
    start = r"^\[[^\]]+\] " if not cont else r"(?!)"
    line = re.sub(rf"({start}|[.!?]”? |“)([a-z])", lambda m: m.group(1) + m.group(2).upper(), line)
    if line.startswith("[") and "]" in line:
        cont = line.endswith("—")
    print(line + ("\n" if para else ""))
