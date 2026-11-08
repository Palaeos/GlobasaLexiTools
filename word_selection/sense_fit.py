"""Does a source word's own dictionary entry attest the concept's meaning?

A word listed in an English translation table can still mean something else in
its own language. Globasa had nicode "squeeze" from Hindi निचोड़ना, whose own
entry says "to extract by squeezing, squeeze out": squeezing is the means, the
meaning is extracting (wringing). It was replaced by bopu, from Vietnamese bóp
"to press (with hands)" and Thai บีบ. Word overlap would pass निचोड़ना (it says
"squeeze") and miss bóp (it says "press"), so the check reads the gloss's
structure instead:

  attests     a gloss part whose head word is the concept's word or a near form
              of a word of its definition ("to press" ~ "apply pressure")
  shifted     the concept's word only with a particle ("squeeze out") or as the
              means of another head ("extract by squeezing")
  homonym     the gloss names the concept's English word but in another of its
              senses: Globasa's miza "(religious) Mass" leaned in part on Greek μάζα,
              which is mass as in physics (a lump, dough); Spanish masa "dough;
              mass (physics)" against misa "Mass". When the headword has other
              senses, the gloss's other words decide: words of the target sense
              (religious, Eucharist) attest it, words of another sense (physics,
              dough, lump) make it a homonym, none at all leaves it ambiguous (a flag)
  unattested  the entry exists but no gloss part mentions the concept: only a flag,
              since a synonym says the same thing (comprimer "to compress")
  no entry    nothing to check (no counter-evidence)

Only "shifted" and "homonym" stop a word counting as agreement: they are read
from what the gloss says, not from what it lacks.
"""

import re

PARTICLES = {"out", "off", "up", "down", "away", "in", "on", "over", "through", "back", "into", "from", "together"}
MEANS = {"by", "with", "through", "using", "via"}
STOP = set("""a an the to of or and in for is are be by with at on from as it its that this which who
something someone somebody one's oneself etc e.g i.e two more most less once side sides other another
any some all each own such very much many few kind sort type way thing things part used use make made
cause causing become being having have get especially now usually often generally particularly also
mainly chiefly typically sometimes formerly""".split())


def _tokens(s):
    return re.findall(r"[a-z]+(?:'[a-z]+)?", s.lower())


def _near(a, b):
    """Same word or near forms (press ~ pressure, squeeze ~ squeezing)."""
    if a == b:
        return True
    n = min(len(a), len(b))
    return n >= 4 and a[:max(4, n - 2)] == b[:max(4, n - 2)]


def _content(text):
    return {t for t in _tokens(text) if t not in STOP and len(t) > 2}


def concept_words(concept):
    """(headwords, definition words) of the concept's English senses."""
    heads, defs = set(), set()
    for wiki, word, pos, sense in concept.get("wikt_senses", []):
        if wiki != "en":
            continue
        heads |= {t for t in _tokens(word) if t not in STOP}
        defs |= _content(sense)
    return heads, defs


def sense_words(concept):
    """(target words, other-sense words): the content words of the concept's own
    senses (label and definition) and those only the headwords' OTHER senses use
    (mass: physics, matter, lump, dough ...)."""
    from .sources.wiktionary import index, senses_for
    target, other = set(), set()
    for wiki, word, pos, sense in concept.get("wikt_senses", []):
        if wiki != "en":
            continue
        target |= _content(sense)
        rest = []
        for s in senses_for(word):
            words = _content(s["sense"]) | _content(s["definition"])
            if s["sense"] == sense:
                target |= words
            elif s["pos"] == pos:
                rest.append(words)
        cap = word[:1].upper() + word[1:]
        for w in dict.fromkeys([word, cap]):        # mass and Mass (the liturgy)
            for e in index().entries("en", w):
                if e["pos"] in (pos, "name"):
                    rest += [_content(g["g"][-1]) for g in e["senses"]]
            if w != word:
                for s in senses_for(w):
                    rest.append(_content(s["sense"]) | _content(s["definition"]))
        # a sense sharing the target's own words is of its domain (the other
        # Eucharist senses of mass: church, celebration), not a rival; judged against
        # the original target words only, so the domain cannot snowball
        core = set(target)
        for words in rest:
            if words & core:
                target |= words
            else:
                other |= words
    heads = {t for w in concept.get("wikt_senses", []) for t in _tokens(w[1])}
    target = {w for w in target if not any(_near(w, h) for h in heads)}
    other = {w for w in other if not any(_near(w, h) for h in heads) and w not in target
             and not any(_near(w, x) for x in target)}
    return target, other


def _parts(gloss):
    """Gloss parts: split at ; and , outside parentheses, parentheses dropped."""
    g = re.sub(r"\([^)]*\)", " ", gloss)
    return [p.strip() for p in re.split(r"[;,]", g) if p.strip()]


def classify_part(part, heads, defs):
    toks = [t for t in _tokens(part)]
    while toks and toks[0] in ("to", "a", "an", "the"):
        toks = toks[1:]
    if not toks:
        return "other"
    head = toks[0]
    nxt = toks[1] if len(toks) > 1 else ""
    if any(_near(head, h) for h in heads):
        # a particle the concept itself has (squeeze out) is no shift
        return "shifted" if nxt in PARTICLES and nxt not in heads else "attests"
    if any(_near(head, d) for d in defs):
        return "attests"
    for i, t in enumerate(toks[1:], 1):
        if any(_near(t, h) for h in heads) and toks[i - 1] in MEANS:
            return "shifted"          # the concept is only the means: extract BY SQUEEZING
    if any(_near(t, h) for t in toks for h in heads):
        return "mentions"
    return "other"


def is_main_sense(concept):
    """Is the concept's sense its headword's most-translated sense of that part of
    speech? Then a bare gloss (bear) most likely means it; for religious Mass it
    does not (physics mass: 12 languages, Eucharist: 11)."""
    from .sources.wiktionary import senses_for
    for wiki, word, pos, sense in concept.get("wikt_senses", []):
        if wiki != "en":
            continue
        same = [s for s in senses_for(word) if s["pos"] == pos]
        if same and max(same, key=lambda s: s["n_langs"])["sense"] != sense:
            return False
    return True


def capitalised_sense(concept):
    """Headwords whose capitalised English form is the target sense (Mass, the
    liturgy, beside mass): a gloss writing it so names that sense."""
    from .sources.wiktionary import index
    out = set()
    for wiki, word, pos, sense in concept.get("wikt_senses", []):
        cap = word[:1].upper() + word[1:]
        if wiki == "en" and cap != word:
            target = _content(sense)
            for e in index().entries("en", cap):
                if any(_content(g["g"][-1]) & target or any(_near(a, b) for a in _content(g["g"][-1]) for b in target)
                       for g in e["senses"]):
                    out.add(word.lower())
    return out


def _which_sense(gloss, target, other, caps=(), heads=()):
    """'target', 'other' or '' from the gloss's own words (parentheses included),
    the headword itself left out (it cannot tell its own senses apart: mass ~
    massive); a capitalised headword (Mass) names the capitalised sense."""
    if any(re.search(rf"\b{re.escape(h[:1].upper() + h[1:])}\b", gloss) for h in caps):
        return "target"
    words = {w for w in _content(gloss) if not any(_near(w, h) for h in heads)}
    t = any(_near(w, x) for w in words for x in target)
    o = any(_near(w, x) for w in words for x in other)
    return "target" if t else ("other" if o else "")


_CACHE = {}


def _concept_cache(concept):
    k = repr(concept.get("wikt_senses"))
    if k not in _CACHE:
        _CACHE[k] = sense_words(concept) + (capitalised_sense(concept), is_main_sense(concept))
    return _CACHE[k]


def fit(lang, word, concept):
    """{fit: attests|shifted|homonym|ambiguous|unattested|no entry|no concept, gloss}."""
    from .sources.wiktionary import lookup
    return fit_glosses([s["gloss"] for s in lookup(lang, word)["senses"]], concept)


def etymology_for_meaning(lang, word, concept):
    """The etymology links of the word's entries that carry the concept's meaning.
    English mass is two words: the Mass < Latin missa, and physical mass < Latin
    massa < Greek μᾶζα. Following every entry's etymology brings in maza, massage,
    massive and Michaelmas, the mistake behind Globasa's miza. A word with one
    entry (or a concept with no English sense) keeps all its links."""
    from .sources.wiktionary import index
    from .languages import BY_CODE
    dump = BY_CODE[lang]["dump"] if lang in BY_CODE else lang
    entries = index().entries(dump, word)
    if len(entries) <= 1 or not concept_words(concept)[0]:
        return [x for e in entries for x in e["etym"]]
    # the concept's own English headword: only entries of the concept's part of speech
    # (mass, adjective "involving a mass of people", shares physical mass's etymology)
    pos = {p for wk, w, p, s in concept.get("wikt_senses", []) if wk == "en" and w.lower() == word.lower()}
    if lang == "en" and pos:
        entries = [e for e in entries if e["pos"] in pos] or entries
    keep = [e for e in entries if fit_glosses([s["g"][-1] for s in e["senses"]], concept)["fit"] == "attests"]
    return [x for e in keep for x in e["etym"]]


def fit_glosses(glosses, concept):
    """fit() for a list of glosses (one word, or one of its entries)."""
    heads, defs = concept_words(concept)
    if not heads:
        return {"fit": "no concept", "gloss": ""}
    target, other, caps, main = _concept_cache(concept)
    senses = [{"gloss": g} for g in glosses if g]
    if not senses:
        return {"fit": "no entry", "gloss": ""}
    rank = {"attests": 5, "ambiguous": 4, "mentions": 3, "homonym": 2, "shifted": 1, "other": 0}
    best, evidence = None, ""
    for s in senses:
        for part in _parts(s["gloss"]):
            c = classify_part(part, heads, defs)
            if c in ("attests", "mentions") and other:
                # the headword has other senses: which one does this gloss mean?
                which = _which_sense(s["gloss"], target, other, caps, heads)
                if c == "mentions":      # named in passing ("a mass of matter"): only target words confirm it
                    c = "attests" if which == "target" else ("homonym" if which == "other" else "mentions")
                else:
                    c = "attests" if which == "target" else ("homonym" if which == "other"
                                                             else ("attests" if main else "ambiguous"))
            if best is None or rank[c] > rank[best]:
                best, evidence = c, s["gloss"]
    if best in ("attests", "mentions"):
        return {"fit": "attests", "gloss": evidence}
    if best in ("shifted", "homonym", "ambiguous"):
        return {"fit": best, "gloss": evidence}
    return {"fit": "unattested", "gloss": "; ".join(s["gloss"] for s in senses[:3])}
