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
2. **Export stanza's non-transformer English depparse** (combined_nocharlm depparse, the same
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
4. **Coreference in the browser** is a separate decision. The desktop model is roberta-large
   (too big for a page). Ask the user before choosing a smaller pretrained coref model, or leave
   it at rule 3 plus a labelled fallback.
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
