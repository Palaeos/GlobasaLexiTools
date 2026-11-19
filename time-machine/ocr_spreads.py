# OCR a scanned translation whose PDF pages are two-page spreads.
#   python3 ocr_spreads.py <scan.pdf> <lang> <out.txt> [first_pdf_page [last_pdf_page]]
# Each PDF page is rendered at 300 dpi and split at its vertical gutter (the
# lightest column band near the middle); each half is OCRed with tesseract
# (psm 4) using models from cache/tessdata. Output: one "=== p<n>" marker per
# book page, running headers (page numbers, "— 10 —") and scanner watermarks
# dropped, words hyphenated across lines rejoined. Texts stay in cache/
# (git-ignored); only this machinery is committed.
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageOps

HERE = Path(__file__).parent
TESSDATA = HERE / "cache" / "tessdata"
pdf, lang, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
first = int(sys.argv[4]) if len(sys.argv) > 4 else 1
last = int(sys.argv[5]) if len(sys.argv) > 5 else None

npages = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
WATERMARK = re.compile(r"h\w*t\w*p\S*win10\S*|win10\.io", re.I)
RUNNING = re.compile(r"^\s*[—–\-~_.,'\"]*\s*\d{1,3}\s*[—–\-~_.,'\"]*\s*$")


def gutter(im):
    g = ImageOps.grayscale(im)
    w, h = g.size
    lo, hi = int(w * 0.40), int(w * 0.60)
    px = g.load()
    best, bx = -1, w // 2
    for x in range(lo, hi, 2):
        s = sum(px[x, y] for y in range(int(h * 0.15), int(h * 0.85), 6))
        if s > best:
            best, bx = s, x
    return bx


def text_block(img):
    # grayscale + contrast, then crop to the rows/columns that hold ink,
    # ignoring a 5% border top and bottom, 1% at the sides (text runs close
    # to the gutter)
    g = ImageOps.autocontrast(ImageOps.grayscale(img), cutoff=1)
    w, h = g.size
    bw = g.point(lambda v: 0 if v < 110 else 255)
    px = bw.load()
    bx0, by0, bx1, by1 = int(w * .01), int(h * .05), int(w * .99), int(h * .95)
    cols = [x for x in range(bx0, bx1, 3) if sum(px[x, y] == 0 for y in range(by0, by1, 4)) > (by1 - by0) / 4 * .02]
    rows = [y for y in range(by0, by1, 3) if sum(px[x, y] == 0 for x in range(bx0, bx1, 4)) > (bx1 - bx0) / 4 * .01]
    if not cols or not rows:
        return g
    m = 20
    return g.crop((max(cols[0] - m, 0), max(rows[0] - m, 0), min(cols[-1] + m, w), min(rows[-1] + m, h)))


def ocr(img, tmp):
    p = os.path.join(tmp, "half.png")
    text_block(img).save(p)
    env = dict(os.environ, TESSDATA_PREFIX=str(TESSDATA))
    r = subprocess.run(["tesseract", p, "-", "-l", lang, "--psm", "4"], capture_output=True, text=True, env=env)
    return r.stdout


def clean(text):
    lines = []
    for ln in text.splitlines():
        ln = WATERMARK.sub("", ln).rstrip()
        if RUNNING.match(ln):
            continue
        lines.append(ln)
    t = "\n".join(lines)
    t = re.sub(r"(\w)[-¬]\n\s*(\w)", r"\1\2", t)          # rejoin hyphenation
    t = re.sub(r"(?<!\n)\n(?!\n)", " ", t)                # unwrap lines
    t = re.sub(r"[ \t]+", " ", t)
    return t.strip()


with tempfile.TemporaryDirectory() as tmp, open(out, "w", encoding="utf-8") as f:
    book = 0
    for n in range(first, (last or npages) + 1):
        base = os.path.join(tmp, "pg")
        subprocess.run(["pdftoppm", "-r", "300", "-f", str(n), "-l", str(n), "-png", "-singlefile", pdf, base], check=True)
        im = Image.open(base + ".png")
        x = gutter(im)
        for half in (im.crop((0, 0, x, im.height)), im.crop((x, 0, im.width, im.height))):
            book += 1
            f.write(f"=== p{n}.{book}\n{clean(ocr(half, tmp))}\n\n")
        f.flush()
        print(n, end=" ", flush=True)
print()
