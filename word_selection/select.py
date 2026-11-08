"""Rank etymon clusters by the methodology's source-selection algorithm.

1. Most language families represented (European en/es/fr/de/ru = one family).
2. Tie-breaks in order: >= 2 East Asian; Arabic + any; Hindi + any;
   European + any; Persian and Turkish.
3. No agreement (best cluster has one family): fallback order
   Mandarin (two-character words only) > Vietnamese > Telugu > Swahili > Arabic > Hindi.

A cluster may carry "support": the languages whose words its best proposal stays
close to (pipeline.agreement). Only they count. Sound decides, not etymology:
false friends are fine (baru: Hindi balu, English bear, German Bär), but a
resemblance no form can stay close to (Persian sorhdar ~ Arabic zarnab) is not
agreement.
"""

from .languages import BY_CODE, FALLBACK_ORDER, TIE_BREAKS, families


def describe(langs):
    fams = sorted(families(langs))
    return f"{len(fams)} famil{'y' if len(fams) == 1 else 'ies'}: {', '.join(fams)}"


def rank(clusters):
    """Annotate and sort clusters; returns them best first, each with
    {langs, families, tie_breaks, rank_key, why}."""
    for c in clusters:
        langs = {m["lang"] for m in c["members"] if m["lang"] in BY_CODE}
        if c.get("support") is not None:
            langs &= set(c["support"])
        c["langs"] = sorted(langs, key=list(BY_CODE).index)
        c["families"] = sorted(families(langs))
        c["tie_breaks"] = [name for name, test in TIE_BREAKS if test(langs)]
        tb_vector = tuple(test(langs) for _, test in TIE_BREAKS)
        fb = 0
        if len(c["families"]) == 1:
            lang = next(iter(langs))
            ok = lang != "cmn" or any(len(m["word"]) == 2 for m in c["members"] if m["lang"] == "cmn")
            fb = len(FALLBACK_ORDER) - FALLBACK_ORDER.index(lang) if lang in FALLBACK_ORDER and ok else 0
        c["rank_key"] = (len(c["families"]), tb_vector, fb, len(langs))
    clusters.sort(key=lambda c: c["rank_key"], reverse=True)
    for i, c in enumerate(clusters):
        why = describe(c["langs"])
        if c.get("loose"):
            why += (f"; loose resemblances not counted (no member of theirs within distance "
                    f"{c['support_tolerance']} of {c['support_form']}): {', '.join(c['loose'])}")
        if c.get("unverified"):
            u = c["unverified"]
            why += (f"; not counted (an unverified etymology guess, or its own entry gives another meaning): "
                    f"{', '.join(u[:3])}"
                    + (f" and {len(u) - 3} more" if len(u) > 3 else ""))
        if c["tie_breaks"]:
            why += "; meets tie-break(s): " + ", ".join(c["tie_breaks"])
        if i > 0:
            top = clusters[0]
            if len(c["families"]) < len(top["families"]):
                why += f"; lost: fewer families than the winner ({len(top['families'])})"
            elif c["rank_key"][1] < top["rank_key"][1]:
                lost = next(name for (name, _), a, b in zip(TIE_BREAKS, c["rank_key"][1], top["rank_key"][1]) if a != b)
                why += f"; lost on tie-break: {lost}"
            elif c["rank_key"] == top["rank_key"]:
                why += "; TIED with the winner -- your call (try other parts of speech or synonyms)"
            else:
                why += "; lost on fallback order / language count"
        elif len(c["families"]) == 1:
            why += "; no cross-family agreement: fallback order applied"
        c["why"] = why
    return clusters
