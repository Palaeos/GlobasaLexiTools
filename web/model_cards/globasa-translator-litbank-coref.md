---
license: mit
language:
- en
library_name: onnx
base_model: compnet-renard/bert-base-cased-literary-coref-v2
tags:
- onnx
- onnxruntime-web
- coreference-resolution
- litbank
- globasa
- apertium
---

# LitBank coreference, ONNX for the browser

This is [compnet-renard/bert-base-cased-literary-coref-v2](https://huggingface.co/compnet-renard/bert-base-cased-literary-coref-v2),
a coreference model for literary English trained on LitBank, exported to ONNX. The Globasa
browser translator runs it with [onnxruntime-web](https://onnxruntime.ai/) in its opt-in
"LitBank" mode for English → Globasa. Chains of mentions tell the translator who *he*, *she*
and *it* refer to, which matters for the pronouns the translator picks in Globasa.

The page fetches the files from a pinned commit of this repo. Nothing is trained or fine-tuned
here: these are the original weights, converted.

## Files

| File | What |
|---|---|
| `coref.bert.onnx.000` … `.002` | bert-base-cased encoder, one segment of ≤ 128 wordpieces → hidden states, in three parts (concatenate them in order) |
| `coref.heads.onnx` | word vectors → the six per-word projections (mention start/end, pair start/end, antecedent start/end) |
| `coref.consts.f32` | biases, output vectors and distance-bucket projections; the layout is in `coref.json` |
| `coref.vocab.txt` | bert-base-cased wordpieces |
| `coref.json` | manifest: the parts with size and SHA-256, the constants layout, the configuration |

The model's scoring is factorised so that the browser never builds a spans × spans tensor. The
JS port (`web/src/coref.mjs`) explains how. The weights are weight-only int8 (123 MB in all).
Dynamic int8 was rejected, because it changed the chains in 871 of 1,025 test documents.

## Checks (made by the export script)

Measured on 1,025 documents (English dev sentences and *The Time Machine* chapters, in the
windows the browser uses):

- The factorised pipeline gives the same chains as [Tibert](https://github.com/CompNet/Tibert)
  except in 7 documents. All 7 have more than 350 spans, where Tibert's padding of the
  antecedent list depends on tie order.
- Weight-only int8 changes the chains of 11 documents compared with fp32.
- onnxruntime-web in JS gives the same output as Python onnxruntime on all 1,025 documents.
- Peak memory on a mobile profile: 0.96 GB for a 4,184-word chapter.

## Licence

The weights are released under **MIT**, as the original model is. LitBank, the training data,
is CC BY 4.0 (Bamman, Popat and Shen, 2019; Bamman, Lewke and Mansoor, 2020). The inference
follows Tibert (GPL-3.0, CompNet). The JS port is GPL-3.0 and lives in the source repo, not
here.

## Source

Export script: `web/tagger/export_litbank_coref.py` in
[Palaeos/GlobasaLexiTools](https://github.com/Palaeos/GlobasaLexiTools) (GPL-3.0).
