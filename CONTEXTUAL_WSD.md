# Contextual word-sense choice for Globasa translation: findings

Measurements from 2026-11-21. All scripts are in the repo, none committed yet. The question: can
contextual embeddings (BERT family) choose the right Globasa word, using how high-resource
languages translate the source word, and for period texts the sense the word had at the time?

## 1. Translation labels for eng→glb lexical choice

Test set: 1,045 silver items from the eng→glb dev gold (`GlobasaTranslation/apertium-glb-eng/test/lexsel_eval.py`).
Each is an English word where the bidix offers several Globasa words and exactly one appears in
the reference translation. The current pipeline gets 57.8% of them right; a cross-encoder
reranker reading the candidates' glosses got 52.6%.

**Ceiling of gloss-based labels** (`test/pivot_oracle.py`). A label from a pivot translation can
only work if the right Globasa word has a pivot-language gloss that no other candidate has. On
898 content-word items:

| Pivot words from | Spanish or Esperanto | Any of 6 languages |
|---|---|---|
| Word list | 92% | 95% |
| Vetted Wiktionary senses | 85% of the items they cover | |

The vetted-sense translation tables are coarser for Spanish and Esperanto because a sense
table lists broad words shared by sibling candidates (*con* under both ton and yon). They do
add French, German and Russian evidence the word list mostly lacks.

**Real sibling translations** (`test/sibling_pivot.py`). Units of `Doxo_passages_extended.tmx`
with English, Globasa and Spanish/Esperanto/French/German. Only UDHR and Pepper & Carrot are
true sibling translations: Vanege's stories were translated from Esperanto and Towa Babel from
Spanish, so they agree with their source by construction and are excluded.

On 263 content-word items (current pipeline: 52%):

| Pivots | Picks | Right | Net gain over the pipeline |
|---|---|---|---|
| Spanish + Esperanto, word list | 96 | 85% | +35 |
| Esperanto, vetted senses | 52 | 92% | +23 |
| All 4 pivots, both sources | 140 | 84% | +52 |

Findings:

- Esperanto is the most precise pivot; French and German add coverage at about 81%.
- Vetted-sense tables must not label function words: precision is 50%, because preposition tables list almost everything.
- Word alignment with SimAlign did not raise precision (about 87% with or without it); it only lowered coverage.
- The errors are lexical. The aligned pivot word is listed under several Globasa candidates: suffix variants (syensipul/syensili), -cu/-gi voice, gender (ixu/femixu), near-synonyms (xaher/lilxaher). Other errors are free translator choices (worth → layeya, holiday → jaxnedin).
- These residual choices need syntax features (transitivity, reflexive, gendered referent), not pivots.

Conclusion: translation labels are 85–92% precise. That is good enough for training labels,
not for rules with zero false positives.

## 2. Period senses with MacBERTh

**The model.** MacBERTh is a historical English BERT trained on 1450–1950 text. Its weights
are MIT-licensed and download without a request; some of its training corpora (COHA, for
instance) are licensed, but only the weights are used.

**The map into mBERT's space** (`time-machine/macberth_map.py`). Both models embed the same
English sentences, and a rotation (orthogonal Procrustes) is fitted from MacBERTh's space into
mBERT's at layer 8. The reverse map is its transpose. On held-out words, the nearest mBERT
vector is the same word in 94% of period text and 88% of modern text. English–Spanish
alignment through the map agrees with mBERT's own alignment at F ≈ 88. So the map is faithful
for cross-language steps.

**The sense test.** Gold: the dated-sense occurrences of *The Time Machine* in
`obscure_resolved.tsv`. Each occurrence gets the sense whose prototype (mean vector of the
headword in that sense's examples) is nearest. All results are on the same gold items
(`time-machine/period_sense_probe.py`). Rerun 2026-11-21 after fixes 1–5 of section 7 (sub-sense
keying, sense groups, modern-year prior, Webster joining, synonym substitution): 89 common
items, up from 87 because the sub-sense fix matched two more gold glosses. The first-run numbers
(87 items) are in brackets.

| Sense inventory | Random | First sense | mBERT | MacBERTh |
|---|---|---|---|---|
| Wiktionary | 25% | 43% | 50.6% (52.9) | 57.3% (58.6) |
| Webster 1913 | 38% | 48% | 57.3% (56.3) | 61.8% (60.9) |
| Pooled (Wiktionary + Webster) | 26% | 45% | 55.1% (55.2) | 62.9% (59.8) |
| **Pooled + year prior** | 26% | 45% | 52.8% (52.9) | **65.2%** (63.2) |
| Pooled + year prior, grouped (`choose()`) | | | | 65.2% |

Findings:

- **The fixes add about 2 points**: 58/89 = 65.2% against 55/87 = 63.2%. The gain is in the pooled inventory (Webster joining, synonym substitution); Wiktionary alone fell by one item.
- **Sense groups change nothing on this gold** (58/89 grouped and ungrouped, and 51/89 for Wiktionary with or without the prior). Grouping was made for gay's ten sub-senses; the gold has few such lemmas.
- **Decide senses inside MacBERTh.** MacBERTh vectors rotated into mBERT's space and compared with mBERT-made prototypes scored only 52.8% (first run 49.4%). The map is fine for alignment, but prototypes must come from the same encoder.
- **Webster and Wiktionary fail on different items.** In the first run at least one was right on 79% of items, yet averaging their examples into one prototype captured little of that gain. Scoring each sense by its better source is the next thing to try.
- **The year prior helps MacBERTh, not mBERT.** A sense quoted around the work's year gets a bonus; a sense first quoted well after it gets a penalty but is never dropped. 0.05 was fixed before looking; the sweep gives 56, 55, 58, 56, 55 of 89 for 0.0, 0.02, 0.05, 0.1, 0.2, so 0.05 is a local peak of 2 items, not a plateau.
- **The gains are small.** Pooled + prior grouped beats Wiktionary alone by 7 items out of 89: encouraging, not proven.
- **Translated examples help little** (`time-machine/translation_sense_probe.py`). The 1900s translators' Spanish/Esperanto words picked a sense in only 17 of 121 gold items, and "translation, else MacBERTh" gained 1 item. A third of the errors are senses with no example at all, which translation cannot fix.
- **Corpus scan** of all Wells and Lovecraft works in `works.tsv` (4,600 occurrences): the period pick agrees with the plain Wiktionary pick about 70% of the time. Most changes on frequent words (little, but, down) look like noise, so scans must be limited to period-sensitive words.

## 3. From sense to Globasa

`time-machine/period_senses.py` attaches the period bilingual dictionaries to each sense:

- **Esperanto leads:** Rhodes 1908 and O'Connor 1907. Esperanto was codified in 1887 and has drifted much less, and Globasa's distinctions follow Esperanto.
- **Spanish only confirms:** Velázquez 1910, with a Spanish-only route labelled "(fallback: Spanish only, 1910 sense may have drifted)". Velázquez "(Ant.)" marks senses already old in 1910. 1910 Spanish has drifted since (*luego*: then "at once", now "later").
- **Globasa** comes through the word list's Esperanto/Spanish columns.

On 126 gold items, the top three suggestions contain a word of the curated rendering (rerun
after fixes 1–5; first run in brackets):

| Sense used | Hit |
|---|---|
| Sense the model picked | 25.4% (23%) |
| Correct sense (perfect sense choice) | 27.8% (26%) |
| Any sense of the word | 35.7% (36%) |

The bottleneck is the dictionaries, not the sense choice. Only 181 of 3,956 senses get a
sense-specific period Esperanto equivalent, since Rhodes' "(cue)" markers are rare; 93 of 101
suggestions came through fallbacks (87 entry-level period Esperanto). Many curated renderings are paraphrases or new
compounds, so word overlap understates real agreement.

## 4. Choosing among existing Globasa words at translation time

**The method.** Embed the source sentence and pick the candidate whose prototype is nearest.
Intervene only above a confidence margin; otherwise keep Apertium's choice, labelled
"(fallback: low confidence)". The models would run in `eng-nlp-service.py`, which already keeps
transformers loaded on the GPU, hooked in as a Python step after `eng-glb-biprefs`.

**Prototypes from vetted senses alone** cover too little. On the 1,045 silver items:

| Coverage | Items |
|---|---|
| Every candidate has examples | 175 (17%) |
| The right word has examples, some rivals don't | 401 (38%) |
| The right word has none | 468 (45%) |

Prototypes therefore need a second source: pivot-labelled corpus sentences (Tatoeba, Europarl;
the labelling of section 1, 85–92% precise) plus Globasa's own Doxo/Xwexi usage, keeping the
dev/test splits out.

**Which encoder:** a modern or multilingual one (mBERT also covers the fra/deu/spa→glb pairs)
for modern text; MacBERTh with the year prior for period mode.

The bar to beat is the pipeline's 57.8% on the silver items. Untested.

## 5. The period proposals pipeline

`time-machine/period_glb.py` takes a text or a word list plus a year and returns ranked Globasa
proposals:

- **Finds** the candidates: rare words, and occurrences whose chosen sense is not current today (labelled old, or last quoted before 1950 with at least two dated quotations) and whose sense group beats the best group holding a current sense by the margin (0.03).
- **Chooses the sense** with MacBERTh over the pooled inventory, with the year prior.
- **Proposes Globasa**, strongest evidence first: your curated rows; vetted Wiktionary senses; period Esperanto; Spanish to confirm; modern tables as a labelled fallback; otherwise "needs rendering".
- **Tiers** each proposal *likely*, *possible* or *rare*.
- **Writes** a proposals table. `--apply` appends new rows to `victorian_wordlist.tsv` as `pending`, for works up to 1914 only; existing rows never change.

Usage:

```
venv/bin/python time-machine/period_glb.py words 1895 presently remark [--context "..."]
venv/bin/python time-machine/period_glb.py work "The War of the Worlds" [--apply]
venv/bin/python time-machine/period_glb.py text path/to/text.txt 1897
```

Words mode runs in about 10 seconds. Embeddings are cached on Warehouse2
(`$GLOBASA_BIG_CACHE/period_glb`), so a second run of a work is fast.

**Results on *The Time Machine*** (3,451 content lemmas, 557 rare; CPU, the GPU driver was down).
Recall is the share of glossary lemmas (`obscure_resolved.tsv`) that get any proposal; it does not
check the sense. "Sense-level" counts gold (lemma, gloss) pairs where a proposed sense shares a
content stem with the gold gloss, a rough check.

| Run | Candidate lemmas | Proposals | Flagged lemmas | dated_sense | obscure | Sense-level | Time |
|---|---|---|---|---|---|---|---|
| Before fixes 1–5, loose filter | 2,875 | 2,017 | 1,640 | 48% | 92% | 49/166 | 116 min (embedding) |
| Fixes 1–5, loose filter | 2,884 | 2,203 | 1,740 | 52% | 92% | | |
| Fixes, margin only | 2,741 | 1,813 | 1,529 | 45% | 92% | 44/166 | 15 min |
| Fixes, two quotes, no margin | 2,328 | 1,468 | 1,257 | 43% | 92% | | |
| **Fixes, margin + two quotes (now the default)** | **2,328** | **1,245** | **1,099** | **41%** | **92%** | **43/166** | **8.5 min** (cached) |
| Fixes, labelled old senses only, with margin | | 814 | 759 | 24% | 92% | | |

The default cuts proposals by 38% and flagged lemmas by a third against the first run. The rare-word
recall stays at 92%. Dated-sense recall drops from 48% to 41% of lemmas, but at sense level only from
49 to 43 of 166: most lost lemmas had the wrong sense anyway (brow → "facial expression", down →
"lower place" for the South Downs). Correct senses that the two-quotation rule loses: accession
"increase", nerve "give strength", start "startle"; each sense has a single dated quotation. The
lemma pre-filter now asks for the old sense in a part of speech the word has in the text.
Proposals: 221 likely, 593 rare, 431 possible. First route: period Esperanto 487, needs rendering
391, curated 178, vetted sense 72, labelled fallbacks 77. Peak memory 6.2 GB.

**Precision of the *likely* tier is low.** 40 likely rows (random, seed 20261121), judged by hand:

| Verdict | Rows | Examples |
|---|---|---|
| Right sense, a real period reading | 8 | constitution "general health", sport "pastime", admire "marvel at", satisfy "convince", hid (past participle), strangely "surprisingly", look (transitive), morrow |
| Right sense, but no period problem | 5 | in vain, then, leave "let remain", intervene, ago |
| Wrong sense | 27 | rag → "banknote", hook → "pickpocket", skull → "head of a college", neck → "bundle of wheat", moon → "outwork", lawn → "clothing made from lawn", blue → "literary", explosive → "plosive", nickel → "cheap", direction → "address" |

So about 20% of likely rows are useful, and 33% have the right sense. The errors are mostly rare
labelled senses (slang, technical, dialect) that win by a small margin (0.03–0.10), or a margin
of 1.0 when the part of speech has no current sense (ago, daily and least as adjectives;
substantive as a verb for a noun). The margin does not separate right from wrong: right rows have
margins from 0.03 to 1.0 as well. The likely tier is a review queue, not a candidate for
`--apply`.

**Data issue found:** `victorian_wordlist.tsv` tags remark → xorjui ("noticed") as a noun
(`eng_tags = n`), but both glossary occurrences are verbs. `sync` takes the analyser's first
reading.

## 6. Next steps

1. Score each sense by its better source instead of the average (aimed at the 79% either-source ceiling).
2. Limit corpus scans to period-sensitive words (dated-sense lemmas, the word list's `period` layer).
3. Link senses to Esperanto more often: more Rhodes/O'Connor cue matching, and Velázquez's numbered senses matched to Webster's.
4. Label a large open eng-epo/eng-spa corpus through the pivots and build translation-time prototypes; evaluate on the 1,045 silver items by coverage band.
5. Prepositions go to the planned fe/de/per/in classifier; suffix, voice and gender choices need syntax features.

## 7. Handover (end of the 2026-11-21 session)

**Nothing is committed and nothing is running** (checked again at the end of the session). The work tree holds:

- Modified: `time-machine/period_dicts.py` (now imports `period_dict_entries.py`; its loaded dictionaries were checked identical) and `time-machine/victorian_wordlist.py` (now imports `wordlist_tags.py`; `sync` gave identical output on scratch copies).
- New scripts: all files in the table below.
- New outputs: `time-machine/macberth_map_report*.txt`, `period_sense_probe_items.tsv`, `period_sense_probe_report.txt`, `webster_sense_probe_items.tsv`, `period_glb_the_time_machine.tsv`.

Commit by the atomic-commit rule (only files changed in lockstep together). One possible grouping:

1. `period_dict_entries.py` + `period_dicts.py`
2. `wordlist_tags.py` + `victorian_wordlist.py`
3. `bert_words.py` + `macberth_map.py`
4. `period_senses.py` + the probes
5. `period_glb.py`
6. `CONTEXTUAL_WSD.md`

Ask the user before committing.

**Changes made during the 2026-11-21 session** (sections 2, 3 and 5 now hold the numbers measured after them):

1. **Sub-sense keying bug fixed.** Wiktionary senses are now keyed on their last, specific gloss, not on `glosses[0]`, which for sub-senses is the parent heading ("Homosexual:" for 10 senses of gay). Before the fix such senses missed their quotation years.
2. **Sense groups.** `period_senses.choose()` picks the Wiktionary sense group first, then its member. It is used in `period_glb.py` and is the "grouped" condition in `period_sense_probe.py`.
3. **Modern-year prior.** From 1950 on, senses tagged dated/archaic/obsolete or Webster [Obs.]/[Archaic] get −1.
4. **Webster joining** compares 5-letter stems with colour/color folded. A weak match (≥ 0.15) may join when it is clearly unique.
5. **Synonym substitution:** senses without examples borrow their definition-synonyms' Wiktionary examples, labelled "synonym substitution". 117 senses gained examples; 1,169 still have none.
6. **Encoder by year** in `period_glb.py`: MacBERTh before 1950, mBERT from 1950 (`PERIOD_GLB_MODERN`). MacBERTh misses the modern sense of gay: 1 of 3 modern sentences, against 2 of 3 for mBERT and RoBERTa-large. The probe does not do this yet.
7. **Tighter candidate filter in `period_glb.py`** (section 5): "last quoted before 1950" needs at least two dated quotations (`QUOTES_MIN`); the old sense must be in a part of speech the word has in the text; an old pick is kept only when its group beats the best current group by `MARGIN`. The Time Machine run prints a table of the filter variants.

**Done (second half of the session):** the gold probe was rerun (65.2% on 89 items against 63.2% on 87, section 2), and the pipeline was rerun with the new filter (1,245 proposals in 8.5 min, section 5). The proposals file `time-machine/period_glb_the_time_machine.tsv` now holds the new run. `--apply` was not run.

**Pending, in order:**

1. **The likely tier is about 20% precise** (8 of 40 useful). Before any `--apply`, try:
   - Do not tier a sense *likely* when its prototype is only a gloss fallback or synonym substitution. Rare slang/technical senses (rag "banknote", hook "pickpocket") look like they win this way; check it by writing the example source into the proposals.
   - Rank by count × margin, and require a margin above 0.1 for single occurrences.
   - When the part of speech has no current sense (margin 1.0: ago, daily, least as adjectives), check the spaCy part of speech before proposing.
   - Measure each change on the same 40-row sample (seed 20261121) plus the glossary recall.
2. The two-quotation rule loses three correct single-quotation senses (accession, nerve, start). A middle way: one quotation is enough when the sense is also Webster-joined.
3. gay results with fixes 1–4 (MacBERTh, 8 test sentences): period 3 of 5 right (robes, hedges, merry); gayly → promiscuous and "a gay life" → quick, fast both wrong.
   - Webster's "Loose; dissipated; lewd" still has no examples: none of its synonyms qualify.
4. The translation-time prototype experiment of section 4 was proposed; the user has not answered yet.
5. **Data question for the user:** `victorian_wordlist.tsv` tags remark → xorjui ("noticed") as a noun, but the glossary occurrences are verbs. Not changed.

**Storage:**

- `/dev/sdb2` (repo + Hugging Face cache) has about 2.4 GB free. MacBERTh weights (439 MB) are in the Hugging Face cache there.
- Embedding caches: `/media/paleos/Warehouse2/Language/Claude/period_glb/` (3.1 GB; MacBERTh, mBERT, RoBERTa-large shards). Reruns reuse them.
- Never write large caches to the repo drive.

## Files

| Path | What |
|---|---|
| `GlobasaTranslation/apertium-glb-eng/test/pivot_oracle.py` | gloss-label ceiling |
| `GlobasaTranslation/apertium-glb-eng/test/sibling_pivot.py` | sibling-translation labels, SimAlign, own tagger pipelines |
| `time-machine/bert_words.py` | word vectors, cached embedding |
| `time-machine/macberth_map.py` | MacBERTh → mBERT map (`MAP_PERIOD=sources` keeps the works unseen) |
| `time-machine/period_senses.py` | pooled sense inventory, year prior, dictionary links, Globasa candidates |
| `time-machine/period_dict_entries.py` | Rhodes / O'Connor / Velázquez loaders (`period_dicts.py` now imports them) |
| `time-machine/period_sense_probe.py` | gold test and scan of the works |
| `time-machine/webster_sense_probe.py` | Webster 1913 inventory test |
| `time-machine/translation_sense_probe.py` | period translators' words as sense evidence |
| `time-machine/wordlist_tags.py` | word-list helpers shared by `victorian_wordlist.py` and `period_glb.py` |
| `time-machine/period_glb.py` | the proposals pipeline |

Caches:

- Git-ignored: `time-machine/cache/`, and `lovecraft/private/` for *At the Mountains of Madness*, which is in copyright.
- Large files on `/media/paleos/Warehouse2/Language/Claude`: MacBERTh vector caches and the `period_glb` embeddings.
- The repo drive (`/dev/sdb2`) is nearly full.
