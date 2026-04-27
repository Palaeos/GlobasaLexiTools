import csv, re
import pandas as pd

PoSDict = {"n": ['n'], "f": ['vblex'], "f.sah": ['vbmod'], "b": ['n', 'vblex'], "t": ['adj', 'adv'],
           "s": ['adj'], "p jm" : ['adv'], "m": ['adv'],
           "su n": ['np'], "su t": ['adj'], "il": ['ij'], "l": ['cnjsub'],
           "num": ['num'], "p": ['pr'], "pn": ['prn'], "d": ['det']}
#functionPoS = ['p', "pn", "d", "l", "f.sah"]
functionPoS = ['p', "d", "l"]

genderForeignDict = {"m": "m", "f": "f", "n": "nt"}
#morpho = input("Duabasali or morfoli? / Bilingual or morphological?\n")

genderDict = {"te": "ut", "to": "nt", "mante": "m", "femte": "f"}

gender_frame = pd.read_csv('menalariPronouns_edited.tsv', sep="\t", index_col=0)
gender_frame.fillna(False, inplace = True)
gender_frame.drop_duplicates(inplace = True)

filename = "word-list.csv"

translation_ext_frame = pd.read_csv("menalariExtension_edited.tsv", sep="\t", index_col=0)
translation_ext_frame.fillna(False, inplace = True)
translation_ext_frame.drop_duplicates(inplace = True)

blank = '<b/>'

GetFunctionWords = True

EngSpaGlb_dictionary = {}

with open(filename, newline='') as csvfile,\
        open('dictionary_En.xml', 'w', newline='') as dictionary_En,\
        open('dictionary_Es.xml', 'w', newline='') as dictionary_Es,\
        open('dictionary_Eo.xml', 'w', newline='') as dictionary_Eo,\
        open('dictionary_De.xml', 'w', newline='') as dictionary_De,\
        open('dictionary_Fr.xml', 'w', newline='') as dictionary_Fr,\
        open('dictionary_Nl.xml', 'w', newline='') as dictionary_Nl,\
        open('dictionary_un.xml', 'w', newline='') as dictionary_un:

    spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    next(spamreader, None)

    for row in spamreader:
        # print(row)
        if row[0].startswith("-"):
            continue
        if GetFunctionWords and row[3] not in functionPoS:
            continue
        elif not GetFunctionWords and row[3] in functionPoS:
            continue
        officialGlosses = [None for i in range(6)]
        officialGlosses[0] = re.sub("\(_.*?_\)", "", row[6]).strip().split("; ") # English
        officialGlosses[1] = re.sub("\(_.*?_\)", "", row[9]).strip().split("; ") # Spanish
        officialGlosses[2] = re.sub("\(_.*?_\)", "", row[8]).strip().split("; ") # Esperanto
        if row[0] in translation_ext_frame.German and translation_ext_frame.German[row[0]]:
            officialGlosses[3] = re.sub("\(_.*?_\)", "", translation_ext_frame.German[row[0]]).strip().split("; ") # German
        if row[0] in translation_ext_frame.French  and translation_ext_frame.French[row[0]]:
            officialGlosses[4] = re.sub("\(_.*?_\)", "", translation_ext_frame.French[row[0]]).strip().split("; ") # French
        if row[0] in translation_ext_frame.Dutch  and translation_ext_frame.Dutch[row[0]]:
            officialGlosses[5] = re.sub("\(_.*?_\)", "", translation_ext_frame.Dutch[row[0]]).strip().split("; ") # Dutch
        englishGlosses = officialGlosses[0]
        if row[0] == "sen":
            print("")
        if row[3].split(".")[0] in PoSDict.keys():

            output = None
            for i, PoS in enumerate(PoSDict[row[3].split(".")[0]]):
                processedGlosses = [None for i in range(6)]
                for j, langGloss in enumerate(officialGlosses):
                    if not langGloss:
                        continue
                    processedGlosses[j] = []
                    if i >= len(langGloss):
                        continue
                    for gloss in langGloss[i].split(", "):
                        gloss = gloss.strip(" ")
                        reduction = re.sub("\(.*?\)", "", gloss)
                        if reduction != gloss:
                            processedGlosses[j].append(reduction)
                            processedGlosses[j].append(gloss.replace("(", "").replace(")", ""))
                        else:
                            processedGlosses[j].append(gloss)

                if PoS == "n" or PoS == "np":
                    genders = []
                    if row[0] in gender_frame.index and isinstance(gender_frame.loc[row[0]].Pronoun, str):
                        anaphora = gender_frame.loc[row[0]].Pronoun.split(", ")
                        for anaphor in anaphora:
                            genders.append(genderDict[anaphor])
                        for gender in genders:
                            dictionary_un.write("<e lm=\"" + row[0] + "\">       <i>" + blank.join(
                                row[0].split()) + "</i><par n=\"__n_" + gender + "\"/></e>\n")
                            print("<e lm=\"" + row[0] + "\">       <i>" + blank.join(
                                row[0].split()) + "</i><par n=\"__n_" + gender + "\"/></e>")

                    else:
                        genders = ["GD"]
                        dictionary_un.write("<e lm=\"" + row[0] + "\">       <i>" + blank.join(
                            row[0].split()) + "</i><par n=\"__n\"/></e>\n")
                        print("<e lm=\"" + row[0] + "\">       <i>" + blank.join(
                            row[0].split()) + "</i><par n=\"__n\"/></e>")
                    for gender in genders:
                        for j in [0,2,3]:
                            if not processedGlosses[j]:
                                continue
                            nouns = processedGlosses[j]
                            for noun in nouns:
                                if not noun:
                                    continue
                                if noun.startswith("_"):
                                    continue
                                if j == 0:
                                    dictionary_dua = dictionary_En
                                elif j == 1:
                                    dictionary_dua = dictionary_Es
                                elif j == 2:
                                    dictionary_dua = dictionary_Eo
                                elif j == 3:
                                    dictionary_dua = dictionary_De
                                elif j == 4:
                                    dictionary_dua = dictionary_Fr
                                elif j == 5:
                                    dictionary_dua = dictionary_Nl
                                if j in [1,3,4,5] and noun.endswith(">"):
                                    foreignGenders = []
                                    for foreignGenderRaw in noun.split(" ")[-1].split("/"):
                                        foreignGender = genderForeignDict[foreignGenderRaw.replace("<", "").replace(">", "")]
                                        noun = re.sub("\<.*?\>", "", noun)
                                        dictionary_dua.write("<e><p><l>" + blank.join(row[
                                                                                          0].split()) + "<s n = \"" + PoS + "\"/><s n = \"" + gender + "\"/></l>   <r>" + blank.join(
                                            noun.split()) + "<s n = \"" + PoS + "\"/><s n = \"" + foreignGender + "\"/></r></p></e>\n")
                                        print("<e><p><l>" + blank.join(row[
                                                                           0].split()) + "<s n = \"" + PoS + "\"/><s n = \"" + gender + "\"/></l>   <r>" + blank.join(
                                            noun.split()) + "<s n = \"" + PoS + "\"/><s n = \"" + foreignGender + "\"/></r></p></e>")
                                else:
                                    dictionary_dua.write("<e><p><l>" + blank.join(row[
                                                                                     0].split()) + "<s n = \"" + PoS + "\"/><s n = \"" + gender + "\"/></l>   <r>" + blank.join(
                                        noun.split()) + "<s n = \"" + PoS + "\"/></r></p></e>\n")
                                    print("<e><p><l>" + blank.join(row[
                                                                       0].split()) + "<s n = \"" + PoS + "\"/><s n = \"" + gender + "\"/></l>   <r>" + blank.join(
                                        noun.split()) + "<s n = \"" + PoS + "\"/></r></p></e>")

                else:
                    # output += ", Verb meanings: " + str(verbs)
                    dictionary_un.write(
                        '<e><p><l>' + row[0] + '</l>       <r>' + row[0] + '<s n = "' + PoS + '"/></r></p></e>\n')
                    for j, langGloss in enumerate(officialGlosses):
                        if not langGloss:
                            continue
                        if len(langGloss) <= i:
                            continue
                        if j == 0:
                            dictionary_dua = dictionary_En
                        elif j == 1:
                            dictionary_dua = dictionary_Es
                        elif j == 2:
                            dictionary_dua = dictionary_Eo
                        elif j == 3:
                            dictionary_dua = dictionary_De
                        elif j == 4:
                            dictionary_dua = dictionary_Fr
                        elif j == 5:
                            dictionary_dua = dictionary_Nl

                        glosses = langGloss[i].split(", ")
                        for gloss in glosses:
                            dictionary_dua.write(
                                '<e><p><l>' + row[0] + '<s n = "'+ PoS +'"/></l>   <r>' + blank.join(gloss.split()).strip() + '<s n = "'+ PoS +'"/></r></p></e>\n')
                            print('<e><p><l>' + row[0] + '<s n = "'+ PoS +'"/></l>   <r>' + blank.join(gloss.split()).strip() + '<s n = "'+ PoS +'"/></r></p></e>')

            # print( "**" + row[0] + "**"+ ", " + output)

            # print("word: " + row[0] + ", PoS: " + row[3] + ", first type: " + row[6])

            # print(englishGlosses)
        if False:
            for englishGloss in englishGlosses[0].split(", "):
                for spanishGloss in spanishGlosses[0].split(", "):
                    # print(englishGloss.trim() + ", " + spanishGloss.trim() + ", " + row[0].trim())
                    EngSpaGlb_dictionary[(englishGloss, spanishGloss)] = row[0]

            #print("\n \n \n")



