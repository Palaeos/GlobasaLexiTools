import json
import os
import sys
import csv
import re
from collections import defaultdict

import wget as wget

from wiktionary_db import WiktionaryDB, Translation

db = WiktionaryDB(readonly=True)

#from WiktionaryPreprocess import split_tsv_by_second_column

#languages = ['deu', 'nld', 'fra', 'rus', 'cmn', 'jpn']
#langCodes = ['de', 'nl', 'fr', 'it', 'ru', 'yi', 'he', 'ar', 'cmn', 'ja']
langCodes = ['de', 'nl', 'ang', 'grc', 'la', 'fr', 'it', 'ru', 'yi', 'he', 'ar', 'cmn', 'ja', 'tr', 'tt']

with open("language-codes ISO 639-2.json", 'r', encoding='utf-8') as file:
    twoLetterCodes = json.load(file)

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

PoSDict = {"n": ['noun'], "f": ['verb'], "f.sah": ['verb'], "b": ['noun', 'verb'], "t": ['adj', 'adv'],
           "s": ['adj'], "p jm" : ['adj', 'adv'], "jm p": ['prep_phrase'], "jm": ['phrase'], "par": ['particle'],  "f par": ['verb particle'],
           "m": ['adv'], "lfik": ['prefix'], "xfik": ['suffix'], "b xfik": ['suffix'], "t xfik": ['suffix'],
           "su n": ['name'], "su t": ['adj'], "il": ['intj'], "l": ['conj'],
           "num": ['num'], "p": ['prep'], "pn": ['pron'], "d": ['det']}

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
                if len(row) >= 4 and row[0] == globasaWord and row[1] == englishGloss and row[2] == PoS and row[3] == englishSense:
                    if row[5] != '':
                        return row[4], row[5]
                    else:
                        return None
            return None
    else:
        return None

def getstuff(senses, globasa_word, english_word, spanish_words, esperanto_words, PoS):
    count = 0
    spaMatch = False
    epoMatch = False
    spaFound = False
    epoFound = False
    if globasa_word == "-abil":
        print("Found")
    match = False
    langDict = {}
    for lang in langCodes:
        langDict[lang] = set()
    sense = ""
    wordEng = ""
    wkPoS = ""
    englishMatched = False
    spaSect = set()
    epoSect = set()
    spaOutput = ""
    epoOutput = ""
    for sense, langTranslations in senses.items():
        spaFound = False
        epoFound = False
        if 'es' in langTranslations:
            spaFound = True
            spaSect = set()
            for translation in langTranslations['es']:
                spaSect.add(translation.word)
            spaOutput = ", ".join(spaSect.intersection(set(spanish_words)))
            spaDiff = spaSect.difference(set(spanish_words))
            if spaDiff:
                spaOutput += " /" + ", ".join(spaDiff) + "/"
            if spaSect.intersection(set(spanish_words)):
                spaMatch = True
        if 'eo' in langTranslations:
            epoFound = True
            epoSect = set()
            for translation in langTranslations['eo']:
                epoSect.add(translation.word)
            epoOutput = ", ".join(epoSect.intersection(set(esperanto_words)))
            epoDiff = epoSect.difference(set(esperanto_words))
            if epoDiff:
                epoOutput += " /" + ", ".join(epoDiff) + "/"
            if epoSect.intersection(set(esperanto_words)):
                epoMatch = True
        match = (((spaMatch and spaFound) or (not spaFound)) and ((epoMatch and epoFound) or (not epoFound)) and (
                    spaFound or epoFound))
        markingQuery = retrieveMarking(senseKeyPath, globasa_word, english_word, PoS, sense)
        if markingQuery:
            yieldOutput = [[english_word], [PoS], [sense], [markingQuery[0]], [markingQuery[1]], [spaOutput],
                           [epoOutput]]
        else:
            yieldOutput = [[english_word], [PoS], [sense], [boolS[match]], [''], [spaOutput],
                           [epoOutput]]

        for lang in langCodes:
            if lang in langTranslations.keys():
                otherLanguageOutput = []
                for translation in langTranslations[lang]:
                    if translation.word == "hirundō":
                        print("Here!")
                    if (PoS == 'noun' or PoS == 'name') and ('masculine' in translation.tags or 'feminine' in translation.tags or 'neuter' in translation.tags):
                        outputWord = translation.word
                        genders = []
                        if 'masculine' in translation.tags:
                            genders += ["<m>"]
                        if 'feminine' in translation.tags:
                            genders += ["<f>"]
                        if 'neuter' in translation.tags:
                            genders += ["<n>"]
                        otherLanguageOutput += [translation.word + " " + "/".join(genders)]
                    else:
                        otherLanguageOutput += [translation.word]
                yieldOutput += [[", ".join(otherLanguageOutput)]]
            else:
                yieldOutput += [""]
        yield yieldOutput

    #yield [english_word, PoS]

def getdata(filename, globasa_word, criteria, PoS, singlePoS):
    for englishWords in criteria[0]:
        englishWord = englishWords.strip()
        if englishWord.startswith("_"):
            yield [englishWord, PoS]
            continue

        found = False

        # Primary PoS lookup
        trans = db.get_translations(englishWord, PoS)
        if trans is not None:
            found = True
            for row in getstuff(trans, globasa_word, englishWord, criteria[1], criteria[2], PoS):
                yield row

        # Fallback PoS lookups
        fallbacks = []
        if PoS == "noun":
            fallbacks.append("name")
        if PoS == "phrase":
            fallbacks.extend(["particle", "adv"])
        if PoS == "verb particle":
            fallbacks.append("adv")
        if singlePoS and PoS == "noun":
            fallbacks.append("verb")
        if singlePoS and PoS == "adj":
            fallbacks.append("adv")
        if PoS == "par":
            fallbacks.append("verb")

        for fb_pos in fallbacks:
            fb_trans = db.get_translations(englishWord, fb_pos)
            if fb_trans is not None:
                found = True
                for row in getstuff(fb_trans, globasa_word, englishWord, criteria[1], criteria[2], fb_pos):
                    yield row

        if not found:
            yield [englishWord, PoS]


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
    languageHeaders = []
    for lang in langCodes:
        if lang in twoLetterCodes.keys():
            languageHeaders += [twoLetterCodes[lang]]
        else:
            languageHeaders += [languageNames[lang]]

    writer.writerow(
         ['Glb'] + ['Eng'] + ['Prt of Sp'] + ['Wiktionary Sense (in Translations)'] + ['App?'] + ['Vetted?'] + ['Spa'] + ['Epo'] + languageHeaders)
    menaWriter.writerow(['Globasa'] + ['Eng with Senses'] + languageHeaders)

    menalariReader = csv.reader(menalari_file, delimiter=',', quotechar='"')
    next(menalariReader, None)

    started = False

    for row in menalariReader:
        if not started:
            if row[0].startswith(startPrefix):
                started = True
            else:
                continue
        #englishGlosses = re.sub("\(_.*?_\)", "", row[6]).strip().split("; ")
        englishGlosses = row[6].strip().split("; ")
        spanishGlosses = re.sub("\(_.*?_\)", "", row[9]).strip().split("; ")
        esperantoGlosses = re.sub("\(_.*?_\)", "", row[8]).strip().split("; ")
        PoSs = row[3].split("; ")
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
        outputGlosses = [[set() for j in range(len(PoSlist))] for i in range(len(langCodes))]
        singlePoS = len(PoSlist) == 1
        if PoSinDict:
            output = None
            delimiterRegex = "(?<!\([^\)])\s*,(?![^\(]*\))"
            for i, gloss in enumerate(zip(englishGlosses, spanishGlosses, esperantoGlosses)):
                p = [re.split(delimiterRegex, gloss[0]), re.split(delimiterRegex, gloss[1]), re.split(delimiterRegex, gloss[2])]
                englishParts = re.split(delimiterRegex, gloss[0])
                newParts = []
                for part in englishParts:
                    reduced = re.sub("\(.*?\)", "", part)
                    if reduced != part:
                        newParts += [reduced]
                        newParts += [part.replace("(", "").replace(")", "")]
                    else:
                        newParts += [part]
                p[0] = newParts
                spanishParts = re.split(delimiterRegex, gloss[1])
                newParts = []
                for part in spanishParts:
                    reduced = re.sub("\(.*?\)", "", part)
                    if reduced != part:
                        newParts += [reduced]
                        newParts += [part.replace("(", "").replace(")", "")]
                    else:
                        newParts += [part]
                p[1] = newParts
                esperantoParts = re.split(delimiterRegex, gloss[2])
                newParts = []
                for part in esperantoParts:
                    reduced = re.sub("\(.*?\)", "", part)
                    if reduced != part:
                        newParts += [reduced]
                        newParts += [part.replace("(", "").replace(")", "")]
                    else:
                        newParts += [part]
                p[2] = newParts

                engSenseDict = {}
                for query_row in getdata(wiktionary_dump_path, row[0], p, PoSlist[i], singlePoS):
                    # print(query_row)
                    if len(query_row) == 2:
                        output = [row[0]] + query_row
                        print("\t".join(output))
                        writer.writerow(output)
                        continue
                    line = ""
                    if query_row[3] == ['s'] and query_row[4] == ['v']:
                        if query_row[0][0] in engSenseDict:
                            engSenseDict[query_row[0][0]] |= set(query_row[2])
                        else:
                            engSenseDict.setdefault(query_row[0][0], set(query_row[2]))
                        for j, entry in enumerate(query_row):
                            if j >= 7 and entry:
                                outputGlosses[j - 7][i].add(entry[0])

                    output = [row[0]] + [", ".join(entry) for entry in query_row]
                    output.insert(6, row[15])

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
