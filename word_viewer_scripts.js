// Alternative script transliterators for Globasa
// Based on Cyrillic for Globasa.py and Musa for Globasa.py
// from /home/paleos/PycharmProjects/LanguageTools/

const UNSTRESSED_FUNCTION_WORDS = new Set([
  "ji", "or", "nor", "kam", "mas", "kwas", "he",
  "ki", "fe", "le", "na", "xa", "ger", "no", "el", "de", "tas",
  "tem", "kom"
]);

function isGlbVowel(c) {
  return "aeiou".includes(c);
}

// Compute stressed syllable index (counting vowels from end, 0-indexed)
// Returns -1 if unstressed (monosyllabic or function word)
function glbStressedSyllable(wordLower) {
  let nSyl = 0;
  for (const c of wordLower) if (isGlbVowel(c)) nSyl++;
  if (nSyl <= 1) return -1;
  return isGlbVowel(wordLower[wordLower.length - 1]) ? 1 : 0;
}

// ============================================================
// Latin with stress marks
// ============================================================

const STRESS_MARKS = {
  a:"\u00e1", e:"\u00e9", i:"\u00ed", o:"\u00f3", u:"\u00fa",
  A:"\u00c1", E:"\u00c9", I:"\u00cd", O:"\u00d3", U:"\u00da"
};

function toLatinStressed(word) {
  const w = word.toLowerCase();
  if (UNSTRESSED_FUNCTION_WORDS.has(w)) return word;
  const target = glbStressedSyllable(w);
  if (target < 0) return word;
  let vowelNo = 0, result = "";
  for (let i = word.length - 1; i >= 0; i--) {
    if (isGlbVowel(w[i])) {
      result = (vowelNo === target ? (STRESS_MARKS[word[i]] || word[i]) : word[i]) + result;
      vowelNo++;
    } else {
      result = word[i] + result;
    }
  }
  return result;
}

// ============================================================
// Cyrillic (from Cyrillic for Globasa.py)
// ============================================================

const CYR = {
  a:"\u0430",e:"\u0435",i:"\u0438",o:"\u043e",u:"\u0443",
  p:"\u043f",b:"\u0431",c:"\u0447",j:"\u0436",t:"\u0442",
  d:"\u0434",k:"\u043a",g:"\u0433",f:"\u0444",s:"\u0441",
  x:"\u0448",h:"\u0445",v:"\u0432",z:"\u0437",r:"\u0440",
  l:"\u043b",m:"\u043c",n:"\u043d",y:"\u0439",w:"\u045e",
  A:"\u0410",E:"\u0415",I:"\u0418",O:"\u041e",U:"\u0423",
  P:"\u041f",B:"\u0411",C:"\u0427",J:"\u0416",T:"\u0422",
  D:"\u0414",K:"\u041a",G:"\u0413",F:"\u0424",S:"\u0421",
  X:"\u0428",H:"\u0425",V:"\u0412",Z:"\u0417",R:"\u0420",
  L:"\u041b",M:"\u041c",N:"\u041d",Y:"\u0419",W:"\u040e"
};

const CYR_IOT = {
  a:"\u044f", e:"\u0439\u0435", i:"\u0439\u0438", o:"\u0439\u043e", u:"\u044e"
};
const CYR_IOT_UP = {
  A:"\u042f", E:"\u0419\u0435", I:"\u0419\u0438", O:"\u0419\u043e", U:"\u042e"
};

function toCyrillic(word) {
  const w = word.toLowerCase();
  const unstressed = UNSTRESSED_FUNCTION_WORDS.has(w);
  const target = unstressed ? -1 : glbStressedSyllable(w);
  let vowelNo = 0, result = "";
  for (let i = word.length - 1; i >= 0; i--) {
    const ch = word[i], cl = w[i];
    if (!(ch in CYR)) { result = ch + result; continue; }
    if (isGlbVowel(cl)) {
      let vc;
      if (i > 0 && w[i-1] === "y") {
        vc = (word[i-1] === "Y" ? CYR_IOT_UP[ch] : CYR_IOT[cl]) || CYR[ch];
        i--;
      } else {
        vc = CYR[ch];
      }
      result = (vowelNo === target ? vc + "\u0301" : vc) + result;
      vowelNo++;
    } else {
      result = CYR[ch] + result;
    }
  }
  return result;
}

// ============================================================
// Musa (from Musa for Globasa.py)
// Codepoints in Unicode Private Use Area
// ============================================================

const MUSA = {
  a:"\uE0EC",e:"\uE0C4",i:"\uE0DC",o:"\uE0BC",u:"\uE0AC",
  p:"\uE216",b:"\uE192",c:"\uE210",j:"\uE18C",
  t:"\uE208",d:"\uE184",k:"\uE20E",g:"\uE18A",
  f:"\uE298",s:"\uE299",x:"\uE294",h:"\uE292",
  v:"\uE1BC",z:"\uE1BD",r:"\uE2CE",l:"\uE142",
  m:"\uE124",n:"\uE116",y:"\uE111",w:"\uE10B"
};

const MUSA_STRESS = {
  a:"\uE0E8",e:"\uE0C0",i:"\uE0D8",o:"\uE0B8",u:"\uE0A8"
};

const MUSA_ENGMA  = "\uE11C"; // ŋ
const MUSA_TRILL  = "\uE2DB"; // r (trilled)
const MUSA_BREAK  = "\uE100"; // syllable break
const MUSA_SPACE  = "\uE040"; // word space
const MUSA_PERIOD = "\uE042\uE040\uE040"; // .
const MUSA_QUEST  = "\uE048\uE040\uE040"; // ?
const MUSA_COMMA  = "\uE048\uE040"; // ,

function toMusa(word) {
  const w = word.toLowerCase();
  const unstressed = UNSTRESSED_FUNCTION_WORDS.has(w);
  const target = unstressed ? -1 : glbStressedSyllable(w);
  let vowelNo = 0, result = "";
  for (let i = w.length - 1; i >= 0; i--) {
    if (isGlbVowel(w[i])) {
      const vc = (vowelNo === target) ? (MUSA_STRESS[w[i]] || MUSA[w[i]]) : MUSA[w[i]];
      result = (vc || w[i]) + result;
      vowelNo++;
      // Syllable break between consecutive vowels
      if (i > 0 && isGlbVowel(w[i-1])) {
        result = MUSA_BREAK + result;
      }
    } else if (w[i] === "n" && i + 1 < w.length && (w[i+1] === "g" || w[i+1] === "k")) {
      result = MUSA_ENGMA + result;
    } else if (w[i] === "r" && i > 0 && w[i-1] === "r") {
      result = MUSA_TRILL + result;
      i--;
    } else {
      result = (MUSA[w[i]] || w[i]) + result;
    }
  }
  return result;
}

// ============================================================
// Script registry and API
// ============================================================

const SCRIPTS = {
  "Latin":            { fn: null },
  "Latin (stressed)": { fn: toLatinStressed },
  "Cyrillic":         { fn: toCyrillic },
  "Musa":             { fn: toMusa },
};

let activeScript = "Latin";

function convertScript(word) {
  const s = SCRIPTS[activeScript];
  if (!s || !s.fn) return word;
  return s.fn(word);
}

function convertScriptSentence(sentence) {
  if (activeScript === "Latin") return sentence;
  // Convert alphabetic words, preserve whitespace and punctuation
  return sentence.replace(/[a-zA-Z]+/g, match => convertScript(match));
}
