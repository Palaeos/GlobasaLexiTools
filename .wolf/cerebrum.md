# Cerebrum

> OpenWolf's learning memory. Updated automatically as the AI learns from interactions.
> Do not edit manually unless correcting an error.
> Last updated: 2026-09-03

## User Preferences
- [2026-11-09] **Seed tuples pick senses in their own editions (done, d7d7156; was 'next session, second step').** seeds.tuple_senses scores each seed's own-edition senses (wiktionary.senses_in) by how many OTHER seeds the table lists; the unique best is ticked, ties left to the user (en:pot+de:Topf+fr:cruche alone ties Topf 'kleines Gefäß'/'Kochtopf'; adding ru:горшок as a seed word breaks it). Words carry pivot_support; with >=2 pivots it is a rank tie-break AFTER methodology tie-breaks and fallback order (rank_key = families, tb, fb, pivots, langs), labelled data evidence. sense_fit sees non-en senses via wiktionary.english_view (bridge: English tables listing the seed AND named by an en translation in its table); no bridge -> 'meaning check skipped (fallback...)' note. OPEN: es/ru/ko editions are NOT built (user runs `JSONL parser non-English.py es|ru`); es seed is vasija (user confirmed 2026-11-09).
- [2026-11-09] **Historical Han for ko/vi (done, d6bef79 + a1caaef; was 'next session, first step').** Shown beside the word, in chips, LexiliAsel (user format: `Koreasa (기질 氣質 “gijil”)`, Vietnamese keeps its quoted roman) and the dossier, ONLY when another Sinosphere word of the cluster/concept shares the spelling: the hanja table lists every homograph (native 독 'jar' is not 毒/獨). Unconfirmed spellings: sources table only. LexiliAsel itself writes Han for ko/vi once (tosa: Koreasa (屠殺 “dosal”)).
- [2026-11-08] **Sources should be enabled conservatively; provide means to check dictionaries to investigate a word's meaning** (user). Done: sources table links each word to its Wiktionary entry plus an established dictionary per language (user: BILINGUAL for the interface language, English, first; foreign monolingual ones last and labelled: SpanishDict, WordReference, dict.cc, LEO, MDBG, Jisho, Naver English, VDict, Shabdkosh, Almaany, Abadis, Tureng, Glosbe; RAE, CNRTL, Duden, TDK, KBBI monolingual) and an "own-language senses" toggle (/api/entry). Etymology cognates are now OFF by default (user): concept "etym_cognates": true / checkbox "Also add cognates found by etymology" turns them on.
- [2026-11-08] **Show progress to the user while they wait** (user): the Word Selector page polls /api/progress during "Gather and propose" and shows the pipeline's current stage and elapsed seconds (pipeline.run(progress=...) reports each stage and the cluster count during proposals). Apply to any new long-running page action.
- [2026-11-08] **Borderline judgements belong to the Globasa development team** (user, on yew: whether yew ~ 주목 counts as false-friend agreement). The tool does not decide them: pipeline.team_questions() detects a winner whose agreement rests on support at distance SUPPORT_BORDER 0.258 (90th pct of cited etymons) .. 0.30 where the ranking changes without it, and presents the question with both outcomes on the page (section 4) and in the dossier ("Questions for the development team").
- [2026-11-08] **The Word Selector page must let the user read the methodology passages that justify each ranking** (user): every cluster and proposal has a "Why: methodology" panel quoting the passages, with a reader drawer opening them in context; steps resting on lexicon data / precedent / fallbacks are labelled as such, not presented as methodology.
- [2026-11-08] **Fallbacks must be marked as such** (user): any secondary source or predicted value carries "(fallback: why)" in flags / forms_how / blend notes; word_selector.html shows notes containing "fallback" as flags. **Follow the real pronunciation** (user) for Arabic/Persian, not LexiliAsel spelling readings: pipeline.PRONUNCIATION_ORACLE = {"fa"}. **Preferred: a comprehensive vocalization dictionary** for Arabic and Persian over predictions.
- [2026-11-07] **Shorthand design calls (user):** ink may cross itself only inside one letter (a loop or circle); any contact between the ink of different letters is penalised, apart from the joint where letters meet (refined 2026-11-07, replacing 'crossing is a feature'). Messy pile-ups of ink are explicitly unwanted. Commoner letters get simpler shapes first (line < semicircle < circle < loop; SIMPLICITY_ORDER_MS), then shorter strokes among equals (SIZE_ORDER_MS): a long simple stroke beats a small complex one. Priority: fast frequent joins come before the simplicity/size ordering, so both orderings are soft (weight 200). No two letters share a sign except s/z (user); minimal-pair-protected pairs (l/r, b/p, f/p, c/j, c/x, h/r) may only have *similar* signs, to forgive sloppy penmanship (SIMILAR_OK). Similar pairs are charged by legibility impairment: SIMILAR_MS_PER_PCT x (context-free misreading % + future risk graded by the methodology tiers: never v/w (= v vs u sign), s/z, final m/n -> 0 (m/n 0.03 as only final); whenever-possible l/r b/p f/p c/j c/x h/r -> 0.02; other 0.05). The methodology also protects +/- a segment at word edges (never except last resort; vowels 'whenever possible'). Misreading ranges from 0 (29 of 231 pairs, e.g. c/x) to 2.6% (e/o); m/j 2.35% (mi/ji), t/f 2.27% (te/fe). Similar must mean genuinely fragile distinctions only (circle turning direction, 45-degree loop/semicircle rotation, curved size); counting line directions or line sizes made nearly every pair 'similar' and wrecked joins. Quarter arcs are not letters, only a join rule (rounded blunt joins, ROUNDED_MS); dropping them as letters cost nothing in the search. No composite signs (circle + another shape) for one sound; Globasa has no digraphs, so Orthic's compound characters and ligatures don't apply. Relying on semicircles is bad because rotated copies of one shape give too little variety; the optimizer's VARIETY_MS term encodes this. Longhand/Orthic-style loops are allowed (for l, r, b or anything else). Superficial likeness to Latin letters is a tie-breaker only (LATIN_MS = 2; 4 ms already cost 4% elsewhere). Big and small circles are also allowed as letter signs (added 2026-11-07); their use hinges on the circle time estimate, which only the user's own timing can settle.
- [2026-11-05] **Shorthand baseline use case, in the user's framing:** used like cursive traditionally, as an everyday hand, but with an actual writing-speed advantage. Benchmark it against normal handwriting.
- [2026-11-05] **Print script goal:** compactness and ease of reading books. Small glyphs must be simple to justify their size. User finds serif type more pleasant in books but suspects familiarity.
- [2026-11-05] **Shorthand also needs a reporting tier built on abbreviations** (user request), layered on the baseline; full outlines stay valid. The baseline itself stays free of word lists for everyday handwriting.
- [2026-11-05] **Shorthand scope:** the baseline must suit quick, low-friction everyday handwriting as well as note-taking, so it should not depend on abbreviation lists or a reporting tier. Weight corpus sources evenly for its statistics.

- [2026-11-04] For decision models that do not know Globasa, keep Globasa out of the context window unless needed, and give argument lists as translations only. Spend the tokens on English, Esperanto and Spanish.

- [2026-11-04] For decision models that do not know Globasa, keep Globasa out of the context window unless it is needed: spend the tokens on English, Esperanto and Spanish.

- GenderResolver.py resolves natural Globasa gender for anaphora, not grammatical gender of European language nouns
- When the resulting .xlsx is corrupted or missing, check for a backup file first before falling back to a .tsv (applied to Wiktionary sense extender v3)
- For sense applicability judgements: always err on core meanings; extended/figurative senses must be corroborated by corpus (Qdrant). WordNet synset judgements (GLB_ENG_WordnetSynsets.tsv_) are unreliable — don't use for scoring.
- Globasa targets core/universal meanings; slang, archaic, domain jargon are generally NOT applicable
- Vetting uses a single 'Tier' column (letters: e=Expert, v=Vetted, l=LLM, a=Script). Higher tiers overwrite lower. Old format (separate Script?/LLM?/Vetted?/Expert? columns) is handled for backward compatibility during loading.

- [2026-10-25] **Anki cards follow the minimum information principle: never make the learner recall a verb AND its class at once.** Meaning cards (Rukone/Produti) ask and answer with the bare verb, modelled on the feeling/state (Hisili/Jotayli) cards: "swim" -> "▯ suyon", never "▯ suyon (suyon)". There is exactly ONE verb-type card (user: "just one verb type card"), "Verb Type", prompt "nenhar ojeto?": "▯ X" -> the frame equivalent to a plain intransitive: "▯ suyon suyon", "▯ buka(cu)", "▯ pilo = ▯ sen pilodo", "▯ idi (no -cu)". A separate Verb Class card (word -> class name) was built and REJECTED; so was a yes/no Optional -cu card. No question side may reveal echo-object use or optional -cu. User chose the explicit "(no -cu)" answer over answering a plain intransitive with its translation: less cognitively taxing.

## Key Learnings
- [2026-11-09] **Kijitu is the user's expected answer for 基質 (matrix, geology): a regression test now (tests/test_sino_precedent.py).** To bisect the Word Selector, `git archive <commit> word_selection | tar -x` into a scratchpad dir with every other repo entry symlinked beside it (precedent/lexicon data resolve relative to the package), then run with sys.path.insert(0, dir). Before changing precedent/coda logic, compare per-root top-1 against HEAD on all LexiliAsel roots (oracle mode), not only the total: losses hide inside a flat total.
- [2026-11-08] **vaso "pot, vessel" (user asked for an assessment).** Its cognates (en vase, de Vase, ru ваза, tr vazo, id vas, fr vase) mean VASE (a flower container), a narrower kind; only Spanish vaso (secondary sense "vessel (container)"), French vaisseau (ship, blood vessel) and the further-support words (Arabic وعاء, Vietnamese vò "jar", Indonesian pasu "container") carry the general meaning. Esperanto merges vazo/poto/kruĉo. Left to the development team. Gap: sense_fit does not detect narrowing to a specific kind (hyponym), only "unattested" (flag).
- [2026-11-08] **Homonymous English headwords (user: miza for the Mass leaned in part on Greek μάζα, physical mass; too stuck to change now).** English mass is two words: Mass < OE mæsse < Latin missa, and physical mass < Latin massa < Greek μᾶζα. Two traps, both fixed: (1) sense_fit: when the headword has other senses, a gloss naming it must show WHICH: target-sense words (incl. same-domain senses, judged against the ORIGINAL target words so the domain cannot snowball; drop filler words especially/now) attest; other-sense words (physics, matter, lump) = homonym (no agreement); bare gloss = ambiguous (flag) unless the target is the headword's most-translated sense (bear) ; capitalised headword in the gloss (Mass) names the capitalised sense when en Wiktionary has a capitalised entry for it; the headword itself is never evidence (mass ~ massive). (2) add_etym_cognates followed every entry's etymology (lookup() merges entries), dragging in maza, massage, massive, Michaelmas, Michael, ميكائيل -- the tool reproduced the miza mistake; now sense_fit.etymology_for_meaning follows only entries that carry the meaning (for the concept's English headword only entries of its POS: the adj "mass of people" shares physical mass's etymology); etymology cognates whose own entry does not carry the meaning are left out by default (tag default-out, tickable). Result: religious Mass -> clean missa cluster (弥撒, Messe, messe, misa x5; 6 families) -> mise/mese/masa.
- [2026-11-08] **Meaning must be attested in each source's own entry, not inferred from a translation table (user: nicode -> bopu).** nicode "squeeze" came from Hindi निचोड़ना, whose own entry says "to extract by squeezing, squeeze out" (wringing), not Epo kunpremi; replaced by bopu < Vietnamese bóp "to press (with hands)", Thai บีบ. Word overlap gets both wrong (Hindi says "squeeze", bóp says "press"). sense_fit.py reads gloss STRUCTURE: head word = concept word or near form of a definition word -> attests; concept word only with a particle (squeeze out; unless the concept has that particle) or after by/with (means) -> shifted. Only "shifted" stops a word counting as agreement (pipeline.check_meanings -> _support); "unattested" is a flag only, because synonyms say the same (comprimer "to compress"). Squeeze test: only निचोड़ना is shifted; its cluster counts 0 families. The flags also catch junk table entries (kana ね/が, es casco "helmet", quejarse).
- [2026-11-08] **Initial affricates are no cluster for e-**: no root begins with dz-, ts-, edz- or ets-; Mandarin dz- -> z (zira, zaxi, zungu; also s, j), ts- -> s (sangu, saypan, sunami; also c). form_rules.normalize writes dz-/ts- as z-/s- (紫杉 dzixan -> zixan, not edzixan). Leave-one-out: all 30.8 -> 30.9, sino 20.5 -> 20.7 (top-3 37.1 -> 37.6).
- [2026-11-08] **False friends count (user: baru < bear + Hindi balu).** Source agreement is by SOUND, not etymology. LexiliAsel baru cites Hindi balu, Indonesian beruang, English bear, German Bär: pairwise 0.15-0.29, up to 5 edits apart (so an edit-count cluster guard would break it). pipeline.agreement(): a cluster's languages count only if a member lies within distance 0.30 of its BEST proposal (95th percentile of cited-etymon-vs-root distances; median 0.11; baru~beruang 0.21); members that are only etymology-cognate guesses never count; select.rank re-ranks on this support and the why lists loose/unverified members. Bridging blends (blend each pair of families) were tried and REMOVED: zarnar sits as close to Arabic zarnab and Persian sorhdar as baru to balu and bear, so distance cannot tell a false pair from a false friend. Results: bear -> bear/Bär/balu/beruang cluster (3 families) over Arabic/Swahili dubu (an "en dubb" etym-cognate guess had given it a European family); yew -> en yew + ko 주목 (yumoke) as a false-friend blend ahead of the Mandarin 紫杉 fallback (a judgement call for the user); Persian sorhdar no longer joins Arabic zarnab.
- [2026-11-08] **Taxon search (user: biological names find same-meaning candidates; the words need no Greco-Latin basis).** sources/taxon.py: Wikispecies API (species.wikimedia.org reachable; {{VN}} may be one line or many: brace-match + top-level pipe split), Wikipedia langlinks of the taxon (redirect Taxus -> Yew article), English Wiktionary senses whose definition names the taxon -> their tables. Rank from the name (binomial = species; -aceae/-idae family, -ales order ... else genus); rank markers removed only for the taxon's own rank (Korean 서양주목 keeps 목; 주목속 -> 주목; 属/屬/속/chi; families also tr -giller, de -gewächse, ru -овые, fa -یان). **Wikispecies uses plurals for broader taxa (user)**: plurals.py (721,883 forms from the raw en dump, 154 s; the concept index has no form-of entries). Scientific-name Wikipedia titles (vi/id taxus) are excluded by default (concept "included" overrides): they otherwise manufacture family agreement. Yew test (Taxus): candidates yew, Eibe, tejo, if, тис, 紅豆杉/紫杉, イチイ, 주목, طقسوس/طخش/زرنب, سرخدار, porsuk; no real cross-family agreement, but two FALSE clusters win (fa sorhdar ~ ar zarnab d=0.293, en yu ~ ko jumok d=0.30) -- short/divergent forms under the 0.30 threshold. Blanket edit-count guard rejected: root-cluster recovery 80.2% -> 68.0% (0.6) / 47.5% (0.5). Expected methodology outcome with no agreement: fallback order, Mandarin two-character 紫杉.
- [2026-11-08] **Cultural words and proper nouns (user: Unix).** Grammar (xwexi abece-ji-lafuzu): proper nouns (C)(C)V(C)(C), any final consonant, codas of 2 even word-finally (Madrid, Polska, Budapest), double stops, iy/uw/wu/yi allowed; culture-specific words = ordinary rules word-finally, proper rules elsewhere (teriyaki, koktel, bakgamon, blakjaku, jazu, vodka, futbal; final -ng -> -ngu: yinyangu). collision.phonotactics(w, kind) and form_rules.shape(kind=). Their form follows the source, not a blend. **Check each language pronunciation** (user): German writes Unix but says [ˈjuːnɪks], French \y.niks; German/French Wiktionary editions (raw dumps /media/paleos/Warehouse2/Language/raw-wiktextract-data-{de,fr}.jsonl) indexed by pronunciation.py; Turkish table roman (yuniks) beats spelling; Latin-script spellings in ja/cmn read as English only as marked fallback. For ORDINARY words Latin-script languages keep spelling (checking every de/fr pronunciation cost 4 roots: parti/vaselin/sabotaje -> paati/vaslin/sabotas). **Spelling vs pronunciation reading of a Latin-script source** (user: Globasa leans on spelling for recognizability, but Yuniks wins because Russian/Arabic loans carry the pronunciation): rank both readings by languages whose checked (non-fallback) form matches; tie -> spelling. Unix: Yuniks (ar de en fa hi ko ru tr) over Uniks (fr). User: Unix is a pun on eunuchs (Multics -> UNICS), so its sound is its identity, and the Globasa wiki renders Utah as Yuta (methodology: English long vowels follow the pronunciation); proposals cite both. Some etymology triples in the concept index are shifted ([Multics>Q739186, Multics, Q739186]). Roots: C+u /Cjuː/ written u 7 vs yu 1 (tuna, tubo, komunika); eu- -> ew (ewropyum). German x -> ks (Globasa x is /ʃ/). Method docs source: github.com/Globasa-Team/main-pages-grav 10.max/*.eng.md (globasa.net itself is egress-blocked).
- [2026-11-08] **Vocalization dictionaries (user: prefer a comprehensive dictionary; code is open source, repo MIT).** Arabic: Camel Morph MSA v1.0 (CC BY 4.0) STEMS section -> 32k bare-lemma keys; lex carries sense suffixes (_1, _2: strip them); verbs lack the final fatha (add it: LexiliAsel cites faʕala); vowel marks in the word outrank the dictionary; only a sense-specific translation-table roman (not the entry first roman) may choose among readings, else gloss overlap with the concept, else POS (nouns first) + lex_logprob. Unvocalized LexiliAsel Arabic (484): dict 238 exact vs Wiktionary 187. Persian: KaamelDict (116,630 entries, GPL -> word_selection_cache/ only, which is now in .gitignore) covers 1378/1679 LexiliAsel etymons (Wiktionary 1310); first variant = Wiktionary 82%, any variant 91%; Wiktionary reading picks the variant. Arabic ث -> t (LexiliAsel 17 t vs 5 s; translit ar 85.7 -> 86.5%). Oracle all 30.8 -> 30.9%, e2e ar/fa 33.7 -> 34.3%. Remaining gap: ~145 Arabic loanwords absent from MSA lexicon. Rejected sources: tihudict (only a demo file public), amirkaveh/persian-words (scraper only), kiasar (no license), persian_phonemizer (Mo in-derived). HomoRich-G2P-Persian is CC0 (sentence-level). `gh` on this machine is gitsome, not GitHub CLI: use curl api.github.com.
- [2026-11-08] **Perso-Arabic transcription coverage.** (1) Persian entries list Classical/Dari romanization first (kitāb), Iranian second (ketâb): lookup() now ranks Iranian first (50 words: 86% exact). (2) 725/726 formless Persian etymons have NO English-Wiktionary entry, but 357 appear in translation tables with tr=: lookup() falls back to table_romans() (fa no-input 726 -> 369). (3) abjad.vocalize_from_cognates: the script gives consonants, a cognate (Turkish for European loans; no Turkish otherwise: its vowel harmony gives edeb/elmas for adab/almas) gives unwritten vowels and mater quality; no vowel insertion before the first or after the last letter; fa final ه = -e, ar ة = -a; ar و/ی only u/i. Held out vs Wiktionary: ~52% exact, ~80% within one edit; FIT_MAX 0.15 (true kept fa 84 / ar 71%, random-root false fits 0.1 / 0.0%). Wired into pipeline.predict_vocalizations (after the ar<->fa skeleton prediction, flagged "check it") and e2e _members_for_root. e2e ar/fa roots: members with a form fa 953 -> 1639, ar 1184 -> 1333; top-1 33.8 -> 33.4 (noise, 29 wins / 38 losses), top-3 56.4 -> 56.9. **LexiliAsel Persian romanizations of European loans are naive spelling readings** (کبالت kabalat, تالنت talanat, و always u: kula, kazinu) where Wiktionary has the pronunciation (kobâlt): table-roman "errors" are mostly gold noise.
- [2026-11-08] **Ancestor-centred Sino-xenic alignment (sino_align.py): correct alignments, neutral on its own.** Leave-one-out sino top-1 19.4 -> 19.4% (top-3 35.3 -> 35.5); with precedent off 14.7 -> 14.3%. Majority votes rarely change with column placement; its lever is precedent learned on it. Misses on 434 Sino roots: 108 (25%) gold >2 edits from EVERY source (blend constraint excludes them: benjunfo = ben + jun(ko) + fo, a per-syllable blend), 103 in top-5, 138 reachable but not proposed. Precedent MARGINAL (count each column under its sub-patterns, so backoff finds supersets) is a wash (all 30.4 -> 30.3; jako +1.2, indic -1.5, sino -0.7) and stays False. **Spelling norm n -> m before b/p** (roots: mb 36, mp 36, nb/np 0) in form_rules.normalize: all 30.4 -> 30.7%, sino 19.4 -> 20.5% (top-3 36.9), no group loses. align() boundary row/column now honour the coda hook (they charged a flat edge gap). Full eval: 3057 roots ~2 min per config (run two in parallel).
- [2026-11-08] **LexiliAsel precedent for Sino-xenic forms (user: prioritize it).** word_selection/precedent.py learns, from roots whose Sinosphere etymons share a Han spelling, which letter Globasa took where cmn/ja/ko/vi disagree (exact pattern, then letter-class layer 'follow language X'): cmn j/ja k/ko g -> k (follows ja, 7 roots 86%); cmn -ng vs ja nothing -> dropped (13/13); cmn a,u vs ja/ko o -> o; cmn x/ja s/ko s -> s; cmn l/ja r/ko r -> l. blend.candidates puts the precedent letter first and penalises departures (PRECEDENT_PENALTY 0.15/position). Safeguard: if a Japanese member is katakana, only Han-spelling-confirmed members follow precedent (loans), else all Sinosphere members. Leave-one-out: Sino-xenic roots top-1 13.2% -> 20.4% (top-3 30.6 -> ~35%), katakana-loan roots unchanged 31.5%. Katakana-loan Japanese/Korean pairs follow different rules (ja r / ko l -> l).
- [2026-11-08] **Precedent generalised to groups, within the methodology (user).** precedent.py groups: sino (cmn ja ko vi; katakana -> Han-confirmed only), jako (ja/ko with katakana ja), arabic (ar present; ar fa tr sw hi id), indic (hi te id), european (>=3 of en es fr de ru). Learned from the pipeline's own member forms (_members_for_root). Methodology order (Methodology for Lexical Development _ Globasa.html, in repo): caveats (applied later by form_rules/collision) > blend within 1 (2 close) phonemes > language-specific rules (Mandarin 'particularly Japanese', -ang -> o; Arabic au -> o; European spelling) ~ precedent > generic letter preferences ('all else more or less equal'). Precedent never touches the WORD-FINAL VOWEL SLOT (a posteriori/a priori vowel, caveats 1-3, Arabic -u are form_rules'). Leave-one-out top-1, 3057 roots: all 26.8 -> 30.6; sino 15.0 -> 20.0; jako 31.7 -> 36.9; arabic 31.1 -> 36.0; indic 30.2 -> 35.4; european 28.8 -> 33.0.
- [2026-11-08] **Han-spelling cognate completion (pipeline.add_han_cognates).** Japanese Sino-xenic words are often absent from English Wiktionary (ja 基質 has no entry, no table); Japanese Wiktionary (WiktionaryLMDB_ja senses) attests them. Sources now gain same-spelling cognates in missing Sinosphere languages, flagged; ambiguous ko/vi homographs (기질: 氣質/器質/基質) propagate only spellings another concept word confirms. sinosphere.words_spelled/surface_forms handle simplified and shinjitai forms.
- [2026-11-08] **Disambiguators stripped at source merge (user).** sources.strip_disambiguator removes trailing (…)/（…） from EVERY gathered word (Wikidata labels/aliases kept them: خمیره (زمین‌شناسی), Matrix (geology)); words merge on the bare form, titled forms kept in w['titles'] and shown on the page as 'as titled'. Wikipedia titles were already stripped in wikidata._title_word.
- [2026-11-08] **Sino-Japanese coda vowels are not a-posteriori vowels (user: kiju is wrong).** In 基質 kishitsu the -tsu is epenthesis after Middle Chinese -t (kicit; Korean gijil keeps -l); form_rules.ending_votes now counts a Han-spelled, on'yomi Japanese form ending in -tsu/-chi/-ku/-ki as voting 'no final vowel' at full weight. Katakana loans keep -u at half weight (EPENTHETIC), as the methodology lists Japanese -u among a-posteriori vowels. kiji itself is WARN by the methodology caveat: minimal pair +/- consonant at the beginning with iji (also fiji, kiwi, keji).
- [2026-11-08] **Middle Chinese coda options (user: offer whenever a reflex occurs; generalise).** precedent.CODA_REFLEX: -t (ja tsu/chi, ko l, vi t), -k (ja ku/ki, ko k, vi c/ch), -p, -m, -n, -ng. LexiliAsel precedent (>=2 languages showing the reflex): -t 9 roots: -tu 5 / dropped 4 (never -l, never -tsu); -k 30: -ku 18, -ki 5, dropped 5; -p 5: dropped 4, -pu 1; -m 10: -m 6, -n 4; -n 73: -n 64; -ng 53: -n 35, -ngu 8, -o 6. form_rules.shape offers the renderings on the BEST blend only (pipeline passes coda=(i==0)), penalty CODA_BASE 0.15 + 0.4*(1-share) (+0.15 if one language only); renderings need >= 3 roots except the stops' a priori -u. Unrestricted versions crowded the list and gave one-syllable roots (byen, nyan, em) two-syllable rivals; final: Sino top-1 19.6 -> 19.8%, top-3 35.5 -> 35.3%. 基質 -> kijitu (CLEAR) first.
- [2026-11-08] **Middle Chinese finals come from the Baxter reading (user: 級 kyū's -u is the -p; Mandarin ji lost it).** sinosphere.mc_finals(spelling) reads the last character's final (級 kip -> p; 質 tsyit/trijH ambiguous). precedent.codas_shown: an unambiguous reading decides (also rules out false Japanese -ku/-ki triggers), an ambiguous one lets surface reflexes choose; Japanese final vowel counts as the -p reflex; Mandarin ending in a vowel after a stop counts as 'cmn lost it'. form_rules: Sino-Japanese final vowel votes no-vowel when the final char had -p (or -tsu/-ku with -t/-k); Mandarin's vowel after a lost stop is labelled 'Mandarin's own vowel, its MC -X lost', not an a-posteriori vowel. Precedent with MC-qualified roots: -p 13 roots: dropped 12 / -pu 1; -t 15: dropped 11 / -tu 4; -k 44: dropped 19 / -ku 18 / -ki 5; -m 23: -n 12 / -m 10; -ng 71: -n 45 / -ngu 12 / other 11.
- [2026-11-08] **Calque stage (word_selection/calques.py; user: select calques systematically, as milkodao was).** Parts: concept-index `parts` table (459k compound/affix templates from the raw dump, with part glosses), Han characters, phrase words; glosses -> Globasa ROOTS via word-list English items (a part supports every root its glosses map to; roots led by the matching item first); head by language (head-final en de ru cmn ja ko hi te tr, Sino-Vietnamese; head-initial es fr ar fa id sw vi). Count INDEPENDENT COINAGES, not languages: Sinosphere words sharing a Han spelling = one (銀河 borrowed), a Wiktionary-marked calque/borrowing joins its model (Persian راه شیری calque of French). This reproduces milkodao: head dao in 3 coinages (Europe+Persian, Arabic, Telugu star+path) beats nahir (Sinosphere once, Hindi). Globasa compounds = plain concatenation modifier+head (986/987 two-root compounds). Eval vs lexicon compounds (842 with an English table): first 21.3%, top-3 27%, top-20 ~38%; misses: wrong English sense chosen, Globasa-internal coinages (aksyonlari), homograph glosses (شیری milk/lion).
- [2026-11-08] **Etymology cognate gathering (dukkha, nirvana, karma, wuwei).** concept-index `etym_reverse` (174k etymons; build took 33 min, disk-bound) maps an etymon to source-language descendants (bor/lbor/der/translit/psm, inh only from sa/pi/pra; Sanskrit n-stem ~ nominative). pipeline.add_etym_cognates follows etymons for 2 rounds (en dukkha -> pi dukkha -> id duka -> sa दुःख -> hi, te), max 3 per language, skips etymons with >40 descendants, flags 'check the meaning' (karma also reaches hi कमाना 'to earn'); then add_han_cognates extends to the Sinosphere (涅槃 -> 열반). Han variant normalisation now maps to kyūjitai for all languages (為 -> 爲). Korean 무위 / Vietnamese vô vi have no hanja/chữ Hán or entries in the local data, so wuwei stops at cmn/ja.
- [2026-11-08] **Word Selector Sino-xenic clustering (user-directed design).** Han spelling decides first: same normalised spelling joins outright; two known different spellings stay apart (except a one-char variant, e.g. 蒸留/蒸餾, which may use the phonetic route). The phonetic Sino route (MC correspondences + optional ja/ko/vi coda/assimilation variants + MC/Cantonese pivots + SINO_MARGIN 0.07) is only a fallback when one side's spelling is unknown. Native readings (Japanese kun'yomi) get no Han spelling and NO Sino route: plain phonetic distance only. Kun/on test: reading's own Wiktionary entry etym (inh ojp/jpx = native, der/bor ltc/och/zh = sino); else on_shaped() (one on'yomi syllable per kanji: C?y?V + i/u/n/ku/ki/tsu/chi/geminate); single kanji also within 0.45 of pivots. Results: LexiliAsel roots with >=2 Sinosphere langs reproduced as one cluster 87.5% -> 89.5%, residual = native/different-word/onomatopoeia splits; pairwise @0.30 recall .791 -> .882 at FP .052 -> .055.
- [2026-11-08] **Sino route vs Japanese (user correction).** MC -ng ~ Japanese long vowel / open syllable (空 kōng~kū, 孫悟空 ~ songoku): NG_VS_JA / JA_LONG variants in align.sino_distance. Nasal coda vs onset-nasal penalty (NASAL_POS, xan~yama) and y~sh 0.8 (SINO_FAR) apply to the SINO ROUTE ONLY: the user's yama/shan example was about the Sino route's etymology, not plain distance. Plain distance stays as calibrated.
- [2026-11-08] **Arabic/Persian abjad skeleton = FALLBACK ONLY (user correction).** cluster.py joins ar/fa by normalised skeleton (word_selection/abjad.py) only when at least one of the pair is unromanized (item['romanized'] = Wiktionary roman AND forms); both romanized -> sound decides. Formless ar/fa words are now kept in clustering (distance 9.0, join only via spelling) and skipped in proposals/check. e2e LexiliAsel: readable ar+fa roots unchanged 94.9%; 178/629 unreadable words now attach.
- [2026-11-08] **Arabic<->Persian vocalization prediction** (abjad.predict_all, pipeline.predict_vocalizations): an unromanized ar/fa word gets readings from a romanized same-skeleton partner. Uses vowel LENGTH (user request): raw Wiktionary roman -> length_form with long vowels A/I/U; long vowels align only to matres (ا و ی), short ones to unwritten slots; Arabic short i/u -> Persian e/o, long keep quality; i stays i before consonantal ی; ay/aw -> Persian ey/ow or majhul i/u (ranked alternatives); geminates collapsed first (LexiliAsel Persian keeps 38/1679). Persian: prefer Iranian roman (â/e/o). LexiliAsel same-skeleton pairs exact match: ar->fa 63.3%, fa->ar 59.6% (copying partner form: 26.3%). Residual errors: Persian vowel drift (azole, fandog), pausal CaCC (jabl, ketf), Wiktionary homograph readings (verbs listed first) -- the pipeline's translation-table roman avoids most of the latter.
- [2026-11-08] **Lexical-contrast detection strategy (user-directed):** use a FOREIGN Wiktionary edition's sense divisions (e.g. ja.wiktionary 兄 vs 弟, de Reis grain vs plant) and their translations into the other source languages -- not English definitions of source words (user rejected that approach). Same sense seen from two editions (Bruder ~ frère) must merge when shared-word languages >= disjoint ones: differing tables are usually incompleteness. Only de/fr editions are indexed (WiktionaryLMDB_de/_fr); zh is configured in wiktionary_config.xlsx but unbuilt; ja/ko not configured. de/fr alone find no contrasts for rice/brother/uncle/wear (they don't make them).
- [2026-11-08] **Japanese + Chinese Wiktionary editions configured** (wiktionary_config.xlsx WiktionarySources: ja '日本語|Japanese', zh '漢語|汉语|中文|Chinese'; names are '|'-separated alternatives). Parser now keeps translation tables with no sense label (sense ''). Test froh vs glücklich with de alone: only Russian splits (счастливый/рад); ja lists 嬉しい under both -> no contrast at 2 families; needs ja/zh editions.
- [2026-11-08] **contrasts.py with ja+zh editions (built by user: ja 17k translation headwords, zh ~bigger but sparse -- no 米/弟弟/高兴/伯父/着る tables).** Rules that were needed: one best-matching sense per pivot (drops frère 'comrade', Schwester 'nun'); phrases built from a general word + modifier don't count as lexical (младшая сестра, elder brother; concept's own words count as general); a sense alike with two mutually distinct senses is the GENERAL term, not a side; English excluded from family count, reported separately. Results: brother 哥哥/弟 and sister 姐姐/妹妹 in 7 families; rice cooked vs grain (5); happy gives cheerful/content/fortunate (English makes it); froh vs glücklich not separated (both classed general).
- [2026-11-08] **Pivot mode for contrasts (user idea: use 幸福 as a pivot).** contrasts.compare_to_pivot(words, concept, (lang, word)): pivot tables = English tables (reverse index) listing the pivot or its same-spelling cognates (幸福な, 행복하다 via stem, unmarked-tone vi), minus the concept's own table; concept words those tables list join the pivot side (哥哥/오빠 with 兄), the rest are foils; foil tables = tables listing foils, not pivot tables. Tables weighted by languages sharing words with the concept (not counting pivot cognates: 米 also = America). Per language: weighted core words, verdict separates / same word / phrase only / no data. Root matching across PoS (related()). Results: rice/米 5 families, brother/兄 10, happy/幸福 6 (cmn/ko/ru/tr/ar 'same' because English 'happiness' lists momentary words too). find()'s field-wide grouping is too noisy for dense fields like happy; pairwise pivot comparison is the useful view.
- [2026-11-08] **Pivot verdicts must control for part of speech (user check of es/fr).** Comparing the pivot's noun (felicidad, bonheur) with the foil's adjectives (alegre, joyeux) made Spanish/French look like they separate; per-POS comparison + a cross-POS 'leak' check (pivot core word's root among foil words: felicidad~feliz, bonheur~heureux, Glück~glücklich, счастье~счастливый) shows they don't. Leak check uses single words only (hermano mayor~hermano and vi anh~anh em are phrases/compounds). happy/幸福 now separates only in ja, vi (+en); es/fr/de/ru/cmn/ko/tr/ar same word. Also compare_to_pivot reports existing Globasa words covering each side's translations (word-list Eng/Spa/Fra/Deu/Rus/Zho/Hin/Ara columns): hoxya 'happiness, joy' merges happy/幸福; mansodar, soso merge brother/兄; risi merges rice/米.
- [2026-11-08] **幸福 split question (goal: basis for a derived word or new root).** Cleanest evidence is the Globasa word list itself: hoxya 'happiness, joy' glosses TWO distinct words in every column (feliĉo/ĝojo, felicidad/alegría, Glück/Freude, bonheur/joie, счастье/радость, 幸福/快乐, ख़ुशी/आनंद, سعادة/فرح); hox merges Epo feliĉa/ĝoja/gaja. Wiktionary's happiness/joy tables cross-list, which is why pivot verdicts understated it. Existing derivations: bonjotay 'well-being' (Zho 幸福, 福祉), dayhoxya 'bliss'. Pipeline on happiness minus joy words: #1 Sinosphere 幸福 cluster (4 families) -> hanfuku/hinfuku/honfuku; #2 Arabic saʿāda (ar, tr). Use word-list multi-language glosses as evidence of a lexical split the Globasa word merges.
- [2026-11-08] **Globasa happiness field (user):** kweho = merry, cheerful (Epo gaja, bonhumora; from 快活/쾌활); furaha family = pleased/enjoy (plaĉi, ĝui); hox/hoxya = feliĉa+ĝoja (+gaja, redundant with kweho). User holds khush/hox = the stable long-term word; short-term words are more variable and casual (data: long side converges on one word per language, short side fragments). Persian خوشحال (khosh+ḥâl) = glad (short), Hindi ख़ुशहाल = prosperous (long): haluhox as the short-term ĝoja word calques the Persian. compare_to_pivot now subtracts neighbour tables already rendered by another Globasa word (umbrella = words for the concept's headword + side-merging words; covered = other words listing the table headword as a gloss item) and drops words listed on both sides from cores and the leak check.
- [2026-11-08] **Privative contrasts count (user: froh, blij).** German froh = '(momentarily) happy', glücklich = 'both momentarily and generally'; Dutch blij = 'happy; momentarily. For generally in life, see gelukkig' (raw dump; nl is not in the concept index -- only the 16 source languages are). A general word covering both sides + a word of its own for the foil side is a MARKED (privative) contrast, the same shape as hox + derived haluhox; compare_to_pivot reports it as verdict 'marked' (families in r['marked']) instead of 'same word'. happy/幸福: separates cmn, ja; marked es (contento), fr (content), de (freudig/froh), ar (مسرور), ko (반갑다); ru now marked too (user: счастье is the long-term word): the own-word test checks relatedness only against pivot-EXCLUSIVE words, since радость sits on both sides.
- [2026-11-08] **Isolating languages ignore the English table's PoS (user: Vietnamese makes the distinction).** vi hạnh phúc / cmn 幸福 are noun and adjective alike, so a noun-table vs adjective-table comparison is a real verdict for them (contrasts.ISOLATING = {vi, cmn}). happy/幸福 now: separates cmn, ja, vi (3 families); marked ar, de/es/fr/ru, ko (3 families); hi, sw, tr cross-POS only.
- [2026-11-08] **Foil side reaches other parts of speech (es/fr/tr deep dive).** Foil words were all adjectives, so nouns (joy) never joined and Turkish mutluluk had nothing to compare with. Fixes: same_root_forms() scans the reverse index's word list for root relatives of foil words (嬉しい->嬉しがる, 기쁘다->기쁨, vui->niềm vui; single words only, vi max one extra syllable); side assignment needs the word itself (or its inflection: 幸せな->幸せ, 행복하다->행복) to be listed in a pivot table, not a root relative (기쁨 under the mixed happiness table must not take 기쁘다); Vietnamese related() = whole syllables with tones (vui !~ vú, u, ừ). Findings: French Wiktionary defines bonheur as 'état' vs joie as 'sentiment'; heureux senses are all lasting/fortune, momentary only in 'heureux de'; Spanish feliz sense 1 '(trait)', contento momentary, ser feliz / estar contento; Turkish mutlu/mutluluk general, sevinç/sevinçli/memnun/neşeli momentary, literary lasting tier saadet, mesut (Arabic s-ʿ-d), bahtiyar (Persian baxt 'fortune'). happy/幸福 now: separates cmn, ja, vi, tr (tr via literary saadet); marked Ewropali, ar, hi, id, ko, sw; te same word.
- [2026-11-08] **Auto-pivot sweep (contrasts.auto_pivot) is SUGGESTED, not always run (user):** contrasts.suggestion() fires when the concept's English headword has <= 2 substantial translation senses (tables covering >= 5 source languages; happy 2, rice 2). Page: section '3b. Contrasts other languages make' with a 'Look for contrasts' button -> POST /api/contrasts (cached per concept). Speed: same_root_forms was 97% of the time (full scans of the reverse index's word list, 1.2M related() calls per 3 pivots); bucketed per language (Han char / first Hangul syllable / vi syllable / first 3 letters) + per-word cache: 3 pivots 12.4s -> 0.6s, whole happy sweep 5.8s.
- [2026-11-08] **Wiktionary dump facts for Sinosphere:** MC is sounds[].zh-pron tagged Middle-Chinese (concept index dropped it). Simplified chars have no readings; map via traditional entry forms raw_tags Simplified-Chinese. Korean hanja: forms tagged hanja / head arg hanja / ko-etym-Sino. Vietnamese: ONLY vi-etym-sino (plain CJK forms mix in chữ Nôm for native words). ja-kanjitab yomi is NOT in wiktextract output. A simplified char with its own MC readings (面) must not be mapped (面->麵 bug). LMDB index fails silently under `ulimit -v 8G`.

- [2026-11-07] **Word Selector calibration facts (from LexiliAsel gold).** Cognate pairwise distance threshold 0.30 (align.py costs) gives F1 0.92; 0.42 merged unrelated words. Blending weighted per LANGUAGE beats per FAMILY (top1 29.6 vs 27.4%); family weighting is for SOURCE selection only. Roots have 0 geminates; C+i+V is written CyV (233 vs 14), C+u+V CwV (91 vs 19). Japanese/Korean epenthetic final vowels count half as a-posteriori evidence. LexiliAsel romanization conventions: Korean eo->a, pinyin z->dz/ui->wey/ou->ow/eng->ong, Arabic ʕ->h with geminates collapsed, Vietnamese â/ơ->e, oa->oe, s<->x swap, r/d/gi->z, nh->n. Vocalised Arabic script transliterates better than a looked-up Wiktionary roman (which can belong to a homograph entry).
- [2026-11-07] **Sandbox network:** *.wikipedia.org reachable; www.wikidata.org, mdbg.net, ftp.edrdg.org blocked (403). Use Wikipedia `langlinks` for multilingual articles. curl to localhost goes through the proxy -- test Flask apps with app.test_client(). Never `pkill -f` a pattern that appears in the same shell command (it kills the shell).
- [2026-11-07] **User wants calques considered (pending Stage 7):** besides loans, propose derivations/compounds that calque the most common way the concept is rendered across the sources.
- [2026-11-07] **Three kinds of gloss confusion, three fixes (from user's trouble words):** (1) synonym cluster / fuzzy concept -> main gloss or core group fronted (menalariMainGloss.tsv: kinmyetu, kone, hasaxi); (2) contrast pair sharing a gloss -> front the distinguishing gloss; (3) ENGLISH HOMOGRAPH (hack: tabar chop / hake computer; spell: jumun magic / harufi letters) -> a qualifier, menalariGlossQualifiers.tsv, rendered in the wordlist's italic (_x_) style. Homographs usually sit in single-gloss rows or across PoS, so the same-row candidate list (menalariMainGloss_candidates.tsv) misses them; detect by comparing qualifier-stripped glosses across all rows. Better fixed upstream in word-list.csv when the Globasa team agrees.
- [2026-11-07] **Main gloss is emphasised on Anki cards (user):** the first gloss of each PoS/verb-type row (wordlist order = main first) is wrapped in `<span class="main-gloss">` by AnkiMaker3.emphasize_main_gloss, only when the row has 2+ glosses. Style must stay distinct from headings: card headings are bold (th, h2) and PoS labels italic, so .main-gloss is 1.15em + thick underline, never bold/italic. CSS is added to the note type by update_vocab_deck.py (MAIN_GLOSS_CSS) if missing. Where the first gloss is not the clearest core (kinmyetu verb: 'look down on' is last), `menalariMainGloss.tsv` (Word, MainGloss, Note) names it; it is moved to the front of whichever row contains it, other rows untouched. Also used to front a DISTINGUISHING gloss (kone verb -> 'be familiar with', not 'know' shared with jixi). An automatic 'front the first unshared gloss' rule was measured and rejected 2026-11-07: it fronts spelling variants (mold->mould), reacts to shares with the word's own derivatives (wakufa/wakufacu), and finds nothing for real contrast pairs whose glosses are all shared (narem/hasaxi). Curate by hand from menalariMainGloss_candidates.tsv. A MainGloss may be a comma-separated CORE GROUP (user, 2026-11-07: hasaxi -> 'tender, loving', since no single gloss separates it from narem); it applies only to a row containing every gloss in it, which are fronted in the group's order inside one emphasis span.
- [2026-11-07] **A Globasa entry's several translations describe ONE concept (user):** they are there to resolve polysemy in the learner's language and to cover every way that language expresses the concept, not a list for the learner to recall. Deck design should test the concept, never ask for the full gloss list.

- [2026-11-07] **Filipino is no longer a Globasa source language (user).** Source set = en es fr ru de (one European family) + cmn ja ko vi hi te ar sw fa tr id (each its own family). The repo's `Methodology for Lexical Development _ Globasa.html` still lists Filipino; it is stale. LexiliAsel `Pilipinasa (...)` entries are historical: parse, don't count.
- [2026-11-05] **Boustrophedon for the Globasa print script (user idea):** no direct reading study found. Removing return sweeps should save about 5% at most (my estimate), and Slattery & Vasilev 2019 found reducing sweep error did not speed reading. Its main promise is relaxing the line-width limit. Syllable blocks allow reversing block order without mirroring glyphs, which Latin cannot do. Direction-free blocks need a non-directional internal layout.
- [2026-11-05] **Script type for Globasa (even-weighted, sources grouped):** syllables are CV 61.9%, CVC 23.7%, V 5.2%, VC 4.2%, CCV 3.4%, CCVC 1.5%; 29.5% have a coda (n+m are 47.9% of codas). `a` is only 27% of nuclei, so an inherent-a abugida with vowel killers needs 102% of Latin's written elements (96% with a nasal coda dot). A full syllabary needs ~500 glyphs for 99.7% coverage. Best fit is an obligatory-vowel syllable-block script with onset, medial (r y w l = 99%), vowel and coda slots. Scripts: session scratchpad only.
- [2026-11-05] **Sound frequency for shorthand must be split by position.** n is the top consonant (7.7% of letters) but 5.0 of that is coda, so as an onset it ranks only 7th (2.7%, behind t s m l k d). r rises from 4.0% in running text to 6.2% of root letters and is only 9% word-initial. With y/w as connectors, i (11.7%) nearly equals a (12.1%), and connectors are 48.6% of letters. Top consonant order varies between texts, so use tiers rather than exact ranks.
- [2026-11-05] **Globasa's minimal-pair rules are documented in `Methodology for Lexical Development _ Globasa.html` (repo root).** Never: v/w, s/z, word-final m/n (zero root violations, letter names excluded). Never except as a last resort: +/- a consonant or vowel at word edges (has many exceptions among short roots: 43 +V end, 95 +C start). Whenever possible: l/r, b/p, f/p, c/j, c/x, h/r. Noun/verb roots should avoid onsets le-, xa-, nun-, ger-, be-, du-. Exclude the letter names (i?e: ibe, ice...) from any root minimal-pair count, because they collide by design. Rule-protected pairs stay safe as the lexicon grows; pairs that merely have low collisions today (t/c, d/j) do not.
- [2026-11-05] **Shorthand from the xwexi lafuzu page:** writing y/w as the i/u connector gives ~0% lexical error (they are permitted unstressed-vowel variants), [ə] is permitted between any consonants so CC can use a neutral link, and stress guidelines split function words into unstressed (join rightward) and stressed (pronouns, stand free). Design recorded in the session reply, scripts not in repo.
- [2026-11-05] **Shorthand statistics (user: Orthic's easy joins target English consonant clusters; Globasa is CV-heavy, confirmed).** Paired TMX TUs, joins Globasa vs English spelling: CC 9.0% vs 24.0%, CV 54.2% vs 36.5%. Word boundaries are 25% of all letter transitions. Dropping all vowels gives 21% context-free lexical errors, and H(V|prev C) is 2.10 vs H(V) 2.28 bits, so vowels should be made cheap rather than omitted. Merging o/u costs 0.03% but t/d costs 0.94% (te/de), so t and d should not share a sign family. n is 38% of syllable codas. Measure with regex tokens: never run GlobasaTokenizer corpus-wide.
- [2026-11-05] **Flash 9B sense pilot results can be replayed offline, but only with the vetting log as the run saw it.** `ask()` needs no server on a cache hit; prompts depend on the selected words and later verdicts shift things, so copy inputs to a scratch dir, truncate `sense_vetting.jsonl` to the run's start (18:21 for the 2026-11-04 run) and check the TSV is byte-identical. Pilot result: 100% precision rests on just 4 human rejections, so it is not yet evidence; 'None of these' wins only 0.4%; 11 of 50 words are grouped, and their strengths are not comparable.
- [2026-11-04] **Sense-vetter cues separate best as sibling comparisons within a word, measured on human verdicts:** sense has the gloss's taxon 99.2% accepted vs a sibling lacking it 80.0%; fits a word tag 97.9% vs 88.6%; Latin name in definition 97.4% vs 90.0%; mentions another of the word's English glosses 99.6% vs 95.1%. Only 227 rejections exist, so these are rough, and adding them moved overall AUC just 0.897 -> 0.902 (within-word 0.906 -> 0.919); the old Eo/Es cues already carry most of the signal. Tag profiles use the tag's gloss plus words typical of its members, built without verdicts so checking against verdicts is fair. A "Latin" `Capital lowercase` pair needs filtering: drop second words seen after lowercase words (Usage notes) and demonym-shaped first words (American marten, Latin plumbum). `BIOLOGICAL_TAGS` is an explicit list because Tags mix hypernym and topic.
- [2026-11-04] **`sense_vetting.jsonl` has two readers, and verdict `u` (unsure) must never count as a judgement in either.** `sense_vetter.py --export` leaves it out; `sense_review_queue.py apply_vetting_log` skips it, since there any human verdict other than `s` reads as a rejection. Any new verdict value needs both checked. In the vetter page, `stillListed()` must mirror the server's `matching()`: paging offsets count only rows the server still lists, and in the "no sense marked" view one mark drops the word's other senses too.
- [2026-11-04] System `node` is v12 (no `?.`, no `fetch`); use `/home/linuxbrew/.linuxbrew/bin/node` (v24). The vetter's page logic can be driven end to end with a stub DOM against a scratch copy of the server on another port. Never `pkill -f` a pattern from inside a Bash tool call: it matches its own shell (exit 144). Kill by pid from `ss -ltnp`.
- [2026-11-04] Flash 9B option position matters: rotating every sense through every letter on simplified prompts (loga, morgi; one sentence each) gives lowercase letters a 3-4x penalty and early letters about 1.5x, Z not favoured. Full prompts swing far more (loga "to say, to tell" 0.393 at H, 0.002 at a, 12 usages), unexplained by letter alone. Fixed: MAX_OPTIONS 25, so only A-Z. --rotate on real prompts (6 words, 18 usages): top-sense spread 0.069 letter, 0.053 neighbours, 0.074 both; 2 shuffles give the same winner as held-out shuffles 90%, 4 give 98%, so default is 4. The N=2.77 in that run is an artefact of pinning the top sense at n//2. Choice format: --compare on 9 words with both verdict kinds, 288 answers each: model-card layout (State, Question, Options, [A], answer line, no system prompt) gives the same winner 96% vs 74% for "A." under Choices, same 0.812 accepted-beats-rejected, only 0.67 vs 0.62 s per answer; now default. Grouped long lists inflate strengths: winners meet few rivals in the final pass, so they are not comparable with ungrouped words. Separately, the shell runs Homebrew llama.cpp 8260 (CPU only, SSE3 reported), so every OpenJev run so far ignored -ngl; speeds measured so far are CPU speeds. /usr/bin/llama-server is a Vulkan build but only finds its backends from cwd /usr/lib; the copy in Warehouse2/Downloads/Llama cpp has them beside it and ran Flash at about 0.5 s per pass.
- [2026-11-04] OpenJev 27B and Flash 9B are both qwen35 with recurrent (SSM) layers in 3 of every 4 blocks (GGUF `attention.recurrent_layers`). Likely why llama-server restores a context checkpoint instead of trimming to the shared prefix (not confirmed), so `-cpent`/`-b`/`-ub` matter for Flash too. Flash has 32 layers, so `-ngl 99` is a full offload on the 16 GB card by file size.

- [2026-11-04] **Syntactic-role vectors (user's idea: words are similar if they take similar arguments) find words of the same type where window vectors find the same topic**, but score no better on Esperanto-sharing or same-tag pairs (AUC 0.55-0.74 for both). `kasiru` gets klosi, binde; `oko` gets xoraham, aham; `baru` under windows gets mama, papa. Too sparse to use as similarity alone (1,416 verb-object pairs from a crude rule parser, 274 of 1,510 content words uncovered). The raw argument lists look more useful directly: `kasiru` objects are xilo, janela, bawe. Idea not yet tested: feed argument glosses to the decision model per occurrence.

- [2026-11-04] **Syntax narrows sense candidates but does not choose among them.** Sheet rows already follow the gloss's PoS (0 verb rows without a v: gloss), so class checks add almost nothing. Wiktionary transitivity does not transfer: accepted `ixara` is labelled intransitive though Globasa has v.tr. Crude particle-based frames kept 85% of sense rows for 177 multi-PoS words; 'loga' looks intransitive only because quotes follow it, so use PosTagger.py rather than simple rules. Absent frames are silence, not rejection.

- [2026-11-04] **Globasa-only word vectors are weak at this corpus size.** PPMI+SVD (dim 50, window 4) on the 30k-token TMX: same-tag words closer than random only 58-71% of the time, split-half neighbour overlap@20 of 0.05-0.20, true synonyms at median rank 172-504 of 1694 (just 20 pairs). Neighbours reflect topic and story (`baru`: mama, papa, dahabutofa), not sense. One configuration only, no subword model tried.

- [2026-11-04] **`GLB_ENG_WiktionarySenses (copy).xlsx` (2026-04-29) is the newest sense sheet found**; the plain `.xlsx` is from Aug 2025 and `.senses_config.json` points to a missing Nextcloud path. Columns: Tier `v` = human, `a` = script, blank = unjudged. App `s` = applies; among Tier `v`, `n` or blank App = rejected (only 227 rejections vs 4833 acceptances, so false-positive estimates are weak).
- [2026-11-04] Agent sandbox sets HTTP proxy variables, so `localhost` over curl or urllib reaches the proxy, which answers with odd pages (a Jetty 404, a 502). Use `curl --noproxy '*'` and `ProxyHandler({})`; check ports with `ss -ltn`.

- [2026-11-04] **`ş` and `ç` in Globasa text are a spelling experiment that did not gain traction in the community** (user), not a former standard orthography. Normalize to `x` and `c` (`şerça` -> `xerca`) when ingesting; Suikal Kraw on Doxo still has it. The Pilpil ji Karote Mon 8 lines mixing many diacritics are left as they are.

- [2026-11-04] **The TMX can hold Globasa-only TUs** (417 since the Nov 2026 Doxo update: Sarin Ci stories and poems, Termodo Fruta, Jaxnedin, Hin Din). `Word Viewer.py`, `run_giza_improved.py` and `ingest_tmx_qdrant.py` all skip TUs lacking the target language, so these stay invisible to them until English is added. New TUs must go at the end of `<body>`: the viewer pairs TMX entries with A3 lines by position. User chose Globasa-only over machine-drafted English.
- [2026-11-04] The A3/glb.txt corpus is TMX en-pairs followed by augmentation lines, so adding en-bearing TUs without re-running alignment makes the viewer attach their context to the first augmentation lines (`sent_idx < len(tmx_entries)`). Re-run alignment after adding English.

- **word_viewer.html two-column entry grid:** the right column must stay capped (`.entry-col-right { max-width: 20rem }`). With `grid-template-columns: 1fr auto` the auto track sizes to the etymology's max-content and, because `.entry-col-left` has `min-width: 0`, the translation table overflows its track and paints over the etymology. `.trans-section` has `overflow-x: auto` as the safety net for wide tables (2 languages + type column + image tiles). Confirmed fixed 2026-09-03.
- **No headless browser verification in this sandbox:** `socket()` is denied environment-wide, so Chromium cannot start even with the sandbox override. Verify CSS layout by reasoning from track-sizing math plus measured screenshot geometry, and say plainly that it was not rendered.
- **Project type:** Python CLI script collection for Globasa constructed language lexicography — NOT a web app
- **Python 3.10+**, procedural style, no `if __name__ == "__main__"` guards, no argparse. Scripts run directly.
- **Central lexicon:** `word-list.csv` fetched from `https://cdn.globasa.net/api2/word-list.csv` (24 columns indexed by Word). Column order changes over time — always use header names, never hardcoded indices. Many scripts wget it at startup.
- **Pandas** for CSV/TSV I/O (`pd.read_csv` with `sep="\t"` for TSV). `csv` module also used.
- **`PoSDict`** (part-of-speech mapping) is duplicated across ~4 files — candidate for extraction.
- **`Lexilista_parser.py`** provides shared wordlist parsing used by multiple scripts.
- **File names often contain spaces** (e.g. `Word selection automator.py`).
- **Hardcoded file paths** throughout — no config files.
- **Menalari extensions** (TSV files) are key data used by AnkiMaker and dictionary tools.
- **Xwexi (lessons/grammar)** in `xwexi-pages-grav/` — git submodule from Globasa-Team/xwexi-pages-grav. Grav CMS pages: `default.{lang}.md` with YAML frontmatter. Lessons in `02.darsu/01-20/`, grammar in `03.gramati/01-14/`, phrases in `04.pimpan-logaxey/`. Supersedes old `gramati-fe-globasa-eng/` fork.
- **Doxo (reader texts)** in `doxo-pages-grav/` — git submodule from Globasa-Team/doxo-pages-grav. Same Grav page convention. Since the Nov 2026 reorganisation: folklore in `01.folklorli-hikaye/`, short stories in `02.lilhikaye/`, poems in `03.poema/`, rotating history/culture pages in `04.histori-ji-kultura/`, historical docs in `05.historili-doku/`, main reader in `06.doxo/`. It is NOT registered in this repo's index (shows untracked), so `git submodule update --remote doxo-pages-grav` fails; use `git -C doxo-pages-grav pull --ff-only`.
- **Wiktionary dump** from Yawipa, preprocessed by `WiktionaryPreprocess.py` into per-prefix subfiles.
- **Key dependencies:** `wn`, `cutlet`, `korean_romanizer`, `genanki`, `pandas`, `beautifulsoup4`, `requests`, `lemminflect`, `hunspell`, `Unidecode`

- **menalariImages_edited.csv** is actually TSV despite the .csv extension — use `csv.reader(f, delimiter='\t')` to parse it correctly.
- **lmdb sub-database keys** must be bytes (`b"wordlist"` not `"wordlist"`). `env.open_db(b"name")` stores the handle under bytes key. Access `self.dbs[b"name"]` or convert with `name.encode("utf-8")` lookup.
- **Word Viewer Flask app** is now a real web app (Flask). The cerebrum note "NOT a web app" is outdated for this specific script.
- **Flask** must be installed in venv: `pip install flask`. Added to requirements.txt.
- **Word Viewer layout** imitates menalari.globasa.net (worldlang-dictionary): green header with Globasa logo + nav + dual search inputs (Globasa / Translation), centered content, dark blue footer with language selector pills. Up to 2 display languages at a time.
- **Word Viewer script typography pattern:** CJK, Greek, RTL, and Indic scripts each have a CSS block that: (1) sets body class via JS map (e.g. `CJK_LANG_CLASS`, `INDIC_LANG_CLASS`), (2) assigns font stacks (Open Sans + script-specific fallback for body, serif + script-specific for `.cell-trans`), (3) suppresses `letter-spacing`/`font-variant-caps`/`font-feature-settings` for non-Latin headings/labels, (4) adjusts `--lh`. Follow this pattern when adding new script families.
- **Venv path**: `${workspaceFolder}/venv/bin/python3` — use this, not system python (numpy/pandas version mismatch on system python). See `.vscode/tasks.json` for reference.
- **HunspellMaker.py** `get_lexiklase()` must handle `xfik` suffix in affix WordClass values (e.g. `b xfik` → strip to `b`), `tabl:` prefix for correlatives, and classes `il`, `m`, `f.sah`/`f.lin`. Use `startswith('b')` not `'b' in klase` (the latter matches `tabl: d` false positive).
- **word-list.csv index has trailing spaces** on some entries (e.g. `hinnumer `). Always strip: `menaFrame.index = menaFrame.index.astype(str).str.strip()`.
- **Hunspell FLAG num + AF**: flags 1-7 in dic entries are AF aliases (expand to suffix flag sets), flags 8+ beyond AF count are raw flags (compound rules). This dual interpretation is how class flags + compound flags coexist.
- **GlobasaGrammarChecker** reuses `PosTagger.py` for tokenization and POS disambiguation. Grammar rules operate on POS-tagged tokens. LT-compatible server at `server.py`.
- **apertium-glb-eng.eng-glb.rtx** is the English→Globasa recursive transfer file. Rule pipeline: `npcomp → NP → NNP → DP/CNP → NOM`, `vblex/prepv → vv → VP → DVP`. The `u@vbpr` lemma is the abstract Globasa tense-particle slot — it generates `nun/le/xa/ger/am/jale/jaxa/…` depending on tense+aspect+polarity tags via the monolingual generator. `CNP` is currently dead (never referenced by other rules).
- **Genitive `'s` in eng-glb.rtx** does NOT need a transfer rule: the bidix maps `'s<gen>` directly to `su<pos>`, and the English possessor-particle-head order matches Globasa (`Mary's house` → `Mari su baytu`). For comparable cases, check the bidix before writing structural rules.
- **rtx attribute assignment with tag rewrite**: `{ X[attr = N.attr>category] }` — no inner brackets around the rewrite. Example: `2[tense = 1.tense>tense_PP]`. Brackets `[X>Y]` are only valid in tag position on lemma references like `u@vbpr.[1.tense>tense_PP]`.
- **rtx output patterns vs verbatim passthrough**: The PoS output pattern (e.g. `vbser: _.out_tense;`) controls which tags are emitted *only when a rule fires* and outputs the chunk via `{N}` or `{%N}`. Chunks that no rule consumes pass through verbatim with every input tag preserved. To strip tags reliably, make sure a rule fires — e.g. extend `prepv` to also accept `vbser` so copular `be` reduces through prepv→vv→VP and hits the DVP catch-all (`%1[tense=""]`). The pattern alone is not sufficient.
- **English tagger marks copular `be` as `<vblex>` (not `<vbser>`)** in most contexts (adjective complements, etc.). The bidix needs an `r="RL"` (eng→glb only) entry `<l>sen<vbser></l><r>be<vblex></r>` in addition to the bidirectional `<l>sen<vbser></l><r>be<vbser></r>`. Don't add `<l>sen<vblex></l>` — `sen<vblex>` isn't in the Globasa monolingual and generation will fail.

- **Corpus/TMX dependency chain** (matters before touching any passage data):
  `Corpora/<text>` source → `ThirtyStoriesToTable.py` etc. → `Doxo_passages.csv` → hand editing (sentence splitting + corrections) → `Doxo_passages_edited_updated.csv` → `make_tmx.py` → `Doxo_passages.tmx` → `extend_tmx_*.py` → `Doxo_passages_extended.tmx` → `run_giza_improved.py` → `giza_output_improved/glb_{lang}/` → gold alignment `sentence_id` space.
- **`Doxo_passages.tmx` is NOT regenerable from `Doxo_passages_edited_updated.csv`.** The CSV holds ~2037 rows but the TMX holds 3145 TUs — the `extend_tmx_*` scripts add TUs (UDHR, P&C, etc.) directly into the TMX. Re-running `make_tmx.py` would silently drop ~1100 TUs and every non-en/glb language. To change existing passages, **patch the TMX in place**, never regenerate.
- **ElementTree round-trips these TMX files losslessly**: whitespace lives in `.text`/`.tail`, so parse → modify `seg.text` → `tostring` reproduces `Doxo_passages.tmx` byte-for-byte. Reusing the existing `<tu>` elements (overwriting seg text) rather than building new ones preserves the pretty-printed layout exactly. `Doxo_passages_extended.tmx` normalises redundant `&quot;` → `"` (semantically identical, ~9KB smaller).
- **Gold alignment `sentence_id` is an index into `giza_output_improved/glb_{lang}/glb.txt`, not into the TMX.** That corpus is ~6550 lines (TMX TUs plus augmentation), so `migrate_gold_tsv.py` only re-anchors correctly *after* `run_giza_improved.py` has been re-run against the updated TMX. Running it against a stale GIZA corpus re-anchors to the old sid space and rewrites the gold TSV.

- **Thirty Short Stories Typst edition**: `Corpora/ThirtyStories.typ` (Feb 2026) is the styling reference — `#set par(first-line-indent: 1em, spacing: 0.95em, leading: 0.55em, justify: true)`, Bodoni Moda 9pt/16pt body, Sour Gummy 25pt headings.
- **The paragraphing is readability formatting, not authorial structure.** Vanege supplied none — the source file is flat sentence pairs (1 blank line within a pair, 2 between pairs) and encodes no paragraphs. The breaks were added to the Typst edition by the repo owner and ChatGPT to make the stories easier to read, so they are not canonical and are free to change.
- **English is the primary side: the breaks were decided in English, and the repo owner placed the Globasa breaks to match, using their knowledge of Globasa.** So recover breaks from the English paragraphs and apply them to both halves — not merely because English text is stable across revisions, but because that is where the paragraphing was decided. Breaks live in `Corpora/thirty_paragraph_breaks.tsv`, keyed by sentence index.

- **Globasa hyphenation must be morpheme-aware.** Plain syllabification breaks across compound seams: `atexalkoba` (atex + alkoba) syllabifies as a-te-xal-ko-ba, whose `xal` straddles the seam; `abilya` (abil + -ya) gives a-bi-lya. That is why word-list.csv carries a manual `Hyphenation` column (77 rows, e.g. `atex-alkoba`). `globasa_word_hyphenation.py` resolves morphemes in order: `Hyphenation` column > `LexiliAsel` composition > productive affix stripping > single morpheme, then syllabifies each morpheme independently.
- **Telling `LexiliAsel` composition from etymology**: a composition reads `abil + -ya`; an etymology reads `Hindi (अबाबील "ababil"), ...`. Discriminate on `" + " in value and "(" not in value`. Always verify the parts concatenate back to the word before trusting the split.
- **Typst edition sets Globasa with `hyphenate: false` plus explicit soft hyphens** (U+00AD) at morpheme/syllable boundaries, because Typst has no Globasa patterns and would otherwise apply English ones. CONFIRMED CORRECT: `hyphenate: false` does NOT suppress soft hyphens — they stay explicit break opportunities. This exact pairing is what the Typst maintainer recommends for restricting a compound to its approved break points (typst/typst#6877 "Hyphenation exceptions", laurmaedje: `#show "kopiosuojauksen": text(hyphenate: false)[kopio-?suojauksen]`). The same character is spelled `-?` (markup shorthand), `sym.hyph.soft`, or `\u{ad}`. Typst has no LaTeX `\hyphenation` equivalent, so per-word show rules or pre-inserted soft hyphens are the only route. Short function words (PREPOSITIONS | DETERMINERS | PARTICLES, len<=4) are bound to the next word with U+00A0, following regulated-language convention (French). Both transforms apply ONLY to the `.typ` output — `Doxo_passages.csv` and the TMX keep source text verbatim.
- **Typst uses Knuth-Plass line breaking**, so unhyphenated justified text is far less river-prone than Butterick's word-processor-era warning implies. Don't over-weight that rule here.

- **Globasa hyphenation is delivered as a Typst lookup table, not inline soft hyphens.** `ThirtyStoriesToTable.py` writes `Corpora/globasa_typesetting.json` (`hyphenations` + `binders`) and the .typ preamble applies it via `#let globasa(body) = { set text(hyphenate: false); show regex(...): it => text(hyphenations.at(it.text, default: it.text)); body }`. A second show rule turns the space after a short function word (preposition, determiner, or tense particle) into a nonbreaking space. Story text therefore contains NO typesetting characters at all — no soft hyphens, no nonbreaking spaces, no `~` markup; every rule lives in Typst code.
- **The show rule MUST be scoped to the Globasa halves, never document-wide.** Globasa and English share homographs in this corpus — banana, canal, deliver, dragon, museum, orange, paper — and a document-wide rule would impose Globasa hyphenation on the English text. Headings are emitted OUTSIDE `#globasa[...]` so the rule cannot introduce breaks into a title.
- **Thirty Short Stories character names are Globasa**, being English names/words adapted into Globasa orthography (Espayk, Wiskers, Drako, Letus, Alfonso), so they are syllabified by the normal Globasa rules. A form is admitted to the table if it is seen lower case, is in the word list, OR occurs outside the preface; only the preface's foreign credits (ChatGPT, OpenAI, Anthropic, Claude, Discord, Vanege) fail all three and are left alone.

- **`goyu` vs `hongu` (hole)**: `goyu` is a hole with a bottom, `hongu` a hole bored through. Not interchangeable — corrections in the Thirty Short Stories replaced `hongu` with `goyu` where a dug pit was meant.
- **`goyu goyu` is grammatical, not a typo.** Globasa `b`-class roots serve as noun or verb by position, so "goyu goyu" = "dig a hole" (V + N). Verified that `PosTagger` resolves it: `Te/PRON karar/V na/PAR goyu/V goyu/N in/PREP` — and it holds across an intervening adjective too (`goyu/V amiku/ADJ goyu/N`). Useful regression sentences for the tagger. Never "correct" a repeated `b`-class word on sight.

- **Wikimedia no longer renders arbitrary thumbnail widths.** `upload.wikimedia.org/.../thumb/<hash>/<File>/<N>px-<File>` now serves ONLY widths already in its cache; anything else returns **HTTP 400**, and new renders have moved to the `thumb.wikimedia.org` host. Measured on `Afghanistan_(orthographic_projection).svg`: 120/250/500/960/1280 → 200, but 220/320/400/480/512/553/600/640/800/1024 → 400. This is what broke 376 of the 390 links in `apkg_image_sync_broken.tsv`. **Never construct a thumbnail URL by hand.** Either use `https://commons.wikimedia.org/wiki/Special:FilePath/<File>?width=N` (works for every width, follows renames, 404s only when the file is genuinely gone) or ask the API for a `thumburl`.
- **The MediaWiki API is the right tool for bulk image work**: `action=query&prop=imageinfo&iiprop=url|size|mime|extmetadata&iiurlwidth=500&redirects=1&maxlag=5`, 50 titles per request. It returns a guaranteed-valid `thumburl`, reports renames via `query.redirects`, flags deleted files with `"missing": true`, and carries licence/author in `extmetadata`. ~36 calls covers the whole lexicon, versus ~1800 HEAD requests against a CDN that rate-limits hard. `thumburl` carries `utm_*` params which are safe to strip.
- **Image store is `menalariImages.jsonl`, keyed word → PoS → sense → images.** Kept flat: `pos` is a field on each sense (three levels, not four), and consumers group by `pos` at render time. `pos` uses the `word-list.csv` annotation vocabulary (`n`, `v.tr`, `adj`…) via `Lexilista_parser.ANNOTATION_MAP`. The store holds the **canonical Commons file title**, never a rendered URL — identity is permanent, every URL is a regenerable cache. `menalariImages_edited.csv` is a frozen backup and is read by nothing.
- **Mapping a store `pos` onto Word Viewer's `pos_groups` must happen server-side.** `pos_groups` is keyed `(pos_name, verb_type_name)`, and `Lexilista_parser._refine_verb_type` rewrites the verb type from the WordClass — so `v.tr` on a `b.oj` word lands in *verb / echo-transitive*, which the annotation key alone does not tell you. `Word Viewer.attach_images_to_pos_groups` does this join; doing it in JS silently mismatches.
- **Only 10 words have two gloss segments sharing one PoS annotation** (`fronta` = `n: forehead; n: front`, plus `bebe`, `dotor`, `kapi`, `ruke`, `haxtagu`, `befobi`, `befuraha`, `peda`, `e`). So PoS group ≈ sense for 2,560 of the 2,560 multi-segment words bar those ten — but the two axes are still distinct and the store models both.
- **`Tags` in word-list.csv encodes hyponymy using Globasa headwords as tag names** — `tren` is tagged `calyo`. 123 of 129 distinct tags are themselves headwords, covering 4,483 word-tag pairs (`calyo` 26, `hewan` 30, `mamoyen` 77, `fruta` 56). **But tags are NOT always hypernyms**: the largest ones are topical, not IS-A (`dexa` 198, `jismulogi` 157, `medis` 156, `kimikamon` 118, `geografi` 87) — a word tagged `medis` is not a kind of medicine. Any hyponym-derived feature must be opt-in per sense, never inferred from the tag list.
- **Most vocabulary cannot be illustrated.** The core-500 list is only 15% imaged (78/500); `jixi` "know", `konceto` "concept", `kwasisen` "seem" and every conjunction have no picture and never will. `illustratable: false` (on a word or a single sense) exists so these leave the curation queue permanently. A weak image is worse than none — a learner over-indexes on whatever they are shown.

- **Image-to-PoS heuristic (user's rule): a still shows a thing or property, an animation shows an action or manner.** So GIFs go to the verb group and stills to the noun group; when the word has neither (adjective/adverb pairs like `amiku` "deep; deeply"), a still falls back to the adjective and a GIF to the adverb. `images_store.infer_pos_for_image` implements it against `ANNOTATION_MAP` via `pos_kind()`. This placed 198/198 of the images the migration had left unassigned, taking the curation queue to zero.
- **Gloss context expansion is for sense matching, not for display.** `_expand_gloss_context` turns a plain (non-italic) parenthetical into a compact and a verbose reading -- "ace (card)" -> "ace", "ace card". It exists to extend glosses into more languages via Wiktionary and Apertium translation. `parseWordEntry` keeps it; `parseEntry` (the slot-based Anki makers) must not, or one gloss eats two PoS slots. Italic parentheticals `(_bird_)` are never expanded.
- **Constructions:** `Constructions.xlsx` pairs a headword with a syntactic frame (`▯ jixi na ▯` = "know how to") plus a `to_exclude` list naming the gloss items that only hold inside the frame. `constructions.py` is the shared matcher; `extract_constructions.py` lifts those items out of `word-list.csv` after each CDN download (idempotent). `hay` and `sengi` are left with NO English gloss -- the frame carries their whole meaning.
- **word-list.csv is CRLF with no terminator on its final line.** Sniff the line ending from the head and the trailing newline from the tail; sniffing either alone gets the other wrong and rewrites all 9271 lines.
- **`str(NaN)` is the truthy string "nan".** AnkiMaker3 reads word-list.csv without `dtype=str`/`fillna`, so an empty gloss becomes "nan" and parses into a bogus gloss. Do NOT add a global `fillna("")` -- AnkiMaker3 relies on the NaN idiom `selected_rows["Tags"] == selected_rows["Tags"]`. Guard at the point of use with `pd.isna`.
- **Globasa__Vocabulary.apkg carries no scheduling** (revlog empty, every card type 0). It is a distribution deck, so note GUIDs are what preserve existing users' progress on re-import -- never regenerate them.
- **Anki canonicalises note tags** into case-insensitive alphabetical order, and treats them as a set. Compare tags as sets when deciding whether a note changed -- a list comparison against AnkiList.csv's wordlist order marks every multi-tag note dirty on every run (bug-192).
- **`.vscode/` is a read-only bind mount in the Claude Code sandbox** (so are `~/.vscode` and `~/.vscode-oss`). Neither the Edit tool nor Bash — even with the sandbox override — can write `tasks.json`; build the file in the scratchpad, validate it, and hand it to the user to copy in.
- **Globasa tense/aspect is a preverb paradigm, not inflection.** `apertium-glb.glb.dix` generates one `u<vbpr>` word per component: tense (`inf`=na, `pres`=nun, `past`=le, `fut`=xa, `cni`=ger, `imp`=am), then aspect (`impf`=nun, `perf`=le, `pros`=xa), then polarity (`neg`=no, `aff`=si). `u<vbpr>` with no tense generates the literal "u", so there is no empty-tense form to rewrite tags into -- suppressing a marker means editing the token out of the stream, not retagging it.
- **`eng-glb.rtx` emits a preverb for every finite VP** (`DVP -> ... VP.[finite]{ u@vbpr.[1.tense] _ %1[tense=""] }`), so English simple present always came out as "nun", which Globasa leaves unmarked. Same shape as the `un` insertion for `<sg>` nouns at rtx line 175.
- **rtx attributes default to the first value in their list.** `tense = [finite] inf pprs ger pp` with `finite = pres past ...`, so a verb with *no* tense tag still transfers as present -- deleting `<pres>` from the biltrans stream does not suppress "nun".
- **The translation aide's back half is split at the transfer/generation boundary** (`_APERTIUM_PIPELINES[dir]["transfer"]` and `["gen"]` in `Word Viewer.py`). Anything the grammar *inserts* (preverbs, numerals) exists only after rtx, so it can only be edited there; anything present in the source is edited in the biltrans stream by `_apply_overrides`.
- **The `petra` tag in word-list.csv is topical "stony things", not IS-A** — 27 entries mixing true rocks (`granito`, `basalto`, `dyorita`, `andesita`, `obsidyan`, `pumica`, `ardwazi`), minerals (`kwarzo`, `kalcita`, `gipsu`, `caku`), gemstones (12: `almasi`, `rubin`, `zafiro`, `zumrudi`, `opal`, `topazi`, `yexim`, `ametisto`, `onikse`, `akiku`, `peridotu`, `lazurdi`), and bulk materials (`xatu`, `ayse`, `cakmake`, `kwangu`). Another instance of the general rule that Tags mix hypernymy with topic — do not treat `petra` as a rock hypernym in any derived-gallery or hyponym feature.
- **Globasa's igneous inventory is half a grid.** It has `dyorita`/`andesita` (the intermediate intrusive/extrusive pair) and `granito`/`basalto`, but NOT rhyolite, gabbro, peridotite or komatiite — so two of the four composition rows are missing their counterpart. Building blocks for compositional coinage are all present: `magma`, `lava`, `atex` (fire), `yunhe`/`yunhedo` (melt/molten), `kristal`, `kanca` (glass), `cengu` (layer), `aloforma` (transform — exact calque of *meta-morph*), `baxgeoli` (underground), `perya` (surface), plus the clastic roots `xatu`/`nentu`/`grava`/`fanko`/`lilpetra`/`daypetra` and `limu`/`namake`/`sokitan`.

- [2026-10-25] **A pronoun belongs to a SENSE, not to a word (user rule).** te = only the live, whole plant (xwexi: te is for "all living forms"; CanonicalSentences #149, kanabis). Every food sense is to; every body part / plant part (leaf, root, nut, ear of grain) is to; cut, picked or dead plants are to. So a plant word never carries just one pronoun arbitrarily: its senses decide. Source of truth: `menalariAnaphorSenses.tsv` (Word, Anaphor, Mena, Check; 315 plant/food words: 9 with both, 72 te only, 234 to only; Check '?' = 23 judgement calls for the user), which overrides menalariPronouns_edited.tsv for those words. AnkiMaker3 orders te first and fills AnaphorMena/AloAnaphorMena from it. Non-plant duals (maux, Farenhayt, esponji, kandidato, membro, virus) are still on the old TSV path, unlabelled.
- [2026-10-25, revised 2026-11-07] **Anki deck subdeck layout (user rule, 2026-11-07):** Globasa::Vocabulary::Produti::{Imajeli,Nenimajeli} holds every *Produti template, ::Rukone::{Imajeli,Nenimajeli} every *Rukone template; the quick card types (Enfasis, Pornamelexi, Alo Pornamelexi, Oposmenalexi, Verb Type) keep a subdeck of their own name. Imajeli/Nenimajeli is decided PER CARD by rendering it and searching for a web `src=` (Wikimedia Imajelinku/Faleanimalinku/DuayumImaje), not per template: the plain Produti card shows the picture on its front, and Animali/Faleli/Nenojetoli Rukone backs show Faleanimalinku. Purpose (user): catch up in pieces, study the trivial cards separately, and study ::Imajeli on a good connection while ::Nenimajeli works offline. Never remove a family parent deck (removing a deck removes its children). Anki's apkg import does not move a learner's EXISTING cards into new decks.

- [2026-10-25] **Optional -cu is predictable from verb class.** b.oro / b.oro.harka glosses carry "v.intr (optional use of -cu)" (7 lack it: plurota, rujwan, sorsore, cwey, gawlubloki, fuxiku, disforma -- probably lexicon gaps). The b.nenoj entries carrying it are -cu HEADWORDS whose own -cu is the optional one: on an ambitransitive root (bukacu, xorucu; 39) X-cu is the root's intransitive; on a feeling/state root (pilocu, termocu; 34) -cu means "become" (= xor-X); the other ~96 -cu words (boncu < adj, okocu, sencu) are ordinary words. Pure verbs use `f.` WordClass codes (f.lin, f.sah) where noun/verbs use `b.`; `b.nenoj.p` = a transitive verb's intransitive use (suferi, kadam).

- [2026-10-25] **Globasa "without" has four prepositions** (user): **wal** (general), **nenhar** (not having), **nenton** (apart / separate from, not along with), **nenyon** (not using). A verb used with no object is *nenhar ojeto*. Prefer the precise one over wal in card prompts and translations.

- [2026-10-25] **Hector's recordings.** Lesson word lists (darsu_NN_lexilista.mp3) read several words per file; the user hand-cut lessons 1-7 in Audacity (projects in /media/paleos/Warehouse2/Applications/Segmentation/Hector/) into Ektor_su_Lafuzu_processed/<word_with_underscores>.ogg (125 clips; Word Viewer's AUDIO_DIR). ffmpeg silencedetect (-40 dB, 0.35 s) reproduces those cuts one-to-one in lessons 1,3,4,6,7, each hand clip 0.1-0.3 s longer (padding). Recordings often skip list words (lesson 5 reads 21 of 28), so count mismatch is normal. Duration alignment drifts once several words are skipped (wrong from mid-list in lesson 5) -- superseded by phoneme recognition: wav2vec2-lv-60-espeak-cv-ft IPA mapped to Globasa letters + in-order edit-distance alignment labels all 125 hand-cut words of lessons 1-7 correctly (lesson 5's skips exactly = the user's missing words). Hector also reads forms not on the list ((fe) ban mara, kenumer te/to). Lesson lists write correlatives as `**kenumer** (**te**/**to**)` = three spoken items, written apart (`kenumer to`). The alphabet page's "X or Y" pronunciations are PERMITTED variants, not errors; its .ogg/.wav files are Wikimedia IPA samples, not Hector.

- [2026-10-25] **Globasa spelling is FULLY phonemic** (user correction of "nearly phonemic"): one letter = one phoneme, per the alphabet table in xwexi 03.gramati/01.abece-ji-lafuzu (c=t͡ʃ, j=d͡ʒ, x=ʃ, h=x, y=j, r=ɾ ...). Spelling -> IPA is a plain per-letter table; no pronunciation dictionary or G2P model is needed. Phoneme model for checking recordings: Models/wav2vec2-lv-60-espeak-cv-ft (facebook, IPA CTC output).

- [2026-10-25] **Lesson 17's word-list recording is a synthesized voice, not Hector's** (user). xwexi_lessons.SYNTHESIZED_LESSONS = {17}: LafuzuDeckMaker keeps it SEPARATE, not dropped (user): own notes (key 'synth:'+spelling, never merged with Hector's -- barix has both), tag 'synthesized', Asel 'Lesson 17 — synthesized voice, not Hector', subdecks Globasa::Lafuzu::Synthesized::<card type>, media prefixed lafuzu_synth_. /splits refuses to export it, and the dictionary's pronunciation button marks its 15 clips '🔊 synthesized' (lookup returns pronunciation_voice: Hector | synthesized). User: never present them as Hector's; the clips stay (segmentation was right). Its 15 clips were already exported into Ektor_su_Lafuzu_processed, named like Hector's -- they are told apart only by which lesson lists the word (no lesson-17 word appears in another lesson). The phoneme-based splits for lessons 8-20 were all correct (user verified).
- [2026-10-25] **Clip names include proper nouns and suffixes** (Engli, Mexiko, -sa, -li): any name/filename rule for clips must allow capitals and a leading hyphen.

- [2026-10-25] **Doxo audio (doxo-pages-grav, 137 files, 65 min) is mainly SYNTHESIZED** (user), like lesson 17. Confirmed human (Hector) audio is only the xwexi course: ~44 min (word lists 14.5, reading exercises 16.1, example sentences 3.8, common phrases 5.7, alphabet 4.1). For speech recognition: enough to fine-tune a pretrained phoneme/CTC model for Hector's voice, not to train from scratch or to generalise to other speakers; never train on synthesized audio as if human. Any Doxo file would need per-file human/synthetic sorting before use.

## Do-Not-Repeat
- [2026-11-10] `pkill -f "[W]ord Viewer.py"` still kills the calling shell when the SAME command line also contains "Word Viewer.py" (e.g. the python launch). Kill by a pattern unique to the server: `kill $(pgrep -f "[p]ython3 -u Word")`. Use `python -u` for background servers or the log stays empty (buffered).
- [2026-11-10] `.vscode/` is read-only in the sandbox: a checkout/merge that changes .vscode/tasks.json fails ("unable to unlink"). If the file on disk already equals the target blob (`git hash-object` vs `git rev-parse <ref>:path`), `git add` it and the fast-forward goes through without writing it.
- [2026-11-10] **Fresh-clone readiness of the Word Viewer (done 2026-11-10, 13b821d..40f51c6, not pushed).** setup.sh + requirements-viewer.txt; submodules registered; inputs optional; WV_AUDIO_DIR/WV_APERTIUM_DIR. Original findings: GitHub origin/main is far behind (images-per-sense never pushed; local main 43 ahead). xwexi-pages-grav and doxo-pages-grav are in .gitmodules but NOT registered as gitlinks (only giza-pp is), so `clone --recursive` skips them. Viewer needs untracked inputs: menalariExtension.tsv, Soti.tsv, graphic_blacklist, Constructions.xlsx, Doxo_course_ranking.csv, giza_output*/; word-list.csv is fetched by globasa_pos on import. AUDIO_DIR and APERTIUM_DIR are hardcoded absolute paths. A build_db() that crashes leaves an empty WordViewerLMDB/, and every later start fails with lmdb ReadonlyError (delete the dir).
- [2026-11-09] In this sandbox: `pkill -f "Word Selector.py"` / `pgrep -f` with the plain pattern matches the calling shell and kills it (exit 144); use `pgrep -af "[W]ord Selector.py"`. curl to the local server needs `--noproxy '*'` (otherwise a 502 from the proxy). git commit needs `-c user.name=Paleos -c user.email=Paleos@paleos.me` (no global identity in the sandbox).
- [2026-11-08] The sandbox hides ~/.gitconfig, so `git commit` fails with "Author identity unknown". Pass `-c user.name=Paleos -c user.email=Paleos@paleos.me` (the author of earlier commits) instead of changing the config.
- [2026-11-08] **Never put `''` inside a `'''...'''` Python replacement string in a heredoc edit** -- it silently became `or ` and broke the parser. Use the Edit tool for replacements containing quotes.
- [2026-11-07] **Never `import` a project script to reuse a constant.** Scripts have no `__main__` guard, so `from update_vocab_deck import COLUMNS` ran the whole update and rewrote Globasa__Vocabulary.apkg and its .bak. Slice the source text / `ast` it, or exec only the needed section against a scratch copy.

- [2026-11-04] **Never run `GlobasaTokenizer` over the whole corpus in one uncapped process.** My script doing this on the 3566-TU TMX exhausted RAM and froze the user's computer, forcing a reboot. Exact cause not diagnosed. Any corpus-wide or unknown-memory job needs `ulimit -v` and `timeout`, and should start on a small sample.

- [2026-11-04] **Never execute `make_tmx.py`, not even with `--help` as a probe.** Project scripts have no argparse and no main guard, so ANY invocation runs them in full. I ran it inside a verification command and it overwrote `Doxo_passages.tmx` with a 591 KB CSV-derived file; restored from backup. Applies to every script here: read it, don't probe it.
- [2026-11-04] Check the working-tree file AFTER the last command that could touch it, and treat a surprising `git diff --stat` as a failure signal. It caught the above where earlier checks in the same command had already passed.

<!-- Mistakes made and corrected. Each entry prevents the same mistake recurring. -->
<!-- Format: [YYYY-MM-DD] Description of what went wrong and what to do instead. -->

- [2026-04-21] Script tiers (1-5) must be CONSERVATIVE — no false positives. Single-word overlap and single WordNet hits cause false positives (e.g. `din` marked 's' for "sunrise to sunset" which is `nuru`). Require 2+ substantive (len>=4) overlapping words for 's'. False negatives are OK — the LLM tier catches them.
- [2026-04-27] Consolidated Script?/LLM?/Vetted?/Expert? into single 'Tier' column. Both extender 3 and LLM_sense_judge updated. Loading handles old format via backward-compatible collapse.
- [2026-04-27] word-list.csv column order changed (WordClass=2, TranslationEng=3, TranslationEpo=4, Tags=6, Antonyms=12, TranslationSpa=15, +TranslationHin=20, +TranslationAra=21). Old hardcoded indices (3=WordClass, 6=Eng, 8=Epo, 9=Spa, 13=Antonyms, 15=Tags) were all wrong. Fixed to use header names.
- [2026-04-28] Extracted shared constants/helpers from extender 3 to wiktionary_constants.py. All configurable constants now in wiktionary_config.xlsx (5 sheets: ExtensionLangs, Dialects, PoSMapping, PoSFallbacks, WiktionarySources). Extension TSV generation moved to separate Wiktionary extension builder.py.
- [2026-04-21] Removed `eng_in_def` shortcut and single-word moderate core match — both produced false positives. Raised composite threshold from +2 to +3.

- [2026-04-30] Globasa POS disambiguation algorithm: (1) prep/particle/det/poss/num projects through t/d;m words to next b, using CBARRIER in CG3 to pass through d;m (det+adv); (2) SVO per clause (N-V-N, extras N), reset at conjunctions/commas/na; (3) t resolved by next connected b (not interrupted by prep/particle/clause boundary). PP-internal nouns excluded from SVO has_nom check.
- [2026-04-30] Affixes (be-, du-, -gi, -cu, -ya, etc.) are irrelevant to b↔noun/verb disambiguation. They change the word itself but don't determine POS in context. The -mo suffix on t-class words always forces ADV.
- [2026-04-30] word-list.csv contains multi-word entries like "sen in" (jm), "sen infra" (jm) that cause false multi-word matches. Tokenizer must restrict multi-word matching to safe patterns (fe/cel/he/no as first word, or second word in MULTI_WORD_PARTS).
- [2026-04-30] In Apertium dix, `b.lin` words (e.g. `sen`) need a `__vbser` paradigm entry alongside `__n` and `__vblex`. CG rule `SELECT (vbser) IF (1* (adj) BARRIER NotAdjAdv)` picks copula reading when followed by a t-class word; otherwise SVO resolves as `vblex`.

- [2026-04-29] HunspellMaker.py: `'b' in klase` matches `tabl: d` (correlatives) as benjilexi. Use `klase.startswith('b')` after stripping `xfik` and handling `tabl:`. Also: `line.strip("\n")` doesn't strip trailing spaces — use `line.strip()`.

- [2026-04-30] **PosTagger.py** exists and implements full Globasa POS disambiguation: (1) unambiguous assignment from WordClass sets (PREP, DET, POSS, PRN, NUM, CONJ, PAR, ADV, ADJ_ONLY, PURE_VERBS, INTJ), (2) prep/particle/det/poss/num projects through t/dm to next b, (3) SVO per clause for remaining b, (4) t/dm resolved by next connected b. Also has `lemmatize()` with prefix/suffix stripping and multi-word matching with conservative patterns. Output: `word/POS` format. Test suite: 21 Xwexi sentences.
- [2026-04-30] **Factored GIZA++ alignment** should use PosTagger.py for Globasa-side POS factors. Key design: internal compound morphemes get NO POS tag (only the head/last morpheme gets the compound's POS). This prevents spurious cross-category alignments (e.g. `tiga` aligning to `short|JJ` instead of `thirty|CD`). The POS tagger resolves contextual POS for `b`-class words (noun vs verb) and `t`-class words (adjective vs adverb) which the static WordClass cannot.
- [2026-04-30] **run_giza_improved.py** implements: dictionary seeding from word-list + menalariExtension (-dictionary flag), word-pair corpus augmentation (sentences ×3 + filtered word pairs), morphological segmentation (LexiliAsel + productive affix stripping with 73 prefixes / 61 suffixes), bidirectional GIZA++ + GDFA symmetrization. Output: `giza_output_improved/`. giza-pp is a git submodule.

- [2026-04-30] **Apertium split pipeline**: Run stages 1-6 (morph→CG→tagger→lsx→pretransfer→biltrans) to get the biltrans stream, modify it for lexical overrides and article suppression, then run stages 7-12 (lrx→anaphora→transfer→revautoseq→gen→postgen). This lets transfer rules handle agreement correctly.
- [2026-04-30] **Apertium un suppression**: To prevent the eng-glb transfer rule from inserting `un@num` for singular nouns from articles ("a"/"the"), change `<sg>` to `<sp>` on the noun's biltrans tags. The NNP fallback rule `(if (1.number = sg) { un@num ... } elif (1.number = pl) { plu@adj ... } else { 1 })` then falls through to the bare noun. Do NOT post-process the output — modify the biltrans stream.
- [2026-04-30] **Apertium biltrans format**: `^source<tags>/alt1<tags>/alt2<tags>$`. Articles: `@`-prefixed `<det>` units (e.g. `@the<det><def>`) mean no Globasa equivalent. Numerals: `<num>` tag (e.g. `one<num>/un<num>`). The `@` prefix distinguishes articles from numerals.
- [2026-04-30] **Apertium pair location**: `/home/paleos/ApplicationSource/GlobasaTranslation/apertium-glb-eng/`. Both `eng-glb` and `glb-eng` modes. Debug modes: `eng-glb-morph`, `-disam`, `-biltrans`, `-transfer`.

- [2026-05-01] **Gold-alignment sentence_id MUST come from the server, not the client's array position.** `/api/alignments` attaches a stable `sentence_id` (the index in the unfiltered global list) to every entry; the annotator must pass `entry.sentence_id` (not its position in the filtered/paginated view) when saving, fetching, or resetting gold annotations. Using the array offset as sid silently corrupts the gold TSV: records get saved against indices that, in any later view with a different corpus/query filter, point to unrelated sentences — and they can't be reset because the server's bulk-reset re-resolves context via the unfiltered `_load_alignments(...)[sid]`, which fails to match the filtered-context where the row was saved.

- [2026-05-01] **Gold tier column** in `gold_alignments/{lang}.tsv`: 7th column, values `saved` (auto-save during editing — work-in-progress) or `gold` (user-confirmed via "✓ Confirm as gold"). Tombstones (links="null") have empty tier. Only `gold` rows feed `merge_gold_priors.py` (quality over quantity). Editing a `gold` record demotes it back to `saved` until reconfirmed. Legacy 6-column rows are migrated as `saved`.

- [2026-05-01] **`migrate_gold_tsv.py`** is the one-shot for re-anchoring TSV rows to correct global sids and adding the `tier` column. Re-runnable; backs up before rewriting; orphans (glb_tokens not findable in the global list) are siphoned to `{lang}.orphans.tsv`. Uses case-insensitive fallback because pre-TMX-substitution rows kept lowercased segmented tokens.

- [2026-05-01] **globasa_tokenizer package structure**: `_types.py` is the ONLY place for `MorphKind` and `Morpheme`. Both `__init__.py` and `segmenter.py` import from `_types.py` to prevent circular import / double-enum identity failure.
- [2026-05-01] **word-list.csv index trailing spaces**: `lex.index = lex.index.astype(str).str.strip()` is required for lexicon loading — same pattern as HunspellMaker.
- [2026-05-01] **LexiliAsel etymology notes format**: strings ending with `. Turkisa (form)...` or `. Am kompara: ...` or starting with `Am X, ...` must be stripped before parsing. See `affix_parser.py` `_ETYM_SUFFIX_RE` and `_AM_NOTE_RE`.
- [2026-05-01] **LRU cache with non-hashable Lexicon**: Use `_LEX_REGISTRY` dict pattern — cache the impl by `id(lex)`, keyed `(word, lex_id, decompose_pseudo)`. Never try to hash a `Lexicon` dataclass directly.
- [2026-05-01] **Hyphenation.py has import-time side effects**: File does file I/O at module level (`menalari_name = ...`). To use only the syllabification algorithm, exec only the lines before `menalari_name = ` from the file source. See `syllable_fallback.py::_get_hyphenation_fn()`.
- [2026-05-01] **conda base env** has pandas etc.; system python3 (linuxbrew Python 3.14) does not. When running scripts that import pandas, use `conda run -n base python ...`.
- [2026-05-01] **pytest on miniconda Python 3.12** is broken in this environment (`imp` module removed in 3.12, but installed pytest version predates that). Use `conda run -n base python -m pytest` instead.

- [2026-05-03] **PosTagger.py is now a CLI shim**; the actual tagger lives in `globasa_pos.py`. Importers (`from PosTagger import tokenize, ...`) still work because PosTagger re-exports the public names — but importing PosTagger still triggers the stdin-read CLI loop side effect, so server code (Word Viewer.py /pos) imports `from globasa_pos` directly to avoid it.
- [2026-05-03] **PosTagger's tokenizer treats `_` as a word character** (uses `\w` in `strip_punct`), so corpus emphasis markers (`_word_`) leave the underscore attached and the lemmatizer fails the lookup → token tagged UNK. Pre-existing issue, not specific to /pos viewer; reflected in /tmx the same way.
- [2026-05-03] **/pos viewer** mirrors /tmx structure: same `_load_tmx_raw` source, paginated cards, target-language gloss row. Per-token decoration is whole-word PoS via `<span class="tok" data-pos="V">surface<sub class="pos-tag">V</sub></span>`. Trailing punctuation is rendered as a separate `.tok-trail` text node so the chip background stops at the word boundary. Show-labels checkbox toggles `body.no-labels` to hide all subscripts at once.
- [2026-05-03] **Compound head rule for PoS**: in Globasa, the rightmost component of a compound supplies the part of speech (head-final morphology, consistent with the GIZA factor design). `globasa_pos.lemmatize` has a hyphen-fallback at the end of its strategy chain — for unknown compounds it recurses on the last hyphen-separated segment. So `Globasa-yonguyen` → lemma=`yonguyen` → tagged N (was previously PROPN via the capital-letter heuristic). Does not yet handle unhyphenated morphological compounds where the last morpheme would require an expanded suffix list or globasa_tokenizer integration.

- [2026-05-14] **Multi-word entries with `WordClass == "jm"` must NOT collapse**: 41 phrasal entries in word-list.csv have just `"jm"` as WordClass — they mix PoS categories (`cel na` = prep+par, `imi am` = pron+par, `sen anti` = cop+prep, `le no` = par+adv, `max kom` = det+conj, etc.). If `globasa_pos.tokenize` collapses them into one token, `assign_pos` falls through to UNK because `jm` matches no class, and the constituents lose their per-word effects (most importantly: `na`'s infinitive-V signal). `tokenize` now guards every multi-word match with `_multi_word_collapsible(lemma)` which rejects `WordClass == "jm"` exactly. Phrasal classes carrying a PoS prefix (`p jm`, `l jm`, `n jm`, `t jm`, `f jm`, `m jm`, `s jm`) still collapse — they have a usable tag.
- [2026-05-14] **Phrasal WordClass ordering is PoS-first**: word-list.csv uses `"p jm"` / `"l jm"` / `"n jm"` etc., NOT `"jm p"` / `"jm l"`. `globasa_pos` class sets like `PREPOSITIONS = _wc_set("p", "jm p")` miss the 138 `p jm` entries — same for any other class set written with `"jm X"` ordering. **TODO**: when adding phrasal-PoS support, use `"p jm"` form (and similarly `"l jm"`, etc., which `CONJUNCTIONS` already gets right).
- [2026-05-14] **PROPN / PRON / N immediately after a PREP are PP-internal**: Stage 3 Step 1 in `globasa_pos.assign_pos` now adds those already-resolved positions to `prep_resolved` when they're the PREP's projection target (possibly after transparent t/dm/ADV). Previously only b-class objects of PREP were tracked, so e.g. `in Englisa` left `Englisa` as a clause-level subject signal — SVO's `has_local_subj` branch then mis-resolved the following b's (the trigger for the `Maxori hikaye bekrea ...` regression where `Maxori` flipped to ADV and `hikaye` to V).
- [2026-05-14] **Coordinating vs subordinating CONJ for SVO**: `globasa_pos.COORD_CONJ_LEMMAS = {ji, or, nor, mas, iji, kam, ji pia, ji max ..., mas fe hataya, mas fe tayti, mas sol eger}`. Coordinating CONJ is **transparent** to `is_clause_boundary` so SVO sees an extended clause across `ji`; subord CONJ (anything containing `ki`, plus `hu`/`ku`/`kwas`/`eger`/`kom`/`harki`/`folki`/...) remains a hard boundary. SVO Step 2 walks segments split by coord CONJ and uses **adjacency propagation**: the first unresolved `b` of each segment is forced to the previous segment's rightmost N/V/PRON/POSS/PROPN anchor, but only when the segment lacks its own subject (PRON/POSS/PROPN not prep-resolved) — independent fragments like `... ji yu suki filme` keep their local SVO frame. Global `has_verb` from any segment carries forward so `Vyata ji imanu sen muhim` resolves both `b`s to N. CONJ display tag is left as-is (the earlier display-inheritance pass was removed — conjunctions show as CONJ).

- [2026-05-14] **CG3 `NOT -1* X BARRIER Y` silently fails when the barrier intervenes** — it only succeeds when the leftward scan reaches start-of-sentence without finding X. To make a "no X to the left within barrier scope" test that ALSO succeeds when the barrier fires before any X is found, use `NEGATE` instead of `NOT`. This caused apertium-glb's rule 88 (lone-b → N fallback) to silently fail at every clause boundary; switching to NEGATE made it fire correctly.
- [2026-05-14] **apertium-glb CG mirrors globasa_pos.py's coord+SVO logic**: Section 2 runs rules 88 (lone-b NEGATE with `(NEGATE -1 (cnjcoo) LINK -1 (vblex))` parallel-verb guard), 91 (Nom-left → V, with `NEGATE -1* (vblex) BARRIER AnyVerbOrClause` to skip still-ambiguous coord neighbours), and 94 (verb-left → N) iterating together so they chain on each other's outputs. Section 3 then SELECTs vblex on a b that follows `cnjcoo` whose previous conjunct is an unambiguous verb, and re-runs rule 94 to catch any newly-resolved verb's object. Source: `/home/paleos/ApplicationSource/GlobasaTranslation/apertium-glb/apertium-glb.glb.rlx`. The pair `apertium-glb-eng` copies `glb.rlx.bin` from `/usr/local/share/apertium/apertium-glb/` at build time, so local changes need either an apertium-glb install (needs sudo) or a direct `cp` to `apertium-glb-eng/glb-eng.rlx.bin`.
- [2026-05-14] **CG3 t-resolution must barrier on the *other* b category**: rules of the form `SELECT (adj) IF (1* (n) BARRIER TConnect)` look past a closer verb to find an n further on, mis-tagging a t-class word as adj when it actually modifies a following verb (e.g. `Le velosi yam pingo`). Use `BARRIER TConnect OR AnyVerb` on the adj/det selects and `BARRIER TConnect OR (n) OR (prn)` on the adv select so the nearest b's category wins.
- [2026-05-14] **Lexilista_parser `_TRANSLATION_ANNOTATION_MAP` is Esperanto/Spanish-only** (`s:`, `tr:`, `intr:`, `adj:`, `adv:`, `interj:`, `prop n:`). But word-list.csv's French / Russian / Chinese columns now use the English-style annotations (`n:`, `v.tr:`, etc.) — the parser doesn't recognize them, falls back to positional alignment with English, and leaves the literal prefix in `pg.gloss`. Consumers either need to defensively strip leading annotations (see `dictionaryPreprocess.py` `_LEADING_ANN_RE`) or the parser must be extended to consult `ANNOTATION_MAP` as a secondary table during `_parseTranslation`. TODO if/when downstream needs cleaner glosses across the board.
- [2026-05-15] **`<sint>` is an English-side tag, not Globasa**: Globasa does not inflect adjectives. The `<s n="sint"/>` sdef in apertium-glb*.dix marks English adjectives whose comparative is **synthetic** (`big`→`bigger`) rather than **analytic** (`beautiful`→`more beautiful`). Source of truth: `apertium-eng/apertium-eng.eng.dix` — adjective entries reference a paradigm name like `big/__adj`, `happ/y__adj`, `expensive__adj`; paradigms whose body contains `<s n="sint"/>` are synthetic, `expensive__adj` (and similar) are analytic. `dictionaryPreprocess.py` loads this set at startup (`_load_synthetic_adj_set`, currently 491 lemmas) and tags only English bilingual adj glosses. Lemminflect is unsuitable — it happily produces "beautifuler", "intelligenter", etc.
- [2026-05-14] **Apertium dixPreprocess emits 14 files**: `dictionary_{En,Es,Eo,De,Fr,Nl,un}_{fn,content}.xml`. Function-word classification uses the parsed English head PoS (PREP/DET/CONJ/PART/PRON/NUMBER) — robust to compound WordClass like `p; lfik` or `num; d`. Verb subtype maps: AUXILIARY→`vbmod`, COPULAR→`vbser`, else `vblex`. Foreign gender markers (`<m>`, `<f>`, `<n>`, including slash-list `<m>/<n>`) are only present in `menalariExtension_edited.tsv`'s German/French/Dutch columns, not in word-list.csv's TranslationDeu/Fra — preprocess prefers word-list (richer coverage) but reads Dutch only from menalariExtension.
- [2026-05-14] **List-commas count as elided coord CONJ**: `assign_pos` precomputes `list_comma_positions` after Stage 2. A comma at position k is a list-comma only when (i) the left side ends an NP coord-item (`_ends_coord_item` walks back through modifiers to a b/N/PRON/PROPN/POSS head), (ii) the right side starts one OR is a coord CONJ (`_starts_coord_item`), and (iii) a coord CONJ is reachable forward without crossing a subord CONJ / `na` / sentence-end. Both `is_clause_boundary` and the SVO segment splitter consult this set; list-commas produce segment splits (kind="comma") in addition to coord-CONJ splits (kind="conj"). The dual-side check correctly excludes sentence-initial topical commas like `Xali, oto ...` (Xali is t-class with no NP head behind it).

- [2026-08-24] **Never name a scratch script after a stdlib module.** A throwaway `inspect.py` in the scratchpad dir shadowed the stdlib `inspect` for anything on `sys.path`, so `import spacy` (which does `import inspect`) executed the scratch script and died with `AttributeError: module 'inspect' has no attribute 'signature'`. Same trap applies to `types.py`, `json.py`, `csv.py`, `re.py`, `copy.py`.
- [2026-08-24] **`cmd | grep ...` / `cmd; echo $?` masks a failing exit code** — the pipeline reports the last command's status, so two failed alignment re-runs looked like "exit code 0". Redirect to a log and propagate explicitly (`python ... > log 2>&1; code=$?; exit $code`) when a background run's success matters.
- [2026-08-24] **Gold priors must be merged AFTER `migrate_gold_tsv.py` re-anchors sids**, and the alignment re-run for that language must come after both. Correct order when passage data changes: patch TMX -> `run_giza_improved.py --eflomal` -> `migrate_gold_tsv.py` -> re-run the affected language pair so the re-anchored gold feeds its priors.

- [2026-09-01] **Never read Anki note fields by hardcoded ordinal.** `apkg_image_sync.py` had `img=14, src=15, gif=19, gif_src=20`, captured before AnkiMaker3 v3 inserted the per-VerbType fields at ordinals 11-18. Ordinal 14 is now `IntransitiveCu`, so the sync was reading verb-type text as image URLs, and the second notetype's offsets were wrong too. Resolve ordinals from the deck's own `fields` table by NAME (`SELECT ntid, name, ord FROM fields`) — the same rule already established for `word-list.csv` headers.
- [2026-09-01] **When adopting a renamed Commons file, keep the old title.** The MediaWiki API follows file redirects and returns the new canonical title; discarding the old one makes the next `apkg_image_sync` treat the deck's pre-rename URL as a different picture and import it twice. Former titles live in the image's `aka` list, and `images_store.image_keys()` returns canonical + former identities for matching against any outside source.
- [2026-09-01] **Don't `pkill -f "<script>.py"` in this harness** — the pattern matches the wrapper shell running the command, killing your own session (exit 144). Find the process by port instead: `ss -lptn 'sport = :5000'`.
- [2026-09-01] **curl to localhost needs `--noproxy '*'`** in this sandbox; the ambient proxy swallows 127.0.0.1 requests. Chromium cannot run at all here (`socket() failed: Operation not permitted`), so browser screenshots are unavailable — verify DOM-building JS by extracting the functions and running them under `node` with a small DOM shim.

- [2026-09-01] **`.pos-noun` / `.pos-verb` in word_viewer.html are bare class selectors carrying a `background`.** Putting one on a container (I put `posCssClass()` on `.gallery-row`) paints a full-width coloured block. Apply them only to small inline labels, or scope the rule.
- [2026-09-01] **Every image dedupe must use `images_store.image_keys()`, not `image_key()`.** Both `migrate_images_jsonl.py` and `apkg_image_sync.py` read from sources (the legacy TSV, the Anki deck) that still hold pre-rename Commons URLs; matching on the canonical key alone re-imports the same picture under its old title. Fixed once in the sync script and then missed in the migration — check both whenever the identity rules change.
- **2026-09-02** -- Do not let `parseEntry` expand gloss context. A plain parenthetical after the colon was being split into two readings, doubling the text in a PoS slot ("that; that one") or silently dropping the parentheses ("be on top of" for "be on top (of)"). 568 rows were affected. The expansion belongs to `parseWordEntry` only. See bug-190.
- **2026-09-02** -- When rewriting `word-list.csv`, hand the file object straight to `csv.reader` and write with the original terminator. Splitting on `str.splitlines(True)` breaks on the exotic line separators it also splits, and defaulting to "\n" rewrites the entire file instead of the 6 intended rows.
- **2026-09-02** -- Do not run `apkg_image_sync.py` after pushing the store into the deck. It syncs deck -> store, the opposite direction, and while the curated store supersedes the deck it can only pollute it (it duplicated an unresolved image on colo/coloya -- bug-191). The push direction is `update_vocab_deck.py`.

- [2026-10-25] **Check an incoming Globasa__Vocabulary.apkg for scheduling before running the deck scripts.** The 08:44 copy was a study-profile export (63,546 revlog rows, 9,981 review cards) despite the "no scheduling" note above; update_vocab_deck exports with_scheduling=False, so the output reset every card. History survives only in Globasa__Vocabulary.apkg.pre-restructure.bak. update_vocab_deck now warns. Test: `sqlite3 collection.anki2 "select count() from revlog"`.

- [2026-10-25] **The wordlist renamed `v.intr (optional -cu)` to `v.intr (optional use of -cu)`** (130 entries; Epo `nedeviga uzo de -cu`, Spa `uso opcional de -cu`). Lexilista_parser's ANNOTATION_MAP knew only the old spelling, so every -cu gloss fell to plain Intransitive and 123 Nenojetoli(-cu) card pairs went blank. After pulling a new word-list.csv, diff AnkiList.csv per column against the previous one -- a column-wide shift is a parser/format break, not lexicon edits.
- [2026-10-25] **Anki never deletes a card whose front an edit has emptied** (that is Tools > Empty Cards), and cards generated by `update_note` IGNORE the template's deck override. update_vocab_deck.py now removes empty cards of its own notes and moves strays into their subdeck on every run.

- [2026-10-25] **The Claude Code sandbox mounts /media/paleos/Warehouse2 read-only.** Clips can be read from Ektor_su_Lafuzu_processed but not written; exports into it must go through the user's own Word Viewer (/splits), not a script run from the session.

- [2026-10-25] **The user's Word Viewer runs with Flask's auto-reloader, and it can reload MID-EDIT.** A multi-step change (lookup body first, helper function second) left the live server with the first edit only: every /lookup was a NameError 500 until the file was touched again. After editing Word Viewer.py while it runs, `touch` it once at the end and hit the changed endpoint on 127.0.0.1:5000 to confirm.

- [2026-10-25] **Never derive a word's senses from its TAGS.** The first seed gave every fruta/sabzi/danyam/hoxinlyo/herba/planta word a "living plant" te sense, so danyam (grain, cereal), risi, estroberi and every spice got te (user: "too sloppy"). A word has a sense only if its dictionary gloss names it -- read Eng AND Epo (Esperanto separates frago fruit / fragujo plant). Both te and to only where the glosses list a plant and a product (funduku "hazel, hazelnut", kanabis "cannabis, marijuana", lawrel "laurel, bay leaf", Epo arakido/ternukso). A taxon (_Malus_) only identifies the species; it is not a plant sense. Tags like danyam's "planta" are topical.

## Decision Log
- [2026-11-07] **Richer shapes + symmetry (user):** dihedral group acts on the inventory; pair/triple contacts computed per orbit representative (12 reps) and copied (_by_symmetry), plus whole-alphabet rotate/mirror moves and best-of-group orientation at the end. A 30-degree direction grid hurt (only 6 distinct orientations per shape vs 8 at 45 degrees). Distance-based look-alikes (shape_distance; same < .13, similar < .16) must not mark cross-family pairs similar unless nearly identical (< .13): calling line vs semicircle "similar" (.145) wrecked results (cost 5-7k vs 2k).
- [2026-11-07] **Tangles (user: "messes like this are to be avoided"):** what worked was precomputing contacts between the 1st and 3rd letter of every stroke triple (84^3, parallel, seconds) so the main search sees them, with CONTACT/OVERLAP_MS 8000; leader went from ~5-7% to 3.6% of words with contact. What failed: flat per-pair/per-window contact charges (150 ms per pair, 5 ms per window) over-constrained the search into identical signs and few sharp joins; identical signs now cost 5000 ms. Rounded-join drawing is not the source of measured contacts (checked).
- [2026-11-07] **Globasa text available in this project is only ~30k tokens (Doxo_passages.tmx already contains every Corpora/ text; word-list.csv has no example sentences; doxo-pages-grav md pages are eng/spa/epo site text; xwexi submodule is empty).** More statistics therefore come from the lexicon (9,008 written forms) and structure: shorthand_word_stats.py. Function words joining the next word = WordClass par/p/l (pronouns pn stand free): 10.4% of word boundaries, top junctions ud it os im. Lexicon misreading ranks vowel pairs worst (a/o 0.99%, a/i 0.94%); protected pairs are not collision-free in the lexicon (l/r 0.14%). Collision check now mixes text and lexicon 50/50.
- [2026-11-07] **Cost refinements from shorthand principles (user asked to check):** added SOFT_RUN_MS (Callendar s.8, two soft joins in a row), CIRCLE_ON_LINE_MS (s.13, circles best on curves), ERROR_ANGLE_MS (Cao & Zhai 67.5 degree joints). Proposed, not built: cross-word joins for unstressed function words, per-letter lineality (s.11), position-specific facility (s.30), left-hand testing.
- [2026-11-07] **Curve compatibility at joins (Callendar s.8, s.54), as now coded in shorthand_optimizer.join_class:** sharp joins always clear; blunt joins merge beside a curve turning the same way; continuous joins are clear only at a point of inflection (two curves turning opposite ways), otherwise they read as one stroke. MERGING_MS 400 and RETRACE_MS 1000 were needed before frequent joins avoided merging (58 of the top 60 clean). Check the top-joins list after every rule change. The 50 commonest pairs may not merge or retrace at all (TOP_JOINS_CLEAN, flat 2000 ms per offending pair; user asked for it); offenders then cluster just past the cutoff (tu #51).
- [2026-11-07] **Shorthand stroke-time model (user asked for better shape ranking, Orthic as shape source):** shorthand_geometry.stroke_time = Cao & Zhai line time on the whole path length x power-law curvature slowdown (radius^(1/3) below 4 mm) x Callendar facility factors (horizontal curves 0.9, longhand loops 0.9, \\ slope 1.2). Cao & Zhai's own arc formula is not used below its 12-36 mm fitted radii. Inventory now 308 strokes incl. Orthic circle-ended lines/arcs. Restarts now within 2%; frequent letters stable across candidates (a e i small lines, o u h large lines, l/r small upright, m large arch, t circle, s small loop).
- [2026-11-07] **Shorthand optimizer result: flat landscape.** 12 restarts within 5% with different alphabets, and every weight change moved the best one, so the model narrows but cannot choose; the user's hand test decides. Pairwise look-alike costs must use a whitelist (rule-protected pairs only): summed pairwise misreading let a first run make 23 pairs alike. Known gap: cost sees only letter pairs, so whole outlines can cross themselves; next step is word-level scoring. User asked about better time models (power law, KeyTime) and a variational rational-spline refinement: agreed answer is a second stage after the hand test.
- [2026-11-07] **`manualofcursives00calliala.pdf/.epub` is Callendar's 1889 phonetic Cursive Shorthand, not the later orthographic Orthic manual used earlier.** Its alphabet table is NOT Orthic (user correction 2026-11-07): never attribute its signs to Orthic. Orthic itself (orthic.shorthand.fun/manual, glyphs at /assets/manual/<X>.png, fetchable with curl here): V = long open U (hairpin), its small form = ste; J = longhand j (loop below the line); G = left half of capital G; L/R mirrored small loops; two sizes, P = 3x S, O = 3x A, D = 3x T. EPUB is OCR and garbles numbers and signs (it lost half of section 54); check the PDF page (PDF page = EPUB page + 1) for any figure. Joining rules: sharp under 90 degrees best; blunt 90-135 must be marked; over 135 may slur unless between straights or beside a same-sense curve; avoid two continuous joins in a row; two sizes only; curvature alone unsafe; hooks unsafe; lift 0.1-0.3 s. Scored in shorthand_style_metrics.py.
- [2026-11-07] **Shorthand practice sheet built (`shorthand_practice_sheet.pdf`, scripts now in repo, not scratchpad).** Consonants are provisional and exist only to compare vowel styles; they were fitted to the zigzag first, so joint and drift figures may favour it. Relative model time: zigzag 1.00, marks 0.94, arcs 1.05, circles 1.90. Next step is the user's hand test; polisher only after a hand-tested set exists.
- [2026-11-07] **Shorthand joins:** a low modelled time for a reversal says nothing about readability. An exact reversal retraces the same line, so signs that end near the opposite of a connector's direction are unreadable. Check interior angle under 25 degrees, not only time.
- [2026-11-07] **Paper access in this sandbox:** curl and WebFetch to gery.casiez.net are blocked by the egress proxy. None of Vatavu, Leiva, Castellucci, Roldan-Pardo, Morin, Meulenbroek, Pelli is in Zotero as of today, so the report's reading-list section rests on the sweep's readings.
- [2026-11-06] **Shorthand full-text findings (Cao & Zhai 2007, Isokoski 2001, Matić preprint; all in Zotero, not all on disk):** full-circle vowels are 1.3-2x slower than one-line marks by every model tried. T(line)=68.8 L^0.469 ms, T(arc)=angle·r^0.414/0.0153 ms: doubling a line adds only 31-38%, a 1/3-length mark costs about 60% of the time. Corner angle adds under 40 ms net, including full reversals, but splitting a stroke costs 1.4-1.5x. Joints near 67.5° are most error-prone; 45°/225° lines are fastest but twice as error-prone as primary axes; vertical upstrokes slowest. Model is ranking-only and tested at 15-90 mm, far above writing size.
- [2026-11-06] **Check Zotero for papers the user says they have.** Zotero fulltext on the parent item can report no attachment: call zotero_get_item_children, then zotero_get_item_fulltext with the attachment key. PDFs live under /media/paleos/Warehouse2/Zotero/storage.
- [2026-11-06] **Shorthand optional marks (user idea, not evaluated):** merged pairs such as s/z may take a small mark in unhurried everyday writing, like Orthic's dotted i against e. Unmarked writing stays valid. To check after the practice sheet: whether length-separated pairs (k/g, c/j, f/v, p/b) could become one sign plus an optional mark.
- [2026-11-06] **Shorthand stroke inventory and polisher (planned, not built):** inventory = shape x orientation x length: straight (4 orientations), quarter arc (8), semicircle (8), each short or long = 40 visible strokes, 80 with travel direction. Polisher: user signs in a table; score bigram-weighted stroke time plus pairwise distinctness (Cao & Zhai E metric); search small edits (swap, rotate, flip travel, change length) and report ranked suggestions only. Legibility is a hard constraint, or speed alone collapses signs into tiny zigzags. Hand test stays the judge.
- [2026-11-06] **Shorthand role vs benchmark (user):** cursive names the role (an everyday hand), not the speed target. User already knows mixed writing beats cursive, so benchmark against the writer's normal hand, and do not present that finding as news. Unbroken outlines stay the default: per the user, they gain speed partly by disregarding the writing line, a freedom Latin mixed writing lacks, so its speed gain from lifts does not transfer. Lifts are at most an escape for long words that climb off the line.
- [2026-11-05] **Idea parked, not started:** the shorthand could be the basis for a math notation (user idea). First question to settle: which stroke shapes stay free once the alphabet is fixed, and whether math symbols can use them without colliding with letters. Pick this up after the vowel-style practice sheet.
- [2026-11-05] **Marti's Taquigrafia Castellana (repo root PDF):** consonants share signs by sound, signs come from a circle plus lines (4 lines, 4 semicircles, 1 quarter arc, 6 hooked variants), vowels are 1/3 consonant length, e/i are implied by a bare consonant, and each word is one unbroken stroke. Lengthening a stroke implies repeated consonant with e/i, which conflicts with a low-friction hand. Marti's rule applied directly to Globasa: 81.3% of letters kept, 3.32% context-free error, mostly te/ete and mi/imi.
- [2026-11-05] **Shorthand models for Globasa:** Duployan/Chinook writing is the closest baseline (geometric, vowels written, used for a contact language). Japanese single-stroke syllable systems (Nakane, Kokuji) suggest one-stroke signs for the most frequent syllables as a rapid tier. Gabelsberger (vowels at word edges, medial vowels symbolic) parallels the reporting-tier first-vowel rule, but its positional method needs ruled lines. Stroke charts for the Japanese systems and mechanics of Marti/Karundeng were not checked.
- [2026-11-05] **Print script shape draft v2** (scratchpad `print_shapes.py`, not in repo): stacked blocks with onset on top, vowel below, medial rising above and coda descending. Vowels are a=chevron, e=bar, i=stem, o=ring, u=cup; consonants are Latin-like skeletons. CV complexity 70, CVC 100, 44-49% narrower than DejaVu at matched blur discrimination. Known flaws: c/d near-mirror, b/h/p cluster, t/y, o/u at small sizes, and tall line pitch from codas.
- [2026-08-24] **Thirty Short Stories body face: Vollkorn**, replacing Bodoni Moda 9pt (headings stay Sour Gummy at 25pt). Chosen from a rendered specimen comparing Bodoni Moda, Bitstream Charter, TeX Gyre Pagella, Alegreya and Vollkorn at 14.5-16pt. Rationale: a Didone's hairline serifs are fragile at reading sizes for learners decoding unfamiliar words, and its neoclassical tone competes with the deliberately childish display face; the display face should carry the personality while the body face stays warm and quiet. Specimen generator kept at `Corpora/font_specimen.typ` (disposable).
- [2026-08-24] NOTE: this sandbox's font visibility does NOT match the user's Typst environment — Bodoni Moda, Sour Gummy and Vollkorn all render for them but are invisible to `fc-list` here. Never conclude a font is unavailable from `fc-list` alone; ask the user or have them check with their compiler.


- [2026-04-20] OpenWolf DesignQC, Reframe, and Dashboard features disabled — project is Python CLI scripts, not a web app. These features add noise without value.
- [2026-04-20] Excluded venv/, giza_output/, doxo-pages-grav/, Wiktionary_dump/, WiktionaryPickled/, Images/, DoxoBased/, TekstaroBased/ from anatomy scan — data artifacts that bloat anatomy.md.
- [2026-04-20] Replaced gramati-fe-globasa-eng/ with git submodules: xwexi-pages-grav (lessons/grammar) and doxo-pages-grav (reader texts), both from Globasa-Team GitHub org.
- [2026-04-20] Lexilista_parser.py rewritten: annotation-based parsing (not positional), multi-language PoS-tagged output via parseWordEntry(), VerbType extended with FEELING/STATE for hisi/jotay verbs, AffixType enum for marking suffixes with their induced PoS, GlossPoS cleaned up (removed SUFFIX/NOUN_SUFFIX/etc.), qualifier extraction from parentheticals, gloss context expansion for (optional) parentheticals.
- [2026-04-30] Factored GIZA++ alignment: use `word|POS` tokens where GIZA++ sees `|POS` as part of the vocabulary entry. Globasa POS from PosTagger.py (contextual disambiguation), English POS from spaCy. Internal compound morphemes are untagged — only the head (last morpheme) gets the compound's resolved POS. This constrains GIZA++ to align within compatible POS categories without requiring any modification to GIZA++ itself.
- [2026-04-28] Three-script architecture for Wiktionary pipeline: (1) English extender → GLB_ENG_WiktionarySenses.xlsx, (2) Multi-Wiktionary sense curator (interactive CLI) → GLB_MULTI_WiktionarySenses.xlsx, (3) Extension builder reads both xlsx + LMDBs → menalariExtension.tsv. Non-English Wiktionary JSONL from kaikki.org, ingested via parameterized parser to WiktionaryLMDB_{lang}/.
- [2026-04-21] `make_tmx.py` INPUT changed from `Doxo_passages_edited.csv` to `Doxo_passages_edited_updated.csv` — the `_updated` file is the canonical source for TMX generation.
- [2026-04-21] Only `Doxo_passages_edited_updated.csv` receives parallel text updates; the non-`_updated` version is left as-is per user preference.
- [2026-04-21] LLM_sense_judge.py uses 5-tier pipeline (all→Script?): T1 core match, T2 register/domain, T3 Qdrant corpus, T4 composite, T5 WordNet oewn:2023 with core-only synset filter. Core-only filter: `parse_translation(core_only=True)` strips segments with `(sexual)`, `(slang)`, etc. qualifiers to prevent homonym synsets (e.g. ball-dance) from polluting expansion. qdrant_client v2+ uses `query_points(using=VECTOR_NAME)` not `search`. 18K rows remain for local LLM (Qwen ~14GB VRAM) as next tier.
- [2026-09-01] **Images are per sense and per part of speech, not per word, and the gallery is a definition rather than decoration.** Goal: a learner should get the meaning from the pictures without leaning on a good gloss. Hence several images per sense (one dog is a dog, three dogs is the concept), hand-ordered by prototypicality, grouped so each PoS shows its own gloss beside its own pictures, three shown with "+N more". The Anki notetype's two still fields are a limit of the card, not of the store: `anki_slots()` takes one still per PoS group so the card's images line up with the PoS1/Mena1 and PoS2/Mena2 glosses printed beside them. Senses are hand-authored — never derived from word-list segments — because deciding which gloss an image illustrates is editorial.
- [2026-09-01] **Images live INSIDE the translation table, one cell per PoS row — not in a separate gallery above it.** The first cut put a captioned gallery above the table, which printed every gloss twice (once in the caption, once in the table's English cell). Constraints "each PoS gloss shown with its images" + "no gloss twice" together admit only one layout: the pictures go in the table beside the gloss that is already there. `buildImageCell` renders the cell; the column appears only for words that have images, so the ~7,300 imageless entries are untouched. `#imageSection` above the table is now only a fallback for images whose `pos` is unassigned.
- [2026-09-01] **Hyponym-derived galleries are live for hypernyms, opt-in per sense.** A sense carries `"derive": {"tag": "calyo"}` (or `"words": [...]`, plus `"exclude"`), and `Word Viewer.expand_derived_senses` fills it at render time from the lead image of every word carrying that tag — reusing the `_tag_index` already built at startup. Resolved at render time, never written into the JSONL, so the set improves whenever a hyponym gains an image; derived entries carry the hyponym's Globasa word and the expanded gallery captions them with it. AnkiMaker3 never sees them, because nothing derived is stored. `calyo` currently yields 17 hyponyms. Opt-in is essential: the Tags column mixes IS-A with topical tags.
- [2026-09-01] **A row's images tile into ONE fixed box (200x150), never a growing strip.** However many pictures a PoS row has, they occupy the space of a single image — 1 fills it, 2 split it, 3 go big-left/two-right, 4+ make a 2x2 with a `+N` badge — so an illustrated row is never taller than a plain one. The full set is one click away in `showGalleryOverlay`, which groups by sense and captions derived images in Globasa.
- [2026-09-01] **Always verify a store write by RELOADING from disk, never by printing the in-memory mapping.** `save_images` silently dropped three derive-only records and the in-memory dict still looked correct; the loss only showed up when the viewer rendered nothing. `images_store.is_empty_record` now defines what may be dropped.
- [2026-09-01] **Hypernyms with a derived gallery**: `calyo` (17 vehicles), `futru` (5 fungi), `yamxey` (55 foods), `flura` (17 flowers), `hewan` (20 animals), `mamoyen` (60 mammals). Derivation does NOT cascade — `mamoyen` is tagged `hewan`, but since `mamoyen` owns no image it contributes nothing to `hewan`'s grid; each hypernym draws only on its direct hyponyms' own images. Note `flura`'s noun group also covers an anatomical sense, so its derived flowers sit on a row whose gloss reads "flower, pussy"; the sense is labelled `flower` in the store.
- [2026-09-01] **Slang/vulgar/sexual noun senses get their own table row**, like a verb's transitivity does. `build_translations_payload` keys pos_groups on `(pos, verb_type, register)`; `register` comes from `Lexilista_parser.normalize_register`, which maps every qualifier spelling in word-list.csv onto one of `informal`/`sexual`/`vulgar` — each language writes its own (`obscena`, `vulgaire`, `familier`, `seksa kunteksto`), so matching the English string alone silently fails. An unknown spelling normalises to None and lands on the plain row: a safe failure. Only NOUN glosses split; `adj (for animate nouns)` and `v.intr (optional -cu)` are conditions on one sense and must never split a row. 19 words are affected, the same 19 that populate Anki's SlangMena.
- [2026-09-01] **The menalariExtension cells are read POSITIONALLY and are grouped by the register-blind `(pos, verb_type)` enumeration.** Adding any new pos_group dimension shifts every later language cell up by one — the register split put flura's French `fleurir` ("to bloom") on the sexual row. `build_translations_payload` therefore keeps a separate `ext_slot` index that ignores `register`, and a register row simply has no extension-language data. Any future row-splitting dimension needs the same treatment.
- [2026-09-01] **The translation table's second column carries BOTH a verb's transitivity and a noun's register.** A noun's registers are sub-rows of "Noun" exactly as transitive/intransitive are sub-rows of "Verb": the PoS cell rowspans them and the type cell holds `sexual`/`vulgar`/`informal`. `buildTransTable` groups consecutive same-PoS rows generically (`runKey` folds "verb phrase" into "verb"), so there is no longer a special verb branch. The column appears when `has_verbs || hasRegisters` — `gigi` is informal-only with no verb and still needs it. A run with nothing to say in that column keeps the old `colSpan = 2` PoS cell, so ordinary words look untouched. The header uses the `type` i18n key (added 2026-09-01, 45/46 languages, Globasa `Tipo`); the older `verb_type` row is left in the CSV but no longer drives the header.
- [2026-09-01] **Word Viewer's routes must be defined ABOVE the `if __name__ == "__main__" or True: app.run(...)` line at the bottom of the file.** `app.run()` blocks, so anything appended after it never registers and every new route 404s. Appending to the end of Word Viewer.py is always wrong.
- [2026-09-01] **`_all_entries` now carries `TranslationEng`** (added for the curator). It previously held only WordClass/Synonyms/Antonyms/Category/LexiliAsel, so anything needing a word's gloss for the whole lexicon had nothing to read.
- [2026-09-01] **The image curator's queue filters to CONTENT parts of speech by default** (`images_store.pos_kind(k) is not None`). Unfiltered it is 7548 words led by `sen`, `te`, `le`, `na`, `mi`, `ji`, `fe` -- particles, pronouns and prepositions sit at the very top of the course ranking and none of them will ever have a picture. Filtered it is 6939 led by `sen`, `loga`, `oko`, `piu`, `fikir`. An `all=1` param / checkbox restores the full list.
- [2026-09-01] **`images_store.is_empty_record` is generous on purpose: only a bare `{word, senses: []}` is dropped.** It bit twice — derive-only hypernym records (bug-186), then a curator-added empty sense (bug-187) — because the rule was "no images means nothing to save". A sense with no images yet is intent; so is any key the module does not recognise. Deleting the last sense is what decays a record back to droppable.
- [2026-09-01] **Test store writes on a word that has NO images.** The curator's write actions were all exercised against `oko`, which already had a picture, so its record survived `save_images` and the drop bug stayed invisible. The empty-word path is the one that exercises the persistence rule.
- [2026-09-01] **Never re-render a list from a container click handler that wraps input fields.** The curator's `.sense` div called `renderSenses()` on click; clicking the label input inside it bubbled up and destroyed that input mid-click, so the field could not be typed in. Selection changes must toggle classes (`setActive`), not rebuild. Same rule applies to any future editable row.
- [2026-09-01] **Curation writes the JSONL; the dictionary serves the LMDB `images` sub-db — they are not the same thing.** `POST /api/images/publish` ("Update dictionary" in the curator) runs `resolve_commons_images.py` for anything still `unresolved`, then rewrites only that one sub-db from `build_image_rows()`. Seconds, versus `/rebuild` re-reading every source file. Curated images do render before publishing — `best_url` falls back to `Special:FilePath` — so skipping it costs speed, not correctness.
- [2026-09-01] **`images_store.save_images` rewrites the whole file (load → mutate → save), so two concurrent writers lose data.** Fine for one curator, but do not run a script that writes the store while the Word Viewer curator is open, and vice versa.
- [2026-09-01] **In the image curator the queue is the only way to open a word, so any filter on it is also a filter on reachability.** A search query therefore bypasses the "outstanding work" filter — a finished word must stay openable for revision. Keep this in mind before adding further queue filters.
- [2026-09-01] **Scientific names live in the gloss as italics** — `swallow (_bird_), martin, _Hirundinidae_`, `alpaca, _Lama pacos_`. `images_store.extract_taxon` reads them, requiring 4+ letters because the chemical elements italicise their symbol identically (`_Al_`, `_Sb_`, `_Ar_`): without that, 102 of 342 matches are elements. 232 words carry a real taxon.
- [2026-09-01] **Wikispecies hosts no files of its own** — every image on a taxon page is a Commons file, so those candidates are canonical titles and as rot-proof as any Commons pick. A taxon page usually has ONE lead image, so the curator also pulls `Category:<taxon>` from Commons: Hirundinidae goes 1 -> 32, Scorpiones -> 40. Not every taxon has a category (`Lama pacos` is a synonym of the accepted `Vicugna pacos`), so it is additive.
- [2026-09-01] **iNaturalist needs TWO calls**: `/v1/taxa?q=` returns a lean record whose `taxon_photos` is empty; the photos are only on `/v1/taxa/<id>`. **Its licensing is the real constraint**: of 12 photos for Hirundinidae, 5 are all-rights-reserved and the rest CC BY-NC or CC BY-NC-ND — across four taxa sampled, only 2 of 25 usable photos were CC BY, and none were CC0 or CC BY-SA. Unlicensed photos are dropped outright; the rest are stored as literal URLs (no canonical title, so `resolve_commons_images.py` skips them and they can rot) and flagged `restricted` in red. Commons/Wikispecies remains the default for anything that will be redistributed.
- [2026-09-01] **Curator candidate search is paginated with an opaque `cont` token, one scheme per source**: Commons search uses `gsroffset` (effectively unlimited — "bird" gives 188 unique over 8 pages and keeps going), the Wikispecies source uses the category's `cmcontinue` and terminates (Scorpiones 82, Hirundinidae 55), and iNaturalist has no continuation at all — `taxon_photos` is a fixed list on the taxon record. The frontend appends, dedupes on file-or-url (a file appears in both a taxon page and its category), guards against overlapping fetches, discards responses from a superseded query, and keeps pulling while the results are too short to overflow the panel — otherwise no scroll event ever fires and paging stalls.
- [2026-09-01] **Wikimedia rate-limits rapid paging and the endpoint returns 502.** Seen while paging 8 Commons pages back-to-back; it recovers after a couple of seconds. Treat an isolated 502 from a candidate search as transient, not a bug.
- [2026-09-01] **xwexi on the b-class noun/verb relationship** (`03.gramati/02.inharelexi`, `07.falelexili-morfo`): Globasa marks the gerund with the prefix **du-** — `dulala` "(the act of) singing", `dudanse` "(the act of) dancing" — and a bare `b` noun is normally the CONCRETE noun, with `-ya` deriving the abstract one (`nasa` = nose + verb smell; `nasaya` = the sense of smell). So "the noun is the act of the verb" is a **lexical property of individual words**, not a rule about the class: `awcu` glosses `n: disappearance` and is the act, while `estuf` (n: stew) is the dish and `bulbula` (n: bubble) the object. 437 words have a noun gloss word identical to a verb gloss word, but that string match is NOT sufficient — hence `also_pos` is hand-declared, never inferred.
- [2026-09-01] **`also_pos` on a sense** lists further parts of speech the same images illustrate. `attach_images_to_pos_groups` attaches the sense to every listed group and stamps a `share` id; `buildTransTable` gives consecutive groups carrying the same share id ONE image cell with a rowSpan, so `awcu` shows the picture once across its Noun and Verb rows. The curator queue counts a PoS covered this way as illustrated.
- [2026-09-02] **Uploaded images**: the curator can take a local file (button, drag-drop or clipboard paste). Stored under `Images/uploaded/` named by content hash, so re-uploading the same picture reuses one file. Validated by DECODING with PIL, not by trusting the extension or the browser's content-type. The image record carries `local` instead of `file`/`url` and `status: "local"` — nothing to resolve, so `resolve_commons_images.py` ignores it.
- [2026-09-02] **A local image is a bare filename in Anki, a URL in the viewer.** `best_url` gives `/user_images/<name>` for the dictionary; `anki_slots` emits just `<name>`, because that is how Anki resolves media out of `collection.media`. **The files must be copied there or the cards show nothing** — AnkiMaker3 prints the count and the cp command at the end of a run. The store references them by name, so `Images/uploaded/` is not disposable: without it a fresh clone has dangling local images.
- [2026-09-02] **node v12 is the only JS syntax check available here and cannot parse optional chaining (`?.`)** or other post-ES2019 syntax. Browsers handle it fine, but using it silently forfeits the only verification of word_viewer.html / images_curator.html, so write the long form.
- [2026-09-02] **There is no reliable automatic detector for an ill-fitting image, and I checked before building one.** Files shared between words look damning but are usually right (`adhesiente`/`leim` are both "adhesive", `artroitis`/`artroitisli` are noun and adjective of one thing); "the filename shares no word with the gloss" fires on 845 of 1803, including correct pairs like `adasisupa` -> Mercimek_çorbasi.jpg; generic camera filenames catch only 4. So `/review` shows many words at once for the eye to scan, and offers those signals as sorts and filters labelled as hints, never as verdicts.
- [2026-09-02] **Filtering the review sheet by tag is the useful move**: 60 `mamoyen`, 55 `yamxey`, 38 `piu` at a time, all one semantic field, where a wrong picture stands out immediately against its neighbours.
- [2026-09-02] **A hypernym illustrated only by hyponyms owns no image**, so anything iterating `all_images` skips it (`yamxey`, `flura`, `mamoyen` vanished from the review sheet until it resolved `derive` the way /lookup does). Watch for this in any future consumer of the store.
- [2026-09-02] **Any new bulk image view must handle NSFW before it ships.** A dense contact sheet is the worst possible place for an unexpected explicit image; `/review` shipped without a cover and had to be fixed.
- [2026-09-02] **NSFW is a flag on the SENSE, never on the word.** `melon` is a fruit and, in its vulgar sense, a breast; covering the word would hide a picture of a melon. `images_store.is_nsfw_sense` reads `sense["nsfw"]`, and only images in a flagged sense are covered — in the dictionary, in `/review` and in the curator alike. The six `graphic_blacklist` words each have one sense, which is marked, so they behave as before. `banana`, `flura` and `melon` are NOT covered, because the images they actually hold belong to their innocuous senses; if an explicit image is added later, tick NSFW on that sense. The curator has a per-sense NSFW checkbox and `POST /api/images/sense` takes `set_nsfw`.
- [2026-09-02] **`graphic_blacklist` is now only a seed**, not a runtime check: it was used once to mark those six senses. The store is the source of truth from here.
- **2026-09-02** -- Construction glosses are lifted out of `word-list.csv` itself (`extract_constructions.py`) rather than only at export time. The wordlist is the shared source for the deck, the dictionary and the sense tools, so cleaning it once beats every consumer re-deriving the exclusion. AnkiMaker3 still applies `to_exclude` as a safety net for a freshly downloaded wordlist.
- **2026-09-02** -- `_apply_to_exclude` and its helpers moved out of AnkiMaker3 into `constructions.py` rather than being copy-pasted into the new script -- the project already regrets duplicating `PoSDict` across four files. `apply_to_exclude` now returns `(text, matched)` so callers decide whether "no match" is a stale rule or an already-clean wordlist.

- [2026-09-07] **kaikki.org is a Wiktionary dump, not an independent source** (user correction). When a citation points at kaikki, treat it as citing Wiktionary and go to `en.wiktionary.org/w/api.php` directly — `action=query&prop=revisions&rvprop=content&rvslots=main&titles=A|B|C` takes up to 20 titles per call and returns raw wikitext, so a whole table of etymology claims can be checked in two requests. kaikki.org itself is blocked by this sandbox's egress proxy anyway.
- [2026-09-07] **`curl` returning HTTP 000 in this sandbox means the egress proxy blocked the host, NOT that the link is dead.** talkpal.ai, reddit.com, quora.com, kaikki.org, glottolog.org, europepmc.org and others all return 000 while being perfectly alive. Never report a citation as broken on that basis — WebFetch says `EGRESS_BLOCKED` explicitly and is the way to tell the two apart. clics.clld.org, concepticon.clld.org, en.wiktionary.org and raw.githubusercontent.com are reachable.
- [2026-09-07] **Reference data that IS reachable and worth reusing**: Concepticon concept list at `raw.githubusercontent.com/concepticon/concepticon-data/master/concepticondata/concepticon.tsv` (ID/GLOSS/DEFINITION); Glottolog at `raw.githubusercontent.com/glottolog/glottolog-cldf/master/cldf/languages.csv` (filter `Level==language` → 8618 languages, 246 families, 183 isolates); CLICS⁴ colexification edges are scrapeable from `clics.clld.org/parameters/<concepticon_id>` by grepping `/edges/<a>-<b>` hrefs, and `clics.clld.org/edges/<a>-<b>` lists the supporting languages. Useful for any future Globasa semantic-field question.
- [2026-09-07] **CLICS is the wrong instrument for abstract vocabulary.** It aggregates Swadesh-style basic wordlists, so FATE, JOY and HAPPINESS have zero colexification edges and HAPPY–GOOD LUCK rests on a single language. Before citing CLICS for a semantic claim, check the edge weight — a citation with no extracted data implies support that usually is not there.

### 2026-09-07 — Globasa semantics follow Esperanto, not English
**Do-Not-Repeat:** Do not analyse Globasa's semantics as English-derived. The user
corrected this: Globasa's semantic architecture is Esperanto's. Evidence in
`word-list.csv`: `hongu` (bore-hole) vs `goyu` (dug pit) are near-identical in the Eng
and Spa columns but cleanly separated in Epo (truo/bori vs foso/fosi). The affix
inventory is Zamenhofian 1:1 (-cu/-gi = -iĝ/-ig, -ya = -ec, -yen = -ul, -tul = -il,
-dom = -ej, pos- = mal-, du- = -ad, be- = passive). ~215 words use the pos-/nen-/bur-/
bon- polarity template, tracking Esperanto not English (posdoste = malamiko,
poshurudom = malliberejo, posasanya = malfacileco).

**Key learning:** The Epo column carries the FINEST distinctions in word-list.csv — it is
not redundant with Eng/Spa. Never treat English-gloss overlap as evidence that two
Globasa entries are synonyms; that test would flag hongu/goyu as duplicates.

**Key learning:** Predictive rule for what Globasa admits — a distinction enters easily if
it is analytically decomposable (root + affix), and resists entry if it is
non-compositional and obligatory (clusivity, sibling seniority, classifiers, honorific
register, evidentiality). Esperanto-style transparency is anti-colexification by design.
- [2026-09-07] **Markdown footnote definitions must each start a line.** Packing several as `[^a]: x · [^b]: y` on one line silently drops all but the first — only the leading one is parsed as a definition, the rest render as literal text. Validate any footnoted document by extracting `\[\^([^\]]+)\](?!:)` (refs) and `^\[\^([^\]]+)\]:` (defs) and diffing the two sets in both directions, plus checking for duplicate definitions.
- [2026-09-07] **Research-doc verification pays off disproportionately for this project.** The colexification doc had 11 factual errors in 20 rows, two of them refuted by the very source cited (Mongolian баялаг, Nahuatl paquiliztli), and one row quoting an Armenian word as Georgian. Anything arriving as "assisted research" with Talkpal/Reddit/Quora/WordHippo citations should be treated as unverified until each row is checked against Wiktionary or a real dictionary — the headline can be right while most of the supporting rows are wrong.
- [2026-09-07] **Globasa framing for happiness/luck**: `hox` (adj, happy+joyful) covers both state and trait happiness, and `xanse` "chance, luck, fortune" (from *chance*) is entirely separate — the American-English configuration, which Oishi et al. 2013 identify as the historical outlier among 30 nations. Most of Globasa's own big source languages (Mandarin, Arabic, Russian, Persian, German, Malay/Indonesian, Korean, Japanese, Vietnamese, Spanish, French) link the two. The "allotted share" metaphor shared by its Arabic (ḥaẓẓ), Persian (baxt), Hindi (bhāgya), Malay (bahagia) and Russian (sčastʹje) sources is unrepresented in the lexicon; `samrudi` is Sanskrit samṛddhi "prosperity", not bhāgya. Observation only — a language change is the Globasa community's call.

### 2026-09-07 — Decomposability rule REFUTED; Esperanto-alignment CONFIRMED
**Do-Not-Repeat:** Do not assert the "Globasa admits decomposable distinctions, resists
non-compositional ones" rule. Tested and refuted. Over 1859 English-merge/Globasa-split
sites: 17.3% carried by roots only vs permutation null 14.8% +/- 1.1% (z=+2.37, 2000
shuffles) — purely lexical splits are slightly OVER-represented, opposite to the
prediction. Globasa makes non-decomposable lexical splits freely (bage/mon, danyam/mais,
mismari/nakun). The 83% "derived" figure is an artifact: lexicon is 59% derived.

**Key learning (confirmed):** Globasa's root inventory aligns Epo > Eng > Spa. Merge counts
of Globasa root-pairs at all verbosity caps: Epo 249 < Eng 467 < Spa 600 (k=all); stable at
k=1,2,3. Symmetric disagreement test: Epo 71% vs Eng 29%; Epo 82% vs Spa 18%; Eng 59% vs
Spa 41%. Spanish is the WORST fit of the three gloss languages.

**Key learning (confounds):** ~20-30% of English-merge sites are English homonymy, not
colexification (beze/ibe "bee", eskela/harxaf "scale", bakxixi/dwan "tip"). Esperanto is
designed to avoid homonymy, so part of its lead is guaranteed by construction — the
Epo-vs-Spa contrast is the confound-free comparison.

**Working explanation:** Globasa splits where Esperanto splits; gaps are where no European
language including Esperanto makes the distinction. The filter is the evidence base, not
the morphology.

### 2026-09-07 — Esperanto transmission: architecture yes, lexicon unproven
**Key learning (project background):** Globasa's creator was active in the Esperanto
community before creating Globasa (per user). This supplies the causal route for the
morphological calque.

**Key learning:** Transmission is fingerprinted in the DERIVATIONAL system, not proven in
the root inventory. 60/79 pos- words gloss to Esperanto mal-; the diagnostic subset is the
>=10 where Eng AND Spa use a simplex root but Globasa+Epo both use a negation prefix
(posdoste/malamiko/enemy/enemigo, poshurudom/malliberejo/prison, posasanya/malfacileco/
difficulty, posfilya/malinklino/aversion, posamikuya/malprofundeco/shallowness).
Convergence cannot produce "enemy = un-friend" independently.

**Do-Not-Repeat:** The "Esperanto idiosyncrasy" discriminating test (Eng+Spa merge vs Epo
splits = 91, converse = 78, 54/46) is BADLY CONSTRUCTED — the sample is pairs of distinct
Globasa roots, so "Globasa splits" has no variance, and the denominators differ. Do not
cite the 54/46 figure as evidence either way.

**Synthesis:** Eurocentrism is concentrated in ~60-79 inherited morphological analyses of
concepts (posamusa=boredom, posdoste=enemy), a bounded auditable set — not a systemic
constraint, since Test B showed nothing prevents coining a root instead.
- [2026-09-07] **CLICS/Concepticon is English-anchored, so any distinction English does not lexicalise is invisible to it — and worse, scrambled** (user's insight, confirmed with data). Concepticon has no GLAD concept at all; of 17 happiness-adjacent concepts only HAPPY (904 forms), GOOD LUCK (315), LAUGH, SMILE, SAD, GOOD have any data, and JOY/HAPPINESS/CHEERFUL/MERRY/DELIGHT/CONTENT/REJOICE/PLEASURE/BLESSED/UNHAPPY/FATE have **zero**. With one happiness slot, a language that splits state from trait gets one word entered arbitrarily: Dutch HAPPY = *gelukkig* (trait, *blij* absent), Mandarin = *gāoxìng/kuàilè* (state, 幸福 absent), Japanese = *ureshii* with 幸せ filed under GOOD LUCK. Before using CLICS for any Globasa semantic-field question, check whether English lexicalises the contrast you care about — if it doesn't, CLICS cannot see it.
- [2026-09-07] **CLICS matches surface forms, so derivation is invisible to it.** Dutch HAPPY=gelukkig / GOOD LUCK=geluk fires no colexification edge even though one is derived from the other; same for Finnish onnellinen/onni, Estonian õnnelik/õnn, N. Saami lihkolaš/lihkku, Serbo-Croatian sretan/sreća, Bulgarian štastliv/štastie, L. Sorbian glucny/gluka, Romani baxtalo/bax, Sakha ʤolloːχ/ʤol, Greek eftixismenos/eftixia. The whole HAPPY–GOOD LUCK edge rests on Mlabri, where one string happened to be entered twice. A zero edge weight in CLICS means "no shared surface form", never "no semantic relationship".
- [2026-09-07] **The state/trait happiness asymmetry** (research finding, docs/research/colexification-happiness-luck.md): the momentary pole is usually a bare root, attaches to joy/glad/cheer/merry/lively/tipsy, and comes from shining, jumping, quickness, rejoicing, love, intoxication or ease — all body-visible. The enduring pole is usually derived or compound, attaches to lucky/blessed/content/fulfilled/prosperous/successful/harmonious, and comes from an allotted share, an omen, things fitting together, or fertility — all external to the person. Globasa's `hox` covers both poles while `truti`, `bonjotay`, `samrudi`, `armoni`, `xanti` and `barakado` lexicalise the whole enduring neighbourhood — the gap is an enduring-happiness word specifically.

### 2026-09-07 — Wiktionary verification of non-European semantic imports
**Key learning (verified, en.wiktionary API):**
CONFIRMED: Indonesian/Malay `hati` = liver + "seat of affections or sensibilities" (strongest
case; must be a NEW root, not an extension of `ganzo`). Indonesian `kami`/`kita` = exclusive/
inclusive we ("excludes/includes the addressee"). `padi`/`beras`/`nasi` = growing/milled/cooked
rice. `saudara` = sibling + "you (singular)". `kakak`/`adik` = older/younger sibling + address.
`gotong royong`, `harambee` = communal labour. Vietnamese `lòng` = bowels + heart.
REFUTED: Arabic `mawsim` has NO monsoon sense — it is season + festival/hajj + harvest +
fixed date/deadline; Hindi `mausam` = season + weather + opportune time. Japanese 腹 lists
only abdomen/belly/stomach/womb, no emotional sense. Swahili `moyo` = heart + courage only.
DOWNGRADED: `muka` social-face sense is Indonesian ONLY — absent from Malay, Tagalog `mukha`,
Hindi `मुख`.

**Do-Not-Repeat:** Do not infer a modern sense from an etymological descendant. English
"monsoon" descends from Arabic mawsim, but mawsim does not mean monsoon. Check the source
language's own entry, not the borrowing language's.

**New find:** Indonesian `nasi` = cooked rice + "(uncommon) livelihood, luck, fortune" — a
staple-food/fortune colexification relevant to docs/research/colexification-happiness-luck-review.md
Part 4, which notes Globasa lacks the allotted-share metaphor.

**Tooling:** reusable en.wiktionary checker written (fetch + per-language section + gloss
extraction, disk-cached). NOTE: strip {{lb}}/{{ng}} templates carefully — the first version
silently ate the inclusive/exclusive labels on kami/kita. Always spot-check raw wikitext.

### 2026-09-07 — Globasa phonotactics + coinage constraints (derived from word-list.csv)
**Key learning:** Root-final segments are restricted. Of 3188 roots: vowel 2175, then n(353),
m(174), l(154), r(144), s(77), y(54), f(22), x(19), w(11), t(1). NO roots end in k, g, p, b,
d, c, j, z, h, v. So borrowings like kakak, adik, gotong are phonotactically ILLEGAL and must
be adapted. Vowel hiatus IS legal (95 root occurrences: ao, eo, ai, ea, iu, ui, oa, ue —
fenxui, bio, aloe). Attested clusters: st nt ng nd tr pr kr ks ny sk mb mp rt nc rm rk nj br
rd nk ns kl. Letter q unused.

**Key learning (user-supplied):** Globasa's approach to clusivity is COMPOUNDING THE EXISTING
SINGULAR PRONOUNS, not borrowing a root. So: miyu (mi+yu, inclusive dual), miuyu (mi+uyu,
inclusive plural), mite/miete (explicit exclusive), imi stays unmarked. Precedent already in
paradigm: femte, mante, femete, manete are compound pronouns. Do NOT propose borrowing
Indonesian `kita`.

**Do-Not-Repeat:** Do not claim sibling seniority is un-expressible in Globasa. `lao` (adj:
old) and `juni` (adj: young; quasi-pfx: offspring, young) are existing roots, so laosodar /
junisodar are already constructible — it is a LEXICALISATION gap, not a resource gap. Check
whether existing roots already license a derivation before calling something a gap.

**Do-Not-Repeat:** `klima` already = weather, so do not propose extending `mosem` to weather.

**Collision status (checked):** free = hati, padi, nasi, beras, kakak, adik, gotong, harambe,
moyo, hara, tayo, manam, miyu, miuyu, mite, miete. TAKEN = lao, juni, muka, mosem, sodar,
risi, imi, hata, hatari, nasiha, ton, tonergo, klima.

### 2026-09-07 — Criterion: a meaning must not be idiosyncratic to one language
**User preference (design principle):** For Globasa imports, a MEANING must be attested
across unrelated language families, not just in one source language.

**Do-Not-Repeat:** Do not test "does the source word colexify?" — test "does the MEANING
recur across unrelated families?" These come apart. Two errors this caused:
  - Downgraded `muka` (social face) because Malay/Tagalog/Hindi cognates lack the sense —
    but the MEANING is attested in Chinese 面子 (reputation/face/dignity), Persian آبرو
    (face/honour/reputation/standing), Turkish yüz (face + sense of shame), Indonesian muka.
    4 families. UPGRADE, not downgrade.
  - Dismissed Swahili for liver-emotion using `moyo` (heart+courage). Wrong lexeme: Swahili
    `ini` (LIVER) = "liver, heart". Check the right word before concluding absence.

**Key learning:** Liver/viscera as seat of feeling is attested in >=6 unrelated families:
Austronesian (hati), Indo-Iranian (Persian jigar: liver + fig. heart + darling), Indo-Aryan
(Hindi jigar: + poetic heart/mind/spirit/courage), Semitic (Arabic kabid: + "heart, best part
of a thing"), Niger-Congo (Swahili ini: + heart), Austroasiatic (Vietnamese lòng), Sino-
Tibetan (Chinese 肝: + fig. mind). => The right import is to EXTEND `ganzo` (existing liver
root, from Putunhwa/Niponsa/Koreasa/Vyetnamsa) with the figurative sense, NOT to coin `hati`
or `jigar`. Import the colexification, not a root.

**Key learning:** A word that spread internationally as a LOANWORD is evidence that one
culture exported a term, not that the meaning is widespread. This kills `harambe` (Kenya-
specific) and `mosem`->appointed-time (Arabic-only sense, though the word spread widely).
This is the "exotic-object route" failure mode.

### 2026-09-07 — Sprachbund refinement to the cross-family criterion
**User preference:** A meaning also qualifies if it recurs across a SPRACHBUND (e.g. the
Sinosphere), not only across genetically unrelated families.

**Do-Not-Repeat:** Do not count areally-diffused attestations as independent families. My
"6 families" for liver-emotion overcounted: Hindi `jigar` is a Persian LOAN, Turkish `ciğer`
likewise, Arabic `kabid` is in the same Islamicate contact zone. Honest count is ~5
independent AREAS: Persianate, Malayic, MSEA (Vietnamese lòng), Sinosphere (Chinese 肝),
Bantu (Swahili ini). Swahili is the key independent confirmation. Same correction applies to
the face-as-standing data (Chinese/Persian/Turkish/Indonesian are not 4 independent draws).

**Key learning — new candidate found via the Sprachbund criterion:** Unified HEART-MIND is
Sinosphere-wide across 4 unrelated languages: Chinese 心 (heart + "mind; intellect; the seat
of thought" + thought/feeling/intention/disposition), Japanese 心 (heart, mind, core, spirit,
soul, sincerity), Korean 마음 (mind, heart, intention, will), Vietnamese tâm (heart,
commitment, centre). Globasa splits this FOUR ways: tutum (heart), siko (mind), ruho (spirit/
soul), fikir (thought) — and `tutum` is coined from English thump-thump / Spanish bum bum.
PROPOSED ROOT: `xin` (free, legal -n coda; Sino-xenic across Mandarin xīn / Japanese shin /
Korean sim / Vietnamese tâm; Globasa x=/ʃ/ ~ Mandarin /ɕ/).

**Key learning — second filter:** Areal attestation qualifies a meaning as ATTESTED, but not
if the meaning encodes a regional MATERIAL fact as universal. Cooked-rice-=-meal is confirmed
Sinosphere-wide (Chinese 飯, Korean 밥, Vietnamese cơm) and Malayic, but importing it would
make rice the default meal — as parochial as bread or maize. Globasa already has `yam`
(meal/food/eat). Accept `nasi` (cooked rice); reject rice-as-meal.

### 2026-09-07 — SETTLED criterion for Globasa semantic imports
**User preference (final form):** A meaning qualifies for import if it recurs across a whole
SPRACHBUND or wider. It must not be MORE idiosyncratic than that — single-language or
single-culture meanings do not qualify. A Sprachbund is sufficient; genetic independence is
not required.

Consequence: the areal-inflation recount (Persianate = one cluster, not 4 families) changes
no verdicts, since Persianate is itself a Sprachbund. Liver-emotion qualifies on Persianate
alone and again on Malayic, MSEA, Sinosphere and Bantu. `xin` (heart-mind) is CLEARED on
criterion grounds — Sinosphere-wide. Remaining reservation about `xin` is community
reception (it merges what Globasa already distinguishes), which is a separate axis from
evidence. `harambe` (Kenya-only) and `mosem`->appointed-time (Arabic-only sense) stay
rejected: narrower than a Sprachbund.

OPEN, user's call: rice-as-meal PASSES the criterion (Sinosphere 飯/밥/cơm + Malayic) but was
held back on a second filter — a meaning encoding a regional MATERIAL fact should not become
the global default. That is a design judgement, not an attestation question.

**Cleared list:** miyu/miuyu (clusivity), laosodar/junisodar (seniority), ganzo+figurative
(liver-feeling), muka+social (face-as-standing), xin (heart-mind), nasi (cooked rice).
Four of six cost no new roots.

### 2026-09-07 — MSEA psycho-collocations make `xin` a derivational hub
**Key learning:** The unified heart-mind is attested across the MSEA Sprachbund as well as
the Sinosphere, in 3 families: Thai ใจ jai (heart/mind/spirit/breath/desire/intention/
opinion/emotion), Lao ໃຈ, Khmer ចិត្ត cit (feeling/heart/will/disposition/intention/mind;
glossed "psycho-"), Burmese စိတ် seik (mind/thought/consciousness/heart/desire/will),
Vietnamese bụng (belly + "(fig.) personality" + "inner feelings"). Vietnamese tâm sits in
BOTH Sprachbünde, so a Sino-xenic form spans them.

**Key learning — the real argument for `xin`:** MSEA's areal feature is not just the
colexification but that the morpheme is a PRODUCTIVE COMPOUNDING BASE. Thai: ดีใจ dii-jai
(good-heart)=glad, เสียใจ sia-jai (spoiled-heart)=sorry, ใจเย็น jai-yen (cool-heart)=calm/
patient, ใจร้อน jai-ron (hot-heart)=impatient. Globasa already has bardi/termo/bon/bur/syahe/
day/lil, so bonxin, burxin, xinsyahe, bardixin, termoxin, dayxin, lilxin are all constructible
on day one. `xin` is an expressive subsystem, not one root.

**Objection to log:** `xinxiku` (erosion, wear) already exists, so `xin` as a root makes it
misparseable as "heart-wearing". Check `tam` (Vietnamese tâm — spans Sinosphere AND MSEA) or
`sim` (Korean) as alternative forms.

**Held, not rejected:** Quechua `ayni` confirms richly (community work, mutual help,
voluntary balanced reciprocal aid, reciprocity, solidarity) and `ayllu` (community/clan/
kinship group), but Wiktionary has NO Aymara ayni entry, so Andean-wide cannot be established
from this source. Same status as `harambe` — needs an ethnographic source, not a rejection.

### 2026-09-07 — ayni CLEARS, harambee CONFIRMED REJECTED, ubuntu is the better African candidate
**ayni — PASSES the Sprachbund criterion.** Wikipedia: "Ayni (Quechua AND Aymara)"; practised
by Quechuas, Aymara and other peoples of Peru/Ecuador/Bolivia = the Andean Sprachbund (the two
families are unrelated with heavy contact). Wiktionary Quechua `ayni` = community work, mutual
help, voluntary balanced reciprocal aid, reciprocity, solidarity; `mink'a` = service, communal
work; Spanish `minga` = "(South America) collective work". CAVEAT: increment over existing
Globasa is small — `soho` already = "reciprocal, mutual" and `sohoya` (reciprocity) is free and
derivable. Propose `ayni` ONLY for the binding-obligation sense (entitlement to return), not
the cosmological extension. `ayni` is free.

**harambee — REJECTED, settled.** Wikipedia: "a Kenyan tradition", "official motto of Kenya".
One national tradition, not a Sprachbund.

**ubuntu — NEW, better candidate.** Bantu-family-wide: Wikipedia "meaning 'humanity' in some
Bantu languages, such as Zulu and Xhosa... a set of closely related Bantu African-origin value
systems", "I am because we are". Wiktionary Zulu `ubuntu` = humanity, human nature, humaneness,
solidarity; Swahili `utu` = humanity, human nature, ubuntu (cognate, East + Southern Africa).
Semantically distinct from Globasa's `insan`/`insanlari`/`boninsanli` (species/collective/
kindness) — none expresses PERSONHOOD CONSTITUTED THROUGH RELATION. `ubuntu` is free and
legal. NOTE: Globasa's `utu` is TAKEN = clothes iron (Turkisa ütü), so the short form is
unavailable.

**Convergence worth noting:** ubuntu (Bantu) and ayni (Andean) independently encode the person
as constituted by relations of exchange.

**Source discipline:** breadth claims here rest on WIKIPEDIA (good for "is this areal", weak
for headword glosses); lexical claims rest on Wiktionary. Wiktionary coverage of Aymara,
Sotho, Tswana and Shona is thin — "no section" is uninformative for those languages.

### 2026-09-07 — Third criterion: banal metaphorical extensions are licensed
**User preference:** One-form-one-meaning IS a desired design property (do not treat it as an
inherited European flaw to erode). Marked meanings should be DERIVED. BUT metaphorical
extension of a word is allowed when the extension is common or trivial enough across
languages.

**The three criteria now compose:**
 1. Is the MEANING attested Sprachbund-wide or wider?
 2. Does it avoid universalising a regional material fact? (rice-as-meal fails)
 3. If it is a metaphorical extension of an existing word, is the LINK attested Sprachbund-
    wide or wider? Yes -> polysemy licensed directly. No -> separate root.

**Verified results of criterion 3:**
 - face -> social standing IS banal. English "face" = "reputation; standing, in the eyes of
   others; dignity; prestige"; Japanese 顔 "a person's reputation"; Chinese 面子; Persian آبرو;
   Turkish yüz; Indonesian muka; Spanish cara "gall, nerve". 6+ families INCLUDING European.
   => `muka` + social sense REINSTATED, no derivation needed.
 - gift -> obligation is NOT banal. English gift = "given voluntarily, WITHOUT CHARGE";
   Spanish regalo, Swahili zawadi, Arabic هدية, Indonesian hadiah all plain gift. Sinosphere-
   only (人情/義理/恩). => needs separate root `giri`, NOT a widened `hadya`.

**Correction:** `hadya` was NOT truncated to a European sense (unlike muka/mosem/ganzo/sodar).
Its own sources (Arabic hadiya, Indonesian hadiah) lack the obligation sense too. Do not cite
it as an instance of the truncation pattern.

**Downgraded:** the figurative-extension affix proposed last turn is largely unnecessary under
criterion 3 — banal extensions need no machinery, non-banal ones take separate roots. Globasa's
lack of figurative-derivation machinery is a much smaller problem than I claimed.

**`ganzo` + feelings:** stays out for REDUNDANCY (`xin` covers the concept), not for violating
one-form-one-meaning — 5 areas make the liver->emotion link common enough to license.

### 2026-09-07 — Word selection methodology: strong on forms, undefended on senses
**Key learning:** `Word selection automator 2.py` is a DATA-GATHERING AID, not a selector —
no scoring code; it prints a candidate list (Jeni: / Aloopsyon:) for human judgement.
 - FORM selection IS de-Eurocentrized: after index 4 it prints "Ewropali (Tongo to sen un
   famil.)" = European counts as ONE family (en,es,fr,ru,de), then "Alo (Moyun to sen un
   famil.)" = each other language is its own family (id,hi,te,ar,sw,fa,tr,cmn,ko,ja,vi).
   Effective 1:11 weighting against European etymons, plus per-script transliterators.
 - CONCEPT selection is undefended: inputs are `english_word`, `PoS`, `query_sense`; URL is
   en.wiktionary.org; translations matched by `if title.text == sense` (the ENGLISH sense
   heading); `langDict["en"].add(word)` seeds English for free on every root. A meaning
   English does not lexicalise cannot enter the pipeline at all.
 => This IS the session's finding in code: global forms, European senses.

**Do-Not-Repeat:** I predicted a scraper bug — that span[lang="cmn"] misses Mandarin,
explaining Putunhwa's 21.6% attestation. WRONG: `cmn` is the correct code and is present
(water 2, liver 4, gift 7 occurrences). The real mechanism is uneven English Wiktionary
translation-table coverage (for "water": sw=0, hi=0, fa=0), rendered as "?" — which conflates
"no data" with "no word".

**CORRECTED 2026-11-07 (user):** Tagalog/Filipino ('tl'/Pilipinasa) being commented out of v2
is NOT a regression — Filipino has been REMOVED as a Globasa source language. 16 sources remain
(5 European = one family + 11 single-language families). Pilipinasa still appears in older
LexiliAsel rows (40.2% of roots); parse it but never count it. The saved methodology HTML is
out of date on this point.

**Four fixes (leverage order):** (1) extend the "European = one family" corrective from forms
to SENSES; (2) allow non-English entry points — machinery already exists in `JSONL parser
non-English.py`, `Multi-Wiktionary sense curator.py`, WiktionaryLMDB_de/fr; (3) distinguish
"no data" from "no word" instead of "?"; (4) add a colexification probe at concept-selection
time, inside the existing 16-language loop.

### 2026-09-07 — Running the word-selection methodology on "reciprocal gift"
**Demonstration:** The concept has NO English headword (English gift = "given voluntarily,
without charge"), so `Word selection automator 2.py` cannot start — `english_word` has no
value. Reciprocal gift is not a hard case for the methodology, it is an impossible one, purely
because of the entry point.

**CORRECTION to an earlier claim:** I said gift->obligation was Sinosphere-only. WRONG. The
Persianate Sprachbund lexicalises it explicitly: Persian منت minnat = "favor, grace" +
"obligation, indebtedness (for a favor)"; Turkish minnet = "gratitude" + "(usually negative)
feeling of obligation or indebtedness for a favor". Two Sprachbünde => clears the criterion
decisively. Partial: Arabic منة minna, Hindi एहसान ehsan ("favour; gift"), Vietnamese ơn,
Korean 의리 uiri. NOT attested: Indonesian budi (sense/mind/character), Swahili fadhili, and
no European language.

**Family weighting:** 4 strong + 4 partial across 8 of 11 non-European families, European
contributing zero — the 1:11 weighting doing exactly what it was designed for.

**Form candidates:** `giri` (Japanese only; clean, free) · `on` (4 Sino-xenic: 恩 cmn ēn / ja on
/ ko eun / vi ơn; legal and free but very short) · `minet`/`minetu` (Persianate fa/tr/ar/ur;
needs adaptation — `mina` is TAKEN). Neither spans both Sprachbünde.

### 2026-09-07 — Reciprocal gift extended to other families (Wikipedia)
**PASSES (ordinary vocabulary):** Persianate minnat/minnet · Sinosphere 恩 on / 義理 giri /
人情 renqing · **Philippine utang na loob** ("a debt of one's inner self (loob)", Bisayan
utang kabubut-un — two Philippine languages) · Andean ayni.

**FAILS (named institutions, single culture):** hau (Māori — Wikipedia notes Mauss "relied on
limited sources", analysis contested), kula (Milne Bay PNG), moka (Mt Hagen PNG), pumasi
(Korean, one language). POTLATCH is borderline: spans Heiltsuk/Haida/Nuxalk/Tlingit/Makah/
Tsimshian/Nuu-chah-nulth/Kwakwaka'wakw/Coast Salish = genuine multi-family Sprachbund, passes
BREADTH, but names a feast and the word is Chinook Jargon (a trade pidgin) — fails filter 2.

**SHARPER FORM OF FILTER 2:** ordinary vocabulary passes; NAMED INSTITUTIONS fail. Test:
do people use the word in daily speech, or is it the name of a ceremony/system?

**META-FINDING:** Most of Mauss's own paradigm examples FAIL the criterion (hau, kula, moka,
potlatch). Using his example list as a candidate list would import exactly the parochialism
the criterion excludes. Confirms the earlier warning against Mauss-as-licence.

**COUNTERWEIGHTS (honest):** (a) South Asia has the OPPOSITE institution — dāna (Sanskrit/
Pali; Hinduism, Buddhism, Jainism, Sikhism) is giving WITHOUT expectation of return. (b) My
claim that no European language attests gift->obligation was TOO STRONG: Russian `blat` is a
lexicalised informal favour-exchange system (framed as corruption, but lexicalised).

**PAYOFF:** utang na loob = "debt of the inner self". Globasa has `jaymu` (debt); with `xin`
proposed, **`xinjaymu`** is constructible morpheme-for-morpheme parallel to the Tagalog.
`xinjaymu` is free. Tagalog `loob` extends the inner-faculty evidence to a SIXTH area
(Sinosphere, MSEA, Malayic, Persianate, Philippine, Bantu).

**POSSIBLE 5th truncation instance (flag cautiously):** Globasa `gwanxi` (Putunhwa 关系,
Koreasa 관계) is glossed "relationship; relate to, concern, involve" — the reciprocal-
obligation-network sense is absent. BUT 关系 genuinely means plain "relationship" in ordinary
Chinese, so unlike muka/mosem this gloss is not wrong; the loaded sense is a specialisation
needing its own justification.

### 2026-09-07 — Closing the absences: reciprocal gift resolves to a COMPOUND, not a root
**Do-Not-Repeat — the conflation:** Wikipedia "Reciprocity (cultural anthropology)" defines
reciprocity as delayed exchange creating obligation, "as in the exchange of BIRTHDAY GIFTS" —
i.e. the PRACTICE is universal, Europe included. What varies is LEXICALISATION. Do not treat
"this culture has the practice" as evidence for "this language lexicalises it". Only the
latter matters for a lexicon.

**Two distinct colexifications, different breadth:**
 A. gift/favour -> obligation — AREAL: Persianate (Persian minnat, Turkish minnet,
    Azerbaijani minnət "favor, grace, thankful or obligated behaviour" — but all one Persian
    borrowing, not independent), Sinosphere, Philippine, Andean.
    TESTED AND NOT FOUND: Dravidian (Telugu kṛtajñata = plain gratitude), Uralic (Hungarian
    hála = gratitude), Kartvelian (მადლობა = thanks), Ethiopian (Amharic ውለታ = favor).
 B. debt -> obligation/duty — BROADER: Tamil கடன் kadan "debt, loan" + "duty, obligation" +
    "indebtedness"; Georgian ვალი vali "debt" + "obligation"; English "debt of gratitude";
    Finnish COMPOSITIONAL kiitollisuudenvelka (gratitude + debt).

**RECOMMENDATION REVERSED:** withdraw `giri` as a root. The majority of tested languages build
this COMPOSITIONALLY (Finnish kiitollisuudenvelka, Tagalog utang na loob). Globasa should too:
**`xinjaymu`** (jaymu "debt" + proposed `xin`), parallel to both. No new root needed.
Separately, `jaymu` + obligation sense may be licensed under criterion 3 — debt->duty is
attested in Tamil, Georgian AND English (3 families incl. European), so the link is banal.

**Genuinely untested (NOT negative):** Zulu, Nahuatl, most of Africa/Americas/Australia/Papua.
My headword guesses failed — Hausa `gafara` actually means "forgiveness, pardon"; Zulu
`isibopho` and Nahuatl `tlaxtlahuilli` returned no section. Extending this needs a descriptive
dictionary per language, not headword guessing by a non-speaker.

**Tooling:** added `defs_retry()` to the checker — the egress proxy returns intermittent 502s,
and a bare failure was previously indistinguishable from "no section". Now returns None on
fetch failure vs [] on genuine absence.

### 2026-09-07 — Eastern concept derivations verified against scholarly sources
**User preference:** Prefers DERIVATIONS over opaque loans for Eastern philosophical concepts,
to make them transparent. Verify derivations against SCHOLARLY sources (SEP, IEP, Oxford
Academic), not Wikipedia.

**CONFIRMED:**
 - dukkha -> `nentrutiya` (nen- + truti "satisfied" + -ya). SEP Mind in Indian Buddhist
   Philosophy: "It should not be translated as 'suffering' but 'unsatisfactoriness.'"
 - wuwei -> `juhudikalfale` (juhudi "effort" + -kal + fale "act"). Scholarly consensus favours
   "effortless action"; Slingerland's Oxford monograph is titled *Effortless Action*; sources
   explicit that wu wei "should not be understood as literal inaction".
 - samsara -> `xenmorcuki` (birth-death-cycle); moksa -> `hurugi` (already exists).

**TOO NARROW:** nirvana -> `hasratuawgi` names ONLY craving. Doctrinal content is "the
extinguishing of the fires of CRAVING, AVERSION and DELUSION" — three fires. Second case
(with dharma) where derivation fails because the concept is defined by a DOCTRINAL LIST rather
than a decomposition. Take the loan `nirvana`, or state that the derivation names the leading
fire only.

**IMPROVED BY SOURCES:** ren -> use **`toninsanya`** (ton- "together with" + insan + -ya =
co-humanity), NOT `boninsanya`. Boodberg's rendering "co-humanity" reflects that 仁 = 人
(person) + 二 (two); `ton-` mirrors the character's own composition morpheme-for-morpheme.
`toninsanya` is free.

**Do-Not-Repeat — METHODOLOGICAL:** I made TWO mid-turn walk-backs based on Wikipedia leads
that were both WRONG. Wikipedia leads with LITERAL ETYMOLOGY (lit. "suffering, pain"; "literally
means not-acting"), which made the scholarly interpretive renderings look like overreach. For
technical terms of art, the encyclopedia lead gives the etymology; the specialist literature
gives the preferred rendering. Go to SEP/IEP/Oxford FIRST for terms of art.

### 2026-09-08 — Papers overturn "effortless action"; `nilfale` adopted for wuwei
**User proposal ADOPTED:** `nilfale` (nil "no/none" + fale "deed, act") for wuwei 無為 — a
morpheme-for-morpheme calque (無 wú = existential "not have/none"; 為 wéi = do/act).

**Do-Not-Repeat:** I told the user there was "scholarly consensus" for Slingerland's
"effortless action". WRONG — that came from a WebSearch AI summary. The actual papers show a
live dispute: Chris Fraser, "On wu-wei as a unifying metaphor", *Philosophy East and West*
(2007) is a published critique of exactly that rendering; Van (2025) says all renderings
"rarely capture the full philosophical" content; Slingerland himself concedes wuwei is "often
translated as 'doing nothing' or 'non-action'". SEARCH THE PAPERS, NOT THE SUMMARIES —
search-engine summaries assert consensus where the literature shows contestation.

**Principle established:** a derivation should calque the LITERAL sense all parties agree on,
not the contested interpretive rendering. `juhudikalfale` picked the disputed side of a named
scholarly debate; `nilfale` does not.

**CONSEQUENCE for ren:** switch from `toninsanya` back to **`boninsanya`**. Boodberg's
"co-humanity" appeared in NONE of six Google Scholar results; the standard renderings are
"humanity", "benevolence", "humaneness". The 人+二 character composition IS standard knowledge
(cited in mainstream 2026 paper), but the rendering is minority. `boninsanya` is the `nilfale`
of that pair.

**Morphology note (open):** `nen-` is the general negation prefix attaching to arbitrary roots;
`nil-` is the determiner "no/none" and in the lexicon attaches ONLY to correlative categories
(nilto, nilte, nilloka, nilwatu, nilmaner, nilseba, nilpul, nilmo; niltogi = nilto + -gi). So
`nilfale` extends nil- beyond correlatives for the first time — `nenfale` is the conservative
alternative. `fale` is a noun as well as a verb and `nil` is a determiner taking nouns, so
`nil fale` is already grammatical as a phrase.

**Tooling:** paperclip searches arxiv/openalex/osf (PREPRINT servers) — wrong domain for
Sinology/Buddhist studies; it matched the author name "Wei Wu" and returned plasma physics.
Use google-scholar for humanities, and keep queries SIMPLE (two over-specific queries returned
empty; a plain one worked).

### 2026-09-08 — teotl/Dao comparison is real (user was right), but not independent evidence
**CORRECTION:** I dismissed the teotl~Dao parallel as an analyst's umbrella of my own making.
WRONG — there is a real comparative subfield. Alexus McLeod (Indiana; early Chinese + Meso-
american philosophy) compares Maya thought with Daoism; author of *Introduction to Meso-
american Philosophy* (Cambridge 2023), *The Dao of Madness* (OUP), contributor to *Brahman and
Dao* (Lexington). And MAFFIE HIMSELF makes the comparison: he takes David Hall's reading of
*dao* as "primarily gerundive and processive" (not nominative/substantive) and proposes reading
*teotl* the same way — "primarily gerundive, processive, and denoting a process".

**But the finding SHARPENS rather than dissolves the objection.** Direction of influence:
Maffie reads teotl processively BECAUSE Hall reads dao processively. So teotl-as-process and
dao-as-process are ONE data point, not two — structurally identical to the areal-inflation
error (counting Hindi jigar as independent of Persian jigar), except the borrowing is scholarly
rather than areal. Chain: Whitehead -> Hall/Ames on dao -> Maffie on teotl, every step contested
(Hall/Ames are criticised for importing Whiteheadian process metaphysics into Chinese thought).

**PATTERN (4th instance today):** Slingerland/wuwei, Boodberg/ren, Maffie/teotl, Hall/dao — in
every case a derivation would encode a NAMED SCHOLAR'S CONTESTED READING. Treat this as the
general condition of philosophical terms of art, not bad luck.

**Recommendation unchanged, better justified:** `di dao`, `di teotl` as culture-specific proper
nouns using Globasa's existing `di` particle ("(optional) proper noun or culture-specific
marker"). No coined root for "processive sacred ground" — it would lexicalise a contested
reading of one tradition derived from a contested reading of another, invisibly.

**Sourcing caveat:** the Hall/Maffie detail surfaced via *Brown JPPE*, an UNDERGRADUATE journal;
Project MUSE and IEP are both EGRESS-BLOCKED so the primary text was unverifiable. McLeod's
Cambridge volume is the solid citation. Treat the Hall attribution as probable, not verified.

### 2026-09-08 — Sinosphere concept sweep: 2 accept, 1 reject, 1 already covered
**ACCEPT — ziran 自然 -> widen `naturali`:** Sinosphere-wide colexification nature <-> spontaneous/
unforced. Chinese "natural; at ease; without strain"; Japanese "spontaneous / spontaneously";
Vietnamese "natural; unstudied" + "(colloquial) suddenly; spontaneously". English "natural"
(a natural manner) carries a slice, so the LINK is banal => licensed under criterion 3.
ALSO fills a plain hole: Globasa has NO word for "spontaneous" (only natura, naturali,
nennaturali, posnaturali, ultranaturali). Pairs with `nilfale` — ziran/wuwei are a matched pair.

**ACCEPT — bao 報 -> neutral requital:** Chinese 報 = "to avenge; take revenge" AND "to repay;
requite; recompense" AND "divine retribution; karma"; Japanese 報 keeps "retribution". Māori
`utu` independently does the same ("reciprocation of kind deeds AND the seeking of revenge").
Sinosphere + Polynesian, INDEPENDENT. Globasa splits: `intikam` (revenge) / `rupaya`
(repayment), no neutral term. `sohoya` (from soho "reciprocal, mutual") is FREE and would carry
it, or widen `rupaya`.

**REJECT — de 德:** the "(philosophical) inherent potency, efficacy, endowment" sense appears
ONLY in Chinese; Japanese 徳 and Korean 덕 give only "virtue, benevolence". Neither Sinosphere-
wide nor ordinary vocabulary. `fadila` (virtue) suffices.

**ALREADY COVERED — kong 空 / śūnyatā:** Globasa `kal` (empty) -> `kalya` (emptiness). Needs
nothing. Li 禮 largely covered by `gixiki` (rite), `merasem` (ceremony), `adebu` (politeness).

**PATTERN (held across 4 rounds):** the Sinosphere concepts that PASS are ordinary-vocabulary
COLEXIFICATIONS (nature<->spontaneous, repay<->avenge); the ones that fail or need loans are
DOCTRINAL TERMS (de-as-potency, dharma, nirvana, teotl). Inverts the intuitive approach — the
valuable imports are unglamorous everyday merges, not famous philosophical vocabulary.

### 2026-09-08 — Indigenous concepts: structural constraint + topographic directionals
**STRUCTURAL CONSTRAINT (state this every time):** Globasa's source languages contain NO
Indigenous American, Australian or Papuan language; Swahili is the only African one. So an
Indigenous-sourced FORM has no etymological support under Globasa's own weighting. Indigenous
meanings can enter only as (a) derivations from existing roots or (b) `di`-marked culture-
specific terms. EXCEPTION: Indonesian and Filipino are Austronesian source languages, so
Austronesian patterns have a legitimate route.

**BEST CANDIDATE — topographic directionals (already derivable, zero new roots):**
Verified typologically: Lamaholot (Austronesian) rae 'mountainward', lau 'seaward', wəli
'parallel with coast', teti 'upward', lali 'downward'; a survey of 100 AUSTRONESIAN LANGUAGES
finds six patterns (landward-seaward, riverine, coastal, elevation, wind, cardinal); Tzeltal
(Mayan) uses uphill/downhill as its habitual absolute frame; also Kalaallisut.
Globasa has NOTHING (no upstream/downstream, no seaward/inland; only `meylu` slope).
DERIVE with existing `hoy-` (toward) + landmark: `hoybahari` seaward, `hoyjabal` mountainward/
inland, `hoykosta` coastward, `hoynahir` riverward. All FREE. Roots present: bahari (sea),
jabal (mountain), liljabal (hill), kosta (coast), nahir (river), gao (high), meylu (slope).
QUALIFICATIONS: environment-dependent (landward/seaward presupposes a coast — this is what
"sociotopography" studies), so available vocabulary not a universal frame. AND English has
upstream/downstream/uphill/downhill, so this is a plain LEXICAL gap, not a Eurocentrism
finding — the Indigenous contribution is showing these are CORE not peripheral.

**ATTESTED BUT LOW PRIORITY — cross vs parallel cousins:** widespread (parallel cousins often
take SIBLING terms; some languages have four distinct cousin words); Globasa has only `kuzin`.
Expressible descriptively, rarely needed outside cross-cousin-marriage societies. Record as a
gap; do not propose.

**FAILS (consistent with the Mauss round):** mana, hau, potlatch, Ometeotl, whakapapa,
turangawaewae — single-culture and/or anthropologically mediated.

**EVIDENCE LIMIT:** Indigenous-language evidence is the WEAKEST of any area this session.
Wiktionary has no Zulu/Nahuatl/Aymara entries; headword guesses have failed. Typological
literature ABOUT these languages can identify FEATURES but cannot verify lexical facts or
supply forms. Proper work needs descriptive grammars and speakers.

### 2026-09-08 — CORRECTION: `nilfale` WITHDRAWN (supersedes the earlier entry)
**Supersedes "2026-09-08 — Papers overturn 'effortless action'; `nilfale` adopted for wuwei".**
With the egress proxy widened, IEP *Daoist Philosophy* is readable and says the OPPOSITE of what
I concluded from a search summary + a Fraser snippet:
  "it is generally agreed that the traditional rendering of it as 'nonaction' or 'no action' is
  INCORRECT." IEP endorses "act naturally", "effortless action", "nonwillful action", and cites
  Slingerland in references rather than disputing him.
So the effortless/nonwillful family is MAINSTREAM and "nonaction" is the REJECTED rendering.
Fraser (2007) critiques Slingerland's UNIFYING-METAPHOR THESIS — not the same as rejecting the
rendering — and remains UNREAD (Project MUSE returns a verification page).

**Why the calque fails even though the morpheme analysis is right:** 無 = existential "not-have",
為 = "do, act" — correct. But 無為 is a fixed classical expression acquired as a unit, whereas
`nilfale` would be a PRODUCTIVE TRANSPARENT COMPOUND that Globasa guarantees a reader parses
compositionally as "no-doing" — delivering exactly the rendering scholarship rejects. Transparency
argues AGAINST derivation here. A loan is defensible on the same grounds as nirvana/darma.

**Do-Not-Repeat:** IEP *Aztec Philosophy* is AUTHORED BY JAMES MAFFIE (University of Maryland) —
it is NOT independent evidence about the reception of his own reading. It also presents Ometeotl
as a genuine popular-religious expression (elite/popular bifurcation), CONTRADICTING the
"scholarly artifact" critique I relayed as settled. And it mentions neither David Hall nor dao,
further weakening the Hall->Maffie attribution.

**STILL BLOCKED:** muse.jhu.edu (verification page) and ndpr.nd.edu. So independent criticism of
Maffie remains unverified from primary sources.

**Meta-lesson (now cuts both ways):** following "search the papers, not the summaries" produced
the WRONG answer once — I retracted `juhudikalfale` on a summary that overstated consensus, then
had to retract the retraction. Correct rule: read the PRIMARY source; where it cannot be read,
mark the claim UNVERIFIED rather than picking a side.

**CONFIRMED by IEP Buddha:** nirvana = "extinguishing of the fires of craving, aversion, and
delusion" (three fires — `hasratuawgi` names one, as the audit says). dukkha "ordinarily means
physical and mental pain, but that in the first noble truth designates diverse kinds of
frustration, and the existential angst" — so `nentrutiya` fits the technical sense.
**CONFIRMED by wals.info:** matches locally computed CLDF. 87A: NAdj 879 (64%), AdjN 373 (27%),
n=1367.

### 2026-09-08 — `nilfale` REINSTATED (supersedes the withdrawal logged above)
**User's decisive argument:** Daodejing 37, 道常無為而無不為 (dào cháng wúwéi ér wú bù wéi). Every
standard translation renders 無為 there with a NEGATION — "The Way never acts yet nothing is left
undone"; "takes no action, but leaves nothing undone"; "does nothing yet nothing is left undone".
The line is a PARADOX BUILT ON STACKED NEGATION: 無為 vs 無不為, with 為 recurring in both halves.
Render 無為 as "effortless action" and the paradox evaporates.

Globasa reproduces it only with a negation-based form:
  `Dao moywatu nilfale, mas nilto no befale.`  (all pieces exist: nilto, no, be-, fale, moywatu, mas)
`juhudikalfale` CANNOT — there is no counterpart clause for "effortless action" to stand against.

**Resolution — both positions are right about different things:** as a STANDALONE CONCEPT GLOSS,
"nonaction" misleads (IEP correct). As a TERM INSIDE THE CANONICAL TEXT, the negation is
structurally required and every translator supplies one (cf. Warp, Weft and Way, "Nonaction in the
Daodejing"). A lexicon entry must serve both => negation-based form + a gloss explaining it is not
idleness, exactly as Chinese does.

**KEY METHOD LESSON (better than the earlier one):** `nilfale` oscillated three times — adopt,
withdraw, reinstate — and every move was driven by WHICH SOURCE WAS REACHABLE, not by new evidence.
What broke the cycle was a DIFFERENT KIND of evidence: a canonical passage the term must carry.
=> For terms of art, TEST THE CANDIDATE AGAINST A TEXT IT MUST TRANSLATE. This is a check the
lexicographer can run without adjudicating a scholarly dispute, and it settled in one step what
three rounds of source-chasing did not.

### 2026-09-08 — Translation tests against primary texts: the method discriminates
**Sources:** ctext.org and suttacentral.net are EGRESS-BLOCKED. Chinese Wikisource
(`道德經 (王弼本)` via the MediaWiki API) and the Wikipedia quotation of Bodhi served instead.
Note zh.wikisource title that works: "道德經 (王弼本)" — "道德經/第37章" and "老子/37" are MISSING.

**Test 1 — Daodejing 37, `nilfale` PASSES.** Primary text (Wang Bi recension, 三十七章):
  道常無為〈順自然也。〉而無不為。〈萬物無不由為以治以成之也。〉
Globasa: `Dao moywatu nilfale, mas nilto no befale.` — `fale` recurs, negation stacks.
**KEY:** Wang Bi's own gloss on 無為 is 〈順自然也〉 = "it accords with ZIRAN". So the classical
commentator supplies the naturalness reading AS COMMENTARY while the term itself stays a negation
— exactly the arrangement proposed (negation-based form + interpretation in the definition). It
also links two proposals: widened `naturali` (ziran) glosses `nilfale`, as 自然 glosses 無為.

**Test 2 — First Noble Truth (SN 56.11, Bodhi), `nentrutiya` PARTIALLY FAILS.** The formula
predicates dukkha of CONCRETE EVENTS: "birth is suffering, aging is suffering, illness is
suffering, death is suffering". `nentrutiya` is an abstract quality-noun — "birth is
unsatisfactoriness" is not a sentence. The adjective `nentruti` (FREE, needs proposing) is
grammatical — `Xencu sen nentruti, laocu sen nentruti, bimarcu sen nentruti, morcu sen nentruti` —
but understates what the formula asserts. `suferi` carries the weight but is what SEP rejects.
=> NO SINGLE GLOBASA WORD COVERS DUKKHA. Pali dukkha is noun AND adjective and spans concrete pain
through existential unsatisfactoriness.

**THIRD OUTCOME for the method** (alongside "derives cleanly" and "needs a loan"): the source term
is POLYSEMOUS ACROSS A RANGE no single transparent compound reproduces. Keep the derivation for
the technical sense, state the split in the entry, do not pretend one word does two jobs.

**The method DISCRIMINATES** — same procedure, one pass and one partial failure. Neither result was
available from dictionary glosses. `xenmorcuki` (saṃsāra) is UNTESTED.

### 2026-09-08 — `walfale` SUPERSEDES `nilfale` (corpus test)
**Data:** 無 + X in the Daodejing main text (Wang Bi commentary + phonological appendix excluded):
**102 tokens, 51 distinct second characters.** 無為 12 · 無以 10 · 無所 6 · 無名 5 · 無欲 5 ·
無不 5 · 無棄 4 · 無事 4 · 無知 3 · 無有 3 · 無味 2 … Ten chapters carry 無為/無不為 in main text:
2, 3, 10, 37, 38, 43, 48, 57, 63, 64.
=> 無 is a PRODUCTIVE PREFIX. The choice is a grammatical decision about 51 forms, not a lexical
one about one word.

**`wal-` beats `nil-` and `nen-`:** Globasa `wal-` = pfx "without", and **`walya` = "v.tr: be
without"** already exists — which is exactly what classical 無 means as a verb ("to lack, not
have"). `wal-` already attaches to content roots (`walaganjon` "miss, feel lack of"). `nil-` is a
determiner bound to the correlative grid; 六十三章 (為無為，事無事，味無味) would require extending
it to three arbitrary verbs at once. `nen-` is privative "un-", not existential "without".

**Renderings:** 三十七 `Dao moywatu walfale, mas nilto no befale.` · 六十三 `Fale walfale, ergo
walergo, xeto walxeto.` · 五十七 `Mi walfale, ji jenmin se-cansu.` · 四十三 `benefiso de walfale`.
Scales: walname (無名), walxiwon (無欲), walergo (無事), walxeto (無味), waljixi (無知) — all free.

**METHOD LESSON:** testing against ONE passage gave a true but incomplete result (negation
required); testing against the PATTERN corrected the implementation. **Test against the pattern,
not only the passage** — a recurring term of art is usually an instance of a productive
construction, and the construction is what the lexicon must support.

### 2026-09-08 — 無不為 must be a CLAUSE, not a compound (user correction)
**User's objection:** combining `wal-` with a negating prefix gives a DOUBLE NEGATION. Correct —
Globasa's morphology is regular, so `wal-`+`nen-`+`fale` composes and CANCELS: `walnenfale` =
"doing". The line would read "the Dao is always without doing, but doing" — a flat contradiction,
not a paradox.

**Why:** the surface symmetry of 無為 / 無不為 is an artifact of classical Chinese terseness. 無
does DIFFERENT work in each half:
  無為   — 無 privates the action ("without doing"); a predicate, a lexical item
  無不為 — 無 QUANTIFIES EXISTENTIALLY over unactioned things ("there is nothing that is not
           done"); a clause, NOT a lexical item
Only the first is a term. Every translator renders the second clausally.

**Correct rendering:** `Dao moywatu walfale, mas nilto no befale.` — `nilto` is a QUANTIFIER, not
a prefix, so quantifier+negation reads as rhetorical emphasis rather than composing and
cancelling. English behaves the same: "nothing is left undone" works, "un-non-done" does not.

**Do-Not-Repeat / general rule:** morphological parallelism in the source is not always semantic
parallelism. A regular agglutinative auxlang COMPOSES what an isolating language merely
JUXTAPOSES, so a construction inert in the source can become active — and cancel — in the target.
Always check whether a proposed compound composes to something the source does not mean.

### 2026-09-08 — Sinosphere Heaven: `janatu` mis-glossed; ṛta/aša/ma'at parallel FAILS
**DEFECT FOUND — `janatu` is mis-glossed.** Globasa `janatu` "heaven" comes from Arabic جَنَّة
*janna* = "GARDEN, PARADISE" (via Indonesisa jannah, Hindi jannat, Turkisa cennet, Parsisa
jannat). It denotes the ABRAHAMIC afterlife-place, glossed as if it were the general concept.
Globasa ALSO has `paradis`. So the lexicon has TWO words for the Abrahamic paradise and NONE for
Sinosphere Heaven. This is the INVERSE of the Part 4 truncation pattern: there a global form kept
only its European sense; here a culture-specific concept got an over-general gloss.

**天 range:** Chinese = sky/heavens + "(religion) Heaven as an impersonal deity" + weather + day
(24h); Korean 하늘 = sky + "(Confucianism) heaven"; Vietnamese trời = sky + weather + "Heaven,
heavenly lord"; Japanese 天 = heavens/sky. sky<->heaven is BANAL (also Arabic samāʾ, Hebrew, Greek,
Latin, Russian, English "the heavens") => licensed. sky<->IMPERSONAL NORMATIVE ORDER is
Sinosphere-specific and arrives by Confucian TRANSMISSION (Korean marks it "(Confucianism)").

**PRECEDENT (excellent citation):** Zürcher, *Catholic Historical Review* 1997 — the late-Ming
Jesuits had to transform "abstract, impersonal Heaven into the personal Lord of Heaven"; Ricci
coined 天主 Tiānzhǔ because 天 would not carry a personal deity. Lee, *Asian Studies* 2026: "Confucian
talk of Tian and moral order resists" the accommodation. Same problem, same direction, 4 centuries
earlier.

**ṛta/aša/ma'at parallel FAILS (tested):** (1) Sanskrit ṛta and Avestan aša are COGNATES —
Indo-Iranian, ONE lineage, not two (the jigar error again). Avestan 𐬀𐬴𐬀 glosses "order (cosmic and
moral)" richly; Sanskrit ऋत's entry is mainly adjectival "proper, right, true"; ma'at reachable
only via an ENGLISH entry. (2) The grouping's bibliography is Dajczer (1976) + van der Leeuw's
interwar phenomenology + self-published grey literature. Commonplace, not finding. SAME SHAPE AS
teotl~dao.

**PROPOSAL:** widen `asman` -> "sky, the heavens" (makes 天地 = `asman ji dunya`); narrow `janatu`
to the Abrahamic paradise (exposing redundancy with `paradis`); `di tian` for Heaven-as-normative-
order, same treatment as `di dao`. NO general "cosmic order" root. Do NOT widen `asman` to the
normative sense — that colexification is not banal.

### 2026-09-08 — PARITY: Sinosphere concepts get ROOTS (supersedes `di tian` in R8)
**User's argument, accepted:** given the Abrahamic concept has its own root (`janatu`), dedicated
roots for Sinosphere concepts are warranted. Marking 天 as `di tian` while `janatu` is unmarked
general vocabulary RESTATES the asymmetry instead of fixing it. => **`tian` as a root.**

**The imbalance, counted:** Abrahamic has 12 dedicated roots — janatu, paradis, jahanom, ruho,
baraka, dambi, kafare, ibada, kido, koheni, rahibu, xabahu (11 Arabic-sourced). Sinosphere has
effectively ZERO (karma is Indic; kido is Chinese-sourced but generic). Lexicon searches: filial
piety = NOTHING; ancestor veneration = only `lefeatre` (kinship term); transcendent = `maryami`,
which is the sage PLANT (Salvia).

**Parallels to 天, ranked:**
 1. 孝 xiao FILIAL PIETY — Chinese ("filial duty; filial piety; mourning; mourning dress; Southern
    Min: to offer up sacrifices") + Japanese ("filial piety"). Globasa has NOTHING. Form `xiaw` ✓
    (`xyaw` legal but xy- onset n=2).
 2. 福 fu BLESSING/FORTUNE/HAPPINESS — Chinese "blessing; happiness; prosperity; good fortune";
    Japanese "good fortune, good luck; happiness; (Buddhism) a blessing; wealthy". Globasa splits
    it FOUR ways (baraka/hox/bonxanse/samrudi). Form `fu` ✓. **Closes a gap the project's own
    colexification-happiness-luck-review.md identified** — hox/xanse sits with the minority.
 3. 魂/魄 hun/po DUAL SOUL — Chinese explicit ("the soul which goes to heaven, as opposed to";
    "the soul which does NOT leave the body after death"). Japanese 魂 and Korean 혼 gloss only
    "soul, spirit" — contrast NOT confirmed (likely coverage gap; 魂魄 konpaku exists). Forms
    `hun`, `po` ✓; `hunpo` ✗ (unattested medial 'np').
 4. 仙 xian — Chinese only, weakest, not proposed.

**Counter-argument noted:** Globasa's Abrahamic vocabulary is ARABIC-sourced, so the imbalance is
conceptual not etymological, and could be said to track adherent numbers. That defends HAVING
dambi/kafare; it does not defend giving them ROOTS while 天 gets a marked term. The disparity in
TREATMENT is what fails.

### 2026-09-08 — Collision checker built; exact-match checking was insufficient
**Tool:** `globasa_collision_check.py` (repo root, indexed in anatomy.md). Six checks graded
BLOCK/WARN/NOTE/CLEAR: (1) exact collision; (2) NEAR-HOMOPHONE via y->i, w->u normalisation —
catches tian~tyan, kwa~kua; (3) edit-distance-1 minimal pairs; (4) MISPARSE — existing words
re-readable as candidate+known morpheme; (5) self-decomposition into prefix+root; (6) phonotactics
derived from the lexicon (codas nmlrsyfxw, onsets, medial clusters, geminates).

**Do-Not-Repeat:** I reported `sim` as free. It is TAKEN — `sim` = "adj: similar, alike, like". I
had run the PHONOTACTIC validator and reported its "OK" as a collision result. These are different
tests; never conflate them. Always run the collision checker.

**Findings:** `tian` WARN (near-homophone `tyan` "dot, point") => **replaced by `tyen`** (user's
suggestion; NOTE, ty- onset n=4, tyenya/tyenli clean, better cross-Sinosphere match tiān/cheon/
thiên). `xiawya` BLOCK (medial 'wy' unattested — `xiaw` cannot take -ya; `xiawli` is CLEAR).
`hoyjabal` BLOCK (medial 'yj' unattested). WARN misparse: xin (xinxikudo, xinyon), nasi (nasiha,
nasibune), fu (furi, fuha), po (pole, pori; poli->polisi), hun (hunfundo), tam (tamiya).
CLEAR: ubuntu, laosodar, junisodar, miuyu, nentrutiya, xenmorcuki, rixencu, bonxansefil, xiawli.

**CORRECTION to the hoy- directionals:** NOT fully productive. hoyjabal illegal; hoybahari cluster
n=1; hoygao n=2. Repair: `hoy` is already a PREPOSITION, so `hoy jabal` works as a phrase — but
they are then prepositional phrases, not lexicalised directionals. The gap is smaller than claimed.

**Short roots are hazardous:** `fu` and `po` have good semantic cases and bad forms; two-letter and
short-CV roots collide broadly and create misparse in existing words.

**METHOD:** always test candidates WITH their likely derivatives (-ya, -li, -yen, -gi, -cu). `xiaw`
passes alone and fails at `xiawya`; `po` passes alone and fails at `poli`.

### 2026-09-08 — PHONOTACTICS CORRECTED: read the xwexi grammar, don't infer from frequency
**Do-Not-Repeat (major):** I inferred Globasa phonotactic constraints from LEXICON FREQUENCY.
Wrong. The rules are DOCUMENTED in
xwexi-pages-grav/03.gramati/01.abece-ji-lafuzu/default.eng.md, "Phonotactics for Ordinary Words".

**The actual rules.** Syllable = (C)(C)V(C).
 - ONSET: any single consonant, or the explicit list: bl fl gl kl pl vl / br dr fr gr kr pr tr vr /
   bw cw dw fw gw hw jw kw lw mw nw pw rw sw tw vw xw zw / by cy dy fy gy hy jy ky ly my ny py ry
   sy ty vy xy zy  (so `xy-` IS permitted — my "rare n=2" was misleading)
 - CODA: **ANY single consonant**. The restricted set -f -l -m -n -r -s -w -x -y applies ONLY
   WORD-FINALLY. => medial clusters are COMPOSITIONAL (coda + permitted onset), NOT a fixed
   attested inventory.
 - STOP+STOP banned across coda-onset: astrato, ativo, otima (hence Globasa `otima` not `optima`).
 - Voicing need not agree (tekno vs magneto).
 - w/y: -iy -iw -uy -uw banned nucleus-coda; iy/uw banned nucleus-onset (syahe not siyahe);
   wu/yi banned onset-nucleus.
 - GEMINATES ARE ALLOWED from derivation: possahay, aselli, burroya. (My geminate check was wrong.)

**Corrections this forces:** `hoyjabal` LEGAL (was BLOCK) — user was right. `xiawya` LEGAL (so
`xiaw` CAN take -ya). `samsara` LEGAL (the `sansara` adaptation was unnecessary). `hunpo` LEGAL.
`xyaw` fine. WITHDRAWN: the claim that the hoy- directional pattern "is not fully productive".
Still blocked, for stated reasons: `sangha` (gh not a permitted onset), `renjing`/`yinyang`
(word-final -g), aktivo/optima (stop+stop).

**Validation:** rewritten `globasa_collision_check.py` run over all 3188 roots => 12 violations
(0.38%), every one a loanword (bakgamon, futbal, hotdogu, koktel, rugbi, vodka, pawndu), a letter
name (iya, iye), a Spanish loan (kesadiya, tortiya) or test data (devtest).

**METHOD:** frequency in a lexicon is evidence about what has been COINED, not what is PERMITTED.
Where a project documents its own rules, READ THEM. A corpus-derived approximation over-rejects,
and the failure is QUIET — an inferred constraint never wrongly admits a form, so nothing in the
output signals the rule set is too tight. ALWAYS check xwexi-pages-grav for documented rules first.

### 2026-09-08 — Illegal word-final consonants are repaired with -u (user-supplied rule)
**Rule:** a form ending outside {f l m n r s w x y} is not rejected — Globasa appends **-u**.
`-ng` -> `-ngu` in 18 roots, overwhelmingly non-European: cengu 层, dongu 东, gungu 弓, jongu 种,
kwangu 矿, tengu 藤, zungu 踪, hongu 孔, sangu 藏, wangu 王, yongu 用, mingu 明, pangu 平 (Putunhwa);
balangu/gubangu (Indonesisa belalang/kumbang); ukungu (Swahilisa); espringu, majangu (via European).
ZERO ordinary words end in -ng (only proper noun `Bering`) — matches the grammar's note that
syllable-final [ŋ] appears "only in proper nouns".
GENERALISES to all illegal finals — roots ending <illegal consonant>+u: -tu 65, -ku 60, -bu 37,
-gu 29, -du 24, -pu 20, -ju 8, -zu 6, -vu 5, -cu 3 (257 roots).
`adapt()` added to globasa_collision_check.py to suggest the repair.

**Results:** renjingu (人情) CLEAR · kongu (空) · xingu (性) · cingu (情) · yangu (陽) NOTE ·
**inyangu** (陰陽) CLEAR — TWO rules apply: -ng->-ngu AND `yi` is banned as onset-nucleus so 陰
cannot be `yin` · **mingu (命) BLOCKED — exact collision with existing `mingu` 明 "clear, evident"**,
so 天命 cannot use it.

**Do-Not-Repeat:** I recorded `yinyang` as "illegal (final -g)" and stopped. Incomplete — the rule
SPECIFIES THE REPAIR. When a form violates phonotactics, apply the documented adaptation before
rejecting it.

**Checker limitation to fix:** `self_decomposes` tests only prefix+root, NOT an existing ROOT
embedded in a proposed compound. `tyenmingu` passes CLEAR despite containing `mingu` (clear), so it
reads as "Heaven-clear" not "Heaven-mandate". Compound candidates need root-boundary checking.
