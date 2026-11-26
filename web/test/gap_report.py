"""Structure gaps in eng->glb (docs/translation/rule_gaps_handover.md): English constructions,
found from the tagger's Penn tags, ranked by chrF against the rest; the most frequent error marks
(@ no bidix translation, # generation failure) and English function words left in the output.
    python3 web/test/gap_report.py DUMP.jsonl      (DUMP from web/test/gap_dump.mjs)
Writes DUMP.jsonl.cons.json (construction -> sources) and DUMP.jsonl.scored.json."""
import json
import re
import sys
from collections import Counter, defaultdict

ns = {}
exec("\n".join(open("/home/paleos/PycharmProjects/GlobasaLexiTools/GlobasaTranslation/apertium-glb-eng/test/score.py")
               .read().splitlines()[:30]), ns)
chrf = ns["chrf"]
rows = [json.loads(l) for l in open(sys.argv[1])]

BE = {"be", "is", "are", "was", "were", "been", "being", "am", "'s", "'re", "'m"}
HAVE = {"have", "has", "had", "'ve", "'d"}
DO = {"do", "does", "did"}
SUBJ = {"i", "you", "he", "she", "we", "they", "it"}
QUANT = {"some", "any", "every", "each", "all", "no", "none", "both", "either", "neither", "many", "much", "few"}
SUBORD = {"because", "when", "if", "while", "although", "though", "since", "until", "before", "after", "unless", "whether", "as"}


def constructions(tags):
    w = [t[0].lower() for t in tags]
    x = [t[1] for t in tags]
    found = set()
    n = len(w)
    for i in range(n):
        nx = x[i + 1] if i + 1 < n else ""
        nx2 = x[i + 2] if i + 2 < n else ""
        if w[i] in BE:
            j = i + 1
            while j < n and x[j].startswith("RB"):
                j += 1
            if j < n and x[j] == "VBN":
                found.add("passive (be + VBN)")
            if j < n and x[j] == "VBG":
                found.add("progressive (be + VBG)")
            if j < n and x[j].startswith("JJ") and j + 1 < n and w[j + 1] in ("to", "that") and i > 0 and w[i - 1] == "it":
                found.add("extraposition (it is ADJ to/that)")
        if w[i] in HAVE and x[i].startswith("VB"):
            j = i + 1
            while j < n and x[j].startswith("RB"):
                j += 1
            if j < n and x[j] == "VBN":
                found.add("perfect (have + VBN)")
        if w[i] in DO and nx == "RB" and i + 1 < n and w[i + 1] in ("not", "n't"):
            found.add("do-support negation")
        if w[i] in ("not", "n't", "never"):
            found.add("negation (not/never)")
        if x[i] == "MD":
            found.add("modal (MD)")
        if x[i] == "TO" and nx == "VB":
            found.add("to-infinitive")
        if x[i] in ("JJR", "RBR") or (w[i] in ("more", "less") and nx.startswith("JJ")):
            found.add("comparative")
        if w[i] == "than":
            found.add("comparison with than")
        if x[i] in ("JJS", "RBS"):
            found.add("superlative")
        if x[i] == "EX":
            found.add("existential there")
        if x[i] == "POS":
            found.add("'s genitive")
        if x[i].startswith("NN") and w[i] != "nothing" and i + 1 < n and w[i + 1] == "of" and nx2 in ("DT", "PRP$", "NN", "NNS", "NNP", "JJ"):
            found.add("of-genitive (N of N)")
        if x[i] in ("WDT", "WP", "WP$") and i > 0 and x[i - 1].startswith(("NN", "PRP", ",")) and not tags[-1][0] == "?":
            found.add("relative clause (that/which/who)")
        if x[i].startswith("NN") or (x[i] == "NN" and tags[i][2] == "PRON"):
            if nx == "PRP" and i + 1 < n and w[i + 1] in SUBJ - {"it"} and nx2.startswith("VB") and nx2 != "VBG":
                found.add("zero relative (N + PRP + V)")
        if x[i] == "VBG" and (i == 0 or x[i - 1] in (",", "IN") and w[i - 1] not in ("of",)):
            found.add("gerund/participle clause (VBG after , / start / IN)")
        if x[i] == "VBN" and i > 0 and x[i - 1] == ",":
            found.add("participle clause (, VBN)")
        if x[i] == "RP":
            found.add("phrasal verb (RP)")
        if w[i].endswith("self") or w[i].endswith("selves"):
            found.add("reflexive (-self)")
        if w[i] in QUANT and x[i] in ("DT", "PDT"):
            found.add("quantifier determiner")
        if w[i] in SUBORD and x[i] == "IN" and i + 1 < n and x[i + 1] in ("PRP", "DT", "NNP", "NN", "NNS"):
            found.add("adverbial clause (because/when/if ...)")
        if x[i] == "CD":
            found.add("number (CD)")
        if x[i] == "HYPH":
            found.add("hyphenated compound")
        if w[i] in ("“", "\"", "”", "'", "‘", "’") and x[i] in ("``", "''", "\"", "NFP", "."):
            found.add("quotation")
    if tags and tags[0][1] == "VB":
        found.add("imperative (starts with VB)")
    if tags and tags[-1][0] == "?":
        found.add("question")
        if tags[0][1] in ("WP", "WRB", "WDT"):
            found.add("wh-question")
        elif tags[0][0].lower() in BE | HAVE | DO or tags[0][1] == "MD":
            found.add("yes/no question (inversion)")
    if sum(1 for t in x if t.startswith("VB") and t not in ("VBG", "VBN")) >= 2 and "CC" in x:
        found.add("coordinated clauses (CC + 2 finite)")
    return found


ENG_FUNC = {"the", "a", "an", "of", "to", "that", "it", "do", "does", "did", "there", "will", "would",
            "have", "has", "had", "been", "being", "is", "are", "was", "were", "which", "who", "whom", "what", "not"}
stats = defaultdict(list)
marks = Counter()
at_words, hash_words, leftover = Counter(), Counter(), Counter()
scores = []
for r in rows:
    s = max(chrf(r["out"], g.strip()) for g in r["gold"].split(" | "))
    r["chrf"] = s
    scores.append(s)
    toks = r["out"].split()
    m = sum(1 for t in toks if t[:1] in "@#*" or "@" in t or "#" in t)
    r["marks"] = m / max(1, len(toks))
    for t in toks:
        tt = re.sub(r"^[^\w@#*\\]+|[^\w]+$", "", t).replace("\\", "")
        if tt.startswith("@"):
            at_words[tt[1:].lower()] += 1
        elif tt.startswith("#") or "#" in tt:
            hash_words[tt.lower()] += 1
        elif tt.lower() in ENG_FUNC:
            leftover[tt.lower()] += 1
    for c in constructions(r["tags"]):
        stats[c].append(r)

mean = sum(scores) / len(scores)
print(f"{len(rows)} sentences, mean chrF {100 * mean:.1f}\n")
print(f"{'construction':48} {'n':>4} {'chrF':>6} {'vs rest':>8} {'marks/tok':>9}")
table = []
for c, rs in stats.items():
    cm = sum(r["chrf"] for r in rs) / len(rs)
    rest = [r["chrf"] for r in rows if r not in rs]
    rm = sum(rest) / len(rest) if rest else cm
    mk = sum(r["marks"] for r in rs) / len(rs)
    table.append((cm - rm, c, len(rs), cm, mk))
for d, c, n, cm, mk in sorted(table):
    if n >= 5:
        print(f"{c:48} {n:4d} {100 * cm:6.1f} {100 * d:+8.1f} {mk:9.3f}")
print("\nmost frequent @ (no translation):", ", ".join(f"{w} {k}" for w, k in at_words.most_common(30)))
print("\nmost frequent # (generation):", ", ".join(f"{w} {k}" for w, k in hash_words.most_common(20)))
print("\nEnglish function words left in the output:", ", ".join(f"{w} {k}" for w, k in leftover.most_common(20)))
json.dump({c: [r["src"] for r in rs] for c, rs in stats.items()}, open(sys.argv[1] + ".cons.json", "w"))
json.dump(rows, open(sys.argv[1] + ".scored.json", "w"))
