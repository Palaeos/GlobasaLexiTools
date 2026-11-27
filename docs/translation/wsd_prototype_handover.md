# Context-based Globasa word choice (eng→glb): the prototype experiment — handover

Written 2026-11-27 for a **separate session**. Do not mix it with the browser parser / LitBank
work (`browser_parser_handover.md`); that session builds the browser side, this one only measures.
Background and earlier numbers: `CONTEXTUAL_WSD.md` (sections 1 and 4; its §7 handover covers the
period-sense work, which is a different track).

## 1. The question

When the eng→glb bidix offers several Globasa words for an English word, can a contextual
embedding pick the one the translator would use, better than the pipeline does now? This is an
offline experiment on the desktop GPU. The browser comes later, and only if the numbers justify it.

The user's goal: **selecting the right Globasa translation in context.** Coreference and the
te/to class are side issues here.

## 2. Rules in force

- Pretrained models only: **no training or fine-tuning** (feedback_no_training_now,
  feedback_no_globasa_specific_training). Nearest-prototype matching is not training.
- The Globasa choices stay in lists: the candidates come from the bidix and the word list. A
  prototype is built from source-language sentences labelled through those lists.
- Only openly licensed data, and nothing that needs a licence request or permission
  (feedback_no_licensed_resources). No OntoNotes-trained models.
- Word sense must not become lrx rules (feedback_word_sense_later).
- Anything that would act at translation time needs a **confidence margin**. Below it, keep
  Apertium's choice, labelled "(fallback: low confidence)" (feedback_mark_fallbacks).
- Memory: run through `memlimit.py` / `web/test/capped.py` (GLOBASA_MEM_GB). Large caches go to
  `/media/paleos/Warehouse2/Language/Claude/`; `/dev/sdb2` (repo + HF cache) is full.

## 3. Test set and bar

- `GlobasaTranslation/apertium-glb-eng/test/lexsel_eval.py` builds the silver items: for every
  word where the bidix offers several Globasa lemmas (eng-glb-biprefs stream) and exactly one of
  them occurs in the gold translation, that lemma is the label. The pipeline's own choice is read
  from the eng-glb-lex stream. It writes `test/local/lexsel_items.tsv`. Reuse its item extraction;
  its reranker part is the earlier, failed baseline.
- **1,045 items** on the eng dev gold. **The bar: the pipeline gets 57.8% right.** The gloss
  cross-encoder (bge-reranker-v2-m3) got 52.6%. Report by coverage band (`CONTEXTUAL_WSD.md` §4):
  every candidate has prototypes / the right one has, some rivals don't / the right one has none.
- The eng-glb pipeline has changed since 2026-11-21 (rule-gap session, rule_gaps_handover.md
  §6b), so first **re-extract the items and re-measure the 57.8%**: the bar may have moved.
- Keep dev for development and test for the final number. **No gold sentence (dev or test) may
  go into a prototype.**

## 4. Method to test

1. **Prototypes:** one vector per Globasa candidate (per English word + part of speech): the
   mean, or a few cluster centres, of the target word's contextual embedding in English sentences
   whose translation used that candidate. Sources, in order of precision:
   - vetted Wiktionary sense examples linked to the candidate (`vetted_senses.load_rows()`);
   - pivot-labelled parallel sentences: English–Esperanto/Spanish (later French/German) pairs
     where the aligned pivot word is a word-list gloss of exactly one candidate (85–92% precise
     in `test/pivot_oracle.py` / `test/sibling_pivot.py`; Esperanto is the most precise pivot).
     Open corpora only. Tatoeba (CC BY 2.0 FR) and Europarl/OPUS sets with open terms: check each
     licence before use. The repo's own Globasa texts (Doxo/Xwexi) are allowed, but keep the gold
     splits out.
   - not for function words: the vetted preposition tables list almost everything (50% precision).
     Prepositions go to the planned fe/de/per/in classifier.
2. **At prediction:** embed the sentence and take the target word's vector (average of its
   wordpieces, from one chosen layer). Score each candidate's prototype by cosine; act only when
   the best beats the second by a margin. Sweep the margin and report precision and coverage per
   value, against the pipeline on the same items.
3. **Encoders to compare** (pretrained, open, small enough to port later):
   - `compnet-renard/bert-base-cased-literary-coref-v2`, a middle layer (it is the LitBank-mode
     coref model, so in that mode the page would get word choice for free). Cached in
     `/media/paleos/Warehouse2/Language/Claude/browser_coref/hf/` (MIT weights). Check whether
     the coref fine-tuning blunted its layers for senses.
   - a small open MiniLM-class English encoder (tens of MB in int8). This is the candidate for
     the default page without the LitBank mode.
   - mBERT (multilingual: would also serve fra/deu/spa→glb). Its vectors are already cached
     for the period work in `/media/paleos/Warehouse2/Language/Claude/period_glb/`.
   Check every model's licence and training data (no OntoNotes) before using it.
4. **Chain consistency (optional, last):** once one mention of an entity gets a confident choice,
   propagate it along the coreference chain ("one sense per discourse", Gale, Church & Yarowsky
   1992). The desktop has chains from eng-nlp-service.py (stanza GUM coref).

## 5. What it will not fix (count them separately)

Suffix variants (syensipul/syensili), -cu/-gi voice, gendered pairs (ixu/femixu), near-synonyms
(xaher/lilxaher), and the translators' free choices (worth → layeya). These need syntax features
(transitivity, reflexive, referent gender: the browser parser will provide some) or stay as
free variation. Report them as a category, not as WSD errors.

## 6. Deliverable

A short report at the end of `CONTEXTUAL_WSD.md` (new section). Contents:
- items and bar (re-measured);
- per encoder: precision and coverage per margin, by coverage band;
- a recommendation: whether to port, which encoder, at which margin;
- the user decision it feeds: word choice in the **default page** (its own small encoder, about
  30–90 MB more) or **only in the LitBank mode** (shared BERT-base, no extra memory).

Scripts go next to the existing ones (`apertium-glb-eng/test/`, `time-machine/bert_words.py`
for cached embeddings). Commit per the atomic-commit rule; push only when asked.

## 7. State of the files (2026-11-27)

- Committed: `CONTEXTUAL_WSD.md`, `time-machine/period_glb.py`, `time-machine/bert_words.py`,
  `apertium-glb-eng/test/lexsel_eval.py`.
- **Not committed** (in the apertium-glb-eng work tree): `test/pivot_oracle.py`,
  `test/sibling_pivot.py`. Read them before reusing; ask the user before committing them.
