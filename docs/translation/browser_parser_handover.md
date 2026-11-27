# Next step: a dependency parser in the browser (eng→glb) — handover

Written 2026-11-27 for the next session. It continues `rule_gaps_handover.md` (§6b is the
session before this one; read §1 ground rules and §3 measuring there first).

## 1. The task

Give the browser translator (`web/`) a dependency parse for English, so the steps that now say
"(fallback: no parser in browser)" do in the browser what they already do on the desktop. The
main target is **sesu**: a 3rd-person possessive whose owner is the subject of its own clause
becomes *sesu* (He lost his keys → Te sonxi sesu klavi). The gold has it about 99 times in the
1,052 eng dev sentences; the browser output has it 0 times. Bare relative clauses and participle
clauses are the second target (rule_gaps_handover.md §4, about 59 sentences).

User decisions in force (2026-11-27): a **pretrained** model is fine, **no training or
fine-tuning**; rules on the parser's output must have zero false positives; word-sense problems
wait for a neural WSD model and are not part of this.

## 1b. Decided with the user (2026-11-27)

- **Parser: stanza `combined_nocharlm` depparse.** It is from the same family and treebanks as
  the browser tagger (UD EWT/GUM, CC BY-SA / CC BY), it reuses the conll17 vectors the page
  already ships, and it adds about 20 MB of ONNX. Not charlm: that would also need the
  forward/backward character LMs exported (bigger, slower). Excluded: spaCy (OntoNotes), UDPipe 1
  (CC BY-NC-SA), transformer parsers (size). The model file is not in the local cache yet
  (only `depparse/combined_electra-large.pt` is): download `combined_nocharlm` depparse into
  `/media/paleos/Warehouse2/Language/Claude/browser_tagger/models/depparse/`, as was done for
  the PoS nocharlm models.
- **Coreference: look for a small open model, and report before using one.** Constraints: openly
  licensed (no OntoNotes-trained models, no NC licences, no licence requests); small enough to
  run in a page (the desktop's stanza GUM coref is roberta-large, far too big); pretrained only.
  If nothing fits, the browser keeps the parse-only rule 3 below (pronoun subject agreeing with
  the possessive, no rival owner), labelled as the fallback it already is. Do not add a
  noun-subject heuristic: it was offered and not chosen (false positives).

## 1c. Coreference candidates found (search 2026-11-27, before any download)

| model | data | licence | size | quality | verdict |
|---|---|---|---|---|---|
| BookNLP **small** coref (`coref_google_bert_uncased_L-2_H-256_A-4`, plus entity tagger `entities_…L-4_H-256` for mentions) | README: "trained on LitBank and PreCo"; the small models are distilled on the big model's predictions over "a collection of contemporary texts" | code MIT; **model files: no licence stated** (hosted at people.ischool.berkeley.edu/~dbamman/booknlp_models/) | BERT 2 layers × 256: a few MB | avg F1 76.4 (big 79.0), literary domain | best fit if the licence and PreCo terms check out |
| compnet-renard/bert-base-cased-literary-coref(-v2) | LitBank (CC BY 4.0) | weights MIT; its inference library Tibert is **GPL-3.0** (must not be copied into this MIT repo: reimplement the e2e-coref span decoding) | bert-base, 110M params (~110 MB int8) | MUC 78.2, B3 62.4, CEAF 54.2 on a LitBank split | possible, but large for a page |
| talmago/allennlp-coref-onnx (MiniLM, ONNX) | distilled from AllenNLP's coref model, i.e. OntoNotes | MIT | small | not reported | excluded (OntoNotes-derived) |
| cp500/infon-coref-pointer (onnxruntime-web ready) | synthetic news-style data of unstated origin | Apache 2.0 | 235 MB fp16 | own val set only | excluded (size, unclear data) |
| stanza GUM / udcoref coref | GUM CC BY / CorefUD | open | roberta-large / xlm-roberta: hundreds of MB | best | too big for a page (desktop only) |
| fastcoref, spaCy coref, neuralcoref, Maverick-OntoNotes | OntoNotes | — | — | — | excluded |

Open questions on the BookNLP route: (1) PreCo's terms. The YITU announcement says "available
for research purpose"; one third-party paper says MIT; the PreCo page itself could not be read
here (egress blocked). (2) The licence of the BookNLP model files. (3) Its mentions cover only
the LitBank entity types (PER, LOC, FAC, GPE, ORG, VEH). That is enough for his/her with a
person or animal-character subject, not for its/their with things.

Before any of this: measure on the desktop how many gold sesu need a chain at all (handover
§4 step 1). If most come from pronoun subjects, the parse-only rule may be enough.

## 1d. LitBank mode (user, 2026-11-27): an opt-in coreference mode for the browser translator

The user asked for a **LitBank mode**: the browser translator gets an optional setting that
loads a LitBank-trained coreference model, so the coref stage of eng→glb (sesu, it/they
classes) runs in the page as on the desktop. The default page stays as it is; the mode is a
larger, opt-in download.

- **Model:** `compnet-renard/bert-base-cased-literary-coref-v2` (MIT weights; trained on LitBank,
  CC BY 4.0; bert-base-cased + an e2e-coref head à la Lee et al. 2017). Downloaded on
  2026-11-27 to `/media/paleos/Warehouse2/Language/Claude/browser_coref/hf/` (tokenizer from
  `bert-base-cased` in the same cache). `model.safetensors` is 486 MB fp32. Config:
  `max_span_size` 10, `segment_size` 128, `mentions_per_tokens` 0.4, `antecedents_nb` 350,
  `mention_scorer_hidden_size` 3000. int8 should bring it to about 120 MB; measure it.
- **Inference code:** Tibert (GPL-3.0), cloned to `…/browser_coref/src/Tibert` (reference only;
  `bertcoref.py` `BertForCoreferenceResolution`: `mention_score`, `pruned_mentions_indexs`,
  `closest_antecedents_indexs`, `mention_compatibility_score`; `predict.py`
  `predict_coref_simple`). Porting it makes our JS a derivative: **the browser version becomes
  GPL-3.0-or-later**. The bundle is already GPL in practice (apertium.wasm = Apertium tools +
  CG-3, and the pair data are GPL). Add `web/LICENSE` (GPL-3.0-or-later) and one README line: `web/`
  is GPL, the rest of GlobasaLexiTools stays MIT. Check first that apertium-spa (COPYING is GPL-2;
  no "or later" grant found in its files) can be combined with GPL-3 code. The user asked about
  GPL for the browser version and then requested this mode; confirm the licence change with
  them — done: user confirmed 2026-11-27, web/LICENSE committed.
- **Depends on the browser parser** (§1b, §4 steps 2–3): the sesu rule needs the clause subject
  (nsubj) from the parse as well as the chains. Build the parser first, then this.
- **Plan:**
  1. Reference outputs: run Tibert's `predict_coref_simple` on the eng dev texts in a separate
     venv (GPL lib, local only) and keep the chains.
  2. Export bert-base + the scoring heads to ONNX (int8). Port span enumeration (≤10 words,
     within a 128-wordpiece segment), mention pruning (top 0.4 × words), antecedent scoring
     (350 closest) and cluster building to JS (`web/src/coref.mjs`, GPL header). Check that the JS
     chains equal Tibert's on the dev texts, as the tagger exporter checks its outputs.
  3. Convert the chains to the service's `coref` shape (`[[{start, end, head}]]`, word indices
     of the browser tokenisation; head = the mention word whose parse head lies outside it).
  4. UI: a "LitBank mode" switch (download size shown, cached like the tagger). In `BROWSER_NLP`,
     map `("eng-glb-neural.py", "coref")` when the mode is on. Off: rule 3 (parse only).
     Notes list the mode as on or off.
  5. Measure: sesu in output against gold, chrF on eng dev, browser vs desktop (electra + roberta
     GUM coref). LitBank covers PER/LOC/FAC/GPE/ORG/VEH entities only, so it/its for things gets
     no chain: the desktop's GUM model stays the reference.

### Memory plan for the LitBank mode (user, 2026-11-27: use checkpoints such as chapters)

The heavy part of the mode is the mention-pair scoring, not the weights. By estimate, one pass
over 1,000 words already needs more than 1 GB (about 400 kept mentions × 350 antecedents ×
2,324 floats). onnxruntime-web's ceiling is 4 GB (wasm32); phones close the tab around 1–2 GB.
So the text is resolved in pieces:

1. **Chapters are checkpoints.** A chapter heading starts a new coreference document: the
   chains, the tensors and the ONNX session's working memory are released before the next
   chapter (dispose every tensor; reuse one session). The analysis of a finished chapter is
   cached by its text, so translating it again costs nothing. Headings are recognised by
   `Chapter N` / `CHAPTER N` / a Roman numeral on its own line, Markdown `#` lines, and Title
   Case lines on their own (the same test as `title_case()` in eng-glb-neural.py). A text with
   no heading is one chapter.
2. **Windows inside a chapter.** A chapter can be 5–10k words, so within it the model runs on
   windows of about 512 wordpieces (Tibert's split setting) and merges the clusters across
   windows. The model card's split + hierarchical-merging (HM) rows are the reference for the
   merge, and the card gives their scores. Only the current window's tensors are alive at any
   time; between windows only the clusters (word spans) are kept.
   Window boundaries follow the text, strongest first: (a) scene breaks (`* * *`, `#`, `***`, a
   centred ornament, two or more blank lines): a hard reset like a chapter; (b) paragraphs: a
   window is as many whole paragraphs as fit the budget, and the last paragraph of the previous
   window is repeated as context (its clusters seed the merge); (c) sentences: only a paragraph
   longer than a window is cut, at a sentence end. Never cut inside a quotation; keep a dialogue
   exchange together where it fits. Size: about 256–512 wordpieces. At 512 (about 400 words,
   ~160 kept mentions) the pair tensor is about 240 MB; at 256 it is about 60 MB (phone-safe).
3. **Nothing from the model crosses a checkpoint.** sesu only needs the possessive's own
   clause. The it/they class (te/to) needs an antecedent, which is nearly always within the
   chapter. A chain that would span chapters is cut, and the notes say so.
4. **Budget test:** extend `web/test/browser.mjs` to report peak memory (CDP
   `Performance.getMetrics` / `performance.measureUserAgentSpecificMemory`) on a long text, such
   as a whole Time Machine chapter. The test fails above a budget. Set the number with the user;
   the starting proposal is a phone-safe ~1 GB for the whole tab.

## 2. Correction to the last handover

§6b of rule_gaps_handover.md (and my report to the user) says no sesu stage exists. **That is
wrong.** sesu is already in the desktop pipeline:

- `GlobasaTranslation/apertium-glb-eng/eng-glb-neural.py`, stage `coref` (it runs after
  `cg-proc`, before the tagger). `coreferent()` (about line 567) decides whether the possessive
  and the clause subject corefer:
  1. the same coreference chain → sesu;
  2. different chains → not sesu;
  3. no chain for one of them: a subject **pronoun** agreeing with the possessive (he/his,
     she/her, it/its, they/their) with no rival owner in the clause (`other_candidates`) →
     sesu, labelled "(fallback: coref did not link them ...)".

  `make_reflexive()` rewrites the reading to `prpers<det><pos><ref>…` (bidix `se<det><pos>` =
  sesu). The subject comes from the dependency parse: `head`/`deprel` (nsubj) of each word.
- `glb-neural.py` stage `se` (`stage_se`) is the Spanish *se* stage, not sesu. That is what
  misled me.

So in the browser, the coref stage does nothing at all. Rule 3 needs **only a parse**. Rule 1
also needs coreference chains; without them, noun subjects ("Oliver thanked … for his …") stay
*tesu*, and so do possessives the parse cannot place.

## 3. What the desktop uses, and what the browser has

| | desktop (`eng-nlp-service.py`, port 8597) | browser (`web/src/tagger.mjs`) |
|---|---|---|
| PoS | stanza combined_electra-large + gum second tagger | stanza combined_nocharlm + gum_nocharlm as ONNX (`web/tagger/export_stanza_pos.py`) |
| depparse | stanza combined_electra-large; tree decoder in Rust (`glb_stanza.fast_depparse`, rust/globasa_fast) | **none** |
| coref | stanza gum-nospeakers_roberta-large-lora | **none** |

The service's `/analyze` answer (`analyze_piece`, eng-nlp-service.py ~line 70) is the
interface every step reads: `words[i] = {i, sent, start, end, text, lemma, upos, xpos, xpos2,
feats, deprel, head, mwt, lexfiles}` and `coref = [[{start, end, head}, …], …]`. The browser
tagger answers the same shape without `head`/`deprel`/`coref`. A browser parser must add `head`
and `deprel` to the same words.

How the browser substitutes a model for the service: `web/build_modes.py` `BROWSER_NLP` maps
`("eng-glb-neural.py", "pos")` to the in-page tagger (the step's `ENG_NLP_URL` points to
`http://browser-nlp`, and `web/py/runner.py` answers it via `pipeline.mjs` → `this.nlp[lang]
.analyze(req)`). Today only the `pos` stage is mapped. The `coref` stage of eng-glb-neural.py,
and `glb-neural.py eng parse/focus`, get the "(fallback: no neural service in browser)" switch
(`NEURAL` in build_modes.py).

## 4. Suggested plan

1. **Measure the ceiling first, on the desktop.** Start the service
   (`cd GlobasaTranslation/apertium-glb-eng && ../../venv/bin/python eng-nlp-service.py`, GPU,
   cap it), then run the eng dev gold natively with and without it
   (`ENG_GLB_NEURAL=0` vs on). Count sesu in output vs gold, and the chrF difference. Also count
   how many sesu come from rule 3 (the fallback label in `ENG_GLB_NEURAL_TRACE`) against rule 1
   (chains). That says how much a parser alone would bring.
2. **Export stanza's non-transformer English depparse** (combined_nocharlm depparse, decided §1b; the same
   pretrain vectors the tagger already ships) to ONNX, modelled on `web/tagger/export_stanza_pos.py`:
   - The wrapper must reproduce stanza's scores. The exporter's own checks pin it: wrapper ==
     stanza, onnxruntime == wrapper on UD EWT test, and LAS/UAS reported with the trimmed int8
     vectors.
   - The parser's input is words + UPOS/XPOS/feats. Use the browser tagger's output, as stanza
     does with its own tagger.
   - Tree decoding (Chu-Liu-Edmonds) in JS. Port the Rust decoder in `rust/globasa_fast`: it
     returns the same trees as stanza's.
   - Model files go to the work dir next to the tagger exports
     (`/media/paleos/Warehouse2/Language/Claude/browser_tagger/`; /dev/sdb2 is full); then
     `web/build.sh` copies them into `dist/tagger/en`.
3. **Wire it in.** `tagger.mjs analyze()` fills `head`/`deprel`. Map `("eng-glb-neural.py",
   "coref")` in `BROWSER_NLP`; the stage gets `coref: []`. Check that the code tolerates empty
   chains: rule 3 should then fire. Do the same for `glb-neural.py eng parse` if its checks
   (names, that/which) only need the parse.
4. **Coreference in the browser:** search for a small open coref model (§1b constraints) and
   report the candidates to the user (licence, training data, size, accuracy on GUM if known)
   before wiring one in. Until then rule 3 only.
5. Then the parser-based rules from rule_gaps_handover.md §4: bare relatives (`acl:relcl` with no
   relative word → *hu … da*; `eng-glb-relative.py` rewrites relatives today) and participle
   clauses (`advcl`/`acl` VBG/VBN). Zero false positives: act only on unambiguous trees.

## 5. How to measure (as before)

- Browser pipeline on all eng dev:
  `cd web && python3 test/capped.py node test/gap_dump.mjs OUT.jsonl && python3 test/gap_report.py OUT.jsonl`.
  The last run's output is the session baseline: mean chrF 63.46, 37 sentences with #. To
  compare runs per sentence, copy the small `cmpj.py` logic (chrF from
  `apertium-glb-eng/test/score.py`).
- Per set: `python3 test/capped.py node test/tagger_quality.mjs 60` (now: curated 83.2, UDHR 49.4,
  P&C 53.0, Tell-tale 73.7, Thirty 66.7).
- Parity: `python3 test/capped.py node test/parity.mjs` must stay "all modes identical"
  (neural steps are off in parity runs).
- Trace one sentence: `python3 test/capped.py node test/trace.mjs "He lost his keys." pos coref`.
- Node is emsdk's:
  `export PATH=/media/paleos/Warehouse2/Language/Claude/wasm/emsdk/node/24.19.0_64bit/bin:$PATH`.
  Start gap_dump/parity **as a separate command after `web/build.sh --no-wasm`**: started in the
  same command line, they read a half-written bundle.

## 6. State of the repos

Everything from 2026-11-27 is committed locally, nothing pushed:

- main repo: 740c251 (apertium-glb, -eng submodules + handover), ba0f0ae (trace.mjs), d3c4f01
  (OpenWolf).
- apertium-glb-epo, apertium-glb-spa and apertium-epo are separate repos with their own commits.

Lists waiting for the user's curation: the `check` rows of
`apertium-glb-epo/epo_glb_affixes.tsv`, the `alt` rows of `apertium-glb-eng/phrasal_verbs.tsv`.
