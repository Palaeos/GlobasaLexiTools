"""Read/write access to WiktionaryLMDB_concepts/ (built by `Wiktionary concept index.py`).

Sub-databases (all values msgpack):
  translations  word\\0pos (English headword) -> {sense: {lang: [[word, roman, tags]]}}
  trans_qid     word\\0pos -> {sense: [QID, ...]}   (translation-table sense -> Wikidata)
  qid           QID -> [[lang, word, pos, sense_or_gloss, kind]]  kind: "t" table, "g" gloss
  reverse       lang\\0word -> [[en_word, pos, sense]]  (which tables list this word)
  entries       lang\\0word -> [entry, ...]  one per dump line (pos/etymology), where
                entry = {pos, senses: [{g, raw, tags, qid, ex}], ipa: [[ipa, tags]],
                         roman: [...], etym: [[type, src_lang, src_term]]}
"""

import os
import re
import unicodedata

import lmdb
import msgpack

DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "WiktionaryLMDB_concepts")
MAP_SIZE = 40 * 1024 ** 3
# Arabic-script vowel marks + tatweel: Wiktionary titles are unvocalised
_HARAKAT = re.compile("[\u064b-\u0652\u0670\u0640]")
SUBDBS = [b"translations", b"trans_qid", b"qid", b"entries", b"reverse"]


def pack(v):
    return msgpack.packb(v, use_bin_type=True)


def unpack(b):
    return msgpack.unpackb(b, raw=False)


def key(a, b):
    return f"{a}\x00{b}".encode("utf-8")


class ConceptIndex:
    def __init__(self, path=DIR, readonly=True):
        self.env = lmdb.open(path, max_dbs=len(SUBDBS), map_size=MAP_SIZE,
                             readonly=readonly, lock=not readonly, readahead=False)
        self.dbs = {}
        for name in SUBDBS:
            try:
                self.dbs[name.decode()] = self.env.open_db(name, create=not readonly)
            except lmdb.NotFoundError:   # older index without this sub-db
                pass

    def close(self):
        self.env.close()

    def _get(self, db, k):
        if db not in self.dbs:
            return None
        with self.env.begin() as txn:
            v = txn.get(k, db=self.dbs[db])
        return unpack(v) if v is not None else None

    # -- English headword side -------------------------------------------
    def translations(self, word, pos):
        return self._get("translations", key(word, pos)) or {}

    def trans_qids(self, word, pos):
        return self._get("trans_qid", key(word, pos)) or {}

    def headword_pos(self, word):
        """All PoS under which an English headword has translation tables."""
        prefix = f"{word}\x00".encode("utf-8")
        out = []
        with self.env.begin() as txn:
            cur = txn.cursor(db=self.dbs["translations"])
            if cur.set_range(prefix):
                for k, _ in cur:
                    if not k.startswith(prefix):
                        break
                    out.append(k[len(prefix):].decode("utf-8"))
        return out

    def qid(self, q):
        return self._get("qid", q.encode("utf-8")) or []

    def tables_listing(self, lang, word):
        """Translation tables (English headword, pos, sense) that list this word.
        lang is a Wiktionary translation code (e.g. 'fa', 'cmn', 'zh')."""
        for w in dict.fromkeys([word, word.lower()]):
            v = self._get("reverse", key(lang, w))
            if v:
                return v
        return []

    # -- Any-language entries ----------------------------------------------
    def entries(self, lang, word):
        """Entries for a word, trying the exact form, then lower/capitalised."""
        bare = _HARAKAT.sub("", word)
        variants = [word, word.lower(), word[:1].upper() + word[1:], bare,
                    unicodedata.normalize("NFC", word), unicodedata.normalize("NFD", word)]
        for w in dict.fromkeys(variants):
            v = self._get("entries", key(lang, w))
            if v:
                return v
        return []


# ---------------------------------------------------------------------------
# Translation-sense -> definition-sense matching. Copied from
# `Wiktionary sense based translation extender 3.py` (a script, not importable),
# adapted to dict senses {g, raw}.
# ---------------------------------------------------------------------------

_STOPWORDS = frozenset(
    "a an the of or and in for to is are was were be been being "
    "by with at on from as it its that this which who whom whose".split()
)


def _content_words(text):
    words = set()
    for w in re.findall(r"[a-zA-Z']+", text.lower()):
        w = w[:-2] if w.endswith("'s") else w
        if w and w not in _STOPWORDS:
            words.add(w)
    return words


def match_sense(sense_key, senses):
    """Return the index of the sense (list of {g, raw}) a translation sense key refers to."""
    sk = sense_key.lower().strip()
    if not sk:
        return None
    after = sk.split(":", 1)[1].strip() if ":" in sk else ""
    for field in ("g", "raw"):
        for i, s in enumerate(senses):
            for gl in s.get(field) or []:
                gl = gl.lower()
                if sk in gl or (after and after in gl):
                    return i
    skw = _content_words(sense_key)
    if not skw:
        return None
    best, best_i = 0.0, None
    for i, s in enumerate(senses):
        for gl in s.get("g") or []:
            score = len(skw & _content_words(gl)) / len(skw)
            if score > best:
                best, best_i = score, i
    return best_i if best >= 0.5 else None


def build_reverse(path=DIR):
    """Post-pass: fill `reverse` from `translations` (no dump needed)."""
    import re as _re
    idx = ConceptIndex(path, readonly=False)
    rev = {}
    with idx.env.begin() as txn:
        for k, v in txn.cursor(db=idx.dbs["translations"]):
            word, pos = k.decode("utf-8").split("\x00", 1)
            for sense, langs in unpack(v).items():
                for code, ts in langs.items():
                    for t in ts:
                        for variant in _re.split(r"\s*/\s*", t[0]):
                            if variant:
                                rev.setdefault((code, variant.strip()), []).append([word, pos, sense])
    with idx.env.begin(write=True) as txn:
        for (code, w), refs in rev.items():
            txn.put(key(code, w), pack(refs[:200]), db=idx.dbs["reverse"])
    idx.close()
    return len(rev)
