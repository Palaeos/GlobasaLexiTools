"""Map MacBERTh (historical English BERT, MIT) word embeddings into the mBERT space.

Why: mBERT shares one space with Spanish, Esperanto, French, German..., so pivot alignment and a
lexical-choice classifier trained there work across languages; MacBERTh (EEBO, ECCO, COHA,
CLMET, EVANS, Hansard; 1450-1950) knows period English senses. A map lets period English
contexts embedded by MacBERTh be compared with pivot words embedded by mBERT.

How: both models embed the SAME English sentences (period side: Heinemann Time Machine 1895,
or with MAP_PERIOD=sources the period sources in sources/ so the book stays unseen; modern: the
English sides of Doxo_passages_extended.tmx = modern), word by word (mean of the word's
subword vectors at layer MAP_LAYER, default 8 = SimAlign's layer). Sentences split 90/10 into
train/test. Both spaces are centred (train mean) and unit-normalised, then:
  procrustes  orthogonal W (a rotation: keeps MacBERTh's distances, so its period distinctions
              survive; the inverse map mBERT -> MacBERTh is W.T)
  ridge       unconstrained linear W (fits closer, may flatten distinctions)
Report on test words, period and modern apart:
  cos      mean cosine of mapped MacBERTh vector and the true mBERT vector of the same token
  P@1 tok  nearest mBERT test vector is the same token occurrence (among <= 20k candidates)
  P@1 word nearest is the same word type
  identity baseline = no map.
Downstream: English (mapped MacBERTh) <-> Spanish (mBERT) links vs English (mBERT) <-> Spanish
(mBERT) links on UDHR + Pepper & Carrot units (mutual argmax, SimAlign's 'inter'): agreement.

    ../venv/bin/python time-machine/macberth_map.py      (from the repo root or anywhere)

Cache: $GLOBASA_BIG_CACHE/macberth/macberth_vecs_L{layer}.npz (float16; default
/media/paleos/Warehouse2/Language/Claude; off when that is missing or MAP_CACHE_VECS=0); writes
time-machine/cache/macberth_to_mbert_L{layer}.npz (W_procrustes, W_ridge, means) and
time-machine/macberth_map_report.txt."""
import glob
import os
import re
import sys
import xml.etree.ElementTree as ET

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bert_words import MACBERTH, MBERT, device, embed as _embed, load, words  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(HERE, "cache")
LAYER = int(os.environ.get("MAP_LAYER", "8"))
# MAP_PERIOD=heinemann (default): period side = The Time Machine; =sources: the period sources
# (Wells essays, Tylor, Huxley, Lankester; capped at MAX_SOURCE_SENTS), for tests ON the book
PERIOD = os.environ.get("MAP_PERIOD", "heinemann")
SUFFIX = f"L{LAYER}" + ("" if PERIOD == "heinemann" else "_" + PERIOD)
# big caches go to the large data drive (GLOBASA_BIG_CACHE), never the nearly full system disk
BIG = os.environ.get("GLOBASA_BIG_CACHE", "/media/paleos/Warehouse2/Language/Claude")
VECS = os.path.join(BIG, "macberth", f"macberth_vecs_{SUFFIX}.npz")
MAPS = os.path.join(CACHE, f"macberth_to_mbert_{SUFFIX}.npz")
REPORT = os.path.join(HERE, f"macberth_map_report{'' if PERIOD == 'heinemann' else '_' + PERIOD}.txt")
PERIOD_TEXTS = ([os.path.join(HERE, "text", "heinemann.txt")] if PERIOD == "heinemann"
                else sorted(glob.glob(os.path.join(HERE, "sources", "*.txt"))))
MAX_SOURCE_SENTS = 4000
TMX = os.path.join(ROOT, "Doxo_passages_extended.tmx")
XLANG = "{http://www.w3.org/XML/1998/namespace}lang"
SENT_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"“‘'])")
MAX_WORDS = 120
RIDGE = 1.0
SIBLING_CTX = ("Globatotal Deklaradoku", "Pilpil ji Karote")


def embed(tok, model, sents):
    return _embed(tok, model, sents, LAYER)


out_lines = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out_lines.append(s)


def period_sentences():
    out = []
    for path in PERIOD_TEXTS:
        text = open(path, encoding="utf-8").read()
        for para in re.split(r"\n\s*\n", text):
            para = " ".join(re.sub(r"\[p\. \d+\]", " ", para).split())
            if len(para) < 20 or para.startswith("#"):
                continue
            for s in SENT_END.split(para):
                w = words(s)
                if 3 <= len(w) <= MAX_WORDS:
                    out.append(w)
    if PERIOD != "heinemann" and len(out) > MAX_SOURCE_SENTS:  # even spread over the sources
        step = len(out) / MAX_SOURCE_SENTS
        out = [out[int(k * step)] for k in range(MAX_SOURCE_SENTS)]
    return out


def tmx_units():
    for tu in ET.parse(TMX).getroot().iter("tu"):
        ctx = next((p.text for p in tu.findall("prop") if p.get("type") == "x-context"), "") or ""
        segs = {tuv.get(XLANG): "".join(tuv.find("seg").itertext()).strip() for tuv in tu.findall("tuv")}
        yield ctx, segs


def normalise(x, mean):
    x -= mean
    x /= np.linalg.norm(x, axis=1, keepdims=True) + 1e-8
    return x


def p_at_1(a, b, labels):
    """a, b: (n, d) unit vectors; nearest b row to each a row is the same row / same label."""
    tok_hits = word_hits = 0
    for i in range(0, len(a), 4096):
        nn = (a[i:i + 4096] @ b.T).argmax(1)
        idx = np.arange(i, i + len(nn))
        tok_hits += int((nn == idx).sum())
        word_hits += int((labels[nn] == labels[idx]).sum())
    return tok_hits / len(a), word_hits / len(a)


# ---------------------------------------------------------------- word vectors (cached)
CACHE_VECS = os.environ.get("MAP_CACHE_VECS", "1" if os.path.isdir(BIG) else "0") == "1"  # float16
if CACHE_VECS and os.path.exists(VECS):
    d = np.load(VECS, allow_pickle=False)
    mac, mb = d["mac"].astype(np.float32), d["mb"].astype(np.float32)
    wlab, sid, is_period = d["word"], d["sid"], d["period"]
    say(f"cached vectors: {len(wlab)} words")
else:
    per = period_sentences()
    mod, seen = [], set()
    for ctx, segs in tmx_units():
        en = segs.get("en")
        if en and en not in seen:
            seen.add(en)
            w = words(en)
            if 3 <= len(w) <= MAX_WORDS:
                mod.append(w)
    sents = per + mod
    say(f"{len(per)} period sentences, {len(mod)} modern sentences on {device}")
    vecs = {}
    for name in (MACBERTH, MBERT):
        tok, model = load(name)
        vecs[name] = embed(tok, model, sents)
        del tok, model
    keep_mac, keep_mb, wl, sl, pl = [], [], [], [], []
    for s, (ws, a, b) in enumerate(zip(sents, vecs[MACBERTH], vecs[MBERT])):
        ok = ~(np.isnan(a).any(1) | np.isnan(b).any(1))
        keep_mac.append(a[ok])
        keep_mb.append(b[ok])
        wl += [w.lower() for w, k in zip(ws, ok) if k]
        sl += [s] * int(ok.sum())
        pl += [s < len(per)] * int(ok.sum())
    del vecs
    mac, mb = np.concatenate(keep_mac), np.concatenate(keep_mb)
    wlab, sid, is_period = np.array(wl), np.array(sl, dtype=np.int32), np.array(pl)
    del keep_mac, keep_mb
    if CACHE_VECS:
        os.makedirs(os.path.dirname(VECS), exist_ok=True)
        np.savez(VECS, mac=mac.astype(np.float16), mb=mb.astype(np.float16), word=wlab, sid=sid,
                 period=is_period)
    say(f"{len(wlab)} word vectors")

# ---------------------------------------------------------------- fit
rng = np.random.default_rng(0)
test_sents = set(rng.choice(np.unique(sid), size=max(1, len(np.unique(sid)) // 10), replace=False).tolist())
test = np.isin(sid, list(test_sents))
mu_mac, mu_mb = mac[~test].mean(0), mb[~test].mean(0)
mac = normalise(mac, mu_mac)
mb = normalise(mb, mu_mb)
X, Y = mac[~test], mb[~test]
U, _, Vt = np.linalg.svd(X.T @ Y)
W_proc = (U @ Vt).astype(np.float32)
W_ridge = np.linalg.solve(X.T @ X + RIDGE * np.eye(X.shape[1], dtype=np.float32), X.T @ Y).astype(np.float32)
del X, Y, U, Vt
np.savez(MAPS, W_procrustes=W_proc, W_ridge=W_ridge, mean_macberth=mu_mac, mean_mbert=mu_mb,
         layer=LAYER)
say(f"layer {LAYER}; train words {int((~test).sum())}, test words {int(test.sum())}")

say(f"\n{'map':10s} {'test part':8s} {'n':>6s} {'cos':>6s} {'P@1 tok':>8s} {'P@1 word':>9s}")
for part, sel in (("period", test & is_period), ("modern", test & ~is_period)):
    idx = np.flatnonzero(sel)[:20000]
    b = mb[idx]
    for name, W in (("identity", None), ("procrustes", W_proc), ("ridge", W_ridge)):
        a = mac[idx] if W is None else mac[idx] @ W
        a /= np.linalg.norm(a, axis=1, keepdims=True) + 1e-8
        cos = float((a * b).sum(1).mean())
        pt, pw = p_at_1(a, b, wlab[idx])
        say(f"{name:10s} {part:8s} {len(idx):6d} {cos:6.3f} {100 * pt:7.1f}% {100 * pw:8.1f}%")

# ---------------------------------------------------------------- downstream: en <-> es links
units = [(words(s["en"]), words(s["es"])) for ctx, s in tmx_units()
         if ctx.startswith(SIBLING_CTX) and s.get("en") and s.get("es")]
units = [(e, p) for e, p in units if 3 <= len(e) <= MAX_WORDS and 1 <= len(p) <= MAX_WORDS]
del mac, mb
tok_mb, mod_mb = load(MBERT)
en_mb = embed(tok_mb, mod_mb, [e for e, _ in units])
es_mb = embed(tok_mb, mod_mb, [p for _, p in units])
del tok_mb, mod_mb
tok_mac, mod_mac = load(MACBERTH)
en_mac = embed(tok_mac, mod_mac, [e for e, _ in units])
del tok_mac, mod_mac


def inter(a, b):
    """mutual-argmax links of two (n, d), (m, d) arrays (NaN rows never link)."""
    a = np.nan_to_num(a)
    b = np.nan_to_num(b)
    a = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-8)
    b = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-8)
    s = a @ b.T
    fw, bw = s.argmax(1), s.argmax(0)
    return {(i, int(j)) for i, j in enumerate(fw) if bw[j] == i}


def mapped(x, W):
    x = x - mu_mac
    x /= np.linalg.norm(x, axis=1, keepdims=True) + 1e-8
    return x @ W


say(f"\nen<->es links on {len(units)} UDHR + P&C units, mutual argmax "
    f"(reference = mBERT en <-> mBERT es)")
ref = [inter(e - mu_mb, p - mu_mb) for e, p in zip(en_mb, es_mb)]
n_ref = sum(map(len, ref))
for name, W in (("procrustes", W_proc), ("ridge", W_ridge)):
    got = [inter(mapped(e, W), p - mu_mb) for e, p in zip(en_mac, es_mb)]
    both = sum(len(r & g) for r, g in zip(ref, got))
    n_got = sum(map(len, got))
    prec, rec = both / max(n_got, 1), both / max(n_ref, 1)
    say(f"  MacBERTh->{name:10s} links {n_got:6d} (ref {n_ref}); agreement P {100 * prec:5.1f}% "
        f"R {100 * rec:5.1f}% F {200 * prec * rec / max(prec + rec, 1e-9):5.1f}")

open(REPORT, "w", encoding="utf-8").write("\n".join(out_lines) + "\n")
say(f"\nmaps: {MAPS}\nreport: {REPORT}")
