"""
Harvest gold, dev and coverage sets for the Globasa-Spanish and Globasa-Esperanto
Apertium pairs (apertium-glb-spa, apertium-glb-epo).

A corpus is a translation reference only in the direction it was really translated:
  - Xwexi (xwexi-pages-grav *.spa.md / *.epo.md): Globasa teaching examples with
    Spanish/Esperanto glosses -> grammar regression, both directions.
  - Hikaye fal Vanege (TMX): Esperanto originals translated into Globasa -> epo->glb
    dev (stories 1-10) and held-out test (stories 11-13).
  - Towa Babel (TMX): Globasa translated from a Spanish Bible -> spa->glb gold.
  - Pepper & Carrot (French original) and the UDHR (English original): Spanish,
    Esperanto and Globasa are sibling translations -> source-side coverage text only.

Output: parallel_gold_cache/{spa,epo}/ (git-ignored; Xwexi, Vanege and the Babel
Spanish are not openly licensed). TSV lines are "source<TAB>gold | alt", the
format of GlobasaTranslation/apertium-glb-*/test/check-gold.sh; '#' lines are
comments naming the Xwexi page and heading.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
XWEXI = ROOT / "xwexi-pages-grav"
TMX = ROOT / "Doxo_passages_extended.tmx"
OUT = ROOT / "parallel_gold_cache"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

LANGS = {"spa": "es", "epo": "eo"}          # Apertium code -> TMX code
VOCAB_HEADINGS = re.compile(r"vocabul|vortlist|lexilista", re.I)
VANEGE_TEST_FROM = 11                       # stories 11.. are held out

EXAMPLE = re.compile(r"^\*\*(?P<glb>[^*]+?)\*\*\s*$")
PHRASE = re.compile(r"^\s*\*\s+\*\*(?P<glb>[^*]+?)\*\*\s+-\s+(?P<tr>.+?)\s*$")


def clean(text):
    """Strip markdown emphasis, HTML and surplus whitespace."""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"(?<!\w)[_*]+|[_*]+(?!\w)", "", text)
    if text.count(")") > text.count("("):          # source typo, e.g. "amikoj)!"
        text = text.replace(")", "", text.count(")") - text.count("("))
    return " ".join(text.split())


ENGLISH = {"the", "this", "that", "these", "those", "an", "is", "are", "i", "you", "he",
           "she", "it", "we", "they", "of", "and", "have", "has", "one", "my", "your", "with"}
ALT_SPLIT = re.compile(r"(?:[.,;]\s+|\s+)(?:o|aŭ|or)\s+(?=[¡¿\"“]?[A-ZÁÉÍÓÚÑĈĜĤĴŜŬ])")


EPO_FUNCTION = {"kaj", "ne", "sed", "kun", "por", "de", "al", "el", "en", "je", "ke", "kiu", "mi",
                "vi", "li", "ŝi", "ĝi", "ni", "ili", "ri", "la", "tre", "nur", "jen", "ĉu", "jes",
                "pli", "ol", "tro", "ĉar", "kiel", "sur", "sub", "post", "dum", "per", "pro", "kiam"}
EPO_ENDING = re.compile(r"(?:[aeiou]|[oa]jn?|[oa]n|[aiou]s|aŭ)$")


def looks_english(text, lang):
    """Untranslated English left on a Spanish/Esperanto page. Esperanto is checked by
    word shape (endings, function words); Spanish by English function words."""
    words = re.findall(r"[^\W\d_]+", text.lower())
    if not words:
        return False
    if lang == "epo":
        # Esperanto has no w/y/q/x; any English function word gives the gloss away
        if any(re.search(r"[wyqx]", w) or w in ENGLISH or w in ("was", "don", "on", "down")
               for w in words):
            return True
        epo_like = sum(w in EPO_FUNCTION or bool(EPO_ENDING.search(w)) for w in words)
        return epo_like / len(words) < 0.6
    return sum(w in ENGLISH for w in words) / len(words) >= 0.3


def variants(translation):
    """Gold alternatives for a gloss.
    'Yo leo, o Estoy leyendo.' -> two sentences; 'amigo(s)' -> amigo / amigos;
    '(Ése) es un pez.' -> with and without the optional part;
    'El pez/los peces nada' -> all-first and all-second readings of the slashes.
    Returns [] for open-ended glosses ('etc.')."""
    if re.search(r"\betc\b", translation):
        return []
    out = []
    for alt in ALT_SPLIT.split(clean(translation)):
        for opt in (re.sub(r"(?<=\w)\(([^)\s]+)\)", "", alt),         # amigo(s) -> amigo
                    re.sub(r"(?<=\w)\(([^)\s]+)\)", r"\1", alt)):     # -> amigos
            for o in (re.sub(r"\s*\([^)]*\)\s*", " ", opt),            # drop (Ése)
                      re.sub(r"[()]", "", opt)):                        # keep Ése
                for k in (0, 1):                                        # slash choices
                    v = re.sub(r"([^\s/]+)\s*/\s*([^\s/]+)", lambda m: m[1 + k], o)
                    v = re.sub(r"\s+([,.!?;:])", r"\1", " ".join(v.split()))
                    if v and v not in out:
                        out.append(v)
    shortest = min((len(v) for v in out), default=0)
    return [v for v in out if len(v) <= 2 * shortest + 20]   # drop explanations


def parse_xwexi_page(path):
    """Yield (heading, kind, globasa, translation) from one Xwexi page."""
    lines = path.read_text(encoding="utf-8").splitlines()
    heading, in_vocab, in_front = "", False, False
    i = 0
    while i < len(lines):
        line = lines[i]
        if i == 0 and line.strip() == "---":
            in_front = True
        elif in_front and line.strip() == "---":
            in_front = False
            i += 1
            continue
        if in_front:
            i += 1
            continue
        if line.startswith("#"):
            heading = clean(line.lstrip("#"))
            in_vocab = bool(VOCAB_HEADINGS.search(heading))
        elif m := EXAMPLE.match(line):
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and not re.match(r"\s*([*#<!|]|---)", lines[j]):
                yield heading, "sentence", clean(m["glb"]), lines[j].strip()
                i = j
        elif line.lstrip().startswith("|"):
            # table cells: **Globasa.**<br />gloss<br />other gloss (07.falelexili-morfo)
            for cell in line.split("|"):
                for group in re.split(r"(?:<br */?>\s*){2,}", cell):
                    m = re.match(r"\s*\*\*([^*]+)\*\*\s*((?:<br */?>.*)?)$", group)
                    if not m or " " not in m[1].strip():
                        continue
                    glosses = [g.strip() for g in re.split(r"<br */?>|,\s+(?=[¡¿])", m[2])
                               if g.strip()]
                    if glosses:
                        yield heading, "table", clean(m[1]), " o ".join(glosses)
        elif not in_vocab and (m := PHRASE.match(line)):
            yield heading, "phrase", clean(m["glb"]), m["tr"]
        i += 1


def xwexi_pairs(lang):
    """Xwexi examples for one language, minus those still carrying the English
    gloss (the Esperanto pages are only partly translated)."""
    pairs = []
    for page in sorted(XWEXI.rglob(f"default.{lang}.md")):
        eng_page = page.with_name("default.eng.md")
        english = set()
        if eng_page.exists():
            english = {clean(tr) for _, _, _, tr in parse_xwexi_page(eng_page)}
        rel = str(page.parent.relative_to(XWEXI))
        for heading, kind, glb, tr in parse_xwexi_page(page):
            if clean(tr) in english or looks_english(tr, lang):
                continue        # untranslated English gloss
            if re.match(r"\s*(o|aŭ|or)\s*:", tr):
                continue        # the "gloss" is another Globasa wording
            if kind == "phrase" and " " not in glb:
                continue        # one-word vocabulary gloss: dictionary, not grammar
            if not variants(tr):
                continue        # open-ended gloss ("etc.")
            pairs.append((f"{rel} / {heading}", kind, glb, tr))
    return pairs


def tmx_units():
    """(context, {lang: text}) for every TU in the extended TMX."""
    for tu in ET.parse(TMX).iter("tu"):
        props = {p.get("type"): p.text for p in tu.iter("prop")}
        texts = {t.get(XML_LANG): " ".join("".join(t.itertext()).split())
                 for t in tu.iter("tuv")}
        yield props.get("x-context", ""), texts


def write_tsv(path, rows, header):
    """rows: (comment or None, source, [gold alternatives])."""
    path.parent.mkdir(parents=True, exist_ok=True)
    last = None
    n = 0
    with open(path, "w", encoding="utf-8") as f:
        for line in header:
            f.write(f"# {line}\n")
        for comment, src, golds in rows:
            if not src or not golds:
                continue
            if comment and comment != last:
                f.write(f"# {comment}\n")
                last = comment
            f.write(f"{src}\t{' | '.join(golds)}\n")
            n += 1
    return n


def main():
    units = list(tmx_units())
    report = []
    for code, tmx_lang in LANGS.items():
        out = OUT / code

        # Xwexi, both directions
        pairs = xwexi_pairs(code)
        # sources: one row per full alternative of the gloss, optional parts kept;
        # slash alternatives are ambiguous as source text and skipped; gold: every variant
        x2g = [(page, max(variants(alt), key=len), variants(glb))
               for page, kind, glb, tr in pairs
               for alt in ALT_SPLIT.split(clean(tr)) if "/" not in alt and variants(alt)]
        g2x = [(page, max(variants(glb), key=len), variants(tr)) for page, kind, glb, tr in pairs]
        hdr = ["Xwexi (xwexi-pages-grav) examples: Globasa written for teaching, "
               f"{code} glosses. Grammar regression; not openly licensed, keep local."]
        report.append((f"{code}-glb-xwexi.tsv", write_tsv(out / f"{code}-glb-xwexi.tsv", x2g, hdr)))
        report.append((f"glb-{code}-xwexi.tsv", write_tsv(out / f"glb-{code}-xwexi.tsv", g2x, hdr)))

        # Gold in the real translation direction only
        if code == "spa":
            rows = [("Towa Babel (Genesis 11:1-9)", t[tmx_lang], [t["glb"]])
                    for ctx, t in units if ctx == "Towa Babel" and t.get(tmx_lang)]
            hdr = ["Towa Babel: Globasa translated from a Spanish Bible (wording looks like "
                   "LBLA, copyrighted). spa->glb gold; keep local."]
            report.append(("spa-glb-babel.tsv", write_tsv(out / "spa-glb-babel.tsv", rows, hdr)))
        if code == "epo":
            dev, test, story, title = [], [], 0, ""
            for ctx, t in units:
                if ctx != "Hikaye fal Vanege" or not t.get("glb"):
                    continue
                if not re.search(r"[.!?:\"”»)…]$", t["glb"]):
                    story += 1
                    title = f"story {story}: {t['glb']} / {t.get('eo', '')}"
                    continue
                if t.get("eo"):
                    row = (title, t["eo"], [t["glb"]])
                    (test if story >= VANEGE_TEST_FROM else dev).append(row)
            hdr = ["Hikaye fal Vanege: Esperanto originals translated into Globasa. "
                   "epo->glb reference; keep local."]
            report.append(("epo-glb-vanege-dev.tsv", write_tsv(out / "epo-glb-vanege-dev.tsv", dev,
                                                               hdr + ["Stories 1-10: rule development."])))
            report.append(("epo-glb-vanege-test.tsv", write_tsv(out / "epo-glb-vanege-test.tsv", test,
                                                                hdr + ["Stories 11-13: held out, score per milestone only."])))

        # Sibling translations: source-side coverage text only
        cov = [t[tmx_lang] for ctx, t in units
               if (ctx.startswith("Pilpil ji Karote") or ctx.startswith("Globatotal Deklaradoku"))
               and t.get(tmx_lang)]
        (out / f"{code}-coverage.txt").write_text("\n".join(cov) + "\n", encoding="utf-8")
        report.append((f"{code}-coverage.txt", len(cov)))

    for name, n in report:
        print(f"{n:5d}  {name}")


main()
