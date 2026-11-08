"""Methodology form rules: turn a blended form into legal root variants, each
with a penalty and a trace of the rules applied.

  - avoid 1 syllable and > 3; prefer 3 over 2
  - a-posteriori vowel from a source (es -o/-a, sw -i/-u, ja -u ...)
      caveat 1: no vowel if that gives 4+ syllables and a source ends in a consonant
                (but English -ation/-ate -> -a; es -ia/-io, fr -aire/-oire, en -y -> -i)
      caveat 2: closed list of common 2-syllable words without vowel (eskol, alim, muhim): flagged only
      caveat 3: no vowel if 8+ languages end in a consonant
  - a-priori vowel after an illegal final consonant (b c d g h j k p t v z):
      Indo-European sources -> -e (English verbs -> -i); others -> -u
  - initial e- before an illegal onset cluster
  - noun/verb roots avoid the onsets le- xa- nun- ger- be- du-
"""

import re

from .align import align
from .collision import FINAL_CODA, ONSET2, VOWELS, phonotactics
from .languages import INDO_EUROPEAN

BANNED_ONSETS = ("le", "xa", "nun", "ger", "be", "du")


def syllables(w):
    return sum(1 for c in w if c in VOWELS)


def syllable_penalty(n):
    return {0: 5.0, 1: 1.0, 2: 0.1, 3: 0.0}.get(n, 0.5 * (n - 3))


def _initial_e(w, trace):
    m = re.match(r"^([^aeiou]+)", w)
    if m:
        o = m.group(1)
        if len(o) > 2 or (len(o) == 2 and o not in ONSET2):
            trace.append(f"initial e- before the cluster '{o}'")
            return "e" + w
    return w


def _final_ok(w):
    return w[-1] in VOWELS or (w[-1] in FINAL_CODA and len(w) > 1 and w[-2] in VOWELS)


# Japanese / Korean add epenthetic vowels after consonants (puraneto, kuraixisu);
# they count, but at half weight, as a-posteriori evidence.
EPENTHETIC = {"ja": 0.5, "ko": 0.5}
VOTE_SCALE = 0.6      # penalty for an ending with no support, relative to the best-supported one
VOWEL_BIAS = -0.1     # "roots tend to end with an a-posteriori vowel found in a source"


SINO_JA_CODA = re.compile(r"(tsu|ci|cu|ku|ki)$")
# a blend's final coda reflex, removed before attaching a Middle Chinese coda option
OPEN_STEM = re.compile(r"(tsu|ci|cu|ku|ki|fu|ng|l|t|k|p|m|n)$")


def _sino_japanese_coda(m):
    """A Sino-Japanese reading whose final -tsu/-chi/-ku/-ki is the epenthetic
    syllable after a Middle Chinese stop (基質 kishitsu < kicit, cf. Korean gijil):
    the etymon ends in a consonant, so its vowel is no a-posteriori vowel."""
    if m["lang"] != "ja" or not SINO_JA_CODA.search((m.get("form") or "").replace(" ", "")):
        return False
    from . import sinosphere
    w = m.get("word", "")
    return sinosphere.is_han_word(w) and sinosphere.ja_reading_kind(w, m["form"].replace(" ", "")) != "native"


def ending_votes(core, members):
    """Per-language vote on what follows the aligned core: a vowel, or nothing ('-').
    Each language has weight 1, split among its forms. A Sino-Japanese reading ending
    in an epenthetic -tsu/-chi/-ku/-ki votes for no vowel (its etymon ends in -t/-k);
    katakana loans keep their -u at half weight (EPENTHETIC)."""
    per_lang = {}
    for m in members:
        per_lang[m["lang"]] = per_lang.get(m["lang"], 0) + 1
    votes, langs = {}, {}
    for m in members:
        f = (m["form"] or "").replace(" ", "")
        if not f:
            continue
        if _sino_japanese_coda(m):
            end, w = "-", 1.0 / per_lang[m["lang"]]
            votes[end] = votes.get(end, 0) + w
            langs.setdefault(end, set()).add(m["lang"])
            continue
        _, pairs = align(core, f)
        end = pairs[-1][1] if pairs and pairs[-1][0] == "-" and pairs[-1][1] in VOWELS else "-"
        w = 1.0 / per_lang[m["lang"]] * (EPENTHETIC.get(m["lang"], 1.0) if end != "-" else 1.0)
        votes[end] = votes.get(end, 0) + w
        langs.setdefault(end, set()).add(m["lang"])
    return votes, langs


def normalize(w, trace):
    """Lexicon-attested spelling norms: no geminates (0 roots have one);
    C+i+V -> CyV (233 roots vs 14) and C+u+V -> CwV (91 vs 19)."""
    out = re.sub(r"([bcdfghjklmnprstvxz])\1", r"\1", w)
    if out != w:
        trace.append("geminate simplified (Globasa roots have none)")
    g = re.sub(r"(?<=[^aeiouyw])i(?=[aeou])", "y", out)
    g = re.sub(r"(?<=[^aeiouyw])u(?=[aeio])", "w", g)
    if g != out and not phonotactics(g):
        trace.append("vowel before vowel written as glide (CyV / CwV, as in fermyum, presyon)")
        out = g
    return out


def shape(form, members, word_class="", coda=True):
    """form: blended Globasa-letter form. members: [{lang, form, word, pos}] of the cluster.
    word_class: Globasa class ('b' noun/verb, 't' adj/adv ...).
    coda: offer Middle Chinese coda renderings (the pipeline does so for its best
    blend only, so the options do not crowd the list).
    Returns [{form, penalty, trace}] (legal variants only, best first)."""
    base_trace = []
    w = _initial_e(normalize(form, base_trace), base_trace)
    # core = form without one a-posteriori vowel (planeta -> planet; kakao stays)
    core = w[:-1] if len(w) > 2 and w[-1] in VOWELS and w[-2] not in VOWELS else w
    votes, vlangs = ending_votes(core, members)
    best = max(votes.values()) if votes else 1.0
    cons_langs = {m["lang"] for m in members if m["form"] and m["form"][-1] not in VOWELS}
    any_cons, many_cons = bool(cons_langs), len(cons_langs) >= 8
    ie = sum(1 for m in members if m["lang"] in INDO_EUROPEAN) >= len(members) / 2
    is_verb = any(m["lang"] == "en" and m.get("pos") == "verb" for m in members)
    en_words = [m.get("word", "").lower() for m in members if m["lang"] == "en"]
    special_a = any(x.endswith("ation") for x in en_words) or (is_verb and any(x.endswith("ate") for x in en_words))
    special_i = any(x.endswith("y") for x in en_words) or any(
        m.get("word", "").lower().endswith(("ia", "io", "aire", "oire"))
        for m in members if m["lang"] in ("es", "fr"))

    cands = []

    def add(f, pen, trace):
        cands.append({"form": f, "penalty": pen, "trace": base_trace + trace})

    def support(end):
        return VOTE_SCALE * (1 - votes.get(end, 0) / best)

    if core != w or core[-1] not in VOWELS:
        # the ending is open: no vowel, or one of the source vowels
        if _final_ok(core) and core[-1] not in VOWELS:
            pen, why = support("-"), f"no final vowel (as in {', '.join(sorted(vlangs.get('-', []))) or 'no source'})"
            if many_cons:
                pen, why = pen - 0.3, why + "; caveat 3: 8+ languages end in a consonant"
            add(core, pen, [why])
        vowel_options = [v for v in votes if v != "-"]
        for v in vowel_options:
            f = core + v
            pen, why = support(v) + VOWEL_BIAS, f"a-posteriori vowel -{v} (as in {', '.join(sorted(vlangs[v]))})"
            if many_cons:
                pen, why = pen + 0.3, why + "; caveat 3 argues against a vowel"
            if syllables(f) >= 4 and any_cons:
                pen, why = pen + 0.5, why + "; caveat 1: 4+ syllables with consonant-final sources"
            add(f, pen, [why])
        if not _final_ok(core) and not vowel_options:
            v = ("i" if is_verb else "e") if ie else "u"
            add(core + v, 0.1, [f"a-priori vowel -{v} after illegal final '{core[-1]}' "
                                f"({'Indo-European' if ie else 'non-Indo-European'} sources"
                                f"{', English verb' if is_verb and ie else ''}; no source supplies a vowel)"])
    else:
        add(w, 0.0, ["ends in a vowel, as its sources do"])
    if special_a:
        add(core + "a", -0.3, ["English -ation noun / -ate verb source -> -a"])
    if special_i:
        add(core + "i", -0.2, ["es -ia/-io, fr -aire/-oire or English -y source -> -i"])
    # Middle Chinese codas: whenever a Sinosphere member shows a reflex (Japanese
    # -tsu, Korean -l, Vietnamese -t ...), offer the renderings existing roots use
    # (-tu, -ku, -m, -n, -ngu ...), attached to the blend's open stem
    from .precedent import coda_options
    opts = coda_options(members) if coda else []
    if opts:
        stem = OPEN_STEM.sub("", w) or w
        for suf, pen, why in opts:
            add(stem + suf, pen, [why])

    out, seen = [], set()
    for c in cands:
        f = c["form"]
        if f in seen or phonotactics(f):
            continue
        seen.add(f)
        n = syllables(f)
        c["penalty"] += syllable_penalty(n)
        if n != 3:
            c["trace"].append(f"{n} syllable{'s' if n != 1 else ''}"
                              + (" (Globasa favours 3)" if n == 2 else " (avoid)" if n in (1,) or n > 3 else ""))
        if word_class[:1] in ("b", "n", "v") and f.startswith(BANNED_ONSETS):
            c["penalty"] += 0.5
            c["trace"].append("noun/verb root begins with a reserved onset (le- xa- nun- ger- be- du-)")
        out.append(c)
    return sorted(out, key=lambda c: c["penalty"])
