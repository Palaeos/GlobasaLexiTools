# Genesis 1 — Globasa draft

Machine output: `Gen_1_glb_machine.txt` (apertium-hbo-glb, `./translate.sh`).
This file is the revision of that output. Each verse gives the revised text,
then what changed and why. Sources: `rendering.md` (R), Isaksson, *The Verb in
Classical Hebrew* (2024) on the conjunction *wa* (I), the Doxo corpus (D),
the Globasa grammar (G), the curated lexicon (L).

Conventions applied throughout:

- **wa** is a natural-language connective whose reading comes from context
  (I pp. 79–80). A verse-initial *wa* before the storyline verb starts a new
  sentence (D: sentence-initial *Ji* in 84 of 2,337 sentences). Specific links
  are rendered: background "now" (no connective), storyline resumption
  "then" `Jaxali,`, fulfilment "so" `Kos to,`, purpose "so that" `celki`.
  *wa* between nouns stays `ji`.
- **Speech:** `loga: “…”` (D: `loga:` 78, `loga,` 57). לֵאמֹר "saying" →
  `, loga:`.
- **Narration** is bare; speech has its own tenses (R: Tense in narration).
- **Possessives:** `sesu` only refers back to the clause's subject (G);
  otherwise `tesu`/`etesu` (animate), `tosu`/`otosu` (inanimate); in relative
  clauses `dasu` (G: "The possessive adjective dasu is used in relative
  clauses").
- **Reading of 1:1–3:** the project's preferred analysis (Holmstedt 2002;
  `Gen_1_ambiguity.tsv`): v. 1 a bare relative on "beginning", v. 2 a
  parenthesis, v. 3 the main clause. Alternative (Masoretic accents, LXX,
  Isaksson's translation): 1:1 a main clause, "In the beginning God set
  apart the heavens and the earth. Now the earth was … Then God said …"

---

**1:1** Fe xoru feki Teo julagi asman ji geo —

- Bare relative on בְּרֵאשִׁית (R, Holmstedt): `fe xoru feki …` (G: `feki`
  modifies time nouns without a resumptive). Alt.: `Fe xoru, Teo julagi asman
  ji geo.`
- ברא → `julagi` (van Wolde 2026, Type 1, plural object). Alt. `krea`, `kostrui`.

**1:2** geo sen kaos ji kalya, luminkalya sen fe perya de daybahari, ji vento de Teo levita fe perya de sui —

- Parenthesis inside the host clause → dashes (R: Parenthesis). Background
  clauses (I p. 143 n. 48: *wa-S.noun-qaṭal + wa-XØ + wa-S.noun-qoṭel*): no
  connective before the first; `ji` inside.
- The verbless clause needs `sen` (G). Participle מְרַחֶפֶת → bare `levita` (R).
- רוּחַ אֱלֹהִים: `vento de Teo`; alt. "Spirit of God" `Ruho de Teo`, "mighty
  wind" `daybala vento` (R: disputed terms).

**1:3** Teo loga: “Am hay lumin.” Ji hay lumin.

- Main clause after the parenthesis. With the alternative reading:
  `Jaxali, Teo loga …` ("Then God said", I p. 125).
- Jussive יְהִי → `am hay` (G: jussive `am`; `hay` "there is"). The fulfilment
  wayyiqtol keeps `ji` ("And there was light", I).

**1:4** Teo oko ki lumin sen bon, ji Teo julagi intre lumin ji luminkalya.

- "saw the light, that it was good" → `oko ki lumin sen bon` (complement
  clause, G `ki`); machine: `oko lumin ki to sen bon`.
- בדל → `julagi` (L; open: `aloyagi`, `vibaja`).

**1:5** Teo namegi lumin din, ji te namegi he luminkalya noce. Hay axam ji hay soba: un din.

- Naming: `namegi X Y` (D: "namegi mi day Rita").
- *wa*-X-qaṭal with fronted object, "and the darkness he called Night" (I p. 377 ex. 92): R default for a contrastive fronted object → `S V he X`.
- יוֹם אֶחָד: cardinal `un din`, as the Hebrew (NASB, CSB, LXX); alt.
  ordinal `unyum din` (ESV, NIV, NRSV).

**1:6** Teo loga: “Am hay kube fe midiya de sui, ji to am julagi intre sui ji sui.”

- *wa* + jussive continues the command ("and let it separate", I p. 37 ex. 19):
  `ji to am julagi`. Machine had future `xa sen julagi`.
- בְּתוֹךְ → `fe midiya de` (R).

**1:7** Kos to, Teo fale kube, ji julagi intre sui hu sen bax kube ji sui hu sen supra kube. Ji to okur denmaner.

- Fulfilment "So God made" (I p. 37 ex. 19) → `Kos to,` (D 36×).
- Verbless relatives "the waters which were under …" need `sen`.
- עשׂה → `fale` (research: generic "make"; keeps the contrast with ברא).
- וַיְהִי־כֵן "and it was so" → `to okur denmaner` "it happened like that":
  `okur` v.intr "occur", `denmaner` adv "like that" (D: "moyto funsyon
  denmaner"). Not `denpul`, the adjective "that kind of".

**1:8** Teo namegi kube asman. Hay axam ji hay soba: duayum din.

**1:9** Teo loga: “Sui bax asman am toncu cel un loka, celki suhegeo na precu.” Ji to okur denmaner.

- *wa*-yiqtol after a jussive = purpose "so that the dry land appears"
  (I p. 236 ex. 117; p. 212 ex. 88) → `celki` + noun + infinitive (G).
- Jussive with subject: `S am V` (G: "Te am yam"). Niphal קוה → `toncu` (`-cu`
  intransitive, G).
- יַּבָּשָׁה → `suhegeo` (`suhe` "dry" + `geo`; not `suikal` "thirsty").
  Machine: `of bax asman` → `bax asman` (מִתַּחַת without לְ).

**1:10** Teo namegi suhegeo geo, ji te namegi he toncudu fe sui bahari. Ji Teo oko ki to sen bon.

- Fronted object as in 1:5.

**1:11** Teo loga: “Geo am gunca planta: gras hu da produti bija, ji drevo fe fruta hu da produti fruta fol sesu jongu, hu dasu bija sen in to, per geo.” Ji to okur denmaner.

- דֶּשֶׁא as the umbrella term with two kinds (majority: Delitzsch, Skinner,
  Gunkel, Westermann pp. 78, 123) → `planta:` then the two kinds. Alt.
  three classes (Dillmann, Driver).
- עֹשֶׂה פְּרִי "yielding fruit" → `produti fruta` (TDOT XI 391, SDBH:
  "produce"), not `fale`.
- "whose seed is in it" → `hu dasu bija sen in to` (G: `dasu`).
- `sesu` refers to the tree, the subject of its relative clause.

**1:12** Geo exgi planta: gras hu da produti bija fol tosu jongu, ji drevo hu da produti fruta, hu dasu bija sen in to, fol tosu jongu. Ji Teo oko ki to sen bon.

- Subject is the earth, so "its kind" is the plants' → `tosu`, not `sesu`.

**1:13** Hay axam ji hay soba: tigayum din.

**1:14** Teo loga: “Am hay luminxey in kube fe asman cel na julagi intre din ji noce, ji ete am sen fe rol fe ixara ji fe rol fe mosem, fe rol fe din ji nyan,

- מָאוֹר "luminary" → `luminxey` (`lumin` + `-xey` "thing", like `yamxey`),
  distinct from אוֹר `lumin`. Machine: `lumin` for both.
- *wa*-qaṭal in a modal series = intention (I p. 466 n. 17; Dallaire:
  purpose) → `ji ete am sen …`.
- לְ of role → `fe rol fe` (word list).

**1:15** ji ete am sen fe rol fe luminxey in kube fe asman, cel na lumin geo.” Ji to okur denmaner.

- `lumin` v.tr "illuminate" takes the object directly.

**1:16** Teo fale dua day luminxey — maxmo day luminxey cel na krasi din, ji maxmo lil luminxey cel na krasi noce — ji estare.

- "the great(er) light … the small(er) light" → `maxmo day`, `maxmo lil`.
  Machine misordered the numeral (`Dua Teo fale …`).
- לְמֶמְשֶׁלֶת הַיּוֹם → `cel na krasi din` (R: construct of an action).

**1:17** Teo plasi ete in kube fe asman cel na lumin geo,

- נתן "set" → `plasi` (D 69×); `gibe` "give" in 1:29. Machine order V-O-S
  (`Ete gibe Teo`).

**1:18** cel na krasi din ji noce, ji cel na julagi intre lumin ji luminkalya. Ji Teo oko ki to sen bon.

- מָשַׁל בְּ "rule over" → `krasi` + direct object (R).

**1:19** Hay axam ji hay soba: careyum din.

**1:20** Teo loga: “Sui am plucu lari fe jiwane bekreayen, ji piu am fley supra geo, fe perya de kube fe asman.”

- Jussives (machine: future `xa`).
- עַל "above" for flying → `supra` (R: above, not touching).
- שׁרץ "swarm, teem": `plucu` is provisional (L: todo).

**1:21** Teo julagi day kayvutu, ji moy jiwane bekreayen hu da retil, hu sui plucu yon da, fol etesu jongu, ji moy piu har fleytul fol etesu jongu. Ji Teo oko ki to sen bon.

- ברא Type 1: the three groups are separated, each to its own sphere (van
  Wolde pp. 15–16) → `julagi`.
- "with which the waters swarm" → `hu sui plucu yon da` (G: resumptive `da`
  after a preposition).
- כָּל־עוֹף כָּנָף "every winged bird" → `piu har fleytul` (`har` "with (having)").
- "their kind": subject is Teo → `etesu`.

**1:22** Teo baraka ete, loga: “Am samrudi ji am plucu, ji am pulgi sui in bahari, ji piu am plucu per geo.”

- V-O-S → S-V-O. לֵאמֹר → `, loga:` (D).

**1:23** Hay axam ji hay soba: limayum din.

**1:24** Teo loga: “Geo am exgi jiwane bekreayen fol etesu jongu: mumu, retilyen ji hewan fe geo, fol etesu jongu.” Ji to okur denmaner.

**1:25** Teo fale hewan fe geo fol etesu jongu, mumu fol etesu jongu, ji moy retilyen fe geo fol etesu jongu. Ji Teo oko ki to sen bon.

- Subject Teo → `etesu` (machine `sesu`).

**1:26** Teo loga: “Imi am fale insan in imisu imaje, kom imisu simya, ji ete am krasi mahi fe bahari, piu fe asman, mumu, moy geo, ji moy retilyen hu da retil per geo.”

- Cohortative → `Imi am` (G).
- *wa*-yiqtol "and let them rule" → `ji ete am krasi` + direct objects (R).
- צלם `imaje`, דמות `simya`, בְּ `in`, כְּ `kom` (R: image and likeness).
- `moy geo` follows MT "all the earth"; Syriac and many translations read
  "all the wild animals of the earth" (`moy hewan fe geo`).

**1:27** Teo julagi insan in sesu imaje; in imaje de Teo, te julagi te; te julagi ete cel manyen ji femyen.

- The two qaṭal clauses elaborate the wayyiqtol without *wa* (I p. 494 ex. 9)
  → semicolons, no `ji`.
- ברא → `julagi` throughout: van Wolde's reading is one sense of separation
  covering both "separate" (1:27c, "separated them into male and female",
  `cel`) and "set apart" (1:27ab); `julagi` (Epo *apartigi*) carries both.
- `sesu imaje`: God's own image (subject God).

**1:28** Teo baraka ete, ji Teo loga tas ete: “Am samrudi ji am plucu, am pulgi geo ji am infragi to, ji am krasi mahi fe bahari, piu fe asman, ji moy hewan hu da retil per geo.”

- V-O-S → S-V-O; "subdue it" (the earth) → `to`.

**1:29** Teo loga: “Am oko, mi gibe tas uyu moy gras hu da produti bija, hu sen fe perya de moy geo, ji moy drevo hu dasu fruta produti bija: to xa sen fe rol fe yamxey tas uyu.

- הִנֵּה → `Am oko,` (D: "Prabu loga, “Am oko, …”").
- Performative qaṭal "I give" → bare `mi gibe` (R); yiqtol "shall be" → `xa`.

**1:30** Ji tas moy hewan fe geo, tas moy piu fe asman, ji tas moy xey hu da retil per geo, hu har jiwa, mi gibe moy kijawiya fe gras fe rol fe yamxey.” Ji to okur denmaner.

- The verb is elided in Hebrew; `mi gibe` is supplied from 1:29 for clarity
  (mark as an addition).
- "in which there is a living soul" → `hu har jiwa` ("which has life").
- יֶרֶק עֵשֶׂב → `kijawiya fe gras` (R: construct, part).

**1:31** Teo oko moyto hu te le fale da, ji am oko, to sen daymo bon. Hay axam ji hay soba: sisayum din.

- "all that he had made" → `moyto hu … da` (D 9×); `le`: completed before
  the narrated now, in a relative clause (R).
- וְהִנֵּה → `ji am oko,`; טוֹב מְאֹד → `daymo bon` (adverb first, G).

---

## Feeding back into the pipeline

Rules the machine could take over (not yet in the rtx): speech quotation
marks; `sesu`/`tesu` by subject; V-O-S with object pronoun → S-V-O; verbless
relatives `hu sen`; *wa*-yiqtol after a jussive → `am` or `celki`; ordinal
`maxmo` for the "great/small light". Lexicon entries changed: מָאוֹר
`luminxey`; עשׂה in 1:11–12 `produti` (sense "yield").
