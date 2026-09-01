# anatomy.md

> Auto-maintained by OpenWolf. Last scanned: 2026-06-08T16:30:08.993Z
> Files: 186 tracked | Anatomy hits: 0 | Misses: 0

## ../../

- `.claude.json` — Declares breakdown (~8814 tok)

## ../../../../tmp/

- `eng_tests.txt` (~90 tok)
- `glb_tests.txt` (~265 tok)

## ../../../../tmp/anymalign/

- `anymalign.py` — -*- coding: utf-8 -*- (~17706 tok)

## ../../.claude/

- `settings.json` (~82 tok)

## ../../.claude/plans/

- `abundant-whistling-platypus.md` — Plan: Non-English Wiktionary Support (Curated Interactive) (~2541 tok)
- `atomic-squishing-allen.md` — Plan: Wiktionary Sense-Based Translation Extender v3 (~2605 tok)
- `floating-giggling-toucan.md` — Plan: Alignment Viewer + Translation Aide Pages (~2104 tok)
- `gleaming-cuddling-fountain.md` — Plan: Update `dictionaryPreprocess.py` to use `Lexilista_parser` (~2561 tok)
- `gold-alignment-annotation.md` — Plan: Manual Gold Alignment Annotation in Word Viewer (~2019 tok)
- `hidden-mapping-hanrahan.md` — Plan: Globasa POS Tagger (CG + Python) (~2076 tok)
- `humming-enchanting-valiant.md` — Plan: Improve Lexilista_parser.py for New PoS Annotations (~4763 tok)
- `i-wish-to-develop-idempotent-gizmo.md` — Plan: Globasa Morphology-Aware Tokenizer (~16666 tok)
- `improve-the-latest-anki-synthetic-cook.md` — Plan: AnkiMaker3 — course-weighted ranking, proper verb-type fields, apkg image sync (~4565 tok)
- `mossy-rolling-hoare.md` — Plan: Improve GIZA++ Alignment Accuracy (~4088 tok)
- `noble-stirring-planet.md` — RTL Layout Refinement for Word Viewer (~2343 tok)

## ../../.claude/projects/-home-paleos-PycharmProjects-GlobasaLexiTools/memory/

- `feedback_atomic_commits.md` (~190 tok)
- `feedback_conservative_script_tiers.md` (~266 tok)
- `MEMORY.md` (~64 tok)

## ../../ApplicationSource/GlobasaTranslation/apertium-glb-eng/

- `apertium-glb-eng.eng-glb.rtx` (~2723 tok)
- `apertium-glb-eng.glb-eng.dix` (~388349 tok)
- `apertium-glb-eng.glb-eng.rtx` (~3409 tok)

## ../../ApplicationSource/GlobasaTranslation/apertium-glb/

- `apertium-glb.glb.dix` (~430090 tok)
- `apertium-glb.glb.rlx` — Globasa Constraint Grammar for POS disambiguation (~2527 tok)

## ./

- `_update_i18n.py` — One-shot script to fill empty cells in word_viewer_i18n.csv with DeepL translations. (~12328 tok)
- `alignment_viewer.html` — Globasa Alignment Viewer (~6391 tok)
- `AnkiMaker2.py` — AnkiFields: reset (~2659 tok)
- `AnkiMaker3.py` — AnkiFields: reset (~6234 tok)
- `annotate_alignments.html` — Globasa Gold Alignment Annotator (~13876 tok)
- `apkg_image_sync.py` — Pulls image links out of Globasa__Vocabulary.apkg into menalariImages.jsonl. Resolves Anki field ordinals BY NAME from the deck's `fields` table (they drifted once already); maps Imajelinku->PoS group 1, DuayumImaje->PoS group 2, Faleanimalinku->animation (~2600 tok)
- `course_ranker.py` — Power-law scoring constants — tune to taste. (~2561 tok)
- `dictionaryPreprocess.py` — ── PoS → Apertium symbol ──────────────────────────────────────────────── (~4993 tok)
- `Doxo_passages_edited_updated.csv` (~68050 tok)
- `extend_tmx_pnc_multi.py` — parse_transcript, find_transcript (~1813 tok)
- `extend_tmx_udhr_multi.py` — Extends TMX with UDHR in 10 languages from Unicode CLDR XMLs; auto sentence splitting (~2000 tok)
- `extend_tmx_udhr.py` — parse_udhr_xml, split_at_sentence, split_by_markers, build_udhr_entries (~2745 tok)
- `fill_telltale_english.py` — TableParser: handle_starttag, handle_endtag, handle_data, split_sentences (~1996 tok)
- `globasa_pos.py` — Globasa POS tagger library. (~8628 tok)
- `HunspellMaker.py` — for: get_lexiklase (~2901 tok)
- `ingest_tmx_qdrant.py` — parse_tmx, main (~1010 tok)
- `JSONL parser non-English.py` — Parameterized JSONL parser for non-English Wiktionary dumps from kaikki.org. (~2473 tok)
- `Lexilista_parser.py` — Declares import (~6780 tok)
- `images_store.py` — Shared per-sense image store (menalariImages.jsonl): word -> PoS -> sense -> images. parse_commons_url (4 URL forms -> canonical file title), best_url/filepath_url (Special:FilePath fallback), image_keys (canonical + `aka` former titles), anki_slots (one still per PoS group), word_pos_keys, JSONL I/O that round-trips unknown keys (~2400 tok)
- `migrate_images_jsonl.py` — One-shot, idempotent: seeds menalariImages.jsonl from menalariImages_edited.csv + Globasa__Vocabulary.apkg; assigns `pos` only for single-PoS words; reports unparsed URLs + the multi-PoS queue (~1700 tok)
- `resolve_commons_images.py` — Refills direct_url from the MediaWiki API (50 titles/request, redirects=1, iiurlwidth=500); records former titles in `aka` on rename; flags deleted files as status=missing (~1800 tok)
- `validate_images.py` — Warnings-only checker: stale/unassigned `pos`, sense labels matching no gloss, gone images, retired words; skips illustratable=false (~1300 tok)
- `menalariImages.jsonl` — Per-sense image store, 1797 words / 1775 images. SOURCE OF TRUTH for images; supersedes menalariImages_edited.csv (which is now an untouched backup) (~250000 tok)
- `LLM_sense_judge.py` — wn_expand (~16417 tok)
- `merge_gold_priors.py` — merge_gold_priors.py — Merge manually-annotated gold alignments into eflomal priors. (~1558 tok)
- `merge_tmx_thirty.py` — Replace Thirty Short Stories TUs in existing TMX with freshly aligned ones from CSV. (~604 tok)
- `migrate_gold_tsv.py` — migrate_gold_tsv.py — One-shot migration for gold_alignments/{lang}.tsv. (~2143 tok)
- `Multi-Wiktionary sense curator.py` — Interactive CLI for curating non-English Wiktionary sense-marked translations. (~3908 tok)
- `pos_viewer.html` — Globasa PoS Viewer — whole-word PoS tagging, served at /pos (~6000 tok)
- `PosTagger.py` — ── Download word list ────────────────────────────────────────────────────── (~5450 tok)
- `PosTagger.py` — Globasa POS tagger: 3-step disambiguation (prep/particle→b, SVO, t/d;m resolution). Reads word-list.csv, outputs inline surface/POS. (~5000 tok)
- `pytest.ini` (~22 tok)
- `requirements.txt` — Python dependencies (~90 tok)
- `run_giza_improved.py` — parse_wordlist_gloss, parse_menalari_gloss, get_word_pairs, segment_word (~24733 tok)
- `tmx_viewer.html` — Globasa TMX Viewer (~6112 tok)
- `translation_aide.html` — Globasa Translation Aide (~6835 tok)
- `Wiktionary extension builder.py` — Wiktionary extension builder — reads vetted senses from xlsx files, (~2776 tok)
- `Wiktionary sense based translation extender 3.py` — match_sense_to_definition, extract_definition_and_examples, crossvalidate, wl_get (~4974 tok)
- `wiktionary_constants.py` — Shared constants and helpers for Wiktionary sense extender scripts. (~3963 tok)
- `Word Viewer.py` — Word Viewer — Flask-based local dictionary for Globasa. (~26198 tok)
- `word_viewer_etym_langs.csv` (~299 tok)
- `word_viewer_i18n.csv` (~2566 tok)
- `word_viewer_i18n.js` — UI heading/label localization for Word Viewer (~876 tok)
- `word_viewer_scripts.js` — Alternative script transliterators for Globasa (~1636 tok)
- `word_viewer.html` — Globasa Word Viewer (~25394 tok)

## ./ — Key Data Files

- `CanonicalSentences.tsv` — Canonical example sentences (~3251 tok)
- `CLAUDE.md` — Project instructions for AI assistants (~1216 tok)
- `Doxo_passages_edited_updated.csv` — Edited Doxo passages (~65391 tok)
- `Doxo_word_frequency.csv` — Word frequency from Doxo corpus (~79012 tok)
- `hyph-qgb.tex` — TeX hyphenation patterns (~11332 tok)
- `language-codes ISO 639-2.json` — ISO 639-2 language codes (~1006 tok)
- `menalariBLexi.tsv` — B-lexicon menalari data (~24214 tok)
- `menalariCorrection.tsv` — Corrections to menalari (~20389 tok)
- `menalariImages_edited.csv` — LEGACY one-image-per-word TSV. No longer read by anything; kept as a backup. Superseded by `menalariImages.jsonl` (~162814 tok)
- `menalariPronouns_edited.tsv` — Pronoun entries for menalari (~51500 tok)
- `README.md` — Project documentation (~982 tok)
- `requirements.txt` — Python dependencies (~66 tok)
- `TekstaroFrequencies.csv` — Tekstaro frequency data (~26041 tok)
- `TRAINING_PLAN.md` — Globasa neural translation model training plan (~6865 tok)
- `wiktionary_config.xlsx` — All configurable constants for Wiktionary pipeline: ExtensionLangs (53 langs), Dialects (9+5 tags), PoSMapping (21), PoSFallbacks (7), WiktionarySources (6 non-English) (~500 tok)
- `xwexi_gramati_sample.md` — Grammar sample (~3162 tok)
- `xwexi_pimpan.md` — Greetings lesson (~5799 tok)
- `xwexi_tree.json` — Globasa lesson tree structure (~39179 tok)

## ./ — Python Scripts

- `AnkiMaker.py` — Main Anki deck generator for content words; uses frequency-sorted wordlist + official wordlist (~2900 tok)
- `AnkiMaker2.py` — Variant Anki generator with AnkiFields reset logic (~2576 tok)
- `dictionaryPreprocess.py` — Generates mono/bilingual Apertium XML entries (14 files: En/Es/Eo/De/Fr/Nl/un × fn/content) via Lexilista_parser.parseWordEntry; verb-subtype-aware (vblex/vbmod/vbser); foreign-gender + Globasa-gender expansion (~3200 tok)
- `extend_tmx_eo.py` — Extends TMX with Esperanto; parse_eo_file, build_eo_by_position, make_tu (~3354 tok)
- `extend_tmx_pnc_multi.py` — Extends TMX with P&C translations (de, fr, da, nl, eo, ru, pt, id) from transcript markdowns (~1200 tok)
- `extend_tmx_udhr_multi.py` — Extends TMX with UDHR (de, fr, ru, zh, hi, ar, pt, tr, id, sw); auto sentence splitting (~2000 tok)
- `extend_tmx_udhr.py` — Extends TMX with UDHR (es, eo); manual split markers (~2748 tok)
- `fill_telltale_english.py` — Extracts modernized English from wiki HTML, sentence-splits and aligns with doxo Globasa, replaces Siri-Logane Tutum in CSV (~200 tok)
- `GenderResolver.py` — Resolves natural Globasa gender for anaphora purposes (~2586 tok)
- `GlobasaSourceTransliterators.py` — Converts romanizations/Latin spellings to Globasa phonetic renditions; uses fugashi (~4628 tok)
- `GlobasaTransliterators.py` — isVowel, globasaCountSyllables, globasaStressSentence, globasaStressWord (~540 tok)
- `HunspellMaker.py` — Generates Hunspell spellcheck dictionaries; get_lexiklase (~2002 tok)
- `Hyphenation.py` — Globasa hyphenation algorithm (~1725 tok)
- `ingest_tmx_qdrant.py` — Parses Doxo_passages.tmx, embeds with multilingual fastembed, uploads to Qdrant globasa_tmx collection (~300 tok)
- `JSONL parser non-English.py` — Parameterized JSONL ingester for non-English Wiktionaries from kaikki.org; --discover mode, downloads + decompresses gz, writes to WiktionaryLMDB_{lang}/ (~3200 tok)
- `JSONL parser.py` — Parses Wiktionary JSONL dumps; Translation class (~1888 tok)
- `JSONL tagInfo.py` — Extracts tag info from JSONL dumps; Translation class (~1441 tok)
- `Lexilista_parser.py` — Shared wordlist parser; GlossPoS, parseEntry (~2118 tok)
- `LLM_sense_judge.py` — 6-tier Wiktionary sense applicability judge: core match, register/domain, Qdrant corpus, composite, WordNet oewn:2023, Qwen LLM. Uses single Tier column (a/l). (~16500 tok)
- `load_globasa_graph.js` — Node.js script using @ladybugdb/core to create globasa.lbug from kuzu_import/ CSVs (~400 tok)
- `make_tmx.py` — TMX file generator (~449 tok)
- `MenaFixer.py` — Fixes omissions of ";" in English glosses (~1194 tok)
- `MenaImageGrabber.py` — Grabs images from Wikimedia Commons; FindBioImageURL, FindAtomImageURL, etc. (~2885 tok)
- `MenalariWordNetAligner.py` — Finds CILI indices for Globasa words via English/Spanish wordnets (~6198 tok)
- `MenaPatcher.py` — Applies patches to the menalari (~154 tok)
- `Multi-Wiktionary sense curator.py` — Interactive CLI for curating non-English Wiktionary senses; lookup by word;lang, select senses, appends to GLB_MULTI_WiktionarySenses.xlsx (~5600 tok)
- `NgramCounter.py` — N-gram frequency counter; saveNGrams (~585 tok)
- `prepare_kuzu_data.py` — Reads word-listNew_.csv, extracts word relations (synonyms, antonyms, derivations, tags), writes pipe-delimited CSVs to kuzu_import/ (~800 tok)
- `PrepositionAnkiMaker.py` — Anki generator for prepositions (~1011 tok)
- `run_giza.py` — Runs GIZA++ alignment; extract_parallel, tokenize, run_giza, show_alignments (~1788 tok)
- `SentenceLister.py` — Sentence extraction (~154 tok)
- `TekstaroFrequencyGuesser.py` — Corpus frequency estimation (~418 tok)
- `ThirtyStoriesToTable.py` — Parses `Corpora/Thirty Short Stories in Globasa new` into `Doxo_passages.csv` (verbatim passage pairs) and a styled Typst edition, applying the preamble and paragraph breaks from `Corpora/thirty_paragraph_breaks.tsv` (~900 tok)
- `Wiktionary extension builder.py` — Reads vetted senses from English + multi-source xlsx, fetches translations from LMDBs, writes menalariExtension.tsv (~4100 tok)
- `Wiktionary sense based translation extender 2.py` — Updated translation extender (~3218 tok)
- `Wiktionary sense based translation extender 3.py` — v3 English extender; PoS-aware cross-validation, imports from wiktionary_constants, outputs GLB_ENG_WiktionarySenses.xlsx only (~2200 tok)
- `Wiktionary sense based translation extender.py` — Uses vetted tuples to query Wiktionary for extra translations (~2450 tok)
- `Wiktionary senseKey preprocess 2.py` — Updated version of sense preprocessor (~4555 tok)
- `Wiktionary senseKey preprocess.py` — Scrapes Wiktionary dump, outputs Eng word/PoS/sense tuples for vetting (~3286 tok)
- `wiktionary_constants.py` — Shared constants + helpers loaded from wiktionary_config.xlsx; EXTENSION_LANGS, DIALECT_LANGS, GLOSSPOS_TO_WIKT, format_translation_word, _resolve_lang, marking loaders (~5600 tok)
- `WiktionaryPreprocess.py` — Splits Wiktionary JSONL dump into per-prefix subfiles (~660 tok)
- `WiktionaryScraper.py` — Live Wiktionary API scraper, get_wiktionary_data (~782 tok)
- `Word selection automator 2.py` — Updated word selection automator (~2827 tok)
- `Word selection automator.py` — Interactive: English word -> Wiktionary scrape -> lexiseleti with Globasa renditions (~2508 tok)
- `Word Viewer.py` — Flask-based local dictionary viewer; WordViewerDB (LMDB 8 sub-dbs), build_db() from all source files, /lookup/<word> JSON API, /audio/<word>.ogg pronunciation serving (~450 tok)
- `word_viewer.html` — Single-page frontend; 16-language selector (up to 2), PoS-grouped translation table with verb rowspan/colspan, gender article/anaphor, Butterick typography, RTL, example tooltips, constructions (~600 tok)
- `Wordnet based translation extender.py` — WIP: queries synonym sets for translations via CILIs (~1769 tok)
- `WordRanker.py` — Scrapes corpus for examples, ranks by corpus order; collectNGrams, processSentence, emphasizeExample (~6280 tok)

## .vscode/

- `tasks.json` (~1704 tok)

## Corpora/

- `Globatotal Deklaradoku tem Insanli Haki` — UDHR in Globasa (~2318 tok)
- `Hikaye fal Vanege` — Stories by Vanege (~7302 tok)
- `Siri-Logane Tutum` — Story (~2854 tok)
- `Thirty Short Stories in Globasa.md` — Main story collection (~10029 tok)

## GlobasaGrammarChecker/

- `__init__.py` (~11 tok)
- `__main__.py` — CLI entry point: check Globasa text from stdin or arguments. (~174 tok)
- `checker.py` — Ensure project root is importable (~599 tok)
- `server.py` — LanguageTool-compatible HTTP server for Globasa grammar checking. (~568 tok)

## GlobasaGrammarChecker/rules/

- `__init__.py` (~150 tok)
- `adverb_mo.py` — word: check (~748 tok)
- `base.py` — GrammarMatch: to_lt_dict, check (~410 tok)
- `conditional.py` — ConditionalRule: check (~554 tok)
- `infinitive.py` — InfinitiveRule: check (~922 tok)
- `negation.py` — NegationRule: check (~473 tok)
- `noun_as_verb.py` — words: check (~569 tok)
- `noun_pile.py` — Minimum consecutive nouns to flag (3+ is suspicious; (~510 tok)
- `np_structure.py` — NPStructureRule: check (~430 tok)
- `passive.py` — PassiveAgentRule: check (~598 tok)
- `question.py` — ke-correlative interrogatives and question particles (~422 tok)
- `tense.py` — TenseParticleRule: check (~473 tok)

## Hunspell/

- `Globasa.aff` — Affix rules (~1325 tok)
- `Globasa.dic` — Dictionary (~18922 tok)

## doxo-pages-grav/ (git submodule)


## globasa_tokenizer/

- `__init__.py` — GlobasaTokenizer: tokenize, tokenize_batch, detokenize, lexicon + 2 more (~1174 tok)
- `_types.py` — Declares from (~316 tok)
- `affix_constraints.py` — suffixes: suffix_pos_ok (~679 tok)
- `affix_parser.py` — from: parse_lexiliasel (~1281 tok)
- `affix_trie.py` — AffixTrie: insert, longest_match, insert, longest_match (~663 tok)
- `alignment.py` — to_aligner_text, to_awesome_align_pair, project_to_words, project_to_morphs (~950 tok)
- `fallback_cascade.py` — cascade (~649 tok)
- `lexicon.py` — Lexicon: build_lexicon, get_lexicon, refresh_lexicon (~2345 tok)
- `mined_stems.py` — from: load_mined_stems, match (~790 tok)
- `offsets.py` — AlignmentError: align (~523 tok)
- `pseudo_morphemes.py` — from: load_inventory, search, dp_cover, match (~2554 tok)
- `segmenter.py` — segment_word (~4694 tok)
- `syllable_fallback.py` — syllabify, syllable_cover (~1000 tok)
- `tokenizer.py` — _GlobasaTokenizerImpl: tokenize, tokenize_batch, detokenize (~2648 tok)

## globasa_tokenizer/data/

- `mined_stems.tsv` — 6551 frequent stems (freq≥3) mined from word-list residues; surface→freq columns; used by MinedStemMatcher for Tier 1 fallback (~9000 tok)
- `pseudo_morphemes.tsv` — ~170 rows; surface→lemma→language→notes; seed Sinitic/European entries + auto-mined; used by PseudoMorphemeMatcher with Aho-Corasick (~250 tok)

## globasa_tokenizer/hf_adapter/

- `__init__.py` — GlobasaPreTokenizer: globasa_split, pre_tokenize, build_pre_tokenizer (~678 tok)

## globasa_tokenizer/spacy_adapter/

- `__init__.py` — GlobasaDefaults: make_doc (~871 tok)
- `pipeline.py` — morph_component, morph_component (~277 tok)

## globasa_tokenizer/tests/

- `test_alignment.py` — lex, test_to_aligner_text_basic, test_to_aligner_text_word_index_chain, test_project_to_words_collap (~1152 tok)
- `test_fallback_cascade.py` — MockMatcher: test_cascade_no_crash, test_cascade_adversarial, test_cascade_single_char, test_cascade (~849 tok)
- `test_grammar_constraints.py` — tok, test_hyphen_inside_word_preserved, test_hyphen_inside_word_second_example, test_emdash_is_punct (~880 tok)
- `test_hf_adapter.py` — test_build_pre_tokenizer, test_pre_tokenizer_splits_morphemes, test_hf_tokenizer_with_word_level_mod (~620 tok)
- `test_lexiliasel.py` — get_expected_lemmas, lex, test_lexiliasel_parity (~1516 tok)
- `test_offsets.py` — tokenizer, test_offsets_exact_match, test_offsets_contiguous_within_word, test_word_index_monotone (~703 tok)
- `test_perf.py` — tok, test_throughput_100k_words_per_sec (~692 tok)
- `test_pseudo_morpheme_split.py` — tok_on, tok_off, test_european_syon_split, test_european_si_split (~1380 tok)
- `test_roundtrip.py` — lex, test_roundtrip_all_words (~626 tok)
- `test_spacy_adapter.py` — test_spacy_language_registration, test_spacy_morph_pipeline, test_spacy_morphs_match_core (~646 tok)
- `test_syllable_fallback.py` — test_syllabify_count, test_syllable_roundtrip, test_syllable_cover_offsets, test_oov_fallback_produc (~747 tok)
- `test_unknowns.py` — tok, test_known_roots_not_split, test_oov_novel_no_unk, test_adversarial_no_crash (~1056 tok)

## kuzu_import/ (generated)


## tools/

- `build_pseudo_morpheme_inventory.py` — Bootstrap script: Pass 1 Sinitic (CJK chars in etymology), Pass 2 European (rule-driven -syon/-si/viu/-tika/-fobi), Pass 3 candidates (terminal n-gram frequency); writes to globasa_tokenizer/data/pseudo_morphemes.tsv (~2284 tok)
- `mine_frequent_stems.py` — Bootstrap script: extracts n-grams (3-5 char) from segmentation residues, freq≥3, writes 6551 stems to globasa_tokenizer/data/mined_stems.tsv (~1077 tok)

## xwexi-pages-grav/ (git submodule)
- `backups/thirty_update_2026-08-24/` — Pre-update snapshot of the Thirty Short Stories data: original `Doxo_passages.tmx`, `Doxo_passages_extended.tmx`, `Doxo_passages_edited_updated.csv`, `gold_alignments/en.tsv`, plus `thirty_revisions_before_2026-08-24.tsv` (the 980 hand-revised rows) and `dropped_hand_edits_2026-08-24.tsv` (479 old-vs-new Globasa differences for review).
- `Corpora/thirty_paragraph_breaks.tsv` — Paragraph breaks per story (StoryIndex, GlobasaTitle, comma-separated sentence indices that start a new paragraph), recovered from `Corpora/ThirtyStories.typ`. Editorial, not authorial: added by the repo owner and ChatGPT, not by Vanege. Globasa and English break at the same sentence positions, so one set serves both.
- `globasa_hyphenation.py` — Pure Globasa syllabifier (possible_onsets, all_consonants, hyphenation, fix_hyphenation), extracted from `Hyphenation.py` so it can be imported without triggering that script's word-list download and pattern-file writes.
- `globasa_word_hyphenation.py` — Morpheme-aware Globasa hyphenation. Splits a word into morphemes (word-list `Hyphenation` column > `LexiliAsel` composition > productive affix stripping) and syllabifies each independently, so compound seams are never broken across (e.g. `atexalkoba` -> a-tex-al-ko-ba, not a-te-xal-ko-ba). API: morphemes(), hyphenate(), break_positions().
