# INKO e-book PDF (Franko Luin's eLIBRO series, Acrobat 4 era) -> plain text.
#   python3 inko_text.py <book.pdf> <out.txt>
# These PDFs use a legacy Esperanto font: the supersigned letters sit in
# Latin-1 slots, so pdftotext returns e.g. "voja¸anto" for vojaĝanto. The
# table below was read off La tempo-maŝino (2001); every slot was checked
# against words in context (ß = ŝ in poßo "pocket", ˛ = ĥ in e˛is "echoed").
# Running headers ("LA TEMPO-MAŜINO eLIBRO"), page numbers and line-end
# hyphenation are removed; paragraphs are kept (blank line between).
import re
import subprocess
import sys

MAP = str.maketrans({
    "¸": "ĝ", "¯": "Ĝ", "ç": "ĉ", "Ç": "Ĉ", "û": "ŭ", "ÿ": "ŝ", "Ÿ": "Ŝ", "ß": "ŝ",
    "î": "ĵ", "Î": "Ĵ", "˛": "ĥ", "ﬁ": "fi", "ﬂ": "fl", "”": '"', "’": "'",
})

pdf, out = sys.argv[1], sys.argv[2]
raw = subprocess.run(["pdftotext", pdf, "-"], capture_output=True, text=True, check=True).stdout
pages = raw.split("\f")
title = None
paras, cur = [], []
for page in pages:
    lines = page.translate(MAP).splitlines()
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if re.fullmatch(r"\d{1,3}", s) or s == "eLIBRO" or re.fullmatch(r"[A-ZĈĜĤĴŜŬ \-]+(eLIBRO)?", s):
            # running header / page number / all-caps title line
            if re.match(r"ĈAPITRO|EPILOGO", s):
                cur and paras.append(" ".join(cur)); cur = []
                paras.append("## " + s.title())
            continue
        if re.fullmatch(r"(Ĉapitro|Epilogo).*", s):
            cur and paras.append(" ".join(cur)); cur = []
            paras.append("## " + s)
            continue
        # a new paragraph begins with an indented line in the layout, which
        # plain pdftotext loses; use the opening quote or a dash after a
        # sentence end as the cue
        if cur and re.match(r'^["—]', s) and re.search(r'[.!?"…]$', cur[-1]):
            paras.append(" ".join(cur)); cur = []
        cur.append(s)
cur and paras.append(" ".join(cur))
text = "\n\n".join(paras)
text = re.sub(r"(\w)- (\w)", r"\1\2", text)   # line-end hyphenation (ido-\nojn)
open(out, "w", encoding="utf-8").write(text + "\n")
print(len(text.split()), "words,", sum(p.startswith("## ") for p in paras), "chapters")
