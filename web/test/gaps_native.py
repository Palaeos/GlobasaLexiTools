"""Structure gaps in spa->glb / epo->glb (docs/translation/rule_gaps_handover.md): constructions
from the pair's own tagger stage (native apertium, neural steps off, 4 sentences at a time,
each under ulimit -v 2 GB) vs
chrF against the gold, and the error marks (@ no translation, # generation, * unknown).
    python3 web/test/capped.py python3 web/test/gaps_native.py spa|epo OUT.json"""
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

ROOT = "/home/paleos/PycharmProjects/GlobasaLexiTools"
ns = {}
exec("\n".join(open(f"{ROOT}/GlobasaTranslation/apertium-glb-eng/test/score.py").read().splitlines()[:30]), ns)
chrf = ns["chrf"]
lang, out_path = sys.argv[1], sys.argv[2]
d = f"{ROOT}/GlobasaTranslation/apertium-glb-{lang}"
files = {"spa": ["spa-glb-babel.tsv", "spa-glb-xwexi.tsv"], "epo": ["epo-glb-vanege-dev.tsv", "epo-glb-xwexi.tsv"]}[lang]
rows = []
for f in files:
    for l in open(f"{ROOT}/parallel_gold_cache/{lang}/{f}", encoding="utf-8"):
        if l.startswith("#") or "\t" not in l:
            continue
        s, g = l.rstrip("\n").split("\t")[:2]
        if s.strip() and g.strip():
            rows.append({"set": f.split("-")[2].split(".")[0], "src": s.strip(), "gold": g.strip()})
env = dict(os.environ, GLB_NEURAL="0", ENG_GLB_NEURAL="0", FRA_GLB_NEURAL="0")


def run(r):
    def ap(mode):
        p = subprocess.run(["bash", "-c", f"ulimit -v 2097152; apertium -d '{d}' {mode}"], input=r["src"] + "\n",
                           capture_output=True, text=True, timeout=120, env=env)
        return p.stdout.strip()
    r["out"] = ap(f"{lang}-glb")
    r["tagged"] = ap(f"{lang}-glb-tagger")
    return r


with ThreadPoolExecutor(4) as ex:
    rows = list(ex.map(run, rows))

LU = re.compile(r"\^([^$]*)\$")


def lus(r):
    return [(m.split("<", 1)[0].lower(), "<" + m.split("<", 1)[1] if "<" in m else "") for m in LU.findall(r["tagged"])]


def cons_spa(r):
    u = lus(r)
    f = set()
    lem = [l for l, _ in u]
    tg = [t for _, t in u]
    for i, (l, t) in enumerate(u):
        nt = tg[i + 1] if i + 1 < len(u) else ""
        if "<enc>" in t or ("<pro>" in t and "<prn>" in t):
            f.add("object clitic pronoun (lo/la/le/me/te...)")
        if "<ref>" in t or l == "se":
            f.add("se / reflexive")
        if l == "gustar" or l == "encantar" or l == "doler" or l == "parecer":
            f.add("gustar-type verb (inverse experiencer)")
        if l == "estar" and "<ger>" in nt:
            f.add("estar + gerund (progressive)")
        if l == "ir" and i + 2 < len(u) and lem[i + 1] == "a" and "<inf>" in tg[i + 2]:
            f.add("ir a + infinitive (future)")
        if "<sbj>" in t or "<prs><sub" in t or "<pis>" in t or "<pii>" in t and "subj" in t:
            f.add("subjunctive")
        if "<sbj" in t:
            f.add("subjunctive")
        if l == "haber" and "<vbhaver>" in t or (l == "haber" and "<pp>" in nt):
            f.add("perfect (haber + participle)")
        if l == "ser" and "<pp>" in nt:
            f.add("ser + participle (passive)")
        if l == "estar" and "<adj>" in nt:
            f.add("estar + adjective")
        if l in ("por", "para") and "<pr>" in t:
            f.add("por / para")
        if l in ("que", "quien", "cual", "donde") and "<rel>" in t:
            f.add("relative clause (que/quien/donde)")
        if "<itg>" in t:
            f.add("interrogative word")
        if l == "no" and "<adv>" in t:
            f.add("negation no")
        if l in ("más", "menos") and ("<adj>" in nt or "<adv>" in nt):
            f.add("comparative más/menos")
        if "<imp>" in t:
            f.add("imperative")
        if "<inf>" in t and i > 0 and "<pr>" in tg[i - 1]:
            f.add("preposition + infinitive")
        if l == "lo" and "<det>" in t and "<adj>" in nt:
            f.add("lo + adjective")
        if "<num>" in t:
            f.add("number")
        if "<pp>" in t and (i == 0 or "<vbhaver>" not in tg[i - 1] and lem[i - 1] not in ("haber", "ser", "estar")):
            f.add("participle (not perfect/passive)")
        if "<ger>" in t and (i == 0 or lem[i - 1] != "estar"):
            f.add("gerund clause")
        if l in ("de",) and "<pr>" in t and i > 0 and "<n>" in tg[i - 1]:
            f.add("N de N")
    if not any("<prn><tn>" in t or "<prn><subj>" in t or ("<prn>" in t and "<p" in t and "<enc>" not in t and "<pro>" not in t) for t in tg) \
            and not any("<n>" in t or "<np>" in t for t in tg[:3]):
        f.add("pro-drop (no subject noun/pronoun)")
    if r["src"].startswith("¿") or r["src"].endswith("?"):
        f.add("question")
    return f


EPO_CORREL = re.compile(r"^(ki|ti|ĉi|neni|i)(u|o|a|e|el|al|am|om|es)n?$")


def cons_epo(r):
    u = lus(r)
    f = set()
    lem = [l for l, _ in u]
    tg = [t for _, t in u]
    nouns = [i for i, t in enumerate(tg) if "<n>" in t]
    verbs = [i for i, t in enumerate(tg) if "<vblex>" in t or "<vbser>" in t]
    for i, (l, t) in enumerate(u):
        if "<acc>" in t and verbs and i < verbs[0]:
            f.add("accusative object before the verb (OV order)")
        if "<acc>" in t:
            f.add("accusative -n")
        if EPO_CORREL.match(l) or l in ("kiu", "tiu", "ĉiu", "neniu", "kio", "tio", "ĉio", "nenio", "kie", "tie", "kiam", "tiam", "kial", "kiel", "tiel", "kies", "ties", "kiom", "tiom"):
            f.add("correlative (kiu/tiu/ĉiu/neni...)")
        if l in ("kiu", "kio", "kie", "kiam", "kies") and i > 0 and ("<n>" in tg[i - 1] or lem[i - 1] in (",", "tio", "tiu")):
            f.add("relative clause (kiu/kio/kie...)")
        if re.search(r"<(pprs|pp|pfut|pprs_?p|pp_?p)>", t) or re.search(r"(ant|int|ont|at|it|ot)(a|e|o)j?n?$", l) and "<vblex>" in t:
            f.add("participle (-anta/-inta/-ata/-ita...)")
        if l == "ju" or l == "des":
            f.add("ju ... des comparative")
        if l == "ĉu":
            f.add("ĉu question / whether")
        if l in ("pli", "malpli", "plej"):
            f.add("pli/plej comparison")
        if "<inf>" in t:
            f.add("infinitive")
        if l == "ne" and "<adv>" in t:
            f.add("negation ne")
        if l == "si" or l == "sia":
            f.add("si / sia (reflexive)")
        if "<num>" in t:
            f.add("number")
        if l in ("estas", "esti") and i + 1 < len(u) and re.search(r"<(pp|pprs)>", tg[i + 1]):
            f.add("esti + participle (compound tense/passive)")
    if r["src"].endswith("?"):
        f.add("question")
    if "*" in r["out"]:
        f.add("has unknown word (*)")
    return f


cons = cons_spa if lang == "spa" else cons_epo
stats = defaultdict(list)
at_words, hash_words, star_words = Counter(), Counter(), Counter()
for r in rows:
    r["chrf"] = max(chrf(r["out"], g.strip()) for g in r["gold"].split(" | "))
    for t in r["out"].split():
        tt = re.sub(r"^[^\w@#*\\¿¡]+|[^\w]+$", "", t).replace("\\", "")
        if tt.startswith("@"):
            at_words[tt[1:].lower()] += 1
        elif "#" in tt:
            hash_words[tt.lower()] += 1
        elif tt.startswith("*"):
            star_words[tt[1:].lower()] += 1
    for c in cons(r):
        stats[c].append(r)
mean = sum(r["chrf"] for r in rows) / len(rows)
print(f"{lang}->glb: {len(rows)} sentences ({Counter(r['set'] for r in rows)}), mean chrF {100 * mean:.1f}")
print(f"{'construction':48} {'n':>4} {'chrF':>6} {'vs rest':>8}")
tab = []
for c, rs in stats.items():
    cm = sum(r["chrf"] for r in rs) / len(rs)
    rest = [r["chrf"] for r in rows if r not in rs]
    tab.append(((cm - sum(rest) / len(rest)) if rest else 0, c, len(rs), cm))
for dlt, c, n, cm in sorted(tab):
    if n >= 4:
        print(f"{c:48} {n:4d} {100 * cm:6.1f} {100 * dlt:+8.1f}")
for name, cnt in (("@ (no translation)", at_words), ("# (generation)", hash_words), ("* (unknown to the analyser)", star_words)):
    print(f"\n{sum(cnt.values())} {name}: " + ", ".join(f"{w} {k}" for w, k in cnt.most_common(30)))
print("\nsentences with: @ %d, # %d, * %d" % tuple(sum(1 for r in rows if ch in r["out"]) for ch in "@#*"))
json.dump({"rows": rows, "cons": {c: [r["src"] for r in rs] for c, rs in stats.items()}}, open(out_path, "w"), ensure_ascii=False)
