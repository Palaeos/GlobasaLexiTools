"""How promising a Wiktionary sense is for a Globasa word: the ranking of sense_vetter.py, importable.

sense_vetter.py lists senses most obvious first; the sense generator ("Wiktionary sense based
translation extender 3.py") orders each word's rows the same way in GLB_ENG_WiktionarySenses.xlsx,
so vetters working in the spreadsheet also meet the most promising senses of a word and part of
speech first. No model and no verdicts beyond the script's own suggestion: the cues are the
word's other glosses, the translations, taxa and tags, measured on vetted rows (cerebrum
2026-11-04).

    glosses = load_glosses(WORD_LIST)
    senses = senses_from_rows(sense_rows.rows(db, markings), glosses)
    by_word, tags = rank(senses, glosses)        # adds "score", "why", "gloss_pos", ...
    ordered = sorted(senses.values(), key=lambda s: order_key(s, ranks))

Importing this module does nothing else (unlike sense_vetter.py, which starts its server).
"""
import collections
import csv
import hashlib
import os
import re
import sys
import unicodedata

import sense_rows

HUMAN_TIERS = ("v", "e")  # vetted, expert

# Sheet column -> word-list column, with the two proofread languages first.
LANGUAGES = {"Epo": ("TranslationEpo", "Eo"), "Spa": ("TranslationSpa", "Es"),
             "French": ("TranslationFra", "Fr"), "German": ("TranslationDeu", "De"),
             "Russian": ("TranslationRus", "Ru"), "Mandarin": ("TranslationZho", "Zh"),
             "Hindi": ("TranslationHin", "Hi"), "Arabic": ("TranslationAra", "Ar")}
FIELD_LABEL = re.compile(r"^[a-z][a-z ,'-]{2,30}:")
REGISTER = re.compile(r"\b(slang|vulgar|archaic|obsolete|dated|dialect\w*|nonstandard|colloquial|derogatory)\b")
STOP = {"the", "and", "for", "with", "that", "this", "from", "which", "used", "not", "are", "was"}
BINOMIAL = re.compile(r"(?:(?<=[a-z,;:] )|(?<=\())([A-Z][a-z]{3,}) ([a-z]{3,})\b")
HIGHER_TAXON = re.compile(r"\b(?:genus|family|order|subfamily|class|species|tribe|subspecies|suborder|phylum)\s+([A-Z][a-z]{3,})\b"
                          r"|\b([A-Z][a-z]{3,}(?:idae|aceae|ales|inae|oidea|iformes|ineae))\b")
GLOSS_NOTE = re.compile(r"_([A-Z][a-z]+(?: [a-z]+)?)_")  # Panthera tigris, Aves; two letters would be element symbols
MIN_TAG_WORDS = 5  # a tag with fewer words cannot show which words of a definition are typical of it
NOT_A_GENUS = re.compile(r"(?:an|ish|ese|ic|ch)$|^(?:Latin|Greek|Thai|Swiss|Human)$")  # American marten, Latin plumbum
BIOLOGICAL_TAGS = {"hewan", "mamoyen", "piu", "mahi", "planta", "fruta", "sabzi", "flura", "bio"}  # a species name fits these
ADV_LABEL = re.compile(r"(?:^|;\s*)adv\b")
TOKEN = re.compile(r"[^\W\d_]+")
TERM_NOTES = re.compile(r"<[^>]*>|\([^)]*\)|_[^_]*_")
TERM_POS = re.compile(r"(^|[;,])\s*[^\s,;:]{1,6}:")
TERM_SPLIT = re.compile(r"[,;/、，；]")


def text(value):
    return str(value).strip() if value is not None else ""


def content_tokens(value):
    normal = unicodedata.normalize("NFKC", value).lower()
    return {w for w in TOKEN.findall(normal) if len(w) > 2 and w not in STOP}


def terms(value):
    """Split a translation cell or gloss into comparable terms, without notes or PoS prefixes."""
    normal = unicodedata.normalize("NFKC", value).lower()
    normal = TERM_POS.sub(r"\1", TERM_NOTES.sub("", normal))
    return [t.strip(" /") for t in TERM_SPLIT.split(normal) if t.strip(" /")]


def load_glosses(word_list="word-list.csv"):
    """{word (lowercase): word-list row}."""
    if not os.path.exists(word_list):
        sys.exit(f"{word_list} is missing: run ./setup.sh --vetter first.")
    with open(word_list, encoding="utf-8") as f:
        return {r["Word"].strip().lower(): r for r in csv.DictReader(f)}


def load_ranks(ranking_file="Doxo_course_ranking.csv"):
    """{word: position in the course}; words met earlier sort first among equal scores."""
    ranks = {}
    if not os.path.exists(ranking_file):
        print(f"  {ranking_file} not found: senses with equal scores keep word-list order (fallback: no course order)")
        return ranks
    with open(ranking_file, encoding="utf-8") as f:
        for rank, row in enumerate(csv.reader(f, delimiter="\t"), start=1):
            if row:
                ranks.setdefault(row[0].strip().lower(), rank)
    return ranks


def row_id(word, label):
    """The sense id shared by the page, its log and the queue: sha1 "word|label"[:16]."""
    return hashlib.sha1(f"{word}|{label}".encode()).hexdigest()[:16]


def compare_translations(row, col, entry):
    """Return per-language comparisons of this sense's translations with the word's own glosses."""
    compared = []
    for column, (gloss_column, short) in LANGUAGES.items():
        # Slashes marked a mismatch against an older word list, so they are recomputed here.
        cell = text(row[col[column]]) if column in col else ""
        if not cell:
            continue
        own = set(terms(entry.get(gloss_column, "")))
        if not own:
            continue
        found = [{"t": t, "hit": t in own} for t in dict.fromkeys(terms(cell))]
        if found:
            compared.append({"lang": short, "terms": found, "hit": any(f["hit"] for f in found)})
    return compared


def senses_from_rows(rows, glosses):
    """One sense per word and Wiktionary label, gathered from every gloss row (sense_rows.HEADER
    shaped) that lists it."""
    col = {name: i for i, name in enumerate(sense_rows.HEADER)}
    sense_col = next(i for i, name in enumerate(sense_rows.HEADER) if name.startswith("Wiktionary Sense"))
    senses = {}
    per_gloss = collections.Counter()
    for row in rows:
        if len(row) <= sense_col:
            continue
        word, label = text(row[col["Glb"]]), text(row[sense_col])
        if not word or not label:
            continue
        key = row_id(word.lower(), label)
        eng, pos = text(row[col["Eng"]]), text(row[col["Prt of Sp"]])
        per_gloss[(word.lower(), eng, pos)] += 1
        sense = senses.get(key)
        if sense is None:
            sense = senses[key] = {
                "id": key, "word": word, "label": label, "eng": eng, "pos": pos,
                "definition": text(row[col["Definition"]]),
                "example": text(row[col["Example"]]),
                "clarification": text(row[col["Clarification"]]),
                "keys": [], "tier": "", "app": "", "glosses": 0, "engs": set(),
                "first_listed": per_gloss[(word.lower(), eng, pos)] == 1,
                "translations": compare_translations(row, col, glosses.get(word.lower(), {})),
            }
        gloss_key = [eng, pos, text(row[col["VerbType"]])]
        if gloss_key not in sense["keys"]:
            sense["keys"].append(gloss_key)
        sense["glosses"] += 1
        sense["engs"].add(eng.lower())
        tier, app = text(row[col["Tier"]]), text(row[col["App?"]])
        # A human verdict outranks a script's when a label repeats.
        if tier in HUMAN_TIERS or not sense["tier"]:
            sense["tier"], sense["app"] = tier, app
    return senses


def score_row(sense):
    """Higher means a more obvious match. Weights reflect the cues measured on vetted rows."""
    label = sense["label"].lower()
    full = f"{label} {sense['definition'].lower()}"
    hits = {c["lang"] for c in sense["translations"] if c["hit"]}
    score, why = 0, []
    if "Eo" in hits:
        score += 3
        why.append(("good", "Eo matches"))
    if "Es" in hits:
        score += 3
        why.append(("good", "Es matches"))
    others = len(hits - {"Eo", "Es"})
    if others:
        score += min(others, 3)
        why.append(("good", f"{others} other language{'s' if others > 1 else ''}"))
    if sense["first_listed"]:
        score += 1
        why.append(("good", "listed first"))
    if sense["glosses"] > 1:
        score += 1
        why.append(("good", "under 2+ glosses"))
    if sense["app"] == "s":
        score += 1
        why.append(("good", "script said yes"))
    elif sense["tier"] == "a" and sense["app"] == "n":
        score -= 2
        why.append(("bad", "script said no"))
    if FIELD_LABEL.match(label) or REGISTER.search(full):
        score -= 2
        why.append(("bad", "field or register label"))
    clarifier = content_tokens(sense["clarification"])
    if clarifier and not clarifier & content_tokens(full):
        score -= 2
        why.append(("bad", "gloss clarifier not mentioned"))
    if not sense["translations"]:
        score -= 1
        why.append(("bad", "nothing to compare"))
    return score, why


def word_tags(glosses, word):
    return [t.strip() for t in text(glosses.get(word, {}).get("Tags")).split(",") if t.strip()]


def sense_text(sense):
    return unicodedata.normalize("NFKC", f"{sense['label']} {sense['definition']}").lower()


def mentions(term, lowered):
    return re.search(rf"\b{re.escape(term)}(?:s|es)?\b", lowered) is not None


def plain_english_words(all_senses):
    """Words seen after a lowercase word are English: "Usage notes" is no species, "Felis catus" is."""
    plain = set()
    for sense in all_senses:
        words = sense["definition"].split()
        for before, word in zip(words, words[1:]):
            if before.islower() and word.islower():
                plain.add(word.strip(".,;:()[]\"'"))
    return plain


def find_taxa(sense, plain):
    found = {f"{genus} {species}" for genus, species in BINOMIAL.findall(sense["definition"])
             if species not in plain and not NOT_A_GENUS.search(genus)}
    for named, by_ending in HIGHER_TAXON.findall(sense["definition"]):
        found.add(named or by_ending)
    return found


def tag_profiles(words_with_senses, glosses):
    """Each tag's own English gloss, plus the definition words typical of its words. No verdicts used."""
    members = collections.defaultdict(set)
    tokens = {}
    for word, group in words_with_senses.items():
        tokens[word] = set().union(*(content_tokens(sense_text(s)) for s in group))
        for tag in word_tags(glosses, word):
            members[tag].add(word)
    spread = collections.Counter(token for found in tokens.values() for token in found)
    gloss_terms, typical = {}, {}
    for tag, words in members.items():
        if tag.lower() in glosses:
            gloss_terms[tag] = [t for t in terms(text(glosses[tag.lower()].get("TranslationEng"))) if len(t) > 2]
        if tag.lower() in glosses and len(words) >= MIN_TAG_WORDS:
            counted = collections.Counter(token for word in words for token in tokens[word])
            typical[tag] = {token for token, n in counted.items()
                            if n >= 3 and n / len(words) >= 0.2
                            and (n / len(words)) / (spread[token] / len(tokens)) >= 5}
    return members, gloss_terms, typical


def tag_fit(sense, tag, gloss_terms, typical):
    """2 for the tag's own gloss, two typical words or a species name on a biological tag; 1 for one typical word."""
    if tag in BIOLOGICAL_TAGS and sense["taxa"]:
        return 2
    lowered = sense_text(sense)
    if any(t not in sense["engs"] and mentions(t, lowered) for t in gloss_terms.get(tag, ())):
        return 2
    return min(len(typical.get(tag, set()) & content_tokens(lowered)), 2)


def score_against_siblings(word, group, plain, gloss_terms, typical, glosses):
    """Add the cues that need a word's other senses: glosses, taxa and tags."""
    entry = glosses.get(word, {})
    all_glosses = list(dict.fromkeys(terms(text(entry.get("TranslationEng")))))
    notes = [n for n in GLOSS_NOTE.findall(text(entry.get("TranslationEng"))) if len(n) > 2]
    tags = word_tags(glosses, word)
    for sense in group:
        lowered = sense_text(sense)
        sense["also_says"] = [t for t in all_glosses
                              if len(t) > 2 and not any(t in own or own in t for own in sense["engs"]) and mentions(t, lowered)]
        sense["taxa"] = find_taxa(sense, plain)
        sense["note_found"] = [n for n in notes if n.split()[0] in f"{sense['label']} {sense['definition']}"]
        sense["fits"] = {tag: fit for tag in tags if (fit := tag_fit(sense, tag, gloss_terms, typical))}
    said_by = collections.Counter(t for s in group for t in s["also_says"])
    any_note = any(s["note_found"] for s in group)
    any_taxon = any(s["taxa"] for s in group)
    any_fit = any(s["fits"] for s in group)
    for sense in group:
        # A synonym that few senses share is what marks out this sense among the word's others.
        distinct = [t for t in sense["also_says"] if said_by[t] <= max(1, len(group) // 3)]
        if distinct:
            sense["score"] += 2
            sense["why"].append(("good", f'also says "{distinct[0]}"'))
        elif sense["also_says"]:
            sense["score"] += 1
            sense["why"].append(("good", f'also says "{sense["also_says"][0]}"'))
        if sense["note_found"]:
            sense["score"] += 3
            sense["why"].append(("good", f"gloss names {sense['note_found'][0]}"))
        elif any_note:
            sense["score"] -= 2
            sense["why"].append(("bad", "another sense has the gloss's name"))
        elif sense["taxa"]:
            sense["score"] += 1
            sense["why"].append(("good", f"names {min(sense['taxa'])}"))
        elif any_taxon:
            sense["score"] -= 1
            sense["why"].append(("bad", "another sense names a species"))
        if sense["fits"]:
            tag = max(sense["fits"], key=sense["fits"].get)
            sense["score"] += sense["fits"][tag]
            sense["why"].append(("good", f"fits tag {tag}"))
        elif any_fit:
            sense["score"] -= 2
            sense["why"].append(("bad", "another sense fits the tag"))


def gloss_pos(sense, glosses):
    """The part of speech of the word-list gloss a sense was looked up for. The sense generator also
    looks a noun gloss up under Wiktionary's proper names (and the reverse), and an adjective-only
    word's gloss under adverbs, so those senses belong to the noun or the adjective."""
    pos = sense["pos"]
    if pos == "name":
        return "noun"
    if pos == "adv" and not ADV_LABEL.search(text(glosses.get(sense["word"].lower(), {}).get("TranslationEng"))):
        return "adj"
    return pos


def rank(senses, glosses):
    """Score every sense in place ("score", "why", "taxa", "fits", "gloss_pos", ...).
    Returns (senses_by_word, (tag_members, tag_gloss_terms, tag_typical))."""
    for sense in senses.values():
        sense["score"], sense["why"] = score_row(sense)
    by_word = collections.defaultdict(list)
    for sense in senses.values():
        by_word[sense["word"].lower()].append(sense)
    tags = tag_profiles(by_word, glosses)
    plain = plain_english_words(senses.values())
    for word, group in by_word.items():
        score_against_siblings(word, group, plain, tags[1], tags[2], glosses)
    for sense in senses.values():
        sense["gloss_pos"] = gloss_pos(sense, glosses)
    return by_word, tags


def order_key(sense, ranks):
    """Most promising first; among equals, words met earlier in the course, then alphabetical."""
    return (-sense["score"], ranks.get(sense["word"].lower(), 10**6), sense["word"], sense["label"])
