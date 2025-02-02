import csv, re

#morpho = input("Duabasali or morfoli? / Bilingual or morphological?\n")

filename = "/home/paleos/Documents/Language/word-list.csv"

blank = '<b/>'

EngSpaGlb_dictionary = {}

with open(filename, newline='') as csvfile:

    spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')


    for row in spamreader:
        # print(row)
        englishGlosses = re.sub("\(_.*?_\)", "", row[4]).strip().split("; ")
        spanishGlosses = re.sub("\(_.*?_\)", "", row[7]).strip().split("; ")
        if False:
            if row[2] == "l":
                output = None
                determiners = englishGlosses[0].split(", ")
                for determiner in determiners:
                    print("<e><p><l>" + blank.join(row[0].split()) + "<s n = \"cnjsub\"/></l>   <r>" + blank.join(determiner.split()) + "<s n = \"cnjsub\"/></r></p></e>")
        if True:


                    if row[2].startswith("b"):
                        output = None
                        nouns = englishGlosses[0].split(", ")
                        # output = "Noun meanings: " + str(nouns)
                        for noun in nouns:
                            print("<e><p><l>" + blank.join(row[0].split()) + "<s n = \"n\"/></l>   <r>" + blank.join(noun.split()) + "<s n = \"n\"/></r></p></e>")

                        if len(englishGlosses) > 1:
                            verbs = englishGlosses[1].split(", ")
                            # output += ", Verb meanings: " + str(verbs)
                            for verb in verbs:
                                parts = verb.split(" ")
                                if len(parts) == 2:
                                    print("<e><p><l>" + row[0] + "<s n = \"vblex\"/></l>   <r>" + parts[0] + "<g><b/>" + parts[
                                        1] + "</g><s n = \"vblex\"/></r></p></e>")
                                else:
                                    print("<e><p><l>" + row[
                                        0] + "<s n = \"vblex\"/></l>   <r>" + verb + "<s n = \"vblex\"/></r></p></e>")
                        # print( "**" + row[0] + "**"+ ", " + output)
                    if row[2] == "su n":
                        output = None
                        proper_nouns = englishGlosses[0].split(", ")
                        for proper_noun in proper_nouns:
                            print("<e><p><l>" + blank.join(row[0].split()) + "<s n = \"np\"/></l>   <r>" + blank.join(proper_noun.split()) + "<s n = \"np\"/></r></p></e>")

                    if row[2] == "p jm":
                        output = None
                        adverbs = englishGlosses[0].split(", ")
                        # output += ", Verb meanings: " + str(verbs)
                        for adverb in adverbs:
                            print("<e><p><l>" + row[0] + "<s n = \"adv\"/></l>   <r>" + adverb + "<s n = \"adv\"/></r></p></e>")

                    if row[2] == "num":
                        output = None
                        numbers = englishGlosses[0].split(", ")
                        for number in numbers:
                            print("<e><p><l>" + row[0] + "<s n = \"num\"/></l>   <r>" + number + "<s n = \"num\"/></r></p></e>")

                    if row[2] == "p":
                        output = None
                        prepositions = englishGlosses[0].split(", ")
                        for preposition in prepositions:
                            print("<e><p><l>" + row[
                                0] + "<s n = \"pr\"/></l>   <r>" + preposition.strip() + "<s n = \"pr\"/></r></p></e>")
                    if row[2] == "il":
                        output = None
                        interjections = englishGlosses[0].split(", ")
                        for interjection in interjections:
                            print("<e><p><l>" + row[
                                0] + "<s n = \"ij\"/></l>   <r>" + interjection.strip() + "<s n = \"ij\"/></r></p></e>")

                    if row[2].startswith("t"):
                        output = None
                        adjectives = englishGlosses[0].split(", ")
                        # output = "Noun meanings: " + str(nouns)
                        for adjective in adjectives:
                            if (adjective.endswith("ly")):
                                print("<e><p><l>" + row[
                                    0] + "<s n = \"adv\"/></l>   <r>" + adjective + "<s n = \"adv\"/></r></p></e>")
                            else:
                                print("<e><p><l>" + row[
                                    0] + "<s n = \"adj\"/></l>   <r>" + adjective + "<s n = \"adj\"/></r></p></e>")

                        if len(englishGlosses) > 1:
                            adverbs = englishGlosses[1].split(", ")
                            # output += ", Verb meanings: " + str(verbs)
                            for adverb in adverbs:
                                print("<e><p><l>" + row[
                                    0] + "<s n = \"adv\"/></l>   <r>" + adverb + "<s n = \"adv\"/></r></p></e>")
                        # print( "**" + row[0] + "**"+ ", " + output)

                        # print("word: " + row[0] + ", PoS: " + row[2] + ", first type: " + row[4])

                        # print(englishGlosses)
                    if False:
                        for englishGloss in englishGlosses[0].split(", "):
                            for spanishGloss in spanishGlosses[0].split(", "):
                                # print(englishGloss.trim() + ", " + spanishGloss.trim() + ", " + row[0].trim())
                                EngSpaGlb_dictionary[(englishGloss, spanishGloss)] = row[0]

                    print("\n \n \n")

                    if True:
                        with open(filename, newline='') as csvfile:

                            spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')

                            for row in spamreader:
                                # print(row)
                                englishGlosses = re.sub("\(_.*?_\)", "", row[4]).strip().split("; ")

                                if row[2].startswith("b"):
                                    print("<e lm=\"" + row[0] + "\">       <i>" + blank.join(
                                        row[0].split()) + "</i><par n=\"__n\"/></e>")
                                    print(
                                        "<e lm=\"" + row[0] + "\">       <i>" + row[0] + "</i><par n=\"__vblex\"/></e>")

                                if row[2] == "num":
                                    print("<e><p><l>" + row[0] + "</l>       <r>" + row[
                                        0] + "<s n = \"num\"/></r></p></e>")

                                if row[2] == "np":
                                    print("<e><p><l>" + row[0] + "</l>       <r>" + blank.join(
                                        row[0].split()) + "<s n = \"np\"/></r></p></e>")
                                if row[2] == "p":
                                    print("<e><p><l>" + row[0] + "</l>       <r>" + row[
                                        0] + "<s n = \"pr\"/></r></p></e>")

                                if row[2].startswith("t"):
                                    print("<e><p><l>" + row[0] + "</l>       <r>" + row[
                                        0] + "<s n = \"adv\"/></r></p></e>")
                                    print("<e lm=\"" + row[0] + "\">       <i>" + row[0] + "</i><par n=\"__adj\"/></e>")

                                if row[2] == "p jm":
                                    print("<e><p><l>" + row[0] + "</l>       <r>" + row[
                                        0] + "<s n = \"adv\"/></r></p></e>")


