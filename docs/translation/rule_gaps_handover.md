# Rule-based gaps in the X→Globasa pairs — handover

Written 2026-11-26 at the end of a long session, for the next one. Goal set by the user:
**close every gap that rules, lists or small pretrained models can close, so that the errors
left in eng→glb, epo→glb and spa→glb are only the ones that need larger-scale machine
learning** (word sense, free restructuring, cross-sentence reference).

## 1. Ground rules for this work

- **Memory caps are not optional.** Every test that runs native Apertium tools or Node goes
  through `python3 web/test/capped.py …` (kills the process tree above `GLOBASA_MEM_GB`,
  default 40 % of RAM); native pipelines also get `ulimit -v`. An uncapped `rtx-proc` once
  pushed the machine into swap and forced a reboot.
- **Word-sense errors wait for a neural model** (contextual WSD), unless a lexical-selection rule
  is really obvious. Don't write lrx rules for *run → funsyon*, *leave → awidi*, *rule → regula*.
- **Rule tiers have zero false positives.** A pattern that can misfire (e.g. guessing bare
  relative clauses from tags) waits for a parser.
- **Commits:** atomic (only files changed in lockstep together), author `Paleos
  <Paleos@paleos.me>` via `git -c user.name=… -c user.email=…` (no global git identity in the
  sandbox), `Co-Authored-By` trailer. Commit and push only when asked. Pairs are separate repos
  (`apertium-glb`, `-eng`, `-fra`, `-deu`, `-nld` are submodules of the main repo; `-epo`, `-spa`,
  `-jpn` are not).
- Curated data lives in one editable list; Apertium files are generated from it, never read back.
- Measure every change: per-sentence native runs before/after on the gold, chrF via the pair's
  `test/score.py` function, plus the parity test for the browser (§3).

## 2. Where things stand (all committed locally, not pushed)

- **Browser translator** `web/` (README "Browser translator"): the pairs' processors as one
  WebAssembly binary, Python steps in Pyodide, output byte-identical to
  `apertium -d <pair> <mode>` for all 13 modes. English→Globasa has an in-browser PoS tagger
  (stanza combined + gum, non-transformer, ONNX) answering `eng-glb-neural.py pos`.
- **eng→glb fixes this session:** context-aware `prune()` (PRON→prn, VBG verb unless prenominal,
  preadv only before JJ/RB); `so<cnjadv>` → *celki*; unknown NNP → name; name case duplicates;
  `np n` NP drops *the*; adverb/verb spacing; hyphenated compounds (rtx `HAJ`, CG, mwe split).
- **All X→glb pairs:** `apertium-glb/glb-pregen.py` before generation: *-mo* only before
  adjectives/adverbs (Xwexi rule), names written as text.
- **epo/spa grammars:** `SEQ sent` → `SENT` (multi-sentence rtx blow-up).
- **User gold:** `GlobasaTranslation/apertium-glb-eng/test/eng-glb-curated.tsv` (committed, own
  text). Current eng→glb with the browser tagger, chrF: curated 83.2, UDHR 48.8, P&C 52.7,
  Tell-tale 71.1, Thirty 65.0 (60 lines per set).

## 3. How to measure

| What | Command |
|---|---|
| Browser = native, all modes | `cd web && python3 test/capped.py node test/parity.mjs` (`PARITY_N`, `PARITY_STEPS=1` finds the first divergent step) |
| eng→glb with/without browser tagger | `python3 test/capped.py node test/tagger_quality.mjs 60` |
| eng→glb construction gaps | `python3 test/capped.py node test/gap_dump.mjs /tmp/x.jsonl && python3 test/gap_report.py /tmp/x.jsonl` |
| epo/spa construction gaps | `python3 web/test/capped.py python3 web/test/gaps_native.py epo /tmp/epo.json` |
| One pair's gold | `python3 test/score.py <mode> <gold.tsv> -v` inside the pair |

After changing a pair: `make` in the pair (after editing `Makefile.am`: `autoreconf -fi && ./configure`
first; restore the tracked `configure~` with `git checkout -- configure~`), then
`web/build.sh --no-wasm` so the browser bundle picks it up. Node: emsdk's
`/media/paleos/Warehouse2/Language/Claude/wasm/emsdk/node/24.19.0_64bit/bin` (system node is v12).

## 4. English→Globasa (1,052 dev sentences, browser pipeline + tagger, mean chrF 61.7)

Sentences affected → what is needed. Examples are MT → gold.

| Gap | n | Example | Fix | Where |
|---|---|---|---|---|
| Possessor = clause subject → *sesu* | 99 (gold) / 0 (MT) | *Insan jwan etesu kef* → *sesu kapi* | needs the clause subject: **browser dependency parser** (stanza small English parser, exported like the tagger); desktop parse stage already has `stage_se` | `web/tagger/`, `glb-neural.py` |
| Generation `#` (wrong tags out of transfer) | 103 | *could* → `#u abil`; *when* → `#denwatu` (gold *denwatu hu*); *more* → `#max`; *then* → `#xafe`; `#prprs` leaks | bug fixes, one by one (trace with `apertium -d . eng-glb-transfer`) | rtx, bidix tags |
| Phrasal verbs (RP) | 47 | *jagegi @up* → *jagecu*; *cudu @up* → *estaycu*; *haha to @off* → *haha tem to* | verb + particle as one unit: apertium-separable (`lsx`) rules + bidix entries; list as one editable TSV | `.lsx`, bidix |
| 's genitive | 41 | *Oliver su kitabudom* → *Kitabudom de Oliver* | **user decision pending** (§7): the rtx deliberately does *X su Y*; gold uses *Y de X* in 40/41 | rtx `NNP` rules |
| *become/get/grow/turn* + ADJ | 22 | *Letus @become xohrapul* → *sencu xohrapul*; *getting worse* → *burcu* | rule: *sencu* + ADJ (lexicalised ADJ-*cu* where the word list has it) | rtx / mwe |
| Participle with no adjective entry | 30 | *@named Eko* → *namedo Eko* / *har name* | when the agreed tag is VBN/VBG and the adj reading has no bidix entry, use the verb participle (*-do/-ne*) | `prune()` / CG |
| Bare relatives, VBG/VBN clauses | ~59 | *nilto yu taypu* → *nilto hu yu taypu da*; *running entirely* → *na funsyon total* | parser (`acl:relcl`, `advcl`) | parser + `eng-glb-relative.py` |
| Title-Case headings | 14 | *@A Wise Seleti* → *Sofipul Seleti* | in a title-case line prefer the lower-case readings (capitalised adjectives are read as names) | CG / `stage_names` |
| Unknown *-ly* adverbs | 12 | `*intently`, `@widely` | derive from the adjective (bare t-word) | analyser side / mwe |
| Coordinated passive | few | *are compiled … and loaded* → *befuha* | an rtx attempt broke tense (`%` propagation) and was reverted; needs the participles tagged first | rtx `vv` |
| Small | 1–3 each | *Kam yu **am** aham mi?* (stray imperative), *let's* → *imi am*, *the most* → *maxim*, wh-words in situ | individual rules | rtx |

Dictionary work (not ML): content words with no bidix entry in 248 sentences (*food, trick,
scroll, noisy, bravery*); function words in 53 (*all → moy, others → alo ete, such, too, so,
once, anymore, alone, next*); analyser gaps in 49. Use the existing vetting pipeline.

## 5. Esperanto→Globasa (397 Vanege dev sentences, real direction, mean chrF 66.3)

**Word formation is the dominant gap.** 167 of 399 sentences (42 %) contain a word the analyser
does not know, scoring −19.7 against the rest. Examples: *blankas, puras, fieras, kontentas*
(adjective + *-as*), *videblas*, *bluaĵoj*, *vulparo*, *ĉirkaŭuloj*, *plendemo*, *iĝas*,
*malkresku*, *alportas*, *matene, unutage, espereble*, *sunlumo, ventpuŝoj*, *kovrata, nomata*.

The **word list is the source for the mapping**, richer than the gold: `LexiliAsel` gives each
derived word's composition (`abil + -ya`, `absurdo + -xey`) and `TranslationEpo` its Esperanto
gloss. Counting the gloss's affix for Globasa words with a given affix (word-list.csv, 9,524 words):

| Globasa | n | Esperanto (count) |
|---|---|---|
| *-cu* | 202 | *-iĝ-* 167 |
| *-gi* | 304 | *-ig-* 191 |
| *-ible* | 50 | *-ebl-* 46 |
| *-xey* | 60 | *-aĵ-* 44 |
| *-lari* | 28 | *-ar-* 20 |
| *-dom* | 66 | *-ej-* 46 |
| *-ya* | 357 | *-ec-* 175 |
| *-sim* | 37 | *-ec-* 29 |
| *-do* | 480 | *-it-* 403 (*-int-* 12, *-at-* 8) |
| *-ne* | 185 | *-ant-* 107 |
| *-yen* | 525 | *-ist-* 108, *-an-* 106, *-ant-* 95, *-ul-* 74 |
| *-ismo / -ista* | 32 / 22 | *-ism-* 31 / *-ist-* 20 |
| *nen-* | 71 | *ne-* 44, *mal-* 14 |
| *bur-* | 36 | *mal-* 9 |
| *re-*, *ri-* | 53, 21 | *re-* 34, 11 |
| *ex-* | 30 | *el-* 9, *ek-* 8 |

(Rough first-word heuristic; the next session should redo it properly over all gloss words and
both directions, and also extract **root pairs** — a derived pair *X+affix ↔ Y+affix* gives
*X ↔ Y* — which covers roots the bidix lacks.)

Proposed design (to agree with the user):
1. Generate one editable TSV `epo_glb_affixes.tsv` from the word list (affix pairs with counts
   and examples; the user curates), plus root pairs from derived words.
2. Analysis: a step after `lt-proc` (or lttoolbox compounding) that segments an unknown
   Esperanto word into root + affixes + ending using the apertium-epo lexicon, choosing
   segmentations whose root is known.
3. Transfer/generation: compose the Globasa word from the root's translation and the affix map
   (*vid-ebl-as* → *sen okoible*, *vulp-ar-o* → *rubahelari*, *blank-as* → *sen sefide*),
   checking the result against the Globasa generator, as `glb-pregen.py` does for *-mo*.
   Adjective + *-as* (*blankas*) → *sen* + adjective is a construction, not an affix.

Other Esperanto gaps:
- *esti* + participle → *be-* passive (*ne estis akceptitaj* → *no beswikara*; now *no sen swikara*), −16.
- *ju pli … des pli* → gold *Folki … max …* (now `*Ju max … *des max`).
- *kiam* as conjunction → *denwatu hu* (now *kewatu*); same gap as English *when*.
- Missing: *apud, ekster, je, for, ajna, iu-tage*.
- Generation `#` in 19 sentences: correlatives/determiners (`#un #den #nil #hin #ban`).
- *sia* → *sesu* already works (no parser needed: Esperanto marks the reflexive possessive).

## 6. Spanish→Globasa (492 sentences; caveat)

483 of the lines are Xwexi examples written in Globasa and glossed in Spanish (real direction
glb→spa, many glossary entries); only 9 Babel lines are spa→glb originals. Trust the error marks
more than the chrF ranking.
- Generation `#` in 43 sentences: `#prpers` (13, the indirect-object clitic doubled: *le dio su
  pan al hombre* — drop the clitic when the full NP is there), `#da` (13, resumptive *da* after
  non-relatives: *de modo que*, *más de ellos que*), `#<det>` (11: *unos a otros*, *lo que*),
  `#moy` (*todos ellos* → *moyete*), `#u` (*He aquí*).
- Analyser gaps: *-mente* adverbs, diminutives *-ito/-ita*, place adverbs (*arriba, abajo,
  debajo, atrás, detrás*), *cuántos, cuya, cualquier, ojalá* — derivation rules + entries.
- Possessor = subject → *sesu* (*le dio su pan* → *sesu roti*): parser, as English.
- *por/para*, *N de N* rank lowest but are glossary lines: sense and gold-direction noise.

## 6b. Session 2026-11-27: what was closed (all committed locally, not pushed)

Measured as in §3. eng dev (1,052, browser pipeline): chrF 61.7 → 63.5 (244 sentences better,
16 worse; sentences with # 103 → 37). Per set (60 lines, browser tagger): curated 83.2, UDHR
48.8 → 49.4, P&C 52.7 → 53.0, Tell-tale 71.1 → 73.7, Thirty 65.0 → 66.7. epo Vanege dev: 66.3 →
70.9 (106 better, 0 worse; # 19 → 4, unknown-word types 168 → 51). spa: 66.3 → 68.6
(48 better, 1 worse; # 50 → 10).

- **Shared, `apertium-glb/glb-pregen.py`:** doubled clitic recipients (`tas<pr><dbl>`, spa);
  `<j/>` targets split and spaced multiword lemmas written as text; particle prefixes the
  generator cannot write alone joined to the verb (exsokutu); composed words with `·`
  (rubahe·lari, a glued `·do` participle suffix) joined, unlisted ones written as text; a bare
  t-word adverb before an adjective takes -mo (pahnamo bukado).
- **eng:** could/might/want/can-not, when → denwatu hu (CG), more/less/how many, possessive
  pronouns (tesu tø, a friend of mine → misu), become/get/grow/turn + ADJ → sencu ADJ, participial
  adjectives and -ly adverbs (`dev/eng_word_formation.py` → derived bidix), phrasal verbs
  (`phrasal_verbs.tsv`, 112 from the word list; mwe keeps a `verb# particle` unit the bidix
  translates), Title Case headings, NP with several adjectives, function words from the word
  list, untranslated articles dropped in postformat. **CG bug:** `NOT 1* X BARRIER Y` is true
  whenever some non-X cohort precedes Y; every such test is `NEGATE` now.
- **epo:** determiners without a noun (unu el → un te/to of, CG det/prn), word formation:
  `dev/epo_word_formation.py` + `epo_glb_affixes.tsv` (77 affix pairs from the word list's affix
  entries; status column to curate): tag variants vbtr/vbntr (+ iĝi), derived lemmas, class
  conversions, compounds; analyser supplement in apertium-epo for lttoolbox compounding
  (`lt-proc -w -e`, `epo-glb-compounds.py` joins the parts after the bidix); closed-class words
  (krom, ekster, apud, kvankam, je, ajna, ju/des pli, iutage); negated passives.
- **spa:** clitics are never subjects (Te quiero → Mi vole yu), a-phrases (NOMA), todo, lo/el +
  de/que, algunos → banøtø, resumptive relatives, gustar variants, -mente adverbs
  (`dev/spa_word_formation.py`), cuyo, cuántos, closed-class words from the word list.
- Tracing tool: `web/test/trace.mjs "sentence" [step ...]` prints the browser stream after steps.

Left for the next session (rule/list work still possible):
1. **Dependency parser in the browser** (§4: sesu for possessor = subject, 99 gold; bare relatives;
   participle clauses). Note: `stage_se` in glb-neural.py is the Spanish *se* stage, not sesu —
   no sesu stage exists on the desktop either. Needs parse + coreference (his = the subject).
2. epo: verb on a noun root (matenas), sen + noun + a (senŝela), remaining compounds with a
   verb modifier (viandomanĝa); review the `check` rows of `epo_glb_affixes.tsv`.
3. spa: arriba/abajo/debajo/encima (no word-list entry), diminutives (-ito), impersonal se → ren.
4. eng: coordinated passives, let's, wh in situ, remaining content-word gaps (food, home, …).

## 7. Decisions for the user

Decided 2026-11-27: keep *X su Y* for 's; Esperanto word formation by lttoolbox compounding
(data generated from one TSV); a pretrained parser is allowed (no training). Open: the
`check` rows of `epo_glb_affixes.tsv` and the `alt` rows of `phrasal_verbs.tsv` (user curation).

## 8. What stays for larger-scale ML (don't try with rules)

Word sense (*Article → Mon*, *rule → regula*, *run → funsyon*, *on → per*, *feel → ganjon*,
*geo / Dunya*), free restructuring in the gold (*Ju pli … → Folki …* wording, paraphrase),
cross-sentence coreference beyond the focus stage, discourse-level tense choice.

## 9. Gotchas learned this session

- lt-proc matches regex entries (bidix and generator name regex) case-insensitively and returns
  both the written and a case-normalised form for inner capitals; `-c` breaks capitalised words.
- rtx-comp: every category used in an output pattern must be declared (`guio: _;`); all
  alternatives of a nonterminal must supply its attributes (`HAJ [$degree=pos]`); `%N` marks the
  child whose attributes go up — two `%` broke tense.
- The `apertium` wrapper started from Node cannot read stdin (destxt prints its usage): pass the
  input as a file.
- rtx `SEQ X` rules must never extend past `sent` (multi-sentence explosion).
- `std::sort` tie order differs between libstdc++ and libc++ (wasm uses a libstdc++ port).
- Penn tags *nothing/something* NN (UPOS PRON) and *so* RB; UD EWT splits hyphenated
  compounds (HYPH); the first part before a hyphen + participle is a noun (*Secret-Telling* →
  *Siri-Logane*, user correction).

## 10. Suggested order

1. Generation-error bugs in eng, epo, spa (cheap, frequent; each is a wrong tag).
2. *when/kiam/cuando* → *denwatu hu* (all three pairs).
3. Esperanto word formation from the word list (largest single gain).
4. *become* + ADJ, participle fallback, Title-Case headings, *-ly/-mente* adverbs.
5. Browser dependency parser → *sesu*, bare relatives, participle clauses (eng, spa).
6. Phrasal verbs (lsx + list), *esti/be* passives, *ju … des*.
7. Dictionary pass (eng content and function words; spa/epo closed classes).
8. 's genitive once decided.
