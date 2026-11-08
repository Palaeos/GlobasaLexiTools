"""LexiliAsel precedent: how existing roots resolved disagreements between the
source languages, by group of related forms.

Where the forms of one etymon disagree at a position, the existing roots show which
letter Globasa took. Groups (each with its own membership test, used both to learn
and to apply):

  sino      cmn ja ko vi        Sino-xenic cognates (with a katakana Japanese
                                member, only those sharing a Han spelling)
  jako      ja ko               European loans in Japanese/Korean (katakana)
  arabic    ar fa tr sw hi id   Arabic loans (an Arabic member present)
  indic     hi te id            Indic words (two or more of them)
  european  en es fr de ru      European words (three or more of them)

Place in the methodology ("Methodology for Lexical Development"):
- The caveats (minimal pairs, syllable count, apparent affixes) trump everything;
  they are applied after blending (form_rules, collision), so precedent cannot
  override them. Blends must still stay within 1 phoneme (or 2 close) of a source.
- The language-specific rules ("simplify Mandarin phonotactics when supported by
  the other East Asian languages, particularly Japanese"; Arabic /au/ -> o as in
  Swahili or Persian; European spelling) are what precedent encodes, so it ranks
  above the generic letter preferences, which apply only "all else being more or
  less equal".
- The word-final vowel slot (a posteriori vowel, caveats 1-3, a priori vowel,
  Arabic -u) belongs to form_rules: precedent neither learns nor decides it.

Leave-one-out on LexiliAsel (3057 roots, right root ranked first, without -> with
precedent): all 26.8 -> 30.6%; sino 15.0 -> 20.0; jako 31.7 -> 36.9; arabic
31.1 -> 36.0; indic 30.2 -> 35.4; european 28.8 -> 33.0. No group loses.
"""

import collections
import re
from functools import lru_cache
from itertools import combinations

SINO = ("cmn", "ja", "ko", "vi")
KATAKANA = re.compile(r"[゠-ヿ]")
VOWELS = set("aeiou")

# Letter classes for the second layer: exact patterns are sparse (Mandarin j/c/x,
# Korean g/k), but the choice is regular one level up: Mandarin palatal vs
# Japanese velar -> a velar, mostly Japanese k (kigan, kido, kingem).
CLASS = {**{c: "P" for c in "jcx"}, **{c: "K" for c in "kg"}, "h": "H", "f": "H",
         **{c: "N" for c in "mn"}, **{c: "L" for c in "lr"}, **{c: "S" for c in "sz"},
         **{c: "T" for c in "td"}, **{c: "B" for c in "pb"}}
MIN_COUNT = 3        # a pattern needs this many roots behind it
# Count every root's column under each of its sub-patterns too, so that backing
# off to (cmn d, ko t) finds the six roots where ja and vi were also present
# (5 took d), not only the one with cmn and ko alone
MARGINAL = False
MIN_SHARE = 0.6      # and this share for its winning letter


# ---------------------------------------------------------------------------
# Groups: which members of a cluster (or of a root's etymons) a group covers
# ---------------------------------------------------------------------------

def _han(m):
    from . import sinosphere
    return set(sinosphere.han_spellings(m["lang"], m.get("word", ""), m.get("form")))


def _sino(members):
    """Sinosphere members; if a Japanese member is katakana (a loan), only those
    sharing a Han spelling with another Sinosphere language's member."""
    idx = [i for i, m in enumerate(members) if m["lang"] in SINO]
    if not any(members[i]["lang"] == "ja" and KATAKANA.search(members[i].get("word", "")) for i in idx):
        return idx
    hs = {i: _han(members[i]) for i in idx}
    return [i for i in idx if hs[i] and any(j != i and members[j]["lang"] != members[i]["lang"]
                                            and hs[i] & hs[j] for j in idx)]


def _jako(members):
    if not any(m["lang"] == "ja" and KATAKANA.search(m.get("word", "")) for m in members):
        return []
    return [i for i, m in enumerate(members) if m["lang"] in ("ja", "ko")]


def _arabic(members):
    if not any(m["lang"] == "ar" for m in members):
        return []
    return [i for i, m in enumerate(members) if m["lang"] in ("ar", "fa", "tr", "sw", "hi", "id")]


def _indic(members):
    return [i for i, m in enumerate(members) if m["lang"] in ("hi", "te", "id")]


def _european(members):
    idx = [i for i, m in enumerate(members) if m["lang"] in ("en", "es", "fr", "de", "ru")]
    return idx if len({members[i]["lang"] for i in idx}) >= 3 else []


GROUPS = {"sino": _sino, "jako": _jako, "arabic": _arabic, "indic": _indic, "european": _european}


def applicable(members):
    """{group: [member index]} for the groups with two or more languages present."""
    out = {}
    for g, sel in GROUPS.items():
        idx = sel(members)
        if len({members[i]["lang"] for i in idx}) >= 2:
            out[g] = idx
    return out


def final_slot(rows):
    """Index of the first column of the word-final vowel slot: the columns after the
    last column where some member has a consonant. Precedent stays out of it."""
    last = -1
    for k in range(len(rows[0])):
        if any(r[k] not in VOWELS and r[k] != "-" for r in rows):
            last = k
    return last + 1


# ---------------------------------------------------------------------------
# Learning from the lexicon
# ---------------------------------------------------------------------------

def _patterns(col):
    """Keys a column counts under: the whole pattern, and (MARGINAL) each
    sub-pattern of two or more languages that still disagree."""
    items = tuple(sorted(col.items()))
    if not MARGINAL:
        return [items]
    return [sub for size in range(len(items), 1, -1) for sub in combinations(items, size)
            if len({c for _, c in sub}) >= 2]


def _classes(col):
    return tuple(sorted((l, CLASS.get(c, c)) for l, c in col.items()))


@lru_cache(maxsize=1)
def _root_members():
    """[(root word, members)] with members in the pipeline's own Globasa letters."""
    from .concept_index import ConceptIndex
    from .lexicon import roots
    from .pipeline import _members_for_root
    ix = ConceptIndex()
    out = []
    for r in roots():
        w = r["word"]
        if w.isalpha() and w.islower():
            out.append((w, _members_for_root(r, "oracle", ix)))
    return out


@lru_cache(maxsize=None)
def _learn(group):
    """(pattern counts, class-level follow counts, per-root contributions) for one
    group. pattern = ((lang, letter), ...) at a column where the group's languages
    disagree ('-' is a gap); the word-final vowel slot is skipped."""
    from .align import msa
    counts = collections.defaultdict(collections.Counter)
    follow = collections.defaultdict(lambda: [collections.Counter(), 0])
    per_root = collections.defaultdict(list)
    sel = GROUPS[group]
    for word, members in _root_members():
        mem = [members[i] for i in sel(members) if members[i]["form"]]
        if len({m["lang"] for m in mem}) < 2:
            continue
        rows = None
        if group == "sino":        # as blend.candidates aligns them
            from . import sino_align
            rows = sino_align.rows(mem, extra=[word], sino_idx=list(range(len(mem))))
        if rows is None:
            _, rows = msa([m["form"] for m in mem] + [word])
        end = final_slot(rows[:-1])
        for k in range(min(end, len(rows[0]))):
            col = {}
            for m, row in zip(mem, rows[:-1]):
                col.setdefault(m["lang"], row[k])
            if len(set(col.values())) < 2:
                continue
            chosen = rows[-1][k]
            for key in _patterns(col):
                counts[key][chosen] += 1
            f = follow[_classes(col)]
            f[1] += 1
            for l, c in col.items():
                if c == chosen:
                    f[0][l] += 1
            per_root[word].append((dict(col), chosen))
    return dict(counts), {k: (v[0], v[1]) for k, v in follow.items()}, dict(per_root)


def model(group="sino"):
    return _learn(group)[0]


def follow_model(group="sino"):
    return _learn(group)[1]


class _Less:
    """A model minus one root's own counts, subtracted at lookup (a deep copy of
    the whole model per root is slow once sub-patterns are counted too)."""

    def __init__(self, base, delta, follow=False):
        self.base, self.delta, self.follow = base, delta, follow

    def get(self, key):
        v, d = self.base.get(key), self.delta.get(key)
        if v is None or d is None:
            return v
        if self.follow:
            return v[0] - d[0], v[1] - d[1]
        return v - d        # Counter subtraction keeps positive counts only


@lru_cache(maxsize=8192)
def _without(group, root):
    """Both models with one root's own contributions removed (leave-one-out)."""
    delta = collections.defaultdict(collections.Counter)
    fdelta = {}
    for col, chosen in _learn(group)[2].get(root, []):
        for key in _patterns(col):
            delta[key][chosen] += 1
        cnt, n = fdelta.get(_classes(col), (collections.Counter(), 0))
        for l, ch in col.items():
            if ch == chosen:
                cnt[l] += 1
        fdelta[_classes(col)] = (cnt, n + 1)
    return _Less(model(group), delta), _Less(follow_model(group), fdelta, follow=True)


def lookup(col, exclude_root=None, group="sino"):
    """col: {lang: letter} for the group's members at one aligned position.
    Returns (letter, n, share, pattern) from the most specific pattern with enough
    precedent, backing off by dropping one language; then by letter class, taking
    the letter of the language precedent follows (pattern ends with ("follows",
    lang)). None if there is none or the languages agree."""
    if len(set(col.values())) < 2:
        return None
    m, fm = _without(group, exclude_root.lower()) if exclude_root else (model(group), follow_model(group))
    items = sorted(col.items())
    for size in range(len(items), 1, -1):
        best = None
        for sub in combinations(items, size):
            if len({c for _, c in sub}) < 2:
                continue
            c = m.get(tuple(sub))
            if not c:
                continue
            n = sum(v for v in c.values() if v > 0)
            if not n:
                continue
            letter, k = c.most_common(1)[0]
            if n >= MIN_COUNT and k / n >= MIN_SHARE and (best is None or n > best[1]):
                best = (letter, n, round(k / n, 2), sub)
        if best:
            return best
    for size in range(len(items), 1, -1):
        best = None
        for sub in combinations(items, size):
            if len({c for _, c in sub}) < 2:
                continue
            got = fm.get(_classes(dict(sub)))
            if not got or got[1] < MIN_COUNT:
                continue
            followed = +got[0]          # positive counts only (leave-one-out can zero them)
            if not followed:            # Globasa took none of the members' letters
                continue
            lang, k = followed.most_common(1)[0]
            share = k / got[1]
            if lang in col and share >= MIN_SHARE and (best is None or got[1] > best[1]):
                best = (col[lang], got[1], round(share, 2), tuple(sub), lang)
        if best:
            letter, n, share, sub, lang = best
            return (letter, n, share, sub + (("follows", lang),))
    return None


def decide(members, column, k, end, exclude_root=None, groups=None):
    """The precedent for one column of a cluster's alignment, from whichever
    applicable group has the most roots behind it; None in the word-final vowel
    slot (form_rules decides that) or without precedent.
    Returns (letter, n, share, pattern, group)."""
    if k >= end:
        return None
    best = None
    for g, idx in (groups if groups is not None else applicable(members)).items():
        col = {}
        for i in idx:
            col.setdefault(members[i]["lang"], column[i])
        if len(col) < 2:
            continue
        got = lookup(col, exclude_root, g)
        if got and (best is None or got[1] > best[1]):
            best = got + (g,)
    return best


# ---------------------------------------------------------------------------
# Middle Chinese codas: how existing roots render a final -t -k -p -m -n -ng
# ---------------------------------------------------------------------------
# Reflexes by language, on the Globasa-letter form's end. Japanese -tsu/-chi/-ku/-ki
# are epenthetic syllables after the stop; Korean -l is MC -t.
CODA_REFLEX = {
    "t": {"ja": r"(tsu|ci|cu)$", "ko": r"l$", "vi": r"t$"},
    "k": {"ja": r"(ku|ki)$", "ko": r"k$", "vi": r"(k|c|ck|kh)$"},
    "p": {"ja": r"(fu|pu)$", "ko": r"p$", "vi": r"p$"},
    "m": {"ko": r"m$", "vi": r"m$"},
    "n": {"ko": r"n$", "vi": r"(n|nh)$", "ja": r"n$", "cmn": r"n$"},
    "ng": {"ko": r"ng$", "vi": r"(ng|nh)$", "cmn": r"ng$"},
}
CODA_PENALTY = 0.4    # an option with no precedent share; scaled down by its share
CODA_BASE = 0.15      # always: an option must earn its place against the plain blend
CODA_SINGLE = 0.15    # more when only one language shows the reflex (ja -ku may be a whole syllable)


def _sino_forms(members):
    out = {}
    for i in _sino(members):
        f = (members[i].get("form") or "").replace(" ", "")
        if f:
            out.setdefault(members[i]["lang"], f)
    return out


def mc_final(members):
    """The Middle Chinese final consonant of the cluster's Han spelling (its last
    character's Baxter reading): (finals, reading) where finals is a set of the
    possible finals ('' = none). 級 -> ({'p'}, 'kip'); 質 -> ({'t', ''}, ...);
    (None, '') without a Han spelling or a reading."""
    from . import sinosphere
    for i in _sino(members):
        m = members[i]
        for sp in sinosphere.han_spellings(m["lang"], m.get("word", ""), m.get("form")):
            fin = sinosphere.mc_finals(sp)
            if fin:
                return set(fin), "/".join(r for rs in fin.values() for r in rs[:1])
    return None, ""


def codas_shown(members, strict=False):
    """{coda: [evidence]} for the cluster's final Middle Chinese consonant. The
    Middle Chinese reading decides when it is unambiguous (級 kip: -p, and then
    Japanese kyū's final -u is the -p's reflex; a whole-syllable Japanese -ku
    after a character with no final is no coda); when it is ambiguous (質 tsyit /
    trijH) the surface reflexes choose among its options; without a reading, the
    surface reflexes alone (two of them if strict). Evidence: 'ja', 'ko', ... or
    'MC:kip'."""
    mem = _sino_forms(members)
    surface = {}
    for coda, rx in CODA_REFLEX.items():
        langs = [l for l, p in rx.items() if mem.get(l) and re.search(p, mem[l])]
        if langs:
            surface[coda] = langs
    finals, reading = mc_final(members)
    if finals is None:
        return {c: ls for c, ls in surface.items() if not strict or len(ls) >= 2}
    if len(finals) == 1:
        c = next(iter(finals))
        if not c:
            return {}
        langs = list(surface.get(c, []))
        if c == "p" and "ja" in mem and mem["ja"][-1] in VOWELS and "ja" not in langs:
            langs.append("ja")                # kyū < kifu: the final -u is the -p
        if c in ("p", "t", "k") and "cmn" in mem and mem["cmn"][-1] in VOWELS:
            langs.append("cmn")               # 級 jí < kip: Mandarin lost the stop
        return {c: langs + [f"MC:{reading}"]}
    out = {}
    for c, ls in surface.items():
        if c in finals:
            if c in ("p", "t", "k") and "cmn" in mem and mem["cmn"][-1] in VOWELS:
                ls = ls + ["cmn"]
            out[c] = ls + [f"MC:{reading}"]
    return out


def _coda_outcome(coda, root):
    """How a root renders a final MC coda: the suffix after the open stem, or '' if
    dropped."""
    if root.endswith(coda):
        return coda
    m = re.search(coda + "([aeiou])$", root)
    if m:
        return coda + m.group(1)
    if coda in ("m", "ng") and root.endswith("n"):
        return "n"
    return ""


@lru_cache(maxsize=1)
def coda_stats():
    """{coda: (Counter(suffix), {suffix: [example roots]}, roots)} from Sino-xenic
    roots whose final Middle Chinese consonant is known (its reading, or two
    surface reflexes)."""
    out = {c: (collections.Counter(), collections.defaultdict(list), [0]) for c in CODA_REFLEX}
    for word, members in _root_members():
        if len(_sino_forms(members)) < 2:
            continue
        for coda in codas_shown(members, strict=True):
            cnt, ex, n = out[coda]
            n[0] += 1
            suf = _coda_outcome(coda, word)
            cnt[suf] += 1
            ex[suf].append(word)
    return {c: (cnt, dict(ex), n[0]) for c, (cnt, ex, n) in out.items()}


def coda_options(members):
    """Endings to offer when a Sinosphere member shows a Middle Chinese coda's reflex,
    as existing roots render it: [(suffix, penalty, why)]. 'Dropped' is the ordinary
    blend and is not repeated here. Stops take the a priori -u prescribed for East
    Asian sources (-tu, -ku, -pu), -ki only where Japanese has it."""
    mem = _sino_forms(members)
    out = []
    for coda, langs in codas_shown(members).items():
        cnt, ex, n = coda_stats()[coda]
        def label(l):
            if l.startswith("MC:"):
                return f"Middle Chinese {l[3:]}"
            if l == "cmn" and coda in ("p", "t", "k"):
                return "cmn lost it"
            hit = re.search(CODA_REFLEX[coda].get(l, "$^"), mem.get(l, ""))
            return f"{l} -{hit.group(0)}" if hit else f"{l} -{mem.get(l, '')[-1:]}"
        shown = ", ".join(label(l) for l in langs)
        langs = [l for l in langs if not l.startswith("MC:")]
        # a rendering needs real precedent (MIN_COUNT roots: -ni / -nu for -n have one
        # each of 73 and only crowd out one-syllable roots like byen); stops always
        # keep the a priori -u, the methodology's own rule for East Asian sources
        sufs = [s for s in cnt if s and cnt[s] >= MIN_COUNT]
        if coda in ("t", "k", "p") and coda + "u" not in sufs:
            sufs.append(coda + "u")          # the a priori vowel, even without precedent
        for suf in sufs:
            if suf.endswith("i") and coda in ("t", "k") and not (mem.get("ja", "").endswith(("ki", "ci"))):
                continue
            k = cnt.get(suf, 0)
            share = k / n if n else 0.0
            why = (f"Middle Chinese -{coda} ({shown}): -{suf}"
                   + (f", as in {', '.join(ex.get(suf, [])[:3])} ({k} of {n} roots)" if k
                      else " with the a priori -u (no precedent yet)"))
            pen = CODA_BASE + CODA_PENALTY * (1 - share) + (CODA_SINGLE if len(langs) < 2 else 0)
            out.append((suf, round(pen, 3), why))
    return out
