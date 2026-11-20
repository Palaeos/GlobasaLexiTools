# Short works of H. G. Wells for translation into Globasa, as plain text ("## <title>" headings).
#   text/man_of_the_year_million.txt  "The Man of the Year Million" (Pall Mall Budget, 1893), the
#       big-headed, large-eyed, hairless future human behind the later "grey alien" figure; text
#       of Wells's 1897 reprint "Of a Book Unwritten" in Certain Personal Matters (Project
#       Gutenberg, already fetched by time-machine/fetch_sources.py). The 1893 magazine text is
#       not on Wikisource or Gutenberg; it is the second witness to look for.
import re
from pathlib import Path

HERE = Path(__file__).parent
SOURCE = HERE.parent / "time-machine" / "sources" / "wells_certain_personal_matters.txt"
WORKS = {"man_of_the_year_million": ("OF A BOOK UNWRITTEN", "THE EXTINCTION OF MAN",
                                     "The Man of the Year Million (1893; reprinted 1897 as Of a Book Unwritten)")}

lines = SOURCE.read_text(encoding="utf-8").split("\n")
for name, (start, end, title) in WORKS.items():
    # the body heading is the second occurrence (the first is the table of contents)
    a = [i for i, l in enumerate(lines) if l.strip() == start][-1]
    b = next(i for i in range(a + 1, len(lines)) if lines[i].strip() == end)
    body = "\n".join(lines[a + 1:b]).strip()
    body = re.sub(r"(?<!\n)\n(?!\n)", " ", body)          # unwrap Gutenberg line breaks
    (HERE / "text").mkdir(exist_ok=True)
    (HERE / "text" / f"{name}.txt").write_text(f"## {title}\n\n{body}\n", encoding="utf-8")
    print(name, len(body.split()), "words")
