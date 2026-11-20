# Fetch H. P. Lovecraft works for translation into Globasa from English Wikisource, one file per
# witness, as plain text ("## <title>" heading).
#   The Call of Cthulhu (written 1926): public domain in the US since 2024 (published 1928) and in
#   life+70 countries (Lovecraft died 1937)
#     text/call_of_cthulhu_weird_tales.txt  Weird Tales 11.2, February 1928: first publication, base
#   Wikisource lists two more witnesses but has not transcribed them (2026-11-20): Beware After
#   Dark! (Macaulay, 1929) and The Outsider and Others (Arkham House, 1939); add them to WITNESSES
#   once their pages exist.
# Not here: At the Mountains of Madness (Astounding Stories, 1936; issues renewed): under US
# copyright until 2032 per Wikisource; this repo takes only openly licensed / public-domain texts.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from wikisource_text import plain

OUT = Path(__file__).parent / "text"
WITNESSES = {
    "call_of_cthulhu_weird_tales": "Weird Tales/Volume 11/Issue 2/The Call of Cthulhu",
}

OUT.mkdir(exist_ok=True)
for name, page in WITNESSES.items():
    text = plain(page).strip()
    (OUT / f"{name}.txt").write_text(f"## {page}\n\n{text}\n", encoding="utf-8")
    print(name, len(text.split()), "words")
