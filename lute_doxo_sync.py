"""Doxo -> Lute: keep a Lute library of the Doxo reader texts.

Run with Lute's own environment (setup: python3 -m venv venv-lute &&
venv-lute/bin/pip install lute3==3.10.3):

    venv-lute/bin/python lute_doxo_sync.py

then start Lute on the same data:

    venv-lute/bin/python -m lute.main --config LuteGlobasa/config.yml --local

Lute's data lives in LuteGlobasa/data/ (its database, the books' audio, backups).
The first run writes LuteGlobasa/config.yml for it and adds the Globasa language
from LuteGlobasa/globasa.yaml. Everything goes through Lute's own code (app
context, Language.from_dict, the book Repository), never into its database by hand.

What becomes a book: every ### section of a doxo-pages-grav page (a fable, a
story, a poem, a UDHR article) is a book of its own; a page with no sections
(Siri-logane Tutum) is one book. Index pages (links only) are skipped. The
two-column HTML page (Aselli Hikaye: Globasa | English) gives its left column.
Tags: doxo, the category folder (lilhikaye, poema, ...) and the page.

Audio: a section gets recordings only when their names point at it and at no
other section. First each file on its own, number included ("gdih mon 01" ->
the section "Mon 1."; a first word shared by all of a page's files and found in
no title, like "gdih", is dropped); then the rest as numbered parts of one
recording ("safe rubahe 01..08" -> "Safe Rubahe"). The parts are joined into one
MP3 in Lute's useraudio folder, with a Lute bookmark at the start of every part
(parts follow the reader's breath, not always the paragraphs). Anything less
certain is listed, not guessed: Vanege's "Kolor-okobimar Piu" and "Mitin de Piu"
both fit "piu 01..09" -- say which in AUDIO_FOR. Who reads the Doxo recordings
is not recorded here; Lute plays them, the Anki drills do not use them.

Sync: a book is added once. LuteGlobasa/data/doxo_sync.json remembers the text
each book was made from, so a later run reports texts Doxo has changed or
dropped -- it never edits or deletes a Lute book, which would lose its reading
state. Update the submodule first: git submodule update --remote doxo-pages-grav
"""
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import tempfile

import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
LUTE_DIR = os.path.join(ROOT, "LuteGlobasa")
DATA = os.path.join(LUTE_DIR, "data")
CONFIG = os.path.join(LUTE_DIR, "config.yml")
LANG_YAML = os.path.join(LUTE_DIR, "globasa.yaml")
MANIFEST = os.path.join(DATA, "doxo_sync.json")
DOXO = os.path.join(ROOT, "doxo-pages-grav")
# Grav drops the numeric folder prefixes from URLs (01.folklorli-hikaye ->
# /folklorli-hikaye). The host is assumed by analogy with xwexi.globasa.net.
DOXO_URL = "https://doxo.globasa.net"
PAGE_FILE = "default.eng.md"
MIN_WORDS = 40          # shorter pages (and untitled page intros) are index pages / notes
# Recordings whose section the names cannot settle: {page folder: {recording base
# name: section title}}. E.g. {"02.lilhikaye/03.hikaye-fal-vanege": {"piu": "Kolor-okobimar Piu"}}
AUDIO_FOR = {}
LANGUAGE = "Globasa"
DRY_RUN = False         # True: report what would happen, change nothing


# ---- reading the pages ----

def front_matter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}, text
    return yaml.safe_load(m.group(1)) or {}, text[m.end():]


def two_column_to_markdown(body):
    """Aselli Hikaye: rows of <div display:table> with a Globasa and an English
    cell. Keep the Globasa cell; a bold row is a title (the first, the page's)."""
    rows = re.findall(r'<div style="display: table;([^"]*)">\s*<div style="display: table-cell;[^"]*">(.*?)</div>',
                      body, re.S)
    out, first = [], True
    for style, cell in rows:
        cell = cell.strip()
        if "font-weight: bold" in style:
            if first:
                first = False
                continue
            out.append(f"### {cell}")
        else:
            out.append(cell)
    return "\n\n".join(out)


def clean(text):
    """Markdown/HTML to plain reading text; line breaks kept (poems)."""
    text = re.sub(r"<audio.*?</audio>", "", text, flags=re.S)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)            # images
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)         # links -> their text
    text = re.sub(r"<[^>]+>", "", text)                           # other HTML
    text = html.unescape(text)
    text = re.sub(r"^#{4,6}\s*", "", text, flags=re.M)            # minor headings -> plain lines
    text = re.sub(r"^>\s?", "", text, flags=re.M)                 # quotes
    text = re.sub(r"(\*\*|__)(.+?)\1", r"\2", text)              # bold
    text = re.sub(r"(?<![\w*])[*_](?!\s)(.+?)(?<!\s)[*_](?![\w*])", r"\1", text)   # italics
    text = re.sub(r"[ \t]+\n", "\n", text)                        # trailing spaces (poem line breaks)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def paragraphs(text):
    return [p for p in re.split(r"\n\s*\n", text) if p.strip()]


def words(text):
    return re.findall(r"[a-zA-Z]+", text)


def page_url(rel_dir):
    parts = [re.sub(r"^\d+\.", "", p) for p in rel_dir.split(os.sep)]
    return DOXO_URL + "/" + "/".join(parts)


def norm_words(s):
    """Lowercase words, numbers without leading zeros ('01' and '1' agree)."""
    return {str(int(w)) if w.isdigit() else w for w in re.sub(r"[^a-z0-9]+", " ", s.lower()).split()}


def audio_groups(page_dir):
    """{base name: [(number or None, filename)]} -- 'safe rubahe 01.mp3' ->
    ('safe rubahe', 1); 'dragon ji panda 2.5.mp3' sorts between 2 and 3."""
    groups = {}
    for fn in os.listdir(page_dir):
        stem, ext = os.path.splitext(fn)
        if ext.lower() != ".mp3":
            continue
        m = re.match(r"^(.*?)\s+(\d+(?:\.\d+)?)$", stem)
        base, num = (m.group(1), float(m.group(2))) if m else (stem, None)
        groups.setdefault(base.lower().strip(), []).append((num, fn))
    for base in groups:
        groups[base].sort(key=lambda x: (x[0] is None, x[0] or 0))
    return groups


def read_page(path):
    """[(section title or None, text)] of one page, and the page's metadata."""
    raw = open(path, encoding="utf-8").read()
    meta, body = front_matter(raw)
    if "display: table-cell" in body:
        body = two_column_to_markdown(body)
    parts = re.split(r"^###\s+(.+?)\s*$", body, flags=re.M)
    sections = []
    intro = clean(parts[0])
    if len(parts) == 1:
        sections.append((None, intro))
    else:
        if len(words(intro)) >= MIN_WORDS:
            sections.append((None, intro))
        for title, text in zip(parts[1::2], parts[2::2]):
            sections.append((title.strip(), clean(text)))
    return meta, sections


def match_audio(sections, groups, overrides):
    """{section index: [files in order]} where the names settle it; notes on the rest."""
    titled = [(i, norm_words(t)) for i, (t, _) in enumerate(sections)]
    all_title_words = set().union(*[tw for _, tw in titled]) if titled else set()
    stems = [(base, num, fn) for base, items in groups.items() for num, fn in items]
    firsts = {base.split()[0] for base, _, _ in stems if base.split()}
    prefix = firsts.pop() if len(firsts) == 1 and not (firsts & all_title_words) else None

    def words_of(base, num=None):
        w = norm_words(base) - ({prefix} if prefix else set())
        if num is not None and float(num).is_integer():
            w = w | {str(int(num))}
        return w

    def fits(w):
        return [i for i, tw in titled if w and w <= tw]

    claims = {}   # section index -> [(label, [files])]
    notes = []
    leftover = {}
    # 1. A file on its own, its number naming the section ("mon 01" -> "Mon 1.").
    for base, num, fn in stems:
        hit = fits(words_of(base, num)) if num is not None else []
        names_section = len(hit) == 1 and float(num).is_integer() and str(int(num)) in titled[hit[0]][1]
        if names_section:
            claims.setdefault(hit[0], []).append((fn, [fn]))
        else:
            leftover.setdefault(base, []).append((num, fn))
    # 2. The rest: a recording in numbered parts, or one file, named after its section.
    titles = {t.lower(): i for i, (t, _) in enumerate(sections)}
    for base, items in sorted(leftover.items()):
        files = [fn for _, fn in sorted(items, key=lambda x: (x[0] is None, x[0] or 0))]
        forced = overrides.get(base)
        hit = [titles[forced.lower()]] if forced and forced.lower() in titles else fits(words_of(base))
        if len(hit) != 1:
            notes.append(f"'{base}' ({len(files)} file(s)) fits {len(hit)} sections: left out")
            continue
        claims.setdefault(hit[0], []).append((base, files))
    assigned = {}
    for i, cl in claims.items():
        if len(cl) != 1:
            notes.append(f"section '{sections[i][0]}' is claimed by {[c[0] for c in cl]}: left out")
            continue
        assigned[i] = cl[0][1]
    return assigned, notes


def collect_books():
    books, notes = [], []
    for dirpath, _, filenames in sorted(os.walk(DOXO)):
        if PAGE_FILE not in filenames or "/.git" in dirpath:
            continue
        rel = os.path.relpath(dirpath, DOXO)
        meta, sections = read_page(os.path.join(dirpath, PAGE_FILE))
        page_title = str(meta.get("title", rel)).strip()
        # Untitled text before the first section is a note or an index unless long.
        texts = [(t, x) for t, x in sections if words(x) and (t is not None or len(words(x)) >= MIN_WORDS)]
        if not texts or sum(len(words(x)) for _, x in texts) < MIN_WORDS:
            continue
        # A page whose only text has no title of its own is one book named after the page.
        sections = [(t or page_title, x) for t, x in texts]
        assigned, page_notes = match_audio(sections, audio_groups(dirpath), AUDIO_FOR.get(rel, {}))
        notes += [f"{rel}: {n}" for n in page_notes]
        category = re.sub(r"^\d+\.", "", rel.split(os.sep)[0])
        page_slug = re.sub(r"^\d+\.", "", rel.split(os.sep)[-1])
        for i, (title, text) in enumerate(sections):
            books.append({
                "title": title if title == page_title else f"{title} · {page_title}",
                "text": text,
                "url": page_url(rel),
                "tags": sorted({"doxo", category, page_slug}),
                "audio": [os.path.join(dirpath, f) for f in assigned.get(i, [])],
                "source": f"{rel}#{title}",
                "hash": hashlib.sha1(text.encode()).hexdigest(),
            })
    return books, notes


# ---- audio ----

def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", path], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def build_audio(book, audio_dir):
    """One MP3 in Lute's useraudio folder; bookmarks at each part after the first."""
    slug = re.sub(r"[^a-z0-9]+", "-", book["source"].lower()).strip("-")
    name = f"doxo-{slug}.mp3"
    target = os.path.join(audio_dir, name)
    parts = book["audio"]
    starts, t = [], 0.0
    for p in parts:
        starts.append(t)
        t += duration(p)
    if len(parts) == 1:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", parts[0], "-c:a", "copy", target], check=True)
    else:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as lst:
            for p in parts:
                lst.write("file '" + p.replace("'", "'\\''") + "'\n")
        try:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst.name,
                            "-c:a", "libmp3lame", "-q:a", "4", target], check=True)
        finally:
            os.unlink(lst.name)
    bookmarks = ";".join(f"{s:.2f}" for s in starts[1:]) or None
    return name, bookmarks


# ---- Lute ----

def ensure_config():
    if os.path.exists(CONFIG):
        return
    os.makedirs(DATA, exist_ok=True)
    with open(CONFIG, "w", encoding="utf-8") as f:
        f.write("# Written by lute_doxo_sync.py: a Lute instance for Globasa, data in LuteGlobasa/data.\n"
                f"ENV: prod\nDBNAME: lute.db\nDATAPATH: {DATA}\nBACKUP_PATH: {os.path.join(DATA, 'backups')}\n")
    print(f"wrote {os.path.relpath(CONFIG, ROOT)}")


def main():
    books, notes = collect_books()
    ensure_config()
    from lute.app_factory import create_app
    from lute.book.model import Book, Repository
    from lute.db import db
    from lute.models.language import Language
    from lute.models.repositories import LanguageRepository

    app = create_app(CONFIG)
    manifest = json.load(open(MANIFEST, encoding="utf-8")) if os.path.exists(MANIFEST) else {}
    with app.app_context():
        langs = LanguageRepository(db.session)
        lang = langs.find_by_name(LANGUAGE)
        if lang is None:
            with open(LANG_YAML, encoding="utf-8") as f:
                lang = Language.from_dict(yaml.safe_load(f))
            if not DRY_RUN:
                db.session.add(lang)
                db.session.commit()
            print(f"added the {LANGUAGE} language from {os.path.relpath(LANG_YAML, ROOT)}")
        repo = Repository(db.session)
        audio_dir = app.env_config.useraudiopath
        added, same, changed, foreign = [], [], [], []
        for b in books:
            existing = repo.find_by_title(b["title"], lang.id) if lang.id else None
            seen = manifest.get(b["title"])
            if existing is not None:
                if seen is None:
                    foreign.append(b["title"])
                elif seen["hash"] != b["hash"]:
                    changed.append(b["title"])
                else:
                    same.append(b["title"])
                continue
            book = Book()
            book.language_name = LANGUAGE
            book.title = b["title"]
            book.text = b["text"]
            book.source_uri = b["url"]
            book.book_tags = b["tags"]
            if b["audio"] and not DRY_RUN:
                book.audio_filename, book.audio_bookmarks = build_audio(b, audio_dir)
            if not DRY_RUN:
                repo.add(book)
                repo.commit()
                manifest[b["title"]] = {"hash": b["hash"], "source": b["source"], "url": b["url"],
                                        "audio": [os.path.relpath(p, DOXO) for p in b["audio"]]}
            added.append(b["title"] + (f"  [audio: {len(b['audio'])} file(s)]" if b["audio"] else ""))
        gone = sorted(set(manifest) - {b["title"] for b in books})
    if not DRY_RUN:
        with open(MANIFEST, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=1, sort_keys=True)

    prefix = "would add" if DRY_RUN else "added"
    print(f"\n{len(books)} Doxo texts: {len(added)} {prefix}, {len(same)} unchanged, "
          f"{len(changed)} changed in Doxo, {len(foreign)} already in Lute from elsewhere, {len(gone)} gone from Doxo")
    for t in added:
        print(f"  + {t}")
    for label, items in (("changed in Doxo since import (Lute book left as it is)", changed),
                         ("same title already in Lute, not made by this sync (left alone)", foreign),
                         ("no longer in Doxo (Lute book left as it is)", gone)):
        if items:
            print(f"\n{label}:")
            for t in items:
                print(f"  ~ {t}")
    if notes:
        print("\naudio not attached (match not certain):")
        for n in notes:
            print(f"  - {n}")


main()
