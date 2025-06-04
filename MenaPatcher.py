import csv
import re
import markdown

from collections import Counter


PoSDict = {"n": ['Noun'], "f": ['Verb'], "f.sah": ['Verb'], "b": ['Noun', 'Verb'], "t": ['Adjective', 'Adverb'],
           "s": ['Adjective'], "p jm": ['Prepositional Phrase'],
           "m": ['Adverb'], "lfik": ['Prefix'], "xfik": ['Suffix'], "b xfik": ['Suffix'], "t xfik": ['Suffix'],
           "su n": ['Proper noun'], "su t": ['Adjective'], "il": ['Interjection'], "l": ['Conjunction'],
           "num": ['Number'], "p": ['Preposition'], "pn": ['Pronoun'], "d": ['Determiner']}


# Take in moby project list and parse as CSV, but with \ as the delimiter via Pandas
# Loop through the word list and write the replacement column to a CSV
import pandas as pd
df = pd.read_csv('mobypos.txt', index_col=0, encoding='iso-8859-1', sep="\\", dtype={'AN': str}, keep_default_na=False)

menalari_name = "word-list.csv"

with open("./" + menalari_name, newline='') as menalari_file, open('menalariCorrection.tsv', 'w', newline='') as menaFix:
    menaWriter = csv.writer(menaFix, delimiter='\t', lineterminator='\n')

    menalariReader = csv.reader(menalari_file, delimiter=',', quotechar='"')
    next(menalariReader, None)

    started = False

    for row in menalariReader:
        englishGlosses = re.sub("\([^)]*\)", "", row[6]).strip().split("; ")
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
        output = ""
        corrected = False
        unknownFound = False
        if len(englishGlosses) == 1 and len(PoSlist) == 2:
            i = 0
            reachedVerbal = False
            nominalPart = []
            verbalPart = []
            for i, gloss in enumerate(englishGlosses[0].split(", ")):
                gloss = gloss.strip()
                if gloss in df.index:
                    mobyRow = df.loc[gloss]
                    mobyPoS = mobyRow["AN"]
                    if "Verb" in PoSlist:
                        if "V" in mobyPoS or "i" in mobyPoS or "t" in mobyPoS:
                            verbalPart += [gloss]
                            if not reachedVerbal:
                                if "N" in mobyPoS or "p" in mobyPoS or "h" in mobyPoS:
                                    nominalPart += [gloss]
                                else:
                                    reachedVerbal = True
                    if "Adverb" in PoSlist:
                        if "v" in mobyPoS:
                            verbalPart += [gloss]
                            if not reachedVerbal:
                                if "A" in mobyPoS or "V" in mobyPoS:
                                    nominalPart += [gloss]
                                else:
                                    reachedVerbal = True
                else:
                    if reachedVerbal:
                        verbalPart += [gloss]
                    else:
                        nominalPart += [gloss]
                    unknownFound = True
            corrected = reachedVerbal
            if (nominalPart or verbalPart) and corrected:
                menaWriter.writerow([row[0]] + [", ".join(nominalPart) + "; " + ", ".join(verbalPart)])
                print(row[0] + "\t" + ", ".join(nominalPart) + "; " + ", ".join(verbalPart))
            else:
                menaWriter.writerow([row[0]])
                print(row[0])
        else:
            menaWriter.writerow([row[0]])
            print(row[0])

