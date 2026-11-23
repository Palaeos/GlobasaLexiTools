"""Blend a cluster's source forms into candidate forms.

Votes are weighted so each FAMILY carries weight 1 (European = one family, split
among its languages; within a language, split among its forms). Close votes are
settled by the methodology's letter preferences. A candidate must differ from at
least one source form by at most 1 phoneme, or 2 close phonemes.
"""

import itertools

from . import precedent, sino_align
from .align import distance, edit_count, msa
from .languages import family

# Methodology: "e over a, e over i, o over any other vowel except u (u over o)";
# "m over n, l over r, h over k, g over k, d over t, p over b"; "s over z, w over v".
PREFER = {("e", "a"), ("e", "i"), ("o", "a"), ("o", "e"), ("o", "i"), ("u", "o"),
          ("m", "n"), ("l", "r"), ("h", "k"), ("g", "k"), ("d", "t"), ("p", "b"),
          ("s", "z"), ("w", "v")}
CLOSE_VOTE = 0.15    # votes within this (fraction of the column total) count as tied
CONTESTED = 0.6      # runner-up >= 60% of the winner -> also try it
# LexiliAsel precedent for Sino-xenic columns (precedent.py) takes priority over
# the vote; each column where a candidate departs from it costs this much
PRECEDENT_PENALTY = 0.15
# fallback (pipeline.propose): when the ordinary blends leave too few legal proposals,
# also try each source form with the precedent applied as far as closeness allows.
# As regular candidates they cost 1.2 pt top-1 (single-source forms outranked consensus).
PRECEDENT_PER_SOURCE = True


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


def candidates(members, max_variants=16, exclude_root=None, per_source=False):
    """members: [{lang, form, word, ...}] (form in Globasa letters).
    Where related forms disagree at a position, LexiliAsel precedent (precedent.py:
    Sino-xenic, Japanese/Korean loans, Arabic loans, Indic, European) decides before
    the vote and the generic letter preferences (Mandarin j / Japanese k / Korean g
    -> k), except in the word-final vowel slot, which form_rules decides.
    exclude_root: leave that root out of the precedent (evaluation).
    Returns [{form, score, origin, notes, closest, precedent}] sorted by score (lower better)."""
    members = [m for m in members if m["form"]]
    if not members:
        return []
    ws = weights(members)
    forms = [m["form"].replace(" ", "") for m in members]
    groups = precedent.applicable(members)
    # Sino-xenic clusters: aligned to the Middle Chinese reading, syllable by syllable
    rows = sino_align.rows(members, sino_idx=groups["sino"]) if "sino" in groups else None
    notes = []
    if rows is not None:
        notes += sino_align.fallback_notes(sino_align.spelling(members, groups["sino"])[0])
    elif "sino" in groups:
        notes.append("Sinosphere forms aligned letter by letter (fallback: no Han spelling shared by "
                     "two languages with readings, or mostly non-Sinosphere cluster)")
    if rows is None:
        _, rows = msa(forms)
    columns = list(zip(*rows))
    picks, contested = [], []
    prec = {}                      # column -> precedent letter
    prec_share = {}                # column -> share of roots behind that precedent
    end = precedent.final_slot(rows)    # the word-final vowel slot is form_rules' business
    for k, col in enumerate(columns):
        ch, note, votes = _column_choices(col, ws, final=(k == len(columns) - 1))
        p = precedent.decide(members, col, k, end, exclude_root, groups) if groups else None
        if p:
            letter, n, share, pattern, group = p
            prec[k] = letter
            prec_share[k] = share
            if ch[0] != letter:
                ch = [letter] + [c for c in ch if c != letter][:1]
                via = " ".join(f"{a}:{b}" for a, b in pattern if a not in ("follows", "same letter"))
                follows = dict(pattern).get("follows")
                if "same letter" in dict(pattern):
                    follows = "the letter, whichever language has it"
                notes.append(f"{letter if letter != '-' else '(none)'} at {via}: LexiliAsel precedent ({group}), "
                             f"{n} roots ({int(share * 100)}%)" + (f", following {follows}" if follows else ""))
        picks.append(ch)
        if note:
            notes.append(note)
        if len(ch) > 1:
            contested.append(k)
    contested = contested[:4]

    def departures(combo):
        return sum(1 for k, c in enumerate(combo) if k in prec and c != prec[k])

    out = {}

    def add(form, origin, extra_notes=(), departs=0):
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
        score += PRECEDENT_PENALTY * departs
        out[form] = {"form": form, "score": round(score, 4), "origin": origin,
                     "notes": list(extra_notes), "closest": closest,
                     "precedent": {"columns": len(prec), "departs": departs}}

    for combo in itertools.islice(itertools.product(*[picks[k] if k in contested else picks[k][:1]
                                                      for k in range(len(picks))]), max_variants):
        f = "".join(c for c in combo if c != "-")
        add(f, "precedent" if prec and not departures(combo) else "consensus", notes, departures(combo))
    for m, f, row in zip(members, forms, rows):
        add(f, f"source form ({m['lang']})", departs=departures(row))
    # Precedent applied to each source: the methodology's middle ground must stay
    # within one phoneme (or two close ones) of some source, and the combinations
    # above explore only a few contested columns, so a precedent-faithful form near a
    # source can be missed (黃泉: Korean hwangcan + the precedent's g-drop -> hwancan,
    # while every combination either kept the g or drifted 3+ edits from all sources).
    if per_source:
        out.clear()          # the fallback returns only the per-source candidates
        target = [prec.get(k, picks[k][0]) for k in range(len(picks))]
        order = sorted((k for k in range(len(picks)) if k < end),
                       key=lambda k: (k not in prec, -prec_share.get(k, 0)))
        for m, f, row in zip(members, forms, rows):
            cur = list(row)
            for k in order:
                if cur[k] == target[k]:
                    continue
                trial = cur[:k] + [target[k]] + cur[k + 1:]
                form = "".join(c for c in trial if c != "-")
                n, close = edit_count(form, f)
                if form and (n <= 1 or (n == 2 and close)):
                    cur = trial
            form = "".join(c for c in cur if c != "-")
            if form != f:
                add(form, f"precedent applied to the {m['lang']} form", [n for n in notes],
                    departures(cur))
    return sorted(out.values(), key=lambda c: c["score"])
