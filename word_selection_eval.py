"""Word Selector evaluation against the official lexicon.

  venv/bin/python word_selection_eval.py translit [lang]   per-language transliteration accuracy
  venv/bin/python word_selection_eval.py roots [oracle|e2e] [N]   leave-one-out root proposals

translit: gold = LexiliAsel romanizations (already in Globasa letters) for
non-Latin scripts; input = the word's Wiktionary romanization/IPA from
WiktionaryLMDB_concepts (or a library romanizer when absent). Spaces ignored.
"""

import collections
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from word_selection import lexicon, translit
from word_selection.align import distance
from word_selection.concept_index import ConceptIndex
from word_selection.languages import BY_CODE

MODE = sys.argv[1] if len(sys.argv) > 1 else "translit"


def lookup_pron(ix, lang, word):
    roman, ipa = "", ""
    for e in ix.entries(BY_CODE[lang]["dump"], word):
        if not roman and e["roman"]:
            roman = e["roman"][0]
        if not ipa and e["ipa"]:
            ipa = e["ipa"][0][0]
    return roman, ipa


def eval_translit(only=None):
    ix = ConceptIndex()
    by_lang = collections.defaultdict(list)
    for r in lexicon.roots():
        for e in r["etymons"]:
            if e["code"] in BY_CODE and e["roman"]:
                by_lang[e["code"]].append(e)
    print(f"{'lang':5} {'n':>5} {'exact':>6} {'mean d':>7} {'no input':>8}")
    for lang, items in sorted(by_lang.items()):
        if only and lang != only:
            continue
        exact, dist, missing, errors = 0, 0.0, 0, []
        for e in items:
            word = e["word"].lstrip("/ ").strip()
            roman, ipa = lookup_pron(ix, lang, word)
            forms = translit.to_globasa(lang, word, roman, ipa)
            gold = e["roman"].replace(" ", "")
            if not forms:
                missing += 1
                continue
            got = forms[0][0].replace(" ", "")
            d = distance(got, gold)
            dist += d
            if got == gold:
                exact += 1
            else:
                errors.append((d, word, roman, got, gold))
        n = len(items) - missing
        print(f"{lang:5} {len(items):5} {exact / max(n, 1):6.1%} {dist / max(n, 1):7.2f} {missing:8}")
        if only:
            random.seed(1)
            for d, word, roman, got, gold in sorted(random.sample(errors, min(40, len(errors))), reverse=True):
                print(f"   {d:4.1f}  {word:14} {roman:18} got {got:16} gold {gold}")


if MODE == "translit":
    eval_translit(sys.argv[2] if len(sys.argv) > 2 else None)
elif MODE == "roots":
    from word_selection.pipeline import evaluate_roots
    evaluate_roots(sys.argv[2] if len(sys.argv) > 2 else "oracle",
                   int(sys.argv[3]) if len(sys.argv) > 3 else None)
