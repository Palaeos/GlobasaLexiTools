# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import os
import sys
import csv
import re
import wn
from collections import defaultdict

import wget as wget

from WiktionaryPreprocess import split_tsv_by_second_column

languages = ['deu', 'nld', 'fra', 'rus', 'ara', 'cmn', 'jpn']

# languages = ['ang', 'enm']

wordnets = {'deu': wn.Wordnet('odenet:1.4'), 'nld': wn.Wordnet('omw-nl:1.4'), 'fra': wn.Wordnet('omw-fr:1.4')}
#languageNames = {'deu': wn.Wordnet('odenet:1.4'), 'nld': 'Dutch', 'fra': 'French', 'rus': 'Russian', 'cmn': 'Mandarin', 'jpn': 'Japanese'}

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

# languageNames = {'deu': 'German', 'nld': 'Dutch', 'fra': 'French', 'rus': 'Russian', 'cmn': 'Mandarin', 'jpn': 'Japanese'}

PoSDict = {"n": ['Noun'], "f": ['Verb'], "f.sah": ['Verb'], "b": ['Noun', 'Verb'], "t": ['Adjective', 'Adverb'],
           "s": ['Adjective'], "p jm": ['Adverb'],
           "m": ['Adverb'], "lfik": ['Prefix'], "xfik": ['Suffix'], "b xfik": ['Suffix'], "t xfik": ['Suffix'],
           "su n": ['Proper noun'], "su t": ['Adjective'], "il": ['Interjection'], "l": ['Conjunction'],
           "num": ['Number'], "p": ['Preposition'], "pn": ['Pronoun'], "d": ['Determiner']}

maxInt = sys.maxsize

while True:
    # decrease the maxInt value by factor 10
    # as long as the OverflowError occurs.

    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt / 10)



def entryToString(entry):
    output = ""
    if entry[0]:
        output = ", ".join(entry[0])

    for i in entry[1:]:
        if i:
            output += "; " + ", ".join(i)

    return output


# morpho = input("Duabasali or morfoli? / Bilingual or morphological?\n")


menalari_name = "word-list.csv"
if not os.path.exists("./word-list.csv"):
    print("Downloading the Globasa word-list")
    wget.download("https://cdn.globasa.net/api2/word-list.csv", menalari_name)

startPrefix = input("Lexi ingay na xoru har keto fe xoru? / What should the word begin with at the start?\nAm sol presyon 'enter' na xoru xorfe xoru. / Just hit enter to start from the beginning.\n")

sensesPath = "./GLB_ENG_WordnetSynsets.tsv"
with open("./" + menalari_name, newline='') as menalari_file, open('menalariExtensions.tsv', 'w', newline='') as menaExp:
    menaWriter = csv.writer(menaExp, delimiter='\t', lineterminator='\n')


    menaWriter.writerow(['Globasa'] + ['Parts of Speech'] + ['English by Sense'] + [languageNames[lang] for lang in wordnets])

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
                        CILI_output = '; '.join([', '.join(
                            engSenseDictPart)
                            for
                            engSenseDictPart in engSenseDict])
                        output += ["; ".join(PoSs)] + [CILI_output] + [
                            "; ".join([", ".join(entry) for entry in outputGloss]) for outputGloss in outputGlosses]
                    elif sense_row[0] == globasaWord and PoS != sense_row[2]:
                        PoSs += [sense_row[2]]
                        for i in range(len(outputGlosses)):
                            outputGlosses[i] += [set()]
                        engSenseDict += [set()]
                    if len(sense_row) < 6:
                        continue
                    if sense_row[0] != globasaWord:
                        outputGlosses = [[set()] for wordnet in wordnets]
                        PoSs = [sense_row[2]]
                        engSenseDict = [set()]

                    if sense_row[0] != globasa_query:
                        globasaMatch = False
                        match = False
                        break


                    first = False
                    globasaWord = sense_row[0]
                    ILI = sense_row[1]
                    PoS = sense_row[2]

                    if sense_row[4] == 's' and sense_row[5] == 'v':
                        match = True
                        engSenseDict[-1] |= set([ILI])
                        for i, lang in enumerate(wordnets):
                            for synset in wordnets[lang].synsets(ili=ILI):
                                outputGlosses[i][-1] |= set(synset.lemmas())

        print(output)
        menaWriter.writerow(output)

    output = [globasaWord] + ["; ".join(PoSs)] + ["; ".join([", ".join(entry) for entry in outputGloss]) for outputGloss
                                                  in outputGlosses]
    print(output)
    menaWriter.writerow(output)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
