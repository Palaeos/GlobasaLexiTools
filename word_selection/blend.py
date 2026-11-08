"""Blend a cluster's source forms into candidate forms.

Votes are weighted so each FAMILY carries weight 1 (European = one family, split
among its languages; within a language, split among its forms). Close votes are
settled by the methodology's letter preferences. A candidate must differ from at
least one source form by at most 1 phoneme, or 2 close phonemes.
"""

import itertools

from .align import distance, edit_count, msa
from .languages import family

# Methodology: "e over a, e over i, o over any other vowel except u (u over o)";
# "m over n, l over r, h over k, g over k, d over t, p over b"; "s over z, w over v".
PREFER = {("e", "a"), ("e", "i"), ("o", "a"), ("o", "e"), ("o", "i"), ("u", "o"),
          ("m", "n"), ("l", "r"), ("h", "k"), ("g", "k"), ("d", "t"), ("p", "b"),
          ("s", "z"), ("w", "v")}
CLOSE_VOTE = 0.15    # votes within this (fraction of the column total) count as tied
CONTESTED = 0.6      # runner-up >= 60% of the winner -> also try it


WEIGHTING = "language"   # "language": each language 1 (form blending); "family": each family 1


def weights(members):
    """Weight per member: each language (or family) sums to 1. Family weighting
    decides the SOURCE (select.py); within a cluster, blending by language fits
    the lexicon better (word_selection_eval.py roots)."""
    if WEIGHTING == "language":
        per = {}
        for m in members:
            per[m["lang"]] = per.get(m["lang"], 0) + 1
        return [1.0 / per[m["lang"]] for m in members]
    fam_langs, lang_forms = {}, {}
    for m in members:
        fam_langs.setdefault(family(m["lang"]), set()).add(m["lang"])
        lang_forms[m["lang"]] = lang_forms.get(m["lang"], 0) + 1
    return [1.0 / len(fam_langs[family(m["lang"])]) / lang_forms[m["lang"]] for m in members]


def _prefer(a, b):
    """True if the methodology prefers letter a over b."""
    return (a, b) in PREFER


def _column_choices(col, ws, final=False):
    votes = {}
    for ch, w in zip(col, ws):
        votes[ch] = votes.get(ch, 0) + w
    total = sum(votes.values())
    ranked = sorted(votes.items(), key=lambda kv: -kv[1])
    best, bw = ranked[0]
    note = None
    # tie-break among near-equal letters by preference
    for ch, w in ranked[1:]:
        # letter preference does not apply to a final vowel (that is the a-posteriori
        # vowel, decided by source support in form_rules)
        if final and best in "aeiou":
            break
        if bw - w <= CLOSE_VOTE * total and ch != "-" and best != "-" and _prefer(ch, best):
            note = f"{ch} over {best} (methodology letter preference)"
            best, bw = ch, w
    choices = [best]
    for ch, w in ranked:
        if ch != best and w >= CONTESTED * bw:
            choices.append(ch)
    return choices[:2], note, votes


def candidates(members, max_variants=16):
    """members: [{lang, form, ...}] (form in Globasa letters).
    Returns [{form, score, origin, notes, closest}] sorted by score (lower better)."""
    members = [m for m in members if m["form"]]
    if not members:
        return []
    ws = weights(members)
    forms = [m["form"].replace(" ", "") for m in members]
    _, rows = msa(forms)
    columns = list(zip(*rows))
    picks, notes, contested = [], [], []
    for k, col in enumerate(columns):
        ch, note, votes = _column_choices(col, ws, final=(k == len(columns) - 1))
        picks.append(ch)
        if note:
            notes.append(note)
        if len(ch) > 1:
            contested.append(k)
    contested = contested[:4]

    out = {}

    def add(form, origin, extra_notes=()):
        if not form or form in out:
            return
        ok = False
        closest = None
        for m, f in zip(members, forms):
            n, close = edit_count(form, f)
            if n <= 1 or (n == 2 and close):
                ok = True
            d = distance(form, f, normalized=True)
            if closest is None or d < closest[0]:
                closest = (d, m["lang"], f)
        if not ok:
            return
        score = sum(w * distance(form, f, normalized=True) for w, f in zip(ws, forms)) / sum(ws)
        out[form] = {"form": form, "score": round(score, 4), "origin": origin,
                     "notes": list(extra_notes), "closest": closest}

    for combo in itertools.islice(itertools.product(*[picks[k] if k in contested else picks[k][:1]
                                                      for k in range(len(picks))]), max_variants):
        f = "".join(c for c in combo if c != "-")
        add(f, "consensus", notes)
    for m, f in zip(members, forms):
        add(f, f"source form ({m['lang']})")
    return sorted(out.values(), key=lambda c: c["score"])
