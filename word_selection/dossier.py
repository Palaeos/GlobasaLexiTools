"""Decision dossier: everything needed to vet a proposal and think it through.

Every item says where it came from; gaps are reported as gaps, never filled in.
"""

import os
import re
import xml.etree.ElementTree as ET
from functools import lru_cache

from . import collision, lexicon
from .concept_index import _content_words
from .languages import BY_CODE, CODES, families

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMX = os.path.join(ROOT, "Doxo_passages.tmx")

# Rough areal groupings for the Sprachbund criterion (approximate; a judgement aid only).
AREAS = {
    "Sinosphere": {"cmn", "ja", "ko", "vi"},
    "Persianate / Islamicate": {"fa", "tr", "ar", "hi", "sw", "id"},
    "Indosphere": {"hi", "te", "id"},
    "Europe": {"en", "es", "fr", "de", "ru"},
    "East Africa (Swahili coast)": {"sw"},
}
DERIV_SUFFIXES = ["ya", "li", "yen", "ne", "gi", "cu", "do", "su", "mo", "ple", "fil"]


def concept_terms(concept, result=None):
    """English (and Esperanto) words describing the concept, for gloss matching."""
    from .sources.wiktionary import english_view
    terms = set()
    # a de/fr sense counts through the English tables it bridges to (Topf -> pot),
    # never with its own-language label read as English
    for wiki, word, pos, sense in english_view(concept).get("wikt_senses", []):
        terms.add(word.lower())
        terms |= _content_words(sense)
    if concept.get("label"):
        terms |= _content_words(concept["label"])
    if result:
        for w in result["words"]:
            if w["lang"] == "en" and not w.get("excluded"):
                terms.add(w["word"].lower())
    return {t for t in terms if len(t) > 2}


def sense_check(member, terms):
    """Own-language senses of a source word: which one fits the concept, what else it means."""
    from .sources import wiktionary
    info = wiktionary.lookup(member["lang"], member["word"])
    scored = []
    for s in info["senses"]:
        overlap = len(_content_words(s["gloss"]) & terms)
        scored.append((overlap, s))
    scored.sort(key=lambda x: -x[0])
    match = scored[0][1] if scored and scored[0][0] > 0 else None
    others = [s for o, s in scored if s is not match]
    flag = None
    f = member.get("sense_fit") or {}
    if not info["senses"]:
        flag = "no own-language entry in Wiktionary (cannot confirm the sense)"
    elif f.get("fit") == "shifted":
        flag = (f"meaning shifted: \"{f['gloss']}\" has the concept's word only with a particle or as the means "
                f"(as nicode < Hindi 'squeeze out' was replaced by bopu)")
    elif f.get("fit") == "homonym":
        flag = (f"another sense of the English word: \"{f['gloss']}\" (as miza leaned on Greek μάζα, "
                f"physical mass, for the Mass)")
    elif f.get("fit") == "ambiguous":
        flag = f"check which sense: \"{f['gloss']}\" gives only the English word, which has other senses"
    elif match is None or f.get("fit") == "unattested":
        flag = "none of its own-language senses attests the concept -- check the sense"
    return {"lang": member["lang"], "word": member["word"], "match": match,
            "other_senses": others[:8], "n_senses": len(info["senses"]), "flag": flag,
            "etym": info["etym"][:6]}


def attestation(result, cluster):
    found = {c for c, s in result["status"].items() if s == "found"}
    in_cluster = set(cluster["langs"])
    rows = []
    for area, langs in AREAS.items():
        rows.append({"area": area, "have_word": sorted(langs & found), "share_form": sorted(langs & in_cluster),
                     "missing_data": sorted(l for l in langs if result["status"].get(l) == "no data"),
                     "no_word": sorted(l for l in langs if result["status"].get(l) == "no word")})
    return {"families_with_word": sorted(families(found)), "families_sharing_form": cluster["families"],
            "areas": rows,
            "note": "Sprachbund criterion: the MEANING should be attested Sprachbund-wide or wider. "
                    "'have_word' counts any word for the concept, cognate or not; 'no data' is a gap "
                    "in the sources, not evidence of absence."}


def neighbours(terms, concept):
    hits = lexicon.search_glosses(sorted(terms)[:30])
    pre, suf = lexicon.affixes()
    return {"words": [{"word": w["word"], "cat": w["cat"], "cls": w["cls"], "eng": w["eng"], "epo": w["epo"]}
                      for w in hits[:40]],
            "note": "Compare the Epo column: it carries Globasa's finest distinctions. "
                    "A shared English gloss is NOT synonymy."}


@lru_cache(maxsize=1)
def _medial_clusters():
    counts = {}
    for r in lexicon.roots():
        w = r["word"].lower()
        for m in re.finditer(r"(?=[aeiou]([^aeiou]{2,})[aeiou])", w):
            counts[m.group(1)] = counts.get(m.group(1), 0) + 1
    return counts


def derivatives(form):
    out = []
    for s in DERIV_SUFFIXES:
        f = form + s
        ph = collision.phonotactics(f)
        exact = f in collision._lex()[0]
        out.append({"form": f, "phonotactics": ph, "taken": exact,
                    "gloss": collision.gloss(f) if exact else ""})
    return out


def unattested_clusters(form):
    counts = _medial_clusters()
    out = []
    for m in re.finditer(r"(?=[aeiou]([^aeiou]{2,})[aeiou])", form):
        n = counts.get(m.group(1), 0)
        if n < 2:
            out.append({"cluster": m.group(1), "roots_with_it": n})
    return out


@lru_cache(maxsize=1)
def _tmx():
    tus = []
    try:
        root = ET.parse(TMX).getroot()
    except (OSError, ET.ParseError):
        return tus
    for tu in root.iter("tu"):
        seg = {}
        ctx = ""
        for p in tu.findall("prop"):
            if p.get("type") == "x-context":
                ctx = p.text or ""
        for tuv in tu.findall("tuv"):
            lang = tuv.get("{http://www.w3.org/XML/1998/namespace}lang")
            s = tuv.find("seg")
            if s is not None and s.text:
                seg[lang] = s.text.strip()
        if "glb" in seg:
            tus.append({"ctx": ctx, **seg})
    return tus


def usage(terms, limit=6):
    pats = [re.compile(r"\b" + re.escape(t) + r"\b", re.I) for t in sorted(terms) if len(t) > 3][:12]
    out = []
    for tu in _tmx():
        text = tu.get("en", "") + " " + tu.get("eo", "")
        hit = [p.pattern for p in pats if p.search(text)]
        if hit:
            out.append({"glb": tu["glb"], "en": tu.get("en", ""), "eo": tu.get("eo", ""), "ctx": tu["ctx"]})
            if len(out) >= limit:
                break
    return out


def pivots(concept, result, cluster):
    """Each Wiktionary sense of the concept (en:pot, de:Topf, fr:cruche): how many
    source words its table supplied, and how many of the chosen cluster's."""
    out = []
    for wiki, word, pos, sense in concept.get("wikt_senses", []):
        pid = f"{wiki}:{word}"
        out.append({"pivot": pid, "pos": pos, "sense": sense,
                    "words": sum(pid in w.get("pivot_support", []) for w in result["words"]),
                    "in_cluster": sum(pid in m.get("pivot_support", []) for m in cluster["members"])})
    return out


def flags(result, cluster):
    out = []
    for m in cluster["members"]:
        for f in m.get("flags", []):
            out.append(f"{m['lang']} {m['word']}: {f}")
    out += list(result.get("notes", []))
    nd = [c for c, s in result["status"].items() if s == "no data"]
    if nd:
        out.append("no data (not 'no word') for: " + ", ".join(nd))
    cl = result["clusters"]
    if len(cl) > 1 and cl[0]["rank_key"] == cl[1]["rank_key"]:
        out.append("the top two clusters are TIED under the methodology")
    elif len(cl) > 1 and len(cl[0]["families"]) - len(cl[1]["families"]) <= 1:
        out.append(f"narrow margin: winner {len(cl[0]['families'])} families vs runner-up {len(cl[1]['families'])}")
    return out


def _with_han(word, han):
    return f"{word} (historical Han {han})" if han else word


def build(concept, result, cluster_index=0, form=None):
    from .pipeline import display_han
    cluster = result["clusters"][cluster_index]
    han = {(m["lang"], m["word"]): display_han(m, cluster) for m in cluster["members"]}
    terms = concept_terms(concept, result)
    props = cluster.get("proposals", [])
    chosen = next((p for p in props if p["form"] == form), props[0] if props else None)
    d = {
        "concept": concept,
        "terms": sorted(terms),
        "cluster": {"index": cluster_index, "langs": cluster["langs"], "families": cluster["families"],
                    "why": cluster["why"], "etym_links": cluster["etym_links"],
                    "existing_roots": cluster.get("existing_roots", [])},
        "losers": [{"index": i, "words": [f"{m['lang']}:{m['word']}" for m in c["members"]][:10], "why": c["why"]}
                   for i, c in enumerate(result["clusters"]) if i != cluster_index][:8],
        "sense_checks": [dict(sense_check(m, terms), han=han[(m["lang"], m["word"])])
                         for m in cluster["members"]],
        "attestation": attestation(result, cluster),
        "neighbours": neighbours(terms, concept),
        "usage": usage(terms),
        "flags": flags(result, cluster),
        "pivots": pivots(concept, result, cluster),
        "team_questions": result.get("team_questions", []),
        "proposal": None,
        "concept_info": [],
    }
    if chosen:
        from .align import align
        for x in chosen["distances"]:
            x["pairs"] = align(chosen["form"], x["form"])[1]
            x["han"] = han.get((x["lang"], x["word"]), "")
        d["proposal"] = {"form": chosen["form"], "trace": chosen["trace"], "severity": chosen["severity"],
                         "distances": chosen["distances"], "collision": chosen["collision"],
                         "derivatives": derivatives(chosen["form"]),
                         "unattested_clusters": unattested_clusters(chosen["form"])}
    from .sources import wikidata
    for q in concept.get("qids", [])[:2]:
        try:
            d["concept_info"].append(wikidata.concept_info(q))
        except Exception as e:
            d["concept_info"].append({"qid": q, "error": f"Wikidata unreachable ({type(e).__name__})"})
    return d


def to_markdown(d):
    L = []
    c = d["concept"]
    title = c.get("label") or ", ".join(w for _, w, _, _ in c.get("wikt_senses", [])) or "concept"
    L.append(f"# Word selection dossier: {title}\n")
    if c.get("wikt_senses"):
        L.append("**Concept (Wiktionary senses):** " + "; ".join(
            f"{w} ({p}): {s}" for _, w, p, s in c["wikt_senses"]))
    if len(d.get("pivots", [])) >= 2:
        L.append("\n**Pivots** (each sense in its own Wiktionary edition; data evidence, not methodology):")
        for p in d["pivots"]:
            L.append(f"- {p['pivot']} ({p['pos']}) '{p['sense']}': {p['words']} source words, "
                     f"{p['in_cluster']} in the chosen cluster")
    if c.get("qids"):
        L.append("**Wikidata:** " + ", ".join(c["qids"]))
    if c.get("seeds"):
        L.append("**Seeds:** " + ", ".join(f"{l}:{w}" for l, w in c["seeds"]))
    for ci in d["concept_info"]:
        if ci.get("error"):
            L.append(f"- {ci['qid']}: {ci['error']}")
        else:
            L.append(f"- {ci['qid']}: {ci.get('descriptions', {}).get('en', '')}"
                     + (f" — Esperanto label: *{ci['eo_label']}*" if ci.get("eo_label") else ""))
    p = d["proposal"]
    if p:
        L.append(f"\n## Proposal: **{p['form']}**  [{p['severity']}]\n")
        L.append("Rules applied: " + "; ".join(p["trace"]))
        L.append("\n| Source | Word | Rendering | Edits | Distance |\n|---|---|---|---|---|")
        for x in p["distances"]:
            L.append(f"| {BY_CODE[x['lang']]['basa']} | {_with_han(x['word'], x.get('han'))} | {x['form']} "
                     f"| {x['edits']} | {x['d']} |")
        col = p["collision"]
        if col["exact"] or col["homophone"]:
            L.append("\n**Collisions:** " + "; ".join(f"{w} ({g})" for w, g in col["exact"] + col["homophone"]))
        mp = [m for m in col["minimal_pairs"] if m["tier"] != "ANY"]
        if mp:
            L.append("\n**Minimal pairs (methodology tiers):** " + "; ".join(
                f"[{m['tier']}] {m['word']} — {m['gloss'][:40]} ({m['why']})" for m in mp))
        rest = [m for m in col["minimal_pairs"] if m["tier"] == "ANY"]
        if rest:
            L.append(f"\nOther minimal pairs ({len(rest)}): " + ", ".join(m["word"] for m in rest[:15]))
        if col["misparse_existing"] or col["self_decomposes"]:
            L.append("\n**Affix look-alikes:** " + "; ".join(
                [f"{w} could read as {how}" for w, g, how in col["misparse_existing"]] + col["self_decomposes"]))
        bad = [x for x in p["derivatives"] if x["phonotactics"] or x["taken"]]
        L.append("\n**Derivatives:** " + (", ".join(
            f"{x['form']} ({'taken: ' + x['gloss'] if x['taken'] else '; '.join(x['phonotactics'])})" for x in bad)
            if bad else "all of " + ", ".join(x["form"] for x in p["derivatives"]) + " are legal and free"))
        if p["unattested_clusters"]:
            L.append("\n**Rare medial clusters:** " + ", ".join(
                f"'{u['cluster']}' ({u['roots_with_it']} roots)" for u in p["unattested_clusters"]))
    cl = d["cluster"]
    L.append(f"\n## Source cluster\n\n{cl['why']}")
    if cl["etym_links"]:
        L.append("\nEtymology links: " + "; ".join(cl["etym_links"][:10]))
    if cl["existing_roots"]:
        L.append(f"\n**Already the etymon of existing root(s):** {', '.join(cl['existing_roots'])}")
    L.append("\n## Why the other clusters lost\n")
    for x in d["losers"]:
        L.append(f"- {', '.join(x['words'])}: {x['why']}")
    L.append("\n## Sense check (each source in its own language)\n")
    for s in d["sense_checks"]:
        m = s["match"]
        line = f"- **{BY_CODE[s['lang']]['basa']} {_with_han(s['word'], s.get('han'))}**: " + (f"“{m['gloss']}”" if m else "—")
        if s["other_senses"]:
            line += "; also: " + "; ".join(f"“{o['gloss'][:60]}”" for o in s["other_senses"][:4])
        if s["flag"]:
            line += f"  ⚠ {s['flag']}"
        L.append(line)
    a = d["attestation"]
    L.append("\n## Attestation (Sprachbund criterion)\n")
    L.append(f"Families with a word for the concept: {', '.join(a['families_with_word'])}  \n"
             f"Families sharing this form: {', '.join(a['families_sharing_form'])}\n")
    for r in a["areas"]:
        L.append(f"- {r['area']}: word in {', '.join(r['have_word']) or '—'}; this form in "
                 f"{', '.join(r['share_form']) or '—'}"
                 + (f"; no data: {', '.join(r['missing_data'])}" if r["missing_data"] else ""))
    L.append(f"\n*{a['note']}*")
    L.append("\n## Globasa neighbours\n")
    for w in d["neighbours"]["words"][:20]:
        L.append(f"- **{w['word']}** ({w['cat']}, {w['cls']}): {w['eng']} | Epo: {w['epo']}")
    L.append(f"\n*{d['neighbours']['note']}*")
    if d["usage"]:
        L.append("\n## Usage test (Doxo passages)\n")
        for u in d["usage"]:
            L.append(f"- {u['glb']}\n  — {u['en'] or u['eo']}  *({u['ctx']})*")
    if d.get("team_questions"):
        L.append("\n## Questions for the development team\n")
        for q in d["team_questions"]:
            L.append(f"- {q['question']}\n  - If yes: **{q['if_yes']['form']}** ({q['if_yes']['why']})"
                     f"\n  - If no: **{q['if_no']['form']}** ({q['if_no']['why']})\n  - Basis: {q['basis']}")
    if d["flags"]:
        L.append("\n## Uncertainty flags\n")
        L += [f"- {f}" for f in d["flags"]]
    return "\n".join(L) + "\n"
