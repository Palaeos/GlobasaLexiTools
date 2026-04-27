


unstressed_function_words = [
    "ji", "or", "nor", "kam", "mas", "kwas", "he",
    "ki", "fe", "le", "na", "xa", "ger", "no", "el", "de", "tas",
    "tem", "kom"
]


stressed_vowels = {
    'a': "á",  # /ä/
    'e': "é",  # /e̞/
    'i': "í",  # /i/
    'o': "ó",  # /o̞/
    'u': "ú",   # /u/
    'A': "Á",  # /ä/
    'E': "É",  # /e̞/
    'I': "Í",  # /i/
    'O': "Ó",  # /o̞/
    'U': "Ú"  # /u/
}

def isVowel(c):
  return (c == 'a') or (c == 'e') or (c == 'i') or (c == 'o') or (c == 'u')


def globasaCountSyllables(sentence: str):
  output = ""

  no_syllables = 0

  for word in sentence.split():
    if word[0].isalpha():
        test_word = word.lower()
        for char in test_word:
            if isVowel(char):
                no_syllables += 1


  return no_syllables

def globasaStressSentence(sentence: str):
  output = ""

  if globasaCountSyllables(sentence) == 1:
      return sentence

  for word in sentence.split():
    if word[0].isalpha():
        output += globasaStressWord(word) + ' '
    else:
      output += word + ' '

  return output.strip()

def globasaStressWord(word: str, unstressed=False):
  output = ""
  test_word = word.lower()

  if word in unstressed_function_words:
    unstressed = True

  # Implementation of Globasa stress rule:
  vowel_no = 0

  stressed_syllable = None

  # First we check if the word is monosyllabic
  no_syllables = 0
  for char in test_word:
    if isVowel(char):
      no_syllables += 1


  if (no_syllables != 1) and isVowel(word[-1]):
    stressed_syllable = 1
  else:
    stressed_syllable = 0
  i = len(word) - 1

  while i >= 0:
    if isVowel(test_word[i]):
      if vowel_no == stressed_syllable and not unstressed:
        output = stressed_vowels[word[i]] + output
      else:
        output = word[i] + output
      vowel_no += 1
    else:
        output = word[i] + output

    i -= 1
  return output