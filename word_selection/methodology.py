"""The passages of Globasa's documentation that justify each step of a ranking.

Sources (word_selection/docs/README.md):
  methodology  Methodology for Lexical Development (docs/methodology.eng.md, CC0)
  qa           Q&A (docs/qa.eng.md, CC0)
  grammar      the phonotactics sections of the grammar (xwexi-pages-grav submodule)

passages() cuts each document into passages: one per bullet (any depth) or
paragraph, with its section and, for a nested bullet, the bullet it hangs from.
justify(texts) maps the pipeline's explanation strings (cluster "why", proposal
trace and blend notes, collision tiers) to the passages that back them, through
RULES. A step that rests on lexicon data rather than the documentation (a spelling
norm, LexiliAsel precedent, a fallback) is reported as such, not dressed up as
methodology.
"""

import os
import re
from functools import lru_cache

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = {
    "methodology": ("Methodology for Lexical Development",
                    os.path.join(ROOT, "word_selection", "docs", "methodology.eng.md"), None),
    "qa": ("Q&A", os.path.join(ROOT, "word_selection", "docs", "qa.eng.md"), None),
    "grammar": ("Grammar: Alphabet and Pronunciation",
                os.path.join(ROOT, "xwexi-pages-grav", "03.gramati", "01.abece-ji-lafuzu", "default.eng.md"),
                "Phonotactics"),   # only the H2 sections whose title contains this
}
URLS = {"methodology": "https://www.globasa.net/eng/max/metode-fe-lexiseleti",
        "qa": "https://www.globasa.net/eng/max/swal-ji-jawabu",
        "grammar": "https://xwexi.globasa.net/eng/gramati/abece-ji-lafuzu"}


def _clean(s):
    s = re.sub(r"<a [^>]*></a>", "", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"(?<![\w*])[_*]([^_*]+)[_*](?![\w*])", r"\1", s)
    s = s.replace("&rarr;", "→").replace("\\", "")
    return re.sub(r"\s+", " ", s).strip()


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


@lru_cache(maxsize=1)
def passages():
    """[{id, doc, doc_title, url, section, text, parent}] in document order."""
    out = []
    for doc, (title, path, only) in DOCS.items():
        try:
            lines = open(path, encoding="utf-8").read().splitlines()
        except FileNotFoundError:
            continue
        h2 = h3 = ""
        in_front = False
        keep = only is None
        stack = []          # [(indent, passage)] for nested bullets
        para = []
        counter = {}

        def emit(text, parent=None):
            sec = " › ".join(x for x in (h2, h3) if x) or title
            n = counter[sec] = counter.get(sec, 0) + 1
            p = {"id": f"{doc}-{_slug(h3 or h2)}-{n}", "doc": doc, "doc_title": title, "url": URLS[doc],
                 "section": sec, "text": _clean(text), "parent": parent["text"] if parent else ""}
            out.append(p)
            return p

        def flush():
            if para and keep:
                emit(" ".join(para))
            para.clear()

        for i, line in enumerate(lines):
            if line.strip() == "---" and (i == 0 or in_front):
                in_front = not in_front
                continue
            if in_front:
                continue
            m = re.match(r"^(#{2,4})\s+(.*)", line)
            if m:
                flush()
                stack.clear()
                text = _clean(m.group(2))
                if len(m.group(1)) == 2:
                    h2, h3 = text, ""
                    keep = only is None or only in text
                else:
                    h3 = text
                continue
            b = re.match(r"^(\s*)[-*]\s+(.*)", line)
            if b and keep:
                flush()
                indent = len(b.group(1).expandtabs(4))
                while stack and stack[-1][0] >= indent:
                    stack.pop()
                p = emit(b.group(2), stack[-1][1] if stack else None)
                stack.append((indent, p))
                continue
            if not line.strip():
                flush()
                continue
            if stack and line.startswith((" ", "\t")) and keep:       # continuation of a bullet
                stack[-1][1]["text"] = _clean(stack[-1][1]["text"] + " " + line)
                continue
            stack.clear()
            para.append(line.strip())
        flush()
    return out


def find(doc, section, text):
    """The passage of `doc` whose section contains `section` and text contains `text`."""
    for p in passages():
        if p["doc"] == doc and section.lower() in p["section"].lower() and text.lower() in p["text"].lower():
            return p
    return None


M, G, Q = "methodology", "grammar", "qa"
# (pattern on an explanation string, [(doc, section, text in passage)], basis note or None)
RULES = [
    # --- source selection (cluster ranking)
    (r"\d+ famil", [(M, "Source Selection", "most language families"),
                    (M, "Source Selection", "considered one family"),
                    (M, "Source Selection", "all in different families")], None),
    (r"two or more East Asian", [(M, "Source Selection", "two or more of the East Asian")], None),
    (r"Arabic plus any other", [(M, "Source Selection", "Arabic, supported by")], None),
    (r"Hindi plus any other", [(M, "Source Selection", "Hindi, supported by")], None),
    (r"European plus any other", [(M, "Source Selection", "European languages, supported by")], None),
    (r"Persian and Turkish", [(M, "Source Selection", "Persian and Turkish")], None),
    (r"tie-break|TIED", [(M, "Source Selection", "If there is a tie")], None),
    (r"TIED|other parts of speech", [(M, "Source Selection", "more thorough search")], None),
    (r"fallback order", [(M, "Source Selection", "If there is still no agreement")], None),
    # --- blending
    (r"^BLEND$", [(M, "Exact Form", "middle ground"), (Q, "", "very closely resembles at least one")], None),
    (r"\b[aeiou] over [aeiou]\b.*letter preference", [(M, "Exact Form", "e over a")], None),
    (r"\b[bcdfghjklmnprstvwxyz] over [bcdfghjklmnprstvwxyz]\b.*letter preference",
     [(M, "Exact Form", "m over n"), (M, "Exact Form", "s over z")], None),
    (r"LexiliAsel precedent \(sino\)", [(M, "Mandarin", "blended with their"),
                                       (M, "Mandarin", "consonant plus glide"),
                                       (M, "Mandarin", "diphthongs are often reduced")],
     "LexiliAsel precedent: how existing roots applied these rules"),
    (r"LexiliAsel precedent \(arabic\)", [(M, "Arabic", "/au̯/"), (M, "Arabic", "/aj/")],
     "LexiliAsel precedent: how existing roots applied these rules"),
    (r"LexiliAsel precedent \(european\)", [(M, "European", "favor spelling of both")],
     "LexiliAsel precedent: how existing roots applied these rules"),
    (r"LexiliAsel precedent \((jako|indic)\)", [(M, "Exact Form", "middle ground")],
     "LexiliAsel precedent: how existing roots resolved such disagreements (not spelled out in the methodology)"),
    (r"loose resemblances not counted", [(M, "Exact Form", "middle ground"),
                                         (Q, "", "very closely resembles at least one")],
     "support needs a member within distance 0.30 of the proposal: 95% of LexiliAsel's cited etymons are "
     "(false friends count, as baru < Hindi balu, English bear, Indonesian beruang)"),
    (r"unverified etymology guesses", [], "an etymology-cognate guess (a fallback) creates no agreement until checked"),
    # --- shaping: final vowels
    (r"a-posteriori vowel|ends in a vowel", [(M, "Exact Form", "tend to end in a vowel"),
                                            (M, "Exact Form", "Examples of a posteriori")], None),
    (r"no final vowel", [(M, "Exact Form", "tend to end in a vowel")], None),
    (r"caveat 1", [(M, "Exact Form", "Caveat 1")], None),
    (r"caveat 3", [(M, "Exact Form", "Caveat 3")], None),
    (r"-ation noun", [(M, "Exact Form", "-ation/-ate")], None),
    (r"-ia/-io", [(M, "Exact Form", "-ia/-io")], None),
    (r"a-priori vowel", [(M, "Exact Form", "a priori vowel should only be added"),
                         (M, "Exact Form", "Indo-European (Romance"), (M, "Exact Form", "All others (Mandarin")], None),
    (r"initial e-", [(M, "Exact Form", "initial vowel e-")], None),
    (r"\d syllables? \(|syllables? \(avoid\)", [(M, "Caveats", "one-syllable words")], None),
    (r"reserved onset", [(M, "Exact Form", "le-, xa-")], None),
    (r"Middle Chinese -", [(M, "Exact Form", "All others (Mandarin")],
     "LexiliAsel precedent: how existing roots render a Middle Chinese final"),
    # --- norms from the lexicon, not the documentation
    (r"geminate simplified|n before b/p|written as glide", [],
     "a spelling norm attested in the lexicon (no root has it otherwise); not in the methodology"),
    (r"fallback", [], "a fallback: secondary data or a prediction, weigh it accordingly"),
    # --- proper nouns, culture-specific words
    (r"proper noun phonotactics|proper noun keeps", [(G, "Proper Nouns", "more lax"), (G, "Proper Nouns", "coda for proper nouns")], None),
    (r"culture-specific word phonotactics|culture-specific word:", [(G, "Culture-Specific", "follow the rules for ordinary words")], None),
    (r"pronunciation reading", [(M, "English", "rule of thumb")], None),
    (r"long vowels follow the pronunciation", [(M, "English", "long vowels")], None),
    (r"spelling \(Latin-script recognizability\)", [(M, "European", "favor spelling of both"),
                                                    (M, "European", "rum"), (Q, "", "spelling recognizability")], None),
    # --- collisions and phonotactics
    (r"^TIER NEVER$", [(M, "Caveats", "Never adopt minimal pairs")], None),
    (r"^TIER LAST_RESORT$", [(M, "Caveats", "absolutely no other option")], None),
    (r"^TIER AVOID$", [(M, "Caveats", "avoid minimal pairs with l and r")], None),
    (r"^TIER ANY$", [(M, "Caveats", "avoid any minimal pair")], None),
    (r"word-final|final consonant cluster", [(G, "Ordinary Words", "Word-final position")], None),
    (r"stop\+stop", [(G, "Ordinary Words", "Coda-onset stops")], None),
    (r"onset .* (too long|not a permitted)", [(G, "Ordinary Words", "the onset consists of")], None),
    (r"nucleus-coda|nucleus-onset|onset-nucleus", [(G, "Ordinary Words", "Nucleus-coda"),
                                                  (G, "Ordinary Words", "Nucleus-onset")], None),
]
_COMPILED = [(re.compile(p), refs, basis) for p, refs, basis in RULES]


def check_rules():
    """Rule references that match no passage (empty when the docs and RULES agree)."""
    return [(pat, ref) for pat, refs, _ in RULES for ref in refs if find(*ref) is None]


def justify(texts):
    """[{step, passages: [passage], basis}] for each explanation string with a rule,
    in order, without repeating a passage already cited for an earlier step."""
    seen, out = set(), []
    for t in texts:
        if not t:
            continue
        for rx, refs, basis in _COMPILED:
            if not rx.search(t):
                continue
            ps = [p for p in (find(*r) for r in refs) if p and p["id"] not in seen]
            seen |= {p["id"] for p in ps}
            if ps or basis:
                out.append({"step": t, "passages": ps, "basis": basis or ""})
    return out


def _steps(texts):
    """Explanation strings split into single steps ('a; b' -> 'a', 'b'; a tie-break
    list into its tie-breaks)."""
    out = []
    for t in texts:
        for part in (t or "").split("; "):
            if part.startswith("meets tie-break(s): "):
                out += part[len("meets tie-break(s): "):].split(", ")
            elif part:
                out.append(part)
    return out


def for_cluster(c):
    """Justification of a cluster's place in the source ranking."""
    return justify(_steps([c.get("why", "")]))


def for_proposal(p):
    """Justification of one proposal: its blend (or cultural reading), shaping trace,
    blend notes, minimal-pair tiers and phonotactic problems."""
    texts = []
    if p.get("kind") is None:
        texts.append("BLEND")
    texts += _steps(p.get("blend", {}).get("notes", []) + p.get("trace", []))
    col = p.get("collision") or {}
    texts += [f"TIER {m['tier']}" for m in col.get("minimal_pairs", []) if m.get("tier")]
    texts += col.get("phonotactics", [])
    return justify(texts)
