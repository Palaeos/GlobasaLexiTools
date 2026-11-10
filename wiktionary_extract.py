"""Read the English Wiktionary dump (kaikki.org raw wiktextract JSONL) into a
WiktionaryDB: translations by sense, senses with examples, and the parts of
speech of Spanish words.

The dump may be a local .jsonl, a local .jsonl.gz, or a URL, which is streamed
and never stored: menalariExtension.tsv needs only the few thousand entries the
vetting decisions name, not the 20 GB dump or the 640 MB full database.

    extract(source, out_dir)              every English entry (what
                                          "JSONL parser 2.py" builds)
    extract(source, out_dir, keys=...)    only these (word, pos) entries

Run directly to build WiktionaryLMDB_vetted/ for the vetted senses:
    python wiktionary_extract.py [dump path or URL]
"""
import gzip
import io
import os
import sys
import urllib.request

try:
    import orjson
    _loads = orjson.loads
except ImportError:
    import json
    _loads = json.loads

from wiktionary_db import (WiktionaryDB, Translation, Example, Sense,
                           encode_key, serialize_translations,
                           serialize_senses, serialize_spanish_pos)

KAIKKI_EN_URL = "https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz"
VETTED_LMDB = "./WiktionaryLMDB_vetted"


def _open_lines(source):
    """Text lines of a path or URL, decompressing .gz on the fly."""
    if source.startswith(("http://", "https://")):
        raw = urllib.request.urlopen(source, timeout=120)
    else:
        raw = open(source, "rb")
    if source.endswith(".gz"):
        raw = gzip.GzipFile(fileobj=raw)
    return io.TextIOWrapper(raw, encoding="utf-8")


def _add_entry(data, translations, senses):
    """Fold one English entry into the accumulators, as JSONL parser 2 did."""
    word, pos = data["word"], data["pos"]

    if "senses" in data:
        lst = senses.setdefault((word, pos), [])
        for s in data["senses"]:
            lst.append(Sense(
                tuple(s.get("glosses", ())),
                tuple(s.get("raw_glosses", ())),
                tuple(s.get("tags", ())),
                tuple(Example(ex.get("text", ""), ex.get("english", ""), ex.get("type", ""))
                      for ex in s.get("examples", ())),
            ))

    if "translations" in data:
        by_sense = translations.setdefault((word, pos), {})
        for t in data["translations"]:
            if "word" not in t or "sense" not in t:
                continue
            code = t.get("code") or t.get("lang_code")
            if not code:
                continue
            tags = t.get("tags", [])
            rom = t.get("romanization", "") or t.get("roman", "")
            by_sense.setdefault(t["sense"], {}).setdefault(code, set()).add(
                Translation(t["word"], rom, "\t".join(tags) if tags else ""))


def extract(source, out_dir, keys=None, max_lines=-1, progress=True):
    """Build a WiktionaryDB at out_dir from the dump at `source`.

    keys: a set of (word, pos) to keep, or None for every English entry. The
    Spanish part-of-speech table (used by the sense generator, not the
    extension) is only built for a full extraction.
    """
    translations, senses, spanish_pos = {}, {}, {}
    words = {w for w, _ in keys} if keys is not None else None
    n = 0
    with _open_lines(source) as lines:
        for line in lines:
            n += 1
            if n == max_lines:
                break
            if progress and n % 1_000_000 == 0:
                print(f"  {n // 1_000_000}M lines, {len(translations)} entries kept", flush=True)
            # Cheap prefilter: "lang" also occurs inside translation lists, so
            # this keeps a superset; the parsed top-level lang decides.
            if '"lang": "English"' not in line and (
                    keys is not None or '"lang": "Spanish"' not in line):
                continue
            try:
                data = _loads(line)
            except ValueError as e:
                print(f"  Skipping a line that is not JSON: {e}")
                continue
            if "word" not in data or "lang" not in data:
                continue
            lang = data["lang"]
            if lang == "Spanish" and keys is None:
                spanish_pos.setdefault(data["word"], set()).add(data["pos"])
                continue
            if lang != "English":
                continue
            if words is not None and (data["word"] not in words
                                      or (data["word"], data["pos"]) not in keys):
                continue
            _add_entry(data, translations, senses)

    print(f"Writing {len(translations)} translation entries, {len(senses)} sense "
          f"entries, {len(spanish_pos)} spanish_pos entries to {out_dir}...")
    tmp = out_dir.rstrip("/") + ".building"
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    with WiktionaryDB(path=tmp, readonly=False) as db:
        with db.env.begin(write=True) as txn:
            for (word, pos), d in translations.items():
                txn.put(encode_key(word, pos), serialize_translations(d), db=db.db_translations)
            for (word, pos), lst in senses.items():
                txn.put(encode_key(word, pos), serialize_senses(lst), db=db.db_senses)
            for w, ps in spanish_pos.items():
                txn.put(w.encode("utf-8"), serialize_spanish_pos(ps), db=db.db_spanish_pos)
    shutil.rmtree(out_dir, ignore_errors=True)
    os.replace(tmp, out_dir)
    return len(translations)


if __name__ == "__main__":
    import vetted_senses
    source = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("WIKTIONARY_DUMP", KAIKKI_EN_URL)
    keys = {(s["lookup_word"], s["pos"]) for s in vetted_senses.load_vetted()
            if s["source"] == "en"}
    print(f"Extracting {len(keys)} English entries for the vetted senses from {source}")
    found = extract(source, VETTED_LMDB, keys)
    print(f"Done: {found} of {len(keys)} entries found.")
