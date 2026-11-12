#!/usr/bin/env python3
"""Stand-in for the source side's lemma table (tools/build_lexicon.py), used
while that project is not reachable.

    python3 reconstruct_lemma_table.py GLB_TABLE.tsv OUT.tsv [--ubs DIR ...]

Takes strongs, lemma, freq, main_en (the SDBH sense chosen by passage),
bdb, klein and flags from an earlier *_glb.tsv, and looks up the same SDBH
sense (by LEXID) in the other language editions found in the --ubs dirs:
es, fr, pt, zh-hans + zh-hant (merged into main_zh).  The curated readings
of בָּרָא (VAN_WOLDE) and צֶלֶם / דְּמוּת (CURATED) are re-added by hand; other curated readings are
lost.
"""

import argparse
import csv
import glob
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_UBS = ["/media/paleos/Warehouse2/Language/Bible translation/hbo-grc/sources/ubs",
               os.path.join(HERE, "sources", "ubs")]
EDITIONS = {"en": ["en"], "es": ["es"], "fr": ["fr"], "pt": ["pt"],
            "zh": ["zh-hans", "zh-hant"]}

# בָּרָא in Gen 1:1-2:4a after E. van Wolde, "Towards a New Understanding of
# the Image of God in Genesis 1:26-27: An Analysis of the Constructions of the
# Verb ברא in the Hebrew Bible", JHS 26 (2026) 1-55, doi:10.5508/jhs29692.
# The sense depends on the construction (§4.4, pp. 34-36; §7, pp. 50-51):
#   Type 1, plural/collective object: symmetrical "to separate" a whole into
#     parts, which become spatially disjoint (Gen 1:1, p. 14; 1:21, pp. 15-16);
#     Resultative "male and female he separated them" (1:27c, p. 33);
#     Niphal infinitive "when they separated" (2:4a, p. 38);
#   Type 2, singular object: asymmetrical "to set apart" one party from a
#     larger whole (1:27ab "set the human being apart in his image", p. 51;
#     2:3 the rest "set apart from all making work", p. 23).
# She contrasts it with בדל, the separating done by the heavenly bodies (p. 14),
# so בדל's glosses must not stand in for it.  es/fr/zh are plain translations
# of her English glosses (she gives none).
VAN_WOLDE = {
    "main": {"en": "to separate; to set apart", "es": "separar; apartar",
             "fr": "séparer; mettre à part", "pt": "separar; pôr à parte",
             "zh": "分开; 分别出来"},
    "curated": [
        "preferred: to separate; separar; séparer [van Wolde 2026 Type 1, plural "
        "object, a whole into spatially disjoint parts: Gen 1:1, 1:21 (pp. 14-16, 34)]",
        "preferred: to set apart; apartar; mettre à part [van Wolde 2026 Type 2, "
        "singular object, set apart from the other living beings: Gen 1:27ab, 2:3 "
        "(pp. 23, 34, 51)]",
        "alternative: to divide; dividir; diviser [1:27c 'separated them into male "
        "and female'; not used: one sense-based rendering (project owner)]",
    ],
}

# צֶלֶם and דְּמוּת (Gen 1:26-27; also 5:1-3, 9:6).  צֶלֶם is a concrete,
# relational noun: a made image of someone (cult images Num 33:52, 2 Kgs
# 11:18; figures 1 Sam 6:5, 11; Ezek 23:14), metaphorically a phantom or
# dream-image that keeps the idea of shape (Ps 39:7; 73:20; Clines, TynBul 19
# [1968] 74-75); always "image of" someone (van Wolde 2026 p. 44).  Akkadian
# ṣalmu "statue, image", an image that makes the god present (van Wolde p. 45,
# citing Berlejung, Bahrani).  דְּמוּת is "likeness, resemblance" (van Wolde p.
# 44 n. 99); the Tell Fekheriye statue calls itself both ṣlm and dmwt (Garr,
# IEJ 50 [2000]: dmwt the king's relation to the god, ṣlm his presence before
# his subjects).  Render צֶלֶם with the general concrete word (imaje: image,
# picture; Epo bildo, imago) and keep דְּמוּת distinct (simya); interpretations
# of what the image consists of stay alternatives.
CURATED = {
    "צלם": {
        "main": {"en": "image", "es": "imagen", "fr": "image", "pt": "imagem",
                 "zh": "形像"},
        "curated": [
            "preferred: image; imagen; image [concrete relational noun: a made image "
            "of someone; Akkadian ṣalmu; Clines 1968 pp. 74-75; van Wolde 2026 pp. 44-45]",
            "alternative: statue; estatua; statue [background of ṣalmu; too narrow "
            "for Gen 1, for notes]",
            "alternative: representative; representante; représentant [functional/royal "
            "reading, Clines 1968 (beth essentiae 'as our image'); interpretation]",
            "alternative: figure; figura; figure [bodily-form reading, Skinner ICC]",
        ],
    },
    "דמות": {
        "main": {"en": "likeness; resemblance", "es": "semejanza", "fr": "ressemblance",
                 "pt": "semelhança", "zh": "样式"},
        "curated": [
            "preferred: likeness; semejanza; ressemblance [resemblance, appearance; "
            "kept distinct from צֶלֶם (van Wolde 2026 p. 44 n. 99; Tell Fekheriye)]",
            "alternative: model; modelo; modèle [pattern, 2 Kgs 16:10]",
        ],
    },
}


def strong(s):
    return "H" + str(int(re.sub(r"\D", "", s)))


def load(dirs):
    """{lang: {strong: [(lexid, [glosses], pos)]}}"""
    out = {}
    for lang, editions in EDITIONS.items():
        for ed in editions:
            path = next((p for d in dirs for p in
                         glob.glob(os.path.join(d, f"UBSHebrewDic-v*-{ed}.JSON"))), None)
            if not path:
                continue
            m = out.setdefault(lang, {})
            for e in json.load(open(path, encoding="utf-8")):
                for sc in e.get("StrongCodes") or []:
                    for bf in e["BaseForms"]:
                        pos = " ".join(bf.get("PartsOfSpeech") or [])
                        for lm in bf.get("LEXMeanings") or []:
                            gl = [g.strip() for s in lm["LEXSenses"]
                                  for x in (s.get("Glosses") or []) for g in re.split("[；;]", x)]
                            m.setdefault(strong(sc), []).append((lm["LEXID"], gl, pos))
    return out


def glosses(S, lang, st, lexid):
    seen = []
    for i, g, _ in S.get(lang, {}).get(st, []):
        if i == lexid:
            seen += [x for x in g if x and x not in seen]
    return "; ".join(seen)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("glb")
    ap.add_argument("out")
    ap.add_argument("--ubs", nargs="+", default=DEFAULT_UBS)
    a = ap.parse_args()
    S = load(a.ubs)
    langs = [l for l in EDITIONS if l != "en" and l in S]
    rows = list(csv.DictReader(open(a.glb, encoding="utf-8"), delimiter="\t"))
    miss = 0
    with open(a.out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["strongs", "lemma", "freq", "pos", "main_en"]
                   + [f"main_{l}" for l in langs] + ["curated", "bdb", "klein", "flags"])
        for r in rows:
            st, en = strong(r["strongs"]), r["main_en"]
            senses = S["en"].get(st, [])
            curated = ""
            if r["lemma"] == "ברא":
                create = next(i for i, g, _ in senses if "to create" in g)
                lexid, pos = None, senses[0][2]
                en, fixed = VAN_WOLDE["main"]["en"], VAN_WOLDE["main"]
                other = [glosses(S, l, st, create).split("; ")[0] for l in ("es", "fr")]
                curated = " | ".join(VAN_WOLDE["curated"] + [
                    f"alternative: to create; {other[0]}; {other[1]} "
                    "[SDBH, BDB, Klein; the traditional reading]",
                    "alternative: to construct; construir; construire [Becking & "
                    "Korpel, JHS 10 (2010) art. 3: a late, non-anthropomorphic "
                    "verb for building/making, chosen over בנה]"])
            else:
                lexid, pos = next(((i, p) for i, g, p in senses if "; ".join(g) == en),
                                  (None, senses[0][2] if senses else ""))
                miss += bool(en and not lexid)
                fixed = {}
                c = CURATED.get(r["lemma"])
                if c:
                    if c["main"]:
                        en, fixed = c["main"]["en"], c["main"]
                    curated = " | ".join(c["curated"])
            w.writerow([r["strongs"], r["lemma"], r["freq"], pos or r.get("pos", ""), en]
                       + [fixed.get(l) or (glosses(S, l, st, lexid) if lexid else "")
                          for l in langs]
                       + [curated, r["bdb"], r["klein"], r.get("source_flags", r.get("flags", ""))])
    print(f"{len(rows)} lemmas -> {a.out}  (editions: en, {', '.join(langs)}; "
          f"English sense not found: {miss})")


if __name__ == "__main__":
    main()
