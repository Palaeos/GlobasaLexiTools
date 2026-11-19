# Victorian English -> Globasa dictionary: browsable page and exports built
# from the word list (victorian_wordlist.tsv, the source of truth). The
# per-work glossary (obscure_resolved.tsv) only contributes attestations and
# evidence; it decides nothing about entries, senses, renderings or layers.
#
#   python3 time-machine/build_termbase.py
#
# Entry = headword; sense = one word-list row (headword + Globasa rendering).
# Glossary rows attach to a sense when their lemma is the headword or one of
# its attested forms (smote -> smite) and their glb is the sense's glb.
#
# Output: victorian_glb.tsv (one row per sense), victorian_glb.json, and
# victorian_glb.html (termbase_template.html with the data injected).
# Translator words (Amos epo, d'Albroi spa) carry their gloss check: in the
# TSV a trailing "?" marks a word link the check did not confirm.
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import webster1913

HERE = Path(__file__).parent


def read_tsv(path):
    lines = path.read_text(encoding="utf-8").rstrip("\n").split("\n")
    hdr = lines[0].split("\t")
    return [dict(zip(hdr, ln.split("\t"))) for ln in lines[1:] if ln.strip()]


def checks(s):
    return dict(x.split(":", 1) for x in s.split()) if s else {}


wordlist = read_tsv(HERE / "victorian_wordlist.tsv")
glossary = [r for r in read_tsv(HERE / "obscure_resolved.tsv") if r["verdict"] in ("obscure", "dated_sense", "technical")]
gl_index = {}
for r in glossary:
    gl_index.setdefault((r["lemma"].strip().lower(), r["glb"].strip()), []).append(r)

APERTIUM = {"pref": "preference (AP_SETVAR=victorian)", "add": "eng→glb entry", "no": "", "pending": ""}
entries = {}
for w in wordlist:
    head = w["headword"]
    e = entries.setdefault(head.lower(), {"headword": head, "senses": []})
    forms = [head.lower()] + [a.strip().lower() for a in w.get("attested", "").split(";") if a.strip()]
    gl = [r for f in forms for r in gl_index.get((f, w["glb"].strip()), [])]
    amos, dal, holt, notes, tr = {}, {}, set(), [], {"epo": "", "spa": ""}
    dict_epo = dict_spa = dict_check = ""
    for r in gl:
        tc = checks(r.get("tr_check", ""))
        for d, col in ((amos, "epo"), (dal, "spa")):
            if r.get(col):
                d[r[col]] = d.get(r[col], False) or tc.get(col, "").startswith("agree")
        for lang, v in tc.items():
            if v.startswith("agree") or not tr.get(lang):
                tr[lang] = v
        if r.get("holt"):
            holt.add(r["holt"])
        if r.get("note"):
            notes.append(r["note"])
        dict_epo = dict_epo or r.get("dict_epo", "")
        dict_spa = dict_spa or r.get("dict_spa", "")
        dict_check = dict_check or r.get("dict_check", "")
    if w.get("notes"):
        notes.append(w["notes"])
    dc = checks(dict_check)
    e["senses"].append({
        "glb": w["glb"], "how": w["glb_how"], "sense": w["sense"], "layer": w["layer"],
        "apertium": APERTIUM.get(w["apertium"], ""), "apertium_reason": w["reason"] if w["apertium"] in ("pref", "add") else "",
        "attest": [{"ref": r["ref"].replace("H:Chapter ", "Ch. ").replace("U:", "Holt: "), "quote": r["quote"]} for r in gl],
        "amos": [{"w": k, "ok": v} for k, v in sorted(amos.items(), key=lambda x: (not x[1], x[0]))],
        "dalbroi": [{"w": k, "ok": v} for k, v in sorted(dal.items(), key=lambda x: (not x[1], x[0]))],
        "holt": sorted(holt), "tr_epo": tr.get("epo", ""), "tr_spa": tr.get("spa", ""),
        "dict_epo": dict_epo, "dict_spa": dict_spa, "dict_chk_epo": dc.get("epo", ""), "dict_chk_spa": dc.get("spa", ""),
        "notes": sorted(set(notes))})

out, tsv = [], []
for key in sorted(entries, key=lambda k: re.sub(r"[^a-z]", "", k)):
    e = entries[key]
    ws = webster1913.senses(e["headword"])
    out.append({"headword": e["headword"], "webster": ws, "senses": e["senses"]})
    for n, s in enumerate(e["senses"], 1):
        tsv.append([e["headword"], str(n), s["layer"], s["sense"], s["glb"], s["how"],
                    " | ".join(f"{a['ref']}: {a['quote']}" for a in s["attest"]),
                    "; ".join(x["w"] + ("" if x["ok"] else "?") for x in s["amos"]),
                    "; ".join(x["w"] + ("" if x["ok"] else "?") for x in s["dalbroi"]),
                    "; ".join(s["holt"]), s["dict_epo"], s["dict_spa"],
                    "; ".join(f"{w['n']}. {('[' + w['label'] + '] ') if w['label'] else ''}{w['gloss']}" for w in ws),
                    s["apertium"]])

with open(HERE / "victorian_glb.tsv", "w", encoding="utf-8") as f:
    f.write("\t".join(["headword", "sense_no", "layer", "sense", "glb", "glb_how", "attestations", "amos_epo",
                       "dalbroi_spa", "holt", "rhodes_oconnor", "velazquez", "webster_1913", "apertium"]) + "\n")
    for t in tsv:
        f.write("\t".join(x.replace("\t", " ") for x in t) + "\n")
(HERE / "victorian_glb.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")

from collections import Counter

print(len(out), "headwords,", len(tsv), "senses;", dict(Counter(t[2] for t in tsv)),
      "; unattested senses:", sum(1 for e in out for s in e["senses"] if not s["attest"]))

tpl = HERE / "termbase_template.html"
if tpl.exists():
    page = tpl.read_text(encoding="utf-8").replace("/*DATA*/[]", json.dumps(out, ensure_ascii=False).replace("</", "<\\/"))
    (HERE / "victorian_glb.html").write_text(page, encoding="utf-8")
    print("victorian_glb.html", len(page) // 1000, "KB")
