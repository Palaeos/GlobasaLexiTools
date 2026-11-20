# The Time Machine → Globasa

Translation workspace for H. G. Wells, *The Time Machine* (1895). The text is public domain: Wells died in 1946, and the book was published before 1929.

- **Base text:** the British first edition (Heinemann, 1895).
- **Second witness:** the American first edition (Holt, 1895). Its wording differs from Heinemann's, and Wells wrote both. Where a Holt reading is plainer, it can guide the Globasa wording.

## Plain-language aim

The Globasa version should also get round the book's Victorian vocabulary. Wells uses *recondite*, *fecundity*, *controvert*, *thither*, *incontinently* (in the sense "at once") and *presently* (in the sense "soon"), and many present-day Anglophones can't read these. Globasa renders each one by its **sense in context**, in plain roots. So the translation also works as a plain-English key: back-translate it and you get the sense, not the Victorian word.

## Files

| File | What it is |
|---|---|
| `fetch_texts.py` | Downloads three editions from English Wikisource ("The Time Machine (Heinemann text)", "(Holt text)" and the Atlantic Edition, vol. 1, 1924) into `text/`, with chapters in reading order. |
| `text/heinemann.txt`, `text/holt.txt` | Plain text, one `## <chapter>` heading per chapter. |
| `scan_obscure.py` | Script tier: proposes candidate words only and decides nothing. A candidate is a non-proper-noun token whose surface form and lemma both have a Zipf value below 3.0 in wordfreq (modern English, all registers). Ligatures are normalised (œ→oe). Each candidate gets its Wiktionary senses (from `../WiktionaryLMDB`) and a `base_hint` for forms that look like regular derivatives; the hint never filters a word out. Writes `obscure_candidates.tsv`. |
| `obscure_candidates.tsv` | 599 candidates with zipf, count, editions (H/U), first context and Wiktionary senses. |
| `obscure_resolved.tsv` | Judgement tier: a verdict per candidate, the sense in context in plain English, and its Globasa rendering. |

### `obscure_resolved.tsv`

Columns: `lemma, verdict, ref, quote, sense, glb, glb_how, note`.

- `verdict` takes one of these values:
  - `obscure`: a general modern reader likely doesn't know the word.
  - `dated_sense`: a common word used in a Victorian sense, such as *presently* meaning "soon". The frequency scan can't find these, so they come from a reading of the text.
  - `transparent`: rare as a string, but obvious from its parts (*tableful*).
  - `technical`: a scientific name.
  - `misprint`: an OCR or printer's error.
- `sense`: the sense in this sentence, written in very common English words. Wiktionary often lacks the sense Wells intends. *Fecundity* here means "inventiveness", for example.
- `glb_how`: where the Globasa rendering comes from. `word-list` means one existing word from `word-list.csv`. `derived (proposed)` means a compound or derivation from existing roots, still to be vetted. `paraphrase` means a short Globasa phrase. `fallback: <why>` gives the reason a fallback was used.

A lemma used in two senses gets one row per sense.

## Translations as sense evidence

Two published translations show how a contemporary translator read each word. They are kept only in the git-ignored `cache/`; just the translator's word for each row is committed.

| | Translation | Source and status |
|---|---|---|
| **epo** | *La tempo-maŝino*, translated by E. W. Amos (Epoko Libro-Klubo, about 1938; INKO e-book 2001) | Free to download, but not openly licensed; the translator's death date is unknown. Used as evidence only, never committed. Copy it in by hand as `cache/amos.pdf`, because the hosts are blocked by the sandbox proxy. |
| **spa** | *La máquina exploradora del tiempo*, translated by J. d'Albroi (Barcelona, B. Bauzá, 1925/26) | The Internet Archive scan `maquina-del-tiempo` carries a Public Domain mark and is also on Wikimedia Commons. |

| Script | What it does |
|---|---|
| `inko_text.py` | Converts INKO e-book PDFs to text. Their legacy font puts ĝ in the `¸` slot, ŝ in `ÿ`/`ß`, ĥ in `˛`, and so on. |
| `ocr_spreads.py` | OCRs a scan of two-page spreads. It renders at 300 dpi, splits at the gutter, crops to the text block, runs tesseract with models in `cache/tessdata`, and drops headers and watermarks. The Internet Archive's own OCR of the Spanish scan is unusable. |
| `align_translations.py <lang> <text>` | Finds the translator's word for each glossary row. It aligns sentences with LaBSE, then words with SimAlign (link confidence of at least 2 of 3 methods). It compares the result with the TranslationEpo or TranslationSpa gloss of the row's Globasa word and writes `cache/evidence_<lang>.tsv`. |
| `merge_evidence.py` | Adds the columns `epo`, `spa` and `tr_check` to `obscure_resolved.tsv`. |

`tr_check` gives one result per language:
- `agree`: the translator's word shares a stem with a gloss of the chosen Globasa word, so the sense is supported.
- `differ`: the two don't match. Review the row; this doesn't mean the row is wrong, because a translator may paraphrase.
- `none(...)`: there is no usable evidence, and the bracket gives the reason.

The check compares word shapes only. The Esperanto result carries the most weight, because Globasa's Epo glosses draw the finest sense distinctions.

## Edition variants (Holt 1895, Atlantic Edition 1924)

`witness_variants.py` (formerly `holt_variants.py`; the comparison itself is `../edition_variants.py`) compares Heinemann with each other witness by Wells. For the Atlantic Edition (1924, Wells's late revision, `text/atlantic.txt`), it finds only 316 variants and 20 short word changes. Wells barely revised the book, e.g. *Overworld* → Upper-world, *lit* → struck, *seas* → lakes, and one glossary row: *genuine, if uncivil* dropped. Holt remains the main source of plainer wording.

For Holt, it matches each Heinemann sentence to the closest Holt sentence and labels every word-level change by shape only: spelling, punctuation, substitution, insertion or deletion. This gives 1,993 variants, written to `holt_variants.tsv`. The script also fills the `holt` column of the glossary when a short Holt substitution covers the row's word, e.g. *valves* → panels, *desiccated* → dried-up, *elated* → "elated by my discoveries".

Rule of thumb: **follow Heinemann for content and for deliberate word choices, and follow Holt for the plain wording.** That covers Holt's synonyms, its explicitations, and its use of clauses where Heinemann has nominalisations ("her rescue" → "I rescued Weena"). Holt is the earlier state of the text and has misprints of its own.

## Existing witness: *Siri-Logane Tutum*

Poe's "The Tell-Tale Heart" (1843) was translated into Globasa by way of a modernised English rewrite. All three texts are in the repo: the Globasawiki page and `Doxo_passages.tmx`. `telltale_witness.py` traces the chain Poe → modern English → Globasa and writes `telltale_witness.tsv`, with 278 modernisations and the Globasa word for each.

- **Scanner calibration:** 71% of the Zipf < 3 words in Poe were also changed by the human modernizer. The words he kept are mostly transparent derivatives (*causeless*, *unperceived*), which is the glossary's `transparent` class.
- **Same choices made independently:** *presently* → soon → *nerxali*, *scarcely* → hardly → *eskaso*, and *singularly* → remarkably. The glossary rows carry these as `precedent` notes.
- **Different choice:** *fancy* → think → *fikir*, where the glossary has *imaje*. This needs a consistency decision.
- **Limitation:** the Globasa follows the modern rewrite closely, so it inherits that rewrite's paraphrases and some translationese. It is a precedent, not a model.

## Scholarly sources

`fetch_sources.py` downloads the public-domain primary sources for curated readings of Wells's terms of art. Readings are taken from the primary text and cited with pages where the source has them.

| File | Source | Settles | Pages |
|---|---|---|---|
| `sources/tylor_primitive_culture.txt` | Tylor, *Primitive Culture* (Wikisource; 1920 printing of the 1871 work) | *survival* (chs. 3–4), *savage* | `[p. N]` |
| `sources/huxley_evolution_ethics.txt` | Huxley, *Evolution and Ethics* (Romanes Lecture 1893) | *struggle*, *fitness*, the "cosmic process" | `[p. N]` |
| `sources/wells_zoological_retrogression.txt` | Wells, "Zoological Retrogression", *Gentleman's Magazine* 271 (Sept 1891) | *degeneration*, *degradation*, *retrogression* | by section |
| `sources/wells_certain_personal_matters.txt` | Wells, *Certain Personal Matters* (1898; Gutenberg #17508) | "Of a Book Unwritten" (= "The Man of the Year Million", 1893): the far-future human body | by essay |
| `sources/lankester_degeneration.txt` | Lankester, *Degeneration: A Chapter in Darwinism* (1880; Internet Archive OCR) | *degeneration*, *etiolated*, *parasitism* | by chapter (the OCR has no page breaks) |
| `cache/sources/webster_1913.txt` | *Webster's Revised Unabridged Dictionary* (1913; Gutenberg #29765), 29 MB, git-ignored | period senses with [Archaic]/[Obs.] labels, e.g. *incontinently* = "at once [Archaic]", *presently* = "now [Obs.]" | headword |

### Period bilingual dictionaries

`period_dicts.py` looks up each row's lemma in English→Esperanto and English→Spanish dictionaries from around 1900. These record how the 1890s sense of a word was rendered at the time, independently of any one translator. The scans are on the Internet Archive and are public domain in the US (published before 1929). The OCR is kept in `cache/dicts/`, and only a short excerpt per row is committed.

| Column | Dictionary | Note |
|---|---|---|
| `dict_epo` | J. Rhodes, *The English-Esperanto Dictionary* (1908), and O'Connor & Hayes, *English-Esperanto Dictionary* (1907) | The OCR drops Esperanto accents (*baldaŭ* → "baldat"); the comparison by 5-letter stem tolerates this. |
| `dict_spa` | Velázquez de la Cadena et al., *A New Pronouncing Dictionary of the Spanish and English Languages* (1910), vol. 2 | It numbers the senses and labels old ones "(Ant.)", e.g. *presently*: "2. (Ant.) Inmediatamente". |

`dict_check` reports agreement separately for Esperanto and Spanish. `agree` means one of the period renderings, in any of the word's senses, shares a stem with the row's Globasa gloss. `differ` means the row should be reviewed. Because a dictionary lists every sense, `agree` is weaker evidence than agreement with a translator, but `differ` is a useful flag. For example, *insensibly* and *ungainly* both had two current senses around 1900, and in each case Wells's sentence decided which applies (see those rows' notes).

The critical editions are still under copyright and are not fetched: Geduld, *The Definitive Time Machine* (1987); Stover, *The Time Machine: An Invention* (1996); Ruddick (Broadview, 2001); and Bergonzi, "The Publication of *The Time Machine*" (*RES*, 1960). They are reading sources only.

## Victorian word list (source of truth)

**`victorian_wordlist.tsv` is the one file to edit.** It has one row per sense: an English headword together with one Globasa rendering. The dictionary page, its exports and the Apertium files are all generated from it, and nothing is read back from generated files. The per-work glossary (`obscure_resolved.tsv`) only supplies attestations, evidence and new candidates.

| Column | Meaning |
|---|---|
| `headword`, `eng_tags` | English lemma as the analyser gives it (*smite*, not *smote*), with its Apertium tags (`adv`, `n`, `vblex`; `mwe` for a phrase) |
| `sense` | the Victorian sense, in plain modern English |
| `glb`, `glb_tags`, `glb_how` | the Globasa rendering, its Apertium tags (`n.nt`, `vblex`, …) and how it was formed |
| `layer` | `period` / `rare` / `technical` |
| `apertium` | `pref` (gated preference), `add` (plain English→Globasa entry), `no`, or `pending` |
| `reason` | why that Apertium decision was made (required for `pref` and `add`) |
| `attested` | inflected forms seen in texts (*smote*, *beheld*) |
| `notes` | free text |

Scripts:

| Command | What it does |
|---|---|
| `victorian_wordlist.py sync` | Appends new glossary senses as `pending`. Their lemma and tags are seeded from the monolingual analysers and the layer from the verdict plus Webster 1913. Existing rows are never changed. |
| `victorian_wordlist.py check` | Validates the list. It errors on bad values or incomplete `pref`/`add` rows, and warns when an analyser lacks a word. That's only a warning, because the list is the truth. |
| `build_termbase.py` | Builds `victorian_glb.tsv`, `.json` and `.html` (the published page) from the list, with attestations from the glossary. |
| `termbase_to_apertium.py` | Builds the Apertium files from the list's `pref`/`add` rows (see the next section). |

Seeded on 2026-11-19 with 528 senses (245 period, 228 rare, 55 technical). The 99 Apertium decisions taken so far are recorded in `apertium`/`reason`; the other 429 rows are `pending`.

## Apertium preferences: `AP_SETVAR=victorian`

The English→Globasa pair (`GlobasaTranslation/apertium-glb-eng`) can now translate period traps in their Victorian sense. It uses Apertium's preferences mechanism (apertium ≥ 3.9, as in apertium-nno-nob). The bilingual dictionary holds both translations, and a constraint grammar run right after `lt-proc -b` (`eng-glb.biprefs.rlx`) keeps the modern one unless the stream variable is set.

```bash
cd GlobasaTranslation/apertium-glb-eng
echo "He will be here presently." | apertium -d . eng-glb                               # … nunli
echo "He will be here presently." | AP_SETVAR=victorian apertium -d . eng-glb           # … nerxali
echo "It was a queer thing."      | AP_SETVAR=victorian=presently apertium -d . eng-glb # only presently switches
echo "It was a queer thing."      | AP_SETVAR=victorian=-queer apertium -d . eng-glb    # all but queer
echo "It was a queer thing."      | AP_SETVAR=eng_variety=Victorian apertium -d . eng-glb  # = victorian
```

- **What is exported:** `termbase_to_apertium.py` exports the word list's `apertium=pref` and `apertium=add` rows, using the list's own tags and never reading the dictionary. It writes:
  - the dictionary entries (`r="RL"`, English→Globasa only) in a BEGIN/END block above the `build_bidix` marker;
  - the CG file;
  - `eng-glb.preferences.xml`, installed as `prefs/eng-glb.xml`.
- **Approval rule:** the period sense must be the normal Victorian reading of the word. A lemma-level switch must not carry a sense that only fits one passage, such as *carriage* → posture or *company* → crowd. An ungated addition must not mistranslate modern text. That excludes *ever* → always and *scarce* → hardly, for example. *fancy* needs a modern rival entry first.
- **First export:** 7 preferences (*presently, queer, curious, awfully, frightfully, apartment, purpose* as a verb) and 12 new English→Globasa entries for words that had none (*smite, behold, bough, feign, meddle*, …).
- **Victorian as a variety of English:** for English→Globasa input, `eng_variety` offers `GB`, `US` and `Victorian`. `Victorian` is the same as `AP_SETVAR=victorian`, and the translation aide shows it in its English-variety menu. The separate `victorian` preference stays declared for per-word selection from the command line. Globasa→English output offers only GB and US.
- **Shared with the English-variety preference:** Victorian English is British English. The British-sense rules for English input (*fall* ≠ autumn, *gas* ≠ petrol) are generated once, by `eng_variety_to_apertium.py` (repo root), from `eng_variety_patch.tsv`. They fire for `AP_SETVAR=eng_variety=GB`, for `eng_variety=Victorian`, **and** for any `victorian` setting. Each generator writes its own fragment: `apertium-glb-eng.eng-glb.victorian.rlx` and `….variety.rlx`, plus `eng-glb.victorian.preferences.xml` and `….variety.preferences.xml`. The pair's Makefile concatenates them into `eng-glb.biprefs.rlx.bin` and `prefs/eng-glb.xml`, which declares both `victorian` and `eng_variety`.
- **What doesn't fit:** multiword expressions, period grammar and words missing from the English analyser are outside preferences. In current Apertium only constraint grammar reads stream variables. Those go to the multiword module, to rtx rules that only fire on archaic patterns, and to apertium-eng respectively.
- **Regression check:** with `AP_SETVAR` unset, all-dev output is identical (0 of 1,117 lines changed). all-test changed only on *dad*, so an lrx default was added for it. chrF is 57.6 on dev and 57.8 on test.
- **Caveat:** 1,321 ambiguous English lemma+POS pairs in the pair have no lexical-selection rule, so their default is transducer order and can flip whenever any entry is added.

## Regenerate

```bash
python3 time-machine/fetch_texts.py            # network; Wikisource API
venv/bin/python time-machine/scan_obscure.py   # needs spacy en_core_web_sm, wordfreq, WiktionaryLMDB
venv/bin/python time-machine/check_resolved.py # coverage, fields, Globasa tokens vs word-list

# translations (cache/ only)
python3 time-machine/inko_text.py time-machine/cache/amos.pdf time-machine/cache/amos_epo.txt
python3 time-machine/ocr_spreads.py time-machine/cache/albroi.pdf spa time-machine/cache/albroi_spa.txt  # ~1 h
venv/bin/python time-machine/align_translations.py epo time-machine/cache/amos_epo.txt
venv/bin/python time-machine/align_translations.py spa time-machine/cache/albroi_spa.txt
python3 time-machine/merge_evidence.py
python3 time-machine/witness_variants.py       # holt_/atlantic_variants.tsv + glossary columns holt, atlantic
venv/bin/python time-machine/telltale_witness.py  # Siri-Logane Tutum chain
python3 time-machine/fetch_sources.py           # PD primary sources + Webster 1913 (cache)
python3 time-machine/period_dicts.py            # Rhodes/O'Connor/Velázquez → dict_epo, dict_spa, dict_check
python3 time-machine/victorian_wordlist.py sync # new glossary senses → word list (pending)
python3 time-machine/victorian_wordlist.py check
python3 time-machine/build_termbase.py          # word list → victorian_glb.{tsv,json,html}
python3 time-machine/termbase_to_apertium.py   # word list → apertium-glb-eng (then: make in the pair)
```
