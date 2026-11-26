"""Export stanza's small English PoS taggers to ONNX for the browser translator.

The desktop eng->glb pipeline prunes Apertium's readings with two stanza taggers
(eng-nlp-service.py: combined + gum, electra-large) where both agree on the Penn tag.
In the browser the same pair runs in their non-transformer form (combined_nocharlm,
gum_nocharlm: UD EWT/GUM, CC BY-SA / CC BY; 96.0 / 93.0 Penn accuracy on EWT test):

    <name>.char.onnx   one word's characters -> its character representation
    <name>.sent.onnx   word ids + pretrained vectors + character reps -> UPOS, Penn, feats
    <name>.vocab.json  word / char / tag vocabularies and the feats columns
    pretrain.words.txt, pretrain.i8, pretrain.scale  the shared conll17 vectors, the most
                       frequent PRETRAIN_TOP words, int8 per row (+ a float32 scale per row)

The two networks are stanza's trained modules, called for one sentence without packed
sequences (for a batch of one, packing changes nothing; padded words would change the
backward character LSTM, so the character network runs per word). Checked on every run:
the wrapper must predict what stanza predicts, and onnxruntime exactly what the wrapper predicts, on UD EWT test sentences; the accuracy with the trimmed int8 vectors is
reported. (Stanza batches sentences, the wrapper takes one at a time; float rounding may
flip a near-tie: at most 0.05% of words may differ, 4 of 25,094 on EWT test.)
Pretrained models only, no training.

    venv/bin/python web/tagger/export_stanza_pos.py [OUT_DIR]
    (run through web/test/capped.py; needs stanza, torch, onnx, onnxruntime)
"""
import json
import os
import sys

os.environ.setdefault("HF_HUB_OFFLINE", "1")
import numpy as np  # noqa: E402
import onnxruntime as ort  # noqa: E402
import stanza  # noqa: E402
import torch  # noqa: E402
import torch.nn.functional as F  # noqa: E402

WORK = os.environ.get("TAGGER_WORK", "/media/paleos/Warehouse2/Language/Claude/browser_tagger")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORK, "export")
HF = os.path.expanduser("~/.cache/huggingface/hub/models--stanfordnlp--stanza-en/snapshots/"
                        "03960e981a2e7e86151a898a8e675d2026cecc73/models")
MODELS = ["combined_nocharlm", "gum_nocharlm"]
PRETRAIN_TOP = int(os.environ.get("PRETRAIN_TOP", "100000"))
CHECK_SENTS = int(os.environ.get("CHECK_SENTS", "2077"))     # all of UD EWT test
MAX_DIFF_RATE = 0.0005


def model_path(name):
    local = os.path.join(WORK, "models", "pos", name + ".pt")
    return local if os.path.exists(local) else os.path.join(HF, "pos", name + ".pt")


def load(name):
    nlp = stanza.Pipeline(lang="en", processors="tokenize,pos", tokenize_pretokenized=True, use_gpu=False,
                          download_method=None, logging_level="WARN", pos_model_path=model_path(name),
                          pos_pretrain_path=os.path.join(HF, "pretrain", "conll17.pt"),
                          pos_forward_charlm_path=None, pos_backward_charlm_path=None)
    proc = nlp.processors["pos"]
    trainer = proc.trainer if hasattr(proc, "trainer") else proc._trainer
    model = trainer.model.eval()
    assert model.charmodel.attn and not model.share_hid and model.tag_names == ["upos", "xpos", "feats"]
    return nlp, trainer, model


class CharNet(torch.nn.Module):
    """One word: char ids [1, L] -> transformed character representation [1, D]."""

    def __init__(self, model):
        super().__init__()
        self.m = model

    def forward(self, chars):
        cm = self.m.charmodel
        embs = cm.char_emb(chars)
        n = cm.num_dir * cm.args["char_num_layers"]
        h0 = cm.charlstm_h_init.expand(n, 1, cm.args["char_hidden_dim"]).contiguous()
        c0 = cm.charlstm_c_init.expand(n, 1, cm.args["char_hidden_dim"]).contiguous()
        out, _ = cm.charlstm.lstm(embs, (h0, c0))
        rep = (out * torch.sigmoid(cm.char_attn(out))).sum(1)
        return self.m.trans_char(rep)


def biaffine(scorer, x1, x2):
    """stanza's BiaffineScorer without aten::bilinear (no ONNX equivalent): the inputs get a
    constant 1 appended, then out[t, k] = x1[t] . W[k] . x2[t] + b[k] as one matrix product."""
    x1 = torch.cat([x1, torch.ones_like(x1[:, :1])], 1)
    x2 = torch.cat([x2, torch.ones_like(x2[:, :1])], 1)
    w, b = scorer.W_bilin.weight, scorer.W_bilin.bias            # [K, I, J], [K]
    k, i, j = w.shape
    z = torch.matmul(x1, w.permute(1, 0, 2).reshape(i, k * j)).reshape(-1, k, j)
    return (z * x2[:, None, :]).sum(2) + b


class SentNet(torch.nn.Module):
    """word ids [1, T], pretrained vectors [1, T, 100], char reps [1, T, D] -> tag ids."""

    def __init__(self, model):
        super().__init__()
        self.m = model

    def forward(self, word, pre, chars):
        m = self.m
        x = torch.cat([m.word_emb(word), m.trans_pretrained(pre), chars], 2)
        hl = m.taggerlstm
        nl, hd = m.args["num_layers"], m.args["hidden_dim"]
        h0 = m.taggerlstm_h_init.expand(2 * nl, 1, hd).contiguous()
        c0 = m.taggerlstm_c_init.expand(2 * nl, 1, hd).contiguous()
        for layer in range(nl):
            hx = (h0[2 * layer:2 * layer + 2], c0[2 * layer:2 * layer + 2])
            h, _ = hl.lstm[layer].lstm(x, hx)
            x = h + torch.sigmoid(hl.gate[layer](x)) * hl.highway_func(hl.highway[layer](x))
        out = x[0]                                                       # [T, 2H]
        upos_hid = F.relu(m.upos_hid(out))
        upos_scores = m.upos_clf(upos_hid)
        hids, scores = {"upos": upos_hid}, {"upos": upos_scores}
        res = {"upos": upos_scores.argmax(1)}
        for name in m.eval_order:
            hid = F.relu(m.tag_hid[name](out))
            hids[name] = hid
            parent = m.parent_representation(name, hids, scores, {})
            clf = m.tag_clf[name]
            if isinstance(clf, torch.nn.ModuleList):
                res[name] = torch.stack([biaffine(c, hid, parent).argmax(1) for c in clf], 1)
            else:
                s = biaffine(clf, hid, parent)
                scores[name] = s
                res[name] = s.argmax(1)
        return res["upos"], res["xpos"], res["feats"]


def ids(trainer, pretrain_lookup, words):
    v = trainer.vocab
    word = torch.tensor([v["word"].map(words)])
    chars = [torch.tensor([v["char"].map(list(w))]) for w in words]
    pre = torch.from_numpy(np.stack([pretrain_lookup(w) for w in words]))[None]
    return word, chars, pre


def read_conllu(path, limit):
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
                cur.append((c[1], c[3], c[4]))
    return sents


def main():
    os.makedirs(OUT, exist_ok=True)
    sents = read_conllu(os.path.join(WORK, "ud", "en_ewt-ud-test.conllu"), CHECK_SENTS)

    # shared pretrained vectors: the most frequent words, int8 per row
    pt = torch.load(os.path.join(HF, "pretrain", "conll17.pt"), map_location="cpu", weights_only=False)
    emb = pt["emb"].numpy() if hasattr(pt["emb"], "numpy") else np.asarray(pt["emb"])
    vocab = pt["vocab"]["_id2unit"]          # PAD, UNK, EMPTY, ROOT, then words by frequency
    keep = min(len(vocab), 4 + PRETRAIN_TOP)
    full_index = {w: i for i, w in enumerate(vocab)}
    sub = emb[:keep].astype(np.float32)
    scale = np.maximum(np.abs(sub).max(1), 1e-8) / 127.0
    q = np.round(sub / scale[:, None]).astype(np.int8)
    deq = q.astype(np.float32) * scale[:, None]
    with open(os.path.join(OUT, "pretrain.words.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(vocab[:keep]))
    q.tofile(os.path.join(OUT, "pretrain.i8"))
    scale.astype(np.float32).tofile(os.path.join(OUT, "pretrain.scale"))

    def key(w):                              # as stanza: lowercased, spaces as no-break spaces
        return w.lower().replace(" ", "\xa0")

    def full_vec(w):
        return emb[full_index.get(key(w), 1)].astype(np.float32)

    def small_vec(w):
        i = full_index.get(key(w), 1)
        return deq[i if i < keep else 1]

    for name in MODELS:
        nlp, trainer, model = load(name)
        char_net, sent_net = CharNet(model).eval(), SentNet(model).eval()
        v = trainer.vocab
        mismatch = total = 0
        correct_small = correct_full = 0
        with torch.no_grad():
            doc = nlp([[w for w, _, _ in s] for s in sents])
            for s, ds in zip(sents, doc.sentences):
                words = [w for w, _, _ in s]
                word, chars, pre = ids(trainer, full_vec, words)
                creps = torch.cat([char_net(c) for c in chars])[None]
                up, xp, _ = sent_net(word, pre, creps)
                ours = list(zip(v["upos"].unmap(up.tolist()), v["xpos"].unmap(xp.tolist())))
                theirs = [(w.upos, w.xpos) for w in ds.words]
                mismatch += sum(a != b for a, b in zip(ours, theirs))
                correct_full += sum(a[1] == g for a, (_, _, g) in zip(ours, s))
                total += len(words)
                _, _, pre_s = ids(trainer, small_vec, words)
                _, xp_s, _ = sent_net(word, pre_s, creps)
                correct_small += sum(a == g for a, (_, _, g) in zip(v["xpos"].unmap(xp_s.tolist()), s))
        print(f"{name}: wrapper vs stanza on {total} EWT words: {mismatch} differences")
        # stanza tags sentences in padded batches, the wrapper one at a time: float rounding
        # can flip a near-tie (full EWT test: 4 of 25,094 words, 3 of them now matching gold)
        if mismatch > MAX_DIFF_RATE * total:
            sys.exit(f"{name}: the wrapper does not reproduce stanza")
        print(f"{name}: Penn accuracy, full float vectors {100 * correct_full / total:.2f}%, "
              f"top {PRETRAIN_TOP} int8 vectors {100 * correct_small / total:.2f}%")

        # ONNX export (classic exporter; dynamic word length / sentence length)
        cpath, spath = (os.path.join(OUT, f"{name}.{p}.onnx") for p in ("char", "sent"))
        ex_word, ex_chars, ex_pre = ids(trainer, small_vec, ["The", "pairs", "are", "here", "."])
        ex_creps = torch.cat([char_net(c) for c in ex_chars])[None]
        torch.onnx.export(char_net, (ex_chars[1],), cpath, input_names=["chars"], output_names=["rep"],
                          dynamic_axes={"chars": {1: "L"}}, opset_version=17, dynamo=False)
        torch.onnx.export(sent_net, (ex_word, ex_pre, ex_creps), spath,
                          input_names=["word", "pre", "chars"], output_names=["upos", "xpos", "feats"],
                          dynamic_axes={"word": {1: "T"}, "pre": {1: "T"}, "chars": {1: "T"},
                                        "upos": {0: "T"}, "xpos": {0: "T"}, "feats": {0: "T"}},
                          opset_version=17, dynamo=False)
        cs, ss = ort.InferenceSession(cpath), ort.InferenceSession(spath)
        diff = 0
        with torch.no_grad():
            for s in sents[:100]:
                words = [w for w, _, _ in s]
                word, chars, pre = ids(trainer, small_vec, words)
                creps_t = torch.cat([char_net(c) for c in chars])[None]
                ref = sent_net(word, pre, creps_t)
                creps_o = np.concatenate([cs.run(None, {"chars": c.numpy()})[0] for c in chars])[None]
                got = ss.run(None, {"word": word.numpy(), "pre": pre.numpy(), "chars": creps_o})
                diff += sum(int((r.numpy() != g).sum()) for r, g in zip(ref, got))
        print(f"{name}: onnxruntime vs wrapper on 100 sentences: {diff} differing tags")
        if diff:
            sys.exit(f"{name}: ONNX export differs")

        feats_cols = list(v["feats"]._id2unit.keys()) if isinstance(v["feats"]._id2unit, dict) else None
        meta = {
            "word": v["word"]._id2unit, "word_lower": v["word"].lower,
            "char": v["char"]._id2unit,
            "upos": v["upos"]._id2unit, "xpos": v["xpos"]._id2unit,
            "feats": {"columns": feats_cols,
                      "values": {k: u for k, u in v["feats"]._id2unit.items()} if feats_cols else None},
            "unk": 1, "pretrain_dim": int(emb.shape[1]), "pretrain_rows": keep,
        }
        with open(os.path.join(OUT, f"{name}.vocab.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False)
    for f in sorted(os.listdir(OUT)):
        print(f"  {os.path.getsize(os.path.join(OUT, f)) / 1e6:7.1f} MB  {f}")


main()
