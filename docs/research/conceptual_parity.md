# Conceptual parity in Globasa: concepts, souls and 氣

*Research notes of 21 November 2026, compiled for the Globasa lexicon team. Every proposal
here is a proposal: nothing has been changed in the word list. Word forms are suggestions
for the Word Selector and the team.*

## Summary

Globasa's lexicon is currently shaped by English and Christian categories. It lacks Indian,
East Asian and Indigenous concepts that are widespread in its own source languages, and its
soul vocabulary follows the English "spirit, soul".

- **Principles.** A meaning follows how source-language speakers use a word, not English or
  Esperanto, and must be attested Sprachbund-wide, or recur across unrelated families.
- **Religion.** Abrahamic slots are filled (bishop, sin, baptism, Easter, godparents), while
  dharma, nirvāṇa, saṃsāra, mantra, qi and 孝 are missing.
- **Indigenous concepts.** These are coined as derivations from existing roots when they recur
  among unrelated peoples. Kinship data show three such gaps.
- **Souls.** *ruho* becomes "spirit" (beings, morale). A person's several souls are named with
  two heads, *hon* (souls that travel) and *paku* (souls bound to the body), plus modifiers.
- **氣.** A new word for the vital substance of Chinese philosophy and medicine, the one sense
  that every language borrows rather than translates.

Section 14 separates sources checked in a literature index from those cited from memory.

## 1. Principles

1. **Avoid anglocentrism at every step.**
   - English Wiktionary sense inventories and English glosses are one view, not the standard.
   - Corpora translated from English hide distinctions, so prefer originals and direct
     translation between non-English languages.
   - Cross-lingual embedding spaces lean toward English, so concept identity should come from
     translation correspondence, not embedding closeness.
   - Vetting shows each concept as a multilingual word set with examples, not under an English
     heading. Wierzbicka's *Imprisoned in English* (2014) argues this case at length.
2. **Breadth criterion.** A meaning must be attested Sprachbund-wide or wider, never narrower.
   For Indigenous concepts, recurrence across independent families and regions replaces
   Sprachbund breadth. Families and macro-areas are counted, never languages or speakers.
3. **Native usage.** Indian, East Asian and Indigenous concepts enter Globasa with the meaning
   and register they have in their own languages, not with the exotic or drifted English use
   (karma "aura", mantra "slogan", chi "mystical energy").
4. **Minimal register.** The source shapes the meaning; the output stays plain Globasa.
5. **Esperanto is one witness, not a veto.** Globasa's semantics follow Esperanto, which is
   itself European. Use the Epo column to see where a distinction already exists, never to
   reject one Esperanto lacks.
6. **Open data only.** Open licences only, and nothing that needs a licence application.
   - Kinbank, CLICS4, D-PLACE, Pulotu and Lexibank are CC BY.
   - eHRAF is licensed, so it's excluded.
   - The Tanzil Qur'an translations carry a NoDerivs clause despite a CC BY label
     ([van Gassen 2026](https://arxiv.org/abs/2606.28867)), so they're excluded.

## 2. Religious vocabulary

**Audit of `word-list.csv`.**

- **Abrahamic concepts with their own entries:** *anjilyen* angel, *biskopo* bishop, *santoyen*
  saint, *dambi* sin, *batiza* baptism, *miza* mass, *Santo Papa* pope, *nubwayen* prophet,
  *rabin* rabbi, *nimatu* grace, *Bibli*, *Kuran*, *Kristodin* Christmas, *Rujiwadin* Easter, and
  godparent words.
- **Non-Abrahamic concepts:** mostly tradition names (*Budaismo*, *daoismo*, *Hinduismo*, *Siki*,
  *Konfuci*), plus *karma*, *yoga* and *medita*.
- **Missing:** dharma, nirvāṇa, saṃsāra, guru, mantra, puja, sutra, Veda, bodhisattva, sangha,
  qi, yin/yang, 孝, Vesak and Diwali.

**General words with Abrahamic meanings.**

| Word | Current meaning | What it doesn't fit |
|---|---|---|
| *teo* | glossed "God" | the Hindu deva, the Shinto kami |
| *janatu*, *jahanom* | paradise and hell | temporary Buddhist heavens and hells; 天 |
| *ruho* | "spirit, soul" | multiple-soul systems; see §§7–10 |
| *dambi* | sin | a karmic fault |
| *kido* | prayer | puja, offerings |
| *xinen* | faith | traditions that put practice before belief |
| *dini* | religion | the category itself is contested: 宗教 is a 19th-century Japanese coinage |

*dao* "path, way" already fits 道.

**Parity rules.**

- Judge each tradition by breadth within its own sphere, as *biskopo* and *batiza* are judged
  within Christianity.
- Check every slot for every tradition: clergy, text, afterlife, ritual, holy day, being, fault,
  practice.
- Write neutral definitions for the general words.
- Include smaller traditions too: Shinto, Jain, Sikh, Chinese folk religion, Indigenous
  traditions.

**Corpus caution.** Bible translations vary by doctrine (*almah*, *ekklesia*, *metanoia*,
*adelphoi*), and translations made under one agency's policy aren't independent evidence.

- A split counts only if it holds across translations of the same language from different
  denominations and translation philosophies.
- Bible evidence confirms; it is never enough on its own.
- Comparable (untranslated) corpora are the main source.

## 3. Indigenous concepts

**Rule.** Indigenous concepts get the same footing as world-religion concepts. When a concept
recurs among unrelated peoples, it is coined as a derivation from existing Globasa roots, with
components chosen the way the source languages themselves build such words. A concept specific
to one people gets no general coinage; texts keep that people's own term.

*xaman* (from Evenki) and *tabu* (from Tongan) show what happens otherwise: one people's word
generalized by anthropology.

**Kinbank experiment** (`concept_discovery/kinbank_categories.py`).

- **Data:** [Kinbank](https://github.com/kinbank/kinbank) (CC BY 4.0): 1,287 languages, 254
  families. The grid is male ego, 26 cells.
- **Global view:** a family-weighted H0 filtration (single linkage on colexification).
- **Systems:** language clustering (Ward linkage, *k* chosen by silhouette).
- **Validation only:** Murdock's systems labelled by rule, adjusted Rand index 0.43.

| Recurrent category | Languages | Families | Macro-areas |
|---|---|---|---|
| cross cousins {FZS, MBS} as their own category | 278 | 90 | all |
| parallel cousins with siblings; father's brother = father (Iroquois-type) | 278 | 90 | all |
| elder vs younger sibling (H0 merge at 0.54: about half the families keep them apart) | — | — | all |

Globasa's kinship terms (*sodar*, *kuzin*, *tie*, plus *man-* / *fem-*) follow the Eskimo
(English-type) system, so all three are derivation candidates.

**Other candidates to check against D-PLACE, Pulotu and CLICS:**

- avoidance relatives (such as the mother-in-law)
- the name taboo for the dead
- the spirit of a place, and custodial relations to land
- obligatory gift exchange
- third-gender roles
- moieties

**Two framing issues:** *mito* "myth" is applied to other peoples' sacred narratives but not to
the Bible, and *ruho* can't express multiple-soul systems (§§7–10).

## 4. Indian and East Asian concepts

**English borrowings from East Asia** (`concept_discovery/english_east_asian_borrowings.py`).

- **Method:** English Wiktionary etymologies (bor, cal, der) from Chinese, Japanese, Korean,
  Vietnamese, Ainu, Mongolian, Manchu and Tibetan, checked against Globasa through LexiliAsel
  source forms, the Zho column and the English glosses.
- **Result:** 3,359 English word+PoS entries, 3,194 of them missing from Globasa (*sushi*,
  *origami*, *kowtow*, *brainwash*, *add oil*).
- **Breadth column:** how many other source languages borrowed the same term (*tsunami* 7,
  *karate* 8).
- **What Globasa already has:** concrete East Asian loans that English took (*umami*, *fenxui*,
  *tofu*, *karaoke*). Abstract social and emotional concepts are missing (面子, 孝, 缘, 人情,
  热闹, 客气, 懐かしい). Globasa inherits English's gaps.

**Indian concepts in Hindi and Telugu and loaned into East Asia**
(`concept_discovery/indic_east_asian_concepts.py`).

- **Scope:** 160 Sanskrit, Pali and Prakrit etymons with a Hindi or Telugu descendant and an
  East Asian one.
- **Attested in both Hindi and Telugu:** 107, of which 68 rely on a Telugu entry spelt like the
  Sanskrit. That fallback is labelled, because English Wiktionary has few Telugu etymology links.
- **Missing in Globasa:** 85 of the 107, among them dharma, saṃsāra (輪廻), nirvāṇa (涅槃),
  kleśa (煩悩), kṣaṇa (刹那), prajñā (般若), dhyāna (禅), samādhi, anitya, kalpa (劫), naraka,
  preta, arhat, asura, bhikṣuṇī, upāsaka, ācārya, mantra, maṇḍala, stūpa, sūtra, tantra,
  āyurveda, lakh and koṭi.
- **Already covered:** *karma*, *yoga*, *Buda*, *sandal*, *jungla*, *zira*, *dexa*, *kurkuma*.
- **Coverage rule:** a concept counts as covered only if one Globasa word matches through two or
  more languages, with a shared Han spelling counting once.

**Native usage, not English drift.**

- Hindi धर्म: religion, virtue, **duty**. Telugu ధర్మము: duty, virtue, right, alms, rule. English
  *dharma* is a technical term.
- In East Asia these concepts live mostly as calques (業, 縁, 輪廻, 無常, 方便), so calques count
  as evidence for the meaning.

Each concept's senses fall into three layers:

1. the core shared by Indian and East Asian usage, which becomes the Globasa meaning;
2. regional extensions, such as Japanese 我慢 "endurance" (from *māna* "pride"), which don't
   come along;
3. English drift, which is excluded.

## 5. Chinese concepts

In the Sinosphere, Daoist and Confucian terms are ordinary words. 道 is road, way, method,
principle. 禮 is rite, etiquette, courtesy, gift. 功夫 is time, effort, skill. 君子 is a person of
virtue.

Globasa already integrates 道 natively: *dao* "path, way, route", and *doduku* "morality" from
道德. That's the model to follow.

Missing: 德, 氣, 禮, 孝, 仁, 義, 陰陽, 功夫, 君子, 無為, 中庸, 緣, 面子, 人情, 道理, 誠, 忠.

Assess each sense across Chinese, Japanese, Korean and Vietnamese, matched by Han spelling
(the `sinosphere` module), using the same three layers.

### 無為: *walfale*, not *nilfale*

The earlier audit's proposal ([semantic-eurocentrism-audit.md](semantic-eurocentrism-audit.md),
Revisions 1–2) stands: **無為 = *walfale*** (*wal-* "without" + *fale* "do").

1. ***nilfale*** (with *nil-* "no") was adopted first, on the belief that "non-action" was the
   agreed literal sense.
2. It was **withdrawn** when the Internet Encyclopedia of Philosophy said the opposite: that the
   traditional rendering is generally agreed to be incorrect, and that Slingerland's "effortless
   action" is preferred.
3. It was **reinstated** after a test on *Daodejing* 37, 道常無為而無不為 "the Way never acts, yet
   nothing is left undone". The line is a paradox built on stacked negation, and "effortless
   action" destroys it.
4. It was **superseded by *walfale*** because 無 is productive in the *Daodejing* (51 distinct
   forms, 102 tokens), so the choice is grammatical, not lexical.
   - *wal-* "without" (cf. *walya* "be without") matches 無's verbal sense and already attaches
     to content roots.
   - *nil-* is bound to the correlative grid.

**無不為 is a clause, not a compound.** *wal-* + *nen-* + *fale* would cancel out, and 無 does
different work in each half: privative in 無為, quantifying "nothing" in 無不為. So *Daodejing* 37
becomes ***Dao moywatu walfale, mas nilto no befale***.

**Not *nenfale*.** *nenfale* is already used for "omission", failing to do a required act
(UDHR 11.2: *fale or nenfale* "act or omission"). *walfale* names a way of acting: without forcing.

**Scholarship.** Readings of *wuwei* are contested (Slingerland's "effortless action" against
Fraser 2007, *Philosophy East and West*), and a derivation can easily encode one scholar's
position. The *Daodejing* 37 test avoids that.

**Proposed verb construction (user, 2026-11-21): *walfale na* + verb, "do something without
forcing it, fluently".**

- Bare *walfale* keeps the *Daodejing* sense (not acting, not forcing), so the paradox of
  *Daodejing* 37 survives. The construction carries the "effortless action" reading, so it doesn't
  become the bare word's definition.
- **Test passage:** Cook Ding carving the ox (庖丁解牛, *Zhuangzi* 3: 恢恢乎其於遊刃必有餘地矣).
  Other candidates: the wheelwright Pian (天道) and the cicada catcher (達生).
- **Recurrence to check:** Japanese 無心 *mushin*, Hindi सहज *sahaj*, Persian *ravān* "flowing,
  fluent".
- **Also to check:** whether *walfale* takes a *na* complement like *abil na*, and its overlap with
  existing words for "fluent" or "easy".

**Still open:** whether *walfale* also covers the Buddhist 無為, a calque of Sanskrit *asaṃskṛta*
"the unconditioned" (whose chief case is nirvāṇa), and Japanese 無為 *mui* "idleness". Each needs
a canonical-passage test of its own.

### *darma* and *nirvana*: native meanings, not doctrinal lists

The earlier audit proposed both as loans "defined by doctrinal lists rather than decompositions".
Under the native-usage principle (§1.3), the meaning should instead follow how Indian and East
Asian speakers use the words. Doctrinal definitions then become uses of that meaning, not the
definition itself.

**Evidence from Wiktionary (§4).**

| Language | dharma | nirvāṇa |
|---|---|---|
| Hindi | धर्म: religion, faith; virtue, righteousness, morality; **duty** | निर्वाण: liberation, extinction; the death of a Buddha or saint |
| Telugu | ధర్మము: **duty**, virtue, right, alms, rule or precept | no entry found |
| Chinese | 法: law, method, way; the Buddha's teaching (佛法); a phenomenon (諸法). 達摩 is the name Bodhidharma | 涅槃, 滅度: release; the Buddha's death (入涅槃); modern 鳳凰涅槃 "rebirth from the ashes" |
| Japanese | 法 *hō*; 達磨 *Daruma* is a name and a doll | 涅槃: release; the Buddha's death (涅槃会, the reclining Buddha) |
| English (drift) | a technical term of Hinduism and Buddhism | "bliss, paradise" |

**Proposed meanings for vetting:**

- ***darma*: duty, right conduct, virtue; the order that things rightly follow; (Buddhist) the
  teaching.**
  - Hindi and Telugu share duty and virtue. Telugu "rule, precept" and East Asian 法 "law, way"
    share the sense of order.
  - Hindi "religion" stays with *dini*: it is a modern Hindi sense and not shared.
  - Telugu "alms" (cf. Hindi धर्मशाला "charitable rest-house") needs a check across languages.
- ***nirvana*: release from suffering and rebirth; the death of a Buddha or saint.**
  - Both senses are shared by India and East Asia.
  - Exclude English "bliss" and Chinese 鳳凰涅槃.
  - Check Indonesian *nirwana*, which may have its own "heaven, eternal happiness" sense in Malay
    usage. If so, that's an Indonesian development to weigh, not English drift.

**Checks still needed.**

- The Chinese and Japanese senses of 法 and 涅槃 in the table are from general knowledge. Confirm
  them in the native Wiktionary indexes, as was done for 氣.
- Add Indonesian (*darma*, *nirwana*) and Korean and Vietnamese (법 / *pháp*, 열반 / *niết bàn*).
- Test both words against canonical passages, as for *walfale*. Candidates:
  - for *darma*, the Bhagavad Gita on *svadharma* (3.35)
  - for *nirvana*, the Pali "blowing out" image in Sutta Nipāta 1074, and a 西遊記 passage

## 6. The soul problem

*ruho* is glossed "spirit, soul" (from Arabic *rūḥ*, Persian, Indonesian *roh*, Turkish *ruh*,
Swahili *roho*, Russian дух). The Christian and English sense merges two things that many
traditions keep apart: the free soul, and the self that survives death.

Globasa texts already use *ruho* more broadly:

- **disposition:** UDHR article 1, *fol ruho fe sodarya* "in a spirit of brotherhood";
- **spirits of the dead:** the Halloween text in Doxo;
- **the inner self:** Poe's *amikuya de ruho*.

The Hebrew Bible project already renders רוח as *vento* and נפש חיה as *bekreayen* in Genesis 1.

*xabahu* is glossed "ghost, apparition, phantom, spirit, spectre; haunt" (from Arabic and
Persian شبح *šabaḥ*).

## 7. The scholarly framework: free soul and body souls

The comparative framework comes from Ernst Arbman's work on Vedic India (1926–27):

- **the free soul:** it leaves the body in dreams, trance and death, and survives as a shade;
- **body souls:** a life or breath soul, and an ego or mind soul.

Others carried it into other regions:

- Hultkrantz (1953) for North America
- Paulson (1958) for northern Eurasia
- Bremmer (1983) for early Greece, where *psychē* is the free soul and *thymos*, *menos* and
  *noos* are body souls

Recent work builds on Bremmer: [Gäb 2021](https://doi.org/10.5282/ubm/epub.77239),
[Blanco 2013](http://etheses.dur.ac.uk/9419/), and the volume
[*Horizons of Shamanism*](https://doi.org/10.16993/bag) (Jackson ed. 2016).

| Tradition | Free soul | Breath or life soul | Mind soul |
|---|---|---|---|
| Vedic (Arbman) | *asu*, later *ātman* | *prāṇa* | *manas* |
| Homer (Bremmer) | *psychē* | *thymos*, *menos* | *noos*, *phrenes* |
| N. Eurasia, N. America | dream soul | breath soul | ego soul |
| China (Yü 1987) | 魂 *hun* | 氣, 魄 *po* | 心 |
| Mesopotamia (Abusch 1998; Steinert 2012) | *zaqīqu*; *eṭemmu*, the ghost | *napištu* | *ṭēmu* |
| Akan | *sunsum*; *okra* returns to God | | |

**Further scholarship:**

- **Hebrew:** Wolff and Johnson read *nefesh* as the living, needy person.
  [Steiner 2015](https://doi.org/10.15699/9781628370775) argues for a *nefesh* outside the body
  (the Katumuwa stele), developed by [Schaper 2020](https://doi.org/10.1163/15685330-12341427).
- **Chinese:** Brashier (1996) cautions that Han texts don't support so tidy a 魂/魄 pair.
- **Pre-Christian Greek:**
  - Stoic *pneuma* holds things together by tension: the cohesion (*hexis*) of a stone, the
    nature (*physis*) of a plant, the *psychē* of an animal.
  - Christian usage narrowed *pneuma* and *psychē* to the Spirit and the immortal soul.
  - Even in the NT, *psychē* often means "life" (Matthew 16:25).
  - Anaximenes fragment B2 ("air holds us together") is probably inauthentic
    ([Vítek 2025](https://doi.org/10.5507/aither.2025.002)).
- **Comparisons of breath and qi:**
  - Kuriyama 1999 (pneuma and qi in Greek and Chinese medicine)
  - Lloyd & Sivin 2002
  - [Stanley-Baker 2022](https://doi.org/10.4324/9780203740262-4)
  - [Craik 2009](https://doi.org/10.1017/s0025727300003331)
  - [Yoeli-Tlalim 2010](https://doi.org/10.1016/j.shpsc.2010.10.005)
  - [Škof 2021](https://doi.org/10.4312/as.2021.9.3.303-320)
  - [Orqueda 2015](https://doi.org/10.1590/1981-5794-1504-5)
  - [Cavallin 2003](https://doi.org/10.30674/scripta.67280)
  - [Oxley & Russell 2020](https://doi.org/10.1177/1357034x20913103)
  - [Andreini 2011](http://hdl.handle.net/10278/29436)
  - [Sivin 2018](https://scholarworks.iu.edu/iupjournals/index.php/jwp/article/view/2156) on
    method
- **Cautions:**
  - The typology is a scholars' construction.
  - Missionary translation has reshaped Indigenous soul words
    ([Pomedli 1985](https://doi.org/10.7202/400138ar);
    [Afriyie 2000](http://hdl.handle.net/10413/3307)).
  - Early Chinese "holism" is contested (Slingerland 2019).

## 8. Outside Eurasia

**The Americas.**

- Hultkrantz (1953) finds soul dualism across most of North America.
- **Nahua** (López Austin 1980): *tonalli* in the head (it leaves in sleep and can be lost through
  fright), *teyolia* in the heart (it goes to the afterlife), *ihiyotl* in the liver (a breath-like
  emanation). See also [Dufendach 2017](https://escholarship.org/uc/item/80d033rm).
- **Maya:** *ch'ulel*, plus an animal co-essence (Vogt 1976).
- **Latin America:** *susto*, illness from soul loss through fright (Rubel, O'Nell &
  Collado-Ardón 1984).
- **The Andes:** Aymara *ajayu* and Quechua *animu* are called back after fright.

**Africa.**

- **Akan:** *okra* (life-soul and destiny, returns to God), *sunsum* (travels in dreams), *ntoro*
  (from the father) ([Agyarko 2026](https://doi.org/10.7833/125-1-2431); Gyekye 1987).
- **Nuer:** *ring* (flesh), *yiegh* (breath, life), *tie* (soul, intellect) (Evans-Pritchard 1956).
- **Dogon:** *kikinu* (Griaule & Dieterlen).
- **Bantu:** the ancestral spirit (*-zimu*) is distinct from the heart-soul.

**Australia.** Among the Yolŋu, *birrimbirr* returns to the clan's waters and *mokuy* is the
ghost that stays behind (Warner 1937).

## 9. Colexification data (CLICS4)

`concept_discovery/clics_soul_colexifications.py`, using
[CLICS4](https://doi.org/10.5281/zenodo.16900179) (Tjuka, Forkel, Rzymski & List 2026, CC BY 4.0).

- **Unit:** languages are pooled by Glottocode.
- **Denominator:** families that record both concepts.
- **Rate:** family-weighted, the mean over families of each family's share of colexifying
  languages.

| Concepts | Families colexifying / with both | Rate | Areas |
|---|---|---|---|
| GHOST = SOUL | 23 / 59 | 0.23 | 5 |
| GHOST = DEMON | 14 / 53 | 0.15 | 4 |
| SOUL = HEART | 13 / 70 | 0.08 | 5 |
| SOUL = MIND | 8 / 49 | 0.08 | 3 |
| BREATH = AIR | 11 / 58 | 0.07 | 4 |
| SPIRIT = BREATH | 5 / 24 | 0.06 | 2 |
| SOUL = LIFE | 6 / 66 | 0.05 | 4 |
| SOUL = BREATH | 6 / 53 | 0.03 | 3 |
| SOUL = DREAM, THROAT, SELF; BREATH = ANGER, STRENGTH | 0 | 0 | — |
| controls: SOUL = BODY, GHOST = GOD | 2 / 68, 3 / 45 | 0.005, 0.007 | — |

- **GHOST = SOUL is widespread, but the shared words are soul or spirit words** (πνεῦμα, дух,
  *vaim*, *nanm*, *ruħ*), not apparition words like *šabaḥ*. So *xabahu* should not become the
  free-soul word.
- **BREATH = SOUL is regional** (Finnish *henki*, Udmurt *lul*, Komi *lov*, Sakha *tɯːn*, Saami
  *vuoigŋa*), plus Greek *pneuma*.
- **By area:**

  | Area | Pattern |
  |---|---|
  | North America | GHOST = SOUL in 4/9 families, 0.39 (Yaqui *jiapsi*, Tzotzil *ʔanima*, Zuni *hapa*, Karuk *pikšip*) |
  | South America | GHOST = SOUL in 8/29, 0.20 (Mapudungun *pɨlʸɨ*, Aguaruna *wakan*) |
  | Africa | SOUL = HEART (Bantu *moyo*, *omwoyo*) and GHOST = ancestral SPIRIT (*omuzimu*, *risambwa*) instead; GHOST = SOUL only among the Dogon |
  | Australia | no data |

- **Limits:**
  - The questionnaire glosses are in English.
  - Some sources are missionary-era.
  - Only identical forms are counted.
  - Some denominators are small.

## 10. 氣 (qi / ki)

氣 is not a soul in the typology: the souls are 魂 and 魄. It is uncountable vital stuff, so it
gets a word of its own, separate from *ruho*.

**In the native Wiktionaries** (Chinese and Japanese Wiktionary).

- **Shared by both:**
  - gas
  - the substance that sustains life: 維持生命活動的基本物質 / 活力の源…流動的な仮想の物体
  - the flowing element that makes up all things (Chinese philosophy)
  - temperament: 特質；性格 / ケ 性質
  - state of mind: 精神狀態 / 心の状態
- **Chinese only:** breath, weather, smell, anger.
- **Japanese only:** intention, fizz, a trace of.

**Shared compounds.** 56 compounds are shared by Chinese and at least two of Japanese, Korean
and Vietnamese.

- in all four: 空氣 air, 氣體 gas, 氣候 climate, 勇氣 courage, 氣質 temperament, 客氣 polite
- in three: 天氣, 士氣, 活氣, 元氣, 氣分

Globasa already has *hawa* (air), *gas*, *nafasu* (breath), *klima* (weather), *energi*, *awra*,
***yunki*** (from 勇气 / 勇気 / 용기) and ***gibun*** (from 気分 / 기분).

**Translation tables.**

- The sense "concept of Chinese philosophy and medicine" is a loan in all 13 languages listed:
  - Arabic تشي / كي, Persian چی, Hebrew צ׳י
  - English *qi/chi*, French *qi*, German *Ki/Qi*, Russian *ци*
  - Indonesian *qi*, Turkish *çi*
  - Esperanto *ĉjio*
  - Korean 기, Vietnamese *khí*
- 士氣 and 氣概 are translated with Russian **дух**. Persian *ruhiyye* and Arabic *rūḥ maʿnawiyya*
  build morale from *rūḥ*.
- 元氣 → health, energy; 気質 → temperament.

**Conclusion.**

- The new word means vital energy and the cosmological substance (Chinese philosophy, medicine,
  qigong), described neutrally.
- Morale and spirit go to *ruho*, energy to *energi*, temperament to a temperament word.
- **Form:** every short form collides with an existing word: *ci* (endearment particle), *ki*
  ("that"), *gi* (the causative suffix). A decision for the team.
- **Comparisons:** Greek *pneuma* and Sanskrit *prāṇa* remain the scholarly comparisons for the
  technical layer. In everyday Hindi, *prāṇ* means "life", which is *jiwa*.
- **Check later:** Malay/Indonesian *semangat*, and Sanskrit *ojas* for the vigour sense.

## 11. Proposed vocabulary

| Concept | Globasa | Status |
|---|---|---|
| spirit: a bodiless being (spirits of the dead, ancestral and nature spirits; the divine Spirit), and the spirit of a person or group (morale, ethos) | ***ruho***, reglossed without "soul" | proposal |
| a soul that travels: free, dream soul | ***hon*** (魂: Korean 혼, Vietnamese *hồn*, Middle Chinese *hwon*, Japanese *kon*) | new root, proposal |
| a soul bound to the body | ***paku*** (魄: Middle Chinese *pak*, Japanese *haku*, Korean 백, Vietnamese *phách*) | new root, proposal |
| the self that survives death (Christian, Islamic, Platonic soul; *jīva*) | compound with head *seya* "self" | form open |
| ghost, apparition (harmful) | *xabahu* | unchanged |
| vital energy | a new 氣 word | form open |
| breath, life, mind | *nafasu*, *jiwa*, *siko* | unchanged |

**Soul types** are compounds on *hon* or *paku*. The test is whether the soul leaves the body
and travels.

| Modifier | Head | Examples |
|---|---|---|
| *roya* "dream" | hon | 魂, Homeric *psychē*, *tonalli*, *sunsum* |
| *nafasu* "breath" | hon | 禮記: 魂氣歸于天 "the *hun*-breath returns to heaven" |
| *saye* "shadow" | hon | *skia*, Malay *bayang* |
| *hewan* "animal" | hon | *wayhel*, *nagual* |
| *name* "name" | hon | Inuit *atiq* |
| *kismetu* "fate" | hon | *okra*, *orí* |
| *lefeatre* "ancestor" | hon | reincarnating ancestor souls |
| *osto* "bone" | paku | the Siberian bone soul |
| *damu* "blood" | paku | blood souls |
| *jiwa* "life" | paku | life that ends with the body (Nuer *yiegh*) |
| (bare) | paku | 魄: 形魄歸于地 "the body-*po* returns to earth" |
| *tutum* "heart", *siko* "mind" | case by case | *teyolia* (travels) → hon; *noos* (stays) → paku |

Chinese texts get their own pair: 三魂七魄 is "three *hon*, seven *paku*". Where traditions
differ, the tradition being described decides.

**Free soul versus the self that survives death.** These answer different questions, so they
get different words:

- The free soul is defined by mobility: it leaves the body during life. That makes it *hon*.
- The surviving self is defined by identity: it is the person themselves, carried on to judgment
  or rebirth. That makes it the *seya* compound.

Traditions combine the two in different ways:

| Tradition | Free soul | Self that survives death |
|---|---|---|
| Homer | *psychē* | none: the shade has no wits (*phrenes*); Tiresias is the exception (*Od.* 10.493–495) |
| China | 魂 (it disperses or becomes an ancestor) | partly the ancestor who receives offerings |
| Plato, Christianity, Islam | merged into the immortal soul | the soul (*psychē*, *anima*, *nafs*/*rūḥ*) |
| Indian traditions | the dream state | *jīva* / *ātman* through rebirth |
| Nahua | *tonalli* | *teyolia* |
| Akan | *sunsum* | *okra* (returns to God) |
| Yolŋu | *mokuy* (the ghost that stays) | *birrimbirr* (returns to the clan waters) |

Homer's *psychē* is *hon* yet is not a surviving self, so the two can't share a word. The
Christian and Platonic merge is what the current gloss of *ruho* reflects. In translation, a
passage that stresses departure or wandering takes *hon*; one that stresses judgment, salvation
or rebirth takes the compound (Matthew 10:28). A Nahua text needs both words.

**Alternatives considered.**

- *ruho* could replace *hon*: it saves a root, but *ruho* then carries three senses and the pull
  toward the Christian "soul" returns.
- *ruho* can't replace *paku*: its sources are souls that leave the body.
- Splitting souls by fate after death, origin or seat in the body works as modifiers, not heads.
- Broadening *xabahu* to the free soul is not supported (§9).

## 12. Translation use

To make the free soul familiar beyond anthropologists, render it consistently in translations.

- **Iliad:** 1.3–5; 5.696–698; 16.855–857; 22.361–363; 22.466–467; 23.65–107.
- **Odyssey:** 10.493–495; 11.204–222; 24.1–14.
- **New Testament:**
  - Matthew 14:26 *phantasma* → *xabahu*
  - Luke 24:37–39 and Acts 12:15 (a ghost, a double)
  - Matthew 10:28 → the surviving-self compound
  - Matthew 16:25 *psychē* → *jiwa*
- **Chinese:** 楚辭《招魂》《大招》; 左傳 Duke Zhao 7 (Zichan on 魄 and 魂); 禮記《郊特牲》; 離魂記 and
  倩女離魂; 牡丹亭; 聊齋誌異 (阿寶, 葉生); 西遊記 chapters 3 and 10–11.
- **Elsewhere:** the Popol Vuh; Nahua texts in the Florentine Codex; Akan and Yoruba collections,
  read for missionary framing.

**Open texts.** Homer (public domain); the NT in Nestle 1904 or Robinson–Pierpont (public
domain), or SBLGNT (CC BY 4.0). NA28 is not open. Chinese originals from Wikisource; ctext.org is
not openly licensed.

**Pipelines.**

- `apertium-glb-grc`: a period- and genre-dependent sense for *psychē*.
- `apertium-qgb-zho`: bidix entries for 魂 / 魄 / 氣.
- Doxo reader pages and Anki cards.

The passage references above are from memory and need checking against the texts.

## Relation to the earlier audit

[semantic-eurocentrism-audit.md](semantic-eurocentrism-audit.md) (7–8 September 2026) proposed
several of the same items. That audit takes precedence where the two overlap.

- **Agreed:**
  - *laosodar* / *junisodar* for elder / younger sibling, which the Kinbank result here
    independently supports
  - *xenmorcuki* / *rixencu* for saṃsāra / rebirth
  - *hurugi* (mokṣa) and *kalya* (śūnyatā), which are already in the lexicon
  - *nirvana* and *darma* as loans
  - *walfale* for 無為
  - the *janatu* gloss correction
  - *inyangu*, *renjingu*, *kongu* and similar forms for 陰陽, 人情, 空
- ***hun* / *po*:** withdrawn there, because the dual is glossed only in Chinese and *po* is
  misparsed as *pole*, *pori*, *polisi*; the changelog later restored *hunpo* as phonotactically
  permitted.
  - *hon* / *paku* (§11) avoid the misparse.
  - The cross-cultural evidence in §§7–9 answers the "only Chinese" objection, since the pair is
    used as heads for soul types everywhere.
  - Both forms still need the collision checker (`globasa_collision_check.py`).
- **Method:** the same rule applies to every proposal here: test a term of art against a canonical
  passage it must translate.

## 13. Open decisions

1. Regloss *ruho* without "soul", and its morale sense, perhaps by a derivation as in Persian
   *ruhiyye*.
2. Adopt *hon* and *paku* as heads, or *ruho* in place of *hon*.
3. The forms of the soul-type compounds, the surviving-self compound and the 氣 word (collisions:
   *ci*, *ki*, *gi*).
4. Whether 氣 also takes the "temperament / state of spirit" sense shared by Chinese and Japanese
   Wiktionary, or whether that sense goes to *ruho* and a temperament word.
5. Build local Korean and Vietnamese Wiktionary indexes, so Sinosphere sharing can be counted over
   four languages.
6. ***darma*, *nirvana* and *walfale*** (see the end of §5): confirm the native senses in the
   native Wiktionaries, add Indonesian, Korean and Vietnamese, and run the canonical-passage
   tests. For *walfale*, decide whether it also covers the Buddhist 無為 and Japanese *mui*.
7. Fix the concept-index etymology gap: `{{bor+|..|-}}` followed by a script template loses its
   term, and calques are missing from the reverse table.

## 14. References

**Checked in a literature index (OpenAlex / arXiv) during this research:**

- Afriyie, E. 2000. *A comparative study of Akan and biblical concepts of a human being.* http://hdl.handle.net/10413/3307
- Agyarko, R. O. 2026. "Sunsum and ntoro in Akan anthropology." https://doi.org/10.7833/125-1-2431
- Andreini, A. 2011. "Categorie dello 'spirito' nella Cina pre-buddhista." http://hdl.handle.net/10278/29436
- Blanco, C. 2013. *The soul as a butterfly in Greek and Roman thought.* http://etheses.dur.ac.uk/9419/
- Cavallin, C. 2003. "Sacrifice as action and actions as sacrifices: the role of breath…" https://doi.org/10.30674/scripta.67280
- Craik, E. M. 2009. "Hippocratic bodily 'channels' and oriental parallels." https://doi.org/10.1017/s0025727300003331
- Dufendach, R. 2017. *Nahua and Spanish concepts of health and disease in colonial Mexico.* https://escholarship.org/uc/item/80d033rm
- Gäb, S. 2021. *Seelenvorstellung und Totenglaube bei Homer.* https://doi.org/10.5282/ubm/epub.77239
- Gessler, L. & Schneider, N. 2021. "BERT has uncommon sense." https://arxiv.org/abs/2109.09780
- Jackson, P. (ed.) 2016. *Horizons of Shamanism.* Stockholm UP. https://doi.org/10.16993/bag
- Karidi, T. et al. 2021. "Putting words in BERT's mouth." https://arxiv.org/abs/2109.11491
- Krech, V. 2025. "A multitude of hearts" (intro, *Metaphor Papers*). https://doi.org/10.46586/mp.438.520
- Orqueda, V. 2015. "Variación semántica de ātmán- en el R̥gveda y el Atharvaveda." https://doi.org/10.1590/1981-5794-1504-5
- Oxley, R. & Russell, A. 2020. "Interdisciplinary perspectives on breath, body and world." https://doi.org/10.1177/1357034x20913103
- Pomedli, M. M. 1985. "The concept of 'soul' in the Jesuit Relations." https://doi.org/10.7202/400138ar
- Rezania, K. & Mohtashami, N. 2025. "Conceptualizing CONDUCT OF LIFE through WAY metaphors." https://doi.org/10.46586/mp.430
- Schaper, J. 2020. "Elements of a history of the soul in North-West Semitic texts." https://doi.org/10.1163/15685330-12341427
- Sivin, N. 2018. "What kinds of comparison are most useful in the study of world philosophies." https://scholarworks.iu.edu/iupjournals/index.php/jwp/article/view/2156
- Škof, L. 2021. "The food, water, air and fire doctrines in ancient Indian and Greek philosophies." https://doi.org/10.4312/as.2021.9.3.303-320
- Stanley-Baker, M. 2022. "Qi 氣." https://doi.org/10.4324/9780203740262-4
- Steiner, R. C. 2015. *Disembodied Souls.* SBL Press. https://doi.org/10.15699/9781628370775
- Tjuka, A., Forkel, R., Rzymski, C. & List, J.-M. 2026. *CLICS⁴* (dataset). https://doi.org/10.5281/zenodo.16900179
- van Gassen, E. 2026. "Open but incompatible." https://arxiv.org/abs/2606.28867
- Vítek, T. 2025. "Psyche and the Pre-Socratics." https://doi.org/10.5507/aither.2025.002
- Yoeli-Tlalim, R. 2010. "Tibetan 'wind' and 'wind' illnesses." https://doi.org/10.1016/j.shpsc.2010.10.005
- Zhou, K., Ethayarajh, K. & Jurafsky, D. 2021. "Frequency-based distortions in contextualized word embeddings." https://arxiv.org/abs/2104.08465

**Cited from memory, not checked here** (standard works; check details and pages before
citing): Abusch 1998 ("Ghost and god"); Arbman 1926–27; Brashier 1996 (*Early China*);
Bremmer 1983 (*The Early Greek Concept of the Soul*); Evans-Pritchard 1956 (*Nuer Religion*);
Gyekye 1987; Haspelmath 2003 (semantic maps); Hultkrantz 1953; Johnson 1949/1964; Kemp &
Regier 2012; Kuriyama 1999 (*The Expressiveness of the Body*); Lloyd & Sivin 2002 (*The Way and
the Word*); López Austin 1980 (*Cuerpo humano e ideología*); Murdock 1949; Paulson 1958; Rubel,
O'Nell & Collado-Ardón 1984 (*Susto*); Slingerland 2019 (*Mind and Body in Early China*);
Steinert 2012; Vogt 1976; Warner 1937; Wierzbicka 2014 (*Imprisoned in English*); Wolff 1974;
Yü Ying-shih 1987 ("O soul, come back!").

**Data:**

- English, Chinese and Japanese Wiktionary (wiktextract dump, August 2025; CC BY-SA)
- Kinbank (CC BY 4.0)
- CLICS4 (CC BY 4.0)
- Globasa `word-list.csv`
- Doxo texts (`doxo-pages-grav`)

**Scripts** (in `concept_discovery/`):

- `kinbank_categories.py`
- `english_east_asian_borrowings.py`
- `indic_east_asian_concepts.py`
- `clics_soul_colexifications.py`
- `lexicon.py`
