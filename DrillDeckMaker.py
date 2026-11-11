"""Globasa__Drills.apkg: procedural drills, one card per SKILL rather than per item.

A learner who sees the same word on every review memorises that word's answer
instead of learning the rule. So each card here holds a pool of generated items
(the Pool field, JSON), and the card's own JavaScript draws a fresh sample of N
of them on every review (drill_templates/drill.js). Anki schedules the skill;
the items change. Every build draws a new pool, so re-importing the package
brings new items while the note GUIDs (derived from SkillId) keep each
learner's scheduling.

First drill family: STRESS, by the rule in xwexi (gramati/abece-ji-lafuzu,
"Stress"): a polysyllabic word ending in a consonant is stressed on its last
vowel, one ending in a vowel on its second-to-last vowel. w and y are
consonants and never stressed. Derived words follow the rule like any other
word, so a suffix can move the stress (kitabu -> kitabudom) or leave it on the
same vowel (varnis -> varnisdo); the derivation skill drills both. Monosyllables are left
out: their stress is a guideline by word class, not a rule of position.

Items come from three sources, labelled on the card:
  real      words from word-list.csv (roots and derived words), with a gloss
  made-up   random words that pass word_selection.collision.phonotactics and are
            not in the lexicon -- they can only be answered by the rule
  built     root + suffix pairs not in the dictionary, built by the suffix/PoS
            table in globasa_tokenizer/affix_constraints.py; labelled "not in
            the dictionary", since the rule makes the form, not the meaning

Deck design: Anki's scheduler does the adapting. There is one card per TARGET
(a word shape that can be weak on its own), so a shape the learner keeps
missing gets Again and comes back sooner, while a mastered one drifts to long
intervals -- adaptivity that needs no stored statistics and syncs like any card.
But a card that holds only its target shape lets the learner answer from the
card instead of the word (user, 2026-11-11), so:
  - every card's front is identical ("Stress", "Tap the stressed vowel.");
  - a round mixes 3 target items with 2 items of the other targets, shuffled
    (drill.js; Pool = {"t": target items, "o": other items});
  - every target holds both endings half and half, so "last vowel" and
    "second-to-last vowel" answers are equally likely on every card. Plain
    consonant-final and vowel-final words are therefore ONE target ("plain"),
    since either alone would always have the same answer.
The suggested rating counts mistakes on target items only (0 Good, 1 Hard,
2+ Again), so the score measures that card's shape. After a miss the next item
is a fresh word of the same shape. Notes are ordered for introduction (Anki
shows new cards in that order): plain, after a suffix, w/y, vowels side by side.

Second family: LISTENING, from Hector's recordings only (the lesson word-list
clips; lesson 17's are a synthesized voice and are left out). A clip plays and
the learner taps the spelling heard among three: the word and two look-alikes
that each change one sound (x/s, r/l, e/i, p/b ...) and still obey the sound
rules, so they cannot be ruled out by spelling alone. The look-alikes are drawn
afresh at every showing from all those the word allows. A recording cannot be
made up, so the novelty is in the choices, not the word.
Here the TARGET of a card is a SPEAKER x CONTRAST pair (user, 2026-11-11):
several cards per speaker, each favouring one contrast group (s z x c j; r l;
e i o u; voicing). A round is 3 clips of that speaker and contrast plus 2 others
(the speaker's other contrasts, and other speakers' clips once there are any),
so Anki brings back sooner the voice and the sound the learner gets least.
A miss is followed by another clip testing the same contrast group.

Third family: DICTATION, the typed version for a keyboard (desktop or laptop):
the clip plays and the learner types what was heard; any difference is a
mistake, and the back aligns the typing with the word letter by letter, naming
each sound confused. Same speaker x contrast cards, in a subdeck of its own
(Globasa::Drills::Dictation) so it can be left out on a phone.
"""
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import tempfile
import zipfile

import pandas as pd
from anki.collection import Collection, ExportAnkiPackageOptions
from anki import import_export_pb2 as pb
from anki.generic_pb2 import Empty

from globasa_tokenizer.affix_constraints import SUFFIX_BASE_POS
from word_selection.collision import ONSET2, phonotactics
from xwexi_lessons import LESSONS_DIR, SYNTHESIZED_LESSONS, clip_name, lesson_entries, spoken_forms

APKG = "Globasa__Drills.apkg"
DECK = "Globasa::Drills"
NOTETYPE = "Globasa drill"
TEMPLATE_DIR = "drill_templates"
WORDLIST = "word-list.csv"
PER_TARGET = 200         # target items per card, half per ending
OTHER_PER_TARGET = 50    # items each OTHER target lends a card's "o" list, half per ending
MADE_UP_SHARE = 1 / 3    # of each non-derivation target
BUILT_SHARE = 1 / 2      # of the derivation target
SEED = None              # an int makes the pools reproducible; None draws fresh ones each build

# Heading is what the front shows: the drill family only. Title names the skill
# and appears on the back alone -- a pattern name on the front would give the
# answer away ("ends in a consonant" says which vowel to tap).
# Media lists every recording a card's pool can play, as [sound:] tags. The
# templates never show it; it is there so Anki's exporter packs the files and
# Check Media does not call them unused (the pool's JSON names them in a way
# Anki does not scan). Never insert it into a template: it would play them all.
FIELDS = ["SkillId", "Heading", "Title", "Prompt", "Kind", "Pool", "Rule", "Media"]
VOWELS = "aeiou"

# Suffixes for built derivations: ones that take a noun base in the suffix/PoS
# table, so any b-class root qualifies. Frequent ones first; all are attested.
BUILD_SUFFIXES = ["li", "yen", "do", "ya", "gi", "cu", "pul", "fil", "kal", "dom",
                  "tul", "xey", "mon", "tim", "kef", "sa"]
assert all("N" in SUFFIX_BASE_POS[s] for s in BUILD_SUFFIXES)

RULE_HTML = """<div class="drill-rule"><b>Stress</b> (Xwexi: Alphabet and Pronunciation)
<ul>
<li>Ends in a consonant: stress the <b>last</b> vowel. <i>ba-r<u>i</u>x, pan-ta-l<u>u</u>n</i></li>
<li>Ends in a vowel: stress the <b>second-to-last</b> vowel. <i>ha-r<u>i</u>-ta, p<u>i</u>-u</i></li>
<li><i>w</i> and <i>y</i> are consonants, never stressed.</li>
<li>Derived words follow the same rule, so a suffix moves the stress: <i>ki-t<u>a</u>-bu</i> → <i>ki-ta-bu-d<u>o</u>m</i>.</li>
</ul></div>"""

PROMPT = "Tap the stressed vowel."
LISTEN_PROMPT = "Tap the spelling you hear."
DICTATE_PROMPT = "Type what you hear, then Enter."
# (target shape, Title shown on the back), in order of introduction.
TARGETS = [
    ("plain", "Stress · plain words"),
    ("derivation", "Stress · after a suffix"),
    ("w-y", "Stress · words with w or y"),
    ("vowel-pairs", "Stress · vowels side by side"),
]
# (SkillId, Title, Prompt, Kind); families are filled in below, in deck order.
SKILLS = [(f"stress:{t}", title, PROMPT, "stress") for t, title in TARGETS]


# ---- the rule ----

def stress_index(w):
    """Index in w of the stressed vowel, by the xwexi rule (polysyllabic words)."""
    vs = [i for i, c in enumerate(w) if c in VOWELS]
    if len(vs) < 2:
        return vs[0] if vs else None
    return vs[-1] if w[-1] not in VOWELS else vs[-2]


def why(w):
    if w[-1] in VOWELS:
        text = "ends in a vowel → stress on the second-to-last vowel"
    else:
        text = f"ends in a consonant ({w[-1]}) → stress on the last vowel"
    if re.search(r"[aeiou]{2}", w):
        text += "; side-by-side vowels are separate syllables"
    if re.search(r"[wy]", w):
        text += "; w and y are consonants"
    return text


def shape(w):
    """The one word shape a word belongs to; w/y and vowel pairs first, as the harder cases."""
    if re.search(r"[wy]", w):
        return "w-y"
    if re.search(r"[aeiou]{2}", w):
        return "vowel-pairs"
    return "plain"


def bucket(item):
    """(shape, ends in a vowel) -- the unit the pool is balanced on."""
    return item["shape"], item["w"][-1] in VOWELS


def marked(w):
    """kitabu -> kitAbu style, for the derivation explanation."""
    i = stress_index(w)
    return w[:i] + w[i].upper() + w[i + 1:]


def first_gloss(eng):
    """'n: library, bookroom; v: ...' -> 'library'."""
    eng = re.sub(r"^[^:]{1,20}:\s*", "", str(eng))
    eng = re.split(r"[;,]", eng)[0]
    return re.sub(r"_", "", eng).strip()


def polysyllabic(w):
    return isinstance(w, str) and re.fullmatch(r"[a-z]+", w) is not None and \
        sum(c in VOWELS for c in w) >= 2


# ---- sources ----

def real_items(df):
    items = []
    for w, eng in zip(df.Word, df.TranslationEng):
        if polysyllabic(w):
            items.append({"k": "stress", "w": w, "s": stress_index(w), "why": why(w),
                          "src": "real", "g": first_gloss(eng), "shape": shape(w)})
    return items


CONSONANTS = "bcdfghjklmnprstvxz"
# Syllable-final consonants for made-up words: any consonant is legal medially,
# but stops and affricates there (dofcifpo) look nothing like Globasa. Draw from
# the word-final set (f l m n r s w x y), weighted toward n, r, l, s.
CODAS = "nnnrrrlllsssmmxfwy"


def made_up_word(rng):
    """Random (C)(C)V(C) syllables; phonotactics() decides what survives."""
    syllables = rng.choice([2, 2, 3, 3, 3, 4])
    out = ""
    for k in range(syllables):
        r = rng.random()
        if r < 0.12 and k > 0:
            onset = ""                                   # hiatus: pi-u
        elif r < 0.22:
            onset = rng.choice(sorted(ONSET2))
        elif r < 0.30:
            onset = rng.choice("wy")
        else:
            onset = rng.choice(CONSONANTS)
        coda = rng.choice(CODAS) if rng.random() < 0.3 else ""
        out += onset + rng.choice(VOWELS) + coda
    return out


def root_spelling_ok(w):
    """xwexi Spelling Convention (root words): next to another vowel, i and u are
    written only when stressed; otherwise y and w. 'kiapo' would be spelt 'kyapo'."""
    s = stress_index(w)
    for i, c in enumerate(w):
        if c in "iu" and i != s and ((i > 0 and w[i - 1] in VOWELS) or
                                     (i + 1 < len(w) and w[i + 1] in VOWELS)):
            return False
    return True


def made_up_items(rng, lexicon, quota):
    """Made-up words filling quota {(shape, ends in vowel): n}."""
    buckets = {b: [] for b in quota}
    seen = set()
    tries = 0
    while tries < 400000 and any(len(buckets[b]) < n for b, n in quota.items()):
        tries += 1
        w = made_up_word(rng)
        if w in seen or w in lexicon or phonotactics(w) or not root_spelling_ok(w):
            continue
        seen.add(w)
        item = {"k": "stress", "w": w, "s": stress_index(w), "why": why(w),
                "src": "made-up", "shape": shape(w)}
        b = bucket(item)
        if b in buckets and len(buckets[b]) < quota[b]:
            buckets[b].append(item)
    return buckets


def derivation_item(root, suffix, src, gloss=None):
    w = root + suffix
    explanation = (f"{marked(root)} + -{suffix} → {marked(w)}: " + why(w))
    item = {"k": "stress", "w": w, "s": stress_index(w), "why": explanation,
            "src": src, "hint": f"{root} + -{suffix}", "shape": "derivation"}
    if gloss:
        item["g"] = gloss
    return item


def real_derivations(df, lexicon):
    """Attested 'root + -suffix' words whose spelling is exactly root + suffix."""
    out = []
    for w, asel, eng in zip(df.Word, df.LexiliAsel, df.TranslationEng):
        m = re.fullmatch(r"\s*([a-z]+)\s*\+\s*-([a-z]+)\s*", str(asel))
        if not m or not polysyllabic(w):
            continue
        root, suffix = m.groups()
        if w == root + suffix and root in lexicon and polysyllabic(root):
            out.append(derivation_item(root, suffix, "real", first_gloss(eng)))
    return out


def built_derivations(df, lexicon, rng, n_vowel_final, n_consonant_final):
    roots = [w for w, cat, cls in zip(df.Word, df.Category, df.WordClass)
             if cat == "root" and str(cls).startswith("b") and polysyllabic(w)]
    want = {True: n_vowel_final, False: n_consonant_final}
    out = {True: [], False: []}
    seen = set()
    tries = 0
    while any(len(out[e]) < want[e] for e in want) and tries < 50000:
        tries += 1
        root, suffix = rng.choice(roots), rng.choice(BUILD_SUFFIXES)
        w = root + suffix
        ends_vowel = w[-1] in VOWELS
        if len(out[ends_vowel]) >= want[ends_vowel] or w in seen or w in lexicon or phonotactics(w):
            continue
        seen.add(w)
        out[ends_vowel].append(derivation_item(root, suffix, "built"))
    return out[True] + out[False]


def take(rng, items, n):
    items = list(items)
    rng.shuffle(items)
    return items[:n]


def quotas(total, sources):
    """Split `total` items of one (shape, ending) bucket between sources {name: share}."""
    out, left = {}, total
    for name, share in list(sources.items())[:-1]:
        out[name] = round(total * share)
        left -= out[name]
    out[list(sources)[-1]] = left
    return out


def build_targets(df, rng):
    """PER_TARGET items for each target shape, half per ending."""
    lexicon = set(df.Word.dropna())
    real = {}
    for it in real_items(df[df.Category.isin(["root", "derived"])]):
        real.setdefault(bucket(it), []).append(it)
    for it in real_derivations(df, lexicon):
        real.setdefault(bucket(it), []).append(it)

    per_bucket = {}
    for sh, _ in TARGETS:
        per_bucket[(sh, True)] = PER_TARGET // 2
        per_bucket[(sh, False)] = PER_TARGET - PER_TARGET // 2

    made_quota = {b: quotas(n, {"made-up": MADE_UP_SHARE, "real": 1})["made-up"]
                  for b, n in per_bucket.items() if b[0] != "derivation"}
    made = made_up_items(rng, lexicon, made_quota)
    built = built_derivations(df, lexicon, rng,
                              round(per_bucket[("derivation", True)] * BUILT_SHARE),
                              round(per_bucket[("derivation", False)] * BUILT_SHARE))
    for it in built:
        made.setdefault(bucket(it), []).append(it)

    targets = {sh: [] for sh, _ in TARGETS}
    for b, n in per_bucket.items():
        generated = made.get(b, [])
        targets[b[0]] += generated + take(rng, real.get(b, []), n - len(generated))
    for items in targets.values():
        rng.shuffle(items)
    return targets


def card_pools(targets, rng):
    """Per card: its target items, plus OTHER_PER_TARGET items of every other
    target (half per ending) for the two non-counting slots of each round."""
    pools = {}
    for sh, _ in TARGETS:
        other = []
        for osh, _ in TARGETS:
            if osh == sh:
                continue
            for ends_vowel in (True, False):
                side = [it for it in targets[osh] if (it["w"][-1] in VOWELS) == ends_vowel]
                other += take(rng, side, OTHER_PER_TARGET // 2)
        rng.shuffle(other)
        pools[f"stress:{sh}"] = {"t": targets[sh], "o": other}
    return pools


# ---- listening ----

# (speaker, clip directory); more speakers are added here as their recordings arrive.
SPEAKERS = [
    ("Hector", "/media/paleos/Warehouse2/Applications/Segmentation/Ektor_su_Lafuzu_processed"),
]

# What each letter sounds like (xwexi Alphabet and Pronunciation), for the reasons.
SOUND = {"s": "s [s]", "z": "z [z]", "x": "x [ʃ] (sh)", "j": "j [dʒ] (j in jam)",
         "c": "c [tʃ] (ch)", "r": "r [ɾ] (tapped)", "l": "l [l]", "e": "e [e]",
         "i": "i [i]", "o": "o [o]", "u": "u [u]", "p": "p", "b": "b", "t": "t",
         "d": "d", "k": "k", "g": "g [g] (hard)", "f": "f", "v": "v"}
# Contrast groups: the item's shape, so a miss is followed by the same group.
# Each letter lists the letters a learner may hear it as.
CONTRASTS = {
    "sibilants": {"s": "xz", "z": "sj", "x": "sc", "j": "zc", "c": "xj"},
    "r-l": {"r": "l", "l": "r"},
    "vowels": {"e": "i", "i": "e", "o": "u", "u": "o"},
    "voicing": {"p": "b", "b": "p", "t": "d", "d": "t", "k": "g", "g": "k", "f": "v", "v": "f"},
}
# An item needs one look-alike from its own group (the contrast it tests); the
# second choice may come from any group (x), since r/l has a single partner.


CONTRAST_NAMES = {"sibilants": "s z x c j", "r-l": "r and l", "vowels": "e i o u",
                  "voicing": "p b t d k g f v"}
# Cards: speaker x contrast, for the tap version and then the typed one.
for kind, family, prompt in (("listen", "Listening", LISTEN_PROMPT), ("dictate", "Dictation", DICTATE_PROMPT)):
    SKILLS += [(f"{kind}:{name.lower()}:{group}", f"{family} · {name} · {CONTRAST_NAMES[group]}", prompt, kind)
               for name, _ in SPEAKERS for group in CONTRASTS]


def lesson_numbers():
    return sorted(int(d) for d in os.listdir(LESSONS_DIR) if d.isdigit())


def lesson_glosses():
    """clip name -> gloss, and the clip names of synthesized lessons."""
    gloss, synth = {}, set()
    for n in lesson_numbers():
        for entry, g in lesson_entries(n):
            for spoken in spoken_forms(entry):
                name = clip_name(spoken)
                if n in SYNTHESIZED_LESSONS:
                    synth.add(name)
                else:
                    gloss.setdefault(name, re.sub(r"[_*]", "", g).strip())
    return gloss, synth


def foils(text, group):
    """[[spelling, contrast]] for every one-letter change in this group whose
    words all obey the sound rules."""
    out, seen = [], set()
    for i, ch in enumerate(text):
        for alt in CONTRASTS[group].get(ch, ""):
            f = text[:i] + alt + text[i + 1:]
            if f in seen or f == text:
                continue
            if any(phonotactics(w) for w in f.split()):
                continue
            seen.add(f)
            out.append([f, f"{SOUND[ch]}, not {SOUND[alt]}"])
    return out


def listen_items(speaker, clip_dir, gloss, synth):
    """One item per (clip, contrast group) with a look-alike in that group and at
    least two look-alikes in all. Returns the items and {media name: source path}."""
    items, media = [], {}
    for fn in sorted(os.listdir(clip_dir)):
        name, ext = os.path.splitext(fn)
        if ext != ".ogg" or name in synth or not re.fullmatch(r"[a-z]+(_[a-z]+)*", name):
            continue
        text = name.replace("_", " ")
        # The name LafuzuDeckMaker gives the same file, so both decks share it.
        media_name = f"lafuzu_darsu_{fn}"
        by_group = {g: foils(text, g) for g in CONTRASTS}
        for group, fs in by_group.items():
            extra = [f for g, other in by_group.items() if g != group for f in other]
            if not fs or len(fs) + len(extra) < 2:
                continue
            item = {"k": "listen", "w": text, "a": media_name, "f": fs, "x": extra,
                    "src": speaker, "shape": group}
            if gloss.get(name):
                item["g"] = gloss[name]
            items.append(item)
            media[media_name] = os.path.join(clip_dir, fn)
    return items, media


# ---- templates ----

def template_js():
    with open(os.path.join(TEMPLATE_DIR, "drill.js"), encoding="utf-8") as f:
        js = f.read()
    # Anki would read these as field references and break the card.
    if "{{" in js or "}}" in js:
        raise SystemExit("drill.js contains a double brace; Anki would read it as a field reference")
    return js


def pool_json(items):
    # Inside <script type="application/json">: keep '<' out so no '</script>' can end it early.
    text = json.dumps(items, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    if "{{" in text or "}}" in text:
        raise SystemExit("pool JSON contains a double brace")
    return text


JS = template_js()
FRONT = """<div class="drill" data-skill="{{SkillId}}" data-kind="{{Kind}}">
<div class="drill-title">{{Heading}}</div>
<div class="drill-prompt">{{Prompt}}</div>
<div class="drill-stage"></div>
<script type="application/json" class="drill-pool">{{Pool}}</script>
</div>
<script>
""" + JS + """
(function () { var r = document.querySelectorAll(".drill"); window.GlobasaDrill.front(r[r.length - 1]); })();
</script>"""
BACK = """<div class="drill-back" data-skill="{{SkillId}}" data-kind="{{Kind}}">
<div class="drill-title">{{Title}}</div>
<div class="drill-summary"></div>
{{Rule}}
<script type="application/json" class="drill-pool">{{Pool}}</script>
</div>
<script>
""" + JS + """
(function () { var r = document.querySelectorAll(".drill-back"); window.GlobasaDrill.back(r[r.length - 1]); })();
</script>"""
with open(os.path.join(TEMPLATE_DIR, "drill.css"), encoding="utf-8") as f:
    CSS = f.read()
TEMPLATE_NAME = "Drill"


def unpack(apkg, workdir):
    with zipfile.ZipFile(apkg) as z:
        z.extractall(workdir)
    packed = os.path.join(workdir, "collection.anki21b")
    db = os.path.join(workdir, "collection.anki2")
    if os.path.exists(packed):
        r = subprocess.run(["zstd", "-d", packed, "-o", db, "-f"], capture_output=True)
        if r.returncode != 0:
            raise RuntimeError(f"zstd failed: {r.stderr.decode()}")
        os.remove(packed)
    return db


def ensure_notetype(col):
    mm = col.models
    nt = mm.by_name(NOTETYPE)
    if nt is None:
        nt = mm.new(NOTETYPE)
        for name in FIELDS:
            mm.add_field(nt, mm.new_field(name))
        t = mm.new_template(TEMPLATE_NAME)
        t["qfmt"], t["afmt"] = FRONT, BACK
        mm.add_template(nt, t)
        nt["css"] = CSS
        mm.add(nt)
        nt = mm.by_name(NOTETYPE)
    # Templates and styling follow this file on every run.
    for name in FIELDS:
        if name not in mm.field_names(nt):
            mm.add_field(nt, mm.new_field(name))
    for t in nt["tmpls"]:
        if t["name"] == TEMPLATE_NAME:
            t["qfmt"], t["afmt"] = FRONT, BACK
    nt["css"] = CSS
    mm.update_dict(nt)
    return mm.by_name(NOTETYPE)


# ---- build ----

rng = random.Random(SEED)
df = pd.read_csv(WORDLIST, dtype=str)
pools = card_pools(build_targets(df, rng), rng)
rules = {"stress": RULE_HTML, "listen": None}

gloss, synth = lesson_glosses()
speaker_items, media_files = {}, {}
for name, clip_dir in SPEAKERS:
    if not os.path.isdir(clip_dir):
        raise SystemExit(f"recordings of {name} not found: {clip_dir}")
    speaker_items[name], files = listen_items(name, clip_dir, gloss, synth)
    media_files.update(files)
OTHER_PER_GROUP = 40   # per other (speaker, contrast) pair in a card's "o" list


def as_kind(it, kind):
    """A listening item as the given kind; dictation needs no look-alikes."""
    if kind != "dictate":
        return it
    out = {k: it[k] for k in ("w", "a", "src", "shape", "g") if k in it}
    out["k"] = "dictate"
    return out


for kind in ("listen", "dictate"):
    for name, _ in SPEAKERS:
        for group in CONTRASTS:
            target = [as_kind(it, kind) for it in speaker_items[name] if it["shape"] == group]
            other = [as_kind(it, kind) for sp, _ in SPEAKERS for g in CONTRASTS if (sp, g) != (name, group)
                     for it in take(rng, [i for i in speaker_items[sp] if i["shape"] == g], OTHER_PER_GROUP)]
            rng.shuffle(other)
            pools[f"{kind}:{name.lower()}:{group}"] = {"t": target, "o": other}

LISTEN_RULE = ("<div class=\"drill-rule\"><b>Sounds</b> (Xwexi: Alphabet and Pronunciation)<ul>"
               "<li>s [s] · z [z] · x [ʃ] as in <i>sh</i> · c [tʃ] as in <i>ch</i> · j [dʒ] as in <i>jam</i></li>"
               "<li>r is a single tap [ɾ], l is [l]</li>"
               "<li>e [e] and i [i], o [o] and u [u] are kept apart</li>"
               "<li>p/b, t/d, k/g, f/v differ only in voicing</li></ul>"
               "<p>Recordings: Hector's readings of the xwexi lesson word lists.</p></div>")
rules["listen"] = LISTEN_RULE
rules["dictate"] = LISTEN_RULE.replace("<p>Recordings:", "<p>Type exactly what you hear: one letter per sound. Recordings:")

workdir = tempfile.mkdtemp(prefix="drills_")
db = unpack(APKG, workdir) if os.path.exists(APKG) else os.path.join(workdir, "collection.anki2")
col = Collection(db)
nt = ensure_notetype(col)
existing = {col.get_note(nid).guid: nid for nid in col.find_notes(f'"note:{NOTETYPE}"')}

# Skills dropped from SKILLS leave the package (a learner's imported copy keeps
# them until deleted by hand: Anki's import never removes notes).
live = {"glb-drill-" + hashlib.sha1(s.encode()).hexdigest()[:12] for s, _, _, _ in SKILLS}
retired = [nid for guid, nid in existing.items() if guid not in live]
if retired:
    print("removed from the package:", ", ".join(col.get_note(n)["SkillId"] for n in retired))
    col.remove_notes(retired)

added = updated = 0
FAMILY_NAMES = {"stress": "Stress", "listen": "Listening", "dictate": "Dictation"}
for skill, title, prompt, kind in SKILLS:
    family = FAMILY_NAMES[kind]
    deck_id = col.decks.id(f"{DECK}::{family}", create=True)
    sounds = ""
    if kind in ("listen", "dictate"):
        used = sorted({it["a"] for part in ("t", "o") for it in pools[skill][part]})
        for m in used:
            target = os.path.join(col.media.dir(), m)
            if not os.path.exists(target):
                shutil.copyfile(media_files[m], target)
        sounds = "".join(f"[sound:{m}]" for m in used)
    values = {"SkillId": skill, "Heading": family, "Title": title,
              "Prompt": prompt, "Kind": kind,
              "Pool": pool_json(pools[skill]), "Rule": rules[kind], "Media": sounds}
    tags = ["drill", kind]
    guid = "glb-drill-" + hashlib.sha1(skill.encode()).hexdigest()[:12]
    if guid in existing:
        note = col.get_note(existing[guid])
        for f in FIELDS:
            note[f] = values[f]
        note.tags = tags
        col.update_note(note)
        updated += 1
        cards = [c.id for c in note.cards() if c.did != deck_id]
        if cards:
            col.set_deck(cards, deck_id)
    else:
        note = col.new_note(nt)
        note.guid = guid
        for f in FIELDS:
            note[f] = values[f]
        note.tags = tags
        col.add_note(note, deck_id)
        added += 1

# New cards are introduced in SKILLS order.
order = []
for skill, _, _, _ in SKILLS:
    nid = col.find_notes(f'"note:{NOTETYPE}" "SkillId:{skill}"')[0]
    order += [c.id for c in col.get_note(nid).cards() if c.type == 0]
if order:
    col.sched.reposition_new_cards(order, starting_from=1, step_size=1,
                                   randomize=False, shift_existing=False)

for skill, _, _, kind in SKILLS:
    for part, label in (("t", "target"), ("o", "other ")):
        items = pools[skill][part]
        src, shapes = {}, {}
        for it in items:
            src[it["src"]] = src.get(it["src"], 0) + 1
            shapes[it["shape"]] = shapes.get(it["shape"], 0) + 1
        if kind == "stress":
            last = sum(it["w"][-1] not in VOWELS for it in items)
            print(f"{skill:20} {label} {len(items):4}  last vowel {last:3} / second-to-last {len(items) - last:3}"
                  f"  {src}  {shapes if part == 'o' else ''}")
        else:
            clips = len({it["a"] for it in items})
            print(f"{skill:20} {label} {len(items):4} items from {clips} clips  {src}  {shapes}")
if synth:
    print(f"left out: {len(synth)} clip names of synthesized lesson(s) {sorted(SYNTHESIZED_LESSONS)}")
print(f"{added} notes added, {updated} updated")

col.export_anki_package(
    out_path=os.path.abspath(APKG),
    options=ExportAnkiPackageOptions(with_scheduling=False, with_deck_configs=True,
                                     with_media=True, legacy=False),
    limit=pb.ExportLimit(whole_collection=Empty()),
)
col.close()
shutil.rmtree(workdir, ignore_errors=True)
print(f"wrote {APKG}")
