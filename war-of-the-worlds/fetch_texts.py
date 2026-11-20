# Fetch The War of the Worlds (Heinemann, London, 1898: the first book edition, proofread from
# scans on English Wikisource) as plain text, chapters in reading order.
#   text/heinemann.txt  base text (Book I "The Coming of the Martians", Book II "The Earth under
#                       the Martians"); one "## Book N/Chapter M" heading per chapter
#   text/atlantic.txt   second witness: The Works of H. G. Wells, Atlantic Edition, vol. 3 (1924),
#                       revised by Wells; chapters numbered 1-27 straight through. The Wikisource
#                       scan of the 1898 edition ends at Book II ch. 9 "Wreckage" ("THE END"), so the
#                       Epilogue (Atlantic ch. 27) comes from this witness only.
# The Pearson's Magazine serial (April-December 1897) is not transcribed on Wikisource.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from wikisource_text import fetch_edition

OUT = Path(__file__).parent / "text"
# the index page lists the chapters only inside transcluded scan pages: follow "next" links
fetch_edition("The War of the Worlds (1898)", OUT / "heinemann.txt",
              first="The War of the Worlds (1898)/Book 1/Chapter 1")
fetch_edition("The Works of H. G. Wells (Atlantic Edition)/The War of the Worlds", OUT / "atlantic.txt",
              first="The Works of H. G. Wells (Atlantic Edition)/The War of the Worlds/Chapter 1")
