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

languages = ['deu', 'nld', 'fra', 'rus', 'cmn', 'jpn']

# languages = ['ang', 'enm']

boolS = ['', 's']

if not os.path.exists("./iso-639-3.tab"):
    print("Downloading the ISO-639-3 names for language codes")
    wget.download("https://iso639-3.sil.org/sites/iso639-3/files/downloads/iso-639-3.tab", 'iso-639-3.tab')

with open("./iso-639-3.tab", 'r', newline='', encoding='utf-8') as infile:
    reader = csv.reader(infile, delimiter='\t')
    headers = next(reader, None)  # Read headers, if present
    languageNames = {}
    for row in reader:
        languageNames.setdefault(row[0], row[6])

# languageNames = {'deu': 'German', 'nld': 'Dutch', 'fra': 'French', 'rus': 'Russian', 'cmn': 'Mandarin', 'jpn': 'Japanese',                 'jpn': 'Japanese'}

PoSDict = {"n": ['Noun'], "f": ['Verb'], "f.sah": ['Verb'], "b": ['Noun', 'Verb'], "t": ['Adjective', 'Adverb'],
           "s": ['Adjective'], "p jm": ['Adverb'],
           "m": ['Adverb'], "lfik": ['Prefix'], "xfik": ['Suffix'], "b xfik": ['Suffix'], "t xfik": ['Suffix'],
           "su n": ['Proper noun'], "su t": ['Adjective'], "il": ['Interjection'], "l": ['Conjunction'],
           "num": ['Number'], "p": ['Preposition'], "pn": ['Pronoun'], "d": ['Determiner']}

# This excludes senses
blacklistDict = {("alokrasi", "revolution"): ["turning of an object around an axis",
                                              "traversal of one body through an orbit around another body"]}

whitelistDict = {("alokrasi", "revolution"): ["political upheaval", "removal and replacement of a government"]}

senseKeyPath = "./GLB_ENG_WiktionarySenses.tsv"
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

def retrieveMarking(senseKeyPath, globasaWord, englishGloss, PoS, englishSense):
    if os.path.exists(senseKeyPath):
        with open(senseKeyPath, newline='') as senseQuery:
            senseReader = csv.reader(senseQuery, delimiter='\t', quotechar='"')
            next(senseReader, None)
            for row in senseReader:
                if row[0] == globasaWord and row[1] == englishGloss and row[2] == PoS and row[3] == englishSense:
                    if row[5] == 'v':
                        return row[4], row[5]
                    else:
                        return None
            return None
    else:
        return None

def getstuff(filename, globasa_word, english_word, spanish_words, esperanto_words, PoS):
    with open(filename, "rt") as csvfile:
        datareader = csv.reader(csvfile, delimiter='\t')
        # yield next(datareader)  # yield the header row
        count = 0
        spaMatch = False
        epoMatch = False
        spaFound = False
        epoFound = False
        match = False
        langDict = {}
        for lang in languages:
            langDict[lang] = set()
        sense = ""
        wordEng = ""
        wkPoS = ""
        englishMatched = False
        spaSect = set()
        epoSect = set()
        for row in datareader:
            old_sense = sense
            sense = row[4]
            previous_wordEng = wordEng
            wordEng = row[1]
            previous_wkPoS = wkPoS
            wkPoS = row[2]

            if sense != old_sense or previous_wordEng != wordEng or previous_wkPoS != wkPoS:
                if englishMatched:
                    spaOutput = ", ".join(spaSect.intersection(set(spanish_words)))
                    spaDiff = spaSect.difference(set(spanish_words))
                    if spaDiff:
                        spaOutput += " /" + ", ".join(spaDiff) + "/"
                    epoOutput = ", ".join(epoSect.intersection(set(esperanto_words)))
                    epoDiff = epoSect.difference(set(esperanto_words))
                    if epoDiff:
                        epoOutput += " /" +  ", ".join(epoDiff) + "/"
                    match = (((spaMatch and spaFound) or (not spaFound)) and ((epoMatch and epoFound) or (not epoFound)) and (spaFound or epoFound))
                    if markingQuery:
                        yieldOutput = [[english_word], [PoS], [old_sense], [markingQuery[0]], [markingQuery[1]], [spaOutput],
                                       [epoOutput]]
                    else:
                        yieldOutput = [[english_word], [PoS], [old_sense], [boolS[match]], [''], [spaOutput],
                                   [epoOutput]]
                    for lang in languages:
                        yieldOutput += [langDict[lang]]
                    yield yieldOutput
                spaMatch = False
                epoMatch = False
                spaFound = False
                epoFound = False
                englishMatched = False
                for lang in languages:
                    langDict[lang] = set()
                spaSect = set()
                epoSect = set()

            markingQuery = retrieveMarking(senseKeyPath, globasa_word, english_word, PoS, old_sense)
            if (re.sub('/translations$', '', row[1]) == english_word and row[2] == PoS) or markingQuery:
                englishMatched = True
                count += 1
                if row[5] in languages:
                    langDict[row[5]].add(row[6])

                if (globasa_word, english_word) in whitelistDict:
                    if sense in whitelistDict[(globasa_word, english_word)]:
                        match = True
                else:
                    if row[5] == 'spa':
                        spaFound = True
                        spaSect.add(row[6])
                        if row[6] in spanish_words:
                            spaMatch = True
                    if row[5] == 'epo':
                        epoFound = True
                        epoSect.add(row[6])
                        if row[6] in esperanto_words:
                            epoMatch = True

            elif count >= 1:
                # done when having read a consecutive series of rows
                return
        yield [english_word, PoS]

def getdata(filename, globasa_word, criteria, PoS):
    for englishWords in criteria[0]:
        englishWord = englishWords.strip()
        if englishWord.startswith("_"):
            yield [englishWord, PoS]
            continue
        path = "./Wiktionary_dump/single_char.tsv"
        if len(englishWord) >= 2:
            firstTwo = englishWord[:2].upper()
            if not ("/" in firstTwo or "\\" in firstTwo):
                path = f"./Wiktionary_dump/{firstTwo}.tsv"

        if not os.path.exists(path):
            yield [englishWord, PoS]
            continue
        for row in getstuff(path, globasa_word, englishWord, criteria[1], criteria[2], PoS):
            yield row


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

startPrefix = input("Lexi ingay na xoru har keto fe xoru? / What should the word begin with at the start?\nAm sol presyon 'enter' na xoru xorfe xoru. / Just hit enter to start from the beginning.\n")


with open("./" + menalari_name, newline='') as menalari_file, open('GLB_ENG_WiktionarySenses_initial.tsv', 'w',
                                                            newline='') as perSense, open('menalariExtension.tsv', 'w',
                                                                                          newline='') as menaExp:
    writer = csv.writer(perSense, delimiter='\t', lineterminator='\n')
    menaWriter = csv.writer(menaExp, delimiter='\t', lineterminator='\n')

    writer.writerow(
         ['Glb'] + ['Eng'] + ['Prt of Sp'] + ['Wiktionary Sense (in Translations)'] + ['App?'] + ['Vetted?'] + ['Spa'] + ['Epo'] + [
            languageNames[lang] for lang in languages])
    menaWriter.writerow(['Globasa'] + ['Eng with Senses'] + [languageNames[lang] for lang in languages])

    menalariReader = csv.reader(menalari_file, delimiter=',', quotechar='"')
    next(menalariReader, None)

    started = False

    for row in menalariReader:
        if not started:
            if row[0].startswith(startPrefix):
                started = True
            else:
                continue
        englishGlosses = re.sub("\(_.*?_\)", "", row[5]).strip().split("; ")
        spanishGlosses = re.sub("\(_.*?_\)", "", row[8]).strip().split("; ")
        esperantoGlosses = re.sub("\(_.*?_\)", "", row[7]).strip().split("; ")
        PoSs = row[2].split("; ")
        PoSlist = []
        PoSinDict = True
        for part in PoSs:
            PoSKey = None
            if part.startswith("b."):
                PoSKey = "b"
            else:
                PoSKey = part
            if PoSKey in PoSDict:
                PoSlist += PoSDict[PoSKey]
            else:
                PoSinDict = False
        outputGlosses = [[set() for j in range(len(PoSlist))] for i in range(len(languages))]

        if PoSinDict:
            output = None
            for i, gloss in enumerate(zip(englishGlosses, spanishGlosses, esperantoGlosses)):
                p = [gloss[0].split(", "), gloss[1].split(", "), gloss[2].split(", ")]
                engSenseDict = {}

                for query_row in getdata(wiktionary_dump_path, row[0], p, PoSlist[i]):
                    # print(query_row)
                    if len(query_row) == 2:
                        output = [row[0]] + query_row
                        print("\t".join(output))
                        writer.writerow(output)
                        continue
                    line = ""
                    if query_row[0][0] in engSenseDict:
                        engSenseDict[query_row[0][0]] |= set(query_row[2])
                    else:
                        engSenseDict.setdefault(query_row[0][0], set(query_row[2]))

                    for j, entry in enumerate(query_row):
                        if j >= 6 and query_row[3] == 's':
                            outputGlosses[j - 4][i] |= entry

                    output = [row[0]] + [", ".join(entry) for entry in query_row]

                    print("\t".join(output))
                    writer.writerow(output)

            engSenseOutput = ', '.join(
                [word + " [" + "|".join(engSenseDict[word]) + "]" for word in engSenseDict.keys()])

            menaWriter.writerow([row[0]] + [engSenseOutput] + [entryToString(entry) for entry in outputGlosses])
            # ["[" + '|'.join(outputGlosses[0]) ]
        else:
            print(row[0])
            menaWriter.writerow([row[0]])
            writer.writerow([row[0]])
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
