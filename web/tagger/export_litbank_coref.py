# SPDX-License-Identifier: GPL-3.0-or-later
"""Export the LitBank coreference model to ONNX for the browser translator's LitBank mode.

Model: compnet-renard/bert-base-cased-literary-coref-v2 (weights MIT; trained on LitBank,
CC BY 4.0), loaded with Tibert (GPL-3.0; installed only in the local venv
/media/paleos/Warehouse2/Language/Claude/browser_coref/venv, never copied into the repo).
Pretrained only, no training. Writes to OUT_DIR:

    coref.bert.onnx.NNN   bert-base-cased, one segment of <= 128 wordpieces -> last hidden
                          states (int8; in parts of <= 45 MB: GitHub Pages refuses files > 100 MB)
    coref.heads.onnx      word vectors [w, 768] -> the 6 per-word projections [w, 6 * 3000]:
                          mention scorer start/end, pair scorer mention start/end, antecedent
                          start/end (web/src/coref.mjs explains the factorisation)
    coref.consts.f32      biases, output vectors, distance-bucket projections (10 x 3000)
    coref.vocab.txt       wordpieces
    coref.json            manifest: parts with size + sha256, constants layout, config
    coref.fixture.jsonl   per input document: Tibert's chains and the exported pipeline's chains
                          (web/test/coref_check.mjs checks the JS port against the latter)

Checked on every run, on the documents of web/test/coref_inputs.mjs (the browser's words and
windows: eng dev sentences, Time Machine chapters with windows + hierarchical merging):
  - wordpieces: the JS tokenizer's ids == the HF fast tokenizer's;
  - Tibert (its own predict_coref path, HM merge) vs this factorised pipeline on the same torch
    weights: the arithmetic is the same, except that Tibert also scores invalid padding
    antecedents (pruned spans, spans after the mention). How often Tibert picks one is counted;
  - onnxruntime fp32 vs torch; int8 variants (dynamic MatMulInteger, weight-only + Dequantize)
    vs fp32: chains changed, size, time per segment. The variant used is the dynamic one when it
    changes no more chains than weight-only, else weight-only.

    node web/test/coref_inputs.mjs WORK/inputs.jsonl
    python3 web/test/capped.py VENV/bin/python web/tagger/export_litbank_coref.py WORK/inputs.jsonl [OUT_DIR]
"""
import hashlib
import json
import os
import sys
import time

BASE = "/media/paleos/Warehouse2/Language/Claude/browser_coref"
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_HOME", os.path.join(BASE, "hf"))
import numpy as np  # noqa: E402
import onnx  # noqa: E402
import onnxruntime as ort  # noqa: E402
import torch  # noqa: E402
from onnx import helper, numpy_helper, TensorProto  # noqa: E402
from onnxruntime.quantization import QuantType, quantize_dynamic  # noqa: E402
from tibert.bertcoref import BertForCoreferenceResolution  # noqa: E402
from tibert.predict import _stream_predict_coref_raw, merge_coref_outputs  # noqa: E402
from tibert.utils import spans_indexs  # noqa: E402
from transformers import BertTokenizerFast  # noqa: E402

SNAP = os.path.join(BASE, "hf/hub/models--compnet-renard--bert-base-cased-literary-coref-v2/snapshots/"
                    "d6f6693711f680099a59d9246bc8282dc9cc4af3")
INPUTS = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(BASE, "export")
CHECK_DOCS = int(os.environ.get("CHECK_DOCS", "100000"))
PART = 45 * 1024 * 1024
# Tibert's own path holds m x 350 x 3092 floats and p x p span matrices per window: a 450-word
# window passed 12 GB (killed by the cap 2026-11-27). Longer windows: no Tibert reference.
TIBERT_MAX_WORDS = int(os.environ.get("TIBERT_MAX_WORDS", "250"))
QUANT_MIN = 1024

torch.set_grad_enabled(False)
model = BertForCoreferenceResolution.from_pretrained(SNAP).eval()
tok = BertTokenizerFast.from_pretrained(SNAP)
cfg = model.config
H, HID, L = cfg.hidden_size, cfg.mention_scorer_hidden_size, cfg.max_span_size
BUCKETS = list(BertForCoreferenceResolution.DIST_BUCKETS)
CLS, SEP, SEG = tok.cls_token_id, tok.sep_token_id, cfg.segment_size

# ── the factorised heads ──────────────────────────────────────────────────
Wm = model.mention_scorer_hidden.weight.numpy()                  # [3000, 1536]
Wp = model.mention_compatibility_scorer_hidden.weight.numpy()    # [3000, 3092]
WCAT = np.ascontiguousarray(np.concatenate(
    [Wm[:, :H], Wm[:, H:2 * H], Wp[:, :H], Wp[:, H:2 * H], Wp[:, 2 * H:3 * H], Wp[:, 3 * H:4 * H]], 0).T)
CONSTS = {
    "mention_b": model.mention_scorer_hidden.bias.numpy(),
    "mention_v": model.mention_scorer.weight.numpy()[0],
    "mention_c": model.mention_scorer.bias.numpy(),
    "pair_b": model.mention_compatibility_scorer_hidden.bias.numpy(),
    "pair_v": model.mention_compatibility_scorer.weight.numpy()[0],
    "pair_c": model.mention_compatibility_scorer.bias.numpy(),
    "dist": (model.dist_bucket_embedding.weight.numpy() @ Wp[:, 4 * H:].T).reshape(-1),
}
K = {k: v.astype(np.float32) for k, v in CONSTS.items()}
DIST = K["dist"].reshape(len(BUCKETS) + 1, HID)


def bucket(d):
    if d <= 0:
        return len(BUCKETS)
    return next((i for i, b in enumerate(BUCKETS) if d <= b), len(BUCKETS))


def relu_dot(x, v, c):
    np.maximum(x, 0, out=x)
    return x @ v + c[0]


# ── this pipeline (the same steps as web/src/coref.mjs) ──────────────────
def encode(pieces, enc_seg, heads):
    ids, wid = [CLS], [-1]
    for w, p in enumerate(pieces):
        ids += p
        wid += [w] * len(p)
    ids.append(SEP)
    wid.append(-1)
    W = len(pieces)
    vec, count = np.zeros((W, H), np.float32), np.zeros(W, np.float32)
    wid = np.array(wid)
    for s0 in range(0, len(ids), SEG):
        hs = enc_seg(np.array([ids[s0:s0 + SEG]], np.int64))
        w = wid[s0:s0 + SEG]
        keep = w >= 0
        np.add.at(vec, w[keep], hs[keep])
        np.add.at(count, w[keep], 1)
    vec /= np.maximum(count, 1)[:, None]
    return heads(vec)


def window(pieces, offset, enc_seg, heads):
    W = len(pieces)
    if not W:
        return []
    proj = encode(pieces, enc_seg, heads)
    spans = spans_indexs(list(range(W)), L)
    S = np.array([s for s, _ in spans])
    E = np.array([e for _, e in spans])
    ms = np.empty(len(spans), np.float32)
    for c0 in range(0, len(spans), 2048):
        s, e = S[c0:c0 + 2048], E[c0:c0 + 2048]
        x = proj[s, :HID] + proj[e - 1, HID:2 * HID] + K["mention_b"]
        ms[c0:c0 + 2048] = relu_dot(x, K["mention_v"], K["mention_c"])
    want = max(min(1, W), int(cfg.mentions_per_tokens * W))
    order = sorted(range(len(spans)), key=lambda p: (-ms[p], p))
    top = []
    for p in order:
        if len(top) >= want:
            break
        s1, e1 = spans[p]
        if not any((s1 < s2 < e1 < e2) or (s2 < s1 < e2 < e1) for s2, e2 in (spans[q] for q in top)):
            top.append(p)
    # antecedent candidates. Tibert takes the 350 (or all, if fewer) closest spans by topk over
    # distances where pruned spans and spans not before the mention are +Inf, so the list is
    # padded with such spans in torch's arbitrary tie order, and they are scored like the rest.
    # With <= 350 spans the list is every span: reproduced exactly (padding spans: distance
    # bucket "not before"). With more, the padding is an arbitrary few of thousands of spans:
    # only the real candidates are scored, the closest deterministic match.
    A = cfg.antecedents_nb
    every = len(spans) <= A
    Pv = lambda q: proj[S[q], 2 * HID:3 * HID] + proj[E[q] - 1, 3 * HID:4 * HID]   # noqa: E731
    Qv = lambda q: proj[S[q], 4 * HID:5 * HID] + proj[E[q] - 1, 5 * HID:6 * HID]   # noqa: E731
    Qall = Qv(np.arange(len(spans))) if every else None
    T = np.array(top)
    Qtop = None if every else Qv(T)
    best = [-1] * len(top)
    for i, p in enumerate(top):
        si = S[p]
        if every:
            qs = np.arange(len(spans))
            dist = si - E + 1
            Q = Qall
        else:
            cands = sorted((si - E[q] + 1, q, j) for j, q in enumerate(top) if E[q] <= si)[:A]
            if not cands:
                continue
            qs = np.array([q for _, q, _ in cands])
            dist = np.array([d for d, _, _ in cands])
            Q = Qtop[[j for _, _, j in cands]]
        x = Pv(p) + Q + DIST[[bucket(d) for d in dist]] + K["pair_b"]
        sc = relu_dot(x, K["pair_v"], K["pair_c"]) + ms[p] + ms[qs]
        k = int(np.argmax(sc))
        if sc[k] > 0:
            best[i] = int(qs[k])
    nodes, index, adj = [], {}, []

    def node(p):
        if p not in index:
            index[p] = len(nodes)
            nodes.append(p)
            adj.append([])
        return index[p]
    for i, p in enumerate(top):
        if best[i] < 0:
            if ms[p] > 0:
                node(p)
            continue
        a, b = node(best[i]), node(p)
        adj[a].append(b)
        adj[b].append(a)
    seen, chains = set(), []
    for n0 in range(len(nodes)):
        if n0 in seen:
            continue
        comp, stack = [], [n0]
        seen.add(n0)
        while stack:
            n = stack.pop()
            comp.append(n)
            for x in adj[n]:
                if x not in seen:
                    seen.add(x)
                    stack.append(x)
        qs = np.array([nodes[n] for n in comp])
        chains.append({"mentions": [(int(S[q]) + offset, int(E[q]) + offset, float(ms[q])) for q in qs],
                       "P": Pv(qs).sum(0), "Q": Qv(qs).sum(0)})
    return chains


def merge(docs):
    if len(docs) <= 1:
        return docs[0] if docs else []
    mid = len(docs) // 2
    left, right = merge(docs[:mid]), merge(docs[mid:])
    if not left or not right:
        return left + right
    score = np.empty((len(right), len(left)), np.float32)
    for ri, r in enumerate(right):
        r_start = min(m[0] for m in r["mentions"])
        r_ms = np.mean([m[2] for m in r["mentions"]])
        for li, lc in enumerate(left):
            l_end = max(m[1] for m in lc["mentions"])
            x = (r["P"] / len(r["mentions"]) + lc["Q"] / len(lc["mentions"]) + DIST[bucket(r_start - l_end + 1)]
                 + K["pair_b"])
            score[ri, li] = relu_dot(x, K["pair_v"], K["pair_c"]) + r_ms + np.mean([m[2] for m in lc["mentions"]])
    taken, out = set(), []
    for li, lc in enumerate(left):
        cand = [(score[ri, li], -ri) for ri in range(len(right)) if ri not in taken]
        if not cand or max(cand)[0] < 0:
            out.append(lc)
            continue
        ri = -max(cand)[1]
        taken.add(ri)
        r = right[ri]
        out.append({"mentions": lc["mentions"] + r["mentions"], "P": lc["P"] + r["P"], "Q": lc["Q"] + r["Q"]})
    return out + [r for ri, r in enumerate(right) if ri not in taken]


def canon(chains):
    return sorted(sorted([s, e] for s, e in c) for c in chains)


def resolve(d, enc_seg, heads):
    docs = [window(d["pieces"][s:e], s, enc_seg, heads) for s, e in d["windows"]]
    return canon([[(m[0], m[1]) for m in c["mentions"]] for c in merge(docs)])


# ── Tibert's own path ─────────────────────────────────────────────────────
def tibert(d):
    wins = [d["words"][s:e] for s, e in d["windows"]]
    if max(map(len, wins), default=0) > TIBERT_MAX_WORDS:
        return None, 0
    outs, hidden, fillers = [], [], 0
    for words, (od, out) in zip(wins, _stream_predict_coref_raw(wins, model, tok, quiet=True, device_str="cpu",
                                                                return_hidden_state=True)):
        outs += od
        hidden += list(out.hidden_states)
        top = out.top_mentions_index[0].tolist()
        topset = set(top)
        a = out.logits.shape[2] - 1
        sp = spans_indexs(list(range(len(words))), L)
        for j, k in enumerate(out.logits[0].argmax(1).tolist()):
            if k == a:
                continue
            ant = int(out.top_antecedents_index[0, j, k])
            if ant not in topset or sp[ant][1] > sp[top[j]][0]:
                fillers += 1
    merged = merge_coref_outputs(outs, hidden, model, "cpu")
    return canon([[(m.start_idx, m.end_idx) for m in c] for c in merged.coref_chains]), fillers


def compare(a, b):
    """documents whose chains differ, and mentions in chains of one but not the other
    (documents without a reference, None, are left out)"""
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    a, b = [x for x, _ in pairs], [y for _, y in pairs]
    docs = sum(1 for x, y in zip(a, b) if x != y)
    ma = [{(tuple(m), tuple(map(tuple, c))) for c in x for m in c} for x in a]
    mb = [{(tuple(m), tuple(map(tuple, c))) for c in y for m in c} for y in b]
    return docs, sum(len(x ^ y) for x, y in zip(ma, mb))


# ── ONNX export ───────────────────────────────────────────────────────────
class Bert(torch.nn.Module):
    def __init__(self, bert):
        super().__init__()
        self.bert = bert

    def forward(self, input_ids):
        # BertModel.forward without its mask builder (it does not trace): no padding, so the
        # mask is all ones and attention_mask=None is the same computation
        emb = self.bert.embeddings(input_ids=input_ids)
        return self.bert.encoder(emb, attention_mask=None).last_hidden_state


def quantize_weights(src, dst):
    """Weight-only int8 + DequantizeLinear (as export_stanza_depparse.py): one scale per row."""
    g = onnx.load(src)
    graph = g.graph
    new_inits, nodes = [], []
    for init in graph.initializer:
        a = numpy_helper.to_array(init)
        if a.dtype != np.float32 or a.size < QUANT_MIN or a.ndim < 2:
            new_inits.append(init)
            continue
        ax = a.ndim - 2
        other = tuple(d for d in range(a.ndim) if d != ax)
        sc = (np.maximum(np.abs(a).max(other), 1e-12) / 127.0).astype(np.float32)
        shape = [1] * a.ndim
        shape[ax] = -1
        q = np.round(a / sc.reshape(shape)).astype(np.int8)
        name = init.name
        new_inits += [numpy_helper.from_array(q, name + "_q"), numpy_helper.from_array(sc, name + "_s"),
                      numpy_helper.from_array(np.zeros(sc.shape, np.int8), name + "_z")]
        nodes.append(helper.make_node("DequantizeLinear", [name + "_q", name + "_s", name + "_z"], [name], axis=ax))
    del graph.initializer[:]
    graph.initializer.extend(new_inits)
    old = list(graph.node)
    del graph.node[:]
    graph.node.extend(nodes + old)
    onnx.save(g, dst)


def sessions(bert_path, heads_path):
    opt = ort.SessionOptions()
    opt.intra_op_num_threads = 1                 # as in the page (no cross-origin isolation)
    b = ort.InferenceSession(bert_path, opt)
    h = ort.InferenceSession(heads_path, opt)
    return (lambda ids: b.run(None, {"input_ids": ids})[0][0]), (lambda v: h.run(None, {"words": v})[0])


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main():
    os.makedirs(OUT, exist_ok=True)
    tmp = os.path.join(OUT, "tmp")
    os.makedirs(tmp, exist_ok=True)
    docs = [json.loads(line) for line in open(INPUTS, encoding="utf-8")][:CHECK_DOCS]
    print(len(docs), "documents,", sum(len(d["words"]) for d in docs), "words", flush=True)

    bad = total = 0
    for d in docs:
        enc = tok(d["words"], is_split_into_words=True, add_special_tokens=False)
        per = [[] for _ in d["words"]]
        for i, w in zip(enc["input_ids"], enc.word_ids()):
            per[w].append(i)
        for w, (a, b) in enumerate(zip(per, d["pieces"])):
            total += 1
            if (a or [tok.unk_token_id]) != b:
                bad += 1
                if bad <= 10:
                    print("  wordpiece differs:", repr(d["words"][w]), a, b)
    print(f"wordpieces: {bad} of {total} words differ from the HF tokenizer", flush=True)

    t0 = time.time()
    ref, fillers = zip(*(tibert(d) for d in docs))
    print(f"Tibert: {sum(r is None for r in ref)} documents skipped (window > {TIBERT_MAX_WORDS} words), "
          f"{sum(len(r) for r in ref if r)} chains, {sum(fillers)} mentions took a padding antecedent "
          f"({time.time() - t0:.0f} s)", flush=True)

    def torch_seg(ids):
        return model.bert(input_ids=torch.from_numpy(ids), attention_mask=torch.ones(ids.shape, dtype=torch.long)
                          ).last_hidden_state[0].numpy()
    own = [resolve(d, torch_seg, lambda v: v @ WCAT) for d in docs]
    print("factorised (torch) vs Tibert: %d documents differ, %d mentions" % compare(own, ref), flush=True)
    for d, a, b in zip(docs, own, ref):
        if b is not None and a != b:
            print("  e.g.", d["id"], "ours-only", [c for c in a if c not in b][:2], "tibert-only",
                  [c for c in b if c not in a][:2])
            break

    # export fp32
    bert32, heads32 = os.path.join(tmp, "bert.fp32.onnx"), os.path.join(tmp, "heads.fp32.onnx")
    ids = torch.tensor([[CLS] + [1000] * 20 + [SEP]])
    model.bert.set_attn_implementation("eager")      # SDPA mask code does not trace
    torch.onnx.export(Bert(model.bert).eval(), (ids,), bert32, input_names=["input_ids"], output_names=["hidden"],
                      dynamic_axes={"input_ids": {1: "S"}, "hidden": {1: "S"}}, opset_version=17, dynamo=False)
    w_in = helper.make_tensor_value_info("words", TensorProto.FLOAT, ["W", H])
    w_out = helper.make_tensor_value_info("proj", TensorProto.FLOAT, ["W", 6 * HID])
    g = helper.make_graph([helper.make_node("MatMul", ["words", "wcat"], ["proj"])], "heads", [w_in], [w_out],
                          [numpy_helper.from_array(WCAT.astype(np.float32), "wcat")])
    onnx.save(helper.make_model(g, opset_imports=[helper.make_opsetid("", 17)], ir_version=8), heads32)

    variants = {"fp32": (bert32, heads32)}
    for name in ("dynamic", "weights"):
        bq, hq = os.path.join(tmp, f"bert.{name}.onnx"), os.path.join(tmp, f"heads.{name}.onnx")
        if name == "dynamic":
            quantize_dynamic(bert32, bq, weight_type=QuantType.QInt8, per_channel=True)
            quantize_dynamic(heads32, hq, weight_type=QuantType.QInt8, per_channel=True)
        else:
            quantize_weights(bert32, bq)
            quantize_weights(heads32, hq)
        variants[name] = (bq, hq)
    results = {}
    for name, (bp, hp) in variants.items():
        seg, heads = sessions(bp, hp)
        x = np.array([[CLS] + [1000] * 126 + [SEP]], np.int64)
        seg(x)
        t0 = time.time()
        for _ in range(5):
            seg(x)
        ms = (time.time() - t0) / 5 * 1000
        out = [resolve(d, seg, heads) for d in docs]
        size = os.path.getsize(bp) + os.path.getsize(hp)
        base = own if name == "fp32" else results["fp32"][0]
        print(f"{name}: {size / 1e6:.0f} MB, {ms:.0f} ms per 128-piece segment (1 thread); vs "
              f"{'torch' if name == 'fp32' else 'fp32'}: %d documents differ, %d mentions; vs Tibert: %d / %d"
              % (compare(out, base) + compare(out, ref)), flush=True)
        results[name] = (out, size, ms)

    dyn, wts = (compare(results[n][0], results["fp32"][0])[1] for n in ("dynamic", "weights"))
    pick = "dynamic" if dyn <= wts else "weights"
    print("using", pick, flush=True)
    bp, hp = variants[pick]

    parts = []
    with open(bp, "rb") as f:
        for k in range(10 ** 3):
            chunk = f.read(PART)
            if not chunk:
                break
            name = f"coref.bert.onnx.{k:03d}"
            with open(os.path.join(OUT, name), "wb") as g:
                g.write(chunk)
            parts.append({"name": name, "size": len(chunk), "sha256": hashlib.sha256(chunk).hexdigest()})
    heads_name = "coref.heads.onnx"
    os.replace(hp, os.path.join(OUT, heads_name))
    layout, off, flat = {}, 0, []
    for k, v in K.items():
        layout[k] = [off, int(v.size)]
        off += int(v.size)
        flat.append(v.reshape(-1))
    np.concatenate(flat).astype("<f4").tofile(os.path.join(OUT, "coref.consts.f32"))
    vocab = "".join(t + "\n" for t in tok.convert_ids_to_tokens(list(range(len(tok)))))
    with open(os.path.join(OUT, "coref.vocab.txt"), "w", encoding="utf-8") as f:
        f.write(vocab)
    manifest = {
        "model": "compnet-renard/bert-base-cased-literary-coref-v2 (MIT; LitBank, CC BY 4.0); inference after Tibert (GPL-3.0)",
        "quantization": pick,
        "models": {"bert": parts, "heads": [{"name": heads_name, "size": os.path.getsize(os.path.join(OUT, heads_name)),
                                             "sha256": sha(os.path.join(OUT, heads_name))}]},
        "consts": {"name": "coref.consts.f32", "layout": layout},
        "vocab": "coref.vocab.txt",
        "config": {"hidden_size": H, "mention_scorer_hidden_size": HID, "max_span_size": L, "segment_size": SEG,
                   "mentions_per_tokens": cfg.mentions_per_tokens, "antecedents_nb": cfg.antecedents_nb,
                   "dist_buckets": BUCKETS},
    }
    with open(os.path.join(OUT, "coref.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    with open(os.path.join(OUT, "coref.fixture.jsonl"), "w", encoding="utf-8") as f:
        for d, ours, theirs in zip(docs, results[pick][0], ref):
            f.write(json.dumps({"id": d["id"], "chains": ours, "tibert": theirs}) + "\n")
    for p in os.listdir(tmp):
        os.remove(os.path.join(tmp, p))
    os.rmdir(tmp)
    print("wrote", OUT, f"({sum(p['size'] for p in parts) / 1e6:.0f} MB bert in {len(parts)} parts)")


main()
