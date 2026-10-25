"""The word lists of the xwexi lessons (02.darsu/NN), as Hector reads them in
darsu_NN_lexilista.mp3. Shared by lesson_audio_labels.py, which proposes how to
cut those recordings, and LafuzuDeckMaker.py, which builds cards from the cuts.
"""
import itertools
import os
import re

# Anchored to this file: the Word Viewer imports it from wherever it was started.
LESSONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "xwexi-pages-grav", "02.darsu")

# Lessons whose word-list recording is a synthesized voice, not Hector's. Their
# clips are not his pronunciation and must not be presented as such.
SYNTHESIZED_LESSONS = {17}

_ENTRY = re.compile(
    r"\s*\* \*\*(.+?)\*\*"
    r"(?:\s*\(\*\*(\w+)\*\*/\*\*(\w+)\*\*\))?"   # kenumer (te/to)
    r"\s*-\s*(.+)")


def lesson_entries(n):
    """[(word, gloss)] in page order, without the repeats and usage notes that
    follow the list ("**doste** - _friend_ or _friends_"). A correlative listed
    with its pronouns -- "**kenumer** (**te**/**to**) - how many" -- is read as
    three items, kenumer, kenumer te, kenumer to, so it yields three entries."""
    page = open(f"{LESSONS_DIR}/{n:02d}/default.eng.md", encoding="utf-8").read()
    m = re.search(r"lexilista\.mp3.*?</audio>(.*?)(?:<audio|\Z)", page, re.S)
    out, seen = [], set()
    for line in (m.group(1) if m else "").splitlines():
        e = _ENTRY.match(line)
        if not e:
            continue
        word, te, to, gloss = e.group(1).strip(), e.group(2), e.group(3), e.group(4).strip()
        forms = [(word, gloss)]
        if te and to:
            forms += [(f"{word} {te}", f"{gloss} (+ {te})"),
                      (f"{word} {to}", f"{gloss} (+ {to})")]
        for w, g in forms:
            if w not in seen:
                seen.add(w)
                out.append((w, g))
    return out


def spoken_forms(entry):
    """What a recording of a list entry may actually say, fullest first:
    "pala (yon/in)" -> pala yon, pala in, pala; "(fe) ban mara" -> fe ban
    mara, ban mara; "max... kom..." -> max kom."""
    text = entry.replace("...", " ")
    full = re.sub(r"[()]", "", text)
    bare = re.sub(r"\([^)]*\)", "", text)
    out = []
    for form in (full, bare):
        options = [tok.split("/") for tok in form.split()]
        for combo in itertools.product(*options):
            spoken = " ".join(combo)
            if spoken and spoken not in out:
                out.append(spoken)
    return out


def clip_name(spoken):
    """Ektor_su_Lafuzu_processed names a clip by its words, underscored."""
    return "_".join(spoken.split())
