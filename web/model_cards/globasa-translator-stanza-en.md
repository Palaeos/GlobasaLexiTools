---
license: cc-by-sa-4.0
language:
- en
library_name: onnx
base_model: stanfordnlp/stanza-en
tags:
- onnx
- onnxruntime-web
- stanza
- part-of-speech
- dependency-parsing
- globasa
- apertium
pipeline_tag: token-classification
---

# Stanza English tagger and parser, ONNX for the browser

These are [Stanza](https://stanfordnlp.github.io/stanza/)'s small English models (1.15.1),
exported to ONNX. The Globasa browser translator runs them in the browser with
[onnxruntime-web](https://onnxruntime.ai/), on the English → Globasa (eng→glb) Apertium pair.
They play the part the desktop pipeline gives the stanza NLP service: they prune Apertium's
readings with PoS tags and supply the dependency parse that the rule-based coreference and
relative-clause steps use.

The page fetches the files from a pinned commit of this repo. Nothing is trained or fine-tuned
here: these are Stanza's pretrained weights, converted.

## Files

| File | What |
|---|---|
| `combined_nocharlm.char.onnx`, `.sent.onnx`, `.vocab.json` | PoS tagger, `combined_nocharlm` (UPOS, Penn tags, feats) |
| `gum_nocharlm.char.onnx`, `.sent.onnx`, `.vocab.json` | PoS tagger, `gum_nocharlm`, second opinion on Penn tags |
| `parser.char.onnx`, `parser.sent.onnx`, `parser.vocab.json` | dependency parser, `combined_nocharlm` (arc scores + relations; trees are decoded in JS) |
| `lemma.dict.json` | Stanza's lemma dictionary, pruned to the entries that change the parser's input |
| `pretrain.words.txt`, `pretrain.i8`, `pretrain.scale` | the shared CoNLL 2017 word vectors: the 100,000 most frequent words, int8 per row plus a float32 scale per row |

The parser's large matrices use weight-only int8 (DequantizeLinear). On the test set that
produced no changed trees.

## Checks (made by the export scripts on every run)

- The ONNX taggers predict what Stanza predicts on UD English EWT test. At most 0.05% of words
  may differ, from float near-ties; 4 of 25,094 do.
- Stanza's Penn accuracy on EWT test: 96.0 (combined) and 93.0 (gum).
- The parser reproduces Stanza's heads and relations on EWT test, given the same tags (the same
  0.05% near-tie limit), and onnxruntime reproduces those trees. UAS/LAS are reported for the
  browser's shortcuts too: dictionary lemmas and the trimmed int8 vectors.

## Licence

These are model weights trained on Universal Dependencies treebanks, mainly English EWT
(CC BY-SA 4.0) and GUM (CC BY 4.0), so they are released here under **CC BY-SA 4.0**. Stanza's
code is Apache 2.0. Credit: Qi, Zhang, Zhang, Bolton and Manning (2020), *Stanza: A Python
Natural Language Processing Toolkit for Many Human Languages*; the UD English EWT and GUM
treebank teams.

## Source

Export scripts: `web/tagger/export_stanza_pos.py` and `web/tagger/export_stanza_depparse.py`
in [Palaeos/GlobasaLexiTools](https://github.com/Palaeos/GlobasaLexiTools) (GPL-3.0). The JS
that runs them is `web/src/tagger.mjs` and `web/src/mst.mjs` there.
