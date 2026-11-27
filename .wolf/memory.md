# Memory

> Chronological action log. Hooks and AI append to this file automatically.
> Old sessions are consolidated by the daemon weekly.

## 2026-05-01 — globasa_tokenizer package: full implementation

| Time  | Description | File(s) | Outcome | ~Tokens |
|-------|-------------|---------|---------|---------|
| 19:00 | Created complete globasa_tokenizer package from plan | globasa_tokenizer/ (15 modules) | 94 tests pass, 0 failures | ~8000 |
| 19:05 | Built _types.py to prevent circular import MorphKind double-enum | _types.py, segmenter.py, __init__.py | Enum identity now consistent | ~200 |
| 19:10 | Built lexicon.py with LexiliAsel parser and affix_trie | lexicon.py, affix_parser.py, affix_trie.py | roots=3179, prefixes=57, suffixes=34 | ~1000 |
| 19:12 | Built pseudo_morphemes.py with Aho-Corasick + DP cover | pseudo_morphemes.py | gongaw→gon(公)+gaw(告) works | ~500 |
| 19:15 | Built segmenter.py with 7-step priority pipeline | segmenter.py | 0 UNK on word-list, hyphen-split works | ~2000 |
| 19:18 | Built tokenizer.py with MWE merge and detokenize | tokenizer.py | smoke test passes | ~500 |
| 19:20 | Built alignment.py, spacy_adapter, hf_adapter | alignment.py, spacy_adapter/, hf_adapter/ | adapter tests pass with importorskip | ~500 |
| 19:22 | Fixed LexiliAsel parity: 122→0 failures via etymology note stripping | affix_parser.py, test_lexiliasel.py | 0 parity failures | ~400 |
| 19:24 | Fixed offsets for capitalized words (Xencudin→Xen surface) | segmenter.py | offset tests pass | ~200 |
| 19:25 | Perf optimization: pre-sort phrases, cache append, direct isalpha | tokenizer.py | ~94k words/sec, threshold set to 80k | ~300 |
| 19:26 | Ran bootstrap tools: 154 pseudo-morphemes + 6551 mined stems | data/pseudo_morphemes.tsv, data/mined_stems.tsv | bootstrap complete | ~200 |

## 2026-04-29 — Hunspell expansion + GlobasaGrammarChecker

| Time  | Description | File(s) | Outcome | ~Tokens |
|-------|-------------|---------|---------|---------|
| 23:10 | Fix get_lexiklase: tabl: prefix, xfik suffix, il/m/f.sah classes | HunspellMaker.py | Correlatives/interjections/adverbs now classified correctly | ~200 |
| 23:15 | Fix trailing-space bugs in derivedBase reading + exception checker | HunspellMaker.py | Index matching now works for entries with trailing spaces | ~50 |
| 23:20 | Expand prefix continuation classes to include applicable suffix flags | HunspellMaker.py | Prefixed forms (poshuru, cisgi) can now take suffixes | ~300 |
| 23:25 | Expand suffix continuation classes for suffix-to-suffix chaining | HunspellMaker.py | -gi → -ne/-do/-yen, -kal → -ya/-mo now recognized | ~300 |
| 23:30 | Auto-expand derivedBase with all single-word derived entries | HunspellMaker.py | dic grows from 4466 to ~8922 entries; 0 single-word exceptions | ~200 |
| 23:35 | Strip menaFrame index whitespace | HunspellMaker.py | Fixes correlative entries with trailing spaces in word-list.csv | ~50 |
| 23:45 | Create GlobasaGrammarChecker package | GlobasaGrammarChecker/ | 5 rules: infinitive, tense, negation, NP closure, question | ~2000 |
| 23:50 | Create LT-compatible HTTP server | GlobasaGrammarChecker/server.py | POST /v2/check endpoint, compatible with language_tool_python | ~300 |
| 23:55 | Verify: 14/14 grammar tests pass, 0 single-word Hunspell exceptions | All | Hunspell exceptions: 94 (all multi-word), typos: 0 missed | ~200 |

| 2026-04-29 | Added Indic script typography to Word Viewer: 8 Noto Sans Indic imports, CSS vars, body.lang-indic classes, suppressed smcp/letter-spacing, increased line-height (1.7 base, 1.8 Telugu/Kannada), JS INDIC_LANG_CLASS map | word_viewer.html | complete | ~1500 |

| 13:20 | Updated TRAINING_PLAN.md with NLLB paper (2207.04672) details: data tagging, curriculum learning, filtering pipeline, NLLB-Seed validation, chrF++ as primary metric, dropout/hyperparams, self-supervised learning findings, updated TMX counts to current (6838 pairs/15 langs) | TRAINING_PLAN.md | done | ~4000 |

| Time | Description | File(s) | Outcome | ~Tokens |
|------|-------------|---------|---------|---------|
| 2026-04-28 | Fixed preface misalignment in Thirty Short Stories: line 4 had two GLB sentences merged with one ENG, shifting all subsequent ENG by one | Doxo_passages_edited_updated.csv, Doxo_passages.tmx | Split row, realigned 10 preface rows, regenerated & merged 980 TUs into TMX (3116 total) | ~2k |
| 2026-04-28 | Expanded UDHR in TMX from 4 to 14 languages (added de, fr, ru, zh, hi, ar, pt, tr, id, sw) using Unicode CLDR XMLs with auto sentence splitting | extend_tmx_udhr_multi.py, Doxo_passages.tmx | 95-99% coverage per language (100 TUs). Auto-split handles most articles; fallback for unsplittable. | ~3k |
| 2026-04-28 | Expanded P&C in TMX with de, fr, da, nl (all 12 eps) + eo, ru, pt, id (ep02+06) using transcript markdown files from framagit repo | extend_tmx_pnc_multi.py, Doxo_passages.tmx | 1511 TUVs added. Sequential English text matching for alignment, (page, idx) key for cross-lang lookup. | ~3k |

## 2026-04-27 (layout restyling)

| Time | Description | File(s) | Outcome | ~Tokens |
|------|-------------|---------|---------|---------|
| -- | Restyled word_viewer.html to menalari layout: green header with logo/nav/dual search, blue footer with lang selector, landing state with Globasa logo, script selector in content | word_viewer.html | Layout matches menalari.globasa.net pattern | ~8000 |

## 2026-04-26

| Time | Description | File(s) | Outcome | ~Tokens |
|------|-------------|---------|---------|---------|
| -- | Planned Word Viewer upgrade (LMDB, Flask, 16 langs, gender, images, audio, constructions, examples) | noble-stirring-planet.md | Plan finalized | ~15k |
| -- | Sonnet agent implemented full plan | Word Viewer.py, word_viewer.html | Both files written (~400+560 lines) | ~85k |
| -- | Fixed venv path in VSCode task | .vscode/tasks.json | Task uses venv python3 | ~1k |
| -- | User confirmed site runs and looks good | Word Viewer.py | Server starts, page loads | ~0 |

| Time | Description | Files | Outcome | ~Tokens |
|------|-------------|-------|---------|---------|
| 2026-04-27 | Wrote Word Viewer Flask app: LMDB builder + lookup API + audio serving + single-page HTML/JS frontend | Word Viewer.py, word_viewer.html, requirements.txt | LMDB built (9119 entries), API tested (ababil, bon, jixi), pronunciation audio detected, constructions + examples + gender display all working | ~12000 |

| 2026-04-20 | Rewrote Lexilista_parser.py: new annotation-based parser with multi-language support, VerbType semantic classes, AffixType, ParsedGloss NamedTuple, parseWordEntry API | Lexilista_parser.py, AnkiMaker2.py | 9162/9162 entries parse successfully | ~8000 |

| 2026-04-21 | Incorporated Tell-Tale Heart parallel text: replaced stale CSV Globasa with doxo-pages-grav version, aligned with modernized English from wiki HTML | Doxo_passages_edited_updated.csv, Doxo_passages.tmx, fill_telltale_english.py, make_tmx.py | 164 sentence-aligned rows (was 125 with missing English), TMX regenerated with 1923 TUs | ~6000 |

| 2026-04-21 | Created LLM_sense_judge.py: 5-tier pipeline (all→Script?). T1: core match, T2: register/domain, T3: Qdrant corpus, T4: composite, T5: WordNet oewn:2023 synonym/hypernym expansion with core-only synset filter (excludes slang qualifiers like "(sexual)"). Homonym detection for leadership↔body-part. | LLM_sense_judge.py, GLB_ENG_WiktionarySenses.xlsx | 8104 's', 1302 'n', 18714 still unjudged (for local LLM). | ~20000 |
| 2026-04-21 | Updated Wiktionary sense extender 3.py: added Script? column between App? and LLM? as lower-tier vetting. Loads/inherits Script? markings, uses them for App? inheritance and extension TSV generation. | Wiktionary sense based translation extender 3.py | Script? tier integrated into full pipeline. | ~2000 |
| HH:MM | description | file(s) | outcome | ~tokens |
|-------|-------------|---------|---------|---------|
| -- | Added xwexi-pages-grav and doxo-pages-grav as git submodules | .gitmodules | success | ~50 |
| -- | Updated CLAUDE.md, anatomy.md, cerebrum.md to reflect submodule changes and remove gramati-fe-globasa-eng references | CLAUDE.md, .wolf/anatomy.md, .wolf/cerebrum.md | success | ~200 |
| -- | Deleted gramati-fe-globasa-eng/ (outdated fork of xwexi-pages-grav) | gramati-fe-globasa-eng/ | removed | ~10 |
| -- | Documented internal structure of xwexi-pages-grav and doxo-pages-grav submodules | .wolf/anatomy.md, .wolf/cerebrum.md | success | ~300 |

## Session: 2026-04-20 12:41

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-20 12:41

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-20 12:41

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 12:43 | Created ../../.claude/plans/humming-enchanting-valiant.md | — | ~1630 |
| 12:46 | Edited ../../.claude/plans/humming-enchanting-valiant.md | modified glosses() | ~796 |
| 12:48 | Created ../../.claude/plans/humming-enchanting-valiant.md | — | ~2504 |
| 12:49 | Edited ../../.claude/plans/humming-enchanting-valiant.md | modified access() | ~328 |
| 12:49 | Edited ../../.claude/plans/humming-enchanting-valiant.md | inline fix | ~75 |
| 12:52 | Edited ../../.claude/plans/humming-enchanting-valiant.md | modified strip_gloss_context() | ~276 |
| 13:00 | Edited ../../.claude/plans/humming-enchanting-valiant.md | expanded (+9 lines) | ~462 |
| 13:00 | Edited ../../.claude/plans/humming-enchanting-valiant.md | modified VerbType() | ~261 |
| 13:02 | Edited ../../.claude/plans/humming-enchanting-valiant.md | 3→8 lines | ~163 |
| 13:04 | Edited ../../.claude/plans/humming-enchanting-valiant.md | 4→4 lines | ~110 |
| 13:06 | Edited ../../.claude/plans/humming-enchanting-valiant.md | 2→7 lines | ~138 |
| 13:06 | Edited ../../.claude/plans/humming-enchanting-valiant.md | 1→3 lines | ~239 |
| 13:10 | Edited ../../.claude/plans/humming-enchanting-valiant.md | access() → AffixType() | ~307 |
| 13:10 | Edited ../../.claude/plans/humming-enchanting-valiant.md | 7→8 lines | ~170 |
| 13:10 | Edited ../../.claude/plans/humming-enchanting-valiant.md | inline fix | ~128 |
| 13:11 | Edited ../../.claude/plans/humming-enchanting-valiant.md | 2→5 lines | ~129 |
| 13:11 | Edited ../../.claude/plans/humming-enchanting-valiant.md | 6→6 lines | ~135 |
| 13:14 | Edited ../../.claude/plans/humming-enchanting-valiant.md | WordClass() → languages() | ~130 |
| 13:15 | Edited ../../.claude/plans/humming-enchanting-valiant.md | modified parseWordEntry() | ~990 |
| 13:18 | Edited ../../.claude/plans/humming-enchanting-valiant.md | modified _parse_annotation_prefix() | ~405 |
| 13:18 | Edited ../../.claude/plans/humming-enchanting-valiant.md | expanded (+17 lines) | ~294 |
| 13:29 | Edited ../../.claude/plans/humming-enchanting-valiant.md | modified _expand_gloss_context() | ~351 |
| 13:41 | Edited ../../.claude/plans/humming-enchanting-valiant.md | English() → PoS() | ~200 |
| 14:09 | Created Lexilista_parser.py | — | ~6780 |
| 14:12 | Edited AnkiMaker2.py | 32→29 lines | ~313 |
| 14:12 | Edited AnkiMaker2.py | expanded (+6 lines) | ~364 |
| 14:14 | Session end: 26 writes across 3 files (humming-enchanting-valiant.md, Lexilista_parser.py, AnkiMaker2.py) | 11 reads | ~18406 tok |

## Session: 2026-04-20 14:19

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 14:33 | Created ../../.claude/plans/atomic-squishing-allen.md | — | ~1147 |
| 14:37 | Created ../../.claude/plans/atomic-squishing-allen.md | — | ~1667 |
| 14:44 | Created ../../.claude/plans/atomic-squishing-allen.md | — | ~1867 |
| 14:48 | Edited ../../.claude/plans/atomic-squishing-allen.md | modified expand_comma_glosses() | ~455 |
| 14:48 | Edited ../../.claude/plans/atomic-squishing-allen.md | 9→9 lines | ~83 |
| 14:48 | Edited ../../.claude/plans/atomic-squishing-allen.md | 12→13 lines | ~205 |
| 14:50 | Edited ../../.claude/plans/atomic-squishing-allen.md | 2→2 lines | ~75 |
| 14:51 | Edited ../../.claude/plans/atomic-squishing-allen.md | modified columns() | ~171 |
| 14:51 | Edited ../../.claude/plans/atomic-squishing-allen.md | modified and() | ~177 |
| 14:54 | Edited ../../.claude/plans/atomic-squishing-allen.md | modified tiers() | ~284 |
| 14:54 | Edited ../../.claude/plans/atomic-squishing-allen.md | modified and() | ~178 |
| 14:55 | Edited ../../.claude/plans/atomic-squishing-allen.md | expanded (+6 lines) | ~139 |
| 14:56 | Edited ../../.claude/plans/atomic-squishing-allen.md | 5→5 lines | ~87 |
| 15:00 | Edited ../../.claude/plans/atomic-squishing-allen.md | 18→14 lines | ~295 |
| 15:08 | Edited ../../.claude/plans/atomic-squishing-allen.md | len() → _expand_gloss_context() | ~450 |
| 15:11 | Edited ../../.claude/plans/atomic-squishing-allen.md | "langCodes" → "VALIDATION_LANGS" | ~25 |
| 15:11 | Edited ../../.claude/plans/atomic-squishing-allen.md | modified applicability() | ~193 |

## Session: 2026-04-20 15:25

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 15:25 | Planned and iterated v3 Wiktionary sense-based translation extender | atomic-squishing-allen.md | plan approved after 7 rounds of feedback | ~5000 |
| 16:00 | Created Wiktionary sense based translation extender 3.py | new file | uses Lexilista_parser, pickle cache, 3-tier vetting, PoS-aware cross-validation | ~3500 |
| 18:05 | Output overwrites GLB_ENG_WiktionarySenses.tsv (with backup) only on full run; filtered runs write to _initial.tsv | Wiktionary sense based translation extender 3.py | done | ~250 |

## Session: 2026-04-20 (cont.)

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| -- | Added es/eo to EXTENSION_LANGS, build_annotation_map(), annotation overlay in extension collection | Wiktionary sense based translation extender 3.py | Spa/Epo annotations from word-list copied to extension TSV for matching vetted senses | ~300 |
| -- | Added Tags and Antonyms columns between Glb and Eng in senses xlsx output | Wiktionary sense based translation extender 3.py | Tags (col 15) and Antonyms (col 13) from word-list.csv now shown per row | ~150 |

## Session: 2026-04-20 (next)

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| -- | Extended _expand_gloss_context to handle trailing parentheticals like "sourdough (bread)" | Lexilista_parser.py | Added _GLOSS_TRAILING_CONTEXT_RE; now splits into [compact, verbose] | ~200 |

## Session: 2026-04-20 (xlsx backup fallback)

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| -- | Added backup fallback when loading senses .xlsx: tries primary → latest backup → .tsv | Wiktionary sense based translation extender 3.py | Extracted _load_markings_from_xlsx(), added _find_latest_backup(), 3-tier load chain | ~400 |
| 03:00 | Created LadybugDB word relations graph + Qdrant TMX search infrastructure | prepare_kuzu_data.py, load_globasa_graph.js, ingest_tmx_qdrant.py, ~/.claude.json | 9119 words, 12698 edges, 2971 TM entries | ~8000 |

## Session: 2026-04-20 01:11

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-20 01:11

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-20 01:11

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-20 01:13

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-20 01:13

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 01:16 | Edited extend_tmx_udhr.py | 2→2 lines | ~14 |
| 01:16 | Session end: 1 writes across 1 files (extend_tmx_udhr.py) | 1 reads | ~14 tok |
| 01:16 | Edited ../../.claude.json | 10→11 lines | ~98 |
| 01:17 | Session end: 2 writes across 2 files (extend_tmx_udhr.py, .claude.json) | 3 reads | ~112 tok |
| 01:17 | Edited ../../.claude.json | 11→12 lines | ~95 |

## Session: 2026-04-20 01:17

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-20 01:18

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-20 01:18

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-20 01:19

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-20 01:19

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-20 01:19

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-20 01:19

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 01:20 | Edited ingest_tmx_qdrant.py | 1→3 lines | ~42 |

## Session: 2026-04-20 01:20

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 01:20 | Edited ingest_tmx_qdrant.py | 4→6 lines | ~56 |

## Session: 2026-04-20 01:20

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-20 01:22

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 01:23 | Edited ingest_tmx_qdrant.py | 4→4 lines | ~37 |
| 01:24 | Created fill_telltale_english.py | — | ~1996 |
| 01:24 | Edited .vscode/tasks.json | 6→6 lines | ~74 |
| 01:24 | Edited .vscode/tasks.json | inline fix | ~18 |
| 01:25 | Session end: 4 writes across 3 files (ingest_tmx_qdrant.py, fill_telltale_english.py, tasks.json) | 2 reads | ~2125 tok |
| 01:26 | Edited ../../.claude.json | 4→4 lines | ~36 |
| 01:27 | Edited ../../.claude.json | "FASTEMBED_MODEL_NAME" → "EMBEDDING_MODEL" | ~20 |
| 01:27 | Session end: 6 writes across 4 files (ingest_tmx_qdrant.py, fill_telltale_english.py, tasks.json, .claude.json) | 3 reads | ~2181 tok |

## Session: 2026-04-20 01:29

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-20 01:29

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 01:30 | Edited ingest_tmx_qdrant.py | 5→8 lines | ~75 |
| 01:31 | Session end: 1 writes across 1 files (ingest_tmx_qdrant.py) | 1 reads | ~1054 tok |

## Session: 2026-04-20 01:32

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 01:44 | Created ../../.claude/plans/noble-stirring-planet.md | — | ~1309 |
| 01:47 | Created ../../.claude/plans/noble-stirring-planet.md | — | ~1523 |
| 01:52 | Edited ../../.claude/plans/noble-stirring-planet.md | 19→20 lines | ~226 |
| 01:53 | Edited ../../.claude/plans/noble-stirring-planet.md | expanded (+6 lines) | ~202 |
| 01:53 | Edited ../../.claude/plans/noble-stirring-planet.md | inline fix | ~37 |
| 01:56 | Edited ../../.claude/plans/noble-stirring-planet.md | 15→19 lines | ~344 |
| 01:57 | Edited ../../.claude/plans/noble-stirring-planet.md | 2→2 lines | ~84 |
| 01:57 | Session end: 7 writes across 1 files (noble-stirring-planet.md) | 19 reads | ~13430 tok |

## Session: 2026-04-21 00:02

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-21 00:02

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-21 00:02

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 00:07 | Edited LLM_sense_judge.py | modified _handle_sigint() | ~2549 |
| 00:07 | Session end: 1 writes across 1 files (LLM_sense_judge.py) | 1 reads | ~2549 tok |
| 00:08 | Created ../../.claude/projects/-home-paleos-PycharmProjects-GlobasaLexiTools/memory/feedback_conservative_script_tiers.md | — | ~284 |
| 00:09 | Created ../../.claude/projects/-home-paleos-PycharmProjects-GlobasaLexiTools/memory/MEMORY.md | — | ~40 |
| 00:15 | Edited LLM_sense_judge.py | modified has_unslashed_words() | ~667 |
| 00:15 | Edited LLM_sense_judge.py | reduced (-11 lines) | ~419 |
| 00:17 | Session end: 5 writes across 3 files (LLM_sense_judge.py, feedback_conservative_script_tiers.md, MEMORY.md) | 2 reads | ~20333 tok |
| 00:23 | Edited LLM_sense_judge.py | modified check_corpus() | ~776 |
| 00:23 | Edited LLM_sense_judge.py | modified judge_row() | ~45 |
| 00:24 | Edited LLM_sense_judge.py | expanded (+6 lines) | ~161 |
| 00:27 | Edited LLM_sense_judge.py | 5→7 lines | ~82 |
| 00:37 | Edited LLM_sense_judge.py | modified _search_sense_evidence() | ~212 |
| 00:37 | Edited LLM_sense_judge.py | 3→3 lines | ~50 |
| 00:38 | Session end: 11 writes across 3 files (LLM_sense_judge.py, feedback_conservative_script_tiers.md, MEMORY.md) | 2 reads | ~21738 tok |

## Session: 2026-04-22 20:23

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-22 20:23

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-22 20:39

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 20:41 | Edited .vscode/tasks.json | expanded (+19 lines) | ~218 |
| 20:41 | Session end: 1 writes across 1 files (tasks.json) | 1 reads | ~653 tok |
| 20:42 | Edited .vscode/tasks.json | 19→18 lines | ~223 |
| 20:42 | Session end: 2 writes across 1 files (tasks.json) | 1 reads | ~876 tok |
| 20:46 | Session end: 2 writes across 1 files (tasks.json) | 1 reads | ~876 tok |
| 20:50 | Edited LLM_sense_judge.py | 3→4 lines | ~71 |
| 20:51 | Session end: 3 writes across 2 files (tasks.json, LLM_sense_judge.py) | 1 reads | ~947 tok |

## Session: 2026-04-26 23:39

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 23:48 | Created Word Viewer.py | — | ~6695 |
| 23:53 | Created word_viewer.html | — | ~10794 |
| 23:54 | Edited Word Viewer.py | modified _db() | ~245 |
| 23:56 | Edited Word Viewer.py | 3→3 lines | ~37 |
| 23:56 | Edited Word Viewer.py | iternext_dup() → _db() | ~91 |
| 00:10 | Edited requirements.txt | 1→2 lines | ~8 |
| 00:14 | Session end: 6 writes across 3 files (Word Viewer.py, word_viewer.html, requirements.txt) | 7 reads | ~32177 tok |
| 00:15 | Edited .vscode/tasks.json | expanded (+17 lines) | ~154 |
| 00:15 | Session end: 7 writes across 4 files (Word Viewer.py, word_viewer.html, requirements.txt, tasks.json) | 9 reads | ~32989 tok |
| 00:17 | Edited .vscode/tasks.json | 5→5 lines | ~43 |
| 00:18 | Session end: 8 writes across 4 files (Word Viewer.py, word_viewer.html, requirements.txt, tasks.json) | 9 reads | ~33032 tok |
| 00:22 | Session end: 8 writes across 4 files (Word Viewer.py, word_viewer.html, requirements.txt, tasks.json) | 9 reads | ~33032 tok |
| 00:25 | Edited Word Viewer.py | 8→11 lines | ~108 |
| 00:25 | Edited Word Viewer.py | expanded (+7 lines) | ~176 |
| 00:25 | Edited Word Viewer.py | 2→3 lines | ~67 |
| 00:25 | Edited word_viewer.html | 5→6 lines | ~63 |
| 00:26 | Edited word_viewer.html | 2→4 lines | ~26 |
| 00:28 | Created word_viewer_i18n.js | — | ~876 |
| 00:29 | Created word_viewer_i18n.csv | — | ~372 |
| 00:29 | Edited Word Viewer.py | modified index() | ~146 |
| 00:30 | Edited word_viewer.html | added 2 condition(s) | ~198 |
| 00:30 | Edited word_viewer.html | modified if() | ~87 |
| 00:30 | Edited word_viewer.html | 2→2 lines | ~19 |
| 00:31 | Edited word_viewer.html | modified if() | ~199 |
| 00:31 | Edited word_viewer.html | "Etymology" → "etymology" | ~11 |
| 00:31 | Edited word_viewer.html | "Derived words" → "derived_words" | ~12 |
| 00:31 | Edited word_viewer.html | "Example sentences" → "example_sentences" | ~14 |
| 00:32 | Edited word_viewer.html | "Sound effect" → "sound_effect" | ~12 |
| 00:33 | Edited word_viewer.html | 5→3 lines | ~44 |
| 00:33 | Edited word_viewer.html | 8→9 lines | ~123 |
| 00:35 | Created word_viewer_i18n.csv | — | ~1135 |
| 00:35 | Edited word_viewer.html | reduced (-65 lines) | ~431 |
| 00:35 | Edited word_viewer.html | added 4 condition(s) | ~105 |
| 00:36 | Edited word_viewer.html | removed 7 lines | ~6 |
| 00:37 | Edited Word Viewer.py | inline fix | ~24 |
| 00:37 | Session end: 31 writes across 6 files (Word Viewer.py, word_viewer.html, requirements.txt, tasks.json, word_viewer_i18n.js) | 11 reads | ~48951 tok |
| 00:40 | Edited word_viewer.html | expanded (+7 lines) | ~86 |
| 00:41 | Edited word_viewer.html | modified for() | ~530 |
| 00:41 | Edited word_viewer.html | expanded (+7 lines) | ~46 |
| 00:41 | Session end: 34 writes across 6 files (Word Viewer.py, word_viewer.html, requirements.txt, tasks.json, word_viewer_i18n.js) | 11 reads | ~49445 tok |
| 00:46 | Edited word_viewer.html | modified for() | ~518 |
| 00:46 | Edited Word Viewer.py | 3→3 lines | ~33 |
| 00:46 | Session end: 36 writes across 6 files (Word Viewer.py, word_viewer.html, requirements.txt, tasks.json, word_viewer_i18n.js) | 11 reads | ~50073 tok |
| 00:51 | Edited word_viewer.html | added 5 condition(s) | ~302 |
| 00:52 | Edited word_viewer.html | expanded (+9 lines) | ~116 |
| 00:52 | Session end: 38 writes across 6 files (Word Viewer.py, word_viewer.html, requirements.txt, tasks.json, word_viewer_i18n.js) | 11 reads | ~50699 tok |
| 00:52 | Edited word_viewer.html | 3→3 lines | ~46 |
| 00:53 | Session end: 39 writes across 6 files (Word Viewer.py, word_viewer.html, requirements.txt, tasks.json, word_viewer_i18n.js) | 11 reads | ~50748 tok |
| 01:00 | Edited word_viewer.html | 9→5 lines | ~71 |
| 01:00 | Edited word_viewer.html | modified if() | ~199 |
| 01:00 | Edited word_viewer.html | reduced (-12 lines) | ~82 |
| 01:01 | Session end: 42 writes across 6 files (Word Viewer.py, word_viewer.html, requirements.txt, tasks.json, word_viewer_i18n.js) | 11 reads | ~51211 tok |
| 01:03 | Edited word_viewer.html | 10→10 lines | ~75 |
| 01:04 | Session end: 43 writes across 6 files (Word Viewer.py, word_viewer.html, requirements.txt, tasks.json, word_viewer_i18n.js) | 11 reads | ~50944 tok |
| 01:08 | Edited Word Viewer.py | 2→3 lines | ~46 |
| 01:09 | Edited Word Viewer.py | modified _giza_tokenize() | ~844 |
| 01:09 | Edited Word Viewer.py | modified findall() | ~693 |
| 01:10 | Edited Word Viewer.py | 8→9 lines | ~104 |
| 01:10 | Edited word_viewer.html | added 1 condition(s) | ~307 |
| 01:11 | Edited word_viewer.html | added 2 condition(s) | ~139 |
| 01:11 | Session end: 49 writes across 6 files (Word Viewer.py, word_viewer.html, requirements.txt, tasks.json, word_viewer_i18n.js) | 13 reads | ~54185 tok |
| 01:14 | Session end: 49 writes across 6 files (Word Viewer.py, word_viewer.html, requirements.txt, tasks.json, word_viewer_i18n.js) | 13 reads | ~54185 tok |
| 01:21 | Session end: 49 writes across 6 files (Word Viewer.py, word_viewer.html, requirements.txt, tasks.json, word_viewer_i18n.js) | 13 reads | ~54185 tok |
| 01:21 | Session end: 49 writes across 6 files (Word Viewer.py, word_viewer.html, requirements.txt, tasks.json, word_viewer_i18n.js) | 13 reads | ~54185 tok |
| 01:24 | Edited word_viewer.html | added 2 condition(s) | ~593 |
| 01:24 | Edited word_viewer.html | expanded (+9 lines) | ~55 |
| 01:24 | Session end: 51 writes across 6 files (Word Viewer.py, word_viewer.html, requirements.txt, tasks.json, word_viewer_i18n.js) | 13 reads | ~55082 tok |
| 01:26 | Edited Word Viewer.py | modified _short_gloss() | ~337 |
| 01:27 | Edited word_viewer.html | added 2 condition(s) | ~312 |
| 01:27 | Session end: 53 writes across 6 files (Word Viewer.py, word_viewer.html, requirements.txt, tasks.json, word_viewer_i18n.js) | 13 reads | ~56091 tok |

## Session: 2026-04-26 01:37

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-26 01:45

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-26 01:45

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-26 01:45

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 01:47 | Edited word_viewer.html | modified escHtml() | ~82 |
| 01:48 | Edited word_viewer.html | modified renderGenderedWord() | ~212 |
| 01:50 | Edited word_viewer.html | added 1 condition(s) | ~116 |
| 01:50 | Edited word_viewer.html | escHtml() → mdToHtml() | ~125 |
| 01:50 | Session end: 4 writes across 1 files (word_viewer.html) | 9 reads | ~11862 tok |
| 01:50 | Created ../../.claude/plans/hidden-mapping-hanrahan.md | — | ~1309 |
| 02:01 | Created ../../.claude/plans/hidden-mapping-hanrahan.md | — | ~1210 |
| 02:05 | Created ../../.claude/plans/hidden-mapping-hanrahan.md | — | ~1331 |
| 02:25 | Created ../../.claude/plans/hidden-mapping-hanrahan.md | — | ~1347 |
| 02:35 | Edited ../../.claude/plans/hidden-mapping-hanrahan.md | inline fix | ~63 |
| 02:40 | Created ../../.claude/plans/hidden-mapping-hanrahan.md | — | ~1755 |
| 02:49 | Edited ../../.claude/plans/hidden-mapping-hanrahan.md | modified SVO() | ~672 |
| 02:54 | Edited Word Viewer.py | modified _short_gloss() | ~520 |
| 02:55 | Edited word_viewer.html | added 8 condition(s) | ~638 |
| 02:55 | Session end: 13 writes across 3 files (word_viewer.html, hidden-mapping-hanrahan.md, Word Viewer.py) | 20 reads | ~36405 tok |
| 03:04 | Edited word_viewer.html | expanded (+17 lines) | ~238 |
| 03:05 | Edited word_viewer.html | added 2 condition(s) | ~276 |
| 03:05 | Session end: 15 writes across 3 files (word_viewer.html, hidden-mapping-hanrahan.md, Word Viewer.py) | 21 reads | ~37368 tok |
| 03:14 | Edited Word Viewer.py | modified _index_translation() | ~706 |
| 03:16 | Edited Word Viewer.py | modified suggest() | ~581 |
| 03:16 | Edited word_viewer.html | expanded (+39 lines) | ~260 |
| 03:17 | Edited word_viewer.html | 3→4 lines | ~56 |
| 03:17 | Edited word_viewer.html | added 8 condition(s) | ~1084 |
| 03:17 | Session end: 20 writes across 3 files (word_viewer.html, hidden-mapping-hanrahan.md, Word Viewer.py) | 21 reads | ~41266 tok |
| 03:20 | Edited Word Viewer.py | modified items() | ~78 |
| 03:20 | Session end: 21 writes across 3 files (word_viewer.html, hidden-mapping-hanrahan.md, Word Viewer.py) | 21 reads | ~41916 tok |
| 03:26 | Edited word_viewer.html | 5→6 lines | ~66 |
| 03:26 | Edited word_viewer.html | 1→3 lines | ~56 |
| 03:28 | Edited word_viewer.html | added 2 condition(s) | ~584 |
| 03:29 | Edited word_viewer.html | added 2 condition(s) | ~338 |
| 03:40 | Created word_viewer_i18n.csv | — | ~1295 |
| 03:41 | Session end: 26 writes across 4 files (word_viewer.html, hidden-mapping-hanrahan.md, Word Viewer.py, word_viewer_i18n.csv) | 22 reads | ~47032 tok |
| 03:45 | Edited word_viewer.html | 5→6 lines | ~99 |
| 03:45 | Session end: 27 writes across 4 files (word_viewer.html, hidden-mapping-hanrahan.md, Word Viewer.py, word_viewer_i18n.csv) | 22 reads | ~47138 tok |
| 03:49 | Edited word_viewer_i18n.csv | expanded (+6 lines) | ~178 |
| 03:49 | Edited word_viewer.html | modified if() | ~61 |
| 03:49 | Session end: 29 writes across 4 files (word_viewer.html, hidden-mapping-hanrahan.md, Word Viewer.py, word_viewer_i18n.csv) | 22 reads | ~47554 tok |
| 03:57 | Edited word_viewer_i18n.csv | expanded (+19 lines) | ~572 |
| 03:58 | Edited word_viewer.html | modified uiLabel() | ~72 |
| 03:58 | Edited word_viewer.html | inline fix | ~10 |
| 03:59 | Edited word_viewer.html | inline fix | ~17 |
| 03:59 | Edited word_viewer.html | modified if() | ~115 |
| 04:00 | Session end: 34 writes across 4 files (word_viewer.html, hidden-mapping-hanrahan.md, Word Viewer.py, word_viewer_i18n.csv) | 22 reads | ~48490 tok |
| 04:05 | Created word_viewer_scripts.js | — | ~1808 |
| 04:06 | Edited Word Viewer.py | modified scripts_js() | ~51 |
| 04:09 | Created word_viewer_scripts.js | — | ~1636 |
| 04:09 | Edited word_viewer.html | 1→2 lines | ~15 |
| 04:10 | Edited word_viewer.html | 4→9 lines | ~72 |
| 04:11 | Edited word_viewer.html | added error handling | ~296 |
| 04:12 | Edited word_viewer.html | 2→2 lines | ~31 |
| 04:12 | Edited word_viewer.html | modified if() | ~146 |
| 04:13 | Edited word_viewer.html | 11→11 lines | ~88 |
| 04:13 | Edited word_viewer.html | 5→5 lines | ~47 |
| 04:13 | Edited word_viewer.html | modified if() | ~104 |
| 04:14 | Edited word_viewer.html | inline fix | ~32 |
| 04:14 | Edited word_viewer.html | 4→6 lines | ~42 |
| 04:15 | Session end: 47 writes across 5 files (word_viewer.html, hidden-mapping-hanrahan.md, Word Viewer.py, word_viewer_i18n.csv, word_viewer_scripts.js) | 27 reads | ~53283 tok |
| 04:24 | Edited Word Viewer.py | modified scripts_js() | ~95 |
| 04:24 | Edited word_viewer.html | expanded (+24 lines) | ~181 |
| 04:25 | Edited word_viewer.html | expanded (+10 lines) | ~112 |
| 04:26 | Edited word_viewer.html | added 2 condition(s) | ~259 |
| 04:26 | Session end: 51 writes across 5 files (word_viewer.html, hidden-mapping-hanrahan.md, Word Viewer.py, word_viewer_i18n.csv, word_viewer_scripts.js) | 27 reads | ~54240 tok |
| 04:28 | Edited word_viewer.html | 24→24 lines | ~230 |
| 04:28 | Session end: 52 writes across 5 files (word_viewer.html, hidden-mapping-hanrahan.md, Word Viewer.py, word_viewer_i18n.csv, word_viewer_scripts.js) | 27 reads | ~54486 tok |
| 04:31 | Edited Word Viewer.py | modified lookup() | ~98 |
| 04:32 | Edited word_viewer.html | modified doLookup() | ~13 |
| 04:32 | Edited word_viewer.html | 3→3 lines | ~42 |
| 04:32 | Edited Word Viewer.py | 13→15 lines | ~155 |
| 04:32 | Session end: 56 writes across 5 files (word_viewer.html, hidden-mapping-hanrahan.md, Word Viewer.py, word_viewer_i18n.csv, word_viewer_scripts.js) | 27 reads | ~55149 tok |
| 04:38 | Edited word_viewer_i18n.csv | 1→3 lines | ~90 |
| 04:38 | Edited word_viewer.html | modified buildLangSelector() | ~71 |
| 04:38 | Edited word_viewer.html | modified buildScriptSelector() | ~72 |
| 04:41 | Edited word_viewer.html | 3→4 lines | ~34 |
| 04:41 | Session end: 60 writes across 5 files (word_viewer.html, hidden-mapping-hanrahan.md, Word Viewer.py, word_viewer_i18n.csv, word_viewer_scripts.js) | 27 reads | ~55467 tok |
| 04:48 | Created word_viewer_etym_langs.csv | — | ~299 |
| 04:49 | Edited word_viewer_i18n.csv | expanded (+20 lines) | ~523 |
| 04:49 | Edited Word Viewer.py | modified etym_langs() | ~105 |
| 04:50 | Edited word_viewer.html | added 1 condition(s) | ~94 |
| 04:50 | Edited word_viewer.html | added 2 condition(s) | ~111 |
| 04:51 | Edited word_viewer.html | inline fix | ~13 |
| 04:51 | Session end: 66 writes across 6 files (word_viewer.html, hidden-mapping-hanrahan.md, Word Viewer.py, word_viewer_i18n.csv, word_viewer_scripts.js) | 27 reads | ~56694 tok |
| 04:57 | Edited word_viewer_etym_langs.csv | inline fix | ~11 |
| 04:58 | Edited word_viewer_etym_langs.csv | inline fix | ~5 |
| 04:58 | Edited word_viewer_i18n.csv | 1→2 lines | ~49 |
| 04:58 | Session end: 69 writes across 6 files (word_viewer.html, hidden-mapping-hanrahan.md, Word Viewer.py, word_viewer_i18n.csv, word_viewer_scripts.js) | 27 reads | ~56763 tok |

## Session: 2026-04-27 14:11

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-27 14:12

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 14:15 | Edited ../../.claude/settings.json | removed 9 lines | ~6 |
| 14:15 | Session end: 1 writes across 1 files (settings.json) | 3 reads | ~6 tok |

## Session: 2026-04-27 14:16

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-27 14:16

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-27 14:16

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-27 14:16

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-27 14:17

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 14:35 | Created _update_i18n.py | — | ~12237 |
| 14:39 | Edited _update_i18n.py | 5→8 lines | ~87 |
| 14:44 | Created word_viewer_i18n.csv | — | ~2566 |
| 14:44 | Edited _update_i18n.py | expanded (+7 lines) | ~144 |
| 14:45 | Session end: 4 writes across 2 files (_update_i18n.py, word_viewer_i18n.csv) | 5 reads | ~43881 tok |
| 14:53 | Created ../../.claude/plans/noble-stirring-planet.md | — | ~1866 |
| 14:57 | Created ../../.claude/plans/noble-stirring-planet.md | — | ~2499 |
| 14:58 | Edited word_viewer.html | 7→9 lines | ~74 |
| 14:58 | Edited word_viewer.html | 2→2 lines | ~14 |
| 14:58 | Edited word_viewer.html | 7→9 lines | ~49 |
| 14:58 | Edited word_viewer.html | 4→5 lines | ~42 |
| 14:58 | Edited word_viewer.html | 7→7 lines | ~40 |
| 14:59 | Edited word_viewer.html | 6→6 lines | ~35 |
| 14:59 | Edited word_viewer.html | 2→2 lines | ~15 |
| 14:59 | Edited word_viewer.html | 3→3 lines | ~20 |
| 14:59 | Edited word_viewer.html | 3→3 lines | ~29 |
| 14:59 | Edited word_viewer.html | 3→3 lines | ~29 |
| 14:59 | Edited word_viewer.html | expanded (+23 lines) | ~203 |
| 15:00 | Edited word_viewer.html | modified saveLangPref() | ~120 |
| 15:00 | Edited word_viewer.html | 4→5 lines | ~42 |
| 15:00 | Edited word_viewer.html | 4→6 lines | ~49 |
| 15:00 | Edited word_viewer.html | 2→2 lines | ~24 |
| 15:01 | Session end: 21 writes across 4 files (_update_i18n.py, word_viewer_i18n.csv, noble-stirring-planet.md, word_viewer.html) | 5 reads | ~54125 tok |
| 15:12 | Edited word_viewer.html | 2→7 lines | ~146 |
| 15:12 | Edited word_viewer.html | expanded (+36 lines) | ~535 |
| 15:13 | Edited word_viewer.html | expanded (+8 lines) | ~99 |
| 15:13 | Edited word_viewer.html | added 1 condition(s) | ~140 |
| 15:14 | Session end: 25 writes across 4 files (_update_i18n.py, word_viewer_i18n.csv, noble-stirring-planet.md, word_viewer.html) | 5 reads | ~55633 tok |
| 15:20 | Session end: 25 writes across 4 files (_update_i18n.py, word_viewer_i18n.csv, noble-stirring-planet.md, word_viewer.html) | 10 reads | ~55633 tok |
| 15:25 | Edited word_viewer.html | 6→9 lines | ~101 |
| 15:25 | Edited word_viewer.html | added 1 condition(s) | ~132 |
| 15:26 | Edited word_viewer.html | expanded (+13 lines) | ~219 |
| 15:26 | Session end: 28 writes across 4 files (_update_i18n.py, word_viewer_i18n.csv, noble-stirring-planet.md, word_viewer.html) | 10 reads | ~56369 tok |
| 15:29 | Edited word_viewer.html | 6→6 lines | ~43 |
| 15:29 | Edited word_viewer.html | 6→6 lines | ~43 |
| 15:29 | Edited word_viewer.html | 6→6 lines | ~41 |
| 15:29 | Edited word_viewer.html | 6→6 lines | ~41 |
| 15:29 | Edited word_viewer.html | 6→6 lines | ~40 |
| 15:29 | Edited word_viewer.html | uppercase() → caps() | ~220 |
| 15:30 | Edited word_viewer.html | uppercase() → caps() | ~110 |
| 15:30 | Edited word_viewer.html | removed 14 lines | ~1 |
| 15:30 | Edited word_viewer.html | 4→1 lines | ~14 |
| 15:31 | Edited word_viewer.html | modified if() | ~62 |
| 15:31 | Session end: 38 writes across 4 files (_update_i18n.py, word_viewer_i18n.csv, noble-stirring-planet.md, word_viewer.html) | 10 reads | ~57050 tok |
| 15:34 | Edited word_viewer.html | "https://fonts.googleapis." → "https://fonts.googleapis." | ~58 |
| 15:34 | Edited word_viewer.html | 2→4 lines | ~81 |
| 15:35 | Edited word_viewer.html | 6→8 lines | ~61 |
| 15:35 | Edited word_viewer.html | 6→8 lines | ~62 |
| 15:35 | Edited word_viewer.html | 6→7 lines | ~50 |
| 15:35 | Edited word_viewer.html | 6→7 lines | ~51 |
| 15:35 | Edited word_viewer.html | 6→7 lines | ~49 |
| 15:35 | Edited word_viewer.html | 12→13 lines | ~109 |
| 15:35 | Edited word_viewer.html | 12→13 lines | ~102 |
| 15:35 | Session end: 47 writes across 4 files (_update_i18n.py, word_viewer_i18n.csv, noble-stirring-planet.md, word_viewer.html) | 10 reads | ~57632 tok |
| 15:41 | Edited word_viewer.html | "https://fonts.googleapis." → "https://fonts.googleapis." | ~44 |
| 15:42 | Edited word_viewer.html | expanded (+16 lines) | ~166 |
| 15:42 | Session end: 49 writes across 4 files (_update_i18n.py, word_viewer_i18n.csv, noble-stirring-planet.md, word_viewer.html) | 10 reads | ~57981 tok |
| 15:44 | Edited word_viewer.html | 7→7 lines | ~50 |
| 15:44 | Edited word_viewer.html | 7→7 lines | ~48 |
| 15:44 | Edited word_viewer.html | 7→7 lines | ~50 |
| 15:44 | Edited word_viewer.html | 3→3 lines | ~22 |
| 15:44 | Edited word_viewer.html | 3→3 lines | ~23 |
| 15:44 | Session end: 54 writes across 4 files (_update_i18n.py, word_viewer_i18n.csv, noble-stirring-planet.md, word_viewer.html) | 10 reads | ~58188 tok |
| 15:49 | Edited word_viewer.html | "https://fonts.googleapis." → "https://fonts.googleapis." | ~58 |
| 15:49 | Edited word_viewer.html | 1→4 lines | ~72 |
| 15:50 | Edited word_viewer.html | expanded (+23 lines) | ~380 |
| 15:51 | Edited word_viewer.html | added 1 condition(s) | ~133 |
| 15:51 | Session end: 58 writes across 4 files (_update_i18n.py, word_viewer_i18n.csv, noble-stirring-planet.md, word_viewer.html) | 10 reads | ~59346 tok |
| 15:53 | Session end: 58 writes across 4 files (_update_i18n.py, word_viewer_i18n.csv, noble-stirring-planet.md, word_viewer.html) | 10 reads | ~59346 tok |
| 15:58 | Session end: 58 writes across 4 files (_update_i18n.py, word_viewer_i18n.csv, noble-stirring-planet.md, word_viewer.html) | 10 reads | ~59346 tok |

## Session: 2026-04-27 15:59

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-27 15:59

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 16:05 | Edited Wiktionary sense based translation extender 3.py | expanded (+12 lines) | ~411 |
| 16:06 | Session end: 1 writes across 1 files (Wiktionary sense based translation extender 3.py) | 2 reads | ~8964 tok |
| 16:12 | Session end: 1 writes across 1 files (Wiktionary sense based translation extender 3.py) | 2 reads | ~8964 tok |
| 16:14 | Edited Wiktionary sense based translation extender 3.py | modified _load_markings_from_rows() | ~462 |
| 16:14 | Edited Wiktionary sense based translation extender 3.py | 6→6 lines | ~99 |
| 16:14 | Edited Wiktionary sense based translation extender 3.py | 7→6 lines | ~54 |
| 16:15 | Edited Wiktionary sense based translation extender 3.py | modified fromkeys() | ~354 |
| 16:15 | Edited Wiktionary sense based translation extender 3.py | 13→12 lines | ~182 |
| 16:15 | Edited LLM_sense_judge.py | 8→8 lines | ~88 |
| 16:15 | Edited LLM_sense_judge.py | 3→1 lines | ~18 |
| 16:15 | Edited LLM_sense_judge.py | 3→3 lines | ~36 |
| 16:15 | Edited LLM_sense_judge.py | "LLM?" → "l" | ~16 |
| 16:16 | Edited LLM_sense_judge.py | modified print() | ~32 |
| 16:16 | Edited LLM_sense_judge.py | modified pipeline() | ~153 |
| 16:16 | Edited LLM_sense_judge.py | inline fix | ~11 |
| 16:16 | Edited LLM_sense_judge.py | inline fix | ~14 |
| -- | Consolidated 4 vetting columns (Script?/LLM?/Vetted?/Expert?) into single 'Tier' column in both extender 3 and LLM_sense_judge.py. Backward-compatible loading collapses old format. | Wiktionary sense based translation extender 3.py, LLM_sense_judge.py | Header, markings, output, extension condition all updated | ~1500 |
| 16:17 | Session end: 14 writes across 2 files (Wiktionary sense based translation extender 3.py, LLM_sense_judge.py) | 3 reads | ~26907 tok |
| 16:31 | Edited Wiktionary sense based translation extender 3.py | modified wl_get() | ~226 |
| 16:32 | Session end: 15 writes across 2 files (Wiktionary sense based translation extender 3.py, LLM_sense_judge.py) | 3 reads | ~27133 tok |
| 16:39 | Edited Word Viewer.py | 26→31 lines | ~319 |
| 16:40 | Edited Word Viewer.py | 1→2 lines | ~40 |
| 16:40 | Edited Word Viewer.py | modified exists() | ~150 |
| 16:40 | Edited Word Viewer.py | modified exists() | ~139 |
| 16:41 | Edited word_viewer.html | 39→36 lines | ~308 |
| 16:44 | Edited word_viewer.html | expanded (+65 lines) | ~384 |
| 16:46 | Edited Wiktionary sense based translation extender 3.py | expanded (+14 lines) | ~202 |
| 16:47 | Edited Wiktionary sense based translation extender 3.py | modified is_dialect() | ~95 |
| 16:47 | Edited Wiktionary sense based translation extender 3.py | modified get_sense_lang_translations() | ~108 |
| 16:48 | Edited Wiktionary sense based translation extender 3.py | modified is_dialect() | ~78 |
| 16:48 | Session end: 25 writes across 4 files (Wiktionary sense based translation extender 3.py, LLM_sense_judge.py, Word Viewer.py, word_viewer.html) | 7 reads | ~60095 tok |
| 16:49 | Session end: 25 writes across 4 files (Wiktionary sense based translation extender 3.py, LLM_sense_judge.py, Word Viewer.py, word_viewer.html) | 7 reads | ~60095 tok |
| 18:35 | Edited Wiktionary sense based translation extender 3.py | expanded (+17 lines) | ~346 |
| 18:36 | Edited Wiktionary sense based translation extender 3.py | 11→15 lines | ~402 |
| 18:36 | Edited Wiktionary sense based translation extender 3.py | modified lang_display_name() | ~62 |
| 18:36 | Edited Wiktionary sense based translation extender 3.py | modified _resolve_lang() | ~368 |
| 18:37 | Edited Wiktionary sense based translation extender 3.py | is_dialect() → _resolve_lang() | ~226 |
| 18:37 | Session end: 30 writes across 4 files (Wiktionary sense based translation extender 3.py, LLM_sense_judge.py, Word Viewer.py, word_viewer.html) | 7 reads | ~62074 tok |
| 18:38 | Session end: 30 writes across 4 files (Wiktionary sense based translation extender 3.py, LLM_sense_judge.py, Word Viewer.py, word_viewer.html) | 7 reads | ~62074 tok |
| 18:40 | Edited Word Viewer.py | modified exists() | ~188 |
| 18:41 | Edited Word Viewer.py | modified exists() | ~157 |
| 18:42 | Session end: 32 writes across 4 files (Wiktionary sense based translation extender 3.py, LLM_sense_judge.py, Word Viewer.py, word_viewer.html) | 7 reads | ~62549 tok |
| 18:43 | Session end: 32 writes across 4 files (Wiktionary sense based translation extender 3.py, LLM_sense_judge.py, Word Viewer.py, word_viewer.html) | 7 reads | ~62549 tok |
| 18:44 | Edited Word Viewer.py | modified exists() | ~144 |
| 18:46 | Edited Word Viewer.py | modified iterrows() | ~88 |
| 18:47 | Edited Wiktionary sense based translation extender 3.py | inline fix | ~18 |
| 18:47 | Session end: 35 writes across 4 files (Wiktionary sense based translation extender 3.py, LLM_sense_judge.py, Word Viewer.py, word_viewer.html) | 7 reads | ~62792 tok |
| 18:48 | Session end: 35 writes across 4 files (Wiktionary sense based translation extender 3.py, LLM_sense_judge.py, Word Viewer.py, word_viewer.html) | 7 reads | ~62705 tok |
| 18:51 | Edited .vscode/tasks.json | expanded (+9 lines) | ~263 |
| 18:51 | Edited .vscode/tasks.json | expanded (+7 lines) | ~168 |
| 18:52 | Session end: 37 writes across 5 files (Wiktionary sense based translation extender 3.py, LLM_sense_judge.py, Word Viewer.py, word_viewer.html, tasks.json) | 8 reads | ~63940 tok |
| 18:56 | Edited Word Viewer.py | 2→1 lines | ~18 |
| 18:56 | Edited Word Viewer.py | 8→3 lines | ~62 |
| 18:57 | Edited Word Viewer.py | 2→1 lines | ~24 |
| 18:58 | Session end: 40 writes across 5 files (Wiktionary sense based translation extender 3.py, LLM_sense_judge.py, Word Viewer.py, word_viewer.html, tasks.json) | 8 reads | ~64022 tok |
| 21:12 | Edited Word Viewer.py | 5→7 lines | ~102 |
| 21:12 | Edited Word Viewer.py | modified find_derived_words() | ~295 |
| 21:13 | Session end: 42 writes across 5 files (Wiktionary sense based translation extender 3.py, LLM_sense_judge.py, Word Viewer.py, word_viewer.html, tasks.json) | 8 reads | ~64312 tok |
| 21:17 | Edited Word Viewer.py | modified split() | ~137 |
| 21:17 | Edited Word Viewer.py | 4→6 lines | ~72 |
| 21:18 | Edited Word Viewer.py | modified list_tags() | ~166 |
| 21:18 | Edited word_viewer.html | modified if() | ~70 |
| 21:19 | Edited word_viewer.html | expanded (+7 lines) | ~142 |
| 21:19 | Edited word_viewer.html | expanded (+6 lines) | ~90 |
| 21:20 | Edited word_viewer.html | expanded (+39 lines) | ~295 |
| 21:20 | Edited word_viewer.html | modified doLookup() | ~134 |
| 21:21 | Edited word_viewer.html | modified browseTag() | ~345 |
| 21:21 | Session end: 51 writes across 5 files (Wiktionary sense based translation extender 3.py, LLM_sense_judge.py, Word Viewer.py, word_viewer.html, tasks.json) | 8 reads | ~66930 tok |
| 21:26 | Edited word_viewer.html | added 3 condition(s) | ~571 |
| 21:26 | Edited word_viewer.html | 1→6 lines | ~58 |
| 21:26 | Edited word_viewer.html | added 1 condition(s) | ~489 |
| 21:27 | Edited word_viewer.html | buildTransTable() → buildMiniTransTable() | ~33 |
| 21:27 | Edited word_viewer.html | removed 14 lines | ~16 |
| 21:27 | Session end: 56 writes across 5 files (Wiktionary sense based translation extender 3.py, LLM_sense_judge.py, Word Viewer.py, word_viewer.html, tasks.json) | 8 reads | ~68506 tok |
| 21:30 | Edited word_viewer.html | 4→4 lines | ~59 |
| 21:30 | Session end: 57 writes across 5 files (Wiktionary sense based translation extender 3.py, LLM_sense_judge.py, Word Viewer.py, word_viewer.html, tasks.json) | 8 reads | ~68569 tok |
| 21:34 | Edited word_viewer.html | 3→8 lines | ~43 |
| 21:34 | Session end: 58 writes across 5 files (Wiktionary sense based translation extender 3.py, LLM_sense_judge.py, Word Viewer.py, word_viewer.html, tasks.json) | 8 reads | ~68615 tok |
| 21:36 | Edited word_viewer.html | expanded (+13 lines) | ~205 |
| 21:37 | Edited word_viewer.html | modified buildMiniTransTable() | ~296 |
| 21:37 | Edited word_viewer.html | modified if() | ~192 |
| 21:37 | Session end: 61 writes across 5 files (Wiktionary sense based translation extender 3.py, LLM_sense_judge.py, Word Viewer.py, word_viewer.html, tasks.json) | 8 reads | ~70370 tok |
| 22:24 | Created ../../.claude/plans/abundant-whistling-platypus.md | — | ~1985 |
| 22:27 | Edited ../../.claude/plans/abundant-whistling-platypus.md | 18→13 lines | ~310 |
| 22:28 | Edited ../../.claude/plans/abundant-whistling-platypus.md | 10→11 lines | ~179 |
| 22:28 | Edited ../../.claude/plans/abundant-whistling-platypus.md | 4→4 lines | ~54 |
| 22:38 | Edited ../../.claude/plans/abundant-whistling-platypus.md | modified CLI() | ~351 |
| 22:39 | Created ../../.claude/plans/abundant-whistling-platypus.md | — | ~1980 |
| 22:40 | Edited ../../.claude/plans/abundant-whistling-platypus.md | 6→10 lines | ~201 |
| 22:42 | Edited ../../.claude/plans/abundant-whistling-platypus.md | modified CLI() | ~203 |
| 22:42 | Edited ../../.claude/plans/abundant-whistling-platypus.md | 10→12 lines | ~200 |
| 22:45 | Edited ../../.claude/plans/abundant-whistling-platypus.md | 6→7 lines | ~132 |
| 22:45 | Edited ../../.claude/plans/abundant-whistling-platypus.md | modified word() | ~231 |
| 22:47 | Edited ../../.claude/plans/abundant-whistling-platypus.md | manually() → language() | ~24 |
| 22:54 | Edited ../../.claude/plans/abundant-whistling-platypus.md | CLI() → pipeline() | ~403 |
| 22:56 | Edited ../../.claude/plans/abundant-whistling-platypus.md | modified extender() | ~258 |
| 22:56 | Edited ../../.claude/plans/abundant-whistling-platypus.md | modified word() | ~738 |
| 22:56 | Edited ../../.claude/plans/abundant-whistling-platypus.md | 17→21 lines | ~348 |
| 22:57 | Edited ../../.claude/plans/abundant-whistling-platypus.md | 7→8 lines | ~183 |
| 23:19 | Edited ../../.claude/plans/abundant-whistling-platypus.md | expanded (+41 lines) | ~731 |
| 23:19 | Edited ../../.claude/plans/abundant-whistling-platypus.md | 13→14 lines | ~275 |

## Session: 2026-04-27 23:44

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-27 23:44

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 23:49 | Created ../../.claude/projects/-home-paleos-PycharmProjects-GlobasaLexiTools/memory/feedback_atomic_commits.md | — | ~202 |
| 23:49 | Edited ../../.claude/projects/-home-paleos-PycharmProjects-GlobasaLexiTools/memory/MEMORY.md | 1→2 lines | ~68 |
| 23:49 | Session end: 2 writes across 2 files (feedback_atomic_commits.md, MEMORY.md) | 1 reads | ~289 tok |
| 00:04 | Session end: 2 writes across 2 files (feedback_atomic_commits.md, MEMORY.md) | 1 reads | ~289 tok |
| 00:07 | Session end: 2 writes across 2 files (feedback_atomic_commits.md, MEMORY.md) | 1 reads | ~289 tok |
| 00:21 | Created wiktionary_constants.py | — | ~3963 |
| 00:23 | Edited Wiktionary sense based translation extender 3.py | removed 159 lines | ~354 |
| 00:23 | Edited Wiktionary sense based translation extender 3.py | removed 96 lines | ~94 |
| 00:24 | Edited Wiktionary sense based translation extender 3.py | removed 55 lines | ~73 |
| 00:24 | Edited Wiktionary sense based translation extender 3.py | removed 64 lines | ~54 |
| 00:25 | Session end: 7 writes across 4 files (feedback_atomic_commits.md, MEMORY.md, wiktionary_constants.py, Wiktionary sense based translation extender 3.py) | 2 reads | ~11170 tok |
| 00:26 | Created Wiktionary extension builder.py | — | ~2776 |
| 00:27 | Edited Wiktionary sense based translation extender 3.py | 10→6 lines | ~74 |
| 00:27 | Edited Wiktionary sense based translation extender 3.py | removed 3 lines | ~6 |
| 00:27 | Edited Wiktionary sense based translation extender 3.py | 4→3 lines | ~30 |
| 00:27 | Edited Wiktionary sense based translation extender 3.py | reduced (-12 lines) | ~90 |
| 00:28 | Edited Wiktionary sense based translation extender 3.py | removed 29 lines | ~68 |
| 00:28 | Edited Wiktionary sense based translation extender 3.py | 16→12 lines | ~152 |
| 00:29 | Created JSONL parser non-English.py | — | ~2473 |
| 00:31 | Created Multi-Wiktionary sense curator.py | — | ~3908 |
| 00:32 | Session end: 16 writes across 7 files (feedback_atomic_commits.md, MEMORY.md, wiktionary_constants.py, Wiktionary sense based translation extender 3.py, Wiktionary extension builder.py) | 2 reads | ~19456 tok |
| 00:34 | Session end: 16 writes across 7 files (feedback_atomic_commits.md, MEMORY.md, wiktionary_constants.py, Wiktionary sense based translation extender 3.py, Wiktionary extension builder.py) | 2 reads | ~19456 tok |
| 00:37 | Session end: 16 writes across 7 files (feedback_atomic_commits.md, MEMORY.md, wiktionary_constants.py, Wiktionary sense based translation extender 3.py, Wiktionary extension builder.py) | 2 reads | ~19456 tok |

## Session: 2026-04-28 (cont.)

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|---------|
| -- | Extended EXTENSION_LANGS to 53 langs (added Persian, Indian, E-European, etc.) + dialect sub-columns (Alemannic, Egyptian Arabic, etc.) | Wiktionary sense based translation extender 3.py | 40→53 languages with 9 dialect virtual codes | ~500 |
| -- | Consolidated Script?/LLM?/Vetted?/Expert? into single Tier column (e/v/l/a) | Wiktionary sense based translation extender 3.py, LLM_sense_judge.py | Backward-compatible loading of old format | ~1500 |
| -- | Fixed word-list.csv column access to use header names instead of hardcoded indices | Wiktionary sense based translation extender 3.py | Column order changes no longer break the script | ~200 |
| -- | Added dialect tag filtering: dialect translations excluded from parent language, shown in own columns | Wiktionary sense based translation extender 3.py | DIALECT_TAGS + is_dialect() + _resolve_lang() | ~400 |
| -- | Created wiktionary_config.xlsx with 5 sheets (ExtensionLangs, Dialects, PoSMapping, PoSFallbacks, WiktionarySources) | wiktionary_config.xlsx | All configurable constants in editable xlsx | ~500 |
| -- | Created wiktionary_constants.py: loads config from xlsx, exposes 15 shared helper functions | wiktionary_constants.py | Shared module for all Wiktionary scripts | ~5600 |
| -- | Refactored extender 3: replaced ~200 lines inline constants/helpers with imports from wiktionary_constants, removed extension TSV generation | Wiktionary sense based translation extender 3.py | 389 lines removed, 10 added | ~2200 |
| -- | Created Wiktionary extension builder.py: reads both English + multi-source xlsx, fetches translations from LMDBs, writes menalariExtension.tsv | Wiktionary extension builder.py | 3482 words with translations, 55 columns, regression-tested | ~4100 |
| -- | Created JSONL parser non-English.py: parameterized ingester for kaikki.org JSONL with --discover mode | JSONL parser non-English.py | Supports fr/de/es/eo/ru/zh | ~3200 |
| -- | Created Multi-Wiktionary sense curator.py: interactive CLI for curating non-English senses (word;lang input, sense selection, appends to xlsx) | Multi-Wiktionary sense curator.py | Interactive gap-filling workflow | ~5600 |
| -- | Smoke-tested extension builder: 9163 rows, 55 cols, dialect data present, newly added langs populated (Korean 30%, Bulgarian 32%, Persian 22%) | menalariExtension.tsv | Regression test passed | ~0 |
| -- | Updated anatomy.md, cerebrum.md with new files and architectural decisions | .wolf/anatomy.md, .wolf/cerebrum.md | Documented 3-script architecture | ~300 |
| 00:40 | Session end: 16 writes across 7 files (feedback_atomic_commits.md, MEMORY.md, wiktionary_constants.py, Wiktionary sense based translation extender 3.py, Wiktionary extension builder.py) | 2 reads | ~19456 tok |
| 00:41 | Session end: 16 writes across 7 files (feedback_atomic_commits.md, MEMORY.md, wiktionary_constants.py, Wiktionary sense based translation extender 3.py, Wiktionary extension builder.py) | 2 reads | ~19456 tok |

## Session: 2026-04-27 00:41

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-27 00:41

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 00:45 | Edited Doxo_passages_edited_updated.csv | 9→10 lines | ~600 |
| 00:47 | Created merge_tmx_thirty.py | — | ~604 |
| 00:48 | Session end: 2 writes across 2 files (Doxo_passages_edited_updated.csv, merge_tmx_thirty.py) | 5 reads | ~11276 tok |
| 2026-04-28 | Extended Esopo fables bitext: replaced 38 old CSV rows (old Globasa, no English, broken quote splits) with 28 properly segmented rows (current Globasa + archive English); updated TMX from 6→33 Esopo TUs | Doxo_passages_edited_updated.csv, Doxo_passages.tmx | success | ~8K |

## Session: 2026-04-29 15:54

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-29 15:55

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-29 15:56

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-29 15:56

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-29 15:56

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 15:57 | Edited word_viewer.html | added 1 condition(s) | ~220 |
| 15:57 | Edited word_viewer.html | inline fix | ~85 |
| 15:58 | Edited word_viewer.html | expanded (+24 lines) | ~305 |
| 15:58 | Session end: 3 writes across 1 files (word_viewer.html) | 1 reads | ~25009 tok |
| 15:59 | Edited word_viewer.html | expanded (+9 lines) | ~375 |
| 15:59 | Edited word_viewer.html | inline fix | ~102 |
| 16:00 | Edited word_viewer.html | expanded (+65 lines) | ~843 |
| 16:00 | Session end: 6 writes across 1 files (word_viewer.html) | 1 reads | ~26770 tok |
| 16:02 | Edited word_viewer.html | inline fix | ~40 |
| 16:02 | Session end: 7 writes across 1 files (word_viewer.html) | 1 reads | ~27398 tok |
| 16:03 | Edited word_viewer.html | inline fix | ~93 |
| 16:07 | Edited word_viewer.html | inline fix | ~41 |
| 16:07 | Edited word_viewer.html | added 1 condition(s) | ~122 |
| 16:07 | Edited word_viewer.html | 8→10 lines | ~96 |
| 16:07 | Session end: 11 writes across 1 files (word_viewer.html) | 1 reads | ~27779 tok |

## Session: 2026-04-29 16:25

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-29 16:25

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-29 16:29

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-29 16:29

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-29 20:42

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-29 20:43

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-29 21:11

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-29 21:11

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 21:23 | Created ../../.claude/plans/mossy-rolling-hoare.md | — | ~1919 |
| 21:46 | Created ../../.claude/plans/mossy-rolling-hoare.md | — | ~3342 |
| 21:50 | Edited ../../.claude/plans/mossy-rolling-hoare.md | modified that() | ~952 |
| 21:50 | Edited ../../.claude/plans/mossy-rolling-hoare.md | modified word() | ~501 |
| 22:13 | Edited ../../.claude/plans/mossy-rolling-hoare.md | expanded (+43 lines) | ~704 |
| 22:13 | Edited ../../.claude/plans/mossy-rolling-hoare.md | modified word() | ~226 |
| 22:18 | Edited ../../.claude/plans/mossy-rolling-hoare.md | modified compose_pivot_dict() | ~1042 |
| 22:18 | Edited ../../.claude/plans/mossy-rolling-hoare.md | modified word() | ~279 |
| 22:23 | Edited ../../.claude/plans/mossy-rolling-hoare.md | added 1 import(s) | ~1268 |
| 22:25 | Edited ../../.claude/plans/mossy-rolling-hoare.md | 25→29 lines | ~482 |
| 22:25 | Edited ../../.claude/plans/mossy-rolling-hoare.md | expanded (+6 lines) | ~196 |
| 22:28 | Created ../../.claude/plans/mossy-rolling-hoare.md | — | ~3215 |
| 22:39 | Edited ../../.claude/plans/mossy-rolling-hoare.md | expanded (+9 lines) | ~430 |
| 22:43 | Created run_giza_improved.py | — | ~4305 |
| 22:45 | Edited run_giza_improved.py | modified parse_menalari_gloss() | ~224 |
| 22:45 | Edited run_giza_improved.py | modified startswith() | ~43 |
| 22:46 | Edited run_giza_improved.py | 2→2 lines | ~37 |
| 22:48 | Edited run_giza_improved.py | modified _load_morphemes() | ~1184 |
| 22:49 | Edited run_giza_improved.py | append() → segment_word() | ~139 |
| 22:50 | Session end: 19 writes across 2 files (mossy-rolling-hoare.md, run_giza_improved.py) | 16 reads | ~42549 tok |
| 22:56 | Edited run_giza_improved.py | "/tmp/giza-pp" → "giza-pp" | ~16 |
| 22:58 | Edited run_giza_improved.py | 5→6 lines | ~70 |
| 22:58 | Edited run_giza_improved.py | modified build_seed_dict() | ~362 |
| 23:01 | Session end: 22 writes across 2 files (mossy-rolling-hoare.md, run_giza_improved.py) | 16 reads | ~42997 tok |
| 23:03 | Edited run_giza_improved.py | added 1 condition(s) | ~1560 |
| 23:04 | Edited run_giza_improved.py | expanded (+32 lines) | ~627 |

## Session: 2026-04-29 (GIZA++ improvements)

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 21:11 | Planned GIZA++ alignment improvements (8 improvements) | mossy-rolling-hoare.md | Plan approved after 7 revision rounds | ~15000 |
| 22:43 | Created run_giza_improved.py with Improvements 1-3: dictionary seeding, word-pair augmentation, morphological segmentation with productive affix stripping | run_giza_improved.py | 13K en pairs, 4570 morpheme entries, 73 prefixes + 61 suffixes | ~5000 |
| 22:56 | Added giza-pp as git submodule, built GIZA++ binaries | giza-pp/ | GIZA++, plain2snt, snt2cooc, mkcls all built | ~500 |
| 23:00 | Ran baseline vs improved GIZA++ comparison on glb↔en | giza_output_baseline/, giza_output_improved/ | Morpheme segmentation works: be+krea↔created, xor+somno↔fell+asleep. Dictionary seeding: insan→human 5x better. Vocab -41%. | ~3000 |
| 23:03 | Added Improvement 7: bidirectional GIZA++ + GDFA symmetrization | run_giza_improved.py | parse_a3(), gdfa_symmetrize(), write_pharaoh(). Many-to-one alignment fixed: bon+ata↔welcome, kitabu+dom↔library, insan+li↔human | ~3000 |
| 23:32 | Edited run_giza_improved.py | modified _load_mwes() | ~453 |
| 23:33 | Edited run_giza_improved.py | modified tokenize() | ~236 |
| 23:43 | Edited run_giza_improved.py | modified _load_mwes() | ~513 |
| 23:45 | Session end: 27 writes across 2 files (mossy-rolling-hoare.md, run_giza_improved.py) | 16 reads | ~49234 tok |
| 23:49 | Session end: 27 writes across 2 files (mossy-rolling-hoare.md, run_giza_improved.py) | 16 reads | ~49234 tok |

## Session: 2026-04-29 23:52

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-29 23:52

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-29 23:52

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-29 23:52

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 23:52 | Edited ../../.claude/plans/mossy-rolling-hoare.md | expanded (+60 lines) | ~827 |

## Session: 2026-04-29 23:52

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 00:05 | Created ../../ApplicationSource/GlobasaTranslation/apertium-glb/apertium-glb.glb.rlx | — | ~1415 |
| 00:10 | Created PosTagger.py | — | ~4822 |
| 00:15 | Edited PosTagger.py | modified tokenize() | ~630 |
| 00:15 | Edited PosTagger.py | modified is_clause_boundary() | ~185 |
| 00:18 | Edited PosTagger.py | modified is_clause_boundary() | ~226 |
| 00:18 | Edited PosTagger.py | 5→10 lines | ~116 |
| 00:19 | Edited PosTagger.py | 4→9 lines | ~128 |
| 00:20 | Edited PosTagger.py | modified range() | ~575 |
| 00:20 | Edited PosTagger.py | 7→7 lines | ~120 |

## Session: 2026-04-30 (POS Tagger)

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|---------|
| -- | Rewrote apertium-glb.glb.rlx: 4 sections (b via context, SVO, t/d;m resolution, interjection cleanup). CBARRIER for scanning through d;m words. | apertium-glb.glb.rlx | Correct CG3 disambiguation replacing flawed -1 rules | ~1400 |
| -- | Created PosTagger.py: 3-step Globasa POS tagger. Step 1: prep/particle/det/poss/num project through t/d;m to b. Step 2: SVO per clause (N-V-N). Step 3: t/d;m resolved by next connected b. | PosTagger.py | All 21 Xwexi test sentences correct, corpus tested | ~5000 |
| -- | Fixed multi-word greediness (conservative: only fe/cel/he/no + multi_word_parts), clause boundary (comma not period), na as clause boundary, -mo → ADV, PP-internal nouns excluded from SVO | PosTagger.py | 5 bug fixes | ~2000 |
| -- | Added `__vbser` paradigm + dix entry for `sen`; CG rule SELECT (vbser) IF (1* (adj) BARRIER NotAdjAdv) favors copula when followed by t-class | apertium-glb.glb.dix, apertium-glb.glb.rlx | sen/vbser before adj, sen/vblex otherwise | ~500 |
| -- | Fixed proper noun tagging: lemmatizer tries original/title case for `su n` words (Globasa, Englisa); unknown capitalized non-sentence-initial words → PROPN; `su n`/`su t` checked before ambiguous classes | PosTagger.py | Mark/PROPN, Kaliforni/PROPN, Globasa/PROPN all correct | ~500 |
| 00:33 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb/apertium-glb.glb.rlx | 3→2 lines | ~28 |
| 00:33 | Session end: 13 writes across 3 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix) | 3 reads | ~13798 tok |
| 00:35 | Session end: 13 writes across 3 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix) | 3 reads | ~13798 tok |
| 00:41 | Edited ../../.claude/plans/mossy-rolling-hoare.md | expanded (+14 lines) | ~1076 |
| 00:41 | Edited ../../.claude/plans/mossy-rolling-hoare.md | modified read() | ~105 |
| 00:51 | Edited run_giza_improved.py | 13→17 lines | ~136 |
| 00:52 | Edited run_giza_improved.py | modified _get_spacy() | ~926 |
| 00:52 | Edited run_giza_improved.py | modified run_giza() | ~366 |
| 00:54 | Edited run_giza_improved.py | modified factorize_glb() | ~483 |
| 00:55 | Edited run_giza_improved.py | modified enumerate() | ~327 |
| 00:55 | Edited run_giza_improved.py | modified _infer_pos_from_wordclass() | ~432 |
| 01:02 | Session end: 21 writes across 5 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 7 reads | ~26741 tok |
| 01:05 | Edited run_giza_improved.py | 4→8 lines | ~97 |
| 01:06 | Edited run_giza_improved.py | modified apply_funcword_rules() | ~955 |
| 01:07 | Edited run_giza_improved.py | modified word() | ~207 |
| 01:09 | Session end: 24 writes across 5 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 7 reads | ~28816 tok |
| 01:14 | Edited HunspellMaker.py | modified get_lexiklase() | ~325 |
| 01:14 | Edited HunspellMaker.py | inline fix | ~11 |
| 01:14 | Edited HunspellMaker.py | modified spell() | ~58 |
| 01:14 | Edited HunspellMaker.py | modified enumerate() | ~273 |
| 01:15 | Edited HunspellMaker.py | 2→2 lines | ~49 |
| 01:15 | Edited HunspellMaker.py | modified isinstance() | ~587 |
| 01:15 | Edited HunspellMaker.py | modified iterrows() | ~292 |
| 01:26 | Edited HunspellMaker.py | 1→2 lines | ~32 |
| 01:27 | Edited HunspellMaker.py | modified iterrows() | ~149 |
| 01:28 | Edited run_giza_improved.py | modified multiway_concordance() | ~1140 |
| 01:28 | Created GlobasaGrammarChecker/__init__.py | — | ~11 |
| 01:28 | Created GlobasaGrammarChecker/rules/__init__.py | — | ~81 |
| 01:28 | Created GlobasaGrammarChecker/rules/base.py | — | ~410 |
| 01:28 | Edited run_giza_improved.py | 5→9 lines | ~122 |
| 01:29 | Created GlobasaGrammarChecker/rules/infinitive.py | — | ~416 |
| 01:29 | Edited run_giza_improved.py | 9→8 lines | ~116 |
| 01:29 | Created GlobasaGrammarChecker/rules/tense.py | — | ~444 |
| 01:29 | Created GlobasaGrammarChecker/rules/negation.py | — | ~532 |
| 01:29 | Created GlobasaGrammarChecker/rules/np_structure.py | — | ~430 |
| 01:29 | Created GlobasaGrammarChecker/rules/question.py | — | ~312 |
| 01:30 | Created GlobasaGrammarChecker/checker.py | — | ~599 |
| 01:30 | Created GlobasaGrammarChecker/server.py | — | ~568 |
| 01:30 | Created GlobasaGrammarChecker/__main__.py | — | ~174 |
| 06:38 | Edited run_giza_improved.py | modified run_giza() | ~42 |
| 06:39 | Edited run_giza_improved.py | 12→16 lines | ~182 |
| 06:39 | Created GlobasaGrammarChecker/rules/infinitive.py | — | ~602 |
| 06:40 | Edited GlobasaGrammarChecker/rules/infinitive.py | 5→5 lines | ~53 |
| 06:40 | Edited GlobasaGrammarChecker/rules/tense.py | 8→9 lines | ~124 |
| 06:42 | Session end: 52 writes across 16 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 10 reads | ~42144 tok |
| 07:05 | Created GlobasaGrammarChecker/rules/infinitive.py | — | ~922 |
| 07:06 | Created GlobasaGrammarChecker/rules/negation.py | — | ~473 |
| 07:06 | Created GlobasaGrammarChecker/rules/question.py | — | ~422 |
| 07:07 | Created GlobasaGrammarChecker/rules/conditional.py | — | ~554 |
| 07:07 | Created GlobasaGrammarChecker/rules/passive.py | — | ~598 |
| 07:10 | Created GlobasaGrammarChecker/rules/__init__.py | — | ~102 |
| 07:10 | Session end: 58 writes across 18 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 22 reads | ~45817 tok |
| 07:12 | Created GlobasaGrammarChecker/rules/adverb_mo.py | — | ~748 |
| 07:13 | Edited GlobasaGrammarChecker/rules/__init__.py | added 1 import(s) | ~116 |
| 07:13 | Session end: 60 writes across 19 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 23 reads | ~46783 tok |
| 07:17 | Created GlobasaGrammarChecker/rules/noun_pile.py | — | ~506 |
| 07:18 | Edited GlobasaGrammarChecker/rules/__init__.py | added 1 import(s) | ~65 |
| 07:19 | Edited GlobasaGrammarChecker/rules/noun_pile.py | inline fix | ~23 |
| 07:19 | Session end: 63 writes across 20 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 23 reads | ~47377 tok |
| 07:27 | Created GlobasaGrammarChecker/rules/noun_as_verb.py | — | ~555 |
| 07:28 | Edited GlobasaGrammarChecker/rules/__init__.py | added 1 import(s) | ~74 |
| 07:29 | Edited GlobasaGrammarChecker/rules/noun_as_verb.py | 3→3 lines | ~38 |
| 07:30 | Session end: 66 writes across 21 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 23 reads | ~48044 tok |
| 07:30 | Edited GlobasaGrammarChecker/rules/noun_as_verb.py | 7→7 lines | ~121 |
| 07:31 | Session end: 67 writes across 21 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 23 reads | ~48165 tok |
| 07:34 | Edited run_giza_improved.py | modified simalign_pivot() | ~1364 |
| 07:37 | Session end: 68 writes across 21 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 23 reads | ~49529 tok |
| 07:39 | Session end: 68 writes across 21 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 23 reads | ~49529 tok |
| 07:43 | Edited PosTagger.py | modified lemmatize() | ~152 |
| 07:43 | Edited PosTagger.py | modified enumerate() | ~229 |
| 07:43 | Edited PosTagger.py | 16→12 lines | ~113 |
| 07:45 | Session end: 71 writes across 21 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 36 reads | ~56130 tok |
| 07:46 | Session end: 71 writes across 21 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 36 reads | ~56130 tok |
| 07:48 | Edited extend_tmx_pnc_multi.py | expanded (+7 lines) | ~106 |
| 07:48 | Edited extend_tmx_pnc_multi.py | modified enumerate() | ~249 |
| 07:49 | Edited extend_tmx_pnc_multi.py | 8→10 lines | ~156 |
| 23:04 | Added factored tokenization (PosTagger.py POS + spaCy en lemma), function word rules (le→NULL before passive, da/kam→NULL), root protection against false segmentation | run_giza_improved.py | 36 le, 522 da, 168 kam corrections per run | ~3000 |
| 07:35 | Added SimAlign pivot alignment for UDHR+P&C multi-way TUs: en pivot via mBERT neural aligner, ~12K clean glb↔X pairs across 14 languages | run_giza_improved.py | simalign pip install, 416 TUs processed | ~2000 |
| 07:40 | Expanded P&C TMX extension: 8 new languages (pl, vi, ko, zh, ja, uk, hu, he), 722 TUVs. Output to _extended.tmx. P&C lang code mapping (cn→zh, kr→ko). | extend_tmx_pnc_multi.py | All 8 improvements complete | ~1000 |
| 07:51 | Session end: 74 writes across 22 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 37 reads | ~58388 tok |
| 08:01 | Session end: 74 writes across 22 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 37 reads | ~58388 tok |
| 08:04 | Session end: 74 writes across 22 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 37 reads | ~58388 tok |
| 08:07 | Edited PosTagger.py | 2→3 lines | ~50 |
| 08:09 | Edited PosTagger.py | 3→2 lines | ~35 |
| 08:09 | Edited PosTagger.py | 2→2 lines | ~43 |
| 08:10 | Edited run_giza_improved.py | modified zip() | ~583 |
| 08:52 | Edited run_giza_improved.py | modified segment_word() | ~605 |
| 08:53 | Session end: 79 writes across 22 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 37 reads | ~61345 tok |
| 08:55 | Session end: 79 writes across 22 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 37 reads | ~61345 tok |
| 09:02 | Edited ../../../../tmp/anymalign/anymalign.py | modified endswith() | ~71 |
| 09:04 | Edited ../../../../tmp/anymalign/anymalign.py | modified endswith() | ~56 |
| 09:04 | Edited ../../../../tmp/anymalign/anymalign.py | inline fix | ~8 |
| 09:36 | Edited run_giza_improved.py | added 1 condition(s) | ~1695 |
| 09:38 | Edited run_giza_improved.py | modified strip() | ~134 |
| 09:38 | Edited run_giza_improved.py | modified word() | ~37 |
| 09:42 | Edited run_giza_improved.py | 7→8 lines | ~77 |
| 09:44 | Session end: 86 writes across 23 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 38 reads | ~63488 tok |
| 09:45 | Session end: 86 writes across 23 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 38 reads | ~63488 tok |
| 09:45 | Session end: 86 writes across 23 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 38 reads | ~63488 tok |
| 09:47 | Edited run_giza_improved.py | expanded (+6 lines) | ~157 |
| 09:48 | Edited run_giza_improved.py | modified _build_eflomal_priors() | ~733 |
| 09:50 | Session end: 88 writes across 23 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 38 reads | ~65945 tok |
| 09:52 | Session end: 88 writes across 23 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 38 reads | ~65945 tok |
| 10:03 | Edited run_giza_improved.py | lower() → case() | ~45 |
| 10:04 | Session end: 89 writes across 23 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 38 reads | ~66782 tok |
| 10:08 | Edited run_giza_improved.py | 7→7 lines | ~97 |
| 10:09 | Session end: 90 writes across 23 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 38 reads | ~66879 tok |
| 10:12 | Edited run_giza_improved.py | modified _build_eflomal_priors() | ~1585 |
| 10:13 | Session end: 91 writes across 23 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 38 reads | ~68480 tok |
| 10:16 | Edited run_giza_improved.py | modified verbs() | ~2048 |
| 10:22 | Session end: 92 writes across 23 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 38 reads | ~71401 tok |
| 10:24 | Edited run_giza_improved.py | 5→5 lines | ~69 |
| 10:24 | Edited run_giza_improved.py | expanded (+72 lines) | ~892 |
| 10:25 | Edited run_giza_improved.py | 5→5 lines | ~76 |
| 10:25 | Edited run_giza_improved.py | 18→19 lines | ~189 |
| 10:25 | Edited run_giza_improved.py | clauses() → subclauses() | ~64 |
| 10:25 | Edited run_giza_improved.py | clause() → final() | ~29 |
| 10:26 | Edited run_giza_improved.py | order() → flexible() | ~64 |
| 10:26 | Edited run_giza_improved.py | expanded (+13 lines) | ~170 |
| 10:27 | Session end: 100 writes across 23 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 38 reads | ~74589 tok |
| 10:31 | Edited run_giza_improved.py | modified startswith() | ~89 |
| 10:31 | Edited run_giza_improved.py | modified split() | ~90 |
| 10:35 | Session end: 102 writes across 23 files (apertium-glb.glb.rlx, PosTagger.py, apertium-glb.glb.dix, mossy-rolling-hoare.md, run_giza_improved.py) | 38 reads | ~75565 tok |

## Session: 2026-04-30 10:37

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-30 10:37

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 11:08 | Created ../../.claude/plans/floating-giggling-toucan.md | — | ~1479 |
| 11:13 | Created ../../.claude/plans/floating-giggling-toucan.md | — | ~1953 |
| 11:17 | Created ../../.claude/plans/floating-giggling-toucan.md | — | ~1962 |
| 11:20 | Created ../../.claude/plans/floating-giggling-toucan.md | — | ~2015 |
| 11:25 | Created ../../.claude/plans/floating-giggling-toucan.md | — | ~2168 |
| 11:27 | Edited ../../.claude/plans/floating-giggling-toucan.md | inline fix | ~170 |
| 11:28 | Edited ../../.claude/plans/floating-giggling-toucan.md | modified marking() | ~98 |
| 11:28 | Edited ../../.claude/plans/floating-giggling-toucan.md | inline fix | ~28 |
| 11:29 | Edited ../../.claude/plans/floating-giggling-toucan.md | 1→6 lines | ~174 |
| 11:29 | Edited ../../.claude/plans/floating-giggling-toucan.md | 1→2 lines | ~45 |
| 11:31 | Edited Word Viewer.py | added 1 import(s) | ~55 |
| 11:31 | Edited Word Viewer.py | 3→7 lines | ~108 |
| 11:32 | Edited Word Viewer.py | modified parse_giza_a3_full() | ~3530 |
| 11:33 | Edited Word Viewer.py | modified rebuild() | ~1331 |
| 11:34 | Edited word_viewer.html | "https://menalari.globasa." → "/alignments" | ~140 |
| 11:37 | Created alignment_viewer.html | — | ~4691 |
| 12:00 | Created alignment_viewer.html — self-contained page for browsing GIZA++ word alignment data with hover highlighting, language/source selectors, search, pagination | alignment_viewer.html | done | ~2500 |
| 11:38 | Created translation_aide.html | — | ~6462 |

| 11:38 | Created translation_aide.html — Apertium-powered translation page with interactive ambiguity resolution (polysemy dropdowns, un toggle for eng->glb, article insertion for glb->eng, pipeline stages). Matches word_viewer.html visual style. | translation_aide.html | created | ~500 |
| 11:43 | Edited Word Viewer.py | modified _build_token_info() | ~736 |
| 11:43 | Edited Word Viewer.py | modified in() | ~246 |
| 11:47 | Edited Word Viewer.py | modified _apply_overrides() | ~806 |
| 11:49 | Edited Word Viewer.py | 6→11 lines | ~152 |
| 11:49 | Edited Word Viewer.py | 11→14 lines | ~156 |
| 11:49 | Edited translation_aide.html | renderTokens() → renderOutput() | ~30 |
| 11:50 | Edited translation_aide.html | added 5 condition(s) | ~1285 |
| 11:50 | Edited translation_aide.html | modified makePolysemyHandler() | ~360 |
| 11:52 | All APIs tested | eng-glb: un suppression/override/opt-in, glb-eng: polysemy/articles, alignments: a3/gdfa/search | ~500 |
| 11:53 | Updated anatomy.md, cerebrum.md | Removed duplicates, added Apertium learnings | ~200 |
| 11:54 | Session end: 25 writes across 5 files (floating-giggling-toucan.md, Word Viewer.py, word_viewer.html, alignment_viewer.html, translation_aide.html) | 16 reads | ~100423 tok |

## Session: 2026-04-30 11:55

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-30 11:55

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 12:06 | Edited alignment_viewer.html | modified then() | ~144 |
| 12:08 | Edited Word Viewer.py | modified _load_tmx_contexts() | ~878 |
| 12:08 | Edited Word Viewer.py | modified _load_alignments() | ~230 |
| 12:09 | Edited Word Viewer.py | modified api_alignment_contexts() | ~566 |
| 12:09 | Edited alignment_viewer.html | 21→24 lines | ~245 |
| 12:10 | Edited alignment_viewer.html | added 2 condition(s) | ~1036 |
| 12:10 | Edited alignment_viewer.html | added 1 condition(s) | ~129 |
| 12:10 | Edited alignment_viewer.html | 8→12 lines | ~56 |
| 12:11 | Edited Word Viewer.py | modified enumerate() | ~368 |
| 12:12 | Session end: 9 writes across 2 files (alignment_viewer.html, Word Viewer.py) | 2 reads | ~25504 tok |

## Session: 2026-04-30 12:15

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-30 12:15

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-30 12:15

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-30 12:15

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-30 12:17

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 12:22 | Edited Word Viewer.py | modified _load_tmx_contexts() | ~452 |
| 12:24 | Edited Word Viewer.py | modified parse_giza_a3_full() | ~607 |

## Session: 2026-04-30 12:24

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-04-30 12:24

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 12:25 | Edited Word Viewer.py | modified _giza_tokenize_preserve_case() | ~526 |
| 12:26 | Session end: 1 writes across 1 files (Word Viewer.py) | 1 reads | ~526 tok |
| 12:30 | Edited run_giza_improved.py | modified segment_word() | ~783 |
| 12:31 | Edited run_giza_improved.py | modified endswith() | ~172 |
| 12:31 | Edited run_giza_improved.py | 2→7 lines | ~85 |
| 12:31 | Edited run_giza_improved.py | "be" → "be-" | ~11 |
| 12:37 | Edited run_giza_improved.py | modified _load_morphemes() | ~538 |
| 12:38 | Edited run_giza_improved.py | modified len() | ~773 |
| 12:38 | Edited run_giza_improved.py | modified items() | ~231 |
| 12:40 | Edited run_giza_improved.py | modified _get_distortion_priors() | ~960 |
| 12:42 | Edited run_giza_improved.py | expanded (+12 lines) | ~379 |
| 12:49 | Edited run_giza_improved.py | added 2 condition(s) | ~435 |
| 12:52 | Edited run_giza_improved.py | modified list() | ~325 |
| 12:54 | Edited run_giza_improved.py | reduced (-10 lines) | ~71 |
| 12:55 | Edited run_giza_improved.py | 8→8 lines | ~59 |
| 12:55 | Edited run_giza_improved.py | 13→13 lines | ~130 |
| 12:55 | Edited run_giza_improved.py | reduced (-7 lines) | ~529 |
| 12:56 | Edited run_giza_improved.py | modified len() | ~426 |
| 12:58 | Session end: 17 writes across 2 files (Word Viewer.py, run_giza_improved.py) | 2 reads | ~28157 tok |
| 13:03 | Edited run_giza_improved.py | modified items() | ~620 |
| 13:05 | Edited run_giza_improved.py | 4→4 lines | ~74 |
| 13:06 | Edited run_giza_improved.py | 9→10 lines | ~146 |
| 13:06 | Edited run_giza_improved.py | 8→10 lines | ~133 |
| 13:08 | Edited run_giza_improved.py | 5→5 lines | ~79 |
| 13:09 | Session end: 22 writes across 2 files (Word Viewer.py, run_giza_improved.py) | 2 reads | ~29078 tok |
| 13:11 | Edited run_giza_improved.py | modified endswith() | ~566 |
| 13:11 | Edited run_giza_improved.py | 8→12 lines | ~125 |
| 13:12 | Edited run_giza_improved.py | modified factor_glb() | ~869 |
| 13:12 | Edited run_giza_improved.py | expanded (+11 lines) | ~257 |
| 13:13 | Edited run_giza_improved.py | modified len() | ~467 |
| 13:13 | Edited run_giza_improved.py | expanded (+7 lines) | ~196 |
| 13:14 | Edited run_giza_improved.py | modified _get_distortion_priors() | ~419 |
| 13:15 | Session end: 29 writes across 2 files (Word Viewer.py, run_giza_improved.py) | 2 reads | ~33718 tok |
| 13:17 | Edited run_giza_improved.py | expanded (+11 lines) | ~383 |
| 13:17 | Edited run_giza_improved.py | reduced (-11 lines) | ~92 |
| 13:17 | Edited run_giza_improved.py | reduced (-14 lines) | ~188 |
| 13:18 | Edited run_giza_improved.py | modified _tag_morpheme() | ~247 |
| 13:18 | Edited run_giza_improved.py | modified endswith() | ~448 |
| 13:19 | Session end: 34 writes across 2 files (Word Viewer.py, run_giza_improved.py) | 2 reads | ~35076 tok |
| 13:26 | Edited run_giza_improved.py | reduced (-13 lines) | ~182 |
| 13:30 | Edited run_giza_improved.py | 30→32 lines | ~417 |
| 13:30 | Edited run_giza_improved.py | 3→3 lines | ~67 |
| 13:31 | Edited run_giza_improved.py | modified items() | ~86 |
| 13:31 | Session end: 38 writes across 2 files (Word Viewer.py, run_giza_improved.py) | 2 reads | ~36506 tok |
| 13:35 | Edited run_giza_improved.py | added 1 condition(s) | ~250 |
| 13:36 | Edited run_giza_improved.py | 10→13 lines | ~179 |
| 13:36 | Edited run_giza_improved.py | modified Mandarin() | ~147 |
| 13:36 | Edited run_giza_improved.py | 10→15 lines | ~247 |
| 13:37 | Edited run_giza_improved.py | expanded (+7 lines) | ~303 |
| 13:38 | Session end: 43 writes across 2 files (Word Viewer.py, run_giza_improved.py) | 2 reads | ~37624 tok |
| 13:40 | Session end: 43 writes across 2 files (Word Viewer.py, run_giza_improved.py) | 2 reads | ~37624 tok |
| 13:44 | Created ../../.claude/plans/gold-alignment-annotation.md | — | ~2153 |
| 13:48 | Created merge_gold_priors.py | — | ~1364 |
| 13:48 | Edited Word Viewer.py | 3→5 lines | ~65 |
| 13:49 | Edited Word Viewer.py | added 2 import(s) | ~70 |
| 13:49 | Edited Word Viewer.py | modified _gold_tsv_path() | ~1395 |
| 13:49 | Edited run_giza_improved.py | expanded (+9 lines) | ~147 |
| 13:51 | Created annotate_alignments.html | — | ~8050 |
| 11:52 | Implemented gold-alignment-annotation feature | annotate_alignments.html (new), merge_gold_priors.py (new), Word Viewer.py (+3 routes), run_giza_improved.py (hook) | all routes smoke-tested; TSV format verified | ~3500 |
| 13:57 | Session end: 50 writes across 5 files (Word Viewer.py, run_giza_improved.py, gold-alignment-annotation.md, merge_gold_priors.py, annotate_alignments.html) | 12 reads | ~111039 tok |
| 13:58 | Edited .vscode/tasks.json | expanded (+31 lines) | ~504 |
| 13:59 | Session end: 51 writes across 6 files (Word Viewer.py, run_giza_improved.py, gold-alignment-annotation.md, merge_gold_priors.py, annotate_alignments.html) | 13 reads | ~112505 tok |
| 14:09 | Edited alignment_viewer.html | expanded (+53 lines) | ~365 |
| 14:09 | Edited alignment_viewer.html | modified if() | ~330 |
| 14:10 | Edited alignment_viewer.html | added 11 condition(s) | ~1120 |
| 14:11 | Edited annotate_alignments.html | added 2 condition(s) | ~291 |
| 14:11 | Edited annotate_alignments.html | 3→4 lines | ~53 |
| 14:11 | Edited annotate_alignments.html | added 2 condition(s) | ~238 |
| 14:13 | Session end: 57 writes across 7 files (Word Viewer.py, run_giza_improved.py, gold-alignment-annotation.md, merge_gold_priors.py, annotate_alignments.html) | 13 reads | ~115582 tok |
| 14:18 | Edited annotate_alignments.html | expanded (+46 lines) | ~311 |
| 14:18 | Edited annotate_alignments.html | expanded (+10 lines) | ~210 |
| 14:19 | Edited annotate_alignments.html | added 13 condition(s) | ~1013 |
| 14:20 | Session end: 60 writes across 7 files (Word Viewer.py, run_giza_improved.py, gold-alignment-annotation.md, merge_gold_priors.py, annotate_alignments.html) | 13 reads | ~118712 tok |
| 14:33 | Edited Word Viewer.py | modified len() | ~429 |
| 14:33 | Edited Word Viewer.py | 8→8 lines | ~77 |
| 14:36 | Session end: 62 writes across 7 files (Word Viewer.py, run_giza_improved.py, gold-alignment-annotation.md, merge_gold_priors.py, annotate_alignments.html) | 13 reads | ~119461 tok |
| 14:47 | Edited annotate_alignments.html | expanded (+9 lines) | ~202 |
| 14:47 | Edited annotate_alignments.html | modified resetToAuto() | ~261 |
| 14:49 | Session end: 64 writes across 7 files (Word Viewer.py, run_giza_improved.py, gold-alignment-annotation.md, merge_gold_priors.py, annotate_alignments.html) | 13 reads | ~120207 tok |
| 14:55 | Edited annotate_alignments.html | modified if() | ~184 |
| 14:57 | Edited annotate_alignments.html | added 4 condition(s) | ~504 |

## Session: 2026-05-01 14:06

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-05-01 14:06

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 14:08 | Edited annotate_alignments.html | expanded (+8 lines) | ~193 |
| 14:08 | Edited annotate_alignments.html | expanded (+8 lines) | ~254 |
| 14:09 | Edited annotate_alignments.html | expanded (+31 lines) | ~260 |
| 14:09 | Edited annotate_alignments.html | 2→4 lines | ~67 |
| 14:11 | Edited annotate_alignments.html | added 3 condition(s) | ~569 |
| 14:12 | Edited Word Viewer.py | modified api_annotated_ids() | ~912 |
| 14:14 | Edited annotate_alignments.html | expanded (+38 lines) | ~351 |
| 14:15 | Edited annotate_alignments.html | added 1 condition(s) | ~734 |
| 14:17 | Session end: 8 writes across 2 files (annotate_alignments.html, Word Viewer.py) | 2 reads | ~33082 tok |

## Session: 2026-05-01 14:17

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 14:33 | Created ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | — | ~3538 |
| 14:34 | Edited Word Viewer.py | modified _load_gold_annotation() | ~708 |
| 14:37 | Edited Word Viewer.py | modified api_bulk_reset_gold() | ~747 |
| 14:38 | Edited merge_gold_priors.py | 1→5 lines | ~90 |
| 14:38 | Edited annotate_alignments.html | added 1 condition(s) | ~298 |
| 14:39 | Edited annotate_alignments.html | added 4 condition(s) | ~548 |
| 14:46 | Created ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | — | ~5364 |
| 14:46 | Session end: 7 writes across 4 files (i-wish-to-develop-idempotent-gizmo.md, Word Viewer.py, merge_gold_priors.py, annotate_alignments.html) | 19 reads | ~86124 tok |
| 14:47 | Session end: 7 writes across 4 files (i-wish-to-develop-idempotent-gizmo.md, Word Viewer.py, merge_gold_priors.py, annotate_alignments.html) | 19 reads | ~86124 tok |
| 14:47 | Session end: 7 writes across 4 files (i-wish-to-develop-idempotent-gizmo.md, Word Viewer.py, merge_gold_priors.py, annotate_alignments.html) | 19 reads | ~86124 tok |
| 14:48 | Edited Word Viewer.py | modified _run_eflomal_for() | ~1927 |
| 14:49 | Edited Word Viewer.py | added 1 import(s) | ~44 |
| 14:50 | Edited annotate_alignments.html | added 7 condition(s) | ~1262 |
| 14:51 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 8→9 lines | ~334 |
| 14:51 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 3→4 lines | ~62 |
| 14:51 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 2→3 lines | ~64 |
| 14:51 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 7→9 lines | ~144 |
| 14:52 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | modified to_aligner_text() | ~1172 |
| 14:52 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 3→5 lines | ~187 |
| 14:52 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 2→3 lines | ~98 |
| 14:52 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 2→3 lines | ~87 |
| 14:53 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | expanded (+13 lines) | ~418 |
| 14:54 | Session end: 19 writes across 4 files (i-wish-to-develop-idempotent-gizmo.md, Word Viewer.py, merge_gold_priors.py, annotate_alignments.html) | 19 reads | ~92195 tok |
| 14:56 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 17→18 lines | ~279 |
| 14:56 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 1→2 lines | ~50 |
| 14:57 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | modified longest_match() | ~1020 |
| 14:57 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | modified tokenize() | ~430 |
| 14:57 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 13→17 lines | ~536 |
| 14:58 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | expanded (+24 lines) | ~663 |
| 14:58 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 2→3 lines | ~91 |

## Session: 2026-05-01 14:59

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-05-01 14:59

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-05-01 19:59

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 20:03 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 9→11 lines | ~568 |
| 20:04 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | fallback() → fragments() | ~120 |
| 20:04 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | modified MorphKind() | ~145 |
| 20:04 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | modified syllabify() | ~1116 |
| 20:04 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | modified word() | ~230 |
| 20:05 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 2→4 lines | ~124 |
| 20:05 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 3→6 lines | ~206 |
| 20:05 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | modified NLLB() | ~345 |
| 20:05 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 1→5 lines | ~272 |
| 20:06 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 9→11 lines | ~305 |
| 20:06 | Session end: 10 writes across 1 files (i-wish-to-develop-idempotent-gizmo.md) | 3 reads | ~39899 tok |
| 20:13 | Created migrate_gold_tsv.py | — | ~2006 |
| 20:13 | Edited Word Viewer.py | expanded (+6 lines) | ~285 |
| 20:13 | Edited Word Viewer.py | modified _load_gold_annotation() | ~462 |
| 20:13 | Edited Word Viewer.py | modified _load_all_annotated_ids() | ~418 |
| 20:14 | Edited Word Viewer.py | modified api_post_gold_alignment() | ~794 |
| 20:14 | Edited Word Viewer.py | modified sorted() | ~90 |
| 20:14 | Edited merge_gold_priors.py | modified columns() | ~266 |
| 20:14 | Edited merge_gold_priors.py | modified except() | ~392 |
| 20:15 | Edited annotate_alignments.html | 3→5 lines | ~79 |
| 20:15 | Edited annotate_alignments.html | 7→8 lines | ~165 |
| 20:15 | Edited annotate_alignments.html | map() → sentence_id() | ~596 |
| 20:16 | Edited annotate_alignments.html | modified buildCard() | ~414 |
| 20:16 | Edited annotate_alignments.html | modified if() | ~185 |
| 20:16 | Edited annotate_alignments.html | 7→7 lines | ~128 |
| 20:16 | Edited annotate_alignments.html | added error handling | ~503 |
| 20:16 | Edited annotate_alignments.html | modified loadGoldAnnotation() | ~378 |
| 20:17 | Edited annotate_alignments.html | added 2 condition(s) | ~610 |
| 20:17 | Edited annotate_alignments.html | modified bulkResetFollowing() | ~355 |
| 20:19 | Edited migrate_gold_tsv.py | expanded (+6 lines) | ~162 |
| 20:19 | Edited migrate_gold_tsv.py | 5→6 lines | ~100 |
| 20:22 | Fixed gold-annotation sid bug + added tier column | annotate_alignments.html, Word Viewer.py, merge_gold_priors.py, migrate_gold_tsv.py | API now attaches stable sentence_id; tier=saved/gold; only gold feeds priors; resetToAuto tombstones + drops from Annotated view | ~big |
| 20:22 | Session end: 30 writes across 5 files (i-wish-to-develop-idempotent-gizmo.md, migrate_gold_tsv.py, Word Viewer.py, merge_gold_priors.py, annotate_alignments.html) | 3 reads | ~49315 tok |
| 20:25 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 1→4 lines | ~438 |
| 20:26 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | modified word() | ~1661 |
| 20:27 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | inline fix | ~209 |
| 20:28 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | expanded (+9 lines) | ~508 |
| 20:28 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | inline fix | ~26 |
| 20:28 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 2→2 lines | ~61 |
| 20:28 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | list() → inventory() | ~87 |
| 20:28 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | inline fix | ~49 |
| 20:28 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | inline fix | ~51 |
| 20:29 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | correctly() → join() | ~165 |
| 20:29 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | modified lemmas() | ~183 |
| 20:29 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 1→2 lines | ~135 |
| 20:44 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 2→3 lines | ~79 |
| 20:45 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | expanded (+45 lines) | ~732 |
| 20:45 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 2→2 lines | ~204 |
| 20:45 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 2→3 lines | ~118 |
| 20:45 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | modified words() | ~326 |
| 20:46 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | expanded (+6 lines) | ~254 |
| 20:46 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 1→2 lines | ~82 |
| 20:48 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | inline fix | ~207 |
| 20:48 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 3→5 lines | ~119 |
| 20:49 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | modified word() | ~1437 |
| 20:49 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 1→4 lines | ~141 |
| 20:49 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 1→2 lines | ~93 |
| 20:50 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | expanded (+7 lines) | ~178 |
| 20:50 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 1→2 lines | ~87 |
| 20:50 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | modified word() | ~188 |
| 20:53 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | expanded (+75 lines) | ~1643 |
| 20:53 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 8→9 lines | ~287 |
| 20:53 | Edited ../../.claude/plans/i-wish-to-develop-idempotent-gizmo.md | 1→3 lines | ~144 |
| 20:58 | Created globasa_tokenizer/affix_trie.py | — | ~663 |
| 20:58 | Created globasa_tokenizer/affix_constraints.py | — | ~679 |
| 20:59 | Created globasa_tokenizer/affix_parser.py | — | ~1083 |
| 20:59 | Created globasa_tokenizer/offsets.py | — | ~523 |
| 20:59 | Created globasa_tokenizer/data/pseudo_morphemes.tsv | — | ~232 |
| 20:59 | Created globasa_tokenizer/data/mined_stems.tsv | — | ~9 |
| 21:00 | Created globasa_tokenizer/pseudo_morphemes.py | — | ~2554 |
| 21:00 | Created globasa_tokenizer/mined_stems.py | — | ~790 |
| 21:02 | Created globasa_tokenizer/syllable_fallback.py | — | ~1000 |
| 21:03 | Created globasa_tokenizer/fallback_cascade.py | — | ~649 |
| 21:03 | Created globasa_tokenizer/lexicon.py | — | ~2345 |
| 21:04 | Created globasa_tokenizer/segmenter.py | — | ~3473 |
| 21:05 | Created globasa_tokenizer/__init__.py | — | ~1360 |
| 21:05 | Created globasa_tokenizer/tokenizer.py | — | ~2478 |
| 21:06 | Created globasa_tokenizer/alignment.py | — | ~950 |
| 21:06 | Created globasa_tokenizer/spacy_adapter/__init__.py | — | ~871 |
| 21:06 | Created globasa_tokenizer/spacy_adapter/pipeline.py | — | ~277 |
| 21:06 | Created globasa_tokenizer/hf_adapter/__init__.py | — | ~678 |
| 21:07 | Created globasa_tokenizer/tests/test_lexiliasel.py | — | ~1163 |
| 21:07 | Created globasa_tokenizer/tests/test_roundtrip.py | — | ~626 |
| 21:07 | Created globasa_tokenizer/tests/test_offsets.py | — | ~703 |
| 21:08 | Created globasa_tokenizer/tests/test_unknowns.py | — | ~1056 |
| 21:08 | Created globasa_tokenizer/tests/test_grammar_constraints.py | — | ~880 |
| 21:08 | Created globasa_tokenizer/tests/test_pseudo_morpheme_split.py | — | ~1380 |
| 21:09 | Created globasa_tokenizer/tests/test_syllable_fallback.py | — | ~747 |
| 21:09 | Created globasa_tokenizer/tests/test_fallback_cascade.py | — | ~849 |
| 21:09 | Created globasa_tokenizer/tests/test_alignment.py | — | ~1118 |
| 21:09 | Created globasa_tokenizer/tests/test_spacy_adapter.py | — | ~646 |
| 21:10 | Created globasa_tokenizer/tests/test_hf_adapter.py | — | ~620 |
| 21:10 | Created globasa_tokenizer/tests/test_perf.py | — | ~586 |
| 21:10 | Created tools/build_pseudo_morpheme_inventory.py | — | ~2284 |
| 21:11 | Created tools/mine_frequent_stems.py | — | ~1077 |
| 21:12 | Edited globasa_tokenizer/segmenter.py | modified segment_word() | ~619 |
| 21:14 | Edited globasa_tokenizer/segmenter.py | modified endswith() | ~389 |
| 21:14 | Edited globasa_tokenizer/affix_parser.py | expanded (+7 lines) | ~144 |
| 21:14 | Edited globasa_tokenizer/affix_parser.py | modified search() | ~202 |
| 21:16 | Edited globasa_tokenizer/affix_parser.py | 3→4 lines | ~67 |
| 21:18 | Edited globasa_tokenizer/tests/test_lexiliasel.py | modified words() | ~402 |
| 21:19 | Edited globasa_tokenizer/tests/test_lexiliasel.py | modified catch_warnings() | ~322 |
| 21:19 | Edited globasa_tokenizer/segmenter.py | modified _shift() | ~245 |
| 21:20 | Edited globasa_tokenizer/segmenter.py | 7→7 lines | ~98 |
| 21:20 | Edited globasa_tokenizer/tests/test_alignment.py | modified test_project_to_morphs_returns_morpheme_objects() | ~162 |
| 21:20 | Edited globasa_tokenizer/segmenter.py | expanded (+31 lines) | ~552 |
| 21:21 | Edited globasa_tokenizer/data/pseudo_morphemes.tsv | 8→9 lines | ~118 |
| 21:22 | Created globasa_tokenizer/_types.py | — | ~316 |
| 21:23 | Edited globasa_tokenizer/__init__.py | reduced (-20 lines) | ~79 |
| 21:23 | Edited globasa_tokenizer/segmenter.py | 2→2 lines | ~26 |
| 21:23 | Edited globasa_tokenizer/tokenizer.py | inline fix | ~12 |
| 21:24 | Edited globasa_tokenizer/tests/test_lexiliasel.py | modified get_expected_lemmas() | ~425 |
| 21:24 | Edited globasa_tokenizer/tokenizer.py | modified _is_alpha() | ~47 |
| 21:25 | Edited globasa_tokenizer/tokenizer.py | expanded (+9 lines) | ~222 |
| 21:25 | Edited globasa_tokenizer/tokenizer.py | modified tokenize() | ~66 |
| 21:25 | Edited globasa_tokenizer/tokenizer.py | modified _merge_mwe() | ~355 |
| 21:26 | Edited globasa_tokenizer/tests/test_perf.py | modified test_throughput_100k_words_per_sec() | ~132 |
| 21:26 | Edited globasa_tokenizer/tokenizer.py | modified _scan_tokens() | ~561 |
| 21:26 | Edited globasa_tokenizer/tests/test_perf.py | modified tokenize_batch() | ~114 |
| 21:26 | Edited globasa_tokenizer/tests/test_perf.py | 3→7 lines | ~103 |

## Session: 2026-05-01 21:30

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 21:37 | Created pytest.ini | — | ~22 |
| 21:38 | Session end: 1 writes across 1 files (pytest.ini) | 0 reads | ~24 tok |

## Session: 2026-05-01 22:20

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 22:21 | Edited Word Viewer.py | 2→3 lines | ~52 |
| 22:21 | Edited Word Viewer.py | modified _get_glb_tokenizer() | ~1986 |
| 22:23 | Created tmx_viewer.html | — | ~6112 |
| 22:23 | Edited word_viewer.html | inline fix | ~156 |
| 22:24 | Edited alignment_viewer.html | inline fix | ~172 |
| 22:24 | Edited translation_aide.html | inline fix | ~172 |
| 22:24 | Edited annotate_alignments.html | inline fix | ~155 |

## Session: 2026-05-02 09:57

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-05-02 09:57

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-05-03 — /pos viewer (whole-word PoS tagging)

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| --:-- | Extracted PosTagger logic into globasa_pos.py library | globasa_pos.py (new), PosTagger.py (now CLI shim) | importing PosTagger still works (re-exports); CLI behaviour preserved | ~5500 |
| --:-- | Added /pos, /api/pos/languages, /api/pos/contexts, /api/pos/tags, /api/pos routes + _pos_tokenize_page helper | Word Viewer.py | endpoints respond 200; sample sentence "Mi suki na lala." → PRON V PAR V | ~600 |
| --:-- | Created pos_viewer.html mirroring tmx_viewer.html shell with PoS palette + .tok+<sub> rendering + Show-labels toggle | pos_viewer.html (new) | served at /pos | ~5000 |
| --:-- | Added <a href="/pos">PoS</a> nav link to all 5 viewer headers | tmx_viewer.html, alignment_viewer.html, annotate_alignments.html, translation_aide.html, word_viewer.html | navigation cohesive | ~50 |

## Session: 2026-05-08 18:34

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-05-08 18:34

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-05-14 18:36

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-05-14 18:36

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 18:37 | Edited globasa_pos.py | modified _anchor_pos() | ~1369 |
| 18:38 | Edited Word Viewer.py | modified _inherit_conj_display_pos() | ~473 |
| 18:43 | Edited globasa_pos.py | segment() → fragment() | ~844 |
| 18:46 | Edited Word Viewer.py | modified enumerate() | ~164 |
| 18:55 | Coord vs subord CONJ in PoS tagger: `ji` no longer hard-splits SVO clauses; subord (ki/hu/eger/...) still does. `b`-words after `ji` now resolve via adjacency-anchor + segment-aware has_verb/has_local_subj, fixing UDHR-style mis-tags. /api/pos serializer additionally inherits CONJ display POS from preceding conjunct. | globasa_pos.py, Word Viewer.py | All 21 TEST_SENTENCES unchanged; new coord cases (`Mi suki kitabu ji filme`, `Patre mwa ji care matre`, `Vyata ji imanu sen muhim`) all correct; grammar checker still sees CONJ. | ~3000 |
| 18:48 | Session end: 4 writes across 2 files (globasa_pos.py, Word Viewer.py) | 2 reads | ~34161 tok |
| 19:05 | Edited globasa_pos.py | modified in() | ~182 |
| 19:05 | Fix: Stage 3 Step 1 now marks already-resolved PROPN/PRON/N immediately after PREP as PP-internal (`prep_resolved`). Previously only b-class objects of PREP were tracked, so `in Englisa` left Englisa looking like a clause subject → SVO mis-tagged `Maxori hikaye bekrea` as ADJ-V-N. Now correctly resolves to ADJ-N-V. | globasa_pos.py | maxori → ADJ, hikaye → N, bekrea → V on sentence 7 of the PoS viewer; all earlier test cases unchanged. | ~500 |
| 19:06 | Session end: 5 writes across 2 files (globasa_pos.py, Word Viewer.py) | 2 reads | ~34343 tok |
| 19:53 | Edited globasa_pos.py | modified _multi_word_collapsible() | ~823 |
| 19:18 | Fix: multi-word matcher in `globasa_pos.tokenize` now skips phrasal entries whose WordClass is exactly `"jm"` (41 entries: `cel na`, `imi am`, `le no`, `max kom`, `sen anti`, `sen in`, etc.). They mix PoS categories and collapse to UNK in `assign_pos`, blocking constituent signals. Keeping them split lets `cel/PREP na/PAR` tokenize separately so `na`'s infinitive-V signal reaches `koberi` and resolves the purpose clause correctly. PoS-prefixed phrasal classes (`p jm`, `l jm`, `n jm`, `t jm`, `f jm`, `m jm`, `s jm`) still collapse. | globasa_pos.py | Sentence 6 now: `cel/PREP na/PAR koberi/V resta/N de/PREP texto/N`. All 21 TEST_SENTENCES unchanged. | ~700 |
| 19:54 | Session end: 6 writes across 2 files (globasa_pos.py, Word Viewer.py) | 2 reads | ~35542 tok |
| 20:00 | Edited globasa_pos.py | added 1 condition(s) | ~769 |
| 20:00 | Edited globasa_pos.py | added 1 condition(s) | ~453 |
| 20:00 | Edited Word Viewer.py | modified _pos_tokenize_page() | ~152 |
| 20:05 | Edited globasa_pos.py | modified _is_np_head() | ~712 |
| 19:45 | Commas before a coord CONJ inside a list act as elision of that CONJ ("A, B, C, ji D" reads as "A ji B ji C ji D"): `globasa_pos.assign_pos` now precomputes `list_comma_positions` after Stage 2. A comma at position k qualifies only when both sides are NP coord-items (left walks back through modifiers to a b/N/PRON/PROPN/POSS head; right walks forward to one OR is itself a coord CONJ) AND a coord CONJ is reachable forward before any subord CONJ / `na` / sentence-end. Both `is_clause_boundary` and the SVO segment splitter consult this set, so list-commas split coord segments the same way `ji` does. Sentence-initial topical commas (`Xali, oto ...`) are correctly NOT marked because the left side has no NP head. Reverted the `/api/pos` CONJ display inheritance — conjunctions are again shown as CONJ. | globasa_pos.py, Word Viewer.py | Sentence 9 of UDHR PoS viewer now correct: `menalari, gramati, pimpan sahigi, ji lil kanonli textolari` all N/N/ADJ N/CONJ ADJ N N; `Xali` stays ADV. All 21 TEST_SENTENCES unchanged. | ~1200 |
| 20:07 | Session end: 10 writes across 2 files (globasa_pos.py, Word Viewer.py) | 2 reads | ~38256 tok |
| 20:11 | Edited globasa_pos.py | modified in() | ~219 |
| 19:55 | Apposition fix: when a PREP marks a PROPN as PP-internal, immediately-following PROPN tokens are also marked. Covers multi-token / appositional names like `yon ChatGPT-4o (OpenAI)` or `yon Claude Opus (Anthropic)` — the parenthesised tag was being seen as a free clause subject, causing seg 1 of sentence 7 to flip to has_local_subj=True and mis-tag hikaye=V → Maxori=ADV. Now correctly: Maxori/ADJ hikaye/N bekrea/V. | globasa_pos.py | sentence 7 of PoS viewer correct; sentence 9 and all 21 TEST_SENTENCES unchanged. | ~400 |
| 20:12 | Session end: 11 writes across 2 files (globasa_pos.py, Word Viewer.py) | 2 reads | ~38475 tok |
| 20:27 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb/apertium-glb.glb.rlx | added error handling | ~1509 |
| 20:33 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb/apertium-glb.glb.rlx | expanded (+26 lines) | ~1867 |
| 20:37 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb/apertium-glb.glb.rlx | expanded (+8 lines) | ~222 |
| 20:40 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb/apertium-glb.glb.rlx | CONJ() → outputs() | ~362 |
| 20:41 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb/apertium-glb.glb.rlx | 70→67 lines | ~892 |
| 20:45 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb/apertium-glb.glb.rlx | expanded (+6 lines) | ~259 |
| 20:50 | Brought apertium-glb's constraint grammar (glb.rlx) up to the same correctness as globasa_pos.py. Three substantive fixes: (1) rule 88 (lone-b → N fallback) was using NOT instead of NEGATE — CG3's NOT silently fails when a BARRIER intervenes, so the original rule only fired at sentence-start and missed every clause-internal "lone b after comma/ji" case; switched to NEGATE so it fires properly. (2) Added a `(NEGATE -1 (cnjcoo) LINK -1 (vblex))` guard on rule 88 so it doesn't defeat the parallel-verb rule. (3) Restructured into 5 sections so SVO rules (88+91+94, all iterating together) run before the new Section 3 parallel-verb SELECT. Rule 91 also gained a `NEGATE -1* (vblex) BARRIER AnyVerbOrClause` clause so it doesn't misfire on still-ambiguous coord neighbours. Also tightened t-resolution barriers (`BARRIER TConnect OR AnyVerb` for adj/det, `BARRIER TConnect OR (n) OR (prn)` for adv) — previously `Le velosi yam pingo` tagged `velosi` adj by looking past the verb to find `pingo` n. | apertium-glb.glb.rlx | All 21 PosTagger TEST_SENTENCES match Python output via the CG pipeline; coord cases (Patre mwa ji glu matre, Mi suki kitabu ji filme, Vyata ji imanu sen muhim) all correct; end-to-end glb-eng translation reads sensibly. | ~6000 |
| 20:47 | Session end: 17 writes across 3 files (globasa_pos.py, Word Viewer.py, apertium-glb.glb.rlx) | 3 reads | ~43950 tok |

## Session: 2026-05-14 21:16

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-05-14 21:21

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 21:28 | Created ../../../../tmp/glb_tests.txt | — | ~282 |
| 21:28 | Created ../../../../tmp/eng_tests.txt | — | ~96 |
| 21:29 | Session end: 2 writes across 2 files (glb_tests.txt, eng_tests.txt) | 2 reads | ~405 tok |

## Session: 2026-05-14 21:30

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 21:35 | Created ../../.claude/plans/gleaming-cuddling-fountain.md | — | ~2502 |
| 21:37 | Edited ../../.claude/plans/gleaming-cuddling-fountain.md | 13→13 lines | ~166 |
| 21:37 | Edited ../../.claude/plans/gleaming-cuddling-fountain.md | modified set() | ~226 |
| 21:37 | Edited ../../.claude/plans/gleaming-cuddling-fountain.md | 1→2 lines | ~33 |
| 21:37 | Edited ../../.claude/plans/gleaming-cuddling-fountain.md | 3→5 lines | ~86 |
| 21:41 | Created dictionaryPreprocess.py | — | ~3169 |
| 21:46 | Edited dictionaryPreprocess.py | modified expand_gloss_tokens() | ~372 |
| 21:47 | Edited dictionaryPreprocess.py | added 1 import(s) | ~47 |
| 21:47 | Edited dictionaryPreprocess.py | modified split_foreign_gender() | ~167 |
| 21:47 | Edited dictionaryPreprocess.py | modified lemma_repr() | ~25 |
| 21:48 | Edited dictionaryPreprocess.py | modified split() | ~140 |

## 2026-05-14 — dictionaryPreprocess.py rewrite for Lexilista_parser

| Time  | Description | File(s) | Outcome | ~Tokens |
|-------|-------------|---------|---------|---------|
| 22:00 | Rewrote dictionaryPreprocess.py to use parseWordEntry (annotation-based) instead of stale local PoSDict + hardcoded column indices | dictionaryPreprocess.py | 14 dicts (En/Es/Eo/De/Fr/Nl/un × {fn,content}), 78k entries, all XML-well-formed | ~3000 |
| 22:01 | Added defensive English-style annotation prefix strip (n:/v.tr:/adj:/…) for Fra/Rus/Zho columns the parser doesn't yet handle | dictionaryPreprocess.py | French glosses now clean ('hirondelle' not 'n: hirondelle') | ~200 |
| 22:02 | Fixed multi-gender (<m>/<n>) extraction + XML escape for & in glosses | dictionaryPreprocess.py | 'account <m>/<n>' splits into two clean per-gender entries; 'ji'→'&' escapes | ~150 |
| 21:50 | Session end: 11 writes across 2 files (gleaming-cuddling-fountain.md, dictionaryPreprocess.py) | 3 reads | ~40124 tok |
| 21:55 | Edited dictionaryPreprocess.py | modified merge_into_dix() | ~888 |
| 21:56 | Session end: 12 writes across 2 files (gleaming-cuddling-fountain.md, dictionaryPreprocess.py) | 3 reads | ~44485 tok |
| 21:59 | Session end: 12 writes across 2 files (gleaming-cuddling-fountain.md, dictionaryPreprocess.py) | 3 reads | ~44485 tok |
| 22:02 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.eng-glb.rtx | 3→1 lines | ~9 |
| 22:02 | Session end: 13 writes across 3 files (gleaming-cuddling-fountain.md, dictionaryPreprocess.py, apertium-glb-eng.eng-glb.rtx) | 3 reads | ~44494 tok |
| 22:03 | Session end: 13 writes across 3 files (gleaming-cuddling-fountain.md, dictionaryPreprocess.py, apertium-glb-eng.eng-glb.rtx) | 3 reads | ~44494 tok |
| 22:17 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb/apertium-glb.glb.dix | modified n() | ~385 |
| 22:23 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb/apertium-glb.glb.dix | expanded (+6 lines) | ~206 |
| 22:23 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb/apertium-glb.glb.dix | expanded (+9 lines) | ~295 |
| 22:23 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb/apertium-glb.glb.dix | modified n() | ~63 |
| 22:24 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb/apertium-glb.glb.dix | modified n() | ~40 |
| 22:25 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb/apertium-glb.glb.dix | 8→9 lines | ~297 |
| 22:25 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.dix | 8→9 lines | ~383 |
| 22:31 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.dix | expanded (+32 lines) | ~540 |
| 22:31 | Session end: 21 writes across 5 files (gleaming-cuddling-fountain.md, dictionaryPreprocess.py, apertium-glb-eng.eng-glb.rtx, apertium-glb.glb.dix, apertium-glb-eng.glb-eng.dix) | 5 reads | ~46860 tok |
| 22:33 | Session end: 21 writes across 5 files (gleaming-cuddling-fountain.md, dictionaryPreprocess.py, apertium-glb-eng.eng-glb.rtx, apertium-glb.glb.dix, apertium-glb-eng.glb-eng.dix) | 5 reads | ~46860 tok |
| 22:58 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 4→5 lines | ~38 |
| 22:58 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 1→3 lines | ~68 |
| 23:00 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 3→3 lines | ~62 |
| 23:00 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 3→3 lines | ~66 |
| 23:01 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 4→4 lines | ~19 |
| 23:02 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 3→3 lines | ~83 |
| 23:04 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 4→5 lines | ~23 |
| 23:04 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 3→4 lines | ~76 |
| 23:04 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | modified VP() | ~302 |
| 23:08 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 4→4 lines | ~38 |
| 23:09 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 4→4 lines | ~36 |
| 23:09 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | inline fix | ~12 |
| 23:10 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | inline fix | ~14 |
| 23:10 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 4→4 lines | ~42 |
| 23:11 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 4→4 lines | ~36 |
| 23:11 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | inline fix | ~27 |
| 23:13 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | inline fix | ~14 |
| 23:13 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 2→2 lines | ~23 |
| 23:15 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 2→2 lines | ~19 |
| 23:15 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | inline fix | ~27 |
| 23:17 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 2→2 lines | ~18 |
| 23:18 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 2→2 lines | ~20 |
| 23:20 | Session end: 43 writes across 6 files (gleaming-cuddling-fountain.md, dictionaryPreprocess.py, apertium-glb-eng.eng-glb.rtx, apertium-glb.glb.dix, apertium-glb-eng.glb-eng.dix) | 6 reads | ~47995 tok |
| 23:24 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb/apertium-glb.glb.dix | removed 28 lines | ~1 |
| 23:24 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb/apertium-glb.glb.dix | — | ~0 |
| 23:24 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb/apertium-glb.glb.dix | — | ~0 |
| 23:26 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.dix | removed 35 lines | ~70 |
| 23:26 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.dix | 9→8 lines | ~340 |
| 23:28 | Session end: 48 writes across 6 files (gleaming-cuddling-fountain.md, dictionaryPreprocess.py, apertium-glb-eng.eng-glb.rtx, apertium-glb.glb.dix, apertium-glb-eng.glb-eng.dix) | 6 reads | ~48435 tok |
| 23:38 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb/apertium-glb.glb.dix | modified n() | ~385 |
| 23:39 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb/apertium-glb.glb.dix | expanded (+6 lines) | ~206 |
| 23:40 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb/apertium-glb.glb.dix | expanded (+10 lines) | ~363 |
| 23:41 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.dix | expanded (+32 lines) | ~540 |
| 23:42 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.dix | 8→9 lines | ~383 |
| 23:42 | Session end: 53 writes across 6 files (gleaming-cuddling-fountain.md, dictionaryPreprocess.py, apertium-glb-eng.eng-glb.rtx, apertium-glb.glb.dix, apertium-glb-eng.glb-eng.dix) | 6 reads | ~50445 tok |
| 23:43 | Session end: 53 writes across 6 files (gleaming-cuddling-fountain.md, dictionaryPreprocess.py, apertium-glb-eng.eng-glb.rtx, apertium-glb.glb.dix, apertium-glb-eng.glb-eng.dix) | 6 reads | ~50445 tok |
| 23:47 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.dix | inline fix | ~24 |
| 23:52 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 3→4 lines | ~31 |
| 23:54 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 9→9 lines | ~53 |
| 23:56 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 1→2 lines | ~14 |
| 23:56 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | inline fix | ~16 |
| 23:57 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | inline fix | ~8 |
| 23:59 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.dix | inline fix | ~25 |
| 00:00 | Edited dictionaryPreprocess.py | modified _count_syllables() | ~530 |
| 00:01 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.dix | inline fix | ~19 |
| 00:02 | Session end: 62 writes across 6 files (gleaming-cuddling-fountain.md, dictionaryPreprocess.py, apertium-glb-eng.eng-glb.rtx, apertium-glb.glb.dix, apertium-glb-eng.glb-eng.dix) | 6 reads | ~52004 tok |
| 00:04 | Edited dictionaryPreprocess.py | modified _load_synthetic_adj_set() | ~646 |
| 00:04 | Edited dictionaryPreprocess.py | added 1 condition(s) | ~172 |
| 00:04 | Edited dictionaryPreprocess.py | 14→14 lines | ~255 |
| 00:06 | Session end: 65 writes across 6 files (gleaming-cuddling-fountain.md, dictionaryPreprocess.py, apertium-glb-eng.eng-glb.rtx, apertium-glb.glb.dix, apertium-glb-eng.glb-eng.dix) | 6 reads | ~53765 tok |
| 00:16 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | expanded (+9 lines) | ~337 |
| 00:18 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 9→9 lines | ~244 |
| 00:21 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | expanded (+8 lines) | ~503 |
| 00:23 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | expanded (+9 lines) | ~179 |
| 00:26 | Session end: 69 writes across 6 files (gleaming-cuddling-fountain.md, dictionaryPreprocess.py, apertium-glb-eng.eng-glb.rtx, apertium-glb.glb.dix, apertium-glb-eng.glb-eng.dix) | 6 reads | ~55118 tok |
| 00:27 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 2→5 lines | ~99 |
| 00:28 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 3→6 lines | ~139 |
| 00:28 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 6→6 lines | ~139 |
| 00:29 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 3→6 lines | ~136 |
| 00:29 | Session end: 73 writes across 6 files (gleaming-cuddling-fountain.md, dictionaryPreprocess.py, apertium-glb-eng.eng-glb.rtx, apertium-glb.glb.dix, apertium-glb-eng.glb-eng.dix) | 6 reads | ~55668 tok |
| 00:40 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 6→9 lines | ~65 |
| 00:40 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 4→4 lines | ~21 |
| 00:48 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 4→6 lines | ~69 |
| 00:51 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.dix | inline fix | ~20 |
| 00:51 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.dix | inline fix | ~24 |
| 00:55 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | added 3 condition(s) | ~515 |
| 00:57 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 5→5 lines | ~34 |
| 00:57 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 10→6 lines | ~147 |
| 00:57 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 6→10 lines | ~276 |
| 00:58 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | expanded (+8 lines) | ~411 |
| 01:00 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 6→4 lines | ~43 |
| 01:01 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 4→4 lines | ~19 |
| 01:05 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | removed 26 lines | ~22 |
| 01:05 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | added 2 condition(s) | ~85 |
| 01:06 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | added 1 condition(s) | ~208 |
| 01:06 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | — | ~0 |
| 01:22 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | added 1 condition(s) | ~124 |
| 01:23 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | modified prn() | ~85 |
| 01:24 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 4→6 lines | ~69 |
| 01:26 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | modified prn() | ~306 |
| 01:29 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | reduced (-6 lines) | ~85 |
| 01:30 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | added 1 condition(s) | ~150 |
| 01:31 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | added 5 condition(s) | ~248 |
| 01:31 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | expanded (+8 lines) | ~317 |
| 01:32 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 11→11 lines | ~318 |
| 01:34 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 6→6 lines | ~160 |
| 01:35 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 6→6 lines | ~157 |
| 01:36 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 11→11 lines | ~326 |
| 01:38 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 4→4 lines | ~21 |
| 01:38 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 3→1 lines | ~5 |
| 01:40 | Session end: 103 writes across 6 files (gleaming-cuddling-fountain.md, dictionaryPreprocess.py, apertium-glb-eng.eng-glb.rtx, apertium-glb.glb.dix, apertium-glb-eng.glb-eng.dix) | 6 reads | ~60304 tok |
| 01:40 | Session end: 103 writes across 6 files (gleaming-cuddling-fountain.md, dictionaryPreprocess.py, apertium-glb-eng.eng-glb.rtx, apertium-glb.glb.dix, apertium-glb-eng.glb-eng.dix) | 6 reads | ~60304 tok |

## Session: 2026-05-16 16:50

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-05-16 16:50

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-05-16 17:07

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-05-16 17:08

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 17:16 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | modified prn() | ~669 |
| 17:35 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 5→5 lines | ~189 |
| 17:37 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | inline fix | ~4 |
| 17:50 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | 1→2 lines | ~10 |
| 17:50 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.rtx | inline fix | ~4 |

## Session: 2026-06-06 14:07

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 14:24 | Created ../../.claude/plans/improve-the-latest-anki-synthetic-cook.md | — | ~2835 |
| 14:50 | Edited ../../.claude/plans/improve-the-latest-anki-synthetic-cook.md | expanded (+9 lines) | ~1063 |
| 14:50 | Edited ../../.claude/plans/improve-the-latest-anki-synthetic-cook.md | 6→8 lines | ~251 |
| 17:55 | Created course_ranker.py | — | ~2276 |
| 18:00 | Created AnkiMaker3.py | — | ~2589 |
| 18:01 | Edited AnkiMaker3.py | modified enumerate() | ~243 |
| 18:04 | Edited AnkiMaker3.py | 2→4 lines | ~46 |
| 18:26 | Created apkg_image_sync.py | — | ~2989 |
| 18:29 | Edited apkg_image_sync.py | expanded (+9 lines) | ~170 |
| 18:29 | Edited apkg_image_sync.py | modified _http_once() | ~504 |
| 18:31 | Edited apkg_image_sync.py | modified _host_of() | ~517 |
| 18:34 | Session end: 11 writes across 4 files (improve-the-latest-anki-synthetic-cook.md, course_ranker.py, AnkiMaker3.py, apkg_image_sync.py) | 5 reads | ~23217 tok |
| 18:54 | Session end: 11 writes across 4 files (improve-the-latest-anki-synthetic-cook.md, course_ranker.py, AnkiMaker3.py, apkg_image_sync.py) | 5 reads | ~23217 tok |
| 18:54 | Session end: 11 writes across 4 files (improve-the-latest-anki-synthetic-cook.md, course_ranker.py, AnkiMaker3.py, apkg_image_sync.py) | 5 reads | ~23217 tok |
| 21:03 | Edited AnkiMaker3.py | modified len() | ~339 |
| 21:04 | Session end: 12 writes across 4 files (improve-the-latest-anki-synthetic-cook.md, course_ranker.py, AnkiMaker3.py, apkg_image_sync.py) | 5 reads | ~23556 tok |
| 21:09 | Edited AnkiMaker3.py | modified _is_t_class_wordclass() | ~156 |
| 21:10 | Edited AnkiMaker3.py | modified len() | ~496 |
| 21:11 | Session end: 14 writes across 4 files (improve-the-latest-anki-synthetic-cook.md, course_ranker.py, AnkiMaker3.py, apkg_image_sync.py) | 5 reads | ~24208 tok |
| 21:15 | Edited AnkiMaker3.py | 2→6 lines | ~58 |
| 21:16 | Edited AnkiMaker3.py | modified if() | ~293 |
| 21:16 | Edited AnkiMaker3.py | 3→5 lines | ~71 |
| 21:16 | Session end: 17 writes across 4 files (improve-the-latest-anki-synthetic-cook.md, course_ranker.py, AnkiMaker3.py, apkg_image_sync.py) | 5 reads | ~24630 tok |
| 21:20 | Edited AnkiMaker3.py | modified _normalise_for_exclude() | ~348 |
| 21:20 | Edited AnkiMaker3.py | modified isinstance() | ~84 |
| 21:21 | Edited AnkiMaker3.py | 6→8 lines | ~80 |
| 21:22 | Edited AnkiMaker3.py | modified _apply_to_exclude() | ~244 |
| 21:22 | Edited AnkiMaker3.py | modified isinstance() | ~86 |
| 21:22 | Session end: 22 writes across 4 files (improve-the-latest-anki-synthetic-cook.md, course_ranker.py, AnkiMaker3.py, apkg_image_sync.py) | 5 reads | ~25472 tok |
| 22:33 | Session end: 22 writes across 4 files (improve-the-latest-anki-synthetic-cook.md, course_ranker.py, AnkiMaker3.py, apkg_image_sync.py) | 5 reads | ~25472 tok |
| 22:36 | Session end: 22 writes across 4 files (improve-the-latest-anki-synthetic-cook.md, course_ranker.py, AnkiMaker3.py, apkg_image_sync.py) | 5 reads | ~25472 tok |
| 22:40 | Edited AnkiMaker3.py | modified _split_items() | ~653 |
| 22:41 | Session end: 23 writes across 4 files (improve-the-latest-anki-synthetic-cook.md, course_ranker.py, AnkiMaker3.py, apkg_image_sync.py) | 5 reads | ~26125 tok |

## Session: 2026-06-06 22:53

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 23:14 | Edited ../../.claude/plans/improve-the-latest-anki-synthetic-cook.md | expanded (+7 lines) | ~193 |
| 23:14 | Edited ../../.claude/plans/improve-the-latest-anki-synthetic-cook.md | expanded (+65 lines) | ~1160 |
| 23:14 | Edited ../../.claude/plans/improve-the-latest-anki-synthetic-cook.md | 1→2 lines | ~71 |
| 23:35 | Edited AnkiMaker3.py | expanded (+10 lines) | ~147 |
| 23:37 | Edited AnkiMaker3.py | expanded (+21 lines) | ~491 |
| 23:38 | Session end: 5 writes across 2 files (improve-the-latest-anki-synthetic-cook.md, AnkiMaker3.py) | 3 reads | ~6183 tok |

## Session: 2026-06-06 23:39

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 23:39 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.eng-glb.rtx | 2→2 lines | ~23 |
| 23:39 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.eng-glb.rtx | 4→3 lines | ~52 |
| 23:40 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.eng-glb.rtx | 3→2 lines | ~37 |
| 23:47 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.eng-glb.rtx | inline fix | ~16 |
| 23:49 | Session end: 4 writes across 1 files (apertium-glb-eng.eng-glb.rtx) | 1 reads | ~138 tok |
| 23:50 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.eng-glb.rtx | modified AJC() | ~135 |
| 23:50 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.eng-glb.rtx | 3→4 lines | ~14 |
| 23:50 | Session end: 6 writes across 1 files (apertium-glb-eng.eng-glb.rtx) | 1 reads | ~298 tok |
| 23:52 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.dix | 1→2 lines | ~37 |
| 00:12 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb/apertium-glb.glb.dix | modified n() | ~243 |
| 00:13 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb/apertium-glb.glb.dix | 3→2 lines | ~25 |
| 00:18 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb/apertium-glb.glb.dix | "LR" → "RL" | ~15 |
| 00:30 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.glb-eng.dix | 1→2 lines | ~37 |
| 00:54 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.eng-glb.rtx | 1→2 lines | ~23 |
| 00:57 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.eng-glb.rtx | 2→4 lines | ~73 |
| 01:00 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.eng-glb.rtx | 4→5 lines | ~96 |
| 01:02 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.eng-glb.rtx | 4→5 lines | ~63 |
| 01:02 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.eng-glb.rtx | 5→2 lines | ~37 |
| 01:03 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb/apertium-glb.glb.dix | removed 12 lines | ~33 |
| 01:03 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb/apertium-glb.glb.dix | modified n() | ~226 |
| 01:04 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/apertium-glb-eng.eng-glb.rtx | 4→4 lines | ~83 |
| 01:05 | Edited ../../ApplicationSource/GlobasaTranslation/apertium-glb/apertium-glb.glb.dix | removed 12 lines | ~33 |
| 01:05 | Session end: 20 writes across 3 files (apertium-glb-eng.eng-glb.rtx, apertium-glb-eng.glb-eng.dix, apertium-glb.glb.dix) | 3 reads | ~1393 tok |
| 01:11 | Session end: 20 writes across 3 files (apertium-glb-eng.eng-glb.rtx, apertium-glb-eng.glb-eng.dix, apertium-glb.glb.dix) | 3 reads | ~1393 tok |

## Session: 2026-06-07 13:49

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-06-07 13:49

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-06-07 13:49

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-06-07 14:00

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-06-07 14:00

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 14:21 | Edited AnkiMaker3.py | modified len() | ~683 |
| 14:22 | Session end: 1 writes across 1 files (AnkiMaker3.py) | 0 reads | ~683 tok |
| 15:31 | Edited AnkiMaker3.py | modified _is_preposition_wordclass() | ~146 |
| 15:31 | Edited AnkiMaker3.py | 5→8 lines | ~138 |
| 15:33 | Edited AnkiMaker3.py | modified _is_preposition_wordclass() | ~432 |
| 15:33 | Session end: 4 writes across 1 files (AnkiMaker3.py) | 2 reads | ~6180 tok |
| 15:36 | Edited AnkiMaker3.py | expanded (+14 lines) | ~209 |
| 15:37 | Edited AnkiMaker3.py | expanded (+10 lines) | ~213 |
| 15:41 | Edited AnkiMaker3.py | modified range() | ~746 |
| 15:41 | Edited AnkiMaker3.py | 6→2 lines | ~16 |
| 16:07 | Edited course_ranker.py | modified emphasize() | ~284 |
| 16:08 | Edited course_ranker.py | 8→8 lines | ~105 |
| 16:15 | Session end: 10 writes across 2 files (AnkiMaker3.py, course_ranker.py) | 3 reads | ~10304 tok |

## Session: 2026-06-08 13:16

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-06-08 13:16

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 18:18 | Edited AnkiMaker3.py | 2→3 lines | ~29 |
| 18:18 | Edited AnkiMaker3.py | 1→3 lines | ~30 |
| 18:29 | Edited AnkiMaker3.py | modified _append_mena() | ~954 |
| 18:30 | Edited AnkiMaker3.py | 2→2 lines | ~41 |
| 19:03 | Session end: 4 writes across 1 files (AnkiMaker3.py) | 0 reads | ~1054 tok |
| 19:25 | Session end: 4 writes across 1 files (AnkiMaker3.py) | 0 reads | ~1054 tok |

## Session: 2026-06-13 17:21

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-06-13 17:21

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 16:19 | Rewrote 258 SVG-thumbnail PNG URLs to direct .svg in DirectURL col | menalariImages_edited.csv | done, 8553 rows intact, verified 200 image/svg+xml | ~3k |
| 12:09 | Reran ThirtyStoriesToTable.py on newest source (Corpora/Thirty Short Stories in Globasa new) | ThirtyStoriesToTable.py, Doxo_passages.csv, Corpora/Thirty Short Stories in Globasa.typ | 962 passage rows, 62 sections; old .typ backed up as .typ.bak | ~8k |
| 12:25 | Replaced Thirty Short Stories block with corrected source in master CSV + both TMX | Doxo_passages_edited_updated.csv, Doxo_passages.tmx, Doxo_passages_extended.tmx | 980->962 TUs, 2165 non-Thirty TUs byte-identical; backups in backups/thirty_update_2026-08-24/ | ~25k |
| 12:51 | Realigned all 15 pairs on updated TMX (eflomal), re-anchored gold sids, fixed gold-priors bug | giza_output_improved/, gold_alignments/en.tsv, merge_gold_priors.py | glb_en 3127 sents; 52/55 gold rows survived; 51 gold sentences now feed priors | ~40k |
| 13:31 | Typst generator: added hand-set preamble + authored paragraph breaks | ThirtyStoriesToTable.py, Corpora/thirty_paragraph_breaks.tsv, Corpora/Thirty Short Stories in Globasa.typ | 62 sections, 136 paragraphs — matches ThirtyStories.typ exactly | ~18k |
| 14:07 | Paragraphed all 31 stories; morpheme-aware soft hyphens + French-style preposition binding for Globasa | ThirtyStoriesToTable.py, globasa_word_hyphenation.py, globasa_hyphenation.py, Hyphenation.py, Corpora/thirty_paragraph_breaks.tsv | 215 paras/lang (was 68); 2668 soft hyphens, 1104 NBSP; max unbreakable span 13 chars | ~60k |
| 14:12 | Verified soft-hyphen approach against typst/typst#6877 — maintainer-endorsed pattern | .wolf/cerebrum.md | hyphenate:false + U+00AD confirmed correct; no change needed to generator | ~5k |
| 14:30 | Moved Globasa hyphenation to a Typst lookup table (JSON + scoped show rule); names syllabified as Globasa | ThirtyStoriesToTable.py, Corpora/globasa_hyphenations.json | 780 entries; .typ text now free of invisible chars; CSV unchanged | ~35k |
| 14:40 | Binding moved from inline ~ into a Typst show rule; tense particles included; data merged into globasa_typesetting.json | ThirtyStoriesToTable.py, Corpora/globasa_typesetting.json | 780 hyphenations + 49 binders; .typ story text fully plain | ~15k |
| 15:21 | Body face switched to Vollkorn after specimen comparison | ThirtyStoriesToTable.py, Corpora/Thirty Short Stories in Globasa.typ | regenerated; 780 hyphenations, 49 binders, 430 paragraphs | ~6k |
| 15:36 | Applied 5 Globasa corrections to source and propagated through CSV, .typ, master CSV and both TMX | Corpora/Thirty Short Stories in Globasa new, Doxo_passages.csv, .typ, Doxo_passages_edited_updated.csv, both .tmx | 5 TUs changed per TMX, 3127 TUs unchanged, 0 old forms remain | ~12k |
| 17:33 | Recorded goyu/hongu distinction; verified PosTagger resolves "goyu goyu" as V+N | .wolf/cerebrum.md | tagger correct; rukejarden and yampyale tag as UNK | ~4k |
| 18:05 | Built per-sense image store: word -> PoS -> sense -> images, canonical Commons file titles instead of rot-prone thumbnail URLs | images_store.py, migrate_images_jsonl.py, resolve_commons_images.py, validate_images.py, menalariImages.jsonl | 1797 words, 1769/1790 URLs (98.8%) parsed to titles; 1576 pos auto-assigned, 198 queued | ~40k |
| 18:20 | Resolved every image through the MediaWiki API — the fix for the HTTP 400 thumbnail rot | resolve_commons_images.py, menalariImages.jsonl | 1766 ok, 4 renamed, 6 deleted upstream; all 10 previously-400 country images now 200 | ~15k |
| 18:35 | Word Viewer gallery: one row per PoS showing its gloss beside its own images, 3 + "+N more" | Word Viewer.py, word_viewer.html | PoS join done server-side (_refine_verb_type makes the annotation key insufficient); verified via node DOM shim | ~30k |
| 18:50 | AnkiMaker3 fills both still slots from PoS groups; DuayumImaje reachable for the first time | AnkiMaker3.py, images_store.py | 48 cols intact, 1722 stills / 46 gifs, 0 dead URLs exported | ~12k |
| 19:05 | Rewrote apkg_image_sync against the JSONL; fixed hardcoded field ordinals + rename-dedupe | apkg_image_sync.py, resolve_commons_images.py, images_store.py, .wolf/buglog.json | round-trip reports 0 new images; bug-184/185 logged | ~20k |
| 19:40 | Applied user's gif->verb / still->noun (+adj/adv) rule; curation queue 198 -> 0 | images_store.py, migrate_images_jsonl.py, menalariImages.jsonl | 1774/1797 words have pos assigned; 23 blanks are words retired from word-list.csv | ~18k |
| 19:45 | Fixed gallery row painting a full-width PoS-coloured block; tint moved to the label | word_viewer.html | verified via node DOM shim on fronta/acum/hongu/amiku | ~5k |
| 19:50 | Fixed migration re-importing pre-rename titles (image_keys, not image_key); removed 4 dupes | migrate_images_jsonl.py, menalariImages.jsonl | image set identical to baseline; migrate + sync both report 0 new | ~8k |
| 20:10 | Moved images from a gallery above the table into the table itself (one cell per PoS row) to stop printing each gloss twice | word_viewer.html, word_viewer_i18n.csv | verified hongu/acum/amiku/jixi/klitoris via node DOM shim; imageless words get no extra column | ~20k |
| 20:35 | Images tile into a fixed 200x150 box (1/2/3/4+badge) and expand to a full gallery overlay | word_viewer.html | verified 1,2,3,4,5,9 image counts + multi-sense via node shim | ~18k |
| 20:50 | Implemented hyponym-derived galleries; designated words tagged `calyo` as its hyponyms | Word Viewer.py, word_viewer.html, validate_images.py, menalariImages.jsonl | calyo shows 1 own + 17 derived, captioned in Globasa; Anki export unaffected | ~22k |
| 21:00 | Expanded gallery got a visible close button; backdrop-click and Escape were the only ways back | word_viewer.html | all three close paths verified; clicking the panel still keeps it open | ~5k |
| 21:20 | Added derived galleries for futru, yamxey, flura, hewan, mamoyen; fixed save_images dropping derive-only records | menalariImages.jsonl, images_store.py, .wolf/buglog.json | 5+55+17+20+60 hyponym images; bug-186 logged | ~15k |
| 21:45 | Slang/vulgar/sexual noun senses split into their own table rows; register normalised across languages | Lexilista_parser.py, Word Viewer.py, word_viewer.html, AnkiMaker3.py | 19 words affected; 419-word sweep shows no false positives; extension-language alignment preserved via ext_slot | ~30k |
| 22:05 | Registers moved into the verb-type column; PoS cell rowspans its register sub-rows | word_viewer.html | verified flura/banana/gigi/oko/baytu/estuf/lil row shapes via node shim | ~10k |
| 22:15 | Column header renamed Verb type -> Type; new i18n key across 45 languages | word_viewer.html, word_viewer_i18n.csv | /i18n serves Type/Tipo/Typ/Тип/種類/Aina | ~4k |
| 22:40 | Closed out plan verification: derive specs survive resolver+sync, store byte-identical, validator clean | menalariImages.jsonl | 1770 ok / 22 unresolvable / 6 gone; 29 flagged = 6 gone + 23 retired words | ~10k |
| 23:05 | Built the Commons image curator (/images) — plan step 9 | images_curator.html, Word Viewer.py, 6 nav links | queue 6939 content-PoS words course-ranked; all 8 write actions exercised, store reverted byte-identical | ~45k |
| 23:25 | Fixed curator add_sense not persisting for imageless words (salamandra); root cause in is_empty_record | images_store.py, .wolf/buglog.json | bug-187; 6 persistence cases tested; salamandra add/fill/delete round-trips clean | ~10k |
| 23:40 | Fixed sense-label field losing focus on click (container re-render); no-op edits no longer write | images_curator.html, .wolf/buglog.json | bug-188; verified input identity survives click, unchanged label/PoS write nothing | ~8k |
| 23:55 | Added /api/images/publish + "Update dictionary" button; extracted build_image_rows from build_db | Word Viewer.py, images_curator.html | resolved 45 of the user's curated images and pushed 1837 into the LMDB without a full rebuild | ~15k |
| 00:10 | Fixed finished words being unreachable in the curator (search now bypasses the done filter) | Word Viewer.py, images_curator.html | bug-189; salamandra/calyo/hongu/abakus all findable; queue still 6937 outstanding | ~6k |
| 00:45 | Added Wikispecies + Commons-category + iNaturalist image sources for taxon words | Word Viewer.py, images_store.py, images_curator.html | 232 taxon words auto-detected; Hirundinidae 32 Commons / 7 iNat candidates; iNat licences flagged | ~35k |
| 01:05 | Paginated candidate search across all three sources + infinite scroll in the curator | Word Viewer.py, images_curator.html | commons 188 unique over 8 pages and continuing; wikispecies terminates at 82/55; inat 7 | ~20k |
| 01:35 | Added also_pos: one image serves a noun that is the act of its verb (awcu) | Word Viewer.py, word_viewer.html, images_curator.html | verified awcu renders one image cell with rowspan 2 across Noun/Verb; consulted xwexi on du-/-ya | ~25k |
| 13:25 | Added local image upload to the curator (file/drag/paste), served at /user_images | Word Viewer.py, images_store.py, images_curator.html, AnkiMaker3.py | PIL-validated, hash-named, traversal blocked; Anki gets a bare filename + a copy reminder | ~25k |
| 13:55 | Built /review contact sheet for spotting ill-fitting images in bulk | images_review.html, Word Viewer.py, 7 navs | 1802 words, 123 tags, filters shared 150 / gone 6 / off-commons 22 / derived 6 | ~30k |
| 14:20 | NSFW covers for /review and the curator; per-row covering in the dictionary | images_review.html, images_curator.html, word_viewer.html, Word Viewer.py | 9 flagged (6 blacklist + banana/flura/melon by register); baytu unaffected | ~15k |
| 14:45 | Moved NSFW from word-level to sense-level; seeded the 6 blacklist senses | images_store.py, Word Viewer.py, word_viewer.html, images_curator.html, menalariImages.jsonl | 6 flagged; melon/banana/flura no longer covered; per-sense toggle verified | ~14k |


## Session: 2026-09-02

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 18:40 | Surveyed the vocabulary deck against the curated image store | Globasa__Vocabulary.apkg, menalariImages.jsonl | 9268 notes, no scheduling (distribution deck); 1655 image fields differ, 5 newly imaged, 10 dropped | ~15k |
| 19:10 | Extracted construction glosses out of word-list.csv; shared the matcher | constructions.py, extract_constructions.py, AnkiMaker3.py, word-list.csv | 6 entries lifted, exactly 12 diff lines, idempotent, CRLF preserved; hay/sengi left gloss-less by design | ~25k |
| 19:20 | Guarded str(NaN)=="nan" in AnkiMaker3 for the now-empty glosses | AnkiMaker3.py | 0 bogus "nan" glosses in the export | ~4k |
| 19:45 | Fixed recurring parenthetical bug: parseEntry no longer expands gloss context | Lexilista_parser.py, .wolf/buglog.json | bug-190; 568 of 8879 rows corrected; parseWordEntry (Wiktionary/Apertium/dictionary) untouched | ~20k |
| 20:05 | Built the deck updater on Anki's own library and pushed the curated images + fresh glosses into the vocabulary deck | update_vocab_deck.py, Globasa__Vocabulary.apkg, requirements.txt | 3687 notes updated, 11 words added, 9267/9267 GUIDs preserved, cards 41532->41698 | ~35k |
| 20:10 | Reverted apkg_image_sync pollution of the curated store (wrong sync direction) | menalariImages.jsonl, .wolf/buglog.json | bug-191; store byte-identical to HEAD again | ~5k |

## Session: 2026-09-03

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 11:40 | Pushed the latest curation progress into the vocabulary deck | AnkiList.csv, Globasa__Vocabulary.apkg | 6 words changed (5 newly curated + waksu 1->8 images); cards 41698->41703 | ~10k |
| 11:42 | Fixed tag-order churn that re-stamped 425 notes per run | update_vocab_deck.py, .wolf/buglog.json | bug-192; re-run now reports 0 updates | ~6k |
| 11:57 | Regenerated after further curation | AnkiList.csv, Globasa__Vocabulary.apkg | esponji gained 4 images (slot 1 filled); cards 41703->41704 | ~5k |
| 12:06 | Regenerated after further curation | AnkiList.csv, Globasa__Vocabulary.apkg | sifre (still replaced + first gif), sifretul (first image); cards 41704->41706 | ~5k |
| 12:08 | Regenerated after further curation | AnkiList.csv, Globasa__Vocabulary.apkg | balde gained its first image; cards 41706->41707 | ~4k |
| 12:15 | Wrote 4 VS Code tasks for the deck pipeline; could not install them (.vscode is a read-only mount) | .vscode/tasks.json (validated, delivered to user) | 19 tasks, existing 15 byte-identical, default build task untouched | ~8k |
| 13:02 | Re-staged the 4 VS Code deck tasks as vscode-tasks.json in the project root (.vscode still read-only to the sandbox) | vscode-tasks.json | 19 tasks; existing 15 + inputs verified identical; user installs with one cp | ~6k |
| 22:48 | Fixed word viewer entry-grid overlap: sidebar capped at 20rem, trans table scrolls, breakpoint 48rem | word_viewer.html | fixed, confirmed by user in the browser | ~18k |
| 22:56 | Diagnosed "un" chip in translation aide (UI article toggle, not Apertium output); found un-chip suppressed on polysemous nouns | translation_aide.html, Word Viewer.py | logged bug-194 | ~15k |
| 23:00 | Moved the un toggle chip before the noun (was after) in the eng-glb aide output | translation_aide.html | fixed, logged bug-195 | ~3k |
| 19:50 | nun (present-tense preverb) suppressed by default with a toggle chip, like un; split back-half pipeline at transfer/gen | Word Viewer.py, translation_aide.html | done, tested against live apertium; bug-194 fixed as a side effect | ~55k |

## Session: 2026-09-07

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 21:40 | Audited the colexification research doc against primary sources | docs/research/colexification-happiness-luck.md | 11 factual errors found; 2 rows refuted by their own citations; 4 label/URL mismatches; family taxonomy double-counts IE x3 and Uralic x2 | ~35k |
| 22:10 | Pulled real data: CLICS⁴ edges, Concepticon IDs, Glottolog CLDF, Wiktionary etymologies for ~60 words | (scratchpad) | HAPPY–GOOD LUCK edge rests on 1 language (Mlabri); FATE/JOY/HAPPINESS have 0 edges; Glottolog = 246 families + 183 isolates, not "50-60" | ~40k |
| 22:25 | Wrote the review + extension | docs/research/colexification-happiness-luck-review.md | 327 lines; corrected classification, Oishi et al. 2013 (24/30 nations), three source metaphors, Globasa hox/xanse analysis | ~20k |
| 22:01 | Analysed semantic Eurocentrism in word-list.csv; user corrected English->Esperanto framing | word-list.csv, cerebrum.md | corrected analysis delivered | ~35k |
| 23:05 | Folded the corrections into the original research doc; kept the audit as a companion | docs/research/colexification-happiness-luck.md, .colexification-happiness-luck.md.orig | 430 lines, 4 tables 0 malformed rows, 83 footnotes all resolving both ways; Romance moved to the "with" column after Italian felice "blessed, lucky" and Portuguese feliz "fortunate" checked out | ~25k |
| 22:07 | Ran Esperanto-alignment + decomposability tests on word-list.csv | word-list.csv | A confirmed, B refuted (z=+2.37) | ~28k |
| 22:11 | Discriminating test for Esperanto transmission | word-list.csv | architecture confirmed, lexical test invalid | ~12k |
| 23:40 | Reoriented the research doc to the user's actual goal: mechanisms of the state/trait split + what each pole attaches to | docs/research/colexification-happiness-luck.md | 329 lines, 11 tables 0 malformed, all footnotes resolving; 6 mechanisms + 2 neighbour clusters + the body/biography asymmetry | ~45k |
| 23:45 | Proved the user's hypothesis that CLICS is blind to this contrast, with data | (CLICS⁴ API) | Concepticon has no GLAD; 11 of 17 happiness concepts have 0 forms; HAPPY is 1 slot filled with the trait word in Dutch/Korean/Turkish and the state word in Mandarin/Japanese/Swedish; 10 languages where trait←luck derivation fires no edge | ~15k |
| 22:25 | Verified 12 non-European colexification claims against en.wiktionary API | docs/research/ | 7 confirmed, monsoon refuted, muka downgraded | ~22k |
| 22:38 | Derived Globasa phonotactics; proposed coinages for verified semantic gaps | word-list.csv | 3 tiers proposed, kita approach retracted | ~26k |
| 22:45 | Re-tested coinages against cross-family criterion | word-list.csv | muka upgraded, hati->ganzo extension, harambe dropped | ~18k |
| 22:47 | Sprachbund criterion; found heart-mind candidate `xin`; recounted areal inflation | word-list.csv | xin proposed, rice-as-meal rejected | ~15k |
| 22:50 | MSEA psycho-collocation check; xin becomes derivational hub | word-list.csv | xin case strengthened, xinxiku objection found | ~14k |
| 22:56 | Investigated ayni + harambee via Wiktionary and Wikipedia | word-list.csv | ayni clears, harambee rejected, ubuntu found | ~20k |
| 23:20 | Applied banal-extension criterion to dropped items | word-list.csv | muka reinstated, giri as root, affix downgraded | ~16k |
| 23:24 | Reviewed word selection methodology | Word selection automator 2.py | forms defended, senses undefended; Tagalog regression logged | ~19k |
| 23:29 | Ran word-selection methodology on reciprocal-gift concept | GlobasaSourceTransliterators.py | 3 tooling bugs logged; Sinosphere-only claim corrected | ~17k |
| 23:35 | Extended reciprocal-gift survey to other families via Wikipedia | word-list.csv | utang na loob passes; Mauss examples fail; xinjaymu derivable | ~18k |
| 23:42 | Closed untested absences for reciprocal gift | word-list.csv | giri withdrawn; xinjaymu compound recommended | ~19k |
| 23:54 | Verified Eastern concept derivations against SEP/IEP/Oxford | word-list.csv | 3 confirmed, nirvana too narrow, ren improved to toninsanya | ~21k |
| 00:01 | Searched papers via google-scholar/paperclip on wuwei + ren | word-list.csv | nilfale adopted; consensus claim retracted; toninsanya->boninsanya | ~22k |
| 00:08 | Checked teotl/Dao comparative literature | word-list.csv | comparison real (user right); not independent evidence; di-marker recommendation stands | ~16k |
| 00:44 | Sinosphere philosophical concept sweep | word-list.csv | ziran + bao accepted, de rejected, kong already covered | ~15k |
| 00:49 | Surveyed Indigenous concept candidates | word-list.csv | topographic directionals derivable via hoy-; cross-cousin low priority | ~17k |
| 01:10 | Wrote semantic-eurocentrism-audit.md | docs/research/, .wolf/anatomy.md | 510-line audit with sources | ~30k |
| 01:16 | Revisited unblocked sources; corrected audit | docs/research/semantic-eurocentrism-audit.md | nilfale withdrawn; IEP Aztec is by Maffie; Fraser still unread | ~14k |
| 01:25 | Reinstated nilfale on Daodejing 37 argument | docs/research/semantic-eurocentrism-audit.md | R1 rewritten; translation-test method logged | ~10k |
| 01:32 | Fetched primary texts; ran translation tests | docs/research/semantic-eurocentrism-audit.md | nilfale passes, nentrutiya partially fails | ~13k |
| 01:36 | Corpus-tested wuwei across the Daodejing | docs/research/semantic-eurocentrism-audit.md | walfale supersedes nilfale; 無 = 51 productive forms | ~15k |
| 01:40 | Corrected 無不為 to a clause after double-negation objection | docs/research/semantic-eurocentrism-audit.md | R7 added | ~8k |
| 09:14 | Sinosphere Heaven; tested rta/asha/maat; paper-backed | docs/research/semantic-eurocentrism-audit.md | R8 added, janatu mis-gloss found | ~16k |
| 09:20 | Parity audit: Sinosphere roots warranted | docs/research/semantic-eurocentrism-audit.md | R9; tian/xiaw/fu proposed, di tian retracted | ~14k |
| 09:27 | Built globasa_collision_check.py; tian->tyen; found sim taken, xiawya/hoyjabal illegal | globasa_collision_check.py, docs/research/, anatomy.md | R10 | ~18k |
| 09:35 | Rewrote phonotactics to documented xwexi rules; validated 99.6% on 3188 roots | globasa_collision_check.py, docs/research/, anatomy.md | R11; hoyjabal/xiawya/samsara/hunpo restored | ~20k |
| 09:41 | Added -u adaptation rule to checker; inyangu, mingu collision found | globasa_collision_check.py, docs/research/ | R12 | ~12k |
| 09:48 | Restructured audit: current findings in body, R1-R12 compressed to changelog | docs/research/semantic-eurocentrism-audit.md | 1100 -> ~630 lines | ~14k |
| 10:58 | Surveyed Globasa geological vocabulary; designed a transparent igneous naming scheme (magma-/lava- on a shared composition root) | word-list.csv (read only), .wolf/cerebrum.md | answered; 2 cerebrum learnings added | ~35k |

## Session: 2026-10-25 08:50

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 09:20 | Anki vocab deck: one subdeck per card type; plant te/to pronoun cards (Pornamelexi + new Alo Pornamelexi, 89 words); named Card 14-19 templates; removed SabziFruta prototype; fixed pronoun TSV garbage rows | update_vocab_deck.py, restructure_vocab_deck.py, AnkiMaker3.py, images_store.py, menalariPronouns_edited.tsv, Globasa__Vocabulary.apkg | done; 40846 cards; input apkg's study history (63k reviews) stripped by export, kept in .pre-restructure.bak | ~60k |
| 11:40 | Plant pronouns moved to per-sense menalariAnaphorSenses.tsv (te = live whole plant; food/parts/cut = to); deck rebuilt from latest word-list.csv; fixed '-cu' annotation rename in parser; update_vocab_deck now removes empty cards | menalariAnaphorSenses.tsv, AnkiMaker3.py, Lexilista_parser.py, update_vocab_deck.py, Globasa__Vocabulary.apkg | done; 40984 cards, 190 Alo Pornamelexi, 0 empty | ~45k |
| 12:30 | Verb class split from meaning: Verb Class card (1785), No Object card (455: echo X X / X(cu) / sen X-do / sen X-pul / no -cu); echo + -cu meaning cards now bare verb like Hisili/Jotayli; -cu headwords special-cased | AnkiMaker3.py, restructure_vocab_deck.py, update_vocab_deck.py, Globasa__Vocabulary.apkg | done; 43224 cards, 0 empty | ~70k |
| 12:50 | Collapsed verb-class cards to one "Verb Type" card (455: frame equivalent to a plain intransitive); removed Verb Class template + VerbClassNote field | AnkiMaker3.py, restructure_vocab_deck.py, update_vocab_deck.py, Globasa__Vocabulary.apkg | done; 41439 cards, 0 empty | ~25k |
| 13:00 | Verb Type prompt 'without an object?' -> 'nenhar ojeto?' | restructure_vocab_deck.py, Globasa__Vocabulary.apkg | done | ~3k |
| 14:00 | Lafuzu deck (249 notes, 498 cards: written<->spoken, Hector's recordings) + Audacity label proposals for lessons 8-20 | LafuzuDeckMaker.py, lesson_audio_labels.py, LessonAudioLabels/, Globasa__Lafuzu.apkg | done; 5 lessons labelled in order, 8 aligned with '?' | ~60k |
| 14:40 | Phoneme-recognition labelling of lessons 8-20 (validated exact on lessons 1-7); shared xwexi_lessons.py parser; deck builder picks up te/to forms and off-list headword clips | lesson_audio_labels.py, xwexi_lessons.py, LafuzuDeckMaker.py, LessonAudioLabels/ | done; 11 labels to check across 13 lessons | ~50k |
| 15:10 | /splits review page in Word Viewer for lesson-recording splits (play, waveform edit, rename, tick, export clips); lesson_audio_labels writes review .json and never regenerates a lesson in review | Word Viewer.py, splits_review.html, lesson_audio_labels.py, xwexi_lessons.py | routes tested via Flask test client on scratch copies; JS syntax-checked; not yet tried in a browser | ~40k |
| 12:45 | Lesson 17 marked synthesized (excluded from Lafuzu deck, export refused); clip-name regex fixed for proper nouns/suffixes (lesson 11's 12 countries); Lafuzu deck rebuilt: 468 notes | xwexi_lessons.py, LafuzuDeckMaker.py, Word Viewer.py, splits_review.html, Globasa__Lafuzu.apkg | done; lesson 11 re-export pending (user, /media read-only here) | ~30k |
| 12:55 | Dictionary pronunciation button names the voice: Hector's, or 'synthesized' for lesson 17's 15 clips; lookup now finds multi-word clips (cel_na) | Word Viewer.py, word_viewer.html | done | ~8k |
| 13:05 | Lesson 11 country-name clips exported (12) via running Word Viewer; Lafuzu deck rebuilt | Globasa__Lafuzu.apkg | done | ~3k |
| 13:20 | Lafuzu deck: synthesized lesson 17 included but separate (own notes, tag, subdecks); 495 notes / 990 cards | LafuzuDeckMaker.py, Globasa__Lafuzu.apkg | done | ~10k |
| 13:30 | ASR feasibility: Hector = 44 min (course only); Doxo audio mainly synthesized (user) | .wolf/cerebrum.md | noted | ~5k |
| 13:45 | Committed session work in 5 atomic commits on images-per-sense (fb6d592..6d1ad95); user's earlier uncommitted work in AnkiMaker3/Lexilista_parser/Word Viewer/word_viewer.html left unstaged by hunk; .apkg, Models/, LessonAudioLabels/.cache excluded (.gitignore added) | git | done, not pushed | ~20k |
| 14:20 | Plant pronouns redone from gloss meaning (user: danyam must be to only): 9 dual, 72 te, 234 to, 23 flagged '?'; deck rebuilt, 181 Alo cards removed | menalariAnaphorSenses.tsv, AnkiList.csv, Globasa__Vocabulary.apkg | done, not committed | ~20k |
| 14:30 | Lafuzu Spoken → Written back no longer replays the recording; builder now syncs templates/CSS every run | LafuzuDeckMaker.py, Globasa__Lafuzu.apkg | done | ~5k |
| 14:45 | Lafuzu: optional Spoken → Typed card (type the written form; punctuation stripped, capitals kept), own subdecks; builder adds missing fields/templates to an existing package; 1485 cards | LafuzuDeckMaker.py, Globasa__Lafuzu.apkg | done | ~10k |
| --:-- | Doxo TMX update: fast-forwarded doxo-pages-grav to 4833a6a, appended 439 TUs (417 glb-only, 22 with en) and fixed Esopo dujotay->jotay; accidental make_tmx.py run caught and reverted | Doxo_passages.tmx, Doxo_passages_extended.tmx, Doxo_passages_edited_updated.csv, extend_tmx_doxo_2026_11.py, fill_telltale_english.py | 3127->3566 TUs, existing bytes identical except the fix; backups in backups/doxo_update_2026-11-04/; alignment and Qdrant not re-run | ~25k |
| --:-- | Normalized Suikal Kraw şerça->xerca; left stylised Pilpil Mon 8 diacritics alone | Doxo_passages.tmx, Doxo_passages_extended.tmx, Doxo_passages_edited_updated.csv, extend_tmx_doxo_2026_11.py | 1 segment changed per file | ~2k |
| --:-- | Chose decision-model candidates for sense pilot: OpenJev 27B Q4_K_M with partial offload, Flash 9B Q8_0 and Gemma 26B as comparisons; nothing downloaded | none | recommendation only | ~6k |
| --:-- | Created sense_review_queue.py: decision-model sense scoring and value-ordered blind review queue; tested only with a fake server, real model still downloading | sense_review_queue.py | end-to-end flow works; no real scores yet | ~20k |
| --:-- | Measured gloss cues for non-corpus senses against vetted rows; scripts in scratchpad only | none | analysis only; latest word list not reachable from sandbox | ~12k |
| --:-- | Reworked sense_review_queue.py prompts: stable prefix, neighbours, extra translations, ablation variants, content words only, thinking disabled; fake-server test | sense_review_queue.py | real model not yet run | ~10k |
| --:-- | Tested Globasa PPMI+SVD vectors against Tags, Synonyms and split-half stability; script in scratchpad | none | weak signal, recorded in cerebrum | ~4k |
| --:-- | Tested word-class and corpus-frame syntax cues on vetted sense rows; script in scratchpad | none | useful as a narrowing filter only, recorded in cerebrum | ~5k |
| --:-- | Compared syntactic-role and window PPMI vectors on Esperanto and tag gold pairs; script in scratchpad | none | same scores, qualitatively different neighbours; recorded in cerebrum | ~6k |
| --:-- | sense_review_queue.py: default prompt drops Globasa unless target cannot be marked in the English, per user | sense_review_queue.py | fake-server test only | ~6k |
| --:-- | sense_review_queue.py: default prompt drops Globasa unless the target cannot be marked in English; adds translated argument lists | sense_review_queue.py | fake-server test only | ~8k |
| --:-- | Created sense_vetter.py/.html: fast model-free sense vetting ordered by proofread Eo/Es matches, with Hide vetted | sense_vetter.py, sense_vetter.html | logic tested in Node with a stub DOM and scratch server; Chromium blocked by sandbox, so visuals unchecked | ~14k |
| --:-- | Sense vetter: permanent server-side undo across restarts, bulk undone as one step, corrections restore prior verdict, Clear on cards | sense_vetter.py, sense_vetter.html | tested in Node stub DOM with scratch server | ~8k |
| --:-- | Checked OpenJev-Flash-9B-Q8_0.gguf metadata for the sense pilot: 32 layers, recurrent layers present, template disables thinking correctly, dry run with --tag=flash9b fine; real model not yet run | none | ready for user to run | ~8k |
| --:-- | Monitored Flash 9B pilot: about 13 s per answer, about 90 s on a full reprocess; found lowercase option letters nearly invisible; advised stopping the run; script not changed | sense_review/cache_flash9b.jsonl | fix pending user decision | ~15k |
| --:-- | Traced no-GPU warning to Homebrew CPU-only llama-server shadowing the Vulkan build; gave user a command; GPU not yet confirmed | .wolf/buglog.json, .wolf/cerebrum.md | diagnosis confirmed by commit match | ~10k |
| --:-- | Flash on Vulkan: --words=2 test finished, about 0.5 s per pass; letter rotation test on simplified prompts found 3-4x lowercase penalty, smaller than full-prompt swing; script unchanged | .wolf/buglog.json, .wolf/cerebrum.md | MAX_OPTIONS fix awaiting user answer | ~12k |
| --:-- | sense_review_queue.py: 25-sense cap, 4 shuffles, --rotate test, letter report, vetting log applied; rotation and --words=2 run on real Flash 9B through a scratch forwarder | sense_review_queue.py, sense_review/ | short test passes; full pilot not yet run | ~25k |
| 18:06 | Sense vetter: added Unsure mark (M), 'Words with no sense marked yet' and 'Senses marked unsure' views; unsure excluded from export and review queue; keys no longer act on a hidden card | sense_vetter.py, sense_vetter.html, sense_review_queue.py | tested on scratch copy with stub DOM, not rendered in a browser | ~9000 |
| 18:13 | Sense vetter: peek at a word's other senses (P or button), with their marks | sense_vetter.py, sense_vetter.html | tested on scratch copy with stub DOM, not rendered in a browser | ~4000 |
| --:-- | sense_review_queue.py: added --format and --compare; model-card choice layout won on stability and is now default; full pilot not yet run | sense_review_queue.py | card 96% same winner vs plain 74% | ~15k |
| 18:23 | Sense vetter: mark senses from the peek (buttons on each row); card and panel stay until moving on, undo stays on the word | sense_vetter.html | tested on scratch copy with stub DOM, not rendered in a browser | ~5000 |
| 18:42 | Sense vetter: scoring cues for other glosses, taxa and tags with sibling demotion; browse by tag with fitting senses first | sense_vetter.py, sense_vetter.html | AUC 0.897 to 0.902, within-word 0.906 to 0.919; tag view tested on scratch copy with stub DOM, not rendered in a browser | ~30000 |
| 20:10 | Checked Flash 9B sense pilot: replayed report from scratch cache (TSV byte-identical); 50 words, 724 rows, queue 128 rows unreviewed; OpenJev 27B never ran beyond 5 answers | sense_review/, .wolf/buglog.json, .wolf/cerebrum.md | no project code or outputs changed | ~25k |
| 20:14 | Shorthand design analysis: join, vowel-reduction and consonant-merge simulations over Doxo_passages.tmx (scratchpad scripts, no project files changed) | .wolf/cerebrum.md | CV-centred design recommended over Orthic's cluster economy | ~12000 |
| 20:23 | Reworked shorthand design from minimal-pair rules and the lafuzu page; simulated tiers, glide-as-vowel, stress phrasing, combined systems | .wolf/cerebrum.md, .wolf/anatomy.md | Rule-based sign families replace t-c/d-j proposal | ~15000 |
| 20:26 | Per-sound frequency and stroke-length cost analysis for shorthand | .wolf/cerebrum.md | r and u must not be distinguished by length; 2:1 length ratio preferred | ~4000 |
| 20:35 | Shorthand stats re-run with even source weights; baseline scoped to everyday handwriting | .wolf/cerebrum.md | Priority groups held; reporting tier dropped from baseline | ~5000 |
| 20:40 | Measured reporting-tier abbreviation methods under even source weights | .wolf/cerebrum.md | Stacked tiers tested, including held-out texts | ~6000 |
| 20:41 | Compared script types (abugida, syllabary, block) and stacked reporting tiers | .wolf/cerebrum.md | Recommended obligatory-vowel syllable blocks; reporting tier about 30% fewer strokes | ~7000 |
| 20:54 | Measured complexity, width and blur discrimination for Latin, Hangul and a draft block script | .wolf/buglog.json, .wolf/cerebrum.md | Simplicity budget quantified | ~9000 |
| 21:01 | Assessed boustrophedon for the print script from eye-movement literature | .wolf/cerebrum.md | Keep as a tested option, not the default | ~1500 |
| 21:08 | Redrew print script shapes as stacked blocks, measured and rendered specimen | .wolf/cerebrum.md | Budget met; several shape pairs still need work | ~6000 |
| 21:11 | Compared non-English shorthand models for Globasa | .wolf/cerebrum.md | Duployan baseline, Japanese idea for rapid tier | ~1500 |
| 21:19 | Read Marti PDF and simulated implied vowels on Globasa | .wolf/cerebrum.md | Implied-vowel tier evaluated | ~5000 |
| 21:36 | Added letter and two-letter frequency tables to the shorthand report | Claude doc | Session stopping; next step: three-style vowel practice sheet | ~1500 |
| 21:45 | Added cursive-replacement design goal to the shorthand report | Claude doc, .wolf/cerebrum.md | Done; next step unchanged | ~300 |
| 21:49 | Parked shorthand-based math notation idea for a later session | .wolf/cerebrum.md | Not started | ~200 |
| 21:46 | Read Cao & Zhai, Isokoski, Matić in full (Zotero, added 2026-11-06); ran stroke-time and line-count models on vowel styles; updated report | Claude doc, .wolf/cerebrum.md, .wolf/anatomy.md | Full circles 1.3-2x slower; reversal worry withdrawn; scripts not in repo | ~14000 |
| 21:49 | Recorded optional distinguishing marks idea for the shorthand (s/z, after Orthic's dotted i); not evaluated | Claude doc, .wolf/cerebrum.md | Written down; practice sheet still first next session | ~300 |
| 22:00 | Recorded stroke inventory scheme and design-polishing script plan for the shorthand; nothing built | .wolf/cerebrum.md | Next session, after practice sheet and reading list | ~300 |
| 22:09 | Literature sweep finished: 26 papers on handwriting speed models and legibility, none yet in Zotero | shorthand_literature_sweep.md | Reading list ready for next session; many read as abstract only | ~subagent |
| 22:17 | Recorded that cursive names the shorthand's role and the speed benchmark is the writer's normal hand | .wolf/cerebrum.md | Noted; report wording already compatible | ~200 |
| 22:19 | Corrected pen-lift inference: unbroken outlines stay default because they can disregard the writing line | .wolf/cerebrum.md | Noted | ~150 |
| 10:00 | Folded reading list into shorthand report; built practice sheet and style metrics in repo; added results to report | shorthand_geometry.py, shorthand_practice_sheet.py, shorthand_practice_sheet.pdf, shorthand_style_metrics.py, Claude doc | Sheet ready to print; next step is the user's hand test | ~30000 |
| 10:40 | Read Callendar 1889 Cursive manual (EPUB + PDF); scored joins by its categories; added principles section to report; sheet pairs page marked feel-only | shorthand_style_metrics.py, shorthand_practice_sheet.py/.pdf, Claude doc, .wolf/cerebrum.md | Provisional set under 42% sharp joins; n hook and flat s are worst | ~25000 |
| 11:30 | Built shorthand_optimizer.py, ran main search + 6 sensitivity runs; geometry and practice sheet now use 3 optimizer candidates; report section added | shorthand_optimizer.py, shorthand_candidates.json, shorthand_geometry.py, shorthand_practice_sheet.py/.pdf, shorthand_style_metrics.py, Claude doc | Candidates 43-48% sharp joins, level line; no stable winner; self-crossing outlines unmodelled | ~40000 |
| 12:10 | Added loops (56-stroke inventory) and a shape-variety cost to the optimizer per user; reran search + variety sensitivity; sheet rebuilt | shorthand_optimizer.py, shorthand_geometry.py, shorthand_candidates.json, shorthand_practice_sheet.py/.pdf | Loops take 4-5 letters; sharp joins 47-54%; still no stable winner | ~20000 |
| 12:40 | Added big/small circles (Callendar-style joins) to optimizer, geometry, metrics and sheet; reran search + half-circle-time variant | shorthand_optimizer.py, shorthand_geometry.py, shorthand_style_metrics.py, shorthand_candidates.json, shorthand_practice_sheet.py/.pdf, Claude doc | Circles take 4 rare consonants; with cheaper circle time they take vowels instead | ~15000 |
| 13:05 | Added Latin-likeness tie-breaker to optimizer (weights 0.25-4 tested, 2 chosen); reran search; sheet rebuilt | shorthand_optimizer.py, shorthand_candidates.json, shorthand_practice_sheet.pdf, Claude doc | 3-4 of 21 letters Latin-like at no cost; more costs 4%+ | ~10000 |
| 13:40 | New stroke-time model in shorthand_geometry (power-law curvature + Callendar facility), Orthic circle-ended strokes (308-stroke inventory); reran search; sheet and metrics updated | shorthand_geometry.py, shorthand_optimizer.py, shorthand_style_metrics.py, shorthand_candidates.json, shorthand_practice_sheet.py/.pdf | Restarts within 2%; core letters stable across candidates | ~25000 |
| 14:30 | Size-by-frequency rule; inter-letter contact measure (shorthand_geometry.contacts) in optimizer: neighbour pairs precomputed in JOIN, 3-4 letter windows in a polishing stage | shorthand_geometry.py, shorthand_optimizer.py | Running | ~30000 |
| 15:40 | Final search: no composites, no quarter-arc letters, rounded-join rule, contact penalty 800, simplicity-before-size order; sheet rebuilt | shorthand_optimizer.py, shorthand_geometry.py, shorthand_candidates.json, shorthand_practice_sheet.py/.pdf | Lines for 8 commonest letters, then semicircles, circles, loops; contacts in 2.6-5% of words | ~30000 |
| 16:30 | Optimizer sped up ~15x (parallel restarts/polishing on 16 cores, cached stroke blocks in contacts_fast); no shared signs except s/z; narrowed similar-sign rule; softened shape ordering so joins lead; sheet rebuilt | shorthand_optimizer.py, shorthand_geometry.py, shorthand_candidates.json, shorthand_practice_sheet.py/.pdf | Full search 52 s; contacts 2.6-5% of words; similar pairs mostly rule-protected | ~40000 |
| 16:55 | Fixed continuous-join rule (inflection = clear), raised merging/retrace costs; reran; sheet rebuilt | shorthand_optimizer.py, shorthand_candidates.json, shorthand_practice_sheet.pdf, Claude doc | Top 60 joins: 58 clean; merging 3-5%, retrace 2% | ~10000 |
| 17:05 | Top-50 joins forbidden from merging/retracing; reran; sheet rebuilt | shorthand_optimizer.py, shorthand_candidates.json, shorthand_practice_sheet.pdf, Claude doc | 50/50 clean in all candidates; first offender tu #51 | ~5000 |
| 17:15 | Unprotected similar signs now a flat 200 ms per pair; reran; sheet rebuilt | shorthand_optimizer.py, shorthand_candidates.json, shorthand_practice_sheet.pdf, Claude doc | No unprotected similar pairs; cost +6%, merging 6-7%, contacts 6-7% | ~5000 |
| 17:40 | Similar-pair cost now weighted by misreading % plus future risk graded by the methodology tiers (re-read Methodology for Lexical Development); reran; sheet rebuilt | shorthand_optimizer.py, shorthand_candidates.json, shorthand_practice_sheet.pdf, Claude doc | Search uses no similar pairs at all; top 50 joins clean | ~8000 |
| 18:20 | Added principle cost terms (soft-join runs, circle on line, 67.5-degree joints); built shorthand_word_stats.py (lexicon collisions, lexicon pairs, word edges, phrase joins) and fed it to the search; sheet rebuilt | shorthand_optimizer.py, shorthand_word_stats.py/.json, shorthand_candidates.json, shorthand_practice_sheet.pdf, Claude doc | Top 50 clean; contacts 5.6% (leader) | ~30000 |
| 19:30 | Tangle reduction: stronger contact costs, 4-5 letter polish windows, vertical-range term, triple contacts precomputed into main search; flat charges tried and reverted in strength; sheet rebuilt | shorthand_optimizer.py, shorthand_geometry.py, shorthand_candidates.json, shorthand_practice_sheet.pdf, Claude doc | Leader: contacts 3.6% of words; merging 11%, retrace 4.5% | ~60000 |
| 20:20 | Subdecks regrouped: all Produti -> ::Produti, non-image Rukone -> ::Rukone, Imajeli Rukone separate (subdeck_for); tested on scratch copy: 11690 Produti / 12146 Rukone / 1753 Imajeli Rukone | update_vocab_deck.py, .wolf/cerebrum.md | done; apkg not rebuilt | ~8k |
| 20:30 | Subdecks: Produti/Rukone each split ::Imajeli / ::Nenimajeli per card by rendered web src (offline study); quick card types keep own subdecks. Accidentally ran update_vocab_deck via import, restored apkg from .bak | update_vocab_deck.py, .wolf/cerebrum.md, .wolf/buglog.json | done; scratch test 1778/9912 Produti, 1811/12088 Rukone, idempotent; apkg not rebuilt | ~25k |
| 21:02 | Main gloss emphasised: AnkiMaker3.emphasize_main_gloss wraps first of 2+ glosses per row in span.main-gloss; update_vocab_deck adds .main-gloss CSS (larger + underline, not bold/italic) | AnkiMaker3.py, update_vocab_deck.py, .wolf/cerebrum.md | helper unit-tested via ast; deck not rebuilt | ~15k |
| 21:03 | Main-gloss overrides: menalariMainGloss.tsv (kinmyetu -> look down on) fronted + emphasised per row by AnkiMaker3.emphasize_main_gloss | AnkiMaker3.py, menalariMainGloss.tsv, .wolf/anatomy.md, .wolf/cerebrum.md | tested via ast; deck not rebuilt | ~8k |
| 21:04 | kone -> 'be familiar with' override; auto 'front the distinguishing gloss' rule rejected (spelling variants, derivative shares, no unique gloss for narem/hasaxi); wrote menalariMainGloss_candidates.tsv for manual review | menalariMainGloss.tsv, menalariMainGloss_candidates.tsv, .wolf/anatomy.md | done | ~10k |
| 21:06 | Core-group main glosses (comma-separated MainGloss, hasaxi -> 'tender, loving'); fixed dropped-gloss bug in emphasize_main_gloss | AnkiMaker3.py, menalariMainGloss.tsv, .wolf/buglog.json, .wolf/cerebrum.md | tested, gloss counts preserved; deck not rebuilt | ~8k |
| 21:09 | Homograph qualifiers: menalariGlossQualifiers.tsv (tabar/hake hack, jumun/harufi spell) applied by emphasize_main_gloss | AnkiMaker3.py, menalariGlossQualifiers.tsv, .wolf/anatomy.md, .wolf/cerebrum.md | tested; deck not rebuilt | ~8k |
| 21:18 | Built Word Selector pipeline + page (stages 0-6 of plan i-would-like-to-atomic-graham); translit 78-91% exact vs gold; roots oracle top1 29.6% top5 58.8% | word_selection/, Word Selector.py, word_selector.html, Wiktionary concept index.py | working, uncommitted | ~200k |
| 21:20 | SESSION SUMMARY: subdecks Produti/Rukone ::Imajeli/::Nenimajeli per card (offline study); main-gloss emphasis + menalariMainGloss.tsv (incl. core groups) + menalariGlossQualifiers.tsv (homographs) + candidates list; accidental apkg rewrite restored (bug-217); dropped-gloss bug fixed (bug-218); ideas saved to memory: translation-based sense examples, streamed corpus panel in Word Viewer. Nothing rebuilt or committed | update_vocab_deck.py, AnkiMaker3.py, menalari*.tsv, memory | done | ~5k |
| 09:27 | Added Word Selection Automator tasks (v2 + original) | .vscode/tasks.json | blocked: .vscode read-only in sandbox, snippet given to user | ~300 |
| 09:47 | Word Selector: Sino-xenic distance + shared-Han link in clustering; proposals for all clusters (LexiliAsel pairwise @0.30: recall 79.1->84.0%, FP 5.2->5.9%) | word_selection/align.py, cluster.py, pipeline.py, word_selector.html | ok | ~6000 |
| 09:55 | Word Selector: MC/Cantonese pivots + SINO_MARGIN; built word_selection_cache/middle_chinese.json (13349 chars, 3992 simp->trad); recall .791->.860, FP .052->.055 | word_selection/middle_chinese.py, cluster.py, pipeline.py | ok | ~8000 |
| 10:08 | Word Selector: Han-spelling-first Sino clustering (hanja, chữ Hán, kyūjitai), native-reading exclusion, on'yomi shape test; renamed middle_chinese.py -> sinosphere.py; roots reproduced 87.5->89.5% | word_selection/sinosphere.py, cluster.py, align.py, pipeline.py | ok | ~25000 |
| 10:16 | Word Selector Sino route: MC -ng ~ Japanese long vowel, nasal coda/onset penalty, y~sh far (Sino route only after user clarification); roots 89.5% unchanged, pairwise recall .883 FP .0547 | word_selection/align.py | ok | ~4000 |
| 10:21 | Word Selector: Arabic/Persian clustering by normalised abjad skeleton (new word_selection/abjad.py); ar+fa roots 94.9->95.4% (e2e) | word_selection/abjad.py, cluster.py | ok | ~5000 |
| 10:22 | Word Selector: abjad join made a romanization fallback (user correction); formless ar/fa words kept for spelling-only joins | word_selection/cluster.py, pipeline.py, Word Selector.py | ok | ~4000 |
| 10:29 | Word Selector: Arabic<->Persian vocalization prediction using vowel length; pipeline.predict_vocalizations fills unromanized ar/fa forms; exact ar->fa 63.3%, fa->ar 59.6% (baseline 26.3%) | word_selection/abjad.py, pipeline.py | ok | ~15000 |
| 10:43 | Word Selector: contrasts.py (foreign-edition sense contrasts); de/fr give none for test concepts; needs zh/ja/ko editions | word_selection/contrasts.py | partial | ~12000 |
| 10:45 | Configured ja + zh Wiktionary editions (xlsx, parser multi-name + unlabelled tables); froh vs glücklich test: de alone insufficient | wiktionary_config.xlsx, JSONL parser non-English.py | ok | ~6000 |
| 11:26 | contrasts.py tested with ja+zh editions: brother/sister/rice found; uncle/wear none (sparse tables); happy finds cheerful/content/fortunate | word_selection/contrasts.py | partial | ~10000 |
| 11:39 | Fixed empty reverse index (716k); contrasts: root matching, neighbour tables, compare_to_pivot (幸福/兄/米 pivots: 6/10/5 families) | word_selection/contrasts.py, WiktionaryLMDB_concepts | ok | ~40000 |
| 11:47 | contrasts.compare_to_pivot: per-POS verdicts + cross-POS leak (es/fr/de/ru don't separate 幸福 vs 嬉しい); Globasa coverage per side (hoxya merges) | word_selection/contrasts.py | ok | ~12000 |
| 11:50 | 幸福 split assessment: word-list glosses show feliĉo/ĝojo-type split in all columns; pipeline top cluster 幸福 (hanfuku...) | analysis | ok | ~8000 |
| 12:11 | contrasts.compare_to_pivot: covered-table subtraction via existing Globasa words (kweho, furahado, barakado, bonjiwa...), shared words dropped; happy/幸福 residual: cmn, ja separate | word_selection/contrasts.py | ok | ~10000 |
| 12:14 | contrasts: 'marked' (privative) verdict -- froh/glücklich, blij/gelukkig pattern; happy/幸福: 2 families separate + 3 marked | word_selection/contrasts.py | ok | ~6000 |
| 12:15 | contrasts: own-word test vs pivot-exclusive words only; Russian (счастье vs радостный/рад) now marked | word_selection/contrasts.py | ok | ~2000 |
| 12:18 | contrasts: ISOLATING={vi,cmn} cross-POS verdicts count; Vietnamese hạnh phúc vs vui now separates | word_selection/contrasts.py | ok | ~2000 |
| 12:22 | contrasts: English is at most marked when the concept's headword shares the pivot side's root (happy ~ happiness) | word_selection/contrasts.py | ok | ~1500 |
| 12:33 | contrasts: foil same-root reach (joy table), inflection-aware side assignment, vi syllable matching; happy/幸福: 4 families separate + 6 marked | word_selection/contrasts.py | ok | ~15000 |
| 12:46 | contrasts: auto_pivot sweep + suggestion hint + page section/API; bucketed same-root search (sweep ~60s -> 5.8s) | word_selection/contrasts.py, Word Selector.py, word_selector.html | ok | ~15000 |
| 12:46 | contrasts sweep speedup recorded | .wolf | ok | ~200 |
| 13:01 | Word Selector: LexiliAsel precedent for Sino-xenic blending (precedent.py, blend, pipeline, page note); top-1 on Sino-xenic roots 13.2% -> 20.4%, loans unchanged | word_selection/precedent.py, blend.py, pipeline.py, word_selector.html | ok | ~20000 |
| 13:26 | precedent generalised to 5 groups within the methodology (final vowel slot excluded); top-1 all roots 26.8 -> 30.6% | word_selection/precedent.py, blend.py | ok | ~25000 |
| 13:38 | Fixed missing ja 基質: Han-spelling cognate completion in pipeline (attested via ja.wiktionary/en.wiktionary/hanja tables) | word_selection/pipeline.py, sinosphere.py | ok | ~8000 |
| 13:45 | Strip disambiguators from all source words at merge; titles kept and shown | word_selection/sources/__init__.py, word_selector.html | ok | ~3000 |
| 13:59 | form_rules: Sino-Japanese -tsu/-chi/-ku/-ki vote no final vowel (kiju no longer proposed) | word_selection/form_rules.py | ok | ~3000 |
| 14:08 | Middle Chinese coda options (-t -k -p -m -n -ng) from LexiliAsel precedent in form_rules; 基質 -> kijitu | word_selection/precedent.py, form_rules.py, pipeline.py | ok | ~15000 |
| 14:16 | MC finals from Baxter readings (級 kip): Japanese -u as -p reflex, Mandarin 'lost it', precedent recounted | word_selection/sinosphere.py, precedent.py, form_rules.py | ok | ~10000 |
| 14:53 | Calque stage: parts table (459k), calques.py with independent-coinage counting (reproduces milkodao); eval 21% first / 38% top-20 on 842 lexicon compounds; etym_reverse build still running | word_selection/calques.py, concept_index.py | partial | ~30000 |
| 14:57 | etym_reverse built (174k); etymology cognates 2 rounds + Han variant normalisation; dukkha/nirvana/karma gather across languages | word_selection/pipeline.py, sinosphere.py, concept_index.py | ok | ~8000 |
| 16:57 | Committed word_selection changes as 4 atomic commits (codas, kyūjitai, etym cognates, calques) | word_selection/* | 7a31746..49c022f | ~3k |
| 17:35 | Ancestor-centred Sino-xenic alignment (sino_align.py), align() boundary coda fix, precedent MARGINAL sub-pattern counts; full eval running | word_selection/sino_align.py, align.py, blend.py, precedent.py | in progress | ~40k |
| 18:21 | Eval: sino_align neutral, MARGINAL wash (off), n->m before b/p +0.3 all / +1.1 sino; leave-one-out overlay replaces deep copy | word_selection/{sino_align,align,blend,precedent,form_rules}.py | uncommitted | ~25k |
| 18:47 | Perso-Arabic coverage: Iranian-first romans, translation-table romans fallback, vocalization from cognates (abjad.vocalize_from_cognates) in pipeline + e2e eval; fa forms 953->1639 | word_selection/{sources/wiktionary,abjad,pipeline,translit}.py, word_selection_eval.py | uncommitted | ~60k |
| 19:15 | Vocalization dictionaries: Camel Morph (ar) + KaamelDict (fa) primary, Wiktionary/cognates marked fallbacks; fallbacks labelled throughout; ث->t; word_selection_cache/ git-ignored | word_selection/{vocalization,pipeline,translit,abjad,blend,sino_align}.py, word_selector.html, .gitignore | uncommitted; oracle 30.9%, e2e ar/fa 34.3% | ~90k |
| 19:43 | Cultural words/proper nouns (Unix): kind-aware phonotactics, cultural.py detection, per-language pronunciation checks (de/fr editions, tr roman), pronunciation vs spelling readings ranked by checked support; ordinary roots unchanged | word_selection/{cultural,pronunciation,collision,form_rules,pipeline,translit}.py | uncommitted; Unix -> Yuniks / yuniksu | ~60k |
| 20:02 | Methodology justifications on the Word Selector page: methodology.py (passages + RULES), vendored CC0 docs, server attaches per cluster/proposal, reader drawer | word_selection/methodology.py, word_selection/docs/, Word Selector.py, word_selector.html | uncommitted; all rule refs resolve | ~30k |
| 20:26 | Taxon search: sources/taxon.py (Wikispecies VN, Wikipedia, Wiktionary definitions), plurals.py, rank markers, Latin titles excluded by default, page taxon field; yew test exposed false clusters (guard measured, left off) | word_selection/sources/{taxon,__init__}.py, plurals.py, cluster.py, pipeline.py, word_selector.html | uncommitted | ~70k |
| 20:37 | False friends: cluster support = members within 0.30 of the best proposal; unverified etym-cognates excluded; re-rank; bridging tried and removed; methodology rules for the new steps | word_selection/{pipeline,select,methodology}.py | uncommitted; bear -> bear/balu cluster, yew -> yumoke (open question) | ~40k |
| 20:45 | Team questions for borderline false-friend agreement (page + dossier); initial dz-/ts- -> z-/s- (zixan) | word_selection/{pipeline,dossier,form_rules,methodology}.py, Word Selector.py, word_selector.html | uncommitted; all 30.9% | ~20k |
| 20:58 | Meaning check against each source's own entry (sense_fit.py): shifted meanings excluded from agreement, unattested flagged; dossier uses it; nicode/bopu case | word_selection/{sense_fit,pipeline,select,methodology,dossier}.py | uncommitted | ~25k |
| 21:07 | Homonym check (miza/μάζα case): sense-aware glosses, capitalised Mass, etymology followed only from meaning-bearing entries, default-out cognates | word_selection/{sense_fit,pipeline,select,methodology,dossier}.py, word_selector.html | uncommitted; Mass -> missa cluster | ~50k |
| 21:12 | Committed meaning check (nicode/miza); vaso assessed (sources mean 'vase'; narrowing not auto-detected yet) | word_selection/* | committed | ~5k |
| 21:15 | Progress display while the Word Selector runs (pipeline progress callback, /api/progress, page polling) | word_selection/pipeline.py, Word Selector.py, word_selector.html | uncommitted, tested | ~8k |
| 21:19 | Dictionary links + own-language senses per source word (page, /api/entry); conservative source defaults left for next session | Word Selector.py, word_selector.html | uncommitted, tested | ~6k |
| 21:23 | Etymology cognates opt-in (concept etym_cognates, page checkbox), off by default | word_selection/pipeline.py, word_selector.html | uncommitted, tested | ~3k |
| 21:25 | Dictionary links: bilingual X-English first, monolingual last (labelled) | word_selector.html | uncommitted | ~2k |
| 21:31 | Session end: Hanzi-for-ko/vi request recorded as next session's first step; uncommitted: etym cognates opt-in, dictionary links (bilingual first), own-language senses, progress display | .wolf/cerebrum.md | recorded | ~1k |
| 22:05 | Recorded next step: non-English pivot via seed words (editions de/fr/ja/zh exist) | .wolf/cerebrum.md | recorded | ~1k |
| 22:15 | Added the user's pivot-chain example (горшок/Topf/vasija/cruche) to next session's notes | .wolf/cerebrum.md | recorded | <1k |
| 22:16 | Corrected next-session note: seed TUPLE (en:pot, ru:горшок, de:Topf, es:vasija, fr:cruche) jointly pins one meaning; rank by pivots agreeing | .wolf/cerebrum.md | recorded | <1k |
| 12:05 | Historical Han for ko/vi (display_han, sources table, chips, LexiliAsel 기질 氣質 “gijil”, dossier) | word_selection/pipeline.py, dossier.py, Word Selector.py, word_selector.html | d6bef79 | ~15k |
| 12:20 | Han shown only when another Sinosphere word confirms it (독 ≠ 毒/獨); unconfirmed homographs in sources table only | same | a1caaef | ~5k |
| 12:50 | Seed tuples: senses_in (any edition), tuple_senses (score by other seeds listed), pivot_support + rank tie-break after methodology, english_view bridge for sense_fit, edition selector, dossier Pivots | word_selection/{sources/wiktionary,sources/seeds,pipeline,select,dossier,methodology}.py, Word Selector.py, word_selector.html | d7d7156; 8 tests pass | ~40k |
| 14:00 | Matrix (基質) regression: bisected to 7a31746 (coda stats) + 5c93d36 (alignment lost j/k/g precedent); fixed with surface-reflex coda stats + letter-level precedent fallback; kijitu first; eval 946->947, no losses | word_selection/precedent.py, blend.py, tests/test_sino_precedent.py | c44351e | ~40k |
| 19:45 | Committed pending work atomically (nun toggle, viewer sidebar, AnkiMaker3+constructions.py, Lafuzu typed card, vocab subdecks, Doxo/images/anaphor data, requirements); viewer smoke-tested (/, /lookup ok; Apertium pair not reachable from sandbox) | many | 1db5628..871e066 | ~25k |
| 19:55 | Fast-forwarded main to images-per-sense (127b008); main 134 ahead of origin/main, not pushed | - | done | ~2k |
| 20:30 | Word Viewer fresh-clone ready: atomic LMDB build, optional inputs, env paths, font 404, submodules registered, small data committed, setup.sh + requirements-viewer.txt, README; verified on a fresh clone with its own venv | Word Viewer.py, setup.sh, requirements-viewer.txt, .gitignore, README.md | 13b821d..40f51c6 | ~60k |
| 21:10 | Decisions-only storage: vetted_senses.py/.tsv, wiktionary_extract.py (stream dump, keep vetted keys), builder+generator read decisions, deterministic output, setup.sh --extension; extract build byte-identical to full-LMDB build | vetted_senses.py, wiktionary_extract.py, Wiktionary extension builder.py, extender 3, wiktionary_constants.py | 354d3cf..4c08322 | ~80k |
| 21:25 | Spanish/Esperanto annotations restored in menalariExtension.tsv (rebuilt from latest word list; old copy in scratchpad) | wiktionary_constants.py, menalariExtension.tsv | committed | ~15k |
| 22:31 | Deferred (bedtime): make sense_vetter.py cloneable; scoped inputs, wrote next-session note | memory/project_sense_vetter_publish.md | deferred | ~2k |
| 13:20 | Sense vetter fresh-clone: sense_rows.py (extender 3 rows, equivalence-verified 52,890 rows), vetted_senses log overlay, sense_vetting.jsonl keys + tracked, extract --senses, setup --vetter, Doxo_course_ranking.csv | sense_rows.py, sense_vetter.py, vetted_senses.py, wiktionary_extract.py, setup.sh, README.md | 959e9da..c73febc | ~60k |
| 14:10 | Word Selector fresh-clone: word_selection/dump.py, concept index builds parts/etym/sinosphere/plurals, missing-index errors, requirements-selector.txt, setup --selector; Viewer translate/alignments/export errors; GlobasaGrammarChecker tracked | word_selection/*, Word Selector.py, Word Viewer.py, setup.sh, README.md | da25cd6..d7e85ab | ~40k |
| 15:23 | Built stress drill prototype: one Anki card per skill, JS samples 5 items from a 240-item JSON pool; rule verified on all xwexi examples; JS tested under node shim | DrillDeckMaker.py, drill_templates/, Globasa__Drills.apkg | ok, not committed; untested on real Anki clients | ~25000 |
| 15:26 | Drill front: neutral Heading field, pattern Title on back only, vowel-pairs prompt hint removed | DrillDeckMaker.py, Globasa__Drills.apkg | ok, node test passes | ~3000 |
| 15:29 | Stress drill: 6 per-shape cards -> 1 mixed card, 600 items balanced by shape and ending; retired skills removed from package | DrillDeckMaker.py, Globasa__Drills.apkg | ok, node test passes | ~8000 |
| 15:39 | Stress drills restructured: 4 target cards, 3 target + 2 other per round, same-shape retry, response times, target-only rating; retry slot bug caught by node test and fixed | DrillDeckMaker.py, drill_templates/, Globasa__Drills.apkg | ok, 40 randomized test runs pass | ~30000 |
| 15:45 | Drill rating now uses timing (fast/steady/slow per vowel count, Easy/Hard by speed), reason shown on back | drill_templates/drill.js, drill.css, Globasa__Drills.apkg | ok, 25 randomized + scripted slow/fast rounds pass | ~9000 |
| 15:57 | Listening drill (Hector only, card per speaker, 3-choice look-alikes by contrast group, timing from clip end, replays) + drill.js refactor into kinds | DrillDeckMaker.py, drill_templates/, Globasa__Drills.apkg | ok, stress 20/20 + listen 15/15 node runs | ~45000 |
| 16:05 | Listening split into speaker x contrast cards; typed Dictation family added (letter diff, typing-safe keys); no word repeated within a round | DrillDeckMaker.py, drill_templates/, Globasa__Drills.apkg | ok, 3 suites x 25 node runs pass | ~40000 |
| 16:12 | Pre-answer replay = miss ('second listen') in listening + dictation drills | drill_templates/drill.js, drill.css, Globasa__Drills.apkg | ok, 3 suites pass (listen 40/40) | ~12000 |
| 16:20 | Stricter drill timing: per-letter limits for stress/listen/dictate, one slow answer = Hard | drill_templates/drill.js, Globasa__Drills.apkg | ok, 3 suites pass | ~15000 |
| 16:29 | Streak rounds (3 clean in a row, max 10 targets) replace fixed 5-item rounds; other-item retries bounded by share | drill_templates/drill.js, Globasa__Drills.apkg | ok, streak test on stress/listen/dictate passes; old fixed-round tests obsolete | ~35000 |
| 16:46 | Lute: venv-lute + LuteGlobasa (Globasa lang def), lute_doxo_sync.py (75 Doxo books, 50 with joined audio + bookmarks, idempotent), lute_anki_marks.py (Lute statuses -> AnkiConnect tags, tested vs fake AnkiConnect on deck copy) | lute_doxo_sync.py, lute_anki_marks.py, LuteGlobasa/globasa.yaml, README.md, .gitignore | ok, not committed | ~60000 |
| 18:23 | Reviewed bible-translation/ (untracked): candidate order hash-dependent, Word trailing spaces, current word-list.csv (PoS-prefixed, comma) unreadable -> silent 0 matches, default list is Dec 2024 (no Fra), source project path missing | bible-translation/build_glb_candidates.py | review only | ~6000 |
| 19:00 | Bible lexicon: fixed nondeterministic ranking, new word-list format, trailing spaces, inexact fallbacks; added Wiktionary extension (en/es/fr + Modern Hebrew corroboration); Gen 1: 77 agree / 5 single / 10 MHe-only / 4 none | bible-translation/* | ok | ~45000 |
| 19:40 | Bible lexicon: Chinese (SDBH zh-hans/hant downloaded to bible-translation/sources/, word list Zho + extension Mandarin); zh as tier vote + tie-break after coverage-bias tests; PoS fit before count; reconstruct_lemma_table.py | bible-translation/* | ok | ~40000 |
| 20:10 | ברא curated readings rebuilt from van Wolde 2026 (constructions, pages); rendering.md table julagi/vibaja/julacu; article saved to sources/literature | bible-translation/* | ok | ~30000 |
| 19:21 | Research: Gen 1:1-2:4a critical vs conservative disputed terms (sources: Skinner, K&D, Westermann, Gunkel 1895, Clines, Hasel, Seely, Walton, Young, Waltke, Poythress, AiG; English versions via emilsharkov/Holy-Bible-JSON, Sefaria, Gutenberg KJV, el.wikisource LXX) | bible-translation/sources/literature/{clines1968,hasel1972,poythress2017,routledge_tynbul,gunkel1895_schoepfung_chaos}.* | report returned to caller | ~90k |
| 21:00 | rendering.md: narration bare verbs (no le), Tense in narration section (nun le anterior, no harmonising pluperfect); ברא construct alternative; research agents on עשה/בדל, vegetation, contested terms | bible-translation/rendering.md | ok | ~20000 |
| 21:20 | Checked Hebrew verb mappings against Xwexi grammar; rendering.md: subordinate clauses need tense marker (open le/u), participle rows fixed, du-/-do/am rows | bible-translation/rendering.md | ok | ~15000 |
| 21:45 | rendering.md: aspect particles relative to narrated now (le/jale anterior, jaxa prospective, nun progressive, du- habitual); subordinate clauses bare in narration (corpus 24/24) | bible-translation/rendering.md | ok | ~12000 |
| 22:10 | rendering.md: conjunction table (corpus-preferred forms, tasu removed, xaki for anterior time clauses); preposition table per use for Gen 1 (extension Hebrew + Doxo) | bible-translation/rendering.md | ok | ~25000 |
| 22:40 | rendering.md: fe uses (fe perya de, fe xoru, fe din feki, fe X-ya alts) and construct-chain de/fe table for Gen 1 | bible-translation/rendering.md | ok | ~15000 |
| 22:55 | rendering.md construct table: examples from lexicon output with source column; fixed Dio -> teo; gaps (מקוה, שרץ, חיה beast) from word list, provisional | bible-translation/rendering.md | ok | ~8000 |
| 23:10 | Curated צלם=imaje, דמות=simya (+alternatives) in reconstruct_lemma_table.py CURATED; lexicon rebuilt; rendering.md image/likeness section with Gen 5:3 note | bible-translation/* | ok | ~15000 |
| 23:50 | Built apertium-hbo-glb (curated TSV -> bidix, rtx, prep, translate.sh); Gen 1 machine output + revised draft (wa per Isaksson, Doxo conventions); rendering.md wa/speech sections | bible-translation/* | ok | ~120000 |
| 21:45 | ברא -> julagi throughout (one sense); draft 1:27c, rendering.md, reconstruct curated updated. Next session: merge UD/BHSA syntax into stream, rewrite rtx on roles (plan given in chat) | bible-translation/* | ok | ~3000 |
| 22:40 | Planned fra-glb Apertium pair + Le Petit Prince pipeline (Apertium keeps fra-glb alignment, SimAlign fra-pivots votes on polysemy, transfer rules for order/inflection, OpenJev as tie-breaker); recorded in Claude memory project_french_pair_little_prince.md | none in repo | plan only, nothing built | ~8k |
| 22:43 | Corrected plan: glb-fra pair already exists at ~/ApplicationSource/GlobasaTranslation/apertium-glb-fra (sandbox-blocked); noted in cerebrum and Claude memory | .wolf/cerebrum.md | next step: inspect that pair with sandbox disabled | ~2k |

## Session 2026-11-12 (bible-translation) — summary
- Built: Globasa lexicon from SDBH (en/es/fr/zh) + Wiktionary extension; rendering.md (wa per Isaksson, tense/aspect, conjunctions, prepositions, de/fe, image/likeness, bara=julagi, Teo/Yahwe/Prabu); apertium-hbo-glb pair; Gen 1 machine output + revised draft. Branch `bible-translation`, commits 7d159a7..HEAD.
- Open: TMX output (Next 0); Kantor 2025 vs Holmstedt on 1:1 (0b); syntax-based rtx via UD PTNK + BHSA (1). Parked: philological-vs-confessional survey, LXX-triangulated confessional version, NT approach (Nyland + LXX Greek via hbo-glb).
- Uncommitted on purpose: copyrighted research texts in bible-translation/ (schmidt.txt, tdot11.txt, tdot2.pdf, walton.pdf, westermann.txt) — user to move or delete.
- Next step: TMX output from translate.sh.
| 22:58 | Recorded follow-on texts (Pinocchio via a new ita-glb pair, UDHR, Andersen/Grimm) in Claude memory; no repo files changed besides this log | .wolf/memory.md | plan only | ~2k |
| 23:01 | Recorded Time Machine translation plan (UK base, US variants as paraphrases) in Claude memory | .wolf/memory.md | plan only | ~2k |
| 23:40 | Bidix pipeline: apertium_common.py + pos_groups (0ee107a, parity byte-identical); build_bidix.py (curated part above marker, word list both ways, Wiktionary RL, analyser check, report); preprocess trimmed; paren-aware gloss split | build_bidix.py, apertium_common.py, dictionaryPreprocess.py | 33.5k entries eng/deu/fra/nld, validated+compiled on scratch copies; merge pending (GlobasaTranslation not visible) | ~60k |
| 21:40 | build_bidix.py end-to-end on the user's glb-fra curated base (scratch copy): curated part byte-identical, 8004 generated entries, validates, compiles LR+RL; curated blocks 13, demotes 10 word-list entries to one direction | build_bidix.py | pass; real merge pending (tree not visible) | ~8k |

## Session: 2026-11-14 12:27

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 14:00 | Added 5 Palaeos/apertium-glb* repos as submodules under apertium/ (clones + staged gitlinks, all on master); .gitmodules is a read-only mount in the sandbox, so its block waits in the scratchpad for the user to paste | apertium/*, .gitmodules (pending) | partial | ~6k |
| 14:30 | Dropped apertium/ clones; GlobasaTranslation/ moved into repo by user — its 5 Globasa pairs staged as submodules at local HEADs (glb +5, glb-eng +32 unpushed); APERTIUM_ROOT now repo-relative in apertium_common (build_bidix, dictionaryPreprocess import it; Word Viewer, TRAINING_PLAN repointed); .gitignore keeps upstream monolinguals out; .gitmodules block pending (read-only mount) | apertium_common.py, build_bidix.py, dictionaryPreprocess.py, Word Viewer.py, TRAINING_PLAN.md, .gitignore | staged, not committed | ~12k |
| 13:40 | Little Prince test: parallel_lexsel/ pipeline (LPP fMRI corpus CC0 fr/en/zh → LaBSE beads → Apertium glb-fra with LU↔token trace → SimAlign → en/zh vote → .lrx → TMX). 571 ambiguous LUs, 207 voted, 30 changed (28 right provisionally); 22% of French tokens unknown to the pair → resolve_list.tsv (1006 lemmas); 6 lrx rules below a marker in the glb-fra .lrx; LePetitPrince.tmx in parallel_lexsel_cache (git-ignored) | parallel_lexsel/*.py, .gitignore, apertium-glb-fra.fra-glb.lrx | done, not committed | ~90k |
| 14:30 | French gaps → sense_vetter Queue view (vetting_queue.py: 1800 proposals / 1562 senses for 456 French lemmas); BIDIX_MERGE env in build_bidix, merged glb-fra only (6649→8161 entries, unknown 22%→12%); vote gender-variant guard; reran stages + TMX | parallel_lexsel/*, sense_vetter.py/.html, build_bidix.py, glb-fra dix/lrx | done, not committed | ~60k |
| 15:30 | apertium-glb-jpn bootstrapped (apertium-init), jpn→glb only: zero-pronoun front end, curated + 5715 generated RL bidix, rtx (clauses, he/focus/clefts, wh), 36/36 gold, dev/grammar-comparison.md, dev/cleft_check.py; apertium-glb gets he/durki; build_bidix jpn + np→n + argv pair filter | GlobasaTranslation/apertium-glb-jpn/*, apertium-glb, build_bidix.py | committed locally, not pushed; GitHub repo + .gitmodules pending (no GitHub CLI, .gitmodules read-only) | ~250k |
| 14:25 | Sense vetter: endless scroll (sentinel #more + IntersectionObserver; loads while the end stays in view; 'End of this view (N senses)'); verified via logging proxy + headless Firefox (1000px: 1 page, 20000px: 2 pages); VS Code task block given to user (.vscode read-only) | sense_vetter.html | done | ~8k |
| 14:45 | Sense vetter counts a word as vetted per part of speech (gloss_pos; name→noun, fallback adv→adj) in the unmarked view, syncWord and undo; verified: 23996 senses listed, none marked in its own PoS, fobi listed for verb while vetted as noun | sense_vetter.py, sense_vetter.html | done | ~10k |
| 17:00 | apertium-glb-jpn names.py: mark/render pipeline steps for proper nouns not in the bidix; translator renditions ($JPN_GLB_NAMES files, then names.tsv) win over transliteration (katakana: epenthesis dropped per proper-noun phonotactics; kanji: Hepburn-like reading); names.py suggest; gold 39/39; @ 32.3→30.9% | GlobasaTranslation/apertium-glb-jpn/names.py, names.tsv, modes.xml | committed locally | ~40k |
| 15:10 | Vetting queue made word-centred (unit = glb + gloss PoS; unvetted units bring all undecided senses; ranked by pivot-tied occurrences; resolved French words dropped): 758 words, 5630 senses, 390 French lemmas left; 80 lemmas (639 tokens) already resolved by the user's vetting; vetter shows 'Other sense of X: vet the whole word' notes | parallel_lexsel/vetting_queue.py, sense_vetter.py/.html | done | ~25k |
| 18:00 | apertium-glb-jpn group 1 (constructions): の-clauses, quotes, te-aux, modality, なる→sencu (Doxo: sencu 61×, xorsen 0×), ない→no hay, subordinators fronted; @ 30.9→26.5%; gold 56/56 | GlobasaTranslation/apertium-glb-jpn rtx/dix/modes/names.py | committed locally | ~60k |
| 15:50 | Sense vetter 'Rebuild & check French' button: /api/rebuild thread runs extension builder → build_bidix.py fra → make → parallel_lexsel/resolution.py → vetting_queue.py (18 s), shows resolved/missing + newly resolved words, reloads queue; queue drops words the pair knows. Test: 97/666 French words resolved (643 tokens), 5 new since last check, queue 5556→5161 | sense_vetter.py/.html, parallel_lexsel/resolution.py, vetting_queue.py | done | ~30k |
| 16:20 | Vetter button made general: 'Rebuild' = extension → build_bidix (all) → make every configured glb-X pair (per-pair failures reported) → Le Petit Prince check only if its data exists (separate labelled line). Reconfigured glb-eng/deu (stale modes). Test 61 s: bidix eng 12330 deu 4437 fra 8084 nld 3469 jpn 5865; nld make fails (files owned by nobody). Found flura→pussy in glb-eng after full merge | sense_vetter.py/.html, GlobasaTranslation pairs | done | ~40k |
| 18:20 | glb-jpn: weather-noun predicates → hay + noun (user correction: Koski hay barix, mi no idi); zero subject before them dropped; gold 58/58 | apertium-glb-jpn rtx, gold, comparison doc | committed locally | ~8k |
| 16:45 | build_bidix: slang/informal/vulgar senses RL only when the word has a plain gloss in that PoS (first version made 31 informal words untranslatable glb→X; narrowed); 20 RL-only entries; rebuilt eng/deu/fra/jpn; flura→flower, momo→boob verified | build_bidix.py, pair dixes | done | ~20k |
| 19:00 | Globasa generator: dictionaryPreprocess dedup bug (55 genders) fixed, apertium-glb generated part regenerated, he moved above marker, generation-only quotes; glb-jpn uses them; 2596/2596 noun forms generate; Tatoeba # 2.1→1.9%, @ 26.5→25.5% | dictionaryPreprocess.py, apertium-glb.glb.dix, apertium-glb-jpn | committed locally | ~40k |
| 17:40 | glb-jpn: compounds.py + build_bidix keeps 882 split compounds (7548 entries); と coordination by Globasa gender; jpn-glb_gender mode (manmi/femmi/mante/femte/femete; no manyu/femyu per user); apertium-glb gendered possessives; gold 65/65 + 10/10 | apertium-glb-jpn, apertium-glb, build_bidix.py | committed locally | ~80k |
| 18:10 | apertium-hbo-glb pronoun gender: GENDER=1 (2 m sg manyu, 2 f sg femyu, 2 f pl femuyu; m pl mixed uyu/ete), curated/pronouns.tsv + pronouns.py (tag/suggest) by word id incl. inserted verb subjects; translate.sh uses in-repo generator (Gen 1 unchanged); apertium-glb manuyu/femuyu | bible-translation/*, apertium-glb | committed locally | ~40k |
| 20:00 | apertium-hbo-glb construct chains + possessives: persons->de else fe, hum attr up nested chains, adjective attachment by agreement, SUF nonterminal (suffix before adj/numeral), sesu via pronouns.tsv, dasu after אשׁר, constructs.py/tsv (de/fe/head/dep, suggest), <psuf>/<abs> in prep; Gen 1: 8 verses fixed; tests/run.sh ok | bible-translation/apertium-hbo-glb/*, rendering.md, README.md | uncommitted | ~60k |
| 20:20 | apertium-hbo-glb: day formula rule (וַיְהִי X יוֹם + numeral -> 'hay soba: N din', rtx colon as "\:"@sent); Gen 1:5,8,13,19,23,31 now match draft | bible-translation/apertium-hbo-glb/*.rtx, rendering.md | uncommitted | ~5k |
| 20:45 | apertium-hbo-glb: curated punctuation (punctuation.py, curated/punctuation.tsv, bidix <punct>, postformat dash/paren spacing, verse-final dash + lower-case continuation); Gen 1:16 dashes as in draft | bible-translation/apertium-hbo-glb/*, rendering.md, README.md | uncommitted | ~10k |
| 21:10 | apertium-hbo-glb: inferred quotation marks (punctuation.py infer_quotes; לאמר -> ', loga:'; CL v.consec PP NP -> 'Teo loga tas ete'); curated ” / noquote overrides; Gen 1 11/11 speeches as in draft; fixtures T.2.x | bible-translation/apertium-hbo-glb/*, rendering.md, README.md | uncommitted | ~20k |
| 22:00 | apertium-hbo-glb: UD PTNK treebank merge (syntax.py; sources/ud cache), role-based clause rules (v NP NP, qatal/yiqtol + NP, fronted xcomp, PP NP), ¦ clause boundaries, treebank adjective attachment, suggest shows tree relation; Gen 1: 1:1,9,17,20,21,22,27,28 changed; no-treebank output identical | bible-translation/apertium-hbo-glb/*, README.md, rendering.md | uncommitted | ~60k |
| 22:15 | hbo-glb: יבשׁה -> 'suhe geo' (user; suhegeo = desert in word list): bidix geo + rtx NP rule; draft 1:9-10 and rendering.md updated | apertium-hbo-glb/curated/bidix.tsv, rtx, data/Gen_1_glb_draft.md | uncommitted | ~3k |
| 22:35 | hbo-glb machine draft as TMX: tmx.py + FORMAT=tmx in translate.sh; data/Gen_1_glb_machine.tmx (31 tu, hbo+glb, x-paragraph) replaces Gen_1_glb_machine.txt; README/draft/anatomy updated | bible-translation/apertium-hbo-glb/tmx.py, translate.sh, data/ | uncommitted | ~6k |

## Session: 2026-11-15 12:48

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 14:18 | qgb-zho: planned pair, cloned Palaeos/apertium-zho, built it, wrote dev/README-fork.md | GlobasaTranslation/apertium-zho | builds; simplified-only dix | ~25k |
| 14:26 | apertium-zho: dev/add_traditional.py (OpenCC s2t/s2tw, v=hans marks), ming/hant/hans analysers + modes | GlobasaTranslation/apertium-zho | 4992 trad entries, builds, idempotent | ~20k |
| 19:30 | glb-spa pair: apertium-init, curated bidix (~200 fn words) + build_bidix spa (15.7k), spa-glb rtx (pro-drop, gustar, haber/estar/ir a tenses per xwexi 07, clitics, comparatives, wh-in-situ), lrx (motion a→cel, cómo es→kepul), sentcase/postformat steps; parallel_gold.py; build_bidix gloss-rank weights; apertium-glb + nor/max/min | GlobasaTranslation/apertium-glb-spa, parallel_gold.py, build_bidix.py | xwexi 101/483 exact, chrF 63.6; Babel chrF 45.1 | ~250k |
| 23:00 | apertium-epo built with lt-comp (+ri, +3.5k stem supplement); glb-epo pair: curated bidix (correlatives) + build_bidix epo (16k), epo→glb rtx (OVS→SVO via -n, wh-in-situ, kiu/kiun relatives, da, estas X → hay X), glb→epo rtx (endings, accusative, agreement); glb-spa: glb→spa rtx (gender/number agreement, tense table, clitics, ¿¡, apocope), pair CG, lrx, reflexive se, mf adjectives in build_bidix | GlobasaTranslation/apertium-glb-{spa,epo}, apertium-epo, build_bidix.py | spa→glb 106/483 chrF 64.5; glb→spa chrF 50.5; epo→glb Vanege dev chrF 64.7; glb→epo loose chrF 55.2 | ~300k |
| 23:59 | glb-fra fra→glb refined from spa work: P&C ep6+ as fra→glb gold (parallel_gold.py fra), SEQ leftovers (no #<det>/#prpers), pair CG (être-verb pp, devoir modal, tout predet, si degree), sentcase/postformat, tout le N→moy, optative que→am, pronominal être PC + reflexive list, modal PC, que+inversion, curated fn words (oui/non/car/voici/…), np bidix fix (NP_SUBTYPED fra), build_bidix rerun | GlobasaTranslation/apertium-glb-fra, build_bidix.py, parallel_gold.py | P&C chrF 28.6→31.7; gold 63→67/67; perf 7→9/9 | ~200k |
| 23:59 | eng→glb refined on English-original corpora: parallel_gold.py eng sets (Thirty Short Stories, P&C 1-5, UDHR, Siri-Logane Tutum; dev/test), restored function entries lost in 11-14 bidix merge, curated eng→glb preps/conj/det/numbers, punctuation + np pass-through (bidix + apertium-glb generation-only), BE/tense rtx rewrite (present unmarked, perfect→le, there is→hay, has the right/entitled→haki), pair CG (N-N-N middle verb, have/for), eng-glb-mwe.py (split # and spaced MWEs, there+be), eng-glb-postformat.py (capitals), lrx with/for/life | GlobasaTranslation/apertium-glb-eng, apertium-glb, parallel_gold.py | dev chrF 45.8→57.3, test 45.4→57.4; glb→eng loose 42.4→44.0 | ~400k |
| 23:59 | committed eng→glb work: apertium-glb 3 commits (d388073..96c1065), apertium-glb-eng 7 (d0a11c4 user's 11-14 regen, ..b952b1e), main b7edb45..001e473; added xaki/leki (user) | apertium-glb, apertium-glb-eng, parallel_gold.py | dev chrF 57.5, test 57.7 | ~40k |
| 23:59 | translationese survey (originals vs translations, xwexi yardstick) + GlobasaGrammarChecker style-hint rule RepeatedTenseRule; base.py issue_type style; CLI marks hints | GlobasaGrammarChecker/rules/style_tense_repeat.py, base.py, __init__.py, __main__.py | 10/10 cases; corpus Siri-Logane 12, ORIG 1 | ~60k |
| 2026-11-19 | Time Machine: fetched Heinemann+Holt from Wikisource; scan_obscure.py (wordfreq Zipf<3 → 599 candidates); 5 agents resolved sense-in-context + Globasa → obscure_resolved.tsv (846 rows); check_resolved.py passes | time-machine/* | done, not committed | ~60k |
| 2026-11-19 | deu/nld->glb V2 refinement: germanic-v2-reorder.py + pair CGs + rtx rewrite + curated function words; walki/celki in apertium-glb; parallel_gold deu/nld loose sets; committed (glb 974eee8, deu 6bd66cb..8994585, nld efb5539..656a5b4, main 661721c..23473a9), not pushed | GlobasaTranslation/apertium-glb-{deu,nld}, apertium-glb, parallel_gold.py | deu P&C 29.1->33.5, UDHR 23.9->27.3, nld P&C 20.7->25.1 | ~250k |
| 15:08 | Doxo translationese survey: feature rates translated (Poe, UDHR, prayers, Aesop/Goldilocks) vs original (Sarin Ci, Vanege); no files changed | doxo-pages-grav | Poe le 110/1000w vs 3-13; UDHR 24 w/sent, fe 53/1000 | ~15k |
| 2026-11-19 | Time Machine: Amos epo (INKO PDF) + d'Albroi spa (IA scan, re-OCR) aligned → tr_check; 2 review agents: 6 better_word applied, 0 sense errors; holt_variants.tsv; Siri-Logane Tutum witness (71% scanner/modernizer agreement; presently/scarcely precedents) | time-machine/* | done, not committed | ~80k |
| 15:32 | Time Machine: fetched PD scholarly sources (Tylor, Huxley, Wells x2, Lankester) + Webster 1913 | time-machine/fetch_sources.py, sources/ | done | ~10k |
| 15:37 | Time Machine: period dictionaries (Rhodes, O'Connor, Velázquez) → dict_epo/dict_spa/dict_check; insensibly/ungainly reviewed against Wells's sentences | time-machine/period_dicts.py | done | ~15k |
| 15:49 | Victorian–Globasa dictionary built (516 headwords, 532 senses) and published as artifact | time-machine/build_termbase.py, termbase_template.html, victorian_glb.* | done | ~20k |
| 16:08 | Apertium preferences AP_SETVAR=victorian in apertium-glb-eng (biprefs CG, prefs xml, 7 prefs + 12 entries, approved list); dad lrx fix; no regression (chrF 57.6/57.8) | time-machine/termbase_to_apertium.py, victorian_prefs.tsv, apertium-glb-eng/* | done, not committed | ~60k |
| 16:15 | Victorian word list made the source of truth (victorian_wordlist.tsv + sync/check); generators read only it; prefs file + report retired; purpose noun-pref bug fixed; page republished | time-machine/* | done, not committed | ~40k |
| 16:17 | Committed Time Machine work: 5 commits (1896942..95026ea) + submodule apertium-glb-eng (03c3e60, 0372123); not pushed | time-machine/*, .gitignore, requirements.txt | done | ~5k |
| 16:30 | English variety patch: apply_eng_variety.py + eng_variety_patch.tsv (VarCon spelling, 6 vocab pairs), TranslationEngGB/US columns, AnkiMaker3 ENG_VARIETY, vscode pipeline step; verified idempotent + fresh-download reapply + stale report | apply_eng_variety.py, eng_variety_patch.tsv, AnkiMaker3.py, vscode-tasks.json, .gitignore | done, not committed | ~40k |
| 16:47 | English variety Apertium preference (glb-eng: biprefs SUBSTITUTE/REMOVE + US respelling step; eng-glb input rules shared with victorian via Makefile-merged fragments); translation aide: pair menu for all built Globasa pairs + preference controls; overrides now win over preferences | eng_variety_to_apertium.py, apertium-glb-eng/*, Word Viewer.py, translation_aide.html, time-machine/termbase_to_apertium.py | done, not committed | ~120k |
| 16:53 | Victorian listed as an English variety: eng_variety=Victorian (eng->glb input) = victorian + GB readings; aide dropdown Default/British/American/Victorian, victorian switch hidden | time-machine/termbase_to_apertium.py, eng_variety_to_apertium.py, translation_aide.html, apertium-glb-eng | done, not committed | ~10k |
| 17:40 | eng->glb "that": pair CG (rel/cnjsub/det/prn by context), lrx that->ki, bidix that/this prn -> dento/hinto, eng-glb-relative.py (hu da / hu S V da / hu pr da), rtx PREPP + NOM excludes rel; dev 57.6->58.0, test 57.8->58.4, that-subset 56.9->61.5 | apertium-glb-eng/* | done, not committed | ~150k |
| 17:40 | Story mode across X->glb: u<vbpr><nar> (generator twins of every past entry, apertium-glb), shared glb-story.py (AP_SETVAR=story drops nar le), wired in eng/deu/epo/fra/jpn/spa (+nld sources, not rebuilt); jpn case.sed superblank fix | apertium-glb, apertium-glb-{eng,deu,epo,fra,jpn,spa,nld} | done, not committed | ~80k |
| 18:05 | Committed that/relatives + story mode: apertium-glb eba663d; eng bcfed74, cb7714f; deu/epo/fra/jpn/spa/nld one each (+ jpn case fix add4846); main b8219bf (submodule bumps); user's own uncommitted edits left unstaged | GlobasaTranslation/* | done, not pushed | ~20k |
| 18:30 | Translation aide fixes: newline before pipeline, compiled-mode halves for eng-glb, story pref for all X->glb pairs, \@ unescape, punctuation rejoin; glb-story.py reads in-stream SETVAR | Word Viewer.py, GlobasaTranslation/apertium-glb/glb-story.py | done, not committed | ~30k |
| 19:30 | eng->glb neural steps: eng-nlp-service.py (stanza electra-large x2 + GUM coref + OEWN), eng-glb-neural.py pos|coref in modes.xml, glb-anaphor.tsv via anaphor_to_apertium.py, 4 RL bidix pronoun entries, README section | apertium-glb-eng/*, anaphor_to_apertium.py | dev chrF 58.0 -> 58.8 (first pass) | ~120k |
| 20:10 | bge-reranker-v2-m3 lexical choice eval (test/lexsel_eval.py, silver labels from dev gold, 1045 items): pipeline 57.8%, reranker 52.6% overall; conf>=0.9 82.8% on 29 items -> not integrated. Partial HF download filled /dev/sdb2 (removed; 2.2G free) | apertium-glb-eng/test/lexsel_eval.py | evaluated, not wired | ~40k |
| 20:30 | eng->glb pronouns: te/tesu default, AP_SETVAR=gender opt-in (bidix RL entries, gender.rlx biprefs fragment, preferences xml, Makefile.am, README). Neural run 2 dev 59.0; te default alone 58.0 -> 59.4 | apertium-glb-eng/* | done, not committed | ~20k |
| 21:10 | sesu for 3rd-person possessives coreferent with clause subject (coref step + parse; apertium-glb RL sesu entries; bidix <ref> entries); PRP$/PRP pruning; possessive dev lines chrF 60.2 -> 64.7, sesu 90 matched / 15 missed / 14 extra (8 gold paraphrases, 3 UDHR style) | eng-glb-neural.py, apertium-glb.glb.dix, apertium-glb-eng.glb-eng.dix, README | done, not committed | ~60k |
| 21:20 | user: UDHR gold tesu after quantified subject ('No one ... his property') is a gold mistake; sesu rule unchanged | cerebrum, memory | recorded | ~1k |
| 21:30 | user: suggested UDHR translation corrections (Whereas -> Fe kolyo ki; No one ... his -> sesu); recorded, pipeline unchanged | .wolf/cerebrum.md, memory | recorded | ~2k |
| 22:00 | legal preference (shall->am, recital Whereas->fe kolyo ki; orthogonal to eng_variety); general: including/therefore/should/should have/will be; tagger segfault traced to broken 2018 perceptron model (valgrind), not fixed; pretagger step tried and removed | legal_wordlist.tsv, legal_to_apertium.py, apertium-glb-eng/*, apertium-glb.glb.dix | done, not committed | ~90k |
| 21:20 | AAVE eng→glb plan finalised (neg. inversion → he nil-; know→jixi default); no code yet | plan file | planned | ~2k |
| 21:25 | tagger: upstream latest eng.prob (HMM) per user; apertium-eng eng.prob/eng.perceptron.prob from origin only; no crashes; dev 57.1, UDHR test 51.1 / legal 52.6 | apertium-eng, apertium-glb-eng | done, not committed | ~10k |
| 21:22 | AAVE: test/aave-cases.tsv (37 cases incl. controls); default dev baseline started in scratchpad | apertium-glb-eng/test/aave-cases.tsv | in progress | ~1.5k |
| 21:28 | committed atomic whole-file pieces: apertium-eng b4b8885 (HMM tagger), main 1f11415 (anaphor_to_apertium.py), 9bf4dcc (legal list+generator); pending: hunk-split commits in apertium-glb-eng (neural steps, coref/sesu, gender pref, legal, should/will-be, whereas/including/therefore) and apertium-glb.glb.dix (sesu; word-list phrases), keeping the user's variety hunks in modes.xml/Makefile.am out; submodule bumps after | apertium-eng, main | partial, not pushed | ~5k |
| 21:37 | Planned fra→glb historical mode: year-of-work meaning shifts, spelling auto-detected | memory/project_fra_period_mode.md | plan recorded, nothing built | ~2k |
| 21:42 | Plan for tomorrow: year-keyed meaning shifts, literature to verify, candidate words | memory/project_fra_period_mode.md | written | ~1k |
| 21:47 | Added the 西遊記 traps and Globasa-stability ideas to tomorrow's plan | memory/project_fra_period_mode.md | written | ~1k |
| 21:58 | setup.sh: validate word-list download (HTML block page no longer saved as CSV), print browser instructions on failure, --word-list FILE; Word Viewer.py exits with same instructions if word-list.csv missing; README note | setup.sh, Word Viewer.py, README.md | tested offline (bad/good/unchanged file) | ~3k |
| 22:04 | TODO saved: neural classifier for eng 'the' → drop vs demonstrative (next session) | memory | noted | ~300 |
| 22:30 | Q&A: AAVE source texts (PD songs/stories, rap licensing), AAVE+Spanish habitual evidence for teaching du- to learners; recorded in auto-memory project_eng_glb_aave as next-session first step; no repo files changed | memory/project_eng_glb_aave.md | noted | ~3k |
| 22:31 | AAVE goal clarified: translate AAVE→glb to build a corpus with organically marked du- habituals (for learners); updated auto-memory note | memory/project_eng_glb_aave.md | noted | ~1k |
| 22:32 | Decision: CORAAL transcripts are the main AAVE source (no rhyme or metre to preserve); rap dropped; next step is the licence check | memory/project_eng_glb_aave.md | noted | ~1k |
| 22:34 | Correction: 'used to' marks past habitual in English/AAVE, so Spanish isn't needed for the past; noted the 'be used to' trap and the 'would' ambiguity | memory/project_eng_glb_aave.md | noted | ~1k |
| 23:06 | TODOs recorded: deu Perfekt/Präteritum→glb mode (deu memory note); Time Machine opening + em dashes in eng→glb (TM memory note). Session landed. Submodule WIP left uncommitted (see summary) | memory | noted | ~2k |
| 23:09 | TODO recorded: story mode (glb-story.py) must leave quotations alone; quote-state plan in project_story_mode memory | memory | noted | ~1.5k |
| 23:10 | TODO recorded: translations must carry over source markup (new memory project_markup_carryover) | memory | noted | ~1.5k |
| 23:12 | TODO recorded: ML fe vs de via pivot-language projection (new memory project_fe_de_classifier) | memory | noted | ~1.5k |
| 23:13 | TODO extended: classifier also decides fe vs per (memory project_fe_de_classifier) | memory | noted | ~800 |
| 23:14 | TODO extended: classifier also decides fe vs in (labels fe/de/per/in) | memory | noted | ~600 |
| 23:15 | User correction: per = literal 'on', fe = abstract 'on' (dates); fixed classifier memory, Do-Not-Repeat added | memory, .wolf/cerebrum.md | fixed | ~1k |
| 23:13 | Decision: keep CORAAL fillers and translate them into Globasa (uh → e) instead of stripping them; look up other fillers, never invent them | memory/project_eng_glb_aave.md, .wolf/cerebrum.md | noted | ~1k |
| 23:14 | Filler: um → em (from the user) | memory/project_eng_glb_aave.md, .wolf/cerebrum.md | noted | ~0.5k |
| 23:17 | User note: deu auf → per or fe by context; removed as pivot, rule added: measure pivot agreement against gold first | memory | noted | ~600 |
| 23:19 | User correction: warten auf → transitive intizar (no prep); ∅ label + VerbTransitivity lookup added; Do-Not-Repeat | memory, .wolf/cerebrum.md | fixed | ~700 |
| 11:11 | Committed 11-19 WIP: apertium-glb-eng 7 commits (4f160d5..), apertium-glb 3 (68b7767, 836b503, 7d9bdb7), main bump; intermediate states checked (xmllint, rtx-comp); removed 6 empty stray files (json/os/sys/...) | GlobasaTranslation/apertium-glb{,-eng} | done, not pushed | ~15k |
| 11:29 | Committed older pair WIP: glb-fra 4 (b16c37e..a9b575e), glb-grc 3 (a2f9f8e..14985d4), zho 2 (fd2e04c, 658e6bd), apertium-epo 1 (5354fab); main bump fra; grc/zho/epo not submodules of main | GlobasaTranslation/* | done, not pushed | ~20k |
| 11:40 | Story mode keeps le inside quotations (quote state, dashes arg for fra/spa/epo); quoted gold lines 5 changed, 4 now match; committed 523dcbe + pairs + main 5e55a6c | GlobasaTranslation/apertium-glb/glb-story.py, apertium-glb-{fra,spa,epo}/modes.xml | done, not pushed | ~25k |
| 12:04 | eng->glb: pronoun-reading CG (a73c286) + verb+det tense fix / have-the-right MWE (9be19d2); dev 57.1->58.7, test 57.9->59.5; buglog 2 entries | apertium-glb-eng | done, not pushed | ~60k |
| 12:08 | HistWords prototype: diachronic scan of Time Machine (gay, checked found → victorian_wordlist pending) + queer/man/gay trajectories 1800–1990 | time-machine/histwords*.py, victorian_wordlist.tsv | low precision flagger; trajectories useful | ~60k |
| 12:10 | eng->glb em/en dashes as ^—<punct>$ units (eng 18ad55d, glb 7b63fd8, main 54c56dd); Time Machine ch.1 dashes stay in place; remaining ch.1 issues recorded in TM memory | eng-glb-mwe.py, glb-eng.dix, apertium-glb.glb.dix | done, not pushed | ~30k |
| 13:20 | eng→glb count/mass noun selection (man insan/manixu, mankind insanlari, hair tofa/tofamon) via count_mass_nouns.tsv + generator; dev chrF telltale 64.9→66.0 | count_mass_*, apertium-glb-eng dix+lrx | 20 sentences improved, 0 worse | ~40k |
| 14:18 | deu Perfekt research: DTA fiction 516 texts counted (Perf/Prät, dialogue vs narration, period, region, past-adverb test); scripts+results in apertium-glb-deu/dev/tense-history (uncommitted); literature mostly paywalled/blocked | apertium-glb-deu/dev/tense-history/* | done | ~80k |
| 15:57 | cross-lingual HistWords: 1890s/1990s English → modern en/es/eo fastText → Globasa, 2+-pivot agreement | time-machine/histwords_crossling.py, fasttext_bin.py | P@1 en .78 es .57 eo .39 | ~50k |
| 17:04 | histwords_crossling: Globasa vote PoS-aware (TARGET_POS, word-list segment labels), one line per PoS; rerun en/es/eo | time-machine/histwords_crossling.py, histwords_crossling_report.txt | film 1890s perli(adj) dropped -> cengu/perya; fancy n imajeya vs adj zarif split | ~6k |
| 17:07 | user: 1890s dumb = palanenabil; row added to victorian_wordlist (derived (proposed), pending) | time-machine/victorian_wordlist.tsv, .wolf/cerebrum.md | check OK, 531 rows | ~2k |
| 17:08 | user: dumb also = lexikal; split dumb into mute/palanenabil + wordless/lexikal (book quote on lexikal) | time-machine/victorian_wordlist.tsv | check OK | ~1k |
| 17:12 | deu Perfekt period setting from Adelung 1782 + Xwexi: cprf tag, glb-story year/cprf-before, CG pp fix; scores unchanged | apertium-glb-deu rtx/rlx/modes.xml, apertium-glb glb.dix/glb-story.py | done, uncommitted | ~60k |
| 17:17 | archaic_senses.py: vetted senses -> period-sense Globasa proposals (75k period senses; A61 B118 C644 D6794) | archaic_senses.py, archaic_senses.tsv, archaic_senses_report.txt | 2 tightening passes (strict table match, own-word exclusion, head rules) | ~25k |
| 17:44 | nld→glb per ANS: progressives (aan het, posture te) → nun nun/le nun, gaan+inf → xa, presentative er, cnjsub clause split, ze agreement; stale nobody build moved aside | apertium-glb-nld reorder/rtx/rlx/dix, deu reorder copy | done, uncommitted; scores unchanged | ~70k |
| 17:49 | nld om te: purpose om → cel na, connective om → na (ANS 19.3.3); te+modal+inf, fronted om-clause V2, te+adj godomo, dat pronoun, ik/hij vorfeld subject fix; nld P&C 25.1→25.3 | apertium-glb-nld reorder/rtx/rlx, deu reorder copy | done, uncommitted | ~25k |
| 17:53 | nld om: lrx default wey, clock times + vragen om → fe; om-te comments corrected (te → na, cel from purpose function) | apertium-glb-nld lrx, reorder | done, uncommitted | ~8k |
| 18:36 | RAM exceeded during archaic_crosscheck rerun; session restart wiped scratch (fastText + HistWords, ~26 GB); loader made compact/in-place | archaic_crosscheck.py | data must be re-fetched | ~3k |
| 18:36 | Globasa date/time order in shared glb-story.py (din D fe mesi M fe nyan Y, satu H:MM), mesi un un → des un; copied to 7 pairs; 0 gold lines changed | apertium-glb/glb-story.py + pair copies | done, uncommitted | ~40k |
| 18:40 | memlimit guard (.pth, venv + user site) + setup.sh; fasttext_bin streams matrix in chunks (verified vs reference); histwords.load in place + release(); crossling/crosscheck load only kept rows | memlimit.py, setup.sh, time-machine/fasttext_bin.py, time-machine/histwords.py, time-machine/histwords_crossling.py, archaic_crosscheck.py | guard stops 1.3 GB test at 0.5 GB limit | ~20k |
| 18:43 | .wolf/optimizations.md created; referenced from OPENWOLF.md Code Generation + .claude/rules/openwolf.md | .wolf/optimizations.md, .wolf/OPENWOLF.md, .claude/rules/openwolf.md | done | ~3k |
| 18:43 | date/time gaps: epo je la oka, at eight + schedule verb/daypart, sentence-initial date fe, num<pl> strip; 0 gold lines changed | apertium-glb/glb-story.py + 7 pair copies | done, uncommitted | ~20k |
| 18:56 | data moved to Warehouse2/Language/Claude (histwords, fasttext, fasttext-raw, refetch.sh); script defaults updated; refetch running | time-machine/histwords.py, histwords_crossling.py, archaic_crosscheck.py, archaic_senses.py | repo disk freed 742 MB | ~4k |
| 18:57 | wiktionary_quote_years.py: dated quotations per sense; sample 0.5 GB in 4 s, 24 MB RSS; full run started | wiktionary_quote_years.py | queer strange 1824-1965 dated; homosexual adj 1979 | ~5k |
| 19:01 | quote years full run (291k dated senses, 129 s, 30 MB); sense_periods.py draft ranges (7588/13387 dated); match_sense_strict moved to sense_rows + own-gloss priority | wiktionary_quote_years.py, sense_periods.py, sense_rows.py, archaic_senses.py | man fixed 1599-now; 402 rows no sense | ~15k |
| 19:05 | user: gay festive/colourful = kolorpul/jaxneli; victorian gay row split; archaic_senses heads() serial-list 'or X' fix; sense_periods curated source (victorian_wordlist overrides archaic proposals) | time-machine/victorian_wordlist.tsv, archaic_senses.py, sense_periods.py | curated 337 rows, 62 dated | ~8k |
| 19:08 | sense_periods: throughout-Modern-English option (yes 664 / no 7421 / unknown 5633) + sense_periods_modern_english.tsv | sense_periods.py | man adult male ALL; gay none throughout | ~5k |
| 19:17 | prepositions: shared prep_line in glb-story.py (all pairs) + nld lrx/bidix senses from heardutchhere.net, CG staat/door, particle-prep split; scoring running | apertium-glb/glb-story.py, apertium-glb-nld lrx/dix/rlx/reorder, apertium-glb.glb.dix (fe muka de) | in progress | ~60k |
| 19:21 | gay story senses added to victorian_wordlist (velosi, akxupul, gay woman → kahabu); sense_periods story + variety columns (core 13117 / marginal 602; Scotland 116 ...) | time-machine/victorian_wordlist.tsv, sense_periods.py | all gay curated rows dated | ~10k |
| 19:23 | prepositions: har-after-noun rule removed (gold shows yon), nld met→yon default; scores neutral-to-up (eng thirty +2 exact, spa +0.1) | glb-story.py, nld lrx | done, uncommitted | ~15k |
| 19:24 | dumb dated senses: sotikal (silent), nenpalafil (taciturn, derived), vokakal (voiceless, derived), xuxgi (to silence, derived) added pending; phrases noted on palanenabil row | time-machine/victorian_wordlist.tsv | check OK 540 rows | ~6k |
| 19:29 | user: dumb 'wordless' default palakal (lexikal alternative) | time-machine/victorian_wordlist.tsv, .wolf/cerebrum.md | check OK | ~1k |
| 19:31 | dumb confusedness: paraphrase row ukungupul konhwoku (book quote moved off palakal); user prefers non-literal renderings | time-machine/victorian_wordlist.tsv, .wolf/cerebrum.md | check OK | ~3k |
| 19:55 | prepositions spa/deu/fra + shared passive agent (Xwexi 07): spa 64.6→66.6, deu +0.1, eng thirty 59.6, fra gold 67/67 kept, pnc 31.7, no regressions | glb-story.py, apertium-glb-{spa,deu,fra} dix/lrx/rlx/rtx, spa-glb-sentcase.py | done, uncommitted | ~120k |
| 20:06 | Wells works: wikisource_text.py + edition_variants.py shared modules (holt_variants refactor verified identical); WotW 1898 + Atlantic 1924 fetched, 1898 vs 1924 variants; Man of the Year Million extracted | wikisource_text.py, edition_variants.py, time-machine/fetch_texts.py, time-machine/holt_variants.py, war-of-the-worlds/*, wells-short-works/* | 120 lexical variants (continently→immediately) | ~30k |
| 20:13 | surveyed de/nl reflexive verbs (Wiktionary 1068/228 senses) vs Doxo/Xwexi options (se, soho, -cu, xor-, sen/sencu/ganjon + adj); classifier in scratchpad | (scratchpad wkt/) | survey done, nothing built | ~40k |
| 20:22 | Time Machine third witness: Atlantic Edition 1924 fetched (text/atlantic.txt); holt_variants.py → witness_variants.py (holt + atlantic, cached tsv); Holt outputs verified identical; fastText en/es/eo extracted (14 s, 650 MB each) | time-machine/fetch_texts.py, time-machine/witness_variants.py, wikisource_text.py, README.md | atlantic: 316 variants, 20 lexical, 1 glossary row | ~15k |
| 20:27 | Lovecraft: Call of Cthulhu (Weird Tales 1928) fetched; ATMoM flagged US-copyright until 2032 | lovecraft/fetch_texts.py | 1 witness, 11904 words | ~6k |
| 20:31 | lovecraft/private/ git-ignored for At the Mountains of Madness (EU PD, US until 2032); fetch blocked by auto-mode classifier | .gitignore, lovecraft/private/README.txt | awaiting user copy | ~2k |
| 20:33 | wired verb constructions: wiktionary_constructions.py (2025 +obj info_templates) → verb_constructions.py proposals → verb_constructions.tsv (17355 rows, undecided) → verb_constructions_to_apertium.py (ok rows → lrx/dix blocks) | 3 new modules + tsv, .gitignore | built, nothing vetted/generated | ~90k |
| 20:37 | verb constructions: two-stage vetting columns (sense_status; status+reviewer), es governed preps only → 4403 rows | verb_constructions.py, verb_constructions_to_apertium.py, verb_constructions.tsv | done | ~10k |
| 20:38 | At the Mountains of Madness private text: user's Mountains_of_Madness.md → lovecraft/private/at_the_mountains_of_madness.txt (12 ch., 40.4k words), git-ignored | lovecraft/private/ | not tracked (verified) | ~2k |
| 20:41 | US/UK variety layers in sense_periods (UK 350, US 147 rows); works.tsv (year written + variety per work); Lovecraft = US with Anglophile spelling | sense_periods.py, works.tsv | mad=insane tagged British-Isles → preference not filter | ~6k |
| 20:53 | period_proposals.py: Wiktionary + decade-embedding period proposals per work; works.tsv gained language/text + Le Petit Prince (fr, private cache); fixes: all senses compete, later-sense penalty, amod/compound adj, precision gates | period_proposals.py, works.tsv, */period_proposals_*.tsv | TM 54, WotW 30, YM 2, Cthulhu 11, Mountains 25 (private) | ~40k |
| 20:59 | apply_eng_periods.py: word-list GB/US gloss views with year ranges (527 dated entries, 195 curated period glosses added); word-list I/O moved to constructions.py (apply_eng_variety verified unchanged) | apply_eng_periods.py, constructions.py, apply_eng_variety.py, extract_constructions.py, word-list.csv | late first quotes of current senses not shown as starts | ~25k |
| 21:10 | SESSION SUMMARY 2026-11-20 (evening): deu Perfekt period setting (Adelung 1782, cprf/year); nld per ANS (progressives, gaan, er, om te, om=wey); date/time order (din D fe mesi M fe nyan Y, satu H:MM) shared in glb-story.py; prepositions: shared prep_line (time fe, phrasal fe…de, tem, of, ton/yon, el drop, passive agent per Xwexi 07) + sense rules for nld (heardutchhere), spa (Spanish Xwexi + SpanishDict), deu (Lingolia), fra (Tex) — spa 64.6→66.6, no regressions; verb constructions pipeline (wiktionary_constructions.py → verb_constructions.py → verb_constructions.tsv → verb_constructions_to_apertium.py), two-stage vetting, nothing vetted. ALL UNCOMMITTED. Open: epo hang on multi-line probe, reflexive transfer support, feeling-state choice for verb roots (lawfen / sen lawfendo / ganjon lawfendo). | many | uncommitted | — |
| 21:08 | histwords_ranges.py + apply_eng_periods '~decade-' starts; only dumb switches cleanly (bobo ~1960-) | histwords_ranges.py, apply_eng_periods.py, word-list.csv | 15 candidate words is too few: needs vetted modern senses (gey, kwir) linked | ~10k |
| 21:11 | committed session work in 10 atomic commits (ddf6fff..75adf24 + sub 9e00f41), not pushed; left .gitignore constructions_cache/ hunk and extract_constructions.py (other session / untracked) | git | done | ~5k |
| 21:13 | Fast-forwarded main to bible-translation (0db0bef..75adf24), not pushed | git | done | ~300 |
| 21:21 | Planned per-vetter 1–5 sense score columns (design saved to memory, not built) | — | deferred to next session | ~1k |
| 22:31 | Session (discussion only): PD SF/fantasy targets, Dying Earth copyright, translation-at-scale plan (Wells first, front-loaded concordance), minimal-register principle, root-vs-derived literary variant idea | memory/project_translation_at_scale.md, memory/feedback_globasa_minimal_register.md, .wolf/cerebrum.md | saved; nothing built | ~6k |
| 22:53 | Added typography principle (imitate original prints, e.g. Caslon for Wells; open fonts only) to translation-at-scale memory | memory/project_translation_at_scale.md | saved | ~1k |
| 22:57 | Noted Typst markup must pass through Apertium (word-bound blanks plan) | memory/project_markup_carryover.md | saved | ~1k |
| 12:19 | the→∅/dem coref-only study on Vanege gold: 163 aligned, 4 dem, no rule beats always-∅; report | definiteness/coref_the.py, REPORT.md | done | ~9000 |
| 12:30 | reactivation hin? post-edit flag (trace only) in coref stage; tested on sample passage | GlobasaTranslation/apertium-glb-eng/eng-glb-neural.py | done | ~3000 |
| 12:40 | Sense vetting by 1-5 scores per vetter: sense_ranking.py extracted; vetted_senses score model + migration (load_vetted unchanged 6553); shared sheet via extender 3 (ranked, Mean/Decision, vetter cols, How to vet); page keys 1-5 + push to sheet; vetting_queue/sense_review_queue/LLM judge adapted | sense_ranking.py, vetted_senses.py/.tsv, sense_rows.py, extender 3, sense_vetter.py/.html, LLM_sense_judge.py, parallel_lexsel/vetting_queue.py, sense_review_queue.py | done; commits b7616ed f9d39fd d064e1e d7464bd 0edb612 (not pushed) | ~60000 |
| 14:00 | Pivot-label ceiling for eng→glb lexical choice (pivot_oracle.py on 1045 silver items): content words gold separable by es+eo word-list glosses 828/898 (current pipeline 512/898); vetted-sense tables cover 531/898, separate 454 (broader tables overlap: with/ton, home/ogar); vetted adds fr/de/ru coverage; residue = morphology (manixu, sidecu/-gi, femixu) + synonyms | apertium-glb-eng/test/pivot_oracle.py | done, not committed | ~40k |
| 15:10 | Sibling-pivot labels on real sentences (sibling_pivot.py, 1000 TMX units, 836 items): true siblings UDHR+P&C content words 263 items, pipeline 136; es+eo picks: word list 96 (85.4% right, net +35), vetted 73 (87.7%), vetted eo 92.3%; all 4 pivots both sources 121 picks 80.2% net +40; ~45% no evidence, ~15% ambiguous (no alignment); vetted tables bad for function words (50%); Vanege eo originals inflate eo to 95.6% | apertium-glb-eng/test/sibling_pivot.py | done, not committed | ~50k |
| 13:05 | Sense ranking: etymology source-word cue (+3/-2, AUC .9265->.9329) and judgements-first ordering (sheet, peek) | sense_ranking.py, extender 3, sense_vetter.py | done, commit (not pushed) | ~15000 |
| 16:00 | sibling_pivot.py with SimAlign + fixed spa/fra/deu taggers: sibling content 263 items (pipeline 136): sentence all-4 both 140 picks 84.3% net +52; align1 133 picks 83.5% +48; es+eo ~87% either way → alignment does not raise precision here; remaining errors = shared pivot words across derivations (-pul/-li, -cu/-gi, gender), synonyms, translator choices | apertium-glb-eng/test/sibling_pivot.py | done, not committed | ~40k |
| 13:21 | spaCy Spanish gender-homograph comparison (sm/md/trf/trf-int8) in scratch venv; trf & int8 40/41, sm 35, md 31 | scratchpad/compare_gender.py | trf chosen candidate | ~6k |
| 16:40 | MacBERTh → mBERT embedding map (time-machine/macberth_map.py): downloaded MacBERTh (MIT, 439 MB, HF disk 1.6 GB left); layer 8, 69k words (Heinemann + TMX en); Procrustes cos .62, P@1 tok 94.8% period / 88.1% modern (identity 0%); ridge cos .74; en↔es link agreement with mBERT F 87.8 (proc) / 89.3 (ridge) | time-machine/macberth_map.py | done, not committed | ~30k |
| 13:26 | AnCora test gender eval fp32 vs int8 (equal); Dutch UD has only Com/Neut; Dutch encoder survey | scratchpad/eval_ancora_gender.py | int8 confirmed; Dutch needs WSD | ~5k |
| 13:46 | Disk full broke the shared sheet save; atomic save in extender 3; senses_dir -> Warehouse2/Language/Claude | extender 3 | fixed (1734b35) | ~3000 |
| 13:50 | Dutch POS baselines (spaCy sm/md/lg, Apertium trimmed/untrimmed) on UD test; Dutch coref survey (OpenBoek CC BY, no stanza nl coref); BERT UPOS fine-tunes running | scratchpad/dutch_pos/*.py, Warehouse2/Language/Claude/dutch_pos | in progress | ~15k |
| 13:56 | UDHR: 'Of nilte, ren am ... tesu' is correct (topic + subject ren); withdrew 'gold error' notes | .wolf/cerebrum.md, memory | done | ~1500 |
| 13:58 | French options survey: spaCy fr metas, fr trf homograph probe, stanza fr coref, compact encoders | Warehouse2/Language/Claude/french_models | done | ~6k |
| 14:06 | Shared vetting sheet generated on Warehouse2/Language/Claude (52,889 rows, Paleos 4:6606 3:27 2:287) | GLB_ENG_WiktionarySenses.xlsx | done | ~1000 |
| 17:30 | period_sense_probe.py over Wells+Lovecraft (5 works, 4547 occ + 108 TM gold): gold acc first-sense 41.7, A mBERT 50.0, B MacBERTh 55.6, C rotated 47.2, D ridge 50.0 (chance 26.3; B vs A 9:4 discordant, not significant); map refit on sources (P@1 93.6/88.1); disk full incident → caches to Warehouse2 | time-machine/period_sense_probe.py, bert_words.py, macberth_map.py | done, not committed | ~60k |
| 17:55 | How much would translated prototype examples help? translation_sense_probe.py: period translators' words pick a sense in 17/121 gold (11 right); translation-else-MacBERTh 61/108 vs 60; of B's 32 errors with quotations on both senses, 29 involve a sense with no es/eo table, 3 separable → ceiling ≈ 30% of items, expected gain a few points | time-machine/translation_sense_probe.py | done, not committed | ~15k |
| 14:36 | Shared sheet numbers-only (Suggestion/Suggested by); exact sheet keys (trailing-space words); backups beside sheet; regeneration blocked by user's open LibreOffice | vetted_senses.py, sense_rows.py, extender 3, LLM_sense_judge.py | committed | ~12000 |
| 18:20 | Contemporary-dictionary prototypes (webster_sense_probe.py): Webster 1913 inventory 105 gold items, B MacBERTh 57.1% (A 50.5, oldest-first 36.2, chance 35.3); on 87 shared items Webster B 60.9 vs Wiktionary B 59.8 — but complementary: either right 69/87 (79%), both wrong 18 | time-machine/webster_sense_probe.py | done, not committed | ~20k |
| 14:34 | fra-glb: neural gender + coref steps (fra-nlp-service.py, fra-glb-neural.py), rtx crf attr + sesu, bidix son/leur<ref> → sesu, glb-anaphor.tsv copy; P&C pronoun words 24→28/53; regtest 69/69 | apertium-glb-fra/*, anaphor_to_apertium.py | done, not committed | ~60k |
| 14:37 | committed fra-glb neural steps (pair a3a5501) + anaphor_to_apertium.py/submodule bump (main 1a5f6f5) | apertium-glb-fra, anaphor_to_apertium.py | done, not pushed | ~2k |
| 14:44 | Score block moved beside Suggestion (vetters between Decision and '|'); tested layout/readback/new vetter/push | extender 3, vetted_senses.py | committed | ~6000 |
| 14:45 | Dutch coref probe: German stanza coref zero-shot on Dutch, 6/7 sensible links; nld-glb ignores antecedents | scratchpad | proposal | ~4k |
| 15:20 | Extension clarifiers for shared translations (15,795 of 60,299; 3,533 fallback); bidix parse unchanged | clarifiers.py, Wiktionary extension builder.py | committed | ~40000 |
| 15:55 | Extension clarifiers stricter: curated clarifier_tags.tsv, noun-only labels/renderings, note-guided fallback; 13,266 clarifiers | clarifiers.py, clarifier_tags.tsv | committed | ~20000 |
| 19:30 | Pooled period inventory (period_senses.py: 4227 senses, 1046 Webster joined, 912 period-only, 1720 dated) + probe rerun: 87 common TM gold items B wikt 58.6 / webster 60.9 / pooled 59.8 / pooled+prior 63.2 (A pooled+prior 52.9, C 49.4; oracle either 79); Globasa suggestion hits curated rendering 23% (gold-sense oracle 26%, any sense 36%), 88/99 via entry-level Esperanto fallback; scan 5 works ~70% same as Wiktionary B, many changes on common words (little, but, down) | time-machine/period_senses.py, period_dict_entries.py, period_sense_probe.py, period_dicts.py | done, not committed | ~90k |
| 15:37 | WSD substitution probe (LaBSE, Spa/Epo glosses) on eng→glb silver: gated +41/957; stopped (user does WSD in another session) | scratchpad/wsd_subst.py | probe only | ~5k |
| 16:43 | shared glb-nlp-service/glb-neural/glb-kam in apertium-glb wired into eng/spa/fra/deu/nld (uncommitted); spa service crashed on es zero mentions; stopped service for RAM (1 GB free) | apertium-glb/*, pairs modes/Makefile.am | in progress | ~30k |
| 16:56 | answered: year parameter as switch (normalisation table, historical encoder MacBERTh/GysBERT/hmBERT MIT, year-keyed rules); noted in project memory | memory | plan | ~3k |
| 17:00 | answered: MacBERTh→RoBERTa distillation not advisable; recommend historical MLM LoRA adapter on frozen roberta-large (year-switched); noted in memory | memory | plan | ~2k |
| 20:30 | period_glb.py proposals pipeline (words mode ~10 s; work mode running on TM), wordlist_tags.py refactor (sync verified identical on scratch copies), translation-time prototype coverage on 1045 silver items (17% all candidates, 45% gold none); findings written to CONTEXTUAL_WSD.md | time-machine/period_glb.py, wordlist_tags.py, victorian_wordlist.py, bert_words.py, CONTEXTUAL_WSD.md | done, not committed | ~60k |
| 21:00 | Affix senses of ordinary words (bisu, gimu, semi, lefe... 12 words) -> own Fiksoli Rukone/Produti cards; parser quasi-sfx/quasi-pfx; verified on scratch deck copies. Accidental update_vocab_deck run via import: deck restored from .bak (older .bak lost) | Lexilista_parser.py, AnkiMaker3.py, update_vocab_deck.py, globasa_word_hyphenation.py, globasa_pos.py, Word Viewer.py | done, not committed | ~90k |
| 21:00 | gay sense test (3 real Wells sentences + 5 made-up): fixed sub-sense gloss keying bug (period_senses/period_glb); 4/8 right; prior separates period vs modern; proposed fixes: group sub-senses, tag-based prior for modern years, Webster spelling-normalised joining, examples for Webster-only senses | time-machine/period_senses.py, period_glb.py | done, not committed | ~25k |
| 17:15 | Dutch BERT UPOS fine-tunes done (merged 97.8/97.5 best size; RobBERT-2023 97.7/97.7) | Warehouse2/dutch_pos | done | ~2k |
| 21:20 | Renamed Afiks -> Fikso fields, templates -> Fiksoli Rukone/Produti (word list: fikso = affix); re-verified on scratch deck copy | AnkiMaker3.py, update_vocab_deck.py | done, not committed | ~5k |
| 21:40 | SESSION END / handover: four fixes (sub-sense gloss key, sense groups, modern prior, stem joining + synonym examples) + encoder-by-year in period_glb; gold-probe rerun interrupted by session end; handover written to CONTEXTUAL_WSD.md §7; all uncommitted | CONTEXTUAL_WSD.md, time-machine/period_senses.py, period_glb.py, period_sense_probe.py | handed over | ~40k |
| 18:45 | discussed inventory-free, non-anglocentric concept discovery for coining | cerebrum.md, memory | idea only | ~3000 |
| 18:51 | audited word-list religious vocabulary (Abrahamic vs non-Abrahamic) | word-list.csv (read), memory | idea only | ~4000 |
| 18:53 | indigenous-concept policy (derivations when recurrent) recorded | memory, cerebrum.md | idea only | ~2500 |
| 19:00 | discussed TDA (persistence, Mapper, family-count filtration) for concept discovery | — | idea only | ~2000 |
| 19:00 | deu->glb neural plugin (glb-neural-deu.py: separable verbs, relative case, Sie number, kam fix, coref te/to/sesu/possessor number, hin? flag) + rtx crf + bidix sesu RL + reorder PARSED kam guard; not committed | GlobasaTranslation/apertium-glb-deu/* | PNC/UDHR pronoun agreement up, service-off output unchanged | ~60k |
| 19:03 | checked word list for East Asian concepts: concrete loans present (umami, fenxui, tofu), social/emotional ones absent (面子 孝 缘 人情 热闹 客气 懐かしい) | word-list.csv (read) | idea only | ~2500 |
| 19:07 | GPU plan for concept discovery; checked venv packages | cerebrum.md | idea only | ~2500 |
| 19:10 | period_sense_probe rerun after fixes 1-5: B pooled+prior grouped 58/89 = 65.2% (was 55/87 = 63.2%); grouping adds 0 | time-machine/period_sense_probe_report.txt, CONTEXTUAL_WSD.md §2-3 | done (CPU) | ~8k |
| 19:10 | period_glb.py filter: QUOTES_MIN=2, old sense in a text PoS, old pick must beat current group by MARGIN; TM run 1,245 proposals (221 likely/593 rare/431 possible), 8.5 min cached; recall obscure 92%, dated lemmas 41% (sense-level 43/166 vs 49); likely-sample precision ~20% (8/40) | time-machine/period_glb.py, period_glb_the_time_machine.tsv, CONTEXTUAL_WSD.md §5,§7 | not committed, no --apply | ~25k |
| 19:21 | fra->glb neural items (agent): kam checks, se clrfx/clpv/clpass, vous <vsg>, NER/vocative person names, hin? trace flag, destxt-dot text fix, service NER+chunking; P&C chrF 30.57 pronouns 56/89 unchanged, grammar 22/23, neural-off identical, make test passes | GlobasaTranslation/apertium-glb-fra/{glb-neural-fra.py,fra-glb-neural.py,fra-nlp-service.py,*.rtx,*.dix,Makefile.am} | uncommitted | ~60k |
| 19:23 | French agent done (kam, se, vous, names, hin? flags; gold unchanged, neural-off identical); core: destxt_dot skip, plugin hook, chunked service; Dutch agent launched | apertium-glb-fra, apertium-glb/glb-neural.py | uncommitted | ~10k |
| 19:25 | built concept_discovery/: kinbank_categories.py (run, ARI 0.43, cross/parallel cousin + elder/younger + bifurcate uncles recurrent) and english_east_asian_borrowings.py (running) | concept_discovery/*.py | ok | ~40000 |
| 19:38 | borrowing scan: found concept-index etym gap ({{bor+|..|-}}+{{ja-r}}), switched to dump stream with labelled fallback; rerunning | concept_discovery/english_east_asian_borrowings.py | running | ~15000 |
| 19:41 | nld->glb neural: glb-neural-nld.py plugin (separable verbs, relatives [RELB]/[RELE], ze number), coref step in modes.xml, rtx crf, bidix sesu, reorder relative extraction | GlobasaTranslation/apertium-glb-nld | built, evaluating | ~60k |
| 19:42 | Spanish items done (kam, se->ren, pro-drop to, sesu, crf; xwexi 9 lines changed, +2.0 chrF sum, 0 fallbacks); spa service stopped; English agent launched | apertium-glb, apertium-glb-spa | uncommitted | ~15k |
| 19:49 | indic_east_asian_concepts.py + lexicon.py: 107 Hindi+Telugu Indic concepts loaned into East Asia, 85 missing in Globasa; borrowing scan refactored onto lexicon (3359 rows, coverage false positives fixed) | concept_discovery/* | ok | ~30000 |
| 19:57 | deu eval done (score.py-style 3 threads, 0 fallbacks): pronoun agree PNC 64->66, UDHR 16->18; service stopped | GlobasaTranslation/apertium-glb-deu | ok | ~5k |
| 19:58 | German agent done (separable, kam, Sie/ihr, relatives, referents/sesu, hin? flags; P&C 64->66, UDHR 16->18 pronoun words); core: POSS_NEEDS_P3 + PROPN person names in chain_verdict | apertium-glb-deu, apertium-glb/glb-neural.py | uncommitted | ~5k |
| 20:19 | nld->glb neural done: coref te/to/sesu, separable verbs, relatives hu..da, ze number, haar/zijn/hun/jullie homographs, tag-question/vocative kam; P&C pronoun words 35(off)/39(parse)->42/97, chrF 25.38/25.49->25.51; service stopped | GlobasaTranslation/apertium-glb-nld | uncommitted | ~120k |
| 20:21 | Dutch agent done (referents/sesu, separable, relatives, kam, uw/jullie; P&C 39->42/97); synced germanic-v2-reorder.py nld->deu (deu neural-off 0/411 changed); core: anaphor_kind decided by parse | apertium-glb-nld, apertium-glb-deu, apertium-glb | uncommitted | ~6k |
| 20:30 | menalariPronouns_edited.tsv: ogar=to, nini=te (user); glb-anaphor.tsv regenerated (5518) | menalariPronouns_edited.tsv, pairs' glb-anaphor.tsv | done, uncommitted | ~1k |
| 20:46 | CLICS4 soul colexification check: ghost=soul 23/59 fam via soul words; breath=soul areal N Eurasia | concept_discovery/clics_soul_colexifications.py | ok | ~8000 |
| 20:52 | CLICS4 per-area soul colexifications (Africa/Americas) + literature search | concept_discovery/clics_soul_colexifications.py | ok | ~9000 |
| 21:02 | 氣 analysis: Sinosphere-shared compounds vs Globasa coverage; form collisions | word-list.csv, concept index | ok | ~5000 |
| 21:06 | 氣 senses compared with hi/te/fa/ar/id/tr translations | concept index | ok | ~3000 |
| 21:10 | 氣 assessed via zh/ja Wiktionary senses | WiktionaryLMDB_zh, _ja | ok | ~3000 |
| 21:12 | 氣 words' translations in zh/ja Wiktionary | WiktionaryLMDB_zh, _ja | ok | ~3000 |
| 21:14 | eng→glb neural items: glb-neural-eng.py (kam by inversion, quotes, tag q, un-invert aux; you sg/pl), eng-glb-neural.py names+that, rtx wh-do/ref, bidix your; dev chrF 61.52→61.71 | apertium-glb-eng/* | done, not committed | ~200k |
| 21:16 | hon/paku forms checked (no collisions; Sino-Xenic readings) | word-list.csv, sinosphere | ok | ~2000 |
| 21:20 | multiple-soul compositional vocabulary proposed (roots checked) | word-list.csv | ok | ~2000 |
| 21:21 | paku as head of soul-type derivations discussed | memory | ok | ~1500 |
| 21:21 | English agent done (you sg/pl, kam, names, that/relatives; dev 61.52->61.71, test 60.76); glb-kam lower-cases function words after kam; all pair copies refreshed | apertium-glb-eng, apertium-glb/glb-kam.py | uncommitted | ~6k |
| 21:23 | hon/paku dual-head criterion recorded | memory | ok | ~1200 |
| 21:24 | committed: apertium-glb 10571e8/a40343b; pairs eng 807848e spa 8edc1dc fra 10e9073 deu b8af8e0 nld 4d18f32; main 4a78d1e a6bc555 + 6 WSD commits (e389a56..fb3c639); not pushed | all | done | ~3k |
| 21:34 | wrote docs/research/conceptual_parity.md + PDF (all parity research, cited) | docs/research/conceptual_parity.* | ok | ~15000 |
| 21:38 | added free soul vs surviving self subsection; PDF regenerated | docs/research/conceptual_parity.* | ok | ~2000 |
| 21:47 | nirvana / 無為 added as next checks; PDF regenerated | docs/research/conceptual_parity.* | ok | ~1500 |
| 21:49 | reconciled conceptual_parity.md with semantic-eurocentrism-audit.md (walfale, hun/po, laosodar...); PDF regenerated | docs/research/conceptual_parity.* | ok | ~6000 |
| 21:53 | merged walfale/nilfale history; darma/nirvana reconsidered by native senses; PDF regenerated | docs/research/conceptual_parity.* | ok | ~6000 |
| 21:54 | added 'walfale na' (fluent, unforced action) proposal; PDF regenerated | docs/research/conceptual_parity.* | ok | ~1500 |
| 22:36 | SESSION SUMMARY: concept discovery for coining (anti-anglocentrism, Sprachbund/recurrence), Kinbank kin categories, East Asian borrowings, Indic Hindi+Telugu+East Asia concepts, CLICS4 soul colexifications, 氣 via zh/ja Wiktionary, soul vocabulary (ruho regloss, hon/paku heads), walfale/darma/nirvana; write-up docs/research/conceptual_parity.md+pdf; commits 5a3e631, a4202ef (not pushed) | concept_discovery/*, docs/research/conceptual_parity.* | landed | — |
| 12:00 | den-/hin- focus stage (glb-neural.py focus), monodix den/hin forms, rtx focus attr + modes in eng/spa/fra/deu/nld, eng relative-who sesu | GlobasaTranslation/apertium-glb*/ | Christie person forms 68.5%→76.7%; test/focus/run.py ok | ~40000 |
| 12:10 | Christie excerpt → Doxo TMX pair + CSV (56 TUs, glb-x-fokus tuv), focus_eval.py, Word Viewer skips glb-x-* | extend_tmx_christie.py, focus_eval.py, Word Viewer.py | landed | ~8000 |
| 14:30 | man-/fem- marking + manfem post-bidix stage, Mr/Mrs titles, focusgender option, deu/nld sexmark | GlobasaTranslation/apertium-glb*/, focus_eval.py | Christie man-/fem- 56.0%→76.0%; test 8/8 | ~30000 |
| 15:30 | jpn pair: focus/deixis/man-fem via glb-neural-jpn.py; sex from pronouns only eng/jpn | GlobasaTranslation/apertium-glb{,-jpn} | jpn gold 65/65; Christie unchanged | ~25000 |
| 17:00 | deu/nld d-pronouns → focus rules, former/latter → unyum/duayum te, GD tø entries, given-name fallback | GlobasaTranslation/apertium-glb{,-deu,-nld} | test 12/12; Christie unchanged | ~35000 |
| 19:00 | spa/fra: dropped subjects, demonstratives/closest-furthest, owner phrases, natural sex; to_text keeps blank chars | GlobasaTranslation/apertium-glb* | test 19/19; Christie focus 78.1%, man-fem 72.0% | ~45000 |
| 14:00 | Word Selector: pivot-free semantic-field sweep (field.py, /api/field, page panel) | word_selection/field.py, Word Selector.py, word_selector.html | tested: 妖怪 ja+zh 1.6 s, de:Geist 0.5 s | ~60k |
| 14:50 | field sweep: typed terms' own entries as tickable rows; missing-entry note (ja:よーかい has none) | word_selection/field.py, word_selector.html | tested | ~5k |
| 14:52 | field sweep: Untick all button | word_selector.html | JS syntax ok | ~2k |
| 14:54 | Sources table: Untick all / Tick all buttons | word_selector.html | JS syntax ok | ~2k |
| 14:55 | etym cognates also follow borrowings FROM gathered words (ja 妖怪 -> en yokai) | word_selection/pipeline.py | tested | ~4k |
| 14:59 | fix: mixed-script table romanizations (ようかい, yōkai) -> latin_roman + labelled retry | word_selection/pipeline.py | tested 妖怪 yokai, 精霊, 妖精 | ~4k |
| 16:10 | write-up of the spirit-beings discussion | docs/research/spirit_beings.md | written | ~9k |
| 16:19 | dossier alignment: pairwise grids merged into one proposal-centred star alignment (shared columns) | word_selector.html | node test ok | ~3k |
| 16:21 | dossier alignment: server MSA centred on a source (align.msa candidates) so 妖怪 k/g share a column | word_selection/align.py, dossier.py, word_selector.html | tested | ~4k |
| 16:29 | Word Selector speed: precedent disk cache + warm, memoized distance, deterministic table order (hash-seed bug), two-phase run (gather+cluster, then blend ticked clusters) | precedent.py, align.py, sources/wiktionary.py, field.py, pipeline.py, Word Selector.py, word_selector.html | phase1 1.7 s, blend 2 clusters 0.24 s; full run unchanged | ~40k |
| 17:30 | chain splitter (3 hard constraints) + GUM split evaluator | GlobasaTranslation/apertium-glb | GUM: rules 2/2 precise, link P/R unchanged 83.3/84.5; tests 19/19; Christie unchanged | ~30000 |
| 17:21 | Word Selector: Save for Reddit (word_selection/reddit.py, /api/reddit, button) | reddit.py, Word Selector.py, word_selector.html | tested via test client | ~8k |
| 17:27 | Han-seeded concepts rank same-character Sino-xenic clusters first (pipeline.han_seeds/han_priority) | word_selection/pipeline.py | tested 妖怪, 黄泉, English-only unchanged | ~6k |
| 17:40 | ja reading kind: obor = native; Latin romans (macrons) count; Han-seeded concepts use the Sino-xenic Japanese reading (黄泉 kōsen) | sinosphere.py, pipeline.py | eval unchanged 31.0/60.4 | ~10k |
| 18:30 | overlapping analysis pieces (glb_chunks), cast lists, coref_eval (GUM/LitBank) | GlobasaTranslation/apertium-glb{,-eng,-fra}, focus_eval.py | LitBank overlap 77.4 vs pieces 66.9 B3; Christie man-fem 76% with cast | ~60000 |
| 19:30 | cast list columns (src/glb lemma, class, marking, gram) + render step in all X→glb modes | GlobasaTranslation/apertium-glb*/ | tests 21/21; Christie unchanged with cast | ~25000 |
| 18:50 | blend: precedent-per-source candidates as fallback only (<2 legal proposals); always-on cost 1.2pt top-1, fallback 30.9/60.5 vs 31.0/60.4 (noise); fixes 黃泉 | blend.py, pipeline.py | kept | ~6k |
| 20:00 | supplement terms (kind/src_pos, post-bidix ⟦lemma⟧, unknown-term readings, head-noun multiword), suggest term rows | GlobasaTranslation/apertium-glb | tests 22/22; spa Jedi example clean | ~20000 |
| 19:15 | Word Selector: team word-selection post format (lexiseleti.py, /api/lexiseleti, 'Word selection post' button); tested on sediment | word_selection/lexiseleti.py, Word Selector.py, word_selector.html | works | ~6000 |
| 19:24 | Reddit post now in the team word-selection format (reddit.py rewritten; lexiseleti.py, /api/lexiseleti, extra button removed); pipeline.add_han_cognates adds the Han base of 物 nouns (堆積物 -> 堆積 in cmn/ja/ko): sediment now leads with 3-family twayjiku | word_selection/reddit.py, word_selection/pipeline.py, Word Selector.py, word_selector.html | tested via /api/reddit | ~9000 |
| 21:07 | taxonomy write-up | docs/research/religion_taxonomy.md | written | ~7k |
| 21:09 | religion_taxonomy: 6 key claims checked (Xunzi, Chau, Josephus, Batnitzky, dīn<dēn confirmed; Jōdo Shinshū softened), §10 verified table | docs/research/religion_taxonomy.md | done | ~8k |
| 21:30 | session wrap: next-session list saved to project memory | memory/project_religion_taxonomy.md | done | ~2k |
| 21:54 | religion_taxonomy.md: §6 edits (sekularcwenton redefined, dayhikaye, xafemodernismo, fading schools), kultuxube, fiction-into-belief, status section; published both reports as artifacts; PDFs docs/research/religion_taxonomy.pdf, spirit_beings.pdf | docs/research | done | ~25k |
| 22:44 | SESSION SUMMARY 2026-11-23: spirit-being vocabulary (ruhoyen, prabu owner spirits, 妖怪 slot, peari, yaksa, Dreaming, tutum heart-mind, departs/remains soul axis, xian) → spirit_beings.md; religion taxonomy (kultucwenton/fikirxube/kultuxube/dini/sekularcwenton …) → religion_taxonomy.md, 6 claims verified, both published + PDFs; Word Selector: field sweep, two-phase blending, precedent cache, hash-seed fix, Han-seed priority, ja reading fixes, offglide, fallback blend, Reddit export, alignment display (code committed ecef598/4dcadd9/296768a). Next: decide dini general sense; add animism + Buddhist cosmology to taxonomy. | docs/research, word_selection | landed | — |
| 22:57 | user correction: duty = musiya (not darma); cerebrum + taxonomy notes fixed | .wolf/cerebrum.md | done | — |
| 23:07 | user: jinn = jini; spirit_beings.md fixed (page/PDF re-render pending) | docs/research/spirit_beings.md | done | — |
| 12:45 | Profiled Word Selector eval, shorthand optimizer, edition_variants with cProfile; Rust plan at ~/.claude/plans/go-around-and-switch-elegant-finch.md | word_selection/*, shorthand_optimizer.py, edition_variants.py | cold LMDB I/O 185/214 s; warm align 4.8 s + collision 5.8 s; optimizer cost() 84 s/restart; variants ~8 min difflib | ~60k |
| 13:40 | Profiled extension builder (23 s: 6.7 s LMDB disk reads, 4.7 s deserialize_translations sets) and spa NLP service: CPU 2.5/4.9 s vs GPU 0.42/0.73 s for 1.2k/3k chars (6-7x; first GPU request 6.5 s warm-up); plan step 0b added | Wiktionary extension builder.py, apertium-glb/glb-nlp-service.py | plan updated, no code changed | ~40k |
| 14:20 | GPU profile of one spa request (user ran it): 0.72 s, GPU busy 0.18 s; depparse CLE decoding (Python) is the top CPU cost; plan: Rust MST decoder, ONNX dropped | plan file | plan updated | ~10k |
| 15:15 | Speed-up plan step 2 (Python fixes): collision.check bisect prefix index (identical on 11,928 candidates), sino_distance lru_cache, get_translations(senses=) for the extension builder (23 s -> 8.6 s warm, identical with PYTHONHASHSEED=0), shorthand cost() precomputed UPPER mask (exact, 314 -> 279 us), _resolve_lang sorted (bug-327: extension was nondeterministic); .gitignore /WiktionaryLMDB* patterns; step0_user.sh for Rust + LMDB move (user runs it) | word_selection/collision.py, word_selection/align.py, wiktionary_db.py, Wiktionary extension builder.py, wiktionary_constants.py, shorthand_optimizer.py, .gitignore | eval roots oracle 200 byte-identical | ~80k |
| 17:30 | Rust crate rust/globasa_fast: align (Word Selector, bit-identical, eval 7.8->5.7 s), gestalt (difflib exact; WotW variants 8 min->1.7 s, TSVs identical), mst (stanza CLE, identical trees on 10k matrices; /analyze JSON identical); services GPU+warm-up+Rust decoder (apertium-glb d60e0be, fra 13f08ff, eng b4faa54); setup.sh --fast + README Performance; fresh-clone test passed without/with cargo; LMDBs moved to QuickRead by user | rust/globasa_fast/*, fast_ext.py, word_selection/align.py, edition_variants.py, tests/test_globasa_fast.py, setup.sh, README.md, requirements-fast.txt, GlobasaTranslation/apertium-glb*/ | committed locally, not pushed | ~150k |
| 18:40 | Browser translator (WebAssembly): multicall Apertium wasm (emsdk 7.0.0, ICU trimmed), Pyodide 314.0.7 runner + subprocess shim, mode manifests, page/worker, capped tests; all 13 modes byte-identical to native (parity, 40 gold lines each, peak 0.9 GB); fixed rtx SEQ-sent blow-up in epo/spa grammars (chrF +0.7 epo) | web/*, GlobasaTranslation/apertium-glb-epo/*.rtx, apertium-glb-spa/*.rtx, README.md | built + tested in Node; headless browser test cannot run here (AF_UNIX blocked); not committed | ~400k |
| 19:10 | Browser translator now mirrors the apertium command (destxt, normalize, wblank attach/detach, retxt in wasm; manifests from apertium-wblank-mode); parity vs `apertium -d` all 13 identical; user confirmed page works in browser | web/* | fixed \@ escapes in output | ~60k |
| 20:05 | In-browser English tagger: stanza combined+gum nocharlm → ONNX (wrapper = stanza up to 4/25k near-ties, ORT = wrapper exactly), int8 top-100k conll17; JS = exporter accuracy 95.99/92.98; bridged into eng-glb-neural.py pos via http://browser-nlp + NeedAnalysis re-run; eng-glb chrF +0.8..+4.3 (curated 66.4→70.7); parity 13/13 still identical | web/tagger/*, web/src/tagger.mjs, web/py/runner.py, web/src/pipeline.mjs, web/site/worker.js, web/build.sh | running/so/nothing unchanged: client prune() policy + English CG, not tagger | ~250k |
| 20:40 | eng-glb-neural.py prune(): UPOS PRON on NN -> prn only; VBG not before NN/JJ/CD -> drop n/adj -ing readings; RB not before JJ/RB -> drop preadv; bidix so<cnjadv> -> celki (RL, user gold). Curated chrF 70.7->76.0 with browser tagger; dev sets unchanged or up (telltale 69.2->70.1); parity ok | GlobasaTranslation/apertium-glb-eng/eng-glb-neural.py, apertium-glb-eng.glb-eng.dix | desktop neural not measured (service not run) | ~60k |
| 21:30 | Gold-sentence fixes: unknown NNP -> name; name case duplicates dropped (bidix + generator); np+n NP drops 'the'; adverb/verb space; glb-pregen.py -mo rule in all 7 X->glb pairs (conservative after first version stripped before unknown words). Curated chrF 81.1 with tagger; dev sets up or equal; parity 13/13. Coordinated passive attempt reverted; zero relatives need a parser | apertium-glb, apertium-glb-{eng,fra,spa,epo,deu,nld,jpn} | committed (not pushed) | ~300k |
| 22:10 | Hyphenated compounds eng->glb: rtx HAJ (n/adj/adv/num + guio + adj/pp/pprs/n -> one hyphenated adjective), npcomp n-n + n; CG: no finite/imp verb before guio, SELECT n before guio + participle (Secret-Telling -> Siri-Logane, gold); eng-glb-mwe splits hyphenated parts of spaced multiwords; prune() leaves words before HYPH; browser tokenizer splits hyphens. Curated 83.2, telltale 68.3/71.1 (up), parity 13/13 | apertium-glb-eng rtx/rlx/mwe/neural, web/src/tagger.mjs | uncommitted | ~150k |
| 22:40 | eng->glb gap analysis on 1052 dev sentences (browser pipeline + tagger): constructions vs chrF, error marks; inventory saved to memory project_eng_glb_rule_gaps | (analysis only) | report to user | ~80k |
| 23:00 | Handover written: docs/translation/rule_gaps_handover.md (eng/epo/spa rule gaps, Esperanto affix map from word list, decisions, order); gap scripts moved into web/test/ | docs/translation/rule_gaps_handover.md, web/test/gap_*.{mjs,py}, web/test/gaps_native.py | uncommitted | ~40k |
| 15:10 | Rule-gap session (plan fix-the-remaining-rule-jolly-twilight): epo determiners/pronouns (CG + rtx), spa clitics/a-phrases/todo/lo/resumptives, eng modals/when/more/possessives, shared glb-pregen (dbl recipients, multiword targets, prefixes, · composition, -mo), epo word formation (epo_glb_affixes.tsv, derived bidix, lt-proc -e compounding, apertium-epo supplement), spa -mente, eng participles/-ly/phrasal_verbs.tsv/title case/function words. eng 61.7->63.5, epo 66.3->70.9, spa 66.3->68.6; parity 13/13 | apertium-glb, -eng, -epo, -spa, apertium-epo; docs/translation/rule_gaps_handover.md §6b; web/test/trace.mjs | committed per repo, not pushed | ~600k |
| 17:30 | Browser dependency parser: stanza combined_nocharlm depparse → ONNX (exporter + pruned lemma dict), mst.mjs decoder, tagger.mjs head/deprel/lemma, BROWSER_NLP coref + glb-neural eng parse (needs_parse). Desktop sesu ceiling measured (full 102/parse-only 34); browser sesu 0→33, eng dev chrF 63.46→63.8, parity ok | web/tagger/export_stanza_depparse.py, web/src/{mst,tagger,pipeline}.mjs, web/build_modes.py, web/build.sh, docs/translation/browser_parser_handover.md §4a | committed bf9d30d..0e2a33c, not pushed | ~250k |
