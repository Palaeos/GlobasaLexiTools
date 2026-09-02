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

