# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import os
import sys
import csv
import re
from collections import defaultdict

import wget as wget

from WiktionaryPreprocess import split_tsv_by_second_column

languages = ['deu', 'nld', 'fra', 'rus', 'ara', 'cmn', 'jpn']

# languages = ['ang', 'enm']

wordnets = []

boolS = ['', 's']

if not os.path.exists("./iso-639-3.tab"):
    print("Downloading the ISO-639-3 names for language codes")
    wget.download("https://iso639-3.sil.org/sites/iso639-3/files/downloads/iso-639-3.tab", 'iso-639-3.tab')

with open("./iso-639-3.tab", 'r', newline='', encoding='utf-8') as infile:
    reader = csv.reader(infile, delimiter='\t')
    headers = next(reader, None)  # Read headers, if present
    languageNames = {}
    for sense_row in reader:
        languageNames.setdefault(sense_row[0], sense_row[6])

# languageNames = {'deu': 'German', 'nld': 'Dutch', 'fra': 'French', 'rus': 'Russian', 'cmn': 'Mandarin', 'jpn': 'Japanese',                 'jpn': 'Japanese'}

PoSDict = {"n": ['Noun'], "f": ['Verb'], "f.sah": ['Verb'], "b": ['Noun', 'Verb'], "t": ['Adjective', 'Adverb'],
           "s": ['Adjective'], "p jm": ['Adverb'],
           "m": ['Adverb'], "lfik": ['Prefix'], "xfik": ['Suffix'], "b xfik": ['Suffix'], "t xfik": ['Suffix'],
           "su n": ['Proper noun'], "su t": ['Adjective'], "il": ['Interjection'], "l": ['Conjunction'],
           "num": ['Number'], "p": ['Preposition'], "pn": ['Pronoun'], "d": ['Determiner']}

# This excludes senses
#blacklistDict = {("alokrasi", "revolution"): ["turning of an object around an axis",  "traversal of one body through an orbit around another body"]}

#whitelistDict = {("alokrasi", "revolution"): ["political upheaval", "removal and replacement of a government"]}

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


def getstuff(filename, english_word, query_sense, PoS):
    with open(filename, "rt") as csvfile:
        datareader = csv.reader(csvfile, delimiter='\t')
        # yield next(datareader)  # yield the header row
        count = 0
        match = False
        langDict = {}
        for lang in languages:
            langDict[lang] = set()
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
                    yieldOutput = [[english_word], [PoS], [old_sense]]
                    for lang in languages:
                        yieldOutput += [langDict[lang]]
                    yield yieldOutput
                match = False
                englishMatched = False
                for lang in languages:
                    langDict[lang] = set()

            if re.sub('/translations$', '', row[1]) == english_word and row[2] == PoS:
                englishMatched = True
                count += 1
                if row[5] in languages:
                    langDict[row[5]].add(row[6])

                if query_sense == sense:
                    match = True

            elif count >= 1:
                # done when having read a consecutive series of rows
                return



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

startPrefix = input("Lexi ingay na xoru har keto fe xoru? / What should the word begin with at the start?\nAm sol presyon 'enter' na xoru xorfe xoru. / Just hit enter to start from the beginning.\n")


with open("./" + menalari_name, newline='') as menalari_file, open('menalariExtensions.tsv', 'w', newline='') as menaExp:
    menaWriter = csv.writer(menaExp, delimiter='\t', lineterminator='\n')


    menaWriter.writerow(['Globasa'] + ['Parts of Speech'] + ['English by Sense'] + [languageNames[lang] for lang in languages])

    outputGlosses = [[set()] for lang in languages]
    PoSs = []

    started = False
    engSenseDict = [{}]



    menalariReader = csv.reader(menalari_file, delimiter=',', quotechar='"')
    next(menalariReader, None)

    started = False

    for row in menalariReader:
        if not started:
            if row[0].startswith(startPrefix):
                started = True
            else:
                continue
        globasa_query = row[0]
        output = [globasa_query]
        first = True
        match = False
        globasaMatch = False
        PoS = ''
        globasaWord = ''

        with open(sensesPath, newline='') as perSense:
            senseReader = csv.reader(perSense, delimiter='\t', quotechar='"')
            next(senseReader, None)
            for sense_row in senseReader:
                if not globasaMatch and sense_row[0] == globasa_query:
                    globasaMatch = True
                if globasaMatch:
                    if sense_row[0] != globasaWord and match:
                        engSenseOutput = '; '.join([', '.join(
                            [word + " [" + "|".join(engSenseDictPart[word]) + "]" for word in engSenseDictPart.keys()]) for
                            engSenseDictPart in engSenseDict])
                        output += ["; ".join(PoSs)] + [engSenseOutput] + [
                            "; ".join([", ".join(entry) for entry in outputGloss]) for outputGloss in outputGlosses]
                    elif sense_row[0] == globasaWord and PoS != sense_row[2]:
                        PoSs += [sense_row[2]]
                        for i in range(len(outputGlosses)):
                            outputGlosses[i] += [set()]
                        engSenseDict += [{}]
                    if len(sense_row) < 6:
                        continue
                    if sense_row[0] != globasaWord:
                        outputGlosses = [[set()] for lang in languages]
                        PoSs = [sense_row[2]]
                        engSenseDict = [{}]

                    if sense_row[0] != globasa_query:
                        globasaMatch = False
                        match = False
                        break


                    first = False
                    globasaWord = sense_row[0]

                    if sense_row[4] == 's' and sense_row[5] == 'v':
                        match = True


                    for query_row in getstuff(path, englishWord, sense, PoS):
                        if query_row[0][0] in engSenseDict:
                            engSenseDict[-1][query_row[0][0]] |= set(query_row[2])
                        else:
                            engSenseDict[-1].setdefault(query_row[0][0], set(query_row[2]))
                        for i, translations in enumerate(query_row[3:]):
                            outputGlosses[i][-1] |= translations

        print(output)
        menaWriter.writerow(output)


    output = [globasaWord] + ["; ".join(PoSs)] + ["; ".join([", ".join(entry) for entry in outputGloss]) for outputGloss
                                                  in outputGlosses]
    print(output)
    menaWriter.writerow(output)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
