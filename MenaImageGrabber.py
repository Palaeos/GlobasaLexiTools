from enum import Enum

from PIL import Image
import csv
import re
import markdown
import requests
from io import BytesIO
import pandas as pd

from bs4 import BeautifulSoup

atomf = pd.read_csv("Periodic_20Table_20of_20Elements.csv", index_col=2)
imgf = pd.read_csv("menalariImages_edited.csv", index_col=0, sep="\t") # For detecting existing images
imgf.fillna(False, inplace=True)

PoSDict = {"n": ['Noun'], "f": ['Verb'], "f.sah": ['Verb'], "b": ['Noun', 'Verb'], "t": ['Adjective', 'Adverb'],
           "s": ['Adjective'], "p jm": ['Prepositional Phrase'],
           "m": ['Adverb'], "lfik": ['Prefix'], "xfik": ['Suffix'], "b xfik": ['Suffix'], "t xfik": ['Suffix'],
           "su n": ['Proper noun'], "su t": ['Adjective'], "il": ['Interjection'], "l": ['Conjunction'],
           "num": ['Number'], "p": ['Preposition'], "pn": ['Pronoun'], "d": ['Determiner']}


def FindBioImageURL(taxon):
    response = requests.get(
        url="https://species.wikimedia.org/wiki/" + taxon,
    )
    if response.status_code != 200:
        return None
    soup = BeautifulSoup(response.content, 'html.parser')

    soupBody = soup.html.body.find("div", class_="mw-page-container").find("div", class_="mw-page-container-inner").find("main", id="content", class_="mw-body").find("div", id="bodyContent").find("div", class_="mw-content-ltr mw-parser-output")
    #print("https://species.wikimedia.org" + title.attrs["href"])
    if not soupBody.figure:
        return None
    sourceURL = "https://species.wikimedia.org" + soupBody.figure.a.attrs["href"]
    response = requests.get(
        url=sourceURL,
    )
    soupBody = BeautifulSoup(response.content, 'html.parser').html.body.find("div", class_="mw-page-container").find("div", class_="mw-page-container-inner").find("main", id="content", class_="mw-body")
    if soupBody.find("a", class_="mw-thumbnail-link"):
        return ["https:" + soupBody.find("a", class_="mw-thumbnail-link").attrs["href"], sourceURL]
    elif soupBody.find("div", class_="mw-content-ltr fullMedia") and soupBody.find("div", class_="mw-content-ltr fullMedia").a:
        return ["https:" + soupBody.find("div", class_="mw-content-ltr fullMedia").a.attrs["href"], sourceURL]

def FindAtomImageURL(atomNum):


    response = requests.get(
        url="https://en.wikipedia.org/wiki/Element_" + str(atomNum),
    )
    if response.status_code != 200:
        return None
    soup = BeautifulSoup(response.content, 'html.parser')

    soupBody = soup.html.body.find("div", class_="mw-page-container").find("div", class_="mw-page-container-inner").find("main", id="content", class_="mw-body").find("td", class_="infobox-image")
    #print("https://species.wikimedia.org" + title.attrs["href"])
    if not soupBody:
        return None
    sourceURL = "https://en.wikipedia.org" + soupBody.a.attrs["href"]
    response = requests.get(
        url=sourceURL,
    )
    soupBody = BeautifulSoup(response.content, 'html.parser').html.body.find("div", class_="mw-page-container").find("div", class_="mw-page-container-inner").find("main", id="content", class_="mw-body")
    if soupBody.find("a", class_="mw-thumbnail-link"):
        return ["https:" + soupBody.find("a", class_="mw-thumbnail-link").attrs["href"], sourceURL]
    elif soupBody.find("div", class_="mw-content-ltr fullMedia") and soupBody.find("div", class_="mw-content-ltr fullMedia").a:
        return ["https:" + soupBody.find("div", class_="mw-content-ltr fullMedia").a.attrs["href"], sourceURL]


def FindImageURL(noun):


    response = requests.get(
        url="https://en.wikipedia.org/wiki/" + str(noun),
    )
    if response.status_code != 200:
        return None
    soup = BeautifulSoup(response.content, 'html.parser')
    reference = None
    if noun == "lake":
       print(noun)

    soupBody = soup.html.body.find("main", class_="mw-body")
    sourceURL = None
    if soupBody.find("td", class_="infobox-image"):
        sourceURL = "https://en.wikipedia.org" + soupBody.find("td", class_="infobox-image").a.attrs["href"]
    elif soupBody.find("table", class_="infobox biota"):
        sourceURL = "https://en.wikipedia.org" + soupBody.find("table", class_="infobox biota").a.attrs["href"]
    elif soupBody.find("figure", class_="mw-default-size", typeof="mw:File/Thumb"):
        if soupBody.find("figure", class_="mw-default-size", typeof="mw:File/Thumb").a:
            sourceURL = "https://en.wikipedia.org" + soupBody.find("figure", class_="mw-default-size", typeof="mw:File/Thumb").a.attrs["href"]

    if not sourceURL:
        return None
    response = requests.get(
        url=sourceURL,
    )
    soupBody = BeautifulSoup(response.content, 'html.parser').html.body.find("div", class_="mw-page-container").find("div", class_="mw-page-container-inner").find("main", id="content", class_="mw-body")
    if soupBody.find("a", class_="mw-thumbnail-link"):
        return ["https:" + soupBody.find("a", class_="mw-thumbnail-link").attrs["href"], sourceURL]
    elif soupBody.find("div", class_="mw-content-ltr fullMedia") and soupBody.find("div", class_="mw-content-ltr fullMedia").a:
        return ["https:" + soupBody.find("div", class_="mw-content-ltr fullMedia").a.attrs["href"], sourceURL]

def FindCountryMapURL(noun):


    response = requests.get(
        url="https://en.wikipedia.org/wiki/" + str(noun),
    )
    if response.status_code != 200:
        return None
    soup = BeautifulSoup(response.content, 'html.parser')

    soupBody = soup.html.body.find("table", class_="infobox ib-country vcard")
    #print("https://species.wikimedia.org" + title.attrs["href"])
    if not (soupBody and soupBody.find_all("img")):
        return None
    images = soupBody.find_all("img")
    sourceURL = None
    if len(images) >= 3:
        if "href" in images[2].parent.attrs:
            sourceURL = "https://en.wikipedia.org" + images[2].parent.attrs["href"]
    else:
        if "href" in images[1].parent.attrs:
            sourceURL = "https://en.wikipedia.org" + images[1].parent.attrs["href"]
    if not sourceURL:
        return None
    response = requests.get(
        url=sourceURL,
    )
    soupBody = BeautifulSoup(response.content, 'html.parser').html.body.find("div", class_="mw-page-container").find("div", class_="mw-page-container-inner").find("main", id="content", class_="mw-body")
    if soupBody.find("a", class_="mw-thumbnail-link"):
        return ["https:" + soupBody.find("a", class_="mw-thumbnail-link").attrs["href"], sourceURL]
    elif soupBody.find("div", class_="mw-content-ltr fullMedia") and soupBody.find("div", class_="mw-content-ltr fullMedia").a:
        return ["https:" + soupBody.find("div", class_="mw-content-ltr fullMedia").a.attrs["href"], sourceURL]


#FindBioImageURL("Hirundinidae")
menalari_name = "word-list.csv"

menalari_name = "word-list.csv"
atomic = True # Periodic Table related

class Mode(Enum):
    GENERIC = 1
    BIO = 2
    ATOMIC = 3


with open("./" + menalari_name, newline='') as menalari_file, open('menalariImages.tsv', 'w', newline='') as menaImages:#, open('menalariImages_old.tsv', 'w', newline='') as menaOldImages:
    menaWriter = csv.writer(menaImages, delimiter='\t', lineterminator='\n')
    #menaOldWriter = csv.writer(menaOldImages, delimiter='\t', lineterminator='\n')

    menalariReader = csv.reader(menalari_file, delimiter=',', quotechar='"')
    next(menalariReader, None)

    started = False
    menaWriter.writerow(["Word"] + ["DirectURL"] + ["SourcePage"])

    for row in menalariReader:
        englishGlosses = row[6].replace("(_", "(").replace("_)", ")").strip().split("; ")
        # row[6].strip().split("; ")
        output = [row[0], row[6]]
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
        corrected = False
        unknownFound = False
        mode = Mode.BIO
        firstGloss = englishGlosses[0].split(", ")[0].strip()
        lastGloss = englishGlosses[0].split(", ")[-1].strip()
        match mode:
            case Mode.GENERIC:
                if len(PoSlist) == 2 and len(englishGlosses[0].split(", ")) == 1:
                    if row[0] in imgf.index and isinstance(imgf.DirectURL[str(row[0])], bool):
                        URL = FindImageURL(firstGloss)
                        if URL:
                            output += URL
            case Mode.BIO:
                if PoSs[0] == "b" and lastGloss != lastGloss.strip("_"):
                    if row[0] in imgf.index and isinstance(imgf.DirectURL[str(row[0])], bool):
                        URL = FindBioImageURL(lastGloss.strip("_"))
                        if URL is not None:
                            output += URL
            case Mode.ATOMIC:
                if lastGloss in atomf.AtomicNumber:
                    atomNum = atomf.AtomicNumber[lastGloss]
                    if atomNum == atomNum:
                        URL = FindAtomImageURL(atomNum)
                        if URL:
                            output += URL




        menaWriter.writerow(output)
        #if row[0] in imgf.index and not isinstance(imgf.DirectURL[str(row[0])], bool):
        #    menaOldWriter.writerow([row[0], row[6], imgf.loc[row[0]].DirectURL, imgf.loc[row[0]].SourcePage])
        #else:
        #    menaOldWriter.writerow([row[0], row[6]])
        print(", ".join(output))


"""
            if atomic:
                if lastGloss in atomf.AtomicNumber:
                    atomNum = atomf.AtomicNumber[lastGloss]
                    if atomNum == atomNum:
                        URL = FindAtomImageURL(atomNum)
                        if URL:
                            output += URL
            elif lastGloss != lastGloss.strip("_"):
                URL = FindImageURL(lastGloss.strip("_"))
                if URL:
                    output += URL
            """