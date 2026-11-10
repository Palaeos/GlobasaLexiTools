"""Shared LMDB-backed storage for Wiktionary translation and sense data.

Replaces the prefix-partitioned pickle files in WiktionaryPickled/ with a single
LMDB environment providing per-key memory-mapped access.
"""

import lmdb
import msgpack
from typing import NamedTuple

# ---------------------------------------------------------------------------
# NamedTuples (single source of truth -- used by all scripts)
# ---------------------------------------------------------------------------


class Translation(NamedTuple):
    word: str
    romanization: str
    tags: str


class Example(NamedTuple):
    text: str
    english: str
    type: str


class Sense(NamedTuple):
    glosses: tuple
    raw_glosses: tuple
    tags: tuple
    examples: tuple


# ---------------------------------------------------------------------------
# Key encoding
# ---------------------------------------------------------------------------

def encode_key(word: str, pos: str) -> bytes:
    return f"{word}\x00{pos}".encode('utf-8')


def decode_key(key_bytes: bytes):
    word, pos = key_bytes.decode('utf-8').split('\x00', 1)
    return (word, pos)


# ---------------------------------------------------------------------------
# Value serialization
# ---------------------------------------------------------------------------

def serialize_translations(trans_dict):
    """dict[sense_str, dict[lang_code, set[Translation]]] -> bytes"""
    converted = {}
    for sense, lang_dict in trans_dict.items():
        converted[sense] = {
            lang: sorted([list(t) for t in trans_set])
            for lang, trans_set in lang_dict.items()
        }
    return msgpack.packb(converted, use_bin_type=True)


def deserialize_translations(data_bytes):
    """bytes -> dict[sense_str, dict[lang_code, set[Translation]]]"""
    raw = msgpack.unpackb(data_bytes, raw=False)
    result = {}
    for sense, lang_dict in raw.items():
        result[sense] = {
            lang: {Translation(*t) for t in trans_list}
            for lang, trans_list in lang_dict.items()
        }
    return result


def serialize_senses(sense_list):
    """list[Sense] -> bytes"""
    converted = []
    for s in sense_list:
        converted.append([
            list(s.glosses),
            list(s.raw_glosses),
            list(s.tags),
            [list(ex) for ex in s.examples]
        ])
    return msgpack.packb(converted, use_bin_type=True)


def deserialize_senses(data_bytes):
    """bytes -> list[Sense]"""
    raw = msgpack.unpackb(data_bytes, raw=False)
    return [
        Sense(
            tuple(s[0]), tuple(s[1]), tuple(s[2]),
            tuple(Example(*ex) for ex in s[3])
        )
        for s in raw
    ]


def serialize_spanish_pos(pos_set):
    """set[str] -> bytes"""
    return msgpack.packb(sorted(pos_set), use_bin_type=True)


def deserialize_spanish_pos(data_bytes):
    """bytes -> set[str]"""
    return set(msgpack.unpackb(data_bytes, raw=False))


# ---------------------------------------------------------------------------
# WiktionaryDB class
# ---------------------------------------------------------------------------

LMDB_DIR = "./WiktionaryLMDB"
MAP_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB


class WiktionaryDB:
    """LMDB-backed storage for Wiktionary translations and senses."""

    def __init__(self, path=LMDB_DIR, readonly=True):
        self.env = lmdb.open(
            path,
            map_size=MAP_SIZE,
            max_dbs=3,
            readonly=readonly,
            readahead=True,
            lock=not readonly,
        )
        self.db_translations = self.env.open_db(b'translations')
        self.db_senses = self.env.open_db(b'senses')
        self.db_spanish_pos = self.env.open_db(b'spanish_pos')
        self._readonly = readonly

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self.env.close()

    # -- Read methods --

    def get_translations(self, word, pos):
        """Lookup translations for (word, pos). Returns dict or None."""
        key = encode_key(word, pos)
        with self.env.begin(db=self.db_translations, buffers=True) as txn:
            val = txn.get(key)
            if val is None:
                return None
            return deserialize_translations(val)

    def get_senses(self, word, pos):
        """Lookup senses for (word, pos). Returns list or None."""
        key = encode_key(word, pos)
        with self.env.begin(db=self.db_senses, buffers=True) as txn:
            val = txn.get(key)
            if val is None:
                return None
            return deserialize_senses(val)

    def get_spanish_pos(self, word):
        """Lookup Spanish PoS tags for a word. Returns set or None."""
        key = word.encode('utf-8')
        with self.env.begin(db=self.db_spanish_pos, buffers=True) as txn:
            val = txn.get(key)
            if val is None:
                return None
            return deserialize_spanish_pos(val)

    # -- Write methods --

    def put_translations(self, word, pos, trans_dict, txn=None):
        """Store translations for (word, pos)."""
        key = encode_key(word, pos)
        val = serialize_translations(trans_dict)
        if txn is not None:
            txn.put(key, val, db=self.db_translations)
        else:
            with self.env.begin(db=self.db_translations, write=True) as t:
                t.put(key, val)

    def put_senses(self, word, pos, sense_list, txn=None):
        """Store senses for (word, pos)."""
        key = encode_key(word, pos)
        val = serialize_senses(sense_list)
        if txn is not None:
            txn.put(key, val, db=self.db_senses)
        else:
            with self.env.begin(db=self.db_senses, write=True) as t:
                t.put(key, val)

    def put_spanish_pos(self, word, pos_set, txn=None):
        """Store Spanish PoS set for a word."""
        key = word.encode('utf-8')
        val = serialize_spanish_pos(pos_set)
        if txn is not None:
            txn.put(key, val, db=self.db_spanish_pos)
        else:
            with self.env.begin(db=self.db_spanish_pos, write=True) as t:
                t.put(key, val)

    # -- Bulk write (for migration/producer) --

    def begin_write(self):
        """Start a write transaction spanning all sub-databases."""
        return self.env.begin(write=True)
