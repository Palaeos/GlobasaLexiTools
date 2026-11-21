"""Recurrent kinship categories from Kinbank, found without a sense inventory.

Tier: script (evidence for vetting; it coins nothing). Idea of 2026-11-21: concepts
that recur among unrelated peoples get Globasa derivations; recurrence is counted in
independent language families and macro-areas, never in languages or speakers.

Method (male ego, the best-covered half of Kinbank):
  1. Grid: parents, parents' siblings, siblings and the eight cousin types, siblings
     and cousins split by age relative to ego. Kinbank sources code cousins at
     different depths (mFZeS / mFeZS / mFZS); all are folded onto this grid. Step 4
     folds relative age away (16 cells) so it does not swamp the cousin contrasts.
  2. Two cells are colexified in a language when they share a form.
  3. Global view: edge weight = mean over families of the family's colexification
     rate; single linkage on 1 - weight is the H0 filtration (when do cells merge
     into one category as the recurrence threshold drops).
  4. Systems: languages are clustered by their partitions (Ward linkage on mean
     pair disagreement, k by silhouette); each cluster's consensus partition (cells merged in
     at least half its languages) gives its categories, with family/area counts.
  5. Validation only: Murdock's cousin systems are labelled by rule and compared
     with the clusters (adjusted Rand index). The rules never feed the clustering.

Inputs:  /media/paleos/Warehouse2/Language/Claude/kinbank/{forms,languages}.csv
         (Kinbank CLDF, CC BY 4.0, commit in COMMIT; KINBANK_DIR overrides).
Outputs: concept_discovery/output/kinbank_h0_merges.tsv   (filtration merges)
         concept_discovery/output/kinbank_systems.tsv     (cluster categories)
         concept_discovery/output/kinbank_languages.tsv   (language -> cluster, rule label)
Run:     venv/bin/python concept_discovery/kinbank_categories.py   (< 1 min, ~0.5 GB)
"""

import os
import re
from collections import Counter, defaultdict
from itertools import combinations

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform
from sklearn.metrics import adjusted_rand_score, silhouette_score

KINBANK_DIR = os.environ.get("KINBANK_DIR", "/media/paleos/Warehouse2/Language/Claude/kinbank")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO, "concept_discovery", "output")

MIN_PAIR_COVERAGE = 0.8      # a language joins the system clustering if it codes this share of pairs
K_RANGE = range(3, 13)       # candidate numbers of systems
CONSENSUS = 0.5              # a cluster merges two cells if at least this share of its languages does
MIN_CLUSTER_LANGS = 5

COUSINS = [p + s + c for p in "FM" for s in "BZ" for c in "SD"]          # FBS, FBD, ... MZD
PARALLEL = {"FBS", "FBD", "MZS", "MZD"}
CELLS = (["F", "M", "FB", "FZ", "MB", "MZ", "eB", "yB", "eZ", "yZ"]
         + [c + "_" + a for c in COUSINS for a in "ey"])
CELL_INDEX = {c: i for i, c in enumerate(CELLS)}
COUSIN_RE = re.compile(r"^m([FM])([ey]?)([BZ])([ey]?)([SD])$")
UNCLE_RE = re.compile(r"^m([FM])([ey]?)([BZ])$")
SIBLING_RE = re.compile(r"^m([ey])([BZ])$")
PAREN_RE = re.compile(r"\(.*?\)")


def cells_of(parameter):
    """Grid cells a Kinbank parameter (male ego) speaks for."""
    if parameter in ("mF", "mM"):
        return [parameter[1]]
    if m := SIBLING_RE.match(parameter):
        return [m.group(1) + m.group(2)]
    if m := UNCLE_RE.match(parameter):
        return [m.group(1) + m.group(3)]
    if m := COUSIN_RE.match(parameter):
        base = m.group(1) + m.group(3) + m.group(5)
        return [base + "_" + a for a in (m.group(4) or "ey")]
    return []


def normalise_form(form):
    return re.sub(r"\s+", " ", PAREN_RE.sub("", str(form))).strip().lower()


def load():
    langs = pd.read_csv(os.path.join(KINBANK_DIR, "languages.csv"),
                        usecols=["ID", "Name", "Glottocode", "Family", "Macroarea"], dtype=str)
    # an isolate (no family) is its own family
    langs["Family"] = langs["Family"].fillna(langs["Glottocode"]).fillna(langs["ID"])
    langs["Macroarea"] = langs["Macroarea"].fillna("unknown")
    forms = defaultdict(lambda: [set() for _ in CELLS])
    for chunk in pd.read_csv(os.path.join(KINBANK_DIR, "forms.csv"),
                             usecols=["Language_ID", "Parameter_ID", "Form"], dtype=str,
                             chunksize=50000):
        for lang, parameter, form in chunk.itertuples(index=False):
            cells = cells_of(parameter)
            if not cells or not isinstance(form, str):
                continue
            form = normalise_form(form)
            if form:
                for c in cells:
                    forms[lang][CELL_INDEX[c]].add(form)
    return langs.set_index("ID"), forms


def base_cell(cell):
    """Cell without relative age: FBS_e -> FBS, eB -> B."""
    return cell.split("_")[0] if "_" in cell else cell.lstrip("ey")


BASE_CELLS = list(dict.fromkeys(base_cell(c) for c in CELLS))


def collapse_age(cells):
    out = [set() for _ in BASE_CELLS]
    for cell, cell_forms in zip(CELLS, cells):
        out[BASE_CELLS.index(base_cell(cell))] |= cell_forms
    return out


def colexification(forms, cells=CELLS):
    """language x pair matrix: 1 shared form, 0 both coded but distinct, nan not coded."""
    pairs = list(combinations(range(len(cells)), 2))
    ids = sorted(forms)
    matrix = np.full((len(ids), len(pairs)), np.nan, dtype=np.float32)
    for r, lang in enumerate(ids):
        lang_cells = forms[lang]
        for col, (a, b) in enumerate(pairs):
            if lang_cells[a] and lang_cells[b]:
                matrix[r, col] = 1.0 if lang_cells[a] & lang_cells[b] else 0.0
    return ids, pairs, matrix


def family_weights(matrix, families):
    """Per pair: mean over families of the family's colexification rate."""
    fam_codes, fam_index = np.unique(families, return_inverse=True)
    rates = np.full((len(fam_codes), matrix.shape[1]), np.nan, dtype=np.float32)
    for f in range(len(fam_codes)):
        rows = matrix[fam_index == f]
        coded = ~np.isnan(rows)
        n = coded.sum(0)
        with np.errstate(invalid="ignore"):
            rates[f] = np.where(n > 0, np.nansum(rows, 0) / np.maximum(n, 1), np.nan)
    return np.nanmean(rates, 0), (~np.isnan(rates)).sum(0)


def h0_merges(weights, pairs):
    """Single-linkage merge sequence on distance 1 - weight (H0 death times)."""
    n = len(CELLS)
    dist = np.ones((n, n), dtype=np.float64)
    for w, (a, b) in zip(weights, pairs):
        if not np.isnan(w):
            dist[a, b] = dist[b, a] = 1.0 - w
    np.fill_diagonal(dist, 0.0)
    tree = linkage(squareform(dist, checks=False), method="single")
    members = {i: [CELLS[i]] for i in range(n)}
    rows = []
    for step, (a, b, d, _) in enumerate(tree):
        left, right = members.pop(int(a)), members.pop(int(b))
        members[n + step] = left + right
        rows.append({"recurrence": round(1.0 - d, 3), "joins": " ".join(left),
                     "with": " ".join(right), "category": " ".join(sorted(left + right, key=CELL_INDEX.get))})
    return rows


def language_distances(matrix):
    """Mean disagreement over jointly coded pairs (chunked rows; N is ~1000)."""
    coded = (~np.isnan(matrix)).astype(np.float32)
    values = np.nan_to_num(matrix)
    both = coded @ coded.T
    agree_one = values @ values.T
    agree_zero = (coded - values) @ (coded - values).T
    with np.errstate(invalid="ignore", divide="ignore"):
        dist = 1.0 - (agree_one + agree_zero) / both
    dist[both == 0] = 1.0
    np.fill_diagonal(dist, 0.0)
    return dist


def consensus_categories(rows, pairs, cells):
    """Union-find over pairs merged in at least CONSENSUS of the languages."""
    parent = list(range(len(cells)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    with np.errstate(invalid="ignore"):
        rate = np.nanmean(rows, 0)
    for (a, b), r in zip(pairs, rate):
        if not np.isnan(r) and r >= CONSENSUS:
            parent[find(a)] = find(b)
    groups = defaultdict(list)
    for i in range(len(cells)):
        groups[find(i)].append(cells[i])
    return sorted((g for g in groups.values() if len(g) > 1), key=lambda g: cells.index(g[0]))


def murdock_label(cells):
    """Rule label for validation only (cousin terms vs siblings and parents' siblings)."""
    def merged(a, b):
        x, y = cells[CELL_INDEX[a]], cells[CELL_INDEX[b]]
        return bool(x and y and x & y) if x and y else None

    brothers = ("eB", "yB")
    par_sib = [merged(c + "_" + a, s) for c in ("FBS", "MZS") for a in "ey" for s in brothers]
    cross_sib = [merged(c + "_" + a, s) for c in ("FZS", "MBS") for a in "ey" for s in brothers]
    cross_cross = merged("FZS_e", "MBS_e")
    par_cross = merged("FBS_e", "FZS_e")
    crow = merged("FZS_e", "F") or merged("FZS_e", "FB")
    omaha = merged("MBS_e", "MB")
    if None in (cross_cross, par_cross) or all(v is None for v in par_sib + cross_sib):
        return "uncoded"
    p, c = any(v for v in par_sib if v), any(v for v in cross_sib if v)
    if p and c:
        return "Hawaiian"
    if p and crow:
        return "Crow"
    if p and omaha:
        return "Omaha"
    if p:
        return "Iroquois"
    if par_cross and cross_cross:
        return "Eskimo"
    if not par_cross and not cross_cross:
        return "Sudanese"
    return "other"


langs, forms = load()
ids, PAIRS, matrix = colexification(forms)
families = langs.loc[ids, "Family"].to_numpy()
areas = langs.loc[ids, "Macroarea"].to_numpy()
print(f"{len(ids)} languages with male-ego kin terms, {len(set(families))} families, "
      f"{len(CELLS)} cells, {len(PAIRS)} pairs", flush=True)

# 1. global H0 filtration
weights, n_families = family_weights(matrix, families)
merges = h0_merges(weights, PAIRS)
os.makedirs(OUT_DIR, exist_ok=True)
pd.DataFrame(merges).to_csv(os.path.join(OUT_DIR, "kinbank_h0_merges.tsv"), sep="\t", index=False)

# 2. systems: cluster languages on the grid with relative age folded in (probe of
# 2026-11-21: the e/y duplicates swamped the cousin contrasts, ARI 0.12 -> 0.43;
# Ward on these disagreement rates is a heuristic, they are not Euclidean)
_, base_pairs, base_matrix = colexification({i: collapse_age(forms[i]) for i in ids}, BASE_CELLS)
keep = (~np.isnan(base_matrix)).mean(1) >= MIN_PAIR_COVERAGE
sub = base_matrix[keep]
kept_ids = [i for i, k in zip(ids, keep) if k]
dist = language_distances(sub)
tree = linkage(squareform(dist, checks=False), method="ward")
best_k, best_s = None, -1.0
for k in K_RANGE:
    labels = fcluster(tree, k, criterion="maxclust")
    s = silhouette_score(dist, labels, metric="precomputed")
    if s > best_s:
        best_k, best_s = k, s
labels = fcluster(tree, best_k, criterion="maxclust")
print(f"system clustering: {len(kept_ids)} languages (>= {MIN_PAIR_COVERAGE:.0%} of pairs coded), "
      f"k = {best_k} (silhouette {best_s:.2f})", flush=True)

rule = [murdock_label(forms[i]) for i in kept_ids]
coded = [j for j, r in enumerate(rule) if r != "uncoded"]
ari = adjusted_rand_score([rule[j] for j in coded], [labels[j] for j in coded])
print(f"validation: adjusted Rand index vs Murdock rule labels = {ari:.2f} "
      f"({len(coded)} languages with a rule label)", flush=True)

kept_rows = {lang: r for r, lang in enumerate(ids)}
systems = []
for cluster in sorted(set(labels), key=lambda c: -(labels == c).sum()):
    members = [kept_ids[j] for j in np.flatnonzero(labels == cluster)]
    if len(members) < MIN_CLUSTER_LANGS:
        continue
    rows = base_matrix[[kept_rows[m] for m in members]]
    fams = Counter(langs.loc[members, "Family"])
    area_counts = Counter(a for a in langs.loc[members, "Macroarea"] if a != "unknown")
    murdock = Counter(rule[j] for j in np.flatnonzero(labels == cluster))
    for category in consensus_categories(rows, base_pairs, BASE_CELLS):
        systems.append({
            "system": int(cluster), "languages": len(members), "families": len(fams),
            "macroareas": len(area_counts),
            "areas": ", ".join(f"{a} {n}" for a, n in area_counts.most_common()),
            "murdock_rule_labels": ", ".join(f"{a} {n}" for a, n in murdock.most_common(4)),
            "category": " ".join(category),
            "top_families": ", ".join(f"{f} {n}" for f, n in fams.most_common(5)),
            "examples": ", ".join(langs.loc[members[:6], "Name"]),
        })
pd.DataFrame(systems).to_csv(os.path.join(OUT_DIR, "kinbank_systems.tsv"), sep="\t", index=False)
pd.DataFrame({"language": kept_ids, "name": langs.loc[kept_ids, "Name"].to_numpy(),
              "family": langs.loc[kept_ids, "Family"].to_numpy(),
              "macroarea": langs.loc[kept_ids, "Macroarea"].to_numpy(),
              "system": labels, "murdock_rule": rule}).to_csv(
    os.path.join(OUT_DIR, "kinbank_languages.tsv"), sep="\t", index=False)
print(f"-> concept_discovery/output/kinbank_{{h0_merges,systems,languages}}.tsv "
      f"({len(merges)} merges, {len(systems)} system categories)")
