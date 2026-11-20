# Fetch three editions of The Time Machine from English Wikisource as plain text, one file per
# edition, chapters in reading order.
#   text/heinemann.txt  (UK, Heinemann 1895) — base text
#   text/holt.txt       (US, Holt 1895)      — second witness
#   text/atlantic.txt   (Atlantic Edition, The Works of H. G. Wells vol. 1, 1924) — third witness:
#                       Wells's own late revision, for plain-language paraphrases (user 2026-11-20)
# Chapter order is read from the edition's rendered table of contents, not
# from the (alphabetical) link list.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from wikisource_text import fetch_edition  # shared with war-of-the-worlds/fetch_texts.py

OUT = Path(__file__).parent / "text"
ATLANTIC = "The Works of H. G. Wells (Atlantic Edition)/The Time Machine"
EDITIONS = {                       # key: (index page, first chapter when the TOC has no links)
    "heinemann": ("The Time Machine (Heinemann text)", None),
    "holt": ("The Time Machine (Holt text)", None),
    "atlantic": (ATLANTIC, ATLANTIC + "/Chapter 1"),
}

for key, (index, first) in EDITIONS.items():
    fetch_edition(index, OUT / f"{key}.txt", first=first)
