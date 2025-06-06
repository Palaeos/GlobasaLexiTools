# GlobasaTools

This repository contains various Python scripts that automate various Globasa related tasks.

- [`dictionaryPreprocess.py`](dictionaryPreprocess.py) - Scrapes the Globasa wordlist to either generate monolingual or bilingual dictionary entries for Apertium
## Anki
- [`AnkiMaker.py`](AnkiMaker.py) - takes in a frequency sorted wordlist and [the official wordlist](https://cdn.globasa.net/api2/word-list.csv) to generate an Anki deck for content words
## Wiktionary
- [`WiktionaryPreprocess.py`](WiktionaryPreprocess.py) - Takes an English Wiktionary dump and breaks it up into different subfiles based on the first two characters of the English word to accelerate searches
- [`Wiktionary senseKey preprocess.py`](Wiktionary%20senseKey%20preprocess.py) - Scrapes the English Wiktionary dump and adds senses from the translation of a given English word if the Spanish gloss is found as a translation for that word. A table of English word - part of speech - sense tuples is the output for further manual vetting
- [`Wordnet based translation extender.py`](Wordnet%20based%20translation%20extender.py) - Uses the tuples from the preprocess to query the Wiktionary dump for Globasa translations in further languages beyond English, Spanish and Esperanto
- [`Word selection automator.py`](Word%20selection%20automator.py) - asks for an English word, then part of speech and finally the intended sense to scrape a Wiktionary dump to automatically generate a lexiseleti complete with Globasa renditions of the phonetics. **Requires**: [`cutlet`](https://github.com/polm/cutlet) for Japanese romanization, [`korean_romanizer`](https://github.com/osori/korean-romanizer) for Korean romanization
  - [`GlobasaTransliterators.py`](GlobasaTransliterators.py) - is used to convert official romanizations and Latin spellings into Globasa renditions of the phonetics

## Wordnet
[`wn`](https://github.com/goodmami/wn) is required for following
- [`MenalariWordNetAligner.py`](MenalariWordNetAligner.py) - uses English and Spanish wordnets to find [Collaborative Interlingual Indicies (CILI)](https://compling.upol.cz/omw/ili) for Globasa words. The output is a table that can be edited to vet the CILIs. (analog of [`Wiktionary senseKey preprocess.py`](Wiktionary%20senseKey%20preprocess.py) for wordnets)
- [`Wordnet based translation extender.py`](Wordnet%20based%20translation%20extender.py) (WIP) - is intended to look up a list of Globasa words with corresponding CILIs and then query the synonym sets for some languages to query translations for the word. (analog of [`Wordnet based translation extender.py`](Wordnet%20based%20translation%20extender.py) for wordnets)

### TODO
- Add Esperanto support in `MenalariWordNetAligner.py` via OMWN [Esperanto IDs](https://github.com/omwn/omw-data/blob/main/wns/wikt/wn-wikt-epo.tab). Due to Esperato being less prone to polysemy, CILIs could be considered automatiocally applicable if attested by Esperanto. (DONE)
- Complete `Wordnet based translation extender.py`. The main challenge here is to collect the translations for each word sense and then assemble them into the wordlist format with `;` separation.

## Needed Data

- [Globasa Wordlist TSV](https://cdn.globasa.net/api2/word-list.tsv)
- Wiktionary translation dump made with the [Yawipa Parser](https://github.com/wswu/yawipa). Originally using premade [dumps](https://cs.jhu.edu/~winston/yawipa-data.html) (Dead link)
