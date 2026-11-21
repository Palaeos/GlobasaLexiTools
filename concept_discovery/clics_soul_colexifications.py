"""Colexification of soul / ghost / breath concepts across language families (CLICS4).

Tier: script (evidence for a lexicon proposal; it decides nothing). Question of
2026-11-21: may Globasa xabahu 'ghost' be broadened to the Eurasian free soul, and does
ruho 'spirit, soul' belong with breath and life (ruach, 氣, prāṇa)? A colexification
recurring in many unrelated families means speakers treat the two concepts as one
meaning; the recurrence counts families, never languages or speakers (as
kinbank_categories.py).

For each concept pair: languages (Glottocodes) that record both concepts, those with a
shared form, families with both / with a shared form, and the family-weighted rate =
mean over families of the family's share of colexifying languages. Varieties of one
Glottocode are pooled (a shared form in any variety counts), which slightly favours
colexification; a family-weighted rate is the measure to compare.

Input:   CLICS4 CLDF (Tjuka, Forkel, Rzymski & List 2026, CC BY 4.0,
         doi:10.5281/zenodo.16900179) in /media/paleos/Warehouse2/Language/Claude/clics4
         (forms.csv.zip, languages.csv; commit in COMMIT; CLICS4_DIR overrides).
Output:  concept_discovery/output/clics_soul_colexifications.tsv  (all areas)
         concept_discovery/output/clics_soul_colexifications_by_area.tsv  (per macro-area)
Run:     venv/bin/python concept_discovery/clics_soul_colexifications.py   (~1 min)
"""

import csv
import io
import os
import re
import zipfile
from collections import Counter, defaultdict

CLICS4_DIR = os.environ.get("CLICS4_DIR", "/media/paleos/Warehouse2/Language/Claude/clics4")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "concept_discovery", "output", "clics_soul_colexifications.tsv")
OUT_AREAS = os.path.join(REPO, "concept_discovery", "output", "clics_soul_colexifications_by_area.tsv")
AREAS = ("Africa", "Eurasia", "Papunesia", "Australia", "North America", "South America")

# (concept, concept, why it is asked). CLICS4 Parameter_IDs.
PAIRS = [
    ("ghost", "soul", "xabahu as free soul: ghost of the dead = soul of the living?"),
    ("ghost", "spirit", "xabahu vs ruho"),
    ("soul", "spirit", "ruho 'spirit, soul': one word in most families?"),
    ("soul", "shadow", "shadow soul (skia, bayang)"),
    ("ghost", "shadow", "shade of the dead"),
    ("ghost", "corpse", "ghost as the dead body's double"),
    ("ghost", "demon", "ghost vs malevolent being"),
    ("ghost", "ancestors", "ghost as ancestor"),
    ("soul", "dream", "dream soul"),
    ("soul", "breath", "breath soul (ruach, prāṇa, 氣)"),
    ("spirit", "breath", "pneuma, spiritus"),
    ("soul", "breathe", "breath soul (verb)"),
    ("spirit", "wind", "ruach, pneuma"),
    ("breath", "wind", "moving air"),
    ("breath", "air", "氣 air"),
    ("spirit", "air", "pneuma, 氣"),
    ("soul", "life", "nefesh, napištum, psychē as life"),
    ("breath", "life", "breath = life"),
    ("soul", "heart", "seat of feeling"),
    ("soul", "mind", "noos, manas"),
    ("soul", "self", "nafs, ātman"),
    ("soul", "throat", "nefesh / napištum 'throat'"),
    ("soul", "body", "contrast check (should be rare)"),
    ("soul", "person", "nefesh 'person'"),
    ("spirit", "god", "divine spirit"),
    ("ghost", "god", "contrast check"),
    ("breath", "strength", "thymos/menos, 氣 vigour"),
    ("spirit", "strength", "vigour, morale"),
    ("breath", "anger", "生氣, thymos"),
]
CONCEPTS = {c for pair in PAIRS for c in pair[:2]}
PAREN_RE = re.compile(r"\(.*?\)")
EXAMPLES = 6


def normalise(form):
    return re.sub(r"\s+", " ", PAREN_RE.sub("", form)).strip().lower()


def load_languages():
    """Language_ID -> (glottocode, family, macroarea, name); an isolate is its own family."""
    out = {}
    with open(os.path.join(CLICS4_DIR, "languages.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            glotto = row["Glottocode"] or f"id:{row['ID']}"
            family = row["Family_Name"] or row["Family"] or glotto
            out[row["ID"]] = (glotto, family, row["Macroarea"] or "unknown", row["Glottolog_Name"] or row["Name"])
    return out


def load_forms(languages):
    """{glottocode: {concept: set(forms)}} for the concepts asked about (streamed)."""
    forms = defaultdict(lambda: defaultdict(set))
    with zipfile.ZipFile(os.path.join(CLICS4_DIR, "forms.csv.zip")) as z, z.open("forms.csv") as raw:
        for row in csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8")):
            concept = row["Parameter_ID"]
            if concept not in CONCEPTS or row["Language_ID"] not in languages:
                continue
            form = normalise(row["Form"])
            if form:
                forms[languages[row["Language_ID"]][0]][concept].add(form)
    return forms


def pair_stats(a, b, forms, info, area=None):
    """Counts for one pair; area restricts to languages of one macro-area."""
    both, colex = [], []
    for glotto, concepts in forms.items():
        if area and info[glotto][2] != area:
            continue
        if concepts.get(a) and concepts.get(b):
            both.append(glotto)
            shared = concepts[a] & concepts[b]
            if shared:
                colex.append((glotto, sorted(shared)[0]))
    colex_set = {g for g, _ in colex}
    by_family = defaultdict(lambda: [0, 0])
    for glotto in both:
        fam = info[glotto][1]
        by_family[fam][0] += 1
        by_family[fam][1] += glotto in colex_set
    weighted = (sum(c / n for n, c in by_family.values()) / len(by_family)) if by_family else 0.0
    colex_families = sorted(f for f, (_, c) in by_family.items() if c)
    areas = Counter(info[g][2] for g in colex_set)
    return {
        "a": a, "b": b, "languages_both": len(both), "languages_colex": len(colex_set),
        "families_both": len(by_family), "families_colex": len(colex_families),
        "family_weighted_rate": round(weighted, 3),
        "macroareas": len([x for x in areas if x != "unknown"]),
        "areas": ", ".join(f"{x} {n}" for x, n in areas.most_common()),
        "families": ", ".join(colex_families[:12]) + (" ..." if len(colex_families) > 12 else ""),
        "examples": "; ".join(f"{info[g][3]} '{form}'" for g, form in colex[:EXAMPLES]),
    }


languages = load_languages()
info = {glotto: (glotto, fam, area, name) for glotto, fam, area, name in languages.values()}
forms = load_forms(languages)
print(f"{len(forms)} languages (Glottocodes) record at least one of {len(CONCEPTS)} concepts", flush=True)

rows = []
for a, b, why in PAIRS:
    stats = pair_stats(a, b, forms, info)
    stats["question"] = why
    rows.append(stats)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
tmp = OUT + ".tmp"
with open(tmp, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
    writer.writeheader()
    writer.writerows(rows)
os.replace(tmp, OUT)

area_rows = [{**{k: v for k, v in pair_stats(a, b, forms, info, area).items()
                 if k not in ("areas", "macroareas")}, "area": area}
             for a, b, _ in PAIRS for area in AREAS]
with open(OUT_AREAS + ".tmp", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["area"] + [k for k in area_rows[0] if k != "area"], delimiter="\t")
    writer.writeheader()
    writer.writerows(area_rows)
os.replace(OUT_AREAS + ".tmp", OUT_AREAS)

print(f"{'pair':<18}{'lang both':>10}{'colex':>7}{'fam both':>9}{'colex':>7}{'fam-wt':>8}{'areas':>6}")
for r in rows:
    print(f"{r['a'] + '/' + r['b']:<18}{r['languages_both']:>10}{r['languages_colex']:>7}"
          f"{r['families_both']:>9}{r['families_colex']:>7}{r['family_weighted_rate']:>8.3f}{r['macroareas']:>6}")
print(f"-> {os.path.relpath(OUT, REPO)}")
