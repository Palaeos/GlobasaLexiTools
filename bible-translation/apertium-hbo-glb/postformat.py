#!/usr/bin/env python3
"""Typography only: attach punctuation, capitalise sentence starts, drop
Masoretic marks except the paragraph sign [פ] (-> blank line)."""

import re
import sys

for line in sys.stdin:
    line = line.rstrip("\n")
    para = "[פ]" in line or "[ס]" in line
    line = re.sub(r"\s*\[[׀פס]\]", "", line)
    line = re.sub(r"\s+([.,;:!?])", r"\1", line)
    line = re.sub(r"\s+", " ", line).strip()
    line = re.sub(r"(^\[[^\]]+\] |[.!?] )([a-z])", lambda m: m.group(1) + m.group(2).upper(), line)
    print(line + ("\n" if para else ""))
