"""Export stanza's small English dependency parser to ONNX for the browser translator.

The desktop eng->glb pipeline parses with stanza combined_electra-large (eng-nlp-service.py).
In the browser the parser runs in its non-transformer form, combined_nocharlm (UD EWT + GUM
and friends, CC BY-SA / CC BY), on the browser tagger's tags (export_stanza_pos.py):

    parser.char.onnx   one word's characters -> its character representation
    parser.sent.onnx   ROOT + words: word, lemma, UPOS, Penn ids, pretrained vectors, character
                       reps -> arc log-probabilities [T+1, T+1] (row = dependent, column = head)
                       and the best relation id per pair [T+1, T+1]
    parser.vocab.json  word / lemma / char / tag / relation vocabularies
    lemma.dict.json    stanza's combined_nocharlm lemma dictionary, pruned to the entries that
                       change the parser's input (below)

The networks are stanza's trained modules, called for one sentence without packed sequences.
Stanza quirk kept: the parser's input concatenates the tag embedding twice and never uses the
feats embedding (depparse/model.py embed()), so feats are not an input here.
Tree decoding (Chu-Liu-Edmonds, one root) is not in the graph: web/src/mst.mjs, a port of
rust/globasa_fast/src/mst.rs.

Lemmas: stanza lemmatises with a dictionary (word+UPOS, then word) and a seq2seq model for
words in neither. The browser uses the dictionary only, with the word itself as fallback. The
parser sees a lemma only through its own lemma vocabulary (lowercased, else UNK), so an entry
is kept only when its lemma's id differs from the id the word itself would get: the pruned
dictionary gives the parser exactly the input the full dictionary gives.

Checked on every run (UD EWT test, gold tokens, the browser tagger's tags):
  - the wrapper reproduces stanza's heads and relations (stanza batches sentences, the wrapper
    takes one at a time: float rounding may flip a near-tie, at most 0.05% of words);
  - onnxruntime reproduces the wrapper's trees;
  - UAS / LAS against gold for stanza, for the browser setting (dictionary lemmas, top-N int8
    vectors) and for lemma = word, so the cost of each shortcut is visible.
Pretrained models only, no training.

    venv/bin/python web/tagger/export_stanza_depparse.py [OUT_DIR]
    (run through web/test/capped.py; needs stanza, torch, onnx, onnxruntime)
"""
import json
import os
import sys

os.environ.setdefault("HF_HUB_OFFLINE", "1")
import numpy as np  # noqa: E402
import onnx  # noqa: E402
import onnxruntime as ort  # noqa: E402
import stanza  # noqa: E402
import torch  # noqa: E402
import torch.nn.functional as F  # noqa: E402
from onnx import helper, numpy_helper  # noqa: E402
from stanza.models.common.chuliu_edmonds import chuliu_edmonds_one_root  # noqa: E402
from stanza.models.common.vocab import ROOT_ID, VOCAB_PREFIX_SIZE  # noqa: E402
from stanza.models.lemma.trainer import _POS_INDEPENDENT  # noqa: E402

WORK = os.environ.get("TAGGER_WORK", "/media/paleos/Warehouse2/Language/Claude/browser_tagger")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORK, "export_parser")
HF = os.path.expanduser("~/.cache/huggingface/hub/models--stanfordnlp--stanza-en/snapshots/"
                        "03960e981a2e7e86151a898a8e675d2026cecc73/models")
PRETRAIN_TOP = int(os.environ.get("PRETRAIN_TOP", "100000"))   # as the tagger's export
CHECK_SENTS = int(os.environ.get("CHECK_SENTS", "2077"))       # all of UD EWT test
ONNX_SENTS = int(os.environ.get("ONNX_SENTS", "300"))
DUMP_SENTS = int(os.environ.get("DUMP_SENTS", "200"))           # score matrices for mst_check.mjs
MAX_DIFF_RATE = 0.0005
QUANT_MIN = 100_000            # float initializers at least this large are stored as int8


def model(kind):
    return os.path.join(WORK, "models", kind, "combined_nocharlm.pt")


def load():
    pre = os.path.join(HF, "pretrain", "conll17.pt")
    nlp = stanza.Pipeline(lang="en", processors="tokenize,pos,lemma,depparse", tokenize_pretokenized=True,
                          use_gpu=False, download_method=None, logging_level="WARN",
                          pos_model_path=os.path.join(WORK, "models", "pos", "combined_nocharlm.pt"),
                          pos_pretrain_path=pre, pos_forward_charlm_path=None, pos_backward_charlm_path=None,
                          lemma_model_path=model("lemma"), lemma_forward_charlm_path=None,
                          lemma_backward_charlm_path=None,
                          depparse_model_path=model("depparse"), depparse_pretrain_path=pre,
                          depparse_forward_charlm_path=None, depparse_backward_charlm_path=None)
    proc = nlp.processors["depparse"]
    trainer = proc.trainer if hasattr(proc, "trainer") else proc._trainer
    m = trainer.model.eval()
    assert not m.args.get("charlm") and not m.args.get("use_arc_embedding") and m.args["linearization"] \
        and m.args["distance"] and isinstance(m.xpos_emb, torch.nn.Embedding) and m.charmodel.attn
    lp = nlp.processors["lemma"]
    lemma_trainer = lp.trainer if hasattr(lp, "trainer") else lp._trainer
    return nlp, trainer, m, lemma_trainer


class CharNet(torch.nn.Module):
    """One word: char ids [1, L] -> transformed character representation [1, D]
    (the same character model as the tagger's; see export_stanza_pos.py)."""

    def __init__(self, m):
        super().__init__()
        self.m = m

    def forward(self, chars):
        cm = self.m.charmodel
        embs = cm.char_emb(chars)
        n = cm.num_dir * cm.args["char_num_layers"]
        h0 = cm.charlstm_h_init.expand(n, 1, cm.args["char_hidden_dim"]).contiguous()
        c0 = cm.charlstm_c_init.expand(n, 1, cm.args["char_hidden_dim"]).contiguous()
        out, _ = cm.charlstm.lstm(embs, (h0, c0))
        rep = (out * torch.sigmoid(cm.char_attn(out))).sum(1)
        return self.m.trans_char(rep)


def pairwise(deep, x):
    """stanza's DeepBiaffineScorer(x, x), pairwise, as matrix products (no einsum):
    out[i, j, k] = [h1_i; 1] . W[:, :, k] . [h2_j; 1] + b[k]."""
    h1, h2 = F.relu(deep.W1(x)), F.relu(deep.W2(x))
    h1 = torch.cat([h1, torch.ones_like(h1[:, :1])], 1)
    h2 = torch.cat([h2, torch.ones_like(h2[:, :1])], 1)
    w, b = deep.scorer.W_bilin.weight, deep.scorer.W_bilin.bias       # [I, J, K], [K]
    i, j, k = w.shape
    z = torch.matmul(h1, w.reshape(i, j * k)).reshape(-1, j, k)       # [T, J, K]
    out = torch.matmul(z.permute(0, 2, 1), h2.t())                    # [T, K, T]
    return out.permute(0, 2, 1) + b                                   # [T, T, K]


class ParseNet(torch.nn.Module):
    """ROOT + words [1, T]: word, lemma, upos, xpos ids, pretrained vectors [1, T, 100], char
    reps [1, T, D] -> arc log-probabilities [T, T], best relation id (vocab id) [T, T]."""

    def __init__(self, m):
        super().__init__()
        self.m = m

    def forward(self, word, lemma, upos, xpos, pre, chars):
        m = self.m
        pos = m.upos_emb(upos) + m.xpos_emb(xpos)
        x = torch.cat([m.trans_pretrained(pre), m.word_emb(word), m.lemma_emb(lemma), pos, pos,
                       chars], 2)
        hl = m.parserlstm
        nl, hd = m.args["num_layers"], m.args["hidden_dim"]
        h0 = m.parserlstm_h_init.expand(2 * nl, 1, hd).contiguous()
        c0 = m.parserlstm_c_init.expand(2 * nl, 1, hd).contiguous()
        for layer in range(nl):
            hx = (h0[2 * layer:2 * layer + 2], c0[2 * layer:2 * layer + 2])
            h, _ = hl.lstm[layer].lstm(x, hx)
            x = h + torch.sigmoid(hl.gate[layer](x)) * hl.highway_func(hl.highway[layer](x))
        out = x[0]                                                       # [T, 2H]
        unlabeled = pairwise(m.unlabeled, out)[:, :, 0]
        deprel = pairwise(m.deprel, out)
        t = torch.arange(out.shape[0])
        offset = (t[None, :] - t[:, None]).float()                       # head - dependent
        unlabeled = unlabeled + F.logsigmoid(pairwise(m.linearization, out)[:, :, 0] * torch.sign(offset))
        dist_pred = 1 + F.softplus(pairwise(m.distance, out)[:, :, 0])
        unlabeled = unlabeled - torch.log((offset.abs() - dist_pred) ** 2 / 2 + 1)
        unlabeled = unlabeled.masked_fill(t[:, None] == t[None, :], -float("inf"))
        return F.log_softmax(unlabeled, 1), deprel.argmax(2) + VOCAB_PREFIX_SIZE


def read_conllu(path, limit):
    """(form, upos, xpos, lemma, head, deprel) per word, multiword tokens and empty nodes skipped."""
    sents, cur = [], []
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line:
            if cur:
                sents.append(cur)
                if len(sents) >= limit:
                    break
            cur = []
        elif not line.startswith("#"):
            c = line.split("\t")
            if "-" not in c[0] and "." not in c[0]:
                cur.append((c[1], c[3], c[4], c[2], int(c[6]), c[7]))
    return sents


def dict_lemma(pos_dict, word, upos):
    """The browser's lemmatiser: stanza's dictionary lookup, the word itself as fallback."""
    hit = pos_dict.get(upos, {}).get(word)
    if hit is None:
        hit = pos_dict.get(_POS_INDEPENDENT, {}).get(word)
    return word if hit is None else hit


def main():
    os.makedirs(OUT, exist_ok=True)
    sents = read_conllu(os.path.join(WORK, "ud", "en_ewt-ud-test.conllu"), CHECK_SENTS)
    nlp, trainer, m, lemma_trainer = load()
    v = trainer.vocab
    char_net, parse_net = CharNet(m).eval(), ParseNet(m).eval()
    assert not lemma_trainer.caseless

    # pretrained vectors: full float rows (stanza's) and the browser's top-N int8 rows
    pt = torch.load(os.path.join(HF, "pretrain", "conll17.pt"), map_location="cpu", weights_only=False)
    emb = pt["emb"].numpy() if hasattr(pt["emb"], "numpy") else np.asarray(pt["emb"])
    full_index = {w: i for i, w in enumerate(pt["vocab"]["_id2unit"])}
    keep = min(len(full_index), 4 + PRETRAIN_TOP)
    sub = emb[:keep].astype(np.float32)
    scale = np.maximum(np.abs(sub).max(1), 1e-8) / 127.0
    deq = np.round(sub / scale[:, None]).astype(np.int8).astype(np.float32) * scale[:, None]

    def vec(w, small):
        i = full_index.get(w.lower().replace(" ", "\xa0"), 1)
        return deq[i if i < keep else 1] if small else emb[i].astype(np.float32)

    root_vec = emb[ROOT_ID].astype(np.float32)

    def inputs(words, upos, xpos, lemmas, small):
        def ids(vocab, xs):
            return torch.tensor([[ROOT_ID] + vocab.map(xs)])
        pre = np.stack([deq[ROOT_ID] if small else root_vec] + [vec(w, small) for w in words])
        chars = [torch.tensor([[ROOT_ID]])] + [torch.tensor([v["char"].map(list(w))]) for w in words]
        return (ids(v["word"], words), ids(v["lemma"], lemmas), ids(v["upos"], upos), ids(v["xpos"], xpos),
                torch.from_numpy(pre)[None], chars)

    def parse(words, upos, xpos, lemmas, small):
        word, lemma, up, xp, pre, chars = inputs(words, upos, xpos, lemmas, small)
        creps = torch.cat([char_net(c) for c in chars])[None]
        arcs, rels = parse_net(word, lemma, up, xp, pre, creps)
        return arcs.numpy().astype(np.float64), rels.numpy()

    def decode(arcs, rels):
        heads = list(chuliu_edmonds_one_root(arcs))[1:]
        return [(h, v["deprel"].unmap([int(rels[j + 1][h])])[0]) for j, h in enumerate(heads)]

    # lemma dictionary, pruned to the entries that change the parser's lemma id
    pos_dict = lemma_trainer.pos_dict
    lv = v["lemma"]
    # (a UPOS entry is compared with what the lookup falls back to without it: the '*' entry or the word)
    star = pos_dict.get(_POS_INDEPENDENT, {})
    pruned = {}
    for p, entries in pos_dict.items():
        kept = {w: lem for w, lem in entries.items()
                if lv.map([lem])[0] != lv.map([w if p == _POS_INDEPENDENT else star.get(w, w)])[0]}
        if kept:
            pruned[p] = kept

    scores = {k: [0, 0] for k in ("stanza", "wrapper", "browser", "lemma=word", "gold tags+lemmas")}
    mismatch = total = 0
    dumps = []
    with torch.no_grad():
        doc = nlp([[w[0] for w in s] for s in sents])
        for si, (s, ds) in enumerate(zip(sents, doc.sentences)):
            words = [w[0] for w in s]
            gold = [(w[4], w[5]) for w in s]
            up = [w.upos for w in ds.words]
            xp = [w.xpos for w in ds.words]
            theirs = [(w.head, w.deprel) for w in ds.words]
            arcs, rels = parse(words, up, xp, [w.lemma for w in ds.words], small=False)
            ours = decode(arcs, rels)
            mismatch += sum(a != b for a, b in zip(ours, theirs))
            total += len(words)
            lem_d = [dict_lemma(pos_dict, w, u) for w, u in zip(words, up)]
            lem_p = [dict_lemma(pruned, w, u) for w, u in zip(words, up)]
            assert lv.map(lem_d) == lv.map(lem_p)
            browser_arcs, browser_rels = parse(words, up, xp, lem_d, small=True)
            if si < DUMP_SENTS:
                dumps.append({"arcs": browser_arcs.tolist(),
                              "heads": [int(h) for h in chuliu_edmonds_one_root(browser_arcs)]})
            runs = {"stanza": theirs, "wrapper": ours, "browser": decode(browser_arcs, browser_rels),
                    "lemma=word": decode(*parse(words, up, xp, words, small=True)),
                    "gold tags+lemmas": decode(*parse(words, [w[1] for w in s], [w[2] for w in s],
                                                      [w[3] for w in s], small=False))}
            for k, pred in runs.items():
                scores[k][0] += sum(p[0] == g[0] for p, g in zip(pred, gold))
                scores[k][1] += sum(p == g for p, g in zip(pred, gold))
    print(f"wrapper vs stanza on {total} EWT words: {mismatch} differing (head, deprel)")
    for k, (u, l) in scores.items():
        print(f"  {k:18s} UAS {100 * u / total:.2f}  LAS {100 * l / total:.2f}")
    if mismatch > MAX_DIFF_RATE * total:
        sys.exit("the wrapper does not reproduce stanza")

    # ONNX export (classic exporter; dynamic word length / sentence length)
    cpath, spath = (os.path.join(OUT, f"parser.{p}.onnx") for p in ("char", "sent"))
    ex = ["The", "pairs", "are", "here", "."]
    word, lemma, up, xp, pre, chars = inputs(ex, ["DET", "NOUN", "AUX", "ADV", "PUNCT"],
                                             ["DT", "NNS", "VBP", "RB", "."], ["the", "pair", "be", "here", "."], True)
    creps = torch.cat([char_net(c) for c in chars])[None]
    torch.onnx.export(char_net, (chars[1],), cpath, input_names=["chars"], output_names=["rep"],
                      dynamic_axes={"chars": {1: "L"}}, opset_version=17, dynamo=False)
    torch.onnx.export(parse_net, (word, lemma, up, xp, pre, creps), spath,
                      input_names=["word", "lemma", "upos", "xpos", "pre", "chars"], output_names=["arcs", "rels"],
                      dynamic_axes={**{n: {1: "T"} for n in ("word", "lemma", "upos", "xpos", "pre", "chars")},
                                    "arcs": {0: "T", 1: "T"}, "rels": {0: "T", 1: "T"}},
                      opset_version=17, dynamo=False)
    fp32_size = os.path.getsize(cpath) + os.path.getsize(spath)
    for p in (cpath, spath):
        quantize_weights(p)

    cs, ss = ort.InferenceSession(cpath), ort.InferenceSession(spath)
    diff = words_n = 0
    with torch.no_grad():
        for s in sents[:ONNX_SENTS]:
            words = [w[0] for w in s]
            up, xp = [w[1] for w in s], [w[2] for w in s]
            lem = [dict_lemma(pos_dict, w, u) for w, u in zip(words, up)]
            ref = decode(*parse(words, up, xp, lem, small=True))
            word, lemma, upi, xpi, pre, chars = inputs(words, up, xp, lem, True)
            creps = np.concatenate([cs.run(None, {"chars": c.numpy()})[0] for c in chars])[None]
            arcs, rels = ss.run(None, {"word": word.numpy(), "lemma": lemma.numpy(), "upos": upi.numpy(),
                                       "xpos": xpi.numpy(), "pre": pre.numpy(), "chars": creps})
            got = decode(arcs.astype(np.float64), rels)
            diff += sum(a != b for a, b in zip(ref, got))
            words_n += len(words)
    print(f"onnxruntime (int8 weights) vs wrapper (float) on {ONNX_SENTS} sentences: "
          f"{diff} of {words_n} words differ")
    if diff > MAX_DIFF_RATE * 4 * words_n:
        sys.exit("ONNX export differs")

    meta = {"word": v["word"]._id2unit, "lemma": v["lemma"]._id2unit, "char": v["char"]._id2unit,
            "upos": v["upos"]._id2unit, "xpos": v["xpos"]._id2unit, "deprel": v["deprel"]._id2unit,
            "root": ROOT_ID, "unk": 1, "pretrain_rows": keep}
    with open(os.path.join(OUT, "parser.vocab.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)
    with open(os.path.join(OUT, "lemma.dict.json"), "w", encoding="utf-8") as f:
        json.dump({"any": _POS_INDEPENDENT, "dict": pruned}, f, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(OUT, "mst_cases.json"), "w", encoding="utf-8") as f:
        json.dump(dumps, f)
    print(f"  float32 ONNX would be {fp32_size / 1e6:.1f} MB")
    for f in sorted(os.listdir(OUT)):
        print(f"  {os.path.getsize(os.path.join(OUT, f)) / 1e6:7.1f} MB  {f}")


def quantize_weights(path):
    """Weight-only int8: every large float initializer becomes int8 + one float scale per slice of
    its second-to-last axis (a weight matrix's rows; for an LSTM's [dirs, 4H, in] the 4H gate
    rows), restored by DequantizeLinear: the computation stays float32, only the file shrinks."""
    g = onnx.load(path)
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
    onnx.save(g, path)


main()
