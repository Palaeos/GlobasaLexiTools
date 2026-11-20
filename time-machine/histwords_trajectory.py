# Script tier: decade-by-decade sense trajectory of chosen English words in HistWords (1800-1990),
# to suggest the year ranges for year-keyed eng->glb choices (e.g. queer -> kwir, man -> insan).
# Per decade: mean cosine similarity of the word to each probe set (one set per sense; the probe
# words stand for that sense), plus the word's nearest neighbours. Similarities are within one
# decade, so no alignment is needed. A probe word missing in a decade is skipped.
#
# Caveat: one vector per word and decade mixes all its senses, so the curves show which sense
# DOMINATES the decade's books, not whether one sentence uses it. Google Books eng-all also
# ends in the 1990s decade: anything after ~2000 needs other evidence (Wiktionary dated quotations).
#
# Output: histwords_trajectory.tsv (word, sense, decade, sim, n_probes) and
# histwords_neighbours.tsv (word, decade, count, neighbours).

import os

import numpy as np

import histwords as hw

HERE = os.path.dirname(os.path.abspath(__file__))

PROBES = {
    "queer": {
        "strange (glb: ajabu)": ["strange", "odd", "peculiar", "curious", "eccentric", "uncanny"],
        "homosexual / LGBT (glb: samajensifil; reclaimed umbrella = kwir)": ["homosexual", "homosexuals", "lesbian", "lesbians", "homosexuality", "transgender"],
        "counterfeit (slang)": ["counterfeit", "forged", "coin", "coins"],
    },
    "man": {
        "human being (glb: insan)": ["human", "mankind", "humanity", "humans", "humankind", "creature", "mortal"],
        "adult male (glb: manixu)": ["woman", "husband", "gentleman", "fellow", "lady"],
    },
    "men": {
        "people (glb: insan)": ["people", "humans", "persons", "mankind", "humanity", "mortals"],
        "adult males (glb: manixu)": ["women", "husbands", "gentlemen", "fellows", "ladies"],
    },
    "mankind": {
        "humanity (glb: insanlari)": ["humanity", "humankind", "human", "race"],
        "males": ["men", "males", "masculine", "husbands"],
    },
    "gay": {
        "cheerful (glb: kweho)": ["cheerful", "merry", "lively", "joyous", "bright", "frivolous"],
        "homosexual (glb: gey, samajensifil)": ["homosexual", "homosexuals", "lesbian", "lesbians", "homosexuality"],
    },
}

with open(os.path.join(HERE, "histwords_trajectory.tsv"), "w", encoding="utf-8") as ft, \
        open(os.path.join(HERE, "histwords_neighbours.tsv"), "w", encoding="utf-8") as fn:
    ft.write("word\tsense\tdecade\tsim\tn_probes\n")
    fn.write("word\tdecade\tcount\tneighbours\n")
    for word, senses in PROBES.items():
        for d in hw.DECADES:
            _, index, _, counts = hw.load(d)
            if word not in index:
                continue
            for sense, probes in senses.items():
                s = [hw.sim(d, word, p) for p in probes]
                s = [x for x in s if x is not None]
                if s:
                    ft.write(f"{word}\t{sense}\t{d}\t{np.mean(s):.3f}\t{len(s)}\n")
            nn = ", ".join(w for w, _ in hw.neighbours(d, word, 12))
            fn.write(f"{word}\t{d}\t{counts.get(word, 0)}\t{nn}\n")
