import csv
import re
import markdown
import string

import genanki
import pandas as pd

PoSDict = {"n": ['Noun'], "f": ['Verb'], "f.sah": ['Verb'], "b": ['Noun', 'Verb'], "t": ['Adjective', 'Verbal Adverb'],
           "s": ['Adjective'], "p jm": ['Adjective', 'Verbal Adverb'],
           "m": ['Adverb'], "lfik": ['Prefix'], "xfik": ['Suffix'], "b xfik": ['Suffix'], "t xfik": ['Suffix'],
           "su n": ['Proper noun'], "su t": ['Adjective'], "il": ['Interjection'], "l": ['Conjunction'],
           "num": ['Number'], "p": ['Preposition'], "pn": ['Pronoun'], "d": ['Determiner']}
contentWordTypes = ["n", "f", "b", "t", "s", "p jm", "m", "il" "su t", "su n"]

my_model = genanki.Model(
  1607392319,
  'Simple Model',
  fields=[
    {'name': 'Question'},
    {'name': 'Answer'},
  ],
  templates=[
    {
      'name': 'Card 1',
      'qfmt': '{{Question}}',
      'afmt': '{{FrontSide}}<hr id="answer">{{Answer}}',
    },
  ])



my_deck = genanki.Deck(
  2059400110,
  'Globasa Content Words')



menalari_name = "word-list.csv"
ranking_name = "Doxo_word_frequency.csv"

df = pd.read_csv(menalari_name, index_col=0)

with open("./" + ranking_name, newline='') as ranking_file:
  rankingReader = csv.reader(ranking_file, delimiter='\t', quotechar="'")
  next(rankingReader, None)

  for row in rankingReader:
    if not row[0] in df.index or str(row[0]).lower() == "devtest":
      continue
    selected_rows = df.loc[row[0]]
    englishText = str(selected_rows['TranslationEng'])
    englishGlosses = re.sub("\(_.*?_\)", "", englishText).strip().split("; ")
    #spanishGlosses = re.sub("\(_.*?_\)", "", selected_rows['TranslationSpa']).strip().split("; ")
    #esperantoGlosses = re.sub("\(_.*?_\)", "", selected_rows['TranslationEpo']).strip().split("; ")
    PoSs = str(selected_rows['WordClass']).split("; ")
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
    if not PoSKey in contentWordTypes:
      continue
    glosses = ""
    for i in range(min(len(englishGlosses), len(PoSlist))):
      glosses += "**" + PoSlist[i] + "**" + ": " + englishGlosses[i] + "  \n   \n"
    tags = str(selected_rows['Tags']).replace(" ", "_").split(",_")

    my_note = None
    front_side = ""
    if len(row) > 1 and row[1] == row[1]:
      front_side = str(row[1])
    else:
      front_side = str(row[0])
    print(markdown.markdown(front_side) + " " + markdown.markdown(glosses))
    # Recognition
    if tags == ["nan"]:
      my_note = genanki.Note(
        model=my_model,
        fields=[markdown.markdown(front_side), markdown.markdown(glosses)]
      )
    else:
      my_note = genanki.Note(
        model=my_model,
        fields=[markdown.markdown(front_side), markdown.markdown(glosses)],
        tags=tags
      )
    my_deck.add_note(my_note)
    # Production
    if tags == ["nan"]:
      my_note = genanki.Note(
        model=my_model,
        fields=[markdown.markdown(glosses), row[0]]
      )
    else:
      my_note = genanki.Note(
        model=my_model,
        fields=[markdown.markdown(glosses), row[0]],
        tags=tags
      )
    my_deck.add_note(my_note)

genanki.Package(my_deck).write_to_file('GlobasaContent.apkg')
"""


  for row in menalariReader:
    if not started:
      if row[0].startswith(startPrefix):
        started = True
      else:
        continue
    englishGlosses = re.sub("\(_.*?_\)", "", row[6]).strip().split("; ")
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
"""