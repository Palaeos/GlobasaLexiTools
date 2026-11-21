"""Pooled period sense inventory: Wiktionary + Webster 1913 + period bilingual dictionaries.

    build(lemmas, keep_quote=None)   {lemma: [sense]}; keep_quote(words) -> False drops a
                                      quotation (leakage filter of the caller)
    prior(sense, year)               -1 / 0 / +1: first attested well after the year (or Webster
                                      [Obs.] in a year before 1913) / unknown / attested around
                                      the year (or current in Webster 1913)
    glb_candidates(sense)            [(Globasa word, how)] for the sense, best first

A sense = {pos, gloss, defs (all definition texts), source wiktionary|webster|both, tags
(Wiktionary), labels (Webster), examples [(words, idx, src)], years (first, last, n) or None,
epo {word: how}, spa {word: how}, table {"es": set, "eo": set} (modern Wiktionary table)}.

Alignment: each Webster sense joins the Wiktionary sense of the same part of speech whose
definition shares most content words (cosine of word sets, + 0.1 when both are marked old;
>= ALIGN_MIN), else it stays a sense of its own ('webster' source, a period-only sense).
Quotation years: wiktionary_quote_years.tsv (Warehouse2), joined on (word, pos, gloss).

Period dictionary equivalents per sense (period_dict_entries.py):
  Esperanto  Rhodes 1908 + O'Connor 1907 segments; part of speech from the Esperanto ending;
             a segment goes to a sense by its English cue "(note), noto" (content words shared
             with the sense's definitions), else by a 5-letter stem shared with the sense's
             modern Wiktionary eo table, else to every sense of that part of speech
             "(fallback: dictionary entry, no sense cue)"
  Spanish    Velázquez 1910 numbered senses, same routes with the es table. Spanish CONFIRMS
             only (user: Spanish drifted over the century, luego 'at once' -> 'later'):
             glb_candidates never lets a Spanish-only match outrank an Esperanto one and labels
             it "(fallback: Spanish only, 1910 sense may have drifted)"; "(Ant.)" = old in 1910.
Globasa: the word list's TranslationEpo / TranslationSpa, same part-of-speech segment, matched
by 5-letter stems; else the sense's modern Wiktionary eo/es table "(fallback: modern Wiktionary
table)"."""
import csv
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import period_dict_entries as pde  # noqa: E402
from bert_words import words  # noqa: E402

WEBSTER = os.path.join(HERE, "cache", "sources", "webster_1913.txt")
QUOTE_YEARS = os.environ.get("QY_OUT", "/media/paleos/Warehouse2/Language/Claude/wiktionary_quote_years.tsv")
WORD_LIST = os.path.join(ROOT, "word-list.csv")
WIKT_POS = ("adj", "adv", "noun", "verb", "prep", "conj", "intj")
OLD_TAGS = {"obsolete", "archaic", "dated", "historical"}
OLD_LABELS = {"Obs.", "Obs", "Archaic"}
ALIGN_MIN = 0.25
ALIGN_WEAK = 0.15
SLACK = 25
MAX_WORDS = 120
MAX_QUOTES = 12
STOP = set("a an the of to in on for and or by with as at from that this be is are was it its "
           "one's someone something oneself who which what not no very more most into out up "
           "being having make made do done any thing used also etc".split())
HEAD = re.compile(r"^[A-Z][A-Z' -]*$")
W_POS = re.compile(r",\s*(v\.\s*[ti]\.|a\.|adv\.|n\.|prep\.|conj\.|interj\.|p\.\s*p\.|p\.\s*a\.)")
W_POS_MAP = {"a": "adj", "adv": "adv", "n": "noun", "prep": "prep", "conj": "conj", "interj": "intj",
             "v": "verb", "p": "adj"}
SENSE_START = re.compile(r"^(?:(\d{1,2})\.\s+|Defn:\s*)")
LABEL = re.compile(r"\[(Obs\.?|Archaic|Poetic|R\.|Colloq\.|Slang|Prov\. Eng\.|Eng\.|Local[^\]]*)\]")
SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"“'(])")
AS_EX = re.compile(r"\bas,\s+([^;.]+)")
# Velázquez: "Remark, va. 1. ...", embedded next headwords "Presentment [prg-zent'-ment], s."
V_HEAD = re.compile(r"(?:^|(?<=[.;] ))([A-Z][a-z'-]+)(?:\s+\[[^\]]*\]|\s+\S*['’]\S*)?,?\s+(s|a|adv|va|vn|vr|prep|conj|pp|pa)\.\s")
V_POS = {"s": "noun", "a": "adj", "adv": "adv", "va": "verb", "vn": "verb", "vr": "verb", "prep": "prep",
         "conj": "conj", "pp": "adj", "pa": "adj"}
V_NUM = re.compile(r"(?:^|\s)(\d{1,2})\.\s")
EPO_POS = (("oj", "noun"), ("o", "noun"), ("aj", "adj"), ("a", "adj"), ("e", "adv"), ("i", "verb"))
WL_LABEL = {"n": "noun", "s": "noun", "v": "verb", "adj": "adj", "a": "adj", "adv": "adv", "prep": "prep",
            "conj": "conj", "interj": "intj"}


def content(text):
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOP and len(w) > 2}


def form_matches(tok, lemma):
    t = tok.lower()
    if t == lemma:
        return True
    stem = lemma[:-1] if lemma[-1:] in "ey" and len(lemma) > 4 else lemma
    return len(stem) >= 3 and t.startswith(stem) and len(t) - len(lemma) <= 4


def _example(text, lemma):
    ws = words(text)
    k = next((i for i, x in enumerate(ws) if form_matches(x, lemma)), None)
    if k is None:
        return None
    lo = max(0, k - MAX_WORDS // 2)
    return ws[lo:lo + MAX_WORDS], k - lo


# ---------------------------------------------------------------- Webster 1913
def webster_blocks(lemmas):
    out, head, buf = {}, None, []
    with open(WEBSTER, encoding="latin-1") as f:
        for line in f:
            s = line.rstrip("\n")
            if HEAD.match(s.strip()) and len(s.strip()) > 1:
                if head in lemmas and buf:
                    out.setdefault(head, []).append("\n".join(buf))
                head, buf = s.strip().lower(), []
            elif head in lemmas:
                buf.append(s)
    if head in lemmas and buf:
        out.setdefault(head, []).append("\n".join(buf))
    return out


def webster_senses(lemma, blocks):
    out = []
    for block in blocks:
        first = block.strip().split("\n", 1)[0]
        m = W_POS.search(first)
        pos = W_POS_MAP.get(m.group(1).split(".")[0].strip(), "?") if m else "?"
        for para in re.split(r"\n\s*\n", block):
            para = " ".join(para.split())
            sm = SENSE_START.match(para)
            if not sm:
                continue
            body = para[sm.end():]
            labels = set(LABEL.findall(body))
            defn, examples = [], []
            for i, s in enumerate(SENT.split(body)):
                ex = _example(s, lemma) if i > 0 else None
                if ex:
                    examples.append(ex)
                elif not examples:
                    defn.append(s)
            for phrase in AS_EX.findall(" ".join(defn)):
                ex = _example(phrase, lemma)
                if ex:
                    examples.append(ex)
            d = re.sub(r"\bas,\s+[^;.]+", "", " ".join(defn)).strip()
            out.append({"pos": pos, "defn": d, "labels": labels, "examples": examples})
    return out


# ---------------------------------------------------------------- Wiktionary
def quote_years(lemmas):
    out = {}
    if not os.path.exists(QUOTE_YEARS):
        return out
    with open(QUOTE_YEARS, encoding="utf-8") as f:
        next(f)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if p[0] in lemmas and len(p) >= 8 and p[6]:
                out[p[0], p[1], p[3].strip()] = (int(p[6]), int(p[7]), int(p[5] or 0))
    return out


def wiktionary_senses(db, lemma, years, keep_quote):
    from sense_rows import match_sense_to_definition
    out = []
    for pos in WIKT_POS:
        ss = db.get_senses(lemma, pos) or []
        mine = []
        for s in ss:
            # the LAST gloss is the specific one: sub-senses share their parent's heading as
            # glosses[0] ("Homosexual:" x 10 for gay), and wiktionary_quote_years.tsv keys on it
            gloss = s.glosses[-1].strip() if s.glosses else ""
            if not gloss:
                continue
            exs = []
            for ex in s.examples:
                text = ex[0] if isinstance(ex, (list, tuple)) else ex
                e = _example(text, lemma)
                if e and (keep_quote is None or keep_quote(e[0])):
                    exs.append(e)
                if len(exs) >= MAX_QUOTES:
                    break
            sense = {"pos": pos, "gloss": gloss, "defs": list(dict.fromkeys(g.strip() for g in s.glosses)),
                     "source": "wiktionary",
                     "tags": set(s.tags), "labels": set(),
                     "examples": [(w, k, "wiktionary") for w, k in exs],
                     "years": next((years[lemma, pos, g.strip()] for g in reversed(s.glosses)
                                    if (lemma, pos, g.strip()) in years), None), "epo": {}, "spa": {},
                     "table": {"es": set(), "eo": set()}, "_obj": s,
                     # sub-senses share their parent heading: decide the group first (choose())
                     "group": (pos, s.glosses[0].strip()) if len(s.glosses) > 1 else None}
            mine.append(sense)
        for tkey, langs in (db.get_translations(lemma, pos) or {}).items():
            m = match_sense_to_definition(tkey, ss)
            hit = next((x for x in mine if x["_obj"] is m), None)
            if hit:
                for code in ("es", "eo"):
                    for t in langs.get(code, ()):
                        hit["table"][code].update(w for w in re.split(r"[\s/]+", t.word.lower()) if len(w) > 1)
        out += mine
    for s in out:
        del s["_obj"]
    return out


BRIT = re.compile(r"(?<=[a-z]{2})our(?=(?:s|ful|ed|ing|ite|able|ly|less)?$)")  # colour -> color


def norm_stems(text):
    """5-letter stems of the content words, British spellings folded (colourful ~ colors)."""
    return {BRIT.sub("or", w)[:5] for w in content(text)}


def _sim(a, b):
    a, b = norm_stems(a), norm_stems(b)
    return len(a & b) / ((len(a) * len(b)) ** 0.5) if a and b else 0.0


def align(wikt, webs):
    """Webster senses into the Wiktionary list (in place); unmatched ones appended."""
    stats = {"joined": 0, "own": 0}
    for b in webs:
        best, score, second = None, 0.0, 0.0
        for w in wikt:
            if w["pos"] != b["pos"] or w["source"] == "webster":
                continue
            sc = _sim(b["defn"], w["gloss"]) + (0.1 if b["labels"] & OLD_LABELS and w["tags"] & OLD_TAGS else 0)
            if sc > score:
                best, score, second = w, sc, score
            elif sc > second:
                second = sc
        # a clear match, or a weaker one that is clearly unique (runner-up under half of it)
        if best is not None and (score >= ALIGN_MIN or (score >= ALIGN_WEAK and second < score / 2)):
            best["defs"].append(b["defn"])
            best["labels"] |= b["labels"]
            best["examples"] += [(w, k, "webster") for w, k in b["examples"]]
            best["source"] = "both"
            stats["joined"] += 1
        else:
            wikt.append({"pos": b["pos"], "gloss": b["defn"], "defs": [b["defn"]], "source": "webster",
                         "tags": set(), "labels": set(b["labels"]),
                         "examples": [(w, k, "webster") for w, k in b["examples"]], "years": None,
                         "epo": {}, "spa": {}, "table": {"es": set(), "eo": set()}, "group": None})
            stats["own"] += 1
    return stats


# ---------------------------------------------------------------- period bilingual dictionaries
def _epo_pos(word):
    w = pde.fold(word)
    for end, pos in EPO_POS:
        if w.endswith(end):
            return pos
    return None


def rhodes_segments(entry_texts):
    """[(cue, [esperanto words])] -- English cue in parentheses before the words, if any."""
    out = []
    for text in entry_texts:
        for block in re.split(r"——+,*", text):
            block = block.split(". ")[0]  # derived headwords follow after a full stop
            for seg in block.split(";"):
                m = re.match(r"\s*(?:,?\s*to,)?\s*(?:\(([^)]*)\),?)?\s*(.*)", seg)
                cue, rest = (m.group(1) or "").strip(), m.group(2)
                ws = [w.strip(" .,’'") for w in re.split(r"[,\s]+", rest)]
                ws = [w for w in ws if len(w) > 2 and re.match(r"^[a-zĉĝĥĵŝŭ’'\-]+$", w)]
                if ws:
                    out.append((cue, ws))
    return out


def velazquez_segments(entry_texts, lemma):
    """[(pos, n, old, [spanish words])] -- only the parts headed by the lemma itself."""
    out = []
    for text in entry_texts:
        heads = list(V_HEAD.finditer(text))
        spans = []
        if not heads or heads[0].start() > 0:  # entry text starts with its own pos
            m = re.match(r"\s*(s|a|adv|va|vn|vr|prep|conj|pp|pa)\.\s", text)
            if m:
                spans.append((V_POS[m.group(1)], m.end(), heads[0].start() if heads else len(text)))
        for i, h in enumerate(heads):
            if h.group(1).lower() != lemma:
                continue
            spans.append((V_POS[h.group(2)], h.end(), heads[i + 1].start() if i + 1 < len(heads) else len(text)))
        for pos, a, b in spans:
            body = text[a:b]
            parts = V_NUM.split(body)
            pieces = [(None, parts[0])] + [(int(parts[i]), parts[i + 1]) for i in range(1, len(parts) - 1, 2)]
            for n, piece in pieces:
                old = "(Ant.)" in piece
                piece = re.sub(r"\([^)]*\)", " ", piece).split(" To ")[0]
                ws = [w.strip(" .,;") for w in re.split(r"[,;]\s*", piece)]
                ws = [w.lower() for w in ws if 2 < len(w) < 40 and re.match(r"^[A-Za-záéíóúñü ]+$", w)]
                if ws:
                    out.append((pos, n, old, ws))
    return out


def _stems(ws):
    return {pde.stem(t) for w in ws for t in w.split() if len(t) > 2}


def attach(senses, lemma, dicts):
    """Esperanto/Spanish period equivalents into the senses (in place)."""
    _, rh = pde.lookup(dicts["rhodes"], lemma)
    _, oc = pde.lookup(dicts["oconnor"], lemma)
    for cue, ws in rhodes_segments(list(rh) + list(oc)):
        by_pos = defaultdict(list)
        for w in ws:
            by_pos[_epo_pos(w)].append(w)
        for pos, group in by_pos.items():
            cands = [s for s in senses if s["pos"] == pos] if pos else senses
            if not cands:
                continue
            target, how = None, None
            if cue:
                sc = [(len(content(cue) & content(" ".join(s["defs"]))), i) for i, s in enumerate(cands)]
                best = max(sc)
                if best[0] and [x for x, _ in sc].count(best[0]) == 1:
                    target, how = [cands[best[1]]], f"Rhodes/O'Connor, cue ({cue})"
            if target is None:
                st = _stems(group)
                sc = [(len(st & _stems(s["table"]["eo"])), i) for i, s in enumerate(cands)]
                best = max(sc)
                if best[0] and [x for x, _ in sc].count(best[0]) == 1:
                    target, how = [cands[best[1]]], "Rhodes/O'Connor, shares a stem with the sense's eo table"
            if target is None:
                target, how = cands, "Rhodes/O'Connor (fallback: dictionary entry, no sense cue)"
            for s in target:
                for w in group:
                    s["epo"].setdefault(w, how)
    _, ve = pde.lookup(dicts["velazquez"], lemma)
    for pos, n, old, ws in velazquez_segments(list(ve), lemma):
        cands = [s for s in senses if s["pos"] == pos]
        if not cands:
            continue
        st = _stems(ws)
        sc = [(len(st & _stems(s["table"]["es"])), i) for i, s in enumerate(cands)]
        best = max(sc)
        tag = " (Ant.: old in 1910)" if old else ""
        if best[0] and [x for x, _ in sc].count(best[0]) == 1:
            target, how = [cands[best[1]]], f"Velázquez {n or ''}{tag}, shares a stem with the sense's es table"
        else:
            target, how = cands, f"Velázquez {n or ''}{tag} (fallback: dictionary entry, no sense cue)"
        for s in target:
            for w in ws:
                s["spa"].setdefault(w, how)


# ---------------------------------------------------------------- Globasa via the word list
_wl_index = None


def _word_list_index():
    """{(lang, pos, stem): {globasa word}} from TranslationEpo / TranslationSpa segments."""
    global _wl_index
    if _wl_index is not None:
        return _wl_index
    _wl_index = defaultdict(set)
    with open(WORD_LIST, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            for lang, col in (("eo", "TranslationEpo"), ("es", "TranslationSpa")):
                text = re.sub(r"\(_.*?_\)|_.*?_|\(.*?\)", " ", r.get(col) or "")
                for seg in re.split(r";\s*(?=[a-z.]+\s*:)", text):
                    m = re.match(r"\s*([a-z.]+)\s*:\s*(.*)", seg)
                    pos = WL_LABEL.get(m.group(1).split(".")[0]) if m else None
                    body = m.group(2) if m else seg
                    for w in re.split(r"[;,]\s*", body):
                        w = w.strip().lower()
                        if w and " " not in w:  # single-word glosses: stems of phrases are noise
                            _wl_index[lang, pos, pde.stem(w)].add(r["Word"])
    return _wl_index


def _glb_for(lang, pos, ws):
    idx = _word_list_index()
    hits = defaultdict(int)
    for w in ws:
        for g in idx.get((lang, pos, pde.stem(w)), set()) | idx.get((lang, None, pde.stem(w)), set()):
            hits[g] += 1
    return sorted(hits, key=lambda g: -hits[g])


def glb_candidates(sense, n=3):
    pos = sense["pos"]
    epo_sense = [w for w, how in sense["epo"].items() if "fallback" not in how]
    epo_any = list(sense["epo"])
    spa_sense = [w for w, how in sense["spa"].items() if "fallback" not in how]
    out, seen = [], set()

    def add(cands, how):
        for g in cands:
            if g not in seen and len(out) < n:
                seen.add(g)
                out.append((g, how))

    epo = _glb_for("eo", pos, epo_sense)
    spa = set(_glb_for("es", pos, spa_sense))
    add([g for g in epo if g in spa], "period Esperanto + Spanish agree")
    add(epo, "period Esperanto (Rhodes/O'Connor)")
    if not out:
        epo2 = _glb_for("eo", pos, epo_any)
        add(epo2, "period Esperanto (fallback: dictionary entry, no sense cue)")
    if not out and spa:
        add(sorted(spa), "period Spanish (fallback: Spanish only, 1910 sense may have drifted)")
    if not out:
        add(_glb_for("eo", pos, sense["table"]["eo"]), "(fallback: modern Wiktionary eo table)")
    if not out:
        add(_glb_for("es", pos, sense["table"]["es"]), "(fallback: modern Wiktionary es table; Spanish only)")
    return out


# ---------------------------------------------------------------- prior + build
MODERN_FROM = 1950
DATED_TAGS = {"obsolete", "archaic", "dated"}  # not 'historical': a historical referent, not a dated word


def prior(sense, year):
    y = sense.get("years")
    if year >= MODERN_FROM and (sense["tags"] & DATED_TAGS or sense["labels"] & OLD_LABELS):
        return -1  # a modern text: a sense dictionaries mark as dated/obsolete is unlikely
    if sense["labels"] & OLD_LABELS and year < 1913:
        # obsolete by 1913: may still be literary in the 1890s, but a weak claim
        return -1 if year > 1850 else 0
    if y:
        first, last, _ = y
        if first > year + SLACK:
            return -1
        if first <= year + SLACK and last >= year - SLACK:
            return 1
        return 0
    if sense["source"] in ("webster", "both") and 1850 <= year <= 1950:
        return 1  # in a 1913 dictionary without an obsolete label
    return 0


def groups(inv_l):
    """{sense index: group key}; senses without a parent heading are their own group."""
    return {k: (s["group"] if s.get("group") else ("own", k)) for k, s in enumerate(inv_l)}


def choose(inv_l, cand, sim, gsim, year, prior_w):
    """Group first, then the member: (picked index, {index: group-level score}).
    sim: {index: cosine to the sense prototype}; gsim: {group key: cosine to the group
    prototype (all members' examples)}. A group's prior is its best member's."""
    grp = groups(inv_l)
    by_g = {}
    for k in cand:
        by_g.setdefault(grp[k], []).append(k)
    gscore = {g: gsim[g] + prior_w * max(prior(inv_l[k], year) for k in ks) for g, ks in by_g.items()}
    g = max(gscore, key=gscore.get)
    k = max(by_g[g], key=lambda j: sim[j] + prior_w * prior(inv_l[j], year))
    return k, {j: gscore[grp[j]] for j in cand}


def _synonym_examples(db, lemma, sense, keep_quote, n=8):
    """Examples for a sense that has none: its definition's single-word synonyms ("Loose;
    dissipated; lewd"); a synonym with more than 2 senses contributes only the sense whose
    glosses share most stems with ours (unique best); its Wiktionary examples with the headword
    put in the synonym's place."""
    out = []
    syns = [w.strip(" .").lower() for d in sense["defs"] for w in re.split(r"[;,]", re.sub(r"\[[^\]]*\]|\(.*?\)", "", d))]
    own = norm_stems(" ".join(sense["defs"]))
    for syn in dict.fromkeys(w for w in syns if re.fullmatch(r"[a-z]{3,}", w) and w != lemma):
        ss = db.get_senses(syn, sense["pos"]) or []
        if len(ss) > 2:  # ambiguous synonym: only its sense that shares most stems with ours
            sc = [len(own & norm_stems(" ".join(x.glosses))) for x in ss]
            best = max(sc) if sc else 0
            ss = [ss[sc.index(best)]] if best and sc.count(best) == 1 else []
        for s in ss:
            for ex in s.examples:
                text = ex[0] if isinstance(ex, (list, tuple)) else ex
                e = _example(text, syn)
                if not e:
                    continue
                ws = list(e[0])
                ws[e[1]] = lemma
                if keep_quote is None or keep_quote(ws):
                    out.append((ws, e[1], f"synonym substitution: {syn}"))
                if len(out) >= n:
                    return out
    return out


def build(lemmas, keep_quote=None):
    from wiktionary_db import WiktionaryDB
    lemmas = set(lemmas)
    years = quote_years(lemmas)
    web = webster_blocks(lemmas)
    dicts = pde.load(all_entries=True)
    inv, stats = {}, defaultdict(int)
    old = os.getcwd()
    os.chdir(ROOT)  # WiktionaryDB path is repo-relative
    try:
        with WiktionaryDB() as db:
            for lemma in sorted(lemmas):
                ss = wiktionary_senses(db, lemma, years, keep_quote)
                webs = webster_senses(lemma, web.get(lemma, []))
                for k, v in align(ss, webs).items():
                    stats[k] += v
                if not ss:
                    continue
                attach(ss, lemma, dicts)
                for s in ss:
                    if not s["examples"]:
                        s["examples"] = _synonym_examples(db, lemma, s, keep_quote)
                    if not s["examples"]:
                        text = s["gloss"]
                        s["examples"] = [([lemma, ":"] + words(text)[:MAX_WORDS - 2], 0, "gloss fallback")]
                inv[lemma] = ss
    finally:
        os.chdir(old)
    stats["lemmas"] = len(inv)
    stats["senses"] = sum(map(len, inv.values()))
    stats["with years"] = sum(1 for v in inv.values() for s in v if s["years"])
    stats["with period epo (sense)"] = sum(1 for v in inv.values() for s in v
                                           if any("fallback" not in h for h in s["epo"].values()))
    stats["synonym substitution"] = sum(1 for v in inv.values() for s in v
                                        if s["examples"][0][2].startswith("synonym"))
    stats["gloss fallback"] = sum(1 for v in inv.values() for s in v if s["examples"][0][2] == "gloss fallback")
    return inv, dict(stats)
