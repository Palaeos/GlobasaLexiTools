#!/usr/bin/env python3
"""Prepare an apertium-hbo passage stream (Hebrew-side bin/passage output) for
the hbo-glb transfer:  stdin -> stdout.

- keeps the first reading of each unit (readings are ordered by parsimony;
  the alternatives are documented in the ambiguity report);
- removes word-anchor tags <id:N> (kept in the source file for alignment);
- drops what Globasa does not render: the article ה<det>, maqaf ־<hyph>, the
  object marker את (rendering.md: Prepositions);
- drops a verse-initial ו: wa is a natural-language connective whose reading
  is set by context (Isaksson, The Verb in Classical Hebrew, pp. 79-80), and a
  new storyline step is a new Globasa sentence (Doxo: sentence-initial Ji in
  84 of 2337 sentences); specific links ("then", "so", "so that") are chosen
  per clause type in the revision (rendering.md: Clause linkage);
- retags verb forms so transfer patterns cannot confuse them: wayyiqtol
  <impf>…<consec> -> <wayy>…<consec>, weqatal <perf>…<consec> -> <weqt>…<consec>,
  jussive <impf>…<jus> -> …<jus> (rtx tag patterns cannot say "not consec");
  likewise a pronoun suffixed to a noun or numeral gets <psuf> (possessive:
  בְּצַלְמוֹ "in his image"; suffixes on prepositions and verbs are not
  possessive), and a numeral not in the construct state gets <abs> (postposed
  יוֹם אֶחָד "day one" vs construct שְׁנֵי הַמְּאֹרֹת "the two lights");
- outputs the analysis only (as a tagger would), NFC-normalised: the stream
  writes שׁ as U+FB2A, the bidix as U+05E9 U+05C1;
- verse references and Masoretic marks in [...] stay as superblanks.
"""

import re
import sys
import unicodedata

UNIT = re.compile(r"\^([^/$]+)/([^$]+)\$")


def first_reading(m):
    surf, readings = m.group(1), m.group(2)
    rd = unicodedata.normalize("NFC", re.sub(r"<id:\d+>", "", readings.split("/")[0]))
    parts = [p for p in rd.split("+")
             if not re.match(r"[^<]*<det>", p) and not p.startswith("את<pr>")]
    if not parts or re.match(r"[^<]*<hyph>", parts[0]):
        return ""
    parts = [retag(p) for p in parts]
    for i in range(1, len(parts)):
        if "<prn>" in parts[i] and re.match(r"[^<]*<(n|num)>", parts[i - 1]):
            parts[i] += "<psuf>"
    parts = [p + "<abs>" if re.match(r"[^<]*<num>", p) and "<cons>" not in p else p
             for p in parts]
    return "^" + "+".join(parts) + "$"


def retag(p):
    if "<consec>" in p:
        p = p.replace("<impf>", "<wayy>").replace("<perf>", "<weqt>")
    if "<jus>" in p:
        p = p.replace("<impf>", "")
    return p


VERSE_WA = re.compile(r"^(\[[^\]]+\] )\^ו<cnjcoo>\+")   # still fused: ^ו+X$

for line in sys.stdin:
    out = UNIT.sub(first_reading, line.rstrip("\n"))
    out = VERSE_WA.sub(r"\1^", re.sub(r"  +", " ", out).replace("$^", "$ ^"))
    print(out)
