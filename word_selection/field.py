"""Semantic-field sweep without an English pivot.

Given seed terms in source languages (ja:妖怪, cmn:妖怪, de:Fabelwesen, fr:esprit),
find the headwords whose OWN-language Wiktionary glosses name a term
(ja.wiktionary 河童: "日本の妖怪の一つ"), in every built native edition (ja zh de fr,
plus es ru ko when built). English Wiktionary is never searched or used to
spread terms: no English pivot. Each hit carries its own edition's translation table, so it can become a
concept for the Word Selector without passing through an English sense.

Terms spread between editions natively: a seed's own-edition translation tables
give its words in the other editions' languages, and an all-Han term is also
searched in its traditional/simplified/shinjitai spellings.

Speed: glosses (not examples) of each edition are written once to
word_selection_cache/glosses_<ed>.tsv (one LMDB pass: ~2 s for ja/zh, ~1 min for
de/fr), rebuilt only when the LMDB is newer; a search is a memory-mapped byte
search of that file, well under a second, holding nothing in RAM.
"""

import mmap
import os
import re
import threading
import time

from .languages import BY_CODE, WIKT_TO_CODE

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "word_selection_cache")
HEAD_FINAL = {"ja", "zh", "ko"}          # genus word comes last in a gloss
MAX_HITS = 400                           # per term and edition
MAX_TABLES = 150                         # table lookups per sweep (genus hits first)
_lock = threading.Lock()                 # one cache build at a time (memory rule)
STATUS = {}                              # edition -> "ready" | "building" | "missing"

# genus = the term is what the gloss defines the headword AS
_GENUS_TAIL = ("の一種", "の一つ", "の総称", "の名", "の類", "之一", "的一種", "的一种", "的總稱", "的总称")
_ARTICLE = re.compile(r"^(?:(?:ein|eine|einer|der|die|das|un|une|le|la|les|l'|des|un|una|el|la|los|las)\s+)?", re.I)
_TRAIL = re.compile(r"[\s。．.、，,；;：:！!）)」』]+$")


def editions():
    """Built native editions (edition -> source-language code); never en."""
    from .contrasts import EDITIONS, available
    return {e: EDITIONS[e] for e in available()}


def lang_edition(lang):
    """Source-language code -> its own edition (cmn -> zh), or None if not built."""
    return next((e for e, l in editions().items() if l == lang), None)


def _db(ed):
    from .sources.wiktionary import other_wiki
    return other_wiki(ed)


def _lmdb_path(ed):
    return os.path.join(ROOT, f"WiktionaryLMDB_{ed}")


def _cache_path(ed):
    return os.path.join(CACHE, f"glosses_{ed}.tsv")


def _stale(ed):
    p, src = _cache_path(ed), os.path.join(_lmdb_path(ed), "data.mdb")
    return not os.path.exists(p) or (os.path.exists(src) and os.path.getmtime(src) > os.path.getmtime(p))


def build(ed):
    """One cursor pass over <ed>'s senses -> glosses_<ed>.tsv: word, pos, sense number, glosses."""
    from wiktionary_db import decode_key, deserialize_senses
    db = _db(ed)
    if db is None:
        STATUS[ed] = "missing"
        return
    os.makedirs(CACHE, exist_ok=True)
    tmp = _cache_path(ed) + ".building"
    clean = re.compile(r"[\t\n\r]+")
    with open(tmp, "w", encoding="utf-8") as f, db.env.begin(db=db.db_senses, buffers=True) as txn:
        for k, v in txn.cursor():
            word, pos = decode_key(bytes(k))
            for i, s in enumerate(deserialize_senses(bytes(v))):
                g = " ; ".join(s.glosses or s.raw_glosses)
                if g:
                    f.write(f"{word}\t{pos}\t{i}\t{clean.sub(' ', g)}\n")
    os.replace(tmp, _cache_path(ed))


def ensure(ed):
    """Build the gloss cache if missing or stale. -> True when ready."""
    with _lock:
        if _stale(ed):
            STATUS[ed] = "building"
            build(ed)
        if os.path.exists(_cache_path(ed)):
            STATUS[ed] = "ready"
    return STATUS.get(ed) == "ready"


def warm():
    """Build every missing cache, smallest edition first (run in a background thread)."""
    eds = list(editions())
    for ed in eds:
        STATUS.setdefault(ed, "ready" if not _stale(ed) else "pending")
    for ed in sorted(eds, key=lambda e: os.path.getsize(os.path.join(_lmdb_path(e), "data.mdb"))):
        try:
            ensure(ed)
        except Exception as e:      # one broken edition must not stop the others
            STATUS[ed] = f"error: {e}"


def _variants(term, lang):
    """The term plus its Han spelling variants (traditional / simplified / shinjitai)."""
    out = [term]
    try:
        from . import sinosphere
        if sinosphere.is_han_word(term):
            for n in sinosphere.normalise(term, lang):
                for l in ("cmn", "ja"):
                    out.extend(sinosphere.surface_forms(n, l))
    except Exception:               # sinosphere.json not built: the term as typed only
        pass
    return list(dict.fromkeys(out))


def _genus(ed, gloss, term):
    """Is the term the gloss's genus (河童: 日本の妖怪の一つ; Nix: Wassergeist, ...)?"""
    for part in re.split(r"\s*[;；]\s*", gloss):
        p = _TRAIL.sub("", part)
        if ed in HEAD_FINAL:
            if p.endswith(term) or any(p.endswith(term + t) for t in _GENUS_TAIL):
                return True
        else:
            head = _ARTICLE.sub("", p, count=1)
            # first two words: "Fabelwesen, das ...", "esprit malin ...", "böser Geist"
            words = re.split(r"[\s,]+", head)[:2]
            if any(w.lower().startswith(term.lower()) for w in words if w):
                return True
    return False


# entries of inflected forms ("Dativ Plural des Substantivs Abenteuergeist", "Pluriel de lutin")
_FORM_OF = re.compile(r"\b(?:(?:Nominativ|Genitiv|Dativ|Akkusativ|Plural|Singular)\b.*\bdes (?:Substantivs|Verbs|Adjektivs)"
                      r"|(?:Pluriel|Féminin|Masculin)(?: (?:singulier|pluriel))? de\b|personne du (?:singulier|pluriel))")


def _letter(b):
    """A letter byte: ASCII letter, or any byte of a non-ASCII UTF-8 character (é, ß, я)."""
    return b >= 0x80 or 65 <= b <= 90 or 97 <= b <= 122


def _boundary_ok(m, i, n, compound):
    """Alphabetic scripts, checked on the bytes around a match: a word or an inflected
    word (<= 2 more letters: Alben, esprits, Geistes), or, for the
    lower-cased German form, a compound head (Wasser|geist: letters before, none after).
    Rejects Alb in Albert, Geist in Geistlicher, démon in démontrer."""
    before = i > 0 and _letter(m[i - 1])
    j, end, tail = i + n, min(len(m), i + n + 12), 0
    while j < end and _letter(m[j]):
        tail += not (0x80 <= m[j] < 0xC0)       # count characters, not UTF-8 continuation bytes
        j += 1
    if compound:
        return before and tail == 0
    return not before and tail <= 2


def search(ed, term):
    """Headwords of <ed> whose glosses contain the term -> [{word, pos, sense_no, gloss, genus}].
    A plain mmap find (C speed) per form; boundaries checked on bytes before decoding."""
    if not ensure(ed):
        return []
    path, hits, seen = _cache_path(ed), [], set()
    if os.path.getsize(path) == 0:
        return []
    cjk = ed in HEAD_FINAL
    with open(path, "rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as m:
        for v in _variants(term, editions().get(ed, ed)):
            forms = [(v, False)]
            if ed == "de" and v[:1].isupper():
                forms.append((v[0].lower() + v[1:], True))
            for form, compound in forms:
                needle, i, last = form.encode("utf-8"), 0, -1
                while len(hits) < MAX_HITS:
                    i = m.find(needle, i)
                    if i < 0:
                        break
                    at, i = i, i + 1
                    if at <= last or not (cjk or _boundary_ok(m, at, len(needle), compound)):
                        continue
                    s = m.rfind(b"\n", 0, at) + 1
                    e = m.find(b"\n", at)
                    e = len(m) if e < 0 else e
                    last = i = e
                    line = m[s:e]
                    cut = 0
                    for _ in range(3):              # gloss column starts after the 3rd tab
                        cut = line.find(b"\t", cut) + 1
                    if at - s < cut:
                        continue                    # the match is in the headword column
                    word, pos, no, gloss = line.decode("utf-8", "replace").split("\t", 3)
                    if word in (term, v) or (word, pos) in seen or _FORM_OF.search(gloss):
                        continue                    # the term's own entry, or an inflected form's entry
                    seen.add((word, pos))
                    hits.append({"word": word, "pos": pos, "sense_no": int(no), "gloss": gloss[:300],
                                 "genus": _genus(ed, gloss, v), "matched": v})
    return hits


def _keys(db, word, dbi=None):
    """(word, pos) keys of a headword in an edition's translations (default) or senses table."""
    from wiktionary_db import decode_key
    pre, out = f"{word}\x00".encode(), []
    with db.env.begin(db=db.db_translations if dbi is None else dbi, buffers=True) as txn:
        cur = txn.cursor()
        if cur.set_range(pre):
            for k, _ in cur:
                k = bytes(k)
                if not k.startswith(pre):
                    break
                out.append(decode_key(k))
    return out


def tables(ed, word, pos=None):
    """{(pos, sense): {source lang: [words]}} of a headword in its own edition."""
    db = _db(ed)
    if db is None:
        return {}
    raw = {}
    for w, p in ([(word, pos)] if pos else _keys(db, word)):
        for sense, codes in (db.get_translations(w, p) or {}).items():
            raw[(p, sense)] = {c: [t.word for t in sorted(ts)] for c, ts in sorted(codes.items())}
    out = {}
    for (p, sense), codes in raw.items():
        langs = {}
        for c, ws in codes.items():
            l = WIKT_TO_CODE.get(c)
            if l:
                langs.setdefault(l, []).extend(w for w in ws if w not in langs.get(l, []))
        out[(p, sense)] = langs
    return out


def _best_table(ed, word, pos):
    t = tables(ed, word, pos)
    if not t:
        return None
    (p, sense), langs = max(t.items(), key=lambda kv: len(kv[1]))
    return {"pos": p, "sense": sense, "langs": {l: ws[:3] for l, ws in langs.items()}, "n_langs": len(langs)}


def parse_terms(text):
    from .sources.seeds import parse
    return parse(text)


def spread(terms):
    """Terms per edition: the typed ones, plus each typed term's own-edition table
    words in the other editions' languages. A table sense spreads only when it pins
    the meaning: it lists another typed term, or it is the headword's only sense
    (fr:esprit has many senses, so it does not spread 精神 "mind" on its own).
    -> [{edition, lang, term, via}]"""
    eds = editions()
    by_lang = {l: e for e, l in eds.items()}
    out, have = [], set()

    def add(ed, lang, term, via):
        if (ed, term) not in have:
            have.add((ed, term))
            out.append({"edition": ed, "lang": lang, "term": term, "via": via})

    for lang, term in terms:
        ed = by_lang.get(lang)
        if ed is None:
            continue
        add(ed, lang, term, "typed")
    for lang, term in terms:
        ed = by_lang.get(lang)
        if ed is None:
            continue
        tabs = tables(ed, term)
        others = {(l, w) for l, w in terms if (l, w) != (lang, term)}
        for (_, sense), langs in tabs.items():
            pinned = any(w in langs.get(l, []) for l, w in others)
            if not pinned and len(tabs) > 1:
                continue
            for l, ws in langs.items():
                if l in by_lang and l != lang:
                    for w in ws[:2]:
                        add(by_lang[l], l, w, f"{ed}.wiktionary table of {lang}:{term} ({sense[:40]})"
                            + ("" if pinned else ", its only sense"))
    return out


def own_entries(ed, lang, term):
    """The typed term's own entry in its edition, one row per part of speech, so the
    term itself can be ticked into the concept (ja:妖怪, zh:妖怪)."""
    db = _db(ed)
    if db is None:
        return []
    rows = []
    for w, pos in _keys(db, term, db.db_senses):
        glosses = [" ; ".join(x.glosses or x.raw_glosses) for x in (db.get_senses(w, pos) or [])]
        rows.append({"word": w, "pos": pos, "sense_no": 0, "gloss": " | ".join(g for g in glosses if g)[:300],
                     "genus": False, "matched": term, "edition": ed, "lang": lang, "terms": [term],
                     "typed": True, "own": True, "table": _best_table(ed, w, pos), "table_looked_up": True})
    return rows


def sweep(text, spread_terms=True):
    """-> {terms, hits, pending, took}: hits sorted genus first, then by table size."""
    t0 = time.time()
    terms = parse_terms(text)
    plan = spread(terms) if spread_terms else [
        {"edition": lang_edition(l), "lang": l, "term": w, "via": "typed"} for l, w in terms if lang_edition(l)]
    hits, pending, merged = [], [], {}
    for p in plan:
        ed = p["edition"]
        if STATUS.get(ed) in ("building", "pending") and _stale(ed):
            pending.append(ed)
            continue
        for h in search(ed, p["term"]):
            k = (ed, h["word"], h["pos"])
            if k in merged:
                merged[k]["terms"].append(p["term"])
                merged[k]["genus"] = merged[k]["genus"] or h["genus"]
                merged[k]["typed"] = merged[k]["typed"] or p["via"] == "typed"
                continue
            rec = {**h, "edition": ed, "lang": p["lang"], "terms": [p["term"]],
                   "typed": p["via"] == "typed", "table": None, "table_looked_up": False}
            merged[k] = rec
            hits.append(rec)
    # typed-term genus hits first; tables only for the top hits (speed)
    hits.sort(key=lambda h: (not h["genus"], not h["typed"], -len(h["terms"])))
    for h in hits[:MAX_TABLES]:
        h["table"], h["table_looked_up"] = _best_table(h["edition"], h["word"], h["pos"]), True
    hits.sort(key=lambda h: (not h["genus"], not h["typed"], -len(h["terms"]),
                             -((h["table"] or {}).get("n_langs", 0))))
    own, missing = [], []
    for p in plan:
        if p["via"] == "typed" and p["edition"] not in pending:
            rows = own_entries(p["edition"], p["lang"], p["term"])
            own.extend(r for r in rows if (r["edition"], r["word"], r["pos"]) not in merged)
            if not rows:
                missing.append(f"{p['lang']}:{p['term']}")
    return {"terms": plan, "hits": own + hits, "missing": missing, "pending": sorted(set(pending)),
            "status": dict(STATUS), "took": round(time.time() - t0, 2)}
