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
- `constructions.py` — Shared construction matcher. Constructions.xlsx pairs a headword with a syntactic frame (`▯ jixi na ▯`) plus a `to_exclude` list of gloss items that only hold inside the frame. split_items/split_annotation/normalise_item/apply_to_exclude (returns (text, matched)), load_constructions, exclusions. Lifted out of AnkiMaker3 so the wordlist cleaner and the deck builder cannot drift (~900 tok)
- `extract_constructions.py` — Strips the `to_exclude` gloss items from word-list.csv in place after each CDN download. Idempotent; preserves CRLF and the missing final terminator; backs up to word-list.csv.pre-constructions. `hay` and `sengi` end with no English gloss — the frame carries their whole meaning (~700 tok)
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
- `images_review.html` — Contact-sheet review UI at /review: every illustrated word as a dense grid of thumbnails + gloss, filterable by tag / flag (shared, gone, off-commons, uploaded, derived), sortable, infinite scroll, click-through to the curator, drop-lead-image action (~1900 tok)
- `images_curator.html` — Commons image curation UI served at /images: course-ranked queue of words whose gloss has an unillustrated content PoS, per-sense image editing (add/remove/reorder/label/set-pos), Commons search grid, one-click "can't be pictured" (~2600 tok)
- `images_store.py` — Shared per-sense image store (menalariImages.jsonl): word -> PoS -> sense -> images. parse_commons_url (4 URL forms -> canonical file title), best_url/filepath_url (Special:FilePath fallback), image_keys (canonical + `aka` former titles), anki_slots (one still per PoS group), anaphor_slots (sense `anaphor: te|to` -> plant pronoun card image), word_pos_keys, JSONL I/O that round-trips unknown keys (~2400 tok)
- `migrate_images_jsonl.py` — One-shot, idempotent: seeds menalariImages.jsonl from menalariImages_edited.csv + Globasa__Vocabulary.apkg; assigns `pos` only for single-PoS words; reports unparsed URLs + the multi-PoS queue (~1700 tok)
- `resolve_commons_images.py` — Refills direct_url from the MediaWiki API (50 titles/request, redirects=1, iiurlwidth=500); records former titles in `aka` on rename; flags deleted files as status=missing (~1800 tok)
- `vscode-tasks.json` — Staged replacement for `.vscode/tasks.json` (that path is a read-only mount in the Claude Code sandbox). Adds the four deck-pipeline tasks; install with `cp vscode-tasks.json .vscode/tasks.json` then delete (~200 tok)
- `LafuzuDeckMaker.py` — Builds/updates Globasa__Lafuzu.apkg (deck Globasa::Lafuzu): written<->spoken cards from Hector's recordings. Sources: lesson word-list clips in Segmentation/Ektor_su_Lafuzu_processed (.ogg), 04.pimpan-logaxey mp3s, 03.gramati/01.abece-ji-lafuzu example words + permitted variants. Pairs audio only on exact filename=text spelling match. Templates Written → Spoken, Spoken → Written (optional via SpokenToWritten field), one subdeck each; synthesized lesson 17 as separate tagged notes under Globasa::Lafuzu::Synthesized::*; GUIDs from text (~2600 tok)
- `splits_review.html` — Word Viewer page /splits: review lesson-recording split proposals. Web Audio playback (sample-accurate), zoomed waveform with draggable edges, shift-click split, merge/delete, rename with lesson-entry datalist, keyboard (Space/C/Enter/arrows/[ ] ; '), autosave, export ticked rows as clips (~3500 tok)
- `lesson_audio_labels.py` — Proposes Audacity label tracks (LessonAudioLabels/darsu_NN_lexilista.txt) for lessons not yet cut. Cuts: ffmpeg silencedetect, padded 0.12 s. Names: wav2vec2 phoneme recogniser (Models/wav2vec2-lv-60-espeak-cv-ft) -> IPA mapped to Globasa letters -> in-order edit-distance alignment with the lesson's entries (skips, two-segment phrases); off-list segments matched against word-list headwords; unsure labels end in "?" (~2600 tok)
- `xwexi_lessons.py` — Shared lesson word-list parser: lesson_entries(n) (expands "**kenumer** (**te**/**to**)" into 3 entries), spoken_forms(entry) ("pala (yon/in)" -> pala yon / pala in / pala), clip_name() (~500 tok)
- `menalariAnaphorSenses.tsv` — Per-sense pronoun for every plant/food word (Word, Anaphor te|to, Mena label). te = live whole plant only; food, parts, cut/dead = to. Overrides menalariPronouns_edited.tsv in AnkiMaker3 (~9000 tok)
- `menalariMainGloss.tsv` — Main-gloss overrides for Anki (Word, MainGloss, Note): AnkiMaker3 fronts and emphasises the named gloss in whichever PoS row contains it, when the wordlist's first gloss is not the clearest core (~50 tok)
- `menalariGlossQualifiers.tsv` — Qualifiers for English homographs the wordlist leaves bare (Word, Gloss, Qualifier, Note): AnkiMaker3 renders the gloss as "hack (_with an axe_)". tabar/hake (hack), jumun/harufi (spell) (~80 tok)
- `menalariMainGloss_candidates.tsv` — Review list for menalariMainGloss.tsv: rows whose first English gloss another (non-related) word shares, with that word, the row's unshared glosses and Epo. Generated ad hoc 2026-11-07, not by a script in the repo (~60000 tok)
- `restructure_vocab_deck.py` — One-off, idempotent schema change to Globasa__Vocabulary.apkg: names templates Card 14-19, adds AloAnaphor/AnaphorMena/AnaphorImaje fields, rewrites Pornamelexi + adds Alo Pornamelexi (plant te/to), removes SabziFruta prototype notetype; adds the single Verb Type card (removes the rejected Verb Class card) and makes echo/-cu meaning cards use the bare verb. Idempotent, extend it for future schema changes. Backup .pre-restructure.bak (~1900 tok)
- `update_vocab_deck.py` — Pushes AnkiList.csv into Globasa__Vocabulary.apkg using Anki's own library, so card generation follows the real conditional templates. Files every card in Globasa::Vocabulary::<template name> (template deck override + move pass, drops emptied subdecks); removes cards an update left empty; warns when the input apkg carries study history. Keeps note type, 32 templates, styling and every note GUID (GUIDs carry learners' scheduling on re-import). Fields matched to columns BY NAME; Lexi is read-only (24 notes are trailing-space twins). Adds new words, reports duplicates and retired notes, never deletes (~1500 tok)
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
- `translation_aide.html` — Globasa Translation Aide; interactive Apertium frontend: polysemy dropdowns, plus un/nun marker chips for the article and present-tense markers Globasa leaves unmarked (~6900 tok)
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
- `extend_tmx_doxo_2026_11.py` — Dry-run by default; `--write` appends the Nov 2026 Doxo texts (mostly Globasa-only TUs) to both TMX files and the master CSV, refuses to run twice (~2300 tok)
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
- `sense_vetter.py` — Local page on port 8090 for vetting Wiktionary senses, most obvious first, no model; scored partly by other glosses, taxa and tags against sibling senses; saves to sense_vetting.jsonl (verdicts s, n, u=unsure, clear), --check and --export modes (~6500 tok)
- `sense_vetter.html` — Keyboard-driven page for sense_vetter.py, with Hide vetted toggle, Unsure mark, peek with marking, browse by tag, and views for words with no sense marked and for unsure senses (~4500 tok)
- `sense_review_queue.py` — Scores Wiktionary senses against TMX usage with a decision model on llama-server, writes a blind annotator queue ordered by value per minute plus a scores TSV to sense_review/; resumable, memory-capped Reads sense_vetting.jsonl; --rotate tests option-order effects; caps passes at 25 senses; default 4 shuffles. Default prompt uses the model-card layout; --compare tests choice formats.
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
- `Word Viewer.py` — Flask-based local dictionary viewer; WordViewerDB (LMDB 8 sub-dbs), build_db() from all source files, /lookup/<word> JSON API, /audio/<word>.ogg pronunciation serving; /splits + /api/splits[/<n>[/audio|/export]] lesson-split review (state in LessonAudioLabels/*.json, export Vorbis 48k mono into AUDIO_DIR, never overwrites unless asked) (~450 tok)
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
- `globasa_collision_check.py` — Candidate-form collision checker for proposed Globasa roots: exact hits, near-homophones (y->i / w->u normalisation, catches tian~tyan), edit-distance-1 minimal pairs, misparse of existing words as candidate+morpheme, self-decomposition into prefix+root, plus phonotactic validation implementing the DOCUMENTED xwexi rules (onset cluster list, coda=any consonant medially / restricted word-finally, stop+stop ban, w/y caveats); validated at 99.6% against all 3188 roots. Severity: BLOCK/WARN/NOTE/CLEAR (~1400 tok)
- `globasa_hyphenation.py` — Pure Globasa syllabifier (possible_onsets, all_consonants, hyphenation, fix_hyphenation), extracted from `Hyphenation.py` so it can be imported without triggering that script's word-list download and pattern-file writes.
- `globasa_word_hyphenation.py` — Morpheme-aware Globasa hyphenation. Splits a word into morphemes (word-list `Hyphenation` column > `LexiliAsel` composition > productive affix stripping) and syllabifies each independently, so compound seams are never broken across (e.g. `atexalkoba` -> a-tex-al-ko-ba, not a-te-xal-ko-ba). API: morphemes(), hyphenate(), break_positions().

## docs/research/

- `colexification-happiness-luck.md` — **State vs trait happiness across languages**: how the "happy right now" / "happy in general" distinction is encoded (6 mechanisms: separate lexemes, copula choice, no split, inner-organ periphrasis, root-and-pattern morphology, trait-word-is-heavier) and what each pole attaches to (momentary → joy/glad/cheer/lively, from shining/jumping/rejoicing/intoxication; enduring → luck/blessed/content/fulfilled/prosperous, from allotted share/omen/fitting-together/fertility). Documents why CLICS is structurally blind to the contrast. 30 languages, ~100 words, all from the Wiktionary API. Original by Mistral Vibe; revised + reoriented by Claude 2026-09-07 (~9000 tok)
- `.colexification-happiness-luck.md.orig` — hidden pre-revision copy of the above, kept because docs/ is untracked in git (~5100 tok)
- `colexification-happiness-luck-review.md` — Source audit + corrected classification + extension of the above. Documents 11 factual errors and 4 citation mismatches; adds real CLICS⁴ / Glottolog / Oishi et al. 2013 data, three recurring source metaphors (allotted share / omen / things fitting together), and a Globasa `hox`–`xanse` analysis (~6500 tok)
- `semantic-eurocentrism-audit.md` — Audit of semantic Eurocentrism in Globasa: Esperanto-alignment measurement (Epo>Eng>Spa), refuted decomposability hypothesis (permutation test), word-selection tooling review, 5 criteria for semantic imports, truncation pattern (muka/mosem/dao/gwanxi/kismetu), proposals (2 roots + ~16 compounds), WALS lexical typology, phonotactics, full source list (~9500 tok)

- `Methodology for Lexical Development _ Globasa.html` — Saved official page: minimal-pair avoidance tiers, source selection, form rules for new roots (~7300 tok)
- `Taquigrafía_Castellana_-_Marti.pdf` — Scan of Marti's Spanish shorthand manual: alphabet, syllabary and joining plates at PDF pages 115-125 (144 pages)
- `1240624.1240850.pdf` — Cao & Zhai 2007, CHI paper modelling pen stroke time from curves, lines and corners; source for the shorthand stroke-time ranking (10 pages)
- `shorthand_geometry.py` — Loads candidate alphabets from shorthand_candidates.json; stroke geometry, word pen paths and the shared stroke-time model (stroke_time)
- `shorthand_optimizer.py` — Simulated-annealing search for a shorthand alphabet, parallel over all cores, about 1 minute (single simple shapes: lines, semicircles, loops, circles; rounded-join rule, inter-letter contact penalty, simplicity/size order by frequency, variety and Latin tie-breaker; Cao & Zhai time, Callendar joins, look-alike whitelist, lineality); writes shorthand_candidates.json
- `shorthand_candidates.json` — Top 3 diverse alphabets from the optimizer, with settings and join/confusion reports; read by shorthand_geometry.py
- `shorthand_word_stats.py` — Word statistics for the shorthand search: even-weighted text letter pairs, lexicon pairs, word-edge letters, word lengths, function-word phrase joins, misreading % per letter pair over text and full word list; writes shorthand_word_stats.json
- `shorthand_word_stats.json` — Output of shorthand_word_stats.py, read by shorthand_optimizer.py
- `shorthand_practice_sheet.py` — Builds the printable A4 vowel-style practice sheet from shorthand_geometry.py
- `shorthand_practice_sheet.pdf` — 8-page practice sheet comparing the 3 optimizer candidates: key, 40-stroke inventory, top 20 pairs, sentences, speed and cold-read log
- `shorthand_style_metrics.py` — Corpus metrics per vowel style: model time, drift, word height, risky joint angles, and joins scored by Callendar's sharp/blunt/continuous categories
- `manualofcursives00calliala.pdf` / `.epub` — Callendar 1889, Manual of Cursive Shorthand (phonetic forerunner of Orthic); joining principles in the introduction and section 54 (book p. 56 = PDF p. 64)
- `shorthand_literature_sweep.md` — Reading list on handwriting speed models and legibility for the shorthand design: papers to read first, two tables, gaps, a small self-test

## Word Selector (2026-11-07)
- `word_selection/calques.py` — calque proposals: split source words (Wiktionary compound parts, Han chars, phrases), gloss parts to Globasa roots, count independent coinages per head and modifier+head, propose modifier+head (~2500 tok)
- `word_selection/precedent.py` — LexiliAsel precedent by group (sino, jako, arabic, indic, european): exact patterns + letter-class 'follow language' layer, leave-one-out via exclude_root, never the word-final vowel slot; used by blend.candidates via decide() (~3000 tok)
- `word_selection/sino_align.py` — ancestor-centred alignment for Sino-xenic clusters: shared Han spelling, each member cut into one syllable per character against Middle Chinese (else Cantonese) readings, syllables aligned to the reading, centre-star merge + complementary-column compaction; ENABLED flag; used by blend.candidates and precedent._learn (sino group) (~2000 tok)
- `word_selection/contrasts.py` — lexical contrasts other languages make inside an English sense, via foreign Wiktionary editions (WiktionaryLMDB_<ed>): pivot words' senses + translation tables; sides = merged foreign senses; contrast = disjoint words in >=2 families; focus() gives exclusions for one side; best sense per pivot, phrase rule, general-sense detection; neighbour English tables via reverse index; related() root matching; compare_to_pivot() pairwise pivot-vs-foil verdicts per language; auto_pivot() sweep, suggestion(), summarize(); wired into Word Selector (/api/contrasts, section 3b) (~7500 tok)
- `word_selection/abjad.py` — Arabic/Persian consonant skeletons (fallback join in cluster.py) + vocalization prediction between them from vowel length (length_form, parse, predict, predict_all) + vocalization from a cognate in another script (vocalize_from, vocalize_from_cognates; FIT_MAX 0.15) (~4000 tok)
- `word_selection/vocalization.py` — vocalization dictionaries: Arabic Camel Morph MSA v1.0 lemma index (CC BY 4.0; arabic(), arabic_form(), arabic_forms() with concept-gloss / table-roman disambiguation) and Persian KaamelDict (GPL, cache only; persian(), persian_forms()); data downloaded into git-ignored word_selection_cache/ (~2500 tok)
- `word_selection/cultural.py` — proper nouns / culture-specific words: detect() (capitalised English name, or English borrowing from a source language with 2+ other languages borrowing the same word; concept "cultural" override), origin_member(), checked_pronunciations(); pipeline.propose_cultural ranks pronunciation vs spelling readings by checked support (~900 tok)
- `word_selection/methodology.py` — passages of the methodology / Q&A (vendored CC0 copies in word_selection/docs/) and grammar phonotactics (xwexi submodule); RULES map ranking explanations (cluster why, proposal trace/notes, collision tiers) to justifying passages; for_cluster(), for_proposal(), check_rules() (~2200 tok)
- `word_selection/docs/` — CC0 copies of globasa.net methodology and Q&A pages from Globasa-Team/main-pages-grav (README gives source/date)
- `word_selection/pronunciation.py` — German/French Wiktionary edition pronunciations for their own words (word -> IPA), built from raw wiktextract dumps on Warehouse2 into word_selection_cache/ (~600 tok)
- `word_selection/sources/taxon.py` — candidates by taxon (concept "taxa"): Wikispecies {{VN}} vernacular names, Wikipedia langlinks of the taxon article, English Wiktionary senses whose definition names the taxon; rank-aware marker removal, plural -> singular, scientific-name titles left out by default (~1800 tok)
- `word_selection/plurals.py` — plural -> singular noun index for source languages from the raw English Wiktionary dump forms (cache) (~500 tok)
- `word_selection/sense_fit.py` — does a source word's own Wiktionary entry attest the concept's meaning? Gloss structure (attests / shifted: particle or means / homonym: another sense of a polysemous English headword / ambiguous / unattested / no entry); etymology_for_meaning() for the etymology-cognate step (~2000 tok)
- `word_selection/sinosphere.py` — Sinosphere support for clustering: build() one dump pass -> word_selection_cache/sinosphere.json (MC Baxter readings, simp->trad, shinjitai->kyūjitai, Korean hanja, Vietnamese chữ Hán from vi-etym-sino); han_spellings() normalised; ja_reading_kind() on'yomi vs kun'yomi; pivots() MC + Cantonese (~3000 tok)
- `Word Selector.py` — Flask page on :8092 for automated word selection (concept builder, sources table, ranked etymon clusters, proposals, dossier, save to word_selection_decisions.jsonl); attaches methodology justifications; /api/methodology serves all passages. Module-level app.run(): import with exec minus that line for test_client (~1600 tok)
- `word_selector.html` — single-page UI for the above (~6000 tok)
- `word_selection/` — pipeline package: languages, concept_index (LMDB accessor + build_reverse), lexicon (LexiliAsel etymon parser, reverse index), translit (rule engine, 16 langs, gold-tuned), align (weighted NW + center-star MSA), cluster (etym links + avg linkage, thr 0.30), select (families/tie-breaks/fallback), blend, form_rules, collision (tiered minimal pairs; globasa_collision_check.py imports it), dossier, pipeline, sources/{wiktionary,wikidata,seeds}
- `Wiktionary concept index.py` — one pass over raw-wiktextract dump -> WiktionaryLMDB_concepts/ (translations WITH roman, sense QIDs, entries with IPA/roman/etym for 16 langs + eo)
- `Dictionary ingest.py` — downloads/indexes CC-CEDICT, JMdict, OMW (downloads blocked in sandbox; adapters not yet written)
- `word_selection_eval.py` — `translit [lang]` per-language accuracy vs LexiliAsel romanizations; `roots [oracle|e2e] [N]` leave-one-out root proposals

## word_selection/tests/

- `test_han_display.py` — display_han / han_unconfirmed / LexiliAsel Han format (~400 tok)
- `test_pivots.py` — pivot_support, rank tie-break after methodology, tuple sense pick (slow: de LMDB) (~450 tok)

- `setup.sh` — one-step Word Viewer setup on a fresh clone: xwexi/doxo submodules, venv/ from requirements-viewer.txt, word-list.csv download (drops WordViewerLMDB when the list changed) (~450 tok)
- `requirements-viewer.txt` — only the Word Viewer's packages (flask, pandas, lmdb, msgpack, requests, wget, fastenum, openpyxl, pillow) (~100 tok)
- `vetted_senses.py` — the vetting decisions store: export() spreadsheets -> vetted_senses.tsv (Glb, Source, Eng, Prt of Sp, VerbType, Wiktionary Sense, App?, Tier; rows with a Tier only); sync() re-exports when GLB_*_WiktionarySenses.xlsx (dir from .senses_config.json) is newer; load_markings() for the sense generator, load_vetted() (App? s, Tier v/e) for the extension builder (~1300 tok)
- `vetted_senses.tsv` — 13,075 committed vetting decisions (~800 KB); everything else in the senses spreadsheets is regenerated
- `wiktionary_extract.py` — stream kaikki raw English dump (path, .gz or URL; never stored) into a WiktionaryDB; keys= keeps only given (word,pos); __main__ builds WiktionaryLMDB_vetted/ (35 MB, ~2.5 min) for the vetted senses (~1100 tok)
- `wiktionary_db.py` — WiktionaryDB (LMDB: translations, senses, spanish_pos), msgpack (de)serializers, Translation/Example/Sense tuples (~1000 tok)
