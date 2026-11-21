# English "the" → Globasa ∅ or hin/den: how far does the existing coref output get?

Script: `definiteness/coref_the.py`, with one row per "the" NP in `definiteness/the_items.tsv`. The coref is the stanza GUM model already served by `GlobasaTranslation/apertium-glb-eng/eng-nlp-service.py`; no new models were used. The gold is *Short Stories by Vanege, Globasa – English* (2026-11-21).

## Result

| | |
|---|---|
| "the" NPs | 209 |
| aligned to a Globasa noun through the word-list gloss | 163 (46 unaligned: compounds, derived words, paraphrases) |
| Globasa ∅ | 157 |
| Globasa hin/den | 6 as labelled; **4 after hand-checking** (see below) |

The best coref-only rules:

| rule | tp | fp | fn | precision | recall |
|---|---:|---:|---:|---:|---:|
| R0 always ∅ | 0 | 0 | 6 | – | 0 |
| R1 anaphoric (has an earlier mention) | 5 | 123 | 1 | 0.04 | 0.83 |
| R2 anaphoric, previous mention ≤ 2 sentences back | 4 | 91 | 2 | 0.04 | 0.67 |
| R3 R2 and (a rival same-head chain or not the subject) | 1 | 30 | 5 | 0.03 | 0.17 |
| R4 R2 and the antecedent was "a N" | 1 | 5 | 5 | 0.17 | 0.17 |

**The existing coref output alone can't support a demonstrative rule.** In this gold, 128 of the 163 "the" NPs are anaphoric, and Globasa keeps 123 of them bare. Every rule that inserts hin/den makes at least 5 errors for each correct demonstrative. "Always ∅" is right 96% of the time.

## What the data says about Globasa
- **Vanege's Globasa behaves like Russian, not like Jenks's Mandarin.** An anaphoric definite is almost always a bare noun, in subject position (4 of 101 are dem), object position (1 of 13) and obliques alike. The subject/topic exception that Dayal & Jiang describe doesn't distinguish anything here, because the bare noun is the default everywhere.
- **The demonstratives that do occur are marked choices.** A referent comes back after one sentence about something else (*Hin juni rubahe*: "the young foxes" after "they jump, dig and roll"). A referent is re-described (*Hin neo drevo* for the earlier "seed"). An object introduced with "a" is picked up again (*Hin sadafa*). These are the "re-activation" cases of the Givenness Hierarchy. Four examples are too few to make a rule from.
- **About half of the Globasa hin/den (16 of 35) appear as this/that/these/those in the English**, so the existing bidix already handles them. The hard "the" cases are rare.

## Check of the gold labels
- **Sample:** of 30 randomly sampled labelled items, 29 are correct.
- **Errors among the 6 dem labels:** 2 are wrong because the 3-token window reached into a neighbouring NP. In "The other birds" ← *den normakal piu*, the den belongs to "this unusual bird". In "the colorblind bird" ← *den coxo lawfen*, the den belongs to "these taunts". Corrected, there are 4 dem labels.
- **Missing English:** 12 Globasa rows have no English, so their hin/den were not scored.
- **The English is itself a translation** (of the Esperanto originals by way of Globasa), so its "the" partly mirrors Esperanto *la*.

## Recommendation
1. **Keep ∅ as the eng→glb default for "the".** This is the current behaviour, and the coref data confirms it. Translationese studies point the same way: translations overuse demonstratives (Kunilovskaya et al. 2021).
2. **Hold back any coref-triggered hin/den** until there are more positive examples. The candidate rule is narrow: an anaphoric NP whose head differs from the antecedent's, or whose antecedent was "a N", with 2–3 sentences in between. It needs tens of positives to test. Those would come from the pivots in the original plan (zho/tha/ind Bible verse alignments) or from more Globasa text with English (Doxo).
3. If the pivot study goes ahead, tighten the labeller first so that only adjectives may stand between hin/den and the noun.
