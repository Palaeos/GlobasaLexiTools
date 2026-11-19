"""English variety preference for the glb->eng Apertium pair, generated from
the variety sources (never from Apertium files):

    eng_variety_patch.tsv   vocabulary pairs (autumn GB / fall US)
    VarCon                  spelling (eng_variety_cache/varcon.txt)
    word-list.csv           which English lemmas the glosses use

Writes into GlobasaTranslation/apertium-glb-eng:

    apertium-glb-eng.glb-eng.biprefs.rlx
        CG run right after lt-proc -b. When AP_SETVAR sets eng_variety
        (GB or US): SUBSTITUTE a US-spelled lemma by its British lemma (the
        English generator is the British build and cannot generate "color");
        REMOVE the other variety's word of each vocabulary pair. Unset: no
        rule fires, output is unchanged.
    glb-eng.us-spelling.tsv
        British -> American surface spellings (colour -> color, realised ->
        realized) for glb-eng-variety.py, the last step of the mode, which
        respells the output when eng_variety=US. Only spelling pairs: both
        forms on one VarCon line, string-similar (VarCon also lists
        vocabulary, and lift -> elevator must not hit the verb), and both in
        ordinary use (wordfreq Zipf >= 1.5; VarCon also lists archaic forms
        such as idaea).
    glb-eng.preferences.xml
        preference eng_variety, options GB and US (installed as
        prefs/glb-eng.xml).
    apertium-glb-eng.eng-glb.variety.rlx, eng-glb.variety.preferences.xml
        eng->glb, the same vocabulary pairs read as input: a word that is
        US-only for a Globasa word (fall -> xuhamosem "autumn") is a wrong
        reading of British input, and vice versa. REMOVE fires for
        eng_variety=GB/US, and the British rules also for
        eng_variety=Victorian and any AP_SETVAR victorian (Victorian English
        is British English). Victorian is an option of the input variety only;
        glb->eng generates GB or US. The pair's
        Makefile concatenates these with the Victorian fragments
        (time-machine/termbase_to_apertium.py).

    python3 eng_variety_to_apertium.py && (cd GlobasaTranslation/apertium-glb-eng && make)
    echo "Mi vole kolor." | AP_SETVAR=eng_variety=US apertium -d GlobasaTranslation/apertium-glb-eng glb-eng
"""
import csv
import difflib
import re
from collections import defaultdict
from pathlib import Path

PAIR = Path("GlobasaTranslation/apertium-glb-eng")
VARCON = Path("eng_variety_cache/varcon.txt")
PATCH = Path("eng_variety_patch.tsv")
RLX = PAIR / "apertium-glb-eng.glb-eng.biprefs.rlx"
SPELL = PAIR / "glb-eng.us-spelling.tsv"
PREFS = PAIR / "glb-eng.preferences.xml"
IN_RLX = PAIR / "apertium-glb-eng.eng-glb.variety.rlx"
IN_PREFS = PAIR / "eng-glb.variety.preferences.xml"

if not VARCON.exists():
    raise SystemExit("run apply_eng_variety.py first (it downloads VarCon)")

# ---- VarCon: per line, British-only and American-only forms
us_to_gb, gb_to_us = defaultdict(set), defaultdict(set)
for line in VARCON.read_text(encoding="utf-8", errors="replace").splitlines():
    if not line or line.startswith("#"):
        continue
    forms = []
    for part in line.split("|")[0].split("/"):
        if ":" not in part:
            continue
        tags, word = part.split(":", 1)
        pref = {t for t in tags.split() if t in ("A", "B", "Z")}
        forms.append((word.strip(), pref))
    gb = [w for w, p in forms if "B" in p and "A" not in p]
    us = [w for w, p in forms if "A" in p and "B" not in p]
    for g in gb:
        for u in us:
            if " " in g or " " in u or difflib.SequenceMatcher(None, g.lower(), u.lower()).ratio() < 0.6:
                continue  # vocabulary, not spelling
            gb_to_us[g.lower()].add(u.lower())
            us_to_gb[u.lower()].add(g.lower())
# a form that is also preferred somewhere in the other variety is not
# variety-specific (e.g. check: A on the bank line, A B as a verb)
preferred_both = set()
for line in VARCON.read_text(encoding="utf-8", errors="replace").splitlines():
    if line and not line.startswith("#"):
        for part in line.split("|")[0].split("/"):
            if ":" in part:
                tags, word = part.split(":", 1)
                p = set(tags.split())
                if "A" in p and "B" in p:
                    preferred_both.add(word.strip().lower())
# both spellings must be in ordinary use (VarCon also lists archaic forms:
# idea / idaea would make "idea" ungenerable)
from wordfreq import zipf_frequency
MIN_ZIPF = 1.5
common = lambda w: zipf_frequency(w, "en") >= MIN_ZIPF
gb_to_us = {g: next(iter(u)) for g, u in gb_to_us.items()
            if len(u) == 1 and g not in preferred_both and common(g) and common(next(iter(u)))}
us_to_gb = {u: next(iter(g)) for u, g in us_to_gb.items()
            if len(g) == 1 and u not in preferred_both and common(u) and common(next(iter(g)))}

# ---- lemmas the glosses actually use
with open("word-list.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
gloss_words = {w.lower() for r in rows for w in re.findall(r"[A-Za-z]+", r.get("TranslationEng", ""))}
substitutions = sorted((u, g) for u, g in us_to_gb.items() if u in gloss_words)

# ---- vocabulary pairs from the patch: Word -> {variety: [items]}
vocab = defaultdict(lambda: defaultdict(list))
skipped = []
if PATCH.exists():
    with open(PATCH, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r.get("variety") not in ("GB", "US"):
                continue
            item = r["item"].strip()
            if " " in item:
                skipped.append(f"{r['Word']}: {item}")
                continue
            vocab[r["Word"].strip()][r["variety"]].append(item)

rules = []
for u, g in substitutions:
    rules.append(f'SUBSTITUTE ("{u}") ("{g}") TARGET ("{u}") IF (0 (VAR:eng_variety)) ;')
rules.append("")
for word in sorted(vocab):
    for variety, other in (("GB", "US"), ("US", "GB")):
        for item in vocab[word][other]:
            rules.append(f'REMOVE ("{item}"i) IF (0 ("<{word}>"i) + (VAR:eng_variety={variety})) ;'
                         f"  # {word}: {variety} uses {', '.join(vocab[word][variety]) or '-'}")

RLX.write_text(
    "# English variety (AP_SETVAR=eng_variety=GB|US) for glb->eng: bidix preferences.\n"
    "# Generated by eng_variety_to_apertium.py from eng_variety_patch.tsv, VarCon and\n"
    "# word-list.csv; do not edit. Unset: no rule fires.\n\n"
    'DELIMITERS = "." ;\n\n'
    "# US-spelled lemmas -> the British lemma the (British) generator knows;\n"
    "# glb-eng-variety.py respells the output for eng_variety=US\n"
    + "\n".join(rules) + "\n", encoding="utf-8")

with open(SPELL, "w", encoding="utf-8") as f:
    f.write("# British -> American spelling, from VarCon (en-wl/wordlist, permissive licence).\n"
            "# Generated by eng_variety_to_apertium.py; do not edit.\n")
    for g in sorted(gb_to_us):
        f.write(f"{g}\t{gb_to_us[g]}\n")

PREFS.write_text("""<preferences>
  <!-- Generated by eng_variety_to_apertium.py; do not edit. -->
  <preference id="eng_variety">
    <description lang="eng">English variety: British (GB) or American (US)</description>
    <long-description lang="eng">
      Spelling (colour / color, realise / realize) and vocabulary (autumn / fall,
      lorry / truck, petrol / gasoline) of the English output. Unset: the pair's
      default choices, which mix both varieties in vocabulary.
    </long-description>
    <options>
      <option id="GB"/>
      <option id="US"/>
    </options>
  </preference>
</preferences>
""", encoding="utf-8")
# ---- eng->glb: the same pairs read as input
in_rules = []
for word in sorted(vocab):
    for variety, other in (("GB", "US"), ("US", "GB")):
        for item in vocab[word][other]:
            # input in `variety`: `item` belongs to the other variety, so
            # translating it as `word` is that variety's sense
            in_rules.append(f'REMOVE ("{word}"i) IF (0 ("<{item}>"i) + (VAR:eng_variety={variety})) ;'
                            f"  # {item}: {other} sense = {word}")
            if variety == "GB":
                # Victorian English is British English
                in_rules.append(f'REMOVE ("{word}"i) IF (0 ("<{item}>"i) + (VAR:eng_variety=Victorian)) ;'
                                f"  # Victorian = British")
                in_rules.append(f'REMOVE ("{word}"i) IF (0 ("<{item}>"i) + (VAR:victorian)) ;'
                                f"  # Victorian = British")
IN_RLX.write_text(
    "# English variety of the INPUT (AP_SETVAR=eng_variety=GB|US, and victorian = British)\n"
    "# for eng->glb. Generated by eng_variety_to_apertium.py from eng_variety_patch.tsv;\n"
    "# do not edit. Concatenated with apertium-glb-eng.eng-glb.victorian.rlx by the Makefile.\n\n"
    + "\n".join(in_rules) + "\n", encoding="utf-8")
IN_PREFS.write_text("""<preferences>
  <!-- Generated by eng_variety_to_apertium.py; do not edit. -->
  <preference id="eng_variety">
    <description lang="eng">English variety of the input: British (GB), American (US) or Victorian</description>
    <long-description lang="eng">
      Read the input as British or American English where a word differs: British
      "fall" is falling, not autumn; British "gas" is not petrol. Unset: both
      readings stay available. Victorian = Victorian-era British English: the
      period senses of the Victorian word list (presently = soon) plus the GB
      readings; the same as AP_SETVAR=victorian.
    </long-description>
    <options>
      <option id="GB"/>
      <option id="US"/>
      <option id="Victorian"/>
    </options>
  </preference>
</preferences>
""", encoding="utf-8")

print(f"{len(in_rules)} eng->glb input rules; {len(substitutions)} lemma substitutions, {sum(len(v['GB']) + len(v['US']) for v in vocab.values())} "
      f"vocabulary removals, {len(gb_to_us)} respellings; multiword pairs not handled yet: {skipped}")
