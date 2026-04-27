import csv
import os
import re
import markdown

from collections import Counter
from lemminflect import getLemma
import pandas as pd

multi_word_parts = ["kom", "xafe", "lefe", "leya", "xaya", "na", "hu", "mara", "watu", "din", "noce" , "leki", "xaki"]

PoSDict = {"n": ['NOUN'], "f": ['VERB'], "f.sah": ['AUX'], "b": ['NOUN', 'VERB'], "t": ['ADJ', 'ADV'],
           "s": ['ADJ'], "m": ['ADV'], "su n": ['PROPN'], "su t": ['ADJ']}

def collectNGrams(sentence, NGramCounter):
    for word in sentence.lower().split(" "):
        for i in range(1, min(len(word), N)):
            for j in range(len(word) - i):
                if word[j:j + i].isalpha():
                    if word[j:j + i] in NGramCounter[i]:
                        NGramCounter[i][word[j:j + i]] += 1
                    else:
                        NGramCounter[i][word[j:j + i]] = 1

def processSentence(sentence, passages, passageCount):
    words = sentence.split(" ")
    i = 0
    while i in range(len(words)):
        candidate = lemmatize(words[i].lower(), df)
        if not candidate:
            if i + 1 < len(words):
                next = lemmatize(words[i + 1].lower(), df)
                if next in multi_word_parts:
                    if i + 1 < len(words) and next:
                        if words[i].lower() + " " + next in df.index:
                            candidate = words[i].lower() + " " + next
                        elif "(fe) " + words[i].lower() + " " + next in df.index:
                            candidate = "(fe) " + words[i].lower() + " " + next
                        i += 1
                    i += 1
            if not candidate:
                i += 1
                continue
        candidate = candidate.strip(':;#,."“”!?-*/+')

        if candidate == "fe":
            if i + 1 < len(words):
                next = lemmatize(words[i + 1].lower(), df)
                if next and (candidate + " " + next in df.index):
                    candidate += " " + lemmatize(words[i + 1].lower(), df)
                    i += 1
                    if i + 2 < len(words) and next and (candidate + " " + next in df.index):
                        next = lemmatize(words[i + 2].lower(), df)
                        candidate += " " + lemmatize(words[i + 2].lower(), df)
                        i += 1
        elif candidate == "cel":
            next = lemmatize(words[i + 1].lower(), df)
            if i + 1 < len(words) and next and (candidate + " " + next in df.index):
                candidate += " " + lemmatize(words[i + 1].lower(), df)
                i += 1
        elif candidate == "he":
            next = lemmatize(words[i + 1].lower(), df)
            if i + 1 < len(words) and next and (candidate + " " + next in df.index):
                candidate += " " + lemmatize(words[i + 1].lower(), df)
                i += 1
        elif candidate == "no" and i + 2 < len(words):
            next = lemmatize(words[i + 1].lower(), df)
            if i + 1 < len(words) and next and (candidate + " " + next in df.index):
                candidate += " " + lemmatize(words[i + 1].lower(), df)
                i += 1
        if i + 1 < len(words):
            next = lemmatize(words[i + 1].lower(), df)
            if next in multi_word_parts:
                if i + 1 < len(words) and next and (candidate + " " + next in df.index):
                    candidate += " " + lemmatize(words[i + 1].lower(), df)
                    i += 1
        passageCount[candidate] += 1
        i += 1
        if len(sentence.split()) > 3:
            if candidate not in passages:
                passages.setdefault(candidate, sentence)
    return passages
def emphasizeExample(word, sentence, df):
    example = ""
    passage_words = sentence.split(" ")
    test_length = len(word.split(" "))
    i = 0
    occurence = word
    while i in range(len(passage_words)):
        member = passage_words[i]
        seek_bound = min(i + test_length, len(passage_words) - 1)
        test_word = ""
        for j in range(i, seek_bound):
            test_word += passage_words[j].lower().strip(':;#,."“”!?-*/+') + " "
        if test_length == 1:
            test_word = passage_words[i].lower().strip(':;#,."“”!?-*/+')
        candidate = lemmatize(test_word.strip(), df)
        if not candidate and test_length > 2:
            test_word = ""
            for j in range(i, seek_bound-1):
                test_word += passage_words[j].lower().strip(':;#,."“”!?-*/+') + " "
            candidate = lemmatize(test_word.strip(), df)
            if not candidate:
                occurence = test_word.strip()
                candidate = lemmatize("(fe) " + test_word.strip(), df)
        if candidate == word:
            original = ""
            for j in range(i, seek_bound):
                original += passage_words[j] + " "
            if test_length == 1:
                original = passage_words[i]
            if any(map(str.isupper, original)):
                if original.lower().removeprefix(word) != original.lower():
                    example += original.replace(occurence.capitalize(), "**" + occurence.capitalize() + "**") + " "
                else:
                    example += original.replace(word, "**" + word + "**") + " "
            else:
                example += original.lower().replace(word, "**" + word + "**") + " "
            i += test_length
        else:
            example += member + " "
            i += 1
    return example.strip(" \n")

def lemmatize(word, df):
    candidate = word.strip(':;#,."“”!?-*/+\n').lower()
    if candidate == '':
        return None
    if candidate.removeprefix('be') in df.index:
        candidate = candidate.removeprefix('be')
    if candidate.removeprefix('du') in df.index:
        candidate = candidate.removeprefix('du')
    if candidate.removesuffix('li') in df.index:
        candidate = candidate.removesuffix('li')
    if candidate.removesuffix('ya') in df.index:
        candidate = candidate.removesuffix('ya')
    if candidate.removesuffix('ne') in df.index:
        candidate = candidate.removesuffix('ne')
    if candidate.removesuffix('do') in df.index:
        candidate = candidate.removesuffix('do')
    if candidate in df.index:
        return candidate
    if candidate.removesuffix('lari') in df.index:
        return candidate.removesuffix('lari')
    if candidate.removesuffix('cu') in df.index:
        return candidate.removesuffix('cu')
    if candidate.removesuffix('gi') in df.index:
        return candidate.removesuffix('gi')
    if candidate.removesuffix('mo') in df.index:
        return candidate.removesuffix('mo')
    return None
menalari_name = "word-list.csv"
ranking_name = "Doxo_word_frequency.csv"
total_ranking_name = "Doxo_total_word_frequency.csv"
passages_name = "Doxo_passages.csv"
Esperanto_name = "EO 15000 Tekstaro filtered with ESPDIC.txt"


wordList = []
N = 4
NGramCounter = [{} for i in range(0,N)]
totalWordList = []
passages = {}
translatedPassages = {}
examplePassages = {}

text_names = ['Corpora/Thirty Short Stories in Globasa','Corpora/Hikaye fal Vanege', 'Corpora/Fabula fal Esopo', 'Corpora/Dahabutofa ji Tiga Baru', 'Corpora/Kastilo Cucurumbel', 'Corpora/Siri-Logane Tutum', 'Corpora/Lala', 'Corpora/Towa Babel', 'Corpora/Kido', 'Corpora/Globatotal Deklaradoku tem Insanli Haki', 'Corpora/“Am Eskri Jandan” fal Paul Graham']

df = pd.read_csv(menalari_name, index_col=0)
sentencef = pd.read_csv("./CanonicalSentences.tsv", sep="\t", index_col=1)
sentencef.fillna(False, inplace = True)
sentences = []

if not os.path.exists("./Doxo_passages_edited.csv"):
    no_passage_list = True
else:
    no_passage_list = False
    doxof = pd.read_csv("./Doxo_passages_edited.csv", sep="\t", index_col=1)
    # doxof.fillna(False, inplace = True)
    doxof = doxof.dropna()
    examf = pd.read_csv("./GlobasaLexiMisal.csv", sep="\t", index_col=0)



with open("./CanonicalSentences.tsv", 'r', newline='') as examples:
    exampleSentences = []
    examplePassageCount = Counter()
    exampleReader = csv.reader(examples, delimiter='\t', quotechar='"')
    next(exampleReader, None)
    # reading each line
    for row in exampleReader:
        line = row[1]
        exampleSentences += [line]
    # reading each word
    for sentence in exampleSentences:
        examplePassages = processSentence(sentence, examplePassages, examplePassageCount)

with open(ranking_name, 'w', newline='') as ranking, open(total_ranking_name, 'w', newline='') as total_ranking, open(passages_name, 'w', newline='') as passage_file:
    passageWriter = csv.writer(passage_file, delimiter='\t', lineterminator='\n')
    writer = csv.writer(ranking, delimiter=',', lineterminator='\n')
    total_writer = csv.writer(total_ranking, delimiter=',', lineterminator='\n')
    totalPassageCount = Counter() # Count of a word over the whole corpus
    for text_name in text_names:
        passageCount = Counter()
        translatedPassageCount = Counter()
        with open(text_name, 'r', newline='') as doxo:
            if no_passage_list:
                sentences = []
                # reading each line
                for line in doxo:
                    sentences += line.split(".")
                for sentence in sentences:
                    if sentence.strip("\n") != "":
                        if sentence.endswith("\n"):
                            passageWriter.writerow([text_name.removeprefix("Corpora/"), sentence.strip().strip("\n")])
                        else:
                            passageWriter.writerow([text_name.removeprefix("Corpora/"), sentence.strip() + "."])
            else:
                filtereddoxof = doxof[doxof["Asel"] == text_name.removeprefix("Corpora/")]
                sentences = filtereddoxof.index.tolist()
            # reading each word
            for sentence in sentences:
                collectNGrams(sentence, NGramCounter)
                passages = processSentence(sentence, passages, passageCount)
        if no_passage_list:
            continue
        for word, count in passageCount.most_common():
            totalPassageCount[word] += count
            if word == "kopi":
                print("Here!")
            if word not in wordList:
                if word in examf.index:
                    example = examf.loc[word].Misal
                    wordList += [word]
                    output = word + "\t" + example + "\t" + text_name.removeprefix("Corpora/").removesuffix(".txt")
                    output += "\t" + examf.loc[word].Example
                    print(output)
                    ranking.write(output + "\n")
                elif word in passages and passages[word] in doxof.index:
                    example = emphasizeExample(word, passages[word], df)
                    wordList += [word]
                    output = word + "\t" + example + "\t" + text_name.removeprefix("Corpora/").removesuffix(".txt")
                    if doxof.loc[passages[word]]["Sentence"]:
                        englishPassage = doxof.loc[passages[word]]["Sentence"]
                        englishGlosses = re.sub("\(_.*?_\)", "", df.loc[word].TranslationEng).strip().split("; ")
                        PoSs = df.loc[word]["WordClass"].split("; ")
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
                        candidateEng = ""
                        englishPassageWords = englishPassage.split(" ")
                        for i, passageWord in enumerate(englishPassageWords):
                            for k, sense in enumerate(englishGlosses):
                                if PoSinDict and k >= len(PoSlist):
                                    continue
                                for engWords in sense.split(", "):
                                    engWords = engWords.strip()
                                    engWordsList = engWords.lower().split(" ")
                                    numEngWords = len(engWordsList)
                                    if numEngWords == 1:
                                        engWord = engWordsList[0]
                                        if PoSinDict:
                                            lemma = getLemma(passageWord.lower().strip(',;.?"-'), upos=PoSlist[k])
                                            if lemma and engWord == lemma[0]:
                                                candidateEng = " ".join(englishPassage.split(" ")[:i] + [
                                                    "**" + englishPassage.split(" ")[i] + "**"] + englishPassage.split(
                                                    " ")[(i + 1):])
                                        else:
                                            if engWord.lower() == passageWord.lower().strip(',;."?-'):
                                                candidateEng = " ".join(englishPassage.split(" ")[:i] + [
                                                    "**" + englishPassage.split(" ")[i] + "**"] + englishPassage.split(
                                                    " ")[(i + 1):])
                                    elif numEngWords > 1:
                                        if i + numEngWords <= len(englishPassageWords) and engWords == " ".join(
                                                englishPassageWords[i:i + numEngWords]).lower().strip(',;."?-'):
                                            candidateEng = " ".join(englishPassage.split(" ")[:i] + ["**" + " ".join(
                                                englishPassage.split(" ")[
                                                i:i + numEngWords]) + "**"] + englishPassage.split(" ")[
                                                                              (i + numEngWords):])

                        if not candidateEng:
                            candidateEng = englishPassage
                        output += "\t" + candidateEng
                    print(output)
                    ranking.write(output + "\n")
                elif word in examplePassages:
                    example = emphasizeExample(word, examplePassages[word], df)
                    wordList += [word]
                    output = word + "\t" + example + "\t" + text_name.removeprefix("Corpora/").removesuffix(".txt")
                    if sentencef.loc[examplePassages[word]]["English"]:
                        englishPassage = sentencef.loc[examplePassages[word]]["English"]
                        englishGlosses = re.sub("\(_.*?_\)", "", df.loc[word].TranslationEng).strip().split("; ")
                        PoSs = df.loc[word]["WordClass"].split("; ")
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
                        candidateEng = ""
                        englishPassageWords = englishPassage.split(" ")
                        for i, passageWord in enumerate(englishPassageWords):
                            for k, sense in enumerate(englishGlosses):
                                if PoSinDict and k >= len(PoSlist):
                                    continue
                                for engWords in sense.split(", "):
                                    engWords = engWords.strip()
                                    engWordsList = engWords.lower().split(" ")
                                    numEngWords = len(engWordsList)
                                    if numEngWords == 1:
                                        engWord = engWordsList[0]
                                        if PoSinDict:
                                            lemma = getLemma(passageWord.lower().strip(',;.?"-'), upos=PoSlist[k])
                                            if engWord == lemma[0]:
                                                candidateEng = " ".join(englishPassage.split(" ")[:i] + ["**" + englishPassage.split(" ")[i] + "**"] + englishPassage.split(" ")[(i+1):])
                                        else:
                                            if engWord.lower() == passageWord.lower().strip(',;."?-'):
                                                candidateEng = " ".join(englishPassage.split(" ")[:i] + ["**" + englishPassage.split(" ")[i] + "**"] + englishPassage.split(" ")[(i+1):])
                                    elif numEngWords > 1:
                                        if i+numEngWords <= len(englishPassageWords) and engWords == " ".join(englishPassageWords[i:i+numEngWords]).lower().strip(',;."?-'):
                                            candidateEng = " ".join(englishPassage.split(" ")[:i] + ["**" + " ".join(englishPassage.split(" ")[i:i+numEngWords]) + "**"] + englishPassage.split(" ")[(i+numEngWords):])

                        if not candidateEng:
                            candidateEng = englishPassage
                        output += "\t" + candidateEng
                    print(output)
                    ranking.write(output + "\n")
                elif word in passages:
                    example = emphasizeExample(word, passages[word], df)
                    wordList += [word]
                    output = word + "\t" + example + "\t" + text_name.removeprefix("Corpora/").removesuffix(".txt")
                    print(output)
                    ranking.write(output + "\n")
                else:
                    wordList += [word]
                    print(word)
                    ranking.write(word + "\n")
        #print(wordList)
        #print(sentences)
    sorted_items = sorted(totalPassageCount.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    totalFrequencyList = [None for i in range(len(sorted_items))]
    bTable = [[] for i in range(len(sorted_items))]
    totalWordCount = 0
    for i, item in enumerate(sorted_items):
        totalFrequencyList[i] = item
        totalWordCount += item[1]
        total_writer.writerow(item)
        for j, other_item in enumerate(sorted_items):
            if j > 200:
                break
            if j == i or item[1]/other_item[1] == 1:
                bTable[i].append(-1)
                continue
            b = -(item[1]/other_item[1] * (j+1) - i + 1)/(1-item[1]/other_item[1])
            bTable[i].append(b)
    with open("bTable.csv", 'w', newline='') as bTable_file:
        b_writer = csv.writer(bTable_file, delimiter=',', lineterminator='\n')
        for row in bTable:
            b_writer.writerow(row)
    with open("bTable.csv", 'w', newline='') as bTable_file:
        b_writer = csv.writer(bTable_file, delimiter=',', lineterminator='\n')
        for row in bTable:
            b_writer.writerow(row)
    for i, counter in enumerate(NGramCounter):
        with open(str(i) + "-Grams.tsv", 'w', newline='') as NGram_file:
            NGram_writer = csv.writer(NGram_file, delimiter='\t', quotechar="'")
            print(str(i) + "-Grams:")
            # Sorting key-value pairs by value, and by key if values are the same
            sorted_items = sorted(counter.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
            for item in sorted_items:
                NGram_writer.writerow(item)
    with open("TekstaroFrequencies.csv", 'r', newline='\n') as fallbackList:
        fallbackReader = csv.reader(fallbackList, delimiter='\t', quotechar='"')
        #next(fallbackReader, None)

        for row in fallbackReader:
            if not row[0] in wordList:
                ##print(word + ": " + str(x[0]))
                wordList += [row[0]]
                output = row[0]
                #if len(x) > 14 and x[14] == x[14]:
                #    output += "\t '" + x[14] + "'"
                ranking.write(output + "\n")
                totalFrequencyList.append((row[0], None))
                print(row[0])
    """  
        for word in fallbackList:
            key = word.strip('\n\r')
            # filtering the rows where Age_Range contains Young
            for x in df.itertuples():
                if x[8] != x[8]:
                    continue
                esperantoGlosses = re.sub("\(_.*?_\)", "", x[8]).strip().split("; ")
                for gloss in esperantoGlosses:
                    for i in gloss.split(", "):
                        if i == key and not x[0] in wordList:
                            ##print(word + ": " + str(x[0]))
                            wordList += [x[0]]
                            output = x[0]
                            if len(x) > 14 and x[14] == x[14]:
                                output += "\t '" + x[14] + "'"
                            ranking.write(output + "\n")
                            print(x[0])
    """
    filtered_df = df.drop(wordList)
    for index, row in filtered_df.iterrows():
        if row.name != row.name:
            continue
        word = str(row.name)
        if row['Example'] == row['Example']:
            example = emphasizeExample(word, row['Example'], df)
            print(word + "\t'" + example + "'")
            ranking.write(word + "\t'" + example + "'" + "\n")
        else:
            print(word)
            ranking.write(word + "\n")
print(wordList)
#print(passages)
