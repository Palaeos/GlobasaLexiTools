from unidecode import unidecode

vowels = ['a',"e","i","o","u", "ư", "ơ", "â", "ê"]



def russianToGlobasa(word):
    output = ""
    i = 0
    while i < len(word):
        if word[i].lower() == "s" and i + 1 < len(word) and word[i+1] == "h":
            output += "x"
            i += 1
        elif word[i].lower() == "c" and i + 1 < len(word) and word[i + 1] == "h":
            output += "c"
            i += 1
        elif word[i].lower() == "d" and i + 2 < len(word) and word[i + 1] == "z" and word[i + 2] == "h":
            output += "j"
            i += 2
        elif word[i].lower() == "z" and i + 1 < len(word) and word[i + 1] == "h":
            output += "j"
            i += 1
        elif word[i].lower() == "k" and i + 1 < len(word) and word[i + 1] == "h":
            output += "h"
            i += 1
        elif word[i].lower() == "j":
            output += "y"
        elif word[i].lower() == "x":
            output += "h"
        else:
            output += word[i]
        i += 1
    return output

def pinyinToGlobasa(word):
    output = ""
    i = 0
    while i < len(word):
        if word[i] == "s" and i + 1 < len(word) and word[i+1] == "h":
            output += "x"
            i += 1
        elif word[i] == "c" and i + 1 < len(word) and word[i + 1] == "h":
            output += "c"
            i += 1
        elif word[i] == "z" and i + 1 < len(word) and word[i + 1] == "h":
            output += "j"
            i += 1
        elif word[i] == "w" and i + 1 < len(word) and (word[i + 1] == "u"):
            output += "u"
            i += 1
        elif word[i] == "y" and i + 1 < len(word) and (word[i + 1] == "i"):
            output += "i"
            i += 1
        elif word[i] == "u" and i + 1 < len(word) and (word[i + 1] == "i" or word[i + 1] == "n"):
            output += "we"
        elif word[i] == "u" and i + 1 < len(word) and (word[i + 1] == "a" or word[i + 1] == "o"):
            output += "w"
        elif word[i] == "o" and i > 0 and (word[i - 1] == "a" or word[i - 1] == "o"):
            output += "w"
            i += 1
        elif word[i] == "i" and i > 0 and (word[i - 1] == "a" or word[i - 1] == "u" or word[i - 1] == "e"):
            output += "y"
            i += 1
        elif word[i] == "q":
            output += "c"
        else:
            output += word[i]
        i += 1
    return output

def vietnameseToGlobasa(word):
    output = ""
    i = 0
    detoned = unidecode(word)
    while i < len(word):
        if word[i].lower() == "s" and i + 1 < len(word) and word[i+1] == "h":
            output += "x"
            i += 1
        elif word[i].lower() == "c" and i + 1 < len(word) and word[i+1] == "h":
            output += "c"
            i += 1
        elif word[i].lower() == "p" and i + 1 < len(word) and word[i+1] == "h":
            output += "f"
            i += 1
        elif word[i].lower() == "t" and i + 1 < len(word) and word[i + 1] == "h":
            output += "t"
            i += 1
        elif word[i].lower() == "k" and i + 1 < len(word) and word[i + 1] == "h":
            output += "h"
            i += 1
        elif word[i].lower() == "g" and i + 1 < len(word) and word[i + 1] == "h":
            output += "g"
            i += 1
        elif word[i].lower() == "g" and i + 1 < len(word) and word[i + 1] == "i":
            output += "j"
            i += 1
        elif word[i].lower() == "n" and i + 1 < len(word) and word[i + 1] == "h":
            output += "ny"
            i += 1
        elif detoned[i].lower() == "u" and i + 1 < len(word) and detoned[i + 1] == "y":
            output += "wi"
            i += 1
        elif word[i] == "o" and i > 0 and (detoned[i - 1] == "a" or detoned[i - 1] == "e"):
            output += "w"
        elif word[i] == "u" and i > 0 and (word[i - 1] in vowels):
            output += "w"
        elif word[i] == "o" and i + 1 < len(word) and (detoned[i + 1] == "a" or detoned[i + 1] == "e" or detoned[i + 1] == "ă"):
            output += "w"
        elif word[i] == "u" and i + 1 < len(word) and i > 0 and (detoned[i + 1] in vowels) and (detoned[i + 1] != "a") and (detoned[i + 1] != "i") and (detoned[i - 1] != "q"):
            output += "u"
        elif word[i] == "u" and i + 1 < len(word) and (detoned[i + 1] in vowels):
            output += "w"
        elif detoned[i] == "y" and i > 0 and (detoned[i - 1] in vowels) and (detoned[i - 1] != "u"):
            output += "y"
        elif detoned[i] == "i" and i > 0 and (detoned[i - 1] in vowels):
            output += "y"
        elif word[i].lower() == "y":
            output += "i"
        elif word[i].lower() == "c":
            output += "k"
        elif word[i].lower() == "d":
            output += "j"
        elif word[i].lower() == "đ":
            output += "d"
        elif word[i].lower() == "q":
            output += "k"
        else:
            output += word[i]
        i += 1
    return output

def koreanToGlobasa(word):
    output = ""
    i = 0
    while i < len(word):
        if word[i].lower() == "c" and i + 1 < len(word) and word[i + 1] == "h":
            output += "c"
            i += 1
        elif word[i].lower() == "e" and i + 1 < len(word) and word[i + 1] == "u":
            output += "u"
            i += 1
        elif word[i].lower() == "e" and i + 1 < len(word) and word[i + 1] == "o":
            output += "ə"
            i += 1
        else:
            output += word[i]
        i += 1
    return output

def hepburnToGlobasa(word):
    output = ""
    i = 0
    while i < len(word):
        if word[i].lower() == "s" and i + 1 < len(word) and word[i+1] == "h":
            output += "x"
            i += 1
        elif word[i].lower() == "c" and i + 1 < len(word) and word[i + 1] == "h":
            output += "c"
            i += 1
        else:
            output += word[i]
        i += 1
    return output

def germanToGlobasa(word):
    output = ""
    i = 0
    while i < len(word):
        if word[i].lower() == "s" and i + 2 < len(word) and word[i+1] == "c" and word[i+2] == "h":
            output += "x"
            i += 2
        elif word[i].lower() == "c" and i + 1 < len(word) and word[i + 1] == "h":
            output += "h"
            i += 1
        elif word[i].lower() == "t" and i + 3 < len(word) and word[i+1] == "s" and word[i+2] == "c" and word[i+3] == "h":
            output += "c"
            i += 3
        elif word[i].lower() == "d" and i + 3 < len(word) and word[i+1] == "s" and word[i+2] == "c" and word[i+3] == "h":
            output += "j"
            i += 3
        elif word[i].lower() == "e" and i + 1 < len(word) and word[i+1] == "i":
            output += "ay"
            i += 1
        elif word[i].lower() == "e" and i + 1 < len(word) and word[i+1] == "h":
            output += "ey"
            i += 1
        elif word[i].lower() == "a" and i + 1 < len(word) and word[i+1] == "h":
            output += "a"
            i += 1
        elif word[i].lower() == "i" and i + 1 < len(word) and word[i+1] == "e":
            output += "i"
            i += 1
        elif word[i].lower() == "s" and i + 1 < len(word) and (word[i + 1] == "t" or word[i + 1] == "p" or word[i + 1] == "k"):
            output += "x"
        elif word[i].lower() == "z":
            output += "tz"
        elif word[i].lower() == "j":
            output += "y"
        elif word[i].lower() == "w":
            output += "v"
        else:
            output += word[i]
        i += 1
    return output

def englishToGlobasa(word):
    output = ""
    i = 0
    while i < len(word):
        if word[i].lower() == "s" and i + 2 < len(word) and word[i+1] == "h":
            output += "x"
            i += 1
        elif word[i].lower() == "c" and i + 1 < len(word) and word[i + 1] == "h":
            output += "c"
            i += 1
        elif word[i].lower() == "t" and i + 1 < len(word) and word[i+1] == "h":
            output += "t"
            i += 1
        elif word[i].lower() == "a" and i + 1 < len(word) and word[i+1] == "i":
            output += "ey"
            i += 1
        elif word[i].lower() == "e" and i + 1 < len(word) and word[i+1] == "i":
            output += "ey"
            i += 1
        elif word[i].lower() == "e" and i + 1 < len(word) and word[i+1] == "a":
            output += "i"
            i += 1
        elif word[i].lower() == "e" and i + 1 < len(word) and word[i+1] == "e":
            output += "i"
            i += 1
        elif word[i].lower() == "o" and i + 1 < len(word) and word[i+1] == "o":
            output += "u"
            i += 1
        elif word[i].lower() == "o" and i + 1 < len(word) and word[i+1] == "o":
            output += "u"
            i += 1
        elif word[i].lower() == "o" and i + 1 < len(word) and word[i+1] == "o":
            output += "u"
            i += 1
        elif word[i].lower() == "a" and (i + 2 <= len(word)-1 and (word[i+2] in vowels) or (i + 3 == len(word)-1 and (word[i+1] == "s") and (word[i+2] == "t") and (word[i+3] in vowels)) ):
            output += "ey"
        elif word[i].lower() == "e" and i + 2 <= len(word)-1 and word[i+2] in vowels:
            output += "i"
        elif word[i].lower() == "u" and i + 2 <= len(word)-1 and word[i+2] in vowels:
            output += "yu"
        elif word[i].lower() == "u" and i + 2 <= len(word)-1 and word[i+2] in vowels:
            output += "yu"
        elif word[i].lower() == "i" and i + 2 <= len(word)-1 and word[i+2] in vowels:
            output += "ay"
        elif word[i].lower() == "q" and i + 2 == len(word)-1 and word[i+1] == "u" and word[i+2] == "e":
            output += "k"
            i += 2
        elif word[i].lower() == "g" and i + 2 == len(word)-1 and word[i+1] == "u" and word[i+2] == "e":
            output += "g"
            i += 2
        elif word[i].lower() == "q" and i + 1 < len(word) and word[i+1] == "u":
            output += "kw"
            i += 1
        elif word[i].lower() == "d" and i + 2 < len(word) and word[i + 1] == "g" and word[i + 2] == "e":
            output += "j"
            i += 2
        elif word[i].lower() == "g" and i + 1 < len(word) and word[i+1] == "u" and word[i+2] == "a":
            output += "g"
            i += 1
        elif word[i].lower() == "g" and i + 1 < len(word) and word[i+1] == "u" and word[i+2] == "a":
            output += "g"
            i += 1
        elif word[i].lower() == "g" and i + 1 < len(word) and (word[i + 1] == "e" or word[i + 1] == "i"):
            output += "j"
        elif word[i].lower() == "c" and i + 1 < len(word) and (word[i + 1] == "e" or word[i + 1] == "i"):
            output += "c"
        elif word[i].lower() == "c":
            output += "k"
        elif i == len(word)-1 and word[i].lower() == "e":
            output += ""
        else:
            output += word[i]
        i += 1
    return output


def frenchToGlobasa(word):
    output = ""
    i = 0
    while i < len(word):
        if word[i].lower() == "s" and i + 2 < len(word) and word[i+1] == "h":
            output += "x"
            i += 1
        elif word[i].lower() == "c" and i + 1 < len(word) and word[i + 1] == "h":
            output += "x"
            i += 1
        elif word[i].lower() == "t" and i + 2 < len(word) and word[i + 1] == "c" and word[i + 2] == "h":
            output += "c"
            i += 2
        elif word[i].lower() == "t" and i + 1 < len(word) and word[i+1] == "h":
            output += "t"
            i += 1
        elif word[i].lower() == "q" and i + 2 == len(word)-1 and word[i+1] == "u" and word[i+2] == "e":
            output += "k"
            i += 2
        elif word[i].lower() == "g" and i + 2 == len(word)-1 and word[i+1] == "u" and word[i+2] == "e":
            output += "g"
            i += 2
        elif word[i].lower() == "a" and i + 2 < len(word) and word[i+1] == "ï" and word[i+2] in vowels:
            output += "ay"
            i += 1
        elif word[i].lower() == "a" and i + 1 < len(word) and word[i+1] == "ï":
            output += "ai"
            i += 1
        elif word[i].lower() == "a" and i + 1 < len(word) and word[i+1] == "ë":
            output += "ae"
            i += 1
        elif word[i].lower() == "a" and i + 1 < len(word) and word[i+1] == "i":
            output += "e"
            i += 1
        elif word[i].lower() == "é":
            output += "ey"
        elif word[i].lower() == "e" and i + 2 < len(word) and word[i+1] == "a" and word[i+2] == "u":
            output += "ew"
            i += 2
        elif word[i].lower() == "a" and i + 1 < len(word) and word[i+1] == "u":
            output += "aw"
            i += 1
        elif word[i].lower() == "e" and i + 1 < len(word) and (word[i+1] == "i" or word[i+1] == "î"):
            output += "e"
            i += 1
        elif word[i].lower() == "e" and i + 1 < len(word) and word[i+1] == "a":
            output += "i"
            i += 1
        elif word[i].lower() == "e" and i + 1 < len(word) and word[i+1] == "e":
            output += "i"
            i += 1
        elif word[i].lower() == "o" and i + 2 < len(word) and word[i+1] == "u" and word[i+2] in vowels:
            output += "w"
            i += 1
        elif word[i].lower() == "o" and i + 1 < len(word) and word[i+1] == "u":
            output += "u"
            i += 1
        elif word[i].lower() == "o" and i + 1 < len(word) and word[i+1] == "o":
            output += "oo"
            i += 1
        elif word[i].lower() == "o" and i + 1 < len(word) and word[i+1] == "o":
            output += "u"
            i += 1
        elif i == len(word)-2 and word[i].lower() == "u" and (word[i+1] == "e"):
            output += "yu"
            i += 1
        elif word[i].lower() == "u" and i + 1 < len(word) and (word[i+1] == "e"):
            output += "we"
            i += 1
        elif word[i].lower() == "o" and i + 1 < len(word) and (word[i+1] == "i" or word[i+1] == "î"):
            output += "wa"
            i += 1
        elif word[i].lower() == "e" and i + 2 < len(word) and word[i+1] == "o" and word[i+1] == "i":
            output += "wa"
            i += 2
        elif word[i].lower() == "o" and i + 1 < len(word) and (word[i+1] == "ï"):
            output += "oi"
            i += 1
        elif word[i].lower() == "y" and i + 1 < len(word) and word[i+1] in vowels and not ():
            output += "y"
        elif word[i].lower() == "i" and i + 1 < len(word) and word[i+1] in vowels:
            output += "y"
        elif word[i].lower() == "q" and i + 1 < len(word) and word[i+1] == "u":
            output += "kw"
            i += 1
        elif word[i].lower() == "g" and i + 1 < len(word) and word[i+1] == "u" and word[i+2] == "a":
            output += "g"
            i += 1
        elif word[i].lower() == "g" and i + 1 < len(word) and word[i+1] == "u" and word[i+2] == "a":
            output += "g"
            i += 1
        elif word[i].lower() == "g" and i + 1 < len(word) and (word[i + 1] == "e" or word[i + 1] == "i"):
            output += "j"
        elif word[i].lower() == "c" and i + 1 < len(word) and (word[i + 1] == "e" or word[i + 1] == "i"):
            output += "c"
        elif word[i].lower() == "c":
            output += "k"
        elif word[i].lower() == "y":
            output += "i"
        elif word[i].lower() == "è" or word[i].lower() == "ê":
            output += "e"
        elif i == len(word)-1 and word[i].lower() == "e":
            output += ""
        elif i == len(word)-1 and word[i].lower() == "x":
            output += "s"
        elif word[i].lower() == "x":
            output += "ks"
        else:
            output += word[i]
        i += 1
    return output


def turkishToGlobasa(word):
    output = ""
    i = 0
    while i < len(word):
        if word[i].lower() == "c":
            output += "j"
        elif word[i].lower() == "ç":
            output += "c"
        elif word[i].lower() == "ş":
            output += "x"
        elif word[i].lower() == "ğ":
            if i >= 1 and word[i-1] == "e":
                output += "j"
            else:
                output += ""
        else:
            output += word[i]
        i += 1
    return output
