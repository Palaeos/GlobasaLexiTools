# GlobasaTools

This repository contains various Python scripts that automate various Globasa related tasks.

- [`dictionaryPreprocess.py`](dictionaryPreprocess.py) - Scrapes the Globasa wordlist to either generate monolingual or bilingual dictionary entries for Apertium
  
- [`Word selection automator.py`](Word%20selection%20automator.py) - asks for an English word, then part of speech and finally the intended sense to scrape a Wiktionary dump to automatically generate a lexiseleti complete with Globasa renditions of the phonetics.
  - [`GlobasaTransliterators.py`](GlobasaTransliterators.py) - is used to convert official romanizations and Latin spellings into Globasa rendition of the phonetics
- [`Wordnet based translation extender.py`](Wordnet%20based%20translation%20extender.py) (WIP) - is intended to look up a list of Globasa words with corresponding CILIs and then query the synonym sets for some languages to query translations for the word. 
