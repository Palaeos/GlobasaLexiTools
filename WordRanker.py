import csv
import re
import markdown

from collections import Counter

import pandas as pd

multi_word_parts = ["kom", "xafe", "lefe", "na"]

def emphasizeExample(word, sentence, df):
    example = ""
    passage_words = sentence.split(" ")
    test_length = len(word.split(" "))
    i = 0
    while i in range(len(passage_words)):
        member = passage_words[i]
        seek_bound = min(i + test_length, len(passage_words) - 1)
        test_word = ""
        for j in range(i, seek_bound):
            test_word += passage_words[j].lower().strip(':;#,."“”!?-*/+') + " "
        if test_length == 1:
            test_word = passage_words[i].lower().strip(':;#,."“”!?-*/+')
        if lemmatize(test_word.strip(), df) == word:
            original = ""
            for j in range(i, seek_bound):
                original += passage_words[j] + " "
            if test_length == 1:
                original = passage_words[i]
            if any(map(str.isupper, original)):
                example += original.replace(word.capitalize(), "**" + word.capitalize() + "**") + " "
            else:
                example += original.lower().replace(word, "**" + word + "**") + " "
            i += test_length
        else:
            example += member + " "
            i += 1
    return example.strip(" \n")

def lemmatize(word, df):
    candidate = word.strip(':;#,."“”!?-*/+\n')
    if candidate == '':
        return None
    if candidate.removeprefix('be') in df.index:
        candidate = candidate.removeprefix('be')
    if candidate.removeprefix('du') in df.index:
        candidate = candidate.removeprefix('du')
    if candidate in df.index:
        return candidate
    if candidate.removesuffix('lari') in df.index:
        return candidate.removesuffix('lari')
    if candidate.removesuffix('li') in df.index:
        return candidate.removesuffix('li')
    return None
menalari_name = "word-list.csv"
ranking_name = "Doxo_word_frequency.csv"
Esperanto_name = "EO 15000 Tekstaro filtered with ESPDIC.txt"


wordList = []
passages = {}

text_names = ['Hikaye fal Vanege', 'Fabula fal Esopo', 'Towa Babel', 'Globatotal Deklaradoku tem Insanli Haki', '“Am Eskri Jandan” fal Paul Graham']

df = pd.read_csv(menalari_name, index_col=0)
sentences = []

with open(ranking_name, 'w', newline='') as ranking:
    writer = csv.writer(ranking, delimiter=',', lineterminator='\n')
    for text_name in text_names:
        passageCount = Counter()
        with open(text_name, 'r', newline='') as doxo:
            # reading each line
            for line in doxo:
                sentences += line.split(".")
            # reading each word
            for sentence in sentences:
                words = sentence.split(" ")
                i = 0
                while i in range(len(words)):
                    candidate = lemmatize(words[i].lower(), df)
                    if not candidate:
                        i += 1
                        continue
                    candidate = candidate.strip(':;#,."“”!?-*/+')
                    if candidate == "fe":
                        next = lemmatize(words[i+1].lower(), df)
                        if i + 1 < len(words) and next and (candidate + " " + next in df.index):
                            candidate += " " + lemmatize(words[i+1].lower(), df)
                            i += 1
                            if i + 2 < len(words) and next and (candidate + " " + next in df.index):
                                next = lemmatize(words[i + 2].lower(), df)
                                candidate += " " + lemmatize(words[i+2].lower(), df)
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
        for word, count in passageCount.most_common():
            if word not in wordList:
                if word in passages:
                    example = emphasizeExample(word, passages[word], df)
                    wordList += [word]
                    output = word + "\t'" + example + ".'\t" + text_name.removesuffix(".txt")
                    print(output)
                    ranking.write(output + " \n")
                else:
                    wordList += [word]
                    print(word)
                    ranking.write(word + "\n")
        #print(wordList)
        #print(sentences)
        """
    with open(Esperanto_name, 'r', newline='\n') as esperantoList:
        for word in esperantoList:
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
                                output += ", '" + x[14] + "'"
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