"""Keep the translations of the right gender for Globasa words marked with fem- / man-.

User 2026-11-28: femkuzin ("female cousin") vets the English table of "cousin", whose
translations mix the genders (fr cousin m + cousine f). The Globasa word says its gender
itself: the prefix fem- / man- in its LexiliAsel (word-structure) column -- the clearest
signal, so no guess from glosses (Esperanto -ino also ends insulino, benzino).

Only tables split by gender are touched: some language pairs a masculine with a feminine
form (user 2026-11-28: "only when the masculine and feminine come in pairs").
Within one language of such a table:
  - an item's gender comes from its Wiktionary tags (feminine / masculine, not both);
    Esperanto items from morphology when the table has both forms (kuzo + kuzino);
    a slash pair ("cousin/cousine") gives the half the table's Esperanto pair puts in the
    same place (kuzo/kuzino: second = feminine);
  - a language is filtered only when its items are split by gender (items of both genders, or
    a slash pair); otherwise everything stays (genderless, untagged, or a table that already
    names one sex, like "wife": grammatically neuter Weib stays);
  - otherwise only the items of the word's gender are kept; the others are dropped and
    reported (menalariExtension_gender.tsv), never guessed.
"""
import re
import unicodedata

# A table is split by gender when this many languages pair a masculine with a feminine form:
# one alone can be two words for one sex (hi गो, गऊ "cow"); they has 18, god 4.
MIN_PAIRED_LANGUAGES = 2
# The person and pronoun forms built on the bare root: femyen "woman", femte "she".
_BARE_ROOT_FORMS = {"te", "-yen"}
_INO_RE = re.compile(r"^(.*)ino(j?)$")


def word_gender(lexiliasel):
    """'f' / 'm' / None from a word's LexiliAsel ('fem- + kuzin', 'man- + duke', 'fem + te')."""
    parts = [p.strip() for p in (lexiliasel or "").split("+")]
    if len(parts) < 2:
        return None
    first = parts[0]
    if first in ("fem-", "man-") or (first in ("fem", "man") and parts[1] in _BARE_ROOT_FORMS):
        return "f" if first.startswith("fem") else "m"
    return None


def _tag_gender(t):
    tags = set((t.tags or "").split("\t"))
    if "feminine" in tags and "masculine" not in tags:
        return "f"
    if "masculine" in tags and "feminine" not in tags:
        return "m"
    return None


def _common_gender(t):
    """Tagged masculine and feminine and nothing else of gender: one word for either sex
    (grc θεός "god, goddess"). Polish "one" adds neuter: the non-masculine-personal plural."""
    tags = set((t.tags or "").split("\t"))
    return {"feminine", "masculine"} <= tags and not tags & {"neuter", "inanimate"}


def _eo_genders(items):
    """{word: 'f'/'m'} for Esperanto items whose other form is in the table too (kuzo + kuzino)."""
    words = {t.word for t in items}
    found = {}
    for w in words:
        if w.startswith("ge") and w[2:] in words:
            found[w] = "both"    # ge-: both sexes together (gekuzo), neither alone
    for w in words:
        m = _INO_RE.match(w)
        if m and (m.group(1) + "o" + m.group(2)) in words:
            found[w] = "f"
            found[m.group(1) + "o" + m.group(2)] = "m"
    return found


def pair_order(eo_items):
    """Which half of a slash pair is feminine: 1 or 2 from the table's Esperanto pair
    (kuzo/kuzino -> 2), or None when the table has no such pair."""
    for t in eo_items or ():
        halves = [h.strip() for h in t.word.split("/")]
        if len(halves) == 2:
            first_f, second_f = (bool(_INO_RE.match(h)) for h in halves)
            if second_f and not first_f:
                return 2
            if first_f and not second_f:
                return 1
    return None


def _plain(word):
    """Lowercase without diacritics or vowel points (Göttin -> gottin, הֵן -> הן)."""
    return "".join(c for c in unicodedata.normalize("NFKD", word.lower()) if not unicodedata.combining(c))


def _counterparts(a, b):
    """Two forms of one stem: a shared beginning of 3+ letters (cousin/cousine, ellos/ellas,
    Gott/Göttin), or all but the last letter of the shorter (oni/one, הם/הן). Not
    dieu/divinité, weiblicher Hirsch/Hinde."""
    if " " in a.strip() or " " in b.strip():
        return False    # phrases agree in gender without being a pair (weiblicher Gott, weibliche Gottheit)
    a, b = _plain(a), _plain(b)
    shared = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    return a != b and (shared >= 3 or (min(len(a), len(b)) >= 2 and shared >= min(len(a), len(b)) - 1))


def _gender_pair(word):
    """The two halves of a gender pair written with a slash ("cousin/cousine", "cugino/cugina"):
    no spaces around the slash, two forms of one stem. Not script variants ("內人 /内人") or
    synonyms ("sul/naïeveling")."""
    halves = word.split("/")
    if len(halves) != 2 or not all(halves) or word != word.strip() or " /" in word or "/ " in word:
        return None
    return halves if _counterparts(*halves) else None


def has_pairs(items):
    """Whether one language's items show a masculine/feminine pair: a slash pair, or an item
    tagged masculine and one tagged feminine that are forms of one stem (Gott, Göttin)."""
    items = list(items)
    if any(_gender_pair(t.word) for t in items):
        return True
    fem = [t.word for t in items if _tag_gender(t) == "f"]
    masc = [t.word for t in items if _tag_gender(t) == "m"]
    return any(_counterparts(f, m) for f in fem for m in masc)


def table_has_pairs(lang_translations):
    """Whether a table is split by gender: some language pairs a masculine with a feminine form
    (es ellos/ellas, de Gott/Göttin, eo kuzo/kuzino). User 2026-11-28: the filter applies only
    where masculine and feminine come in pairs; a table that already names one sex (hind: de
    Hinde, Hirschkuh, weiblicher Hirsch m) is left alone."""
    paired = 0
    for lang, items in lang_translations.items():
        if has_pairs(items) or (lang == "eo" and _eo_genders(items)):
            paired += 1
            if paired >= MIN_PAIRED_LANGUAGES:
                return True
    return False


def filter_items(items, gender, lang, eo_items=(), table_split=True):
    """(kept, dropped) Translations of one language for a word of `gender` ('f'/'m').
    Filtered only when the table is split by gender (table_has_pairs) and this language has
    items of both genders (or a slash pair): ils + elles once the table pairs ellos/ellas.
    A slash pair whose feminine half is known comes back as that half alone."""
    items = list(items)
    if not table_split:
        return items, []
    other = "m" if gender == "f" else "f"
    tag = "feminine" if gender == "f" else "masculine"
    eo_gender = _eo_genders(items) if lang == "eo" else {}
    order = pair_order(eo_items)
    graded = []    # (Translation, 'f' / 'm' / None)
    split = False  # a slash pair shows the language splits
    for t in items:
        halves = _gender_pair(t.word)
        if halves:
            split = True
            if order is not None:
                fem, masc = halves[order - 1], halves[2 - order]
                graded.append((t._replace(word=fem if gender == "f" else masc), gender))
            else:
                graded.append((t, "pair"))    # which half is which is not known: dropped
            continue
        graded.append((t, eo_gender.get(t.word) or _tag_gender(t)))
    other_tag = "masculine" if gender == "f" else "feminine"

    def includes(t, g, gen, gen_tag):
        return g == gen or (g is None and gen_tag in (t.tags or "").split("\t"))

    has_target = any(includes(t, g, gender, tag) for t, g in graded)
    has_other = any(includes(t, g, other, other_tag) for t, g in graded)
    if not (split or (has_target and has_other)):
        return items, []
    kept = [t for t, g in graded if g == gender or (g is None and _common_gender(t))]
    if not any(g == gender for _, g in graded):
        # No item of this gender alone: one whose tags include it among others (Polish "one",
        # feminine + masculine + neuter: every plural but the masculine-personal "oni").
        kept = [t for t, g in graded if g is None and tag in (t.tags or "").split("\t")]
    dropped = [t for t, _ in graded if t not in kept]
    return kept, dropped
