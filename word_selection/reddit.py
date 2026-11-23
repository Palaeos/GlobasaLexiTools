"""A Word Selector result as a Reddit post in the team's word-selection format
(Markdown that renders on new and old Reddit):

    **Ewropali** (Tongo to sen un famil.):
    - Englisa (sediment, dregs; sedimentate, subside; sedimentary)
    - Rusisa (отложение “otlojeniye”, осадок “osadok”; осаждать “osajdat”)
    **Alo** (Moyun to sen un famil.):
    - Putunhwa (沉积物 “cenjiu”; 堆積 “dweyji”)
    ...
    **Jeni:** twejiki (3 famil, "tweji"), rosuba (2 famil), sedimen (2 famil)

        P: dweyji
        K: twe jak
        J: twe jiki

    Nota: ...

Per language: words of one part of speech joined by ", ", parts of speech by "; "
(the concept's sense order); a non-Latin (and Vietnamese) word is followed by its
Globasa-letter form in curly quotes. Jeni: the blended clusters with two or more
families, in ranked order: best proposal, family count (a range when some members
are only loose resemblances), the runner-up in quotes. The leading candidate is
aligned (code block) against the closest source of each language. Nota: a Han
base taken from a 物 noun (-xey), and the team questions.
"""

import re
import unicodedata

from . import sino_align
from .align import msa
from .languages import BY_CODE, families

LIMIT = 40000          # Reddit self-post limit (characters)
_SPECIAL = re.compile(r"([\\*_^~|`>#\[\]])")

# the order the team lists source languages in
ORDER_EUROPE = ["en", "es", "fr", "ru", "de"]
ORDER_OTHER = ["id", "hi", "te", "ar", "sw", "fa", "tr", "cmn", "ko", "ja", "vi"]
QUOTED = {"vi"}                    # Latin script, but the Globasa form is not obvious
STRESS = {"\u0300", "\u0301"}  # Russian stress marks in Wiktionary headwords


def esc(s):
    """Escape Reddit Markdown in inline text (|, *, _, ^, ~, ...)."""
    return _SPECIAL.sub(r"\\\1", str(s or "")).replace("\n", " ")


def basa(lang):
    return BY_CODE.get(lang, {}).get("basa", lang)


def _plain(word, lang):
    """Drop Russian stress marks (отложе́ние -> отложение); other diacritics and
    Arabic/Persian vowel marks stay."""
    if lang != "ru":
        return word
    d = unicodedata.normalize("NFD", word)
    return unicodedata.normalize("NFC", "".join(ch for ch in d if ch not in STRESS))


def _form(w):
    return (w.get("forms") or [""])[0].replace(" ", "")


def _show(w):
    word = esc(_plain(w["word"], w["lang"]))
    quoted = w["lang"] in QUOTED or not BY_CODE.get(w["lang"], {}).get("latin", True)
    f = _form(w)
    return f"{word} “{esc(f)}”" if quoted and f else word


def _language_line(lang, words, sense_pos, pos_order, status):
    if not words:
        return f"- {basa(lang)} ({'nil lexi' if status == 'no word' else '—'})"
    groups, seen = {}, set()
    for w in words:
        key = _form(w) or _plain(w["word"], w["lang"]).lower()   # 沉积物 / 沉積物: one form, shown once
        pos = sense_pos.get(w.get("sense"), "") or w.get("pos", "") or pos_order[0]
        if (pos, key) in seen:
            continue
        seen.add((pos, key))
        groups.setdefault(pos, []).append(_show(w))
    order = pos_order + [p for p in groups if p not in pos_order]
    return f"- {basa(lang)} (" + "; ".join(", ".join(groups[p]) for p in order if p in groups) + ")"


def _count(c):
    """'3' or, when loose / unverified members are set aside, '2-3'."""
    hi = len(c.get("families") or [])
    sup = c.get("support")
    lo = len(families(sup)) if sup is not None else hi
    return f"{lo}-{hi}" if lo < hi else str(hi)


def _ok(p):
    return p.get("severity") not in ("BLOCK", "WARN")


def _candidates(clusters):
    blended = [c for c in clusters if any(_ok(p) for p in c.get("proposals") or [])]
    wide = [c for c in blended if len(c.get("families") or []) >= 2]
    return wide or blended[:3]


def _jeni(c, chosen_form):
    props = [p for p in c["proposals"] if _ok(p)]
    if chosen_form and any(p["form"] == chosen_form for p in props):
        props = [p for p in props if p["form"] == chosen_form] + [p for p in props if p["form"] != chosen_form]
    first = esc(props[0]["form"])
    s = (f"**{first}**" if props[0]["form"] == chosen_form else first) + f" ({_count(c)} famil"
    if len(props) > 1:
        s += f', "{esc(props[1]["form"])}"'
    return s + ")"


def _labels(langs):
    """One letter per language (P, K, N, V), two where first letters clash (En, Es)."""
    first = [basa(l)[0] for l in langs]
    return {l: basa(l)[:1] if first.count(basa(l)[0]) == 1 else basa(l)[:2] for l in langs}


def _alignment(c, chosen_form=None):
    """Lines aligning the leading proposal (J) with the closest source of each language."""
    props = [p for p in c["proposals"] if _ok(p)]
    p = next((q for q in props if q["form"] == chosen_form), props[0])
    picked = {}
    for d in p.get("distances") or []:          # sorted closest first
        picked.setdefault(d["lang"], d)
    langs = [l for l in ORDER_EUROPE + ORDER_OTHER if l in picked]
    if len(langs) < 2:
        return []
    members = [{"lang": l, "word": picked[l]["word"], "form": picked[l]["form"]} for l in langs]
    rows = sino_align.rows(members, extra=[p["form"]])
    if rows is None:
        _, rows = msa([m["form"] for m in members] + [p["form"]], candidates=range(len(members)))
    lab = _labels(langs)
    width = max(len(v) for v in lab.values())
    names = [lab[l] for l in langs] + ["J"]
    return [f"    {n.ljust(width)}: " + "".join(" " if ch == "-" else ch for ch in r).rstrip()
            for n, r in zip(names, rows)]


def _han_base_note(c, words, label, chosen_form=None):
    """Nota when the leading cluster is a Han base taken from a 物 noun (堆積 of 堆積物)."""
    bases = {(m.get("han_base") or {}).get("of") for m in c["members"]} - {None}
    if not bases:
        return []
    props = [p for p in c["proposals"] if _ok(p)]
    form = next((p["form"] for p in props if p["form"] == chosen_form), props[0]["form"])
    nouns = [w for w in words if not w.get("excluded")
             and any(b in (w.get("han") or []) for b in bases)]
    shown = ", ".join(f"{basa(w['lang'])} {esc(w['word'])}" for w in nouns) or ", ".join(sorted(bases))
    sp = sorted(bases)[0]
    return [f"Nota: {shown} = {esc(sp[:-1])} + {esc(sp[-1])} (\"thing\"). Cel \"{esc(label)}\": "
            f"**{esc(form)}xey**, eger {esc(form)} beseleti. (Check the meaning: {esc(sp[:-1])} may "
            "name only the action.)"]


def to_reddit(concept, res, chosen_form=None, max_props=None):
    """-> Markdown for a Reddit post in the team's word-selection format."""
    label = concept.get("label") or ", ".join(w for _, w, _, _ in concept.get("wikt_senses", [])) or "concept"
    sense_pos = {s[3]: s[2] for s in concept.get("wikt_senses", [])}
    pos_order = list(dict.fromkeys(s[2] for s in concept.get("wikt_senses", []))) or ["noun"]
    by_lang = {}
    for w in res["words"]:
        if not w.get("excluded"):
            by_lang.setdefault(w["lang"], []).append(w)
    status = res.get("status", {})
    L = ["**Ewropali** (Tongo to sen un famil.):", ""]
    L += [_language_line(l, by_lang.get(l, []), sense_pos, pos_order, status.get(l)) for l in ORDER_EUROPE]
    L += ["", "**Alo** (Moyun to sen un famil.):", ""]
    L += [_language_line(l, by_lang.get(l, []), sense_pos, pos_order, status.get(l)) for l in ORDER_OTHER]
    cands = _candidates(res.get("clusters", []))
    if cands:
        L += ["", "**Jeni:** " + ", ".join(_jeni(c, chosen_form) for c in cands)]
        al = _alignment(cands[0], chosen_form)
        if al:
            L += [""] + al
        notes = _han_base_note(cands[0], res["words"], label, chosen_form)
        if notes:
            L += [""] + notes
    for q in res.get("team_questions") or []:
        if q["if_yes"]["form"] == q["if_no"]["form"]:
            continue           # the answer changes nothing
        L += ["", f"Nota: {esc(q.get('question', ''))} If yes: **{esc(q['if_yes']['form'])}**; "
                  f"if no: **{esc(q['if_no']['form'])}**."]
    L += ["", "---", "", "^(Generated with the Globasa Word Selector; forms are proposals for discussion.)"]
    text = "\n".join(L) + "\n"
    return text[:LIMIT - 60] + "\n\n(truncated at Reddit's length limit)\n" if len(text) > LIMIT else text
