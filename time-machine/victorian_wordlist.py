# The Victorian word list: victorian_wordlist.tsv is the SOURCE OF TRUTH for
# the Victorian English -> Globasa dictionary. Edit it by hand. Everything
# else is generated from it:
#   build_termbase.py        -> victorian_glb.tsv / .json / .html
#   termbase_to_apertium.py  -> apertium-glb-eng (bidix block, biprefs CG,
#                               preferences declaration)
# Apertium files are outputs only; nothing is read back from them.
#
#   python3 time-machine/victorian_wordlist.py sync    # add new glossary senses
#   python3 time-machine/victorian_wordlist.py check   # validate the list
#
# Columns (one row per sense = headword + Globasa rendering):
#   headword     English lemma as the analyser gives it (smite, not smote)
#   eng_tags     Apertium tags of the headword, dot-separated (adv, n, vblex);
#                "mwe" for a multiword headword
#   sense        the Victorian sense, in plain modern English
#   glb          Globasa rendering (one word, or a phrase)
#   glb_tags     Apertium tags of the Globasa word (adv, n.nt, n.GD, vblex);
#                empty for a phrase
#   glb_how      word-list | derived (proposed) | paraphrase | fallback: why
#   layer        period | rare | technical
#   apertium     pref    gated preference: modern translation stays default,
#                        AP_SETVAR=victorian selects this one
#                add     plain eng->glb entry (the word has no translation, and
#                        the sense is safe in modern text too)
#                no      never exported
#                pending not decided yet (never exported)
#   reason       why that apertium decision
#   attested     surface forms seen in texts (smote; beheld)
#   notes        free text
#
# sync: new (headword, glb) pairs from the per-work glossary
# obscure_resolved.tsv are appended with apertium=pending; existing rows are
# never changed. Tags and lemmas are seeded from the monolingual analysers
# (English: apertium-eng via the pair's untrimmed analyser; Globasa:
# apertium-glb) and the layer from the glossary verdict + Webster 1913.
# check: allowed values, required fields for pref/add rows, duplicates, and
# (warnings only) whether the analysers still know headword+tags / glb+tags.
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import webster1913

from wordlist_tags import (APERTIUM, COLS, ENG_AN, GLB_AN, GLOSSARY, HERE, LAYERS, ROOT, WL,  # noqa: E402,F401
                           analyse, eng_lemma_tags, glb_tags_for, inherent, read_tsv, write_wordlist)


def sync():
    rows = read_tsv(WL)[1] if WL.exists() else []
    have = {(r["headword"].lower(), r["glb"].strip()) for r in rows}
    _, gl = read_tsv(GLOSSARY)
    gl = [r for r in gl if r["verdict"] in ("obscure", "dated_sense", "technical") and r["glb"].strip()]
    surfaces = sorted({r["lemma"] for r in gl if " " not in r["lemma"]})
    eng = analyse(ENG_AN, surfaces)
    glbs = sorted({r["glb"].strip() for r in gl if " " not in r["glb"].strip()})
    glb = analyse(GLB_AN, glbs)
    new = {}
    for r in gl:
        surface, g = r["lemma"].strip(), r["glb"].strip()
        lemma, eng_tags = eng_lemma_tags(surface, eng)  # smote -> smite
        key = (lemma, g)
        if key in have:
            continue
        e = new.get(key)
        if not e:
            glb_tags = glb_tags_for(g, eng_tags, glb)
            verdicts = set()
            e = new[key] = {"headword": lemma, "eng_tags": eng_tags, "sense": r["sense"], "glb": g,
                            "glb_tags": glb_tags, "glb_how": r["glb_how"], "apertium": "pending",
                            "reason": "", "attested": set(), "notes": "", "_v": verdicts}
        e["_v"].add(r["verdict"])
        if surface.lower() != lemma:
            e["attested"].add(surface.lower())
    added = []
    for e in new.values():
        v = e.pop("_v")
        e["layer"] = ("period" if "dated_sense" in v or ("technical" not in v and webster1913.is_period(e["headword"]))
                      else "technical" if "technical" in v else "rare")
        e["attested"] = "; ".join(sorted(e["attested"]))
        added.append(e)
    rows += sorted(added, key=lambda r: (r["headword"], r["glb"]))
    write_wordlist(rows)
    print(f"{len(added)} new senses appended as pending; {len(rows)} rows in {WL.name}")


def check():
    _, rows = read_tsv(WL)
    errors, warnings = [], []
    seen = set()
    for n, r in enumerate(rows, 2):
        key = (r["headword"].lower(), r["glb"].strip(), r["eng_tags"])
        if key in seen:
            errors.append(f"line {n}: duplicate {key}")
        seen.add(key)
        for c in ("headword", "sense", "glb", "layer", "apertium"):
            if not r.get(c, "").strip():
                errors.append(f"line {n}: empty {c} ({r['headword']})")
        if r["apertium"] not in APERTIUM:
            errors.append(f"line {n}: apertium must be one of {sorted(APERTIUM)} ({r['headword']})")
        if r["layer"] not in LAYERS:
            errors.append(f"line {n}: layer must be one of {sorted(LAYERS)} ({r['headword']})")
        if r["apertium"] in ("pref", "add"):
            if " " in r["headword"] or r["eng_tags"] in ("", "mwe"):
                errors.append(f"line {n}: {r['apertium']} needs a one-word headword with eng_tags ({r['headword']})")
            if " " in r["glb"].strip() or not r["glb_tags"]:
                errors.append(f"line {n}: {r['apertium']} needs a one-word glb with glb_tags ({r['headword']} → {r['glb']})")
            if not r["reason"].strip():
                errors.append(f"line {n}: {r['apertium']} needs a reason ({r['headword']})")
    # consistency with the analysers (warnings: the list is the truth, the
    # analysers may simply lack a word)
    exp = [r for r in rows if r["apertium"] in ("pref", "add")]
    eng = analyse(ENG_AN, sorted({r["headword"] for r in exp}))
    glb = analyse(GLB_AN, sorted({r["glb"] for r in exp}))
    for r in exp:
        if not any(l.lower() == r["headword"].lower() and t[:1] == r["eng_tags"].split(".")[:1]
                   for l, t in eng.get(r["headword"], [])):
            warnings.append(f"English analyser has no {r['headword']}<{r['eng_tags']}> (entry will never match)")
        if not any(inherent(t)[:len(r['glb_tags'].split('.'))] == r["glb_tags"].split(".")
                   for l, t in glb.get(r["glb"], [])):
            warnings.append(f"Globasa analyser has no {r['glb']}<{r['glb_tags']}> (generation may fail)")
    from collections import Counter
    print(f"{len(rows)} rows; apertium:", dict(Counter(r['apertium'] for r in rows)),
          "layer:", dict(Counter(r['layer'] for r in rows)))
    for w in warnings:
        print("warning:", w)
    for e in errors:
        print("ERROR:", e)
    sys.exit(1 if errors else 0)


cmd = sys.argv[1] if len(sys.argv) > 1 else "sync"
if cmd == "sync":
    sync()
elif cmd == "check":
    check()
else:
    sys.exit("usage: victorian_wordlist.py [sync|check]")
