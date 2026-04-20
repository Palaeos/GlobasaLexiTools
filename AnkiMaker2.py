import copy
import csv
import re
import markdown
import string

from Lexilista_parser import *
from GlobasaTransliterators import *

import random

from tabulate import tabulate
import pandas as pd



class AnkiFields:
    """These will become the fields of the card template"""

    def __init__(self):
        # set all members to their initial value
        self.Lexi = ""
        self.EnfasisdoLexi = ""
        self.PoS = ["", "", ""]
        self.Mena = ["", "", ""]
        self.AnimateAdjective = ""
        self.InanimateAdjective = ""
        self.Imajelinku = ""
        self.ImajeAsel = ""
        self.Faleanimalinku = ""
        self.Faleanimaasel = ""
        self.NSFW = ""
        self.DuayumImaje = ""
        self.DuayumImajeAsel = ""
        self.Anaphor = ""
        self.AloAnaphor = ""
        self.Oposmenalexi = ""
        self.GlobasaMisal = ""
        self.MisalClozed = ""
        self.MisalBasatayti = ""
        self.FaleliMisal = ""
        self.FaleliMisalClozed = ""
        self.FaleliMisalBasatayti = ""
        self.TigayumMisal = ""
        self.TigayumMisalClozed = ""
        self.TigayumMisalBasatayti = ""
        self.Transitive = ""
        self.Intransitive = ""
        self.Copula = ""
        self.EchoTransitive = ""
        self.Paladoawdio = ""
        self.PaladoKodek = ""
        self.Soti = ""
        self.Sotiasel = ""
        self.Sotikodek = ""
        self.Sotilabel = ""
        self.tags = ""

    def reset(self):
        # set all members to their initial value
        self.Lexi = ""
        self.EnfasisdoLexi = ""
        self.PoS = ["","",""]
        self.Mena = ["", "", ""]
        self.AnimateAdjective = ""
        self.InanimateAdjective = ""
        self.Imajelinku = ""
        self.ImajeAsel = ""
        self.Faleanimalinku = ""
        self.Faleanimaasel = ""
        self.NSFW = ""
        self.DuayumImaje = ""
        self.DuayumImajeAsel = ""
        self.Anaphor = ""
        self.AloAnaphor = ""
        self.GlobasaMisal = ""
        self.MisalClozed = ""
        self.MisalBasatayti = ""
        self.FaleliMisal = ""
        self.FaleliMisalClozed = ""
        self.FaleliMisalBasatayti = ""
        self.TigayumMisal = ""
        self.TigayumMisalClozed = ""
        self.TigayumMisalBasatayti = ""
        self.Transitive = ""
        self.Intransitive = ""
        self.Copula = ""
        self.EchoTransitive = ""
        self.Paladoawdio = ""
        self.PaladoKodek = ""
        self.Soti = ""
        self.Sotiasel = ""
        self.Sotikodek = ""
        self.Sotilabel = ""
        self.Oposmenalexi = ""
        self.tags = ""

PoS_display_dict_Eng = {
GlossPoS.NOUN : "Noun",
GlossPoS.VERB : "Verb",
GlossPoS.ADJECTIVE : "Adjective",
GlossPoS.VERBAL_ADVERB : "Verbal-Adverb",
GlossPoS.ADVERB : "Adverb",
GlossPoS.INTERJECTION : "Interjection",
GlossPoS.PREFIX : "Prefix",
GlossPoS.PRONOUN : "Pronoun",
GlossPoS.PROPER_NOUN : "Proper noun",
GlossPoS.PROPER_ADJECTIVE : "Proper adjective",
GlossPoS.DETERMINER : "Determiner",
GlossPoS.CONJUNCTION : "Conjunction",
GlossPoS.NUMBER : "Number",
GlossPoS.PARTICLE : "Particle",
GlossPoS.PREPOSITION : "Preposition",
GlossPoS.POSTPOSITION : "Postposition",
GlossPoS.PHRASE : "Phrase",
GlossPoS.VERB_PHRASE : "Verb phrase",
GlossPoS.NOUN_PHRASE : "Noun phrase",
GlossPoS.ADJECTIVE_PHRASE : "Adjective phrase",
GlossPoS.CONJUNCTION_PHRASE : "Conjunction phrase",
GlossPoS.PHRASAL_PREPOSITION : "Phrasal preposition",
GlossPoS.PHRASAL_CONJUNCTION : "Phrasal conjunction",
GlossPoS.PREPOSITIONAL_PHRASE : "Prepositional phrase",
GlossPoS.POSSESSIVE_PRONOUN : "Possessive pronoun",
GlossPoS.POSSESSIVE_ADJECTIVE : "Possessive adjective",
GlossPoS.PHRASAL_ADVERB : "Phrasal adverb",
}



codecDict = {"ogg": "ogg", "mp3": "mp3"}
contentWordTypes = ["n", "f", "b", "t", "s", "p jm", "m", "il", "su t", "su n"]




menalari_name = "word-listNew.csv"
ranking_name = "Doxo_word_frequency.csv"

df = pd.read_csv(menalari_name, index_col=0)
prnf = pd.read_csv("menalariPronouns_edited.tsv", sep="\t", index_col=0)
imgf = pd.read_csv("menalariImages_edited.csv", index_col=0, sep="\t")
imgf.fillna(False, inplace = True)
gfcf = pd.read_csv("graphic_blacklist", index_col=0, sep=",")
prnf.fillna(False, inplace = True)
construction_frame = pd.read_excel("Constructions.xlsx", index_col=0, na_values = False)
construction_frame.fillna(False, inplace = True)
cardEscrow = []
maxEscrowLength = 5

with open("./" + ranking_name, newline='') as ranking_file, open('AnkiList.csv', 'w', newline='') as AnkiList:
  AnkiWriter = csv.writer(AnkiList, delimiter='\t', lineterminator='\n')
  rankingReader = csv.reader(ranking_file, delimiter='\t', quotechar="'")
  next(rankingReader, None)
  fields = AnkiFields()

  for row in rankingReader:
    fields.reset()
    if not row[0] in df.index or str(row[0]).lower() == "devtest":
      continue
    print(row[0])
    #if row[0] == "(fe) duli mara":
    #  print("duli mara")
    if row[0] == "ufue":
      print("duli mara")
    fields.Lexi = row[0]
    if row[0] == "dur na":
        print("start")
    if globasaCountSyllables(row[0]) > 1:
        fields.EnfasisdoLexi = globasaStressSentence(row[0]).strip()
    selected_rows = df.loc[row[0]]
    pronouns = ""
    if row[0] in prnf.index:
      if isinstance(prnf.loc[row[0]].Pronoun, str):

        pronouns = prnf.loc[row[0]].Pronoun.split(",")
        fields.Anaphor = pronouns[0]
        if len(pronouns) > 1:
            fields.AloAnaphor = pronouns[1]
    antonyms = selected_rows['Antonyms']
    if antonyms and antonyms == antonyms:
        fields.Oposmenalexi = str(antonyms)
    antonyms = ""


    if row[0] in construction_frame.index and construction_frame.loc[row[0]]['to_exclude'] and construction_frame.loc[row[0]]['to_exclude'] != "":
        englishRawGlosses = str(selected_rows['TranslationEng']).replace(construction_frame.loc[row[0]]['to_exclude'], "").strip("; ,")
    else:
        englishRawGlosses = str(selected_rows['TranslationEng'])
    if englishRawGlosses:
        glosses = parseEntry(englishRawGlosses, str(selected_rows['WordClass']))
        print(str(glosses))
        verbCount = 0
        for i, gloss in enumerate(glosses):
            if gloss.pos != GlossPoS.VERB:
                fields.Mena[i-verbCount] = markdown.markdown(gloss.gloss)
                fields.PoS[i-verbCount] = PoS_display_dict_Eng[gloss.pos]
            else:
                verbCount += 1
                if gloss.verb_type is None:
                    print("?")
                match gloss.verb_type:
                    case VerbType.INTRANSITIVE:
                        fields.Intransitive = markdown.markdown(gloss.gloss)
                    case VerbType.TRANSITIVE:
                        fields.Transitive = markdown.markdown(gloss.gloss)
                    case VerbType.COPULAR:
                        fields.Copula = markdown.markdown(gloss.gloss)
                    case VerbType.ECHO_TRANSITIVE:
                        fields.EchoTransitive = markdown.markdown(gloss.gloss)
                    case VerbType.INTRANSITIVE_CU:
                        fields.Intransitive = markdown.markdown(gloss.gloss)
                    case VerbType.FEELING:
                        fields.Intransitive = markdown.markdown(gloss.gloss)
                    case VerbType.STATE:
                        fields.Intransitive = markdown.markdown(gloss.gloss)
                    case _:
                        print("?")

    if len(row) > 1:
        fields.GlobasaMisal = markdown.markdown(str(row[1]))
        fields.MisalClozed = markdown.markdown(re.sub("\*\*.*?\*\*", "[...]", str(row[1])))
    if len(row) > 3:
        fields.MisalBasatayti = markdown.markdown(str(row[3]))
    tags = []
    if selected_rows['Tags'] == selected_rows['Tags']:
      tags += str(selected_rows['Tags']).replace(" ", "_").split(",_")
    if len(row) > 2 and row[2] == row[2]:
      tags += [str(row[2]).replace(" ", "_")]
    fields.tags = " ".join(tags)
    if  row[0] in imgf.index and (not isinstance(imgf.DirectURL[row[0]],pd.Series)) and imgf.DirectURL[row[0]]:
      if imgf.DirectURL[row[0]].endswith(".gif"):
          fields.Faleanimalinku = str(imgf.DirectURL[row[0]])
          fields.Faleanimaasel = str(imgf.SourcePage[row[0]])
      else:
          fields.Imajelinku = str(imgf.DirectURL[row[0]])
          fields.ImajeAsel = str(imgf.SourcePage[row[0]])
      if str(row[0]) in gfcf.index:
          fields.NSFW = "y"
    AnkiWriter.writerow(
        [fields.Lexi, fields.EnfasisdoLexi, fields.PoS[0], fields.PoS[1], fields.PoS[2], fields.Mena[0], fields.Mena[1],
         fields.Mena[2], fields.AnimateAdjective, fields.InanimateAdjective, fields.Transitive, fields.EchoTransitive, fields.Intransitive, fields.Copula, fields.Imajelinku, fields.ImajeAsel, fields.NSFW, fields.DuayumImaje,
         fields.DuayumImajeAsel, fields.Faleanimalinku, fields.Faleanimaasel, fields.Anaphor, fields.Oposmenalexi, fields.GlobasaMisal, fields.MisalClozed, fields.MisalBasatayti,
         fields.FaleliMisal, fields.FaleliMisalClozed, fields.FaleliMisalBasatayti, fields.TigayumMisal, fields.TigayumMisalClozed, fields.TigayumMisalBasatayti,
         fields.Paladoawdio, fields.PaladoKodek, fields.Soti, fields.Sotiasel, fields.Sotikodek,
         fields.Sotilabel, fields.tags])

