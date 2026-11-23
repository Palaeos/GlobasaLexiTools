"""
Append "The Coming of Mr Quin" (Agatha Christie, 1924) excerpt to the TMX pair and the
master passages CSV, from the three-column table in
"Preata de Mansenyor Quin fal Agatha Christie.md":

  Original                 -> <tuv xml:lang="en">
  Translation              -> <tuv xml:lang="glb">
  Translation with notes   -> <tuv xml:lang="glb-x-fokus">  (the focus-tracking notes, inline:
                              [neo fokus: te], [dente → te], [fokus in logalari] ...)

The notes illustrate the den-/hin- reference-focus guidelines and are the gold for
glb-neural.py's focus stage (focus_eval.py). The CSV has no column for them, so it gets
glb + en only.

Run from the repo root; pass --write to apply, with no argument it prints the alignment for
review and touches nothing. New TUs go at the very end of <body> (the Word Viewer pairs TMX
entries with GIZA output by position); every existing TU stays byte-identical, as in
extend_tmx_doxo_2026_11.py. Refuses to run twice.
"""
import csv
import io
import os
import re
import shutil
import sys
from xml.sax.saxutils import escape

SOURCE = "Preata de Mansenyor Quin fal Agatha Christie.md"
TMX_FILES = ["Doxo_passages.tmx", "Doxo_passages_extended.tmx"]
CSV_FILE = "Doxo_passages_edited_updated.csv"
BACKUP_DIR = "backups/christie_2026-11-23"
CONTEXT = "Preata de Mansenyor Quin fal Agatha Christie"
FOKUS_LANG = "glb-x-fokus"

SENT_END = re.compile(r"(?<=[.!?…])([\"”’]?)\s+(?=[“\"‘—(A-ZÀ-Ý])")
TITLE = re.compile(r"^\*\*((?:[^*]|\*(?!\*))*)\*\*\*?\s*")
NOTE = re.compile(r"\s*\[[^\]]*\]")

# Sentence merges where the translation splits differently (0-based indices after splitting;
# applied from the end so earlier indices stay valid). Checked against the dry-run listing.
MERGE = {
    "en": [(40, 41),    # He knew all those things. + And it puzzled him.
           (24, 25)],   # Nothing unusual about Alex Portal. + The usual good sound English stock.
    "glb": [(23, 24)],  # Te laoje kriban caredes nyan ... + Te suki esportu ...
}


def cells():
    """The three table cells as (title, text) with paragraphs kept ("\\n\\n")."""
    with open(SOURCE, encoding="utf-8") as f:
        lines = f.read().splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("| :---")) + 1
    body = "\n".join(lines[start:]).strip().strip("|").strip()
    out = []
    for cell in re.split(r"\s\|\s", body):
        cell = cell.strip().replace("\\!", "!").replace("\\[", "[").replace("\\]", "]")
        m = TITLE.match(cell)
        title, cell = (m.group(1), cell[m.end():]) if m else ("", cell)
        if title.count("*") % 2:            # "**... fal *Agatha Christie***": the italics close too
            title += "*"
        paras = [p.strip() for p in cell.split("\n") if p.strip()]
        out.append((clean(title), clean("\n\n".join(paras))))
    if len(out) != 3:
        raise SystemExit(f"{SOURCE}: expected 3 table cells, found {len(out)}")
    return out


def clean(text):
    """Bold (the highlighted pronouns) goes; *italics* become _italics_ like existing TUs."""
    text = text.replace("**", "")
    text = re.sub(r"\*([^*\n]+)\*", r"_\1_", text)
    return re.sub(r"[ \t]+", " ", text).strip()


def split(text):
    out = []
    for para in text.split("\n\n"):
        last = 0
        for m in SENT_END.finditer(para):
            out.append(para[last:m.end()].strip())
            last = m.end()
        out.append(para[last:].strip())
    return [s for s in out if s]


def merged(sentences, merges):
    sentences = list(sentences)
    for a, b in sorted(merges, reverse=True):
        sentences[a:b + 1] = [" ".join(sentences[a:b + 1])]
    return sentences


def build_units():
    (en_title, en), (glb_title, glb), (fk_title, fk) = cells()
    en_s = merged(split(en), MERGE["en"])
    glb_s = merged(split(glb), MERGE["glb"])
    fk_s = merged(split(fk), MERGE["glb"])
    if not (len(en_s) == len(glb_s) == len(fk_s)):
        raise SystemExit(f"sentence counts differ: en {len(en_s)}, glb {len(glb_s)}, fokus {len(fk_s)}")
    for g, k in zip(glb_s, fk_s):
        if " ".join(NOTE.sub("", k).split()) != " ".join(g.split()):
            raise SystemExit(f"annotated sentence does not match the translation:\n  {g}\n  {k}")
    units = [(glb_title, en_title, fk_title)]
    units += list(zip(glb_s, en_s, fk_s))
    return units


def tu_xml(glb, en, fokus, entities):
    lines = ["    <tu>", f'      <prop type="x-context">{escape(CONTEXT, entities)}</prop>']
    for lang, text in (("glb", glb), ("en", en), (FOKUS_LANG, fokus)):
        lines += [f'      <tuv xml:lang="{lang}">',
                  f"        <seg>{escape(text, entities)}</seg>",
                  "      </tuv>"]
    lines.append("    </tu>\n")
    return "\n".join(lines)


def patched_tmx(path, units):
    with open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    if f'<prop type="x-context">{CONTEXT}</prop>' in text:
        raise SystemExit(f"{path} already contains {CONTEXT}; refusing to append twice")
    # Doxo_passages.tmx writes " as &quot;; the extended file writes it raw.
    entities = {'"': "&quot;"} if "&quot;" in text else {}
    cut = text.rindex("\n", 0, text.rindex("</body>")) + 1
    return text[:cut] + "".join(tu_xml(g, e, k, entities) for g, e, k in units) + text[cut:]


def patched_csv(units):
    with open(CSV_FILE, encoding="utf-8", newline="") as f:
        text = f.read()
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter="\t", lineterminator="\n")
    for glb, en, _ in units:
        writer.writerow([CONTEXT, glb, en])
    return text + buf.getvalue()


units = build_units()

if "--write" not in sys.argv:
    for n, (glb, en, fokus) in enumerate(units):
        print(f"{n:3d} en    {en}\n    glb   {glb}\n    fokus {fokus}\n")
    print(f"{len(units)} TUs. Dry run: nothing written.")
    sys.exit()

outputs = {path: patched_tmx(path, units) for path in TMX_FILES}
outputs[CSV_FILE] = patched_csv(units)
os.makedirs(BACKUP_DIR, exist_ok=True)
for path, content in outputs.items():
    shutil.copy2(path, BACKUP_DIR)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(content)
print(f"Appended {len(units)} TUs to {', '.join(outputs)}. Backups in {BACKUP_DIR}/")
