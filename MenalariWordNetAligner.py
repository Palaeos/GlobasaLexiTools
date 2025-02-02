import os
import sys
import pandas as pd
import csv
import re
import wn
import itertools
from wn.similarity import path, lch
from wn.taxonomy import lowest_common_hypernyms, common_hypernyms

PoSDict = {"n": ['n'], "f": ['v'], "f.sah": ['v'], "b": ['n', 'v'], "t": ['a', 'r'],
           "s": ['a'], "p jm": ['r'], "jm": ['t'], "m": ['r'],  "su n": ['n'], "su t": ['a'],
           "num": ['n'], "p": ['r']}
# 'i53558' for artifact, 'i35547' for abstract entities, 'i69080' for social group,  "i69527" for language, "i75492" for animal cries/noises
# 'i68061' for beliefs ' i81450' for systems, 'i69080' for attitudes, 'i35610' for action, 'i81084' for form of government,
# 'i58265' for room, 'i88069' for doer, actor, 'i35546' for physical entity, 'i35589' for group, 'i88364' for authority, ' i91363' for military officer
# 'i35561' for causal agent, 'i35549' for physical object, 'i35548' for thing, 'i35569' for matter
SuffixDict = {("dom",'n'): ['i53558'], ("ya",'n'): ['i35547'], ("tim",'n'): ['i69080'], ("sa",'n'): ["i69527", "i75492"],
              ("ismo",'n'): [ "i68061", 'i81450', 'i69080'], ('krasi','n'): ['i35610', 'i81084'], ('tul', 'n'): ['i55130', 'i35573'],
              ('kamer','n'): ['i58265'], ('ista','n'): ['i88069'], ('yen','n'): ['i35561'], ('xey','n'): ['i35549', 'i35548', 'i35569'],
              ('kaxa','n'): ['i35546'], ('lari','n'): ['i35589'], ('kef','n'): ['i88364'], ('ente','n'): ['i35561']}

# 'i35563' for animal, i43203 for (live) birds,  i76470 for food, i35564 for plant, i105676 for fruit, i64399 for body part
# i105042 for fungus, i35552 for living being,  i54111 for furniture,  i55130 for instrumentality,  i35573 for article
# i78658 for beverage,  i35581 for form,  i52057 for clothing, i78162 for seasoning, i113651 for material
# i52319 for means of transport,  i114224 for rock,  i113874 for element, i115285 for crystal, i114036 for mineral
# i56458 for musical instrument, i97626 for atmospheric phenomenon, i105484 for plant structure
TagDictHypernym = {('hewan', 'n'): ['i35563'], ('piu', 'n'): ['i43203'], ('basa', 'n'):["i69527"], ('yamxey', 'n'):['i76470'],
                   ('sabzi', 'n'): ['i35564', 'i105484'] , ('planta', 'n'): ['i35564', 'i105484'], ('bio', 'n'): ['i35552'], ('tul', 'n'): ['i55130', 'i35573'],
                   ('fruta', 'n'):['i105676'], ('jismulogi', 'n'): ['i64399'], ('futru','n'): ['i105042'],
                   ('gluxey', 'n'): ['i78658'], ('mubile','n'): ['i54111'], ("dom",'n'): ['i53558'], ('klima', 'n'): ['i97626'],
                   ('figura', 'n'): ['i35581'], ('kimikali monlari', 'n'): ['i113874'], ('musikatul', 'n'): ['i56458'],
                   ('labas', 'n'): ['i52057', 'i55130'], ('calyo', 'n'): ['i52319'] , ('materyal', 'n'): ['i113651'],
                   ('petra', 'n'): ['i114224', 'i115285', 'i114036'], ('hoxinlyo', 'n'): ['i78162', 'i35564']}

# i85253 for continent, i81888 for country
TagDictInstance_of = {('daygeo', 'n'): ['i85253'], ('dexa', 'n'): ['i81888']}

senseKeyPath = "./GLB_ENG_WordnetSynsets.tsv"

def retrieveMarking(senseKeyPath, globasaWord, ILI):
    if os.path.exists(senseKeyPath):
        with open(senseKeyPath, newline='') as senseQuery:
            senseReader = csv.reader(senseQuery, delimiter='\t', quotechar='"')
            next(senseReader, None)
            for row in senseReader:
                if row[0] == globasaWord and row[1] == ILI:
                    if row[5] == 'v':
                        return row[4], row[5]
                    else:
                        return None
            return None
    else:
        return None

def retrieveMarkings(senseKeyPath, globasaWord, PoS):
    applicable_synsets = set()
    other_synsets = set()
    if os.path.exists(senseKeyPath):
        with open(senseKeyPath, newline='') as senseQuery:
            senseReader = csv.reader(senseQuery, delimiter='\t', quotechar='"')
            next(senseReader, None)
            for row in senseReader:
                if row[0] == globasaWord and row[2] == PoS:
                    if row[5] == 'v':
                        if row[4] == 's':
                            applicable_synsets.update(en.synsets(ili=row[1]))
                        else:
                            other_synsets.update(en.synsets(ili=row[1]))
            return applicable_synsets, other_synsets
    else:
        return None

def filterByAffix(globasa_word : str, synsets, PoS):
    filtered_synsets = set()
    attested_suffix = ""
    for suffix, pos in SuffixDict.keys():
        if pos != PoS:
            break
        if globasa_word.endswith(suffix):
            attested_suffix = suffix
            break
    if attested_suffix == '':
        return synsets
    ILI = SuffixDict[attested_suffix, PoS][0]
    topic = en.synsets(ili=ILI)[0]
    for synset in synsets:
        if lowest_common_hypernyms(synset, topic)[0] == topic:
            filtered_synsets.add(synset)
    return filtered_synsets

def filterByTag(globasa_word : str, tags : [str], synsets, PoS):
    filtered_synsets = set()
    hypernyms = set()
    instance_ofs = set()
    for tag in tags:
        if (tag,PoS) in TagDictHypernym.keys():
            for ili in TagDictHypernym[(tag, PoS)]:
                hypernyms.update(en.synsets(ili=ili))
        if (tag, PoS) in TagDictInstance_of.keys():
            for ili in TagDictInstance_of[(tag, PoS)]:
                instance_ofs.update(en.synsets(ili=ili))
    if not (hypernyms or instance_ofs):
        return synsets
    if hypernyms:
        filtered_hypernyms = hypernyms.copy()
        for hypernym1, hypernym2 in itertools.product(hypernyms, hypernyms):
            if lowest_common_hypernyms(hypernym1, hypernym2)[0] == hypernym1 and hypernym1 != hypernym2:
                filtered_hypernyms.remove(hypernym1)

        for synset in synsets:
            for hypernym in filtered_hypernyms:
                if lowest_common_hypernyms(synset, hypernym)[0] == hypernym:
                    filtered_synsets.add(synset)
    if instance_ofs:
        for synset in synsets:
            for instance_of in instance_ofs:
                testInstance_of = synset.get_related('instance_hypernym')
                if testInstance_of and instance_of in lowest_common_hypernyms(testInstance_of[0], instance_of):
                    filtered_synsets.add(synset)
    return filtered_synsets

def filterByAntonym(antonyms : [str], synsets, PoS_index):
    filtered_synsets = set()
    hypernyms = set()
    for antonym in antonyms:
        for synset in synsets:
            for anto_synset in synset.get_related('antonym'):
                if checkWordSynset(antonym, PoS_index, anto_synset):
                    filtered_synsets.add(synset)
    if filtered_synsets:
        return filtered_synsets
    else:
        return synsets

thresholdFunction = [0,1,2,2]
thresholdFunctionBi = [0,1,1,1,2]

def getThreshold(length, thresholdFunction):
    if length >= len(thresholdFunction):
        return thresholdFunction[-1]
    else:
        return thresholdFunction[length]

#wn.config.data_directory = '~/wn_data'

en = wn.Wordnet('oewn:2023')
es = wn.Wordnet('omw-es:1.4')

menalari_name = "word-list.csv"

def checkWordSynset(globasa_word, PoS_index, synset):
    with open("./" + menalari_name, newline='') as menalari_file:
        menalariReader = csv.reader(menalari_file, delimiter=',', quotechar='"')
        next(menalariReader, None)
        for row in menalariReader:
            if row[0] == globasa_word:
                englishGlosses = set(re.sub("\(_.*?_\)", "", row[5]).strip().split("; ")[PoS_index].split(', '))

                return len(englishGlosses.intersection(set(synset.lemmas())))

def setBasedQuery(englishQuery, spanishQuery, PoS ):
    applicable_synsets = set()
    total_synsets = set()
    for engWord in englishQuery:
        engWord = engWord.strip()
        engSynsets = set(en.synsets(engWord, pos=PoSlist[i]))
        if PoSlist[i] == 'a':
            engSynsets.update(set(en.synsets(engWord, pos='s')))
        if applicable_synsets:
            if applicable_synsets.intersection(engSynsets):
                applicable_synsets.intersection_update(engSynsets)
            else:
                """matched = False
                for synset in (en.synsets(engWord, pos=PoSlist[i])):
                    additions = set()
                    for existing_synset in applicable_synsets:
                        if path(synset, existing_synset) >= 0.40:
                            additions.add(synset)
                            matched = True
                    applicable_synsets |= additions

                if not matched:
                    applicable_synsets |= set(en.synsets(engWord, pos=PoSlist[i]))"""
        else:
            applicable_synsets |= set(engSynsets)
        total_synsets |= set(engSynsets)

    for spaWord in spanishQuery:
        spaWord = spaWord.strip()
        spaSynsets = set(es.synsets(spaWord, pos=PoSlist[i]))
        if PoSlist[i] == 'a':
            spaSynsets.update(set(es.synsets(word.strip(), pos='s')))
        translated_synsets = set()
        for synset in spaSynsets:
            translated_synsets |= set(synset.translate('oewn:2023'))
        if applicable_synsets:
            if applicable_synsets.intersection(translated_synsets):
                applicable_synsets.intersection_update(translated_synsets)
        else:
            applicable_synsets |= translated_synsets

    yield applicable_synsets, total_synsets

def scoreBasedQuery(englishQuery, spanishQuery, PoS):
    applicable_synsets = set()
    total_synsets = set()
    for engWord in englishQuery:
        engWord = engWord.strip()
        engSynsets = set(en.synsets(engWord, pos=PoSlist[i]))
        if PoSlist[i] == 'a':
            engSynsets.update(set(en.synsets(engWord, pos='s')))
        for synset in engSynsets:
            applicable = False
            synsetSpa = synset.translate(lexicon='omw-es:1.4')
            englishLemmas = set(synset.lemmas())
            """synsetAntonyms = synset.relations('antonym')
            for antonym in synsetAntonyms:
                if checkWordSynset(row[0], i, antonym):
                    applicable = True"""
            if synsetSpa:
                spanishLemmas = set(synsetSpa[0].lemmas())
                if len(englishLemmas.intersection(set(englishQuery))) + len(
                    spanishLemmas.intersection(set(spanishQuery))) >= getThreshold(len(englishQuery) + len(spanishQuery),
                                                                                        thresholdFunction):
                    applicable = True
            else:
                if len(englishLemmas.intersection(set(englishQuery))) >= getThreshold(len(englishQuery), thresholdFunction):
                    applicable = True
            if applicable:
                applicable_synsets.add(synset)

            total_synsets.add(synset)
    for spaWord in spanishQuery:
        spaWord = spaWord.strip()
        spaSynsets = set(es.synsets(spaWord, pos=PoSlist[i]))
        if PoSlist[i] == 'a':
            spaSynsets.update(set(es.synsets(word.strip(), pos='s')))
        for synset in spaSynsets:
            total_synsets |= set(synset.translate(lexicon='oewn:2023'))
    yield applicable_synsets, total_synsets


startPrefix = input("Lexi ingay na xoru har keto fe xoru? / What should the word begin with at the start?\nAm sol presyon 'enter' na xoru xorfe xoru. / Just hit enter to start from the beginning.\n")

started = False

with open("./" + menalari_name, newline='') as menalari_file, open('GLB_ENG_WordnetSynsets_initial.tsv', 'w',
                                                            newline='') as perSense, open('menalariExtension.tsv', 'w',
                                                                                          newline='') as menaExp:
    writer = csv.writer(perSense, delimiter='\t', lineterminator='\n')
    writer.writerow(
        ['Globasa'] + ['CILI'] + ['Prt of Sp'] + ['CILI definition'] + ['App?'] + ['Vetted?'] + [
            'English'])
    menaWriter = csv.writer(menaExp, delimiter='\t', lineterminator='\n')
    menalariReader = csv.reader(menalari_file, delimiter=',', quotechar='"')
    next(menalariReader, None)
    for row in menalariReader:
        if not started:
            if row[0].startswith(startPrefix):
                started = True
            else:
                continue
        englishGlosses = re.sub("\(_.*?_\)", "", row[5]).strip().split("; ")
        processedSpanishLine = re.sub("\(_.*?_\)", "", row[8]).strip()
        processedSpanishLine = re.sub('\(-a,\s+-e\)', '', processedSpanishLine)
        processedSpanishLine = re.sub('\(-a,\s+-que\)', '', processedSpanishLine)
        processedSpanishLine = re.sub('\(-as,\s+-es\)', '', processedSpanishLine)
        processedSpanishLine = re.sub('\(&\)', '', processedSpanishLine)
        spanishGlosses = processedSpanishLine.split("; ")

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
                PoSinDict = True
            else:
                PoSlist += ["N/A"]
        outputGlosses = [set() for j in range(len(PoSlist))]

        if PoSinDict:
            output = None
            antonyms = row[13].split(', ')
            applicable_synsets = [set() for j in range(len(PoSlist))]
            total_synsets = [set() for j in range(len(PoSlist))]
            other_synsets = [set() for j in range(len(PoSlist))]
            for i, gloss in enumerate(zip(englishGlosses, spanishGlosses, esperantoGlosses)):
                if PoSlist == ["N/A"] or PoSlist[i] == "N/A":
                    continue

                #p = [gloss[0].split(", "), gloss[1].split(", "), gloss[2].split(", ")]
                englishQuery, spanishQuery = gloss[0].split(", "), gloss[1].split(", ")
                for index in range(len(englishQuery)):
                    englishQuery[index] = englishQuery[index].strip()
                for index in range(len(spanishQuery)):
                    spanishQuery[index] = spanishQuery[index].strip(' .')
                applicable = False
                for word in englishQuery:
                    synsets = set(en.synsets(word.strip(), pos=PoSlist[i]))
                    if PoSlist[i] == 'a':
                        synsets.update(set(en.synsets(word.strip(), pos='s')))
                    if not synsets:
                        englishQuery.remove(word)
                for word in spanishQuery:
                    synsets = set(es.synsets(word.strip(), pos=PoSlist[i]))
                    if PoSlist[i] == 'a':
                        synsets.update(set(es.synsets(word.strip(), pos='s')))
                    if not es.synsets(word.strip(), pos=PoSlist[i]):
                        spanishQuery.remove(word)
                for applicableParts, totalParts in scoreBasedQuery(englishQuery, spanishQuery, PoS=PoSlist[i]):
                #for applicableParts, totalParts in setBasedQuery(englishQuery, spanishQuery, PoS=PoSlist[i]):

                    applicable_synsets[i], total_synsets[i] = applicableParts, totalParts
                    if row[1] == 'derived':
                        applicable_synsets[i] = filterByAffix(row[0], applicable_synsets[i], PoS=PoSlist[i])
                    applicable_synsets[i] = filterByTag(row[0], row[15].split(', '), applicable_synsets[i], PoS=PoSlist[i])
                    #applicable_synsets[i] = filterByAntonym(row[13].split(', '), applicable_synsets[i], i)

                    other_synsets[i] = total_synsets[i].difference(applicable_synsets[i])

                retrieval = retrieveMarkings(senseKeyPath, row[0], PoS=PoSlist[i])
                if retrieval:
                    applicable_synsets[i] |= retrieval[0]
                    applicable_synsets[i] -= retrieval[1]
                    other_synsets[i] |= retrieval[1]
                    other_synsets[i] -= retrieval[0]
                for synset in applicable_synsets[i]:
                    status = retrieveMarking(senseKeyPath, row[0], str(synset.ili.id))
                    if status:
                        output = [row[0], str(synset.ili.id), PoSlist[i], str(synset.ili.definition()), status[0], status[1],
                                  str(", ".join(synset.lemmas()))]
                    else:
                        output = [row[0], str(synset.ili.id), PoSlist[i], str(synset.ili.definition()), 's', ' ',
                              str(", ".join(synset.lemmas()))]

                    if es.synsets(ili=synset.ili.id):
                        output += [str(", ".join((es.synsets(ili=synset.ili.id))[0].lemmas()))]
                    writer.writerow(output)
                    print("\t".join(output))
                for synset in other_synsets[i]:
                    status = retrieveMarking(senseKeyPath, row[0], str(synset.ili.id))
                    if status:
                        output = [row[0], str(synset.ili.id), PoSlist[i], str(synset.ili.definition()), status[0],
                                  status[1],
                                  str(", ".join(synset.lemmas()))]
                    else:
                        output = [row[0], str(synset.ili.id), PoSlist[i], str(synset.ili.definition()), ' ', ' ', str(", ".join(synset.lemmas()))]
                    if es.synsets(ili=synset.ili.id):
                        output += [str(", ".join((es.synsets(ili=synset.ili.id))[0].lemmas()))]
                    writer.writerow(output)
                    print("\t".join(output))

                #output = [row[0], englishGlosses, synsets]
           # print(output)
                    """else:
                        matched = False
                        for synset in translated_synsets:
                            additions = set()
                            for existing_synset in applicable_synsets[i]:
                                if path(synset, existing_synset) >= 0.40:
                                    additions.add(synset)
                                    matched = True
                            applicable_synsets[i] |= additions
                        if not matched:
                            applicable_synsets[i] |= set(translated_synsets)"""

""" 
                    for synset in en.synsets(engWord, pos=PoSlist[i]):
                        synsetSpa = synset.translate(lexicon='omw-es:1.4')
                        englishLemmas = set(synset.lemmas())
                        synsetAntonyms = synset.relations('antonym')
                        for antonym in synsetAntonyms:
                            if checkWordSynset(row[0], i, antonym):

                        if synsetSpa:
                            spanishLemmas = set(synsetSpa[0].lemmas())
                            applicable = len(englishLemmas.intersection(set(p[0]))) >= getThreshold(len(p[0]), thresholdFunctionBi) and len(spanishLemmas.intersection(set(p[1]))) >= getThreshold(len(p[1]), thresholdFunctionBi)
                        else:
                            applicable = len(englishLemmas.intersection(set(p[0]))) >= getThreshold(len(p[0]), thresholdFunction)

                        if applicable:
                            applicable_synsets[i].add(synset)
                        else:
                            other_synsets[i].add(synset)
"""