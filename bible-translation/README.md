# Bible translation: Globasa side

The Globasa-specific part of the Hebrew/Greek → Globasa translation.

## Interface to the Hebrew/Greek project

The source side lives at
`~/Nextcloud/Documents/Language/Code/Bible translation`. Point `SRC` at it:

```sh
SRC="$HOME/Nextcloud/Documents/Language/Code/Bible translation"
```

| Source-side output | Used for |
|---|---|
| `"$SRC/bin/passage" REF [--anchors --ambiguity-report FILE]` | pre-tagged Apertium stream (apertium-hbo tags, readings ordered by parsimony, syntax labels, `<id:N>` word anchors) |
| `"$SRC/tools/build_lexicon.py" REF` → `"$SRC/data/lexicon/<REF>.tsv"` | per-lemma SDBH sense (chosen by passage), en/es/fr glosses, BDB, Klein, flags |

## Genesis 1 sample

```sh
python3 "$SRC/tools/build_lexicon.py" "Gen 1"
python3 build_glb_candidates.py "$SRC/data/lexicon/Gen_1.tsv"     # -> data/Gen_1_glb.tsv
"$SRC/bin/passage" "Gen 1" --anchors --ambiguity-report data/Gen_1_ambiguity.tsv > data/Gen_1.hbo.txt
```

`data/Gen_1_lemmas_reconstructed.tsv` stands in for `$SRC/data/lexicon/Gen_1.tsv`
(the source project was not reachable on 2026-11-12). `reconstruct_lemma_table.py`
takes the Strong's numbers, English senses, BDB/Klein and flags from an
earlier `*_glb.tsv` and looks the same SDBH sense (LEXID) up in the other
editions: `main_es`, `main_fr`, `main_zh` (zh-hans + zh-hant merged), `pos`.
`curated` holds only the בָּרָא reading. Regenerate from the real table when
the source side is available, and have `build_lexicon.py` emit `main_zh`.

SDBH editions: en/es/fr in `Warehouse2/Language/Bible translation/hbo-grc/sources/ubs/`;
zh-hans/zh-hant (from [ubs-open-license](https://github.com/ubsicap/ubs-open-license),
v0.9.4, CC BY-SA) in `bible-translation/sources/ubs/` (gitignored; Claude
could not write to Warehouse2; move them there). Portuguese is also published.

Inputs (defaults, in the repo root):

- `word-list.csv`: the current word list (PoS-labelled cells,
  `n: water; v.tr: irrigate`); the old unlabelled TSV also works.
- `menalariExtension.tsv`: the Wiktionary extension ("Wiktionary extension
  builder.py"), vetted Wiktionary senses with translations. Used columns:
  English, Spanish, French, Mandarin, and Hebrew. `--extension ""` disables it.

How a candidate is reached, e.g. `geo(en+es+fr+he*)`:

| Tag | Meaning |
|---|---|
| `en` `es` `fr` | the SDBH gloss in that language matches the word's gloss |
| `zh` | the same for Chinese (word list `TranslationZho`, extension `Mandarin`). Counts toward "glosses agree" but otherwise only breaks ties: Chinese covers about half the words, unevenly per PoS, so ranking by it rewards coverage (`danyam` "grain" beat `bija` "seed" for זרע) |
| `he` | the Biblical lemma's consonants match the extension's Hebrew column. That column is **Modern Hebrew**: it only corroborates (breaks ties) and proposes candidates only when no SDBH gloss matches, labelled "Modern Hebrew homograph … check the sense" (את → `yu` "you", קרא → `doxo` "read") |
| `*` | reached only through the Wiktionary extension |
| `~` | inexact: plural stripped, phrase head (`dry ground` → `ground`), or Hebrew plene/defective spelling (אלהים ~ אלוהים) |

Ranking: tier (≥ 2 of en/es/fr/zh agree, one, none), common words before
proper names, PoS fit (word list labels vs SDBH: זכר adj → `man`, נקבה noun →
`femyen`), affixes last, en/es/fr reached, Modern Hebrew support, earliest
SDBH gloss in en/es/fr, Chinese support, word list before Wiktionary, the
gloss as the word's primary meaning, shorter word, alphabetical. The order is
deterministic. (English gloss order alone lets homonyms win: "heaven" →
`janatu` "paradise".)

Gen 1 results (96 lemmas):

| how | lemmas |
|---|---|
| glosses agree (≥ 2 of en/es/fr/zh) | 77, of which 26 corroborated by Modern Hebrew; Chinese reaches a candidate in 45 lemmas |
| one language only | 5 |
| Modern Hebrew only (no SDBH gloss, or none matched) | 10: את, על, חי, טוב, כי, אל, גדול, מאד, חשׁך, שׁרץ |
| nothing | 4: כל, הנה, מקוה, קטן |

The earlier word-list-only run (Dec 2024 list, en+es) had 67 / 8 / 21 none.

## Files

- `build_glb_candidates.py`: Globasa candidates from a lemma table.
- `reconstruct_lemma_table.py`: stand-in lemma table from SDBH JSON.
- `rendering.md`: how Hebrew constructions are rendered in Globasa.
- `data/`: generated tables (bulk data → `Warehouse2/Language/Bible translation/globasa/`).

## apertium-hbo-glb

`apertium-hbo-glb/`: a Hebrew → Globasa Apertium pair, modelled on
`apertium-glb-eng` (installed copy: `/usr/local/old-apertium-2024/share/apertium/`).

- `curated/bidix.tsv`: the bilingual list, the source of truth (one default
  per Hebrew lemma + PoS, alternatives and basis per row).
- `make_bidix.py`: TSV → `apertium-hbo-glb.hbo-glb.dix`; Globasa tags
  (noun gender) come from the apertium-glb analyser.
- `apertium-hbo-glb.hbo-glb.rtx`: transfer rules implementing `rendering.md`
  (tag patterns are adjacent: `v.*.consec`; no clause rule may start with NP).
- `prep_stream.py`: first reading, NFC, drops article/maqaf/את and the
  verse-initial *wa*, retags wayyiqtol (`wayy`) and jussive.
- `translate.sh [STREAM]`: prep → pretransfer → bidix → rtx → apertium-glb
  generator → `postformat.py`. Unknown-to-generator words go to stderr.

Gen 1: machine output `data/Gen_1_glb_machine.txt`; revised draft with the
basis of every change `data/Gen_1_glb_draft.md`.

## Next

0. **TMX output:** `translate.sh` should write a TMX file (one `<tu>` per
   verse: Hebrew source + Globasa machine draft, later the revised draft),
   like the Doxo TMX files in the repo root.
1. **Syntax-based transfer:** merge UD PTNK roles (nsubj, obj, obl, mark)
   and BHSA phrase functions / clause types into the stream by word id;
   rewrite the rtx clause rules on roles; map BHSA clause types to the *wa*
   table in `rendering.md`; compare Gen 1 with `data/Gen_1_glb_draft.md`.

1. **Portuguese:** SDBH publishes it (pt JSON) and the extension has a
   Portuguese column; the word list has none.
2. **Greek:** the extension's Ancient Greek column can do for the NT what
   the Hebrew column does here, and it is the right period.
3. **The pair:** an `apertium-hbo-glb` pair. Bilingual dictionary from
   `*_glb.tsv`; transfer rules from `rendering.md`; generation through the
   installed `apertium-glb`.
