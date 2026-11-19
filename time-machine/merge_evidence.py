# Fold translation evidence (cache/evidence_<lang>.tsv from
# align_translations.py) into obscure_resolved.tsv as columns:
#   epo, spa  — the translator's word(s) at that spot (E. W. Amos ~1938;
#               J. d'Albroi 1925/26); single words only, the translation
#               texts themselves stay in cache/
#   tr_check  — per language: agree | differ | none(<why>), e.g.
#               "epo:agree spa:differ"
# Rows are matched on lemma|ref|quote. Re-running replaces the columns.
#   python3 merge_evidence.py [epo] [spa]
import csv
import sys
from pathlib import Path

HERE = Path(__file__).parent
LANGS = sys.argv[1:] or ["epo", "spa"]
path = HERE / "obscure_resolved.tsv"
lines = path.read_text(encoding="utf-8").rstrip("\n").split("\n")
hdr = lines[0].split("\t")
base = [h for h in hdr if h not in ("epo", "spa", "tr_check")]
rows = [dict(zip(hdr, ln.split("\t"))) for ln in lines[1:]]

ev = {}
for lang in ["epo", "spa"]:
    p = HERE / "cache" / f"evidence_{lang}.tsv"
    if lang not in LANGS or not p.exists():
        continue
    with open(p, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            e = r["evidence"]
            short = e if not e.startswith("none") else "none(" + e[6:-1].split(":")[0] + ")"
            ev.setdefault(r["key"], {})[lang] = (r.get(f"{lang}_words") or "", short.replace(" ", "_"))

for r in rows:
    key = f"{r['lemma']}|{r['ref']}|{r['quote']}"
    e = ev.get(key, {})
    checks = []
    for lang in ["epo", "spa"]:
        words, verdict = e.get(lang, (r.get(lang, ""), None))
        r[lang] = words
        if verdict:
            checks.append(f"{lang}:{verdict}")
        elif r.get("tr_check"):
            checks += [c for c in r["tr_check"].split() if c.startswith(lang + ":")]
    r["tr_check"] = " ".join(checks)

cols = base + ["epo", "spa", "tr_check"]
with open(path, "w", encoding="utf-8") as f:
    f.write("\t".join(cols) + "\n")
    for r in rows:
        f.write("\t".join((r.get(c) or "").replace("\t", " ") for c in cols) + "\n")
from collections import Counter

for lang in ["epo", "spa"]:
    c = Counter(next((x.split(":", 1)[1] for x in r["tr_check"].split() if x.startswith(lang + ":")), "-")
                for r in rows if r["verdict"] != "transparent")
    print(lang, dict(c))
