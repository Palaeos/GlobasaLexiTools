# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import os
import sys
import csv
import re
import cutlet
import GlobasaTransliterators as gbTr
from korean_romanizer.romanizer import Romanizer
from transliterate import translit

import wget as wget

from WiktionaryPreprocess import split_tsv_by_second_column

languages = ['eng', 'spa', 'fra', 'rus', 'deu', 'ind', 'tgl', 'hin', 'tel', 'ara', 'swa', 'fas', 'tur', 'cmn', 'kor', 'jpn', 'vie']


if not os.path.exists("./iso-639-3.tab"):
    print("Downloading the ISO-639-3 names for language codes")
    wget.download("https://iso639-3.sil.org/sites/iso639-3/files/downloads/iso-639-3.tab", 'iso-639-3.tab')

with open("./iso-639-3.tab", 'r', newline='', encoding='utf-8') as infile:
    reader = csv.reader(infile, delimiter='\t')
    headers = next(reader, None)  # Read headers, if present
    languageNames = {}
    for sense_row in reader:
        languageNames.setdefault(sense_row[0], sense_row[6])

maxInt = sys.maxsize

while True:
    # decrease the maxInt value by factor 10
    # as long as the OverflowError occurs.

    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt / 10)

import itertools

import pandas as pd

def getdata(english_word, query_sense, PoS):
    englishWord = english_word.strip()
    if englishWord.startswith("_"):
        return [englishWord, PoS]
    path = "./Wiktionary_dump/single_char.tsv"
    if len(englishWord) >= 2:
        firstTwo = englishWord[:2].upper()
        if not ("/" in firstTwo or "\\" in firstTwo):
            path = f"./Wiktionary_dump/{firstTwo}.tsv"

    if not os.path.exists(path):
        return [englishWord, PoS]
    return getstuff(path, englishWord, query_sense, PoS)


def getstuff(filename, english_word, query_sense, PoS):
    with open(filename, "rt") as csvfile:
        datareader = csv.reader(csvfile, delimiter='\t')
        # yield next(datareader)  # yield the header row
        count = 0
        match = False
        langDict = {}
        for lang in languages:
            langDict[lang] = set()
        translitDict = {}
        for lang in languages:
            translitDict[lang] = set()
        sense = ""
        wordEng = ""
        wkPoS = ""
        englishMatched = False
        for row in datareader:
            old_sense = sense
            sense = row[4]
            previous_wordEng = wordEng
            wordEng = row[1]
            previous_wkPoS = wkPoS
            wkPoS = row[2]
            if sense != old_sense or previous_wordEng != wordEng or previous_wkPoS != wkPoS:
                if englishMatched and match:
                    langDict["eng"].add(english_word)

                    return langDict, translitDict
                match = False
                englishMatched = False
                for lang in languages:
                    langDict[lang] = set()

            if re.sub('/translations$', '', row[1]) == english_word and row[2] == PoS:
                englishMatched = True
                count += 1
                if row[5] in languages:
                    langDict[row[5]].add(row[6])

                    if len(row) >= 8 and row[5] == "tel":
                        translitDict[row[5]].add(row[7].split("=")[-1])
                    if len(row) >= 8 and row[5] == "cmn":
                        translitDict[row[5]].add(row[7].split("=")[-1])
                    #if len(row) >= 8 and row[5] == "jpn":
                    #    translitDict[row[5]].add(row[7].split("=")[-1])
                    if len(row) >= 8 and row[5] == "kor":
                        translitDict[row[5]].add(row[7].split("=")[-1])
                    if len(row) >= 8 and row[5] == "fas":
                        translitDict[row[5]].add(row[7].split("=")[-1])
                    if len(row) >= 9 and row[5] == "rus":
                        translitDict[row[5]].add(row[8].split("=")[-1])
                    if len(row) >= 9 and row[5] == "hin":
                        translitDict[row[5]].add(row[8].split("=")[-1])

                if query_sense == sense:
                    match = True

            elif count >= 1:
                # done when having read a consecutive series of rows
                return
        return langDict, translitDict

def entryToString(entry):
    output = ""
    if entry[0]:
        output = ", ".join(entry[0])

    for i in entry[1:]:
        if i:
            output += "; " + ", ".join(i)

    return output


# morpho = input("Duabasali or morfoli? / Bilingual or morphological?\n")

# Example usage
wiktionary_dump_path = './tr_sorted'

if not os.path.isdir("./Wiktionary_dump/"):
    print("Downloading the Wiktionary dump")
    wget.download("https://www.cs.jhu.edu/~winston/yawipa-data/tr", 'tr')
    split_tsv_by_second_column('tr')

menalari_name = "word-list.csv"
if not os.path.exists("./word-list.csv"):
    print("Downloading the Globasa word-list")
    wget.download("https://cdn.globasa.net/api2/word-list.csv", menalari_name)

#sensesPath = "./GLB_ENG_Wiktionary_Senses.tsv"
sensesPath = "./GLB_ENG_WiktionarySenses.tsv"
if not os.path.exists(sensesPath):
    print("Fe lutuf, funsyon \" Wiktionary translation expander.py\" xorfe hinto. Xafe hinto, am rinamegi explasi cel \"./GLB_ENG_Wiktionary_Senses.tsv\" ")

"Yahweh\tProper noun\tpersonal name of God"



#english_word, PoS,  query_sense = "yaksha	Noun	(Buddhism) a kind of supernatural being".split("\t")

    #"yaksha	Noun	(Buddhism) a kind of supernatural being".split("\t")

    #"yak	Noun	ox-like mammal".split("\t")
#"Yahweh\tProper noun\tpersonal name of God".split("\t")\
                                  #"Mark\tProper noun\tmale given name".split("\t")
english_word = input("English word: ")
PoS = input("Part of Speech: ")

query_sense = input("Wiktionary sense: ")

# edge	Noun	in graph theory: any of the pairs of vertices in a graph

outputGlosses = [set() for i in range(len(languages))]
globasaized = [set() for i in range(len(languages))]

outputGlosses[0] |= set([english_word])

basaName = ['Englisa', 'Espanisa', 'Fransesa', 'Rusisa', 'Doycesa', 'Indonesisa', 'Pilipinasa', 'Hindisa', 'Telugusa', 'Arabisa', 'Swahilisa', 'Parsisa', 'Turkisa', 'Putunhwa', 'Hangusa', 'Niponsa', 'Vyetnamsa']


langDict, translitDict = getdata(english_word, query_sense, PoS)

#Test with "Mark	Proper noun	male given name"


print("Ewropali (Tongo to sen un famil.): ")

katsu = cutlet.Cutlet('hepburn', use_foreign_spelling=False)

for i, lang in enumerate(languages):
    words = "?"
    if langDict[lang]:
        glosses = set()
        if translitDict[lang]:
            for word, translit in zip(langDict[lang], translitDict[lang]):
                gloss = word
                if translit:
                    if lang == "cmn":
                        translit = gbTr.pinyinToGlobasa(translit)
                    if lang == "rus":
                        translit = gbTr.russianToGlobasa(translit)
                    if lang == "jpn":
                        translit += " \"" + gbTr.hepburnToGlobasa(translit) + "\""
                    if lang == "kor":
                        translit += " \"" + gbTr.koreanToGlobasa(translit) + "\""
                    gloss += " \"" + translit + "\""

                glosses.add(gloss)
        else:
            for word in langDict[lang]:
                gloss = word

                if lang == "eng":
                    gloss += " \"" + gbTr.englishToGlobasa(word) + "\""

                if lang == "fra":
                    gloss += " \"" + gbTr.frenchToGlobasa(word) + "\""

                if lang == "deu":
                    gloss += " \"" + gbTr.germanToGlobasa(word) + "\""
                if lang == "tur":
                    gloss += " \"" + gbTr.turkishToGlobasa(word) + "\""
                if lang == "vie":
                    gloss += " \"" + gbTr.vietnameseToGlobasa(word) + "\""

                if lang == "jpn":
                    gloss += " \"" + gbTr.hepburnToGlobasa(str(katsu.romaji(word))) + "\""
                if lang == "kor":
                    gloss += " \"" + gbTr.koreanToGlobasa(Romanizer(word).romanize()) + "\""
                if lang == "rus":
                    gloss += " \"" + gbTr.russianToGlobasa(translit(word, 'ru', reversed=True)) + "\""
                glosses.add(gloss)

        words = ", ".join(glosses)
    line = "    * " + basaName[i] + " (" + words + ")"
    print(line)
    if i == 4:
        print("Awstronesili (Tongo to sen un famil.): ")
    if i == 6:
        print("Alo (Moyun to sen un famil.): ")



# See PyCharm help at https://www.jetbrains.com/help/pycharm/
