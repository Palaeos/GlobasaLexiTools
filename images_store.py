"""Shared store for per-sense word images (menalariImages.jsonl).

Replaces the single-image `menalariImages_edited.csv`. Two things changed:

1. **Hierarchy.** A word has parts of speech, a part of speech has senses, and a
   sense has any number of images: word -> PoS -> sense -> images. A `b`-class
   word is a noun *and* a verb, and those want different pictures (`acum` is a
   sneeze and to sneeze). The store keeps this flat, with `pos` as a field on
   each sense, and groups by `pos` at render time.

2. **Identity, not rendering, is stored.** Wikimedia no longer renders arbitrary
   thumbnail widths on upload.wikimedia.org — it serves only widths already in
   cache — so a stored `.../thumb/.../553px-Foo.svg.png` URL rots. We keep the
   canonical file title instead and treat every URL as a regenerable cache;
   `resolve_commons_images.py` refills it from the Commons API.

Record shape, one JSON object per line::

    {"word": "acum", "senses": [
      {"pos": "n", "label": "a sneeze", "images": [
        {"file": "Sneeze.JPG", "wiki": "commons", "kind": "still",
         "source_page": "https://commons.wikimedia.org/wiki/File:Sneeze.JPG",
         "direct_url": "https://thumb.wikimedia.org/.../500px-Sneeze.JPG",
         "width": 500, "resolved": "2026-09-01", "status": "ok"}]},
      {"pos": "v.tr", "label": "", "images": [...]}]}

An image carries EITHER `file` + `wiki` (Wikimedia-hosted, resolvable) OR a
literal `url` (Giphy, math renders — carried through untouched, never resolved).

Unknown keys round-trip untouched, on the word record, on a sense and on an
image. Hand-added fields (`illustratable`, `note`, `derive`, `exclude`) must
survive every writer that doesn't know about them.
"""
import json
import os
import re
import urllib.parse

IMAGES_JSONL = "menalariImages.jsonl"

DEFAULT_WIDTH = 500

# Wikimedia project prefix (as it appears in upload.wikimedia.org paths) -> host.
WIKI_HOSTS = {
    "commons": "commons.wikimedia.org",
    "en": "en.wikipedia.org",
    "species": "species.wikimedia.org",
}

GIF_EXTS = (".gif",)

# https://upload.wikimedia.org/wikipedia/<wiki>/thumb/a/af/<File>/500px-<File>.png
_THUMB_RE = re.compile(
    r"^https?://(?:upload|thumb)\.wikimedia\.org/wikipedia/(\w+)"
    r"/thumb/[0-9a-f]/[0-9a-f]{2}/([^/]+)/[^/]+$"
)
# https://upload.wikimedia.org/wikipedia/<wiki>/a/af/<File>
_ORIG_RE = re.compile(
    r"^https?://(?:upload|thumb)\.wikimedia\.org/wikipedia/(\w+)"
    r"/[0-9a-f]/[0-9a-f]{2}/([^/?#]+)$"
)
# https://commons.wikimedia.org/wiki/Special:FilePath/<Title>?width=500
_FILEPATH_RE = re.compile(
    r"^https?://([a-z-]+)\.(?:wikimedia|wikipedia)\.org/wiki/Special:FilePath/([^?#]+)"
)
# https://commons.wikimedia.org/wiki/File:<Title>  (also en.wikipedia, species.)
_FILEPAGE_RE = re.compile(
    r"^https?://([a-z-]+)\.(?:wikimedia|wikipedia)\.org/wiki/File:([^?#]+)$"
)


def _norm_title(raw):
    """Percent-decode and normalise a file title (spaces -> underscores)."""
    return urllib.parse.unquote(raw).replace(" ", "_").strip()


def _norm_wiki(wiki):
    """species.wikimedia.org shows Commons files through InstantCommons, and
    `commons` is the default repository, so both land on Commons."""
    return "commons" if wiki in ("species", "commons") else wiki


def parse_commons_url(url):
    """Return (wiki, file_title) for a Wikimedia URL, or None if unresolvable.

    Handles the four forms seen in the wild: upload/thumb rendering URLs, upload
    originals, `Special:FilePath` links, and `/wiki/File:` pages. Giphy links and
    the `wikimedia.org/api/rest_v1` math endpoint return None on purpose — they
    have no canonical title, so they are stored as literal `url` entries.
    """
    if not url or not url.startswith(("http://", "https://")):
        return None

    m = _THUMB_RE.match(url) or _ORIG_RE.match(url)
    if m:
        return _norm_wiki(m.group(1)), _norm_title(m.group(2))

    m = _FILEPATH_RE.match(url) or _FILEPAGE_RE.match(url)
    if m:
        return _norm_wiki(m.group(1)), _norm_title(m.group(2))

    return None


def wiki_host(wiki):
    return WIKI_HOSTS.get(wiki, "commons.wikimedia.org")


def api_endpoint(wiki):
    return f"https://{wiki_host(wiki)}/w/api.php"


def filepath_url(file, wiki="commons", width=DEFAULT_WIDTH):
    """Durable Special:FilePath URL — always resolves, follows renames, and is
    immune to the thumbnail-width restriction that broke the stored URLs."""
    quoted = urllib.parse.quote(file, safe="")
    base = f"https://{wiki_host(wiki)}/wiki/Special:FilePath/{quoted}"
    return f"{base}?width={width}" if width else base


def file_page_url(file, wiki="commons"):
    return f"https://{wiki_host(wiki)}/wiki/File:{urllib.parse.quote(file, safe='')}"


def best_url(img, width=DEFAULT_WIDTH):
    """The URL a consumer should render. Single place that decides."""
    if img.get("direct_url"):
        return img["direct_url"]
    if img.get("file"):
        return filepath_url(img["file"], img.get("wiki", "commons"), width)
    return img.get("url", "")


def source_page(img):
    if img.get("source_page"):
        return img["source_page"]
    if img.get("file"):
        return file_page_url(img["file"], img.get("wiki", "commons"))
    return img.get("url", "")


def guess_kind(name):
    """`still` or `gif`, from a file title or URL."""
    base = (name or "").split("?")[0].lower()
    return "gif" if base.endswith(GIF_EXTS) else "still"


def make_image(url=None, file=None, wiki="commons", src_page=None, kind=None):
    """Build an image record from either a canonical title or a literal URL."""
    img = {}
    if file:
        img["file"] = file
        img["wiki"] = wiki
    else:
        img["url"] = url
    img["kind"] = kind or guess_kind(file or url)
    if src_page:
        img["source_page"] = src_page
    img["status"] = "unresolved"
    return img


def image_key(img):
    """Identity used to dedupe within a word."""
    if img.get("file"):
        return ("file", img.get("wiki", "commons"), img["file"])
    return ("url", img.get("url", ""))


def image_keys(img):
    """Every identity this image answers to: the canonical one plus any title it
    was renamed away from (`aka`). Matching against an outside source that has
    not caught up -- the Anki deck still holding a pre-rename URL -- needs these,
    or the same picture is adopted twice under two names."""
    keys = {image_key(img)}
    wiki = img.get("wiki", "commons")
    for old in img.get("aka") or []:
        keys.add(("file", wiki, old))
    return keys


def make_sense(pos="", label="", images=None):
    return {"pos": pos, "label": label, "images": list(images or [])}


def word_pos_keys(english_gloss):
    """The annotation keys of a word's English gloss, in order, deduplicated.

    `"n: alphabet, ABCs; v.tr: alphabetize"` -> `["n", "v.tr"]`. This is the
    vocabulary the `pos` field on a sense uses. Segments with no annotation
    contribute `""`, which is also what an unassigned sense carries.

    Reuses `Lexilista_parser._parse_annotation_prefix` — the canonical
    implementation — imported lazily so this module stays stdlib-only for
    consumers that only need the URL and JSONL helpers.
    """
    from Lexilista_parser import _parse_annotation_prefix

    keys = []
    for seg in (english_gloss or "").strip().split("; "):
        if not seg.strip():
            continue
        prefix, _gloss, _qualifier = _parse_annotation_prefix(seg)
        key = prefix or ""
        if key not in keys:
            keys.append(key)
    return keys


# ---------- reading a record ----------

def senses_of(record):
    return (record or {}).get("senses") or []


def all_images(record):
    """Every image in the word, in document order."""
    return [img for sense in senses_of(record) for img in sense.get("images") or []]


def usable(images):
    """Images worth showing. Drops the ones the API reported as gone — a dead
    URL on a card or in a gallery is worse than an empty slot."""
    return [i for i in images or [] if i.get("status") != "missing"]


def stills(images):
    return [i for i in usable(images) if i.get("kind") != "gif"]


def gifs(images):
    return [i for i in usable(images) if i.get("kind") == "gif"]


def pos_groups(record):
    """[(pos, [sense, ...]), ...] in first-appearance order.

    First-appearance order matches `word-list.csv` segment order, and therefore
    the PoS1/PoS2 fields on the Anki note.
    """
    groups = {}
    order = []
    for sense in senses_of(record):
        pos = sense.get("pos", "") or ""
        if pos not in groups:
            groups[pos] = []
            order.append(pos)
        groups[pos].append(sense)
    return [(pos, groups[pos]) for pos in order]


def is_illustratable(obj):
    """False only when explicitly marked. Applies to a word record or a sense."""
    return (obj or {}).get("illustratable", True) is not False


def anki_slots(record, width=DEFAULT_WIDTH):
    """Map the store onto the notetype's fixed image fields.

    One still per PoS group, in PoS-group order, into the two still slots —
    mirroring the PoS1/Mena1 and PoS2/Mena2 pairs printed beside them on the
    card. PoS groups with no still are skipped rather than consuming a slot, so
    `acum` (noun photo + verb GIF) fills slot 1 and the GIF slot, leaving slot 2
    empty. The first GIF anywhere in the word fills the animation slot.

    Returns a dict of the six field values, empty strings where unfilled.
    """
    picks = []
    for _pos, senses in pos_groups(record):
        for sense in senses:
            group_stills = stills(sense.get("images"))
            if group_stills:
                picks.append(group_stills[0])
                break
        if len(picks) == 2:
            break

    animation = next(iter(gifs(all_images(record))), None)

    out = {"Imajelinku": "", "ImajeAsel": "",
           "DuayumImaje": "", "DuayumImajeAsel": "",
           "Faleanimalinku": "", "Faleanimaasel": ""}
    names = [("Imajelinku", "ImajeAsel"), ("DuayumImaje", "DuayumImajeAsel")]
    for (url_field, src_field), img in zip(names, picks):
        out[url_field] = best_url(img, width)
        out[src_field] = source_page(img)
    if animation is not None:
        out["Faleanimalinku"] = best_url(animation, width)
        out["Faleanimaasel"] = source_page(animation)
    return out


# ---------- JSONL I/O ----------

def load_images(path=IMAGES_JSONL):
    """Returns {word: record}. The whole record is kept so unknown keys survive
    a load/save round-trip. Missing file -> empty mapping."""
    out = {}
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{lineno}: {e}") from e
            word = (rec.get("word") or "").strip()
            if word:
                rec["word"] = word
                out[word] = rec
    return out


def save_images(mapping, path=IMAGES_JSONL):
    """Write {word: record} sorted by word, atomically. Records with neither
    images nor any hand-set flag are dropped so the file stays a list of things
    that actually say something."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for word in sorted(mapping, key=lambda w: (w.lower(), w)):
            rec = mapping[word]
            if not all_images(rec) and is_illustratable(rec) and len(rec) <= 2:
                continue
            rec["word"] = word
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    os.replace(tmp, path)
