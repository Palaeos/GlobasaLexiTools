"""Word-level BERT vectors shared by macberth_map.py and period_sense_probe.py.

    load(name)                       tokenizer + model (MacBERTh needs do_lower_case: it ships no
                                     tokenizer_config)
    embed(tok, model, sents, layer)  one float32 array per pre-split sentence, a row per word =
                                     mean of its subword vectors at that layer; NaN rows for
                                     words truncated away
    words(text)                      the word splitter both models are fed with"""
import re

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer, BertTokenizerFast

MBERT, MACBERTH = "bert-base-multilingual-cased", "emanjavacas/MacBERTh"
WORD = re.compile(r"\w+(?:['’]\w+)*|[^\w\s]")
BATCH = 32
device = "cuda" if torch.cuda.is_available() else "cpu"


def words(text):
    return WORD.findall(text)


def load(name):
    tok = (BertTokenizerFast.from_pretrained(name, do_lower_case=True) if name == MACBERTH
           else AutoTokenizer.from_pretrained(name))
    model = AutoModel.from_pretrained(name, output_hidden_states=True).eval().to(device)
    if device == "cuda":
        model.half()
    return tok, model


def embed_cached(name, sents, layer, cache_dir):
    """embed() with a per-sentence disk cache: cache_dir/<model>_L<layer>/shard_NNNN.npz, one
    float16 array per sentence (key = sha1 of the words). New sentences go to a new shard; the
    model is loaded only when something is missing. cache_dir None = no cache."""
    import hashlib
    import os
    keys = [hashlib.sha1("\x1f".join(s).encode()).hexdigest() for s in sents]
    have = {}
    d = os.path.join(cache_dir, f"{name.replace('/', '_')}_L{layer}") if cache_dir else None
    shards = []
    if d and os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.endswith(".npz"):
                z = np.load(os.path.join(d, f))
                shards.append(z)
                for k in z.files:
                    have[k] = z
    todo = sorted({i for i, k in enumerate(keys) if k not in have}, key=lambda i: keys[i])
    todo = list({keys[i]: i for i in todo}.values())
    new = {}
    if todo:
        tok, model = load(name)
        for k, v in zip([keys[i] for i in todo], embed(tok, model, [sents[i] for i in todo], layer)):
            new[k] = v.astype(np.float16)
        del tok, model
        if d:
            os.makedirs(d, exist_ok=True)
            np.savez(os.path.join(d, f"shard_{len(shards):04d}.npz"), **new)
    return [(new[k] if k in new else have[k][k]).astype(np.float32) for k in keys]


@torch.no_grad()
def embed(tok, model, sents, layer):
    out = []
    for i in range(0, len(sents), BATCH):
        batch = sents[i:i + BATCH]
        enc = tok(batch, is_split_into_words=True, truncation=True, max_length=512,
                  padding=True, return_tensors="pt")
        hs = model(**{k: v.to(device) for k, v in enc.items()}).hidden_states[layer].float().cpu().numpy()
        for b, ws in enumerate(batch):
            vec = np.full((len(ws), hs.shape[-1]), np.nan, dtype=np.float32)
            acc = {}
            for t, wi in enumerate(enc.word_ids(b)):
                if wi is not None:
                    acc.setdefault(wi, []).append(t)
            for wi, ts in acc.items():
                vec[wi] = hs[b, ts].mean(0)
            out.append(vec)
        del hs
    return out
