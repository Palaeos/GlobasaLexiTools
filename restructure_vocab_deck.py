"""Schema changes to Globasa__Vocabulary.apkg, run before update_vocab_deck.py
picks up new AnkiList.csv columns. Extend it rather than writing another.

1. Names the six templates still called "Card 14".."Card 19", and makes the
   Nenojetoli pair spell "(-cu)" alike. update_vocab_deck.py files each card in
   a subdeck named after its template, so these names become deck names.
2. Adds the fields for plants' two pronouns. te covers "all living forms", so a
   plant word is te while it grows and to once picked or harvested
   (CanonicalSentences #149, kanabis). AnkiMaker3 already computed AloAnaphor
   and threw it away; the card showed only the first of "to, te".
3. Pornamelexi asks for Anaphor, now against the referent's label and picture
   when the word has two pronouns; the new Alo Pornamelexi asks for AloAnaphor.
   Alo Pornamelexi is conditional on AloAnaphorMena, not AloAnaphor: a dual word
   with no label (maux, Farenhayt) would be an unanswerable te-or-to card, so
   those show both pronouns on the Pornamelexi back instead.
4. Removes the "Globasa lexi SabziFruta" notetype, the prototype of (3). Its one
   note, estroberi, duplicates the regular estroberi note.
5. Separates a verb's class from its meaning (minimum information principle):
   one Verb Type card asking the frame equivalent to a plain intransitive
   ("▯ suyon" -> "▯ suyon suyon", "▯ buka" -> "▯ buka(cu)", "▯ pilo" ->
   "▯ sen pilodo", "▯ idi" -> "▯ idi (no -cu)"). The echo-object and -cu meaning cards ask and answer with
   the bare verb, as the feeling and state cards always have.

Idempotent: re-running changes nothing.
"""
import os
import shutil
import subprocess
import tempfile
import zipfile

from anki.collection import Collection, ExportAnkiPackageOptions
from anki import import_export_pb2 as pb
from anki.generic_pb2 import Empty

APKG = "Globasa__Vocabulary.apkg"
BACKUP = "Globasa__Vocabulary.apkg.pre-restructure.bak"
NOTETYPE = "Globasa lexi"
PROTOTYPE = "Globasa lexi SabziFruta"

RENAMES = {
    "Card 14": "Maxpul Kostrui 1 Rukone",
    "Card 15": "Maxpul Kostrui 2 Rukone",
    "Card 16": "Maxpul Kostrui 1 Produti",
    "Card 17": "Maxpul Kostrui 2 Produti",
    "Card 18": "Inanimate Adjective Rukone",
    "Card 19": "Animate Adjective Rukone",
    "Nenojetoli(cu) Produti": "Nenojetoli(-cu) Produti",
}

# Each group is inserted right after the field named first, in this order.
NEW_FIELDS = [
    ("Anaphor", ["AloAnaphor", "AnaphorMena", "AloAnaphorMena",
                 "AnaphorImaje", "AnaphorImajeAsel",
                 "AloAnaphorImaje", "AloAnaphorImajeAsel"]),
    ("State", ["VerbClass", "NoObjectForm"]),
]

AUDIO = """<audio autoplay>
  <source src="{{Paladoawdio}}" type="audio/mpeg">
  Your browser does not support the audio element.
</audio>"""

MENALARI = """<p><a href="https://menalari.globasa.net/eng/lexi/{{Lexi}}">
<div class= "card">Menalari</div>
</a></p>"""


def referent(prefix):
    """The label and picture telling the learner which referent is meant."""
    return f"""{{{{#{prefix}Mena}}}}<div class= "mena"><em>{{{{{prefix}Mena}}}}</em></div>{{{{/{prefix}Mena}}}}
{{{{#{prefix}Imaje}}}}
<p><a href="{{{{{prefix}ImajeAsel}}}}">
<img src="{{{{{prefix}Imaje}}}}" alt="Asel" height="250">
</a></p>
{{{{/{prefix}Imaje}}}}"""


PORNAMELEXI_FRONT = f"""{{{{#Anaphor}}}}
pornamelexi
<div class= "lexi"><h2>{{{{Lexi}}}}</h2> </div>
{referent("Anaphor")}

{AUDIO}
{{{{/Anaphor}}}}"""

# A labelled dual shows the other referent too, so every review rehearses the
# contrast; an unlabelled dual just lists both pronouns.
PORNAMELEXI_BACK = f"""pornamelexi

<div class= "lexi"><div class= "{{{{Anaphor}}}}"><h2>{{{{Lexi}}}}</h2></div></div>
{referent("Anaphor")}

<div class= "{{{{Anaphor}}}}">{{{{Anaphor}}}}</div>
{{{{#AloAnaphor}}}}
{{{{#AloAnaphorMena}}}}<div class= "mena">{{{{AloAnaphorMena}}}}: <span class= "{{{{AloAnaphor}}}}">{{{{AloAnaphor}}}}</span></div>{{{{/AloAnaphorMena}}}}
{{{{^AloAnaphorMena}}}}<div class= "{{{{AloAnaphor}}}}">{{{{AloAnaphor}}}}</div>{{{{/AloAnaphorMena}}}}
{{{{/AloAnaphor}}}}
{MENALARI}"""

ALO_PORNAMELEXI_FRONT = f"""{{{{#AloAnaphorMena}}}}
pornamelexi
<div class= "lexi"><h2>{{{{Lexi}}}}</h2> </div>
{referent("AloAnaphor")}

{AUDIO}
{{{{/AloAnaphorMena}}}}"""

ALO_PORNAMELEXI_BACK = f"""pornamelexi

<div class= "lexi"><div class= "{{{{AloAnaphor}}}}"><h2>{{{{Lexi}}}}</h2></div></div>
{referent("AloAnaphor")}

<div class= "{{{{AloAnaphor}}}}">{{{{AloAnaphor}}}}</div>
<div class= "mena">{{{{AnaphorMena}}}}: <span class= "{{{{Anaphor}}}}">{{{{Anaphor}}}}</span></div>
{MENALARI}"""


# The one Verb Type card, asked without the verb's meaning (minimum information
# principle): "▯ suyon" -> "▯ suyon suyon", "▯ buka" -> "▯ buka(cu)", "▯ pilo"
# -> "▯ sen pilodo", "▯ idi" -> "▯ idi (no -cu)" -- the frame equivalent to a
# plain intransitive. Prompt "nenhar ojeto?": nenhar = without (not having);
# wal is the general "without". The meaning cards ask and answer with the bare
# verb.
VERB_TYPE_FRONT = f"""{{{{#NoObjectForm}}}}
nenhar ojeto?
<div class= "lexi"><h2>▯ {{{{Lexi}}}}</h2> </div>

{AUDIO}
{{{{/NoObjectForm}}}}"""

VERB_TYPE_BACK = f"""nenhar ojeto?
<div class= "lexi"><h2>▯ {{{{Lexi}}}}</h2> </div>
<div class= "cell-Verb"><h3>{{{{NoObjectForm}}}}</h3></div>
<div class= "mena">{{{{VerbClass}}}}</div>
{MENALARI}"""

def unpack(apkg, workdir):
    with zipfile.ZipFile(apkg) as z:
        z.extractall(workdir)
    packed = os.path.join(workdir, "collection.anki21b")
    db = os.path.join(workdir, "collection.anki2")
    if os.path.exists(packed):
        r = subprocess.run(["zstd", "-d", packed, "-o", db, "-f"],
                           capture_output=True)
        if r.returncode != 0:
            raise RuntimeError(f"zstd failed: {r.stderr.decode()}")
        os.remove(packed)
    if not os.path.exists(db):
        raise RuntimeError(f"no collection found in {apkg}")
    return db


workdir = tempfile.mkdtemp(prefix="vocab_restructure_")
col = Collection(unpack(APKG, workdir))
mm = col.models
nt = mm.by_name(NOTETYPE)

for tmpl in nt["tmpls"]:
    if tmpl["name"] in RENAMES:
        print(f"template {tmpl['name']!r} -> {RENAMES[tmpl['name']]!r}")
        tmpl["name"] = RENAMES[tmpl["name"]]

# Earlier drafts of the Verb Type card: a yes/no Optional -cu card, then a
# No Object card beside a separate Verb Class card. One card is enough.
for field in nt["flds"]:
    if field["name"] == "OptionalCu":
        mm.rename_field(nt, field, "NoObjectForm")
        print("renamed field 'OptionalCu' -> 'NoObjectForm'")
for tmpl in nt["tmpls"]:
    if tmpl["name"] in ("Optional -cu", "No Object"):
        print(f"renamed template {tmpl['name']!r} -> 'Verb Type'")
        tmpl["name"] = "Verb Type"
for tmpl in list(nt["tmpls"]):
    if tmpl["name"] == "Verb Class":
        mm.remove_template(nt, tmpl)
        print("removed template 'Verb Class' and its cards")
for field in list(nt["flds"]):
    if field["name"] == "VerbClassNote":
        mm.remove_field(nt, field)
        print("removed field 'VerbClassNote'")

names = [f["name"] for f in nt["flds"]]
for after, group in NEW_FIELDS:
    for i, name in enumerate(group):
        if name not in names:
            field = mm.new_field(name)
            mm.add_field(nt, field)
            mm.reposition_field(nt, field, names.index(after) + 1 + i)
            names = [f["name"] for f in nt["flds"]]
            print(f"added field {name!r}")

for name, front, back in (
        ("Alo Pornamelexi", ALO_PORNAMELEXI_FRONT, ALO_PORNAMELEXI_BACK),
        ("Verb Type", VERB_TYPE_FRONT, VERB_TYPE_BACK)):
    if name not in {t["name"] for t in nt["tmpls"]}:
        mm.add_template(nt, mm.new_template(name))
        print(f"added template {name!r}")
by_name = {t["name"]: t for t in nt["tmpls"]}
for name, front, back in (
        ("Pornamelexi", PORNAMELEXI_FRONT, PORNAMELEXI_BACK),
        ("Alo Pornamelexi", ALO_PORNAMELEXI_FRONT, ALO_PORNAMELEXI_BACK),
        ("Verb Type", VERB_TYPE_FRONT, VERB_TYPE_BACK)):
    by_name[name]["qfmt"] = front
    by_name[name]["afmt"] = back

# The meaning cards of echo-object and -cu verbs ask and answer with the bare
# verb, as the Hisili and Jotayli cards always have: "swim" -> "▯ suyon", not
# "▯ suyon (suyon)", which made the learner recall the verb AND its class. The
# class lives on Verb Type: "▯ suyon" -> "▯ suyon suyon", "▯ xoru(cu)". The
# general Produti front also stops naming the class in its row labels.
BARE = [(r"<h2>▯ {{Lexi}} ({{Lexi}})</h2>", r"<h2>▯ {{Lexi}}</h2>"),
        (r"<h2>▯ {{Lexi}} ▯</h2>", r"<h2>▯ {{Lexi}}</h2>"),
        (r"<h2>▯ {{Lexi}}(cu)</h2>", r"<h2>▯ {{Lexi}}</h2>"),
        (r"<h2>▯ ? </h2>", r"<h2>▯ ?</h2>"),
        (r"<h2>▯ ? ▯</h2>", r"<h2>▯ ?</h2>"),
        (r"<h2>▯ ? (?)</h2>", r"<h2>▯ ?</h2>"),
        (r"<h2>▯ ?(cu)</h2>", r"<h2>▯ ?</h2>")]
SIDE_FIXES = {
    "Produti": {"qfmt": [("<td>Intransitive (-cu)</td>", "<td>Intransitive</td>"),
                         ("<td>Echo-transitive</td>", "<td>Transitive</td>")]},
    "Rusoti-Ojetoli Rukone": {"qfmt": BARE, "afmt": BARE},
    "Rusoti-Ojetoli Produti": {"qfmt": BARE, "afmt": BARE},
    "Nenojetoli(-cu) Rukone": {"qfmt": BARE, "afmt": BARE},
    "Nenojetoli(-cu) Produti": {"qfmt": BARE, "afmt": BARE},
}
for name, sides in SIDE_FIXES.items():
    tmpl = by_name[name]
    for side, swaps in sides.items():
        for old, new in swaps:
            if old in tmpl[side]:
                tmpl[side] = tmpl[side].replace(old, new)
                print(f"{name} {side}: {old!r} -> {new!r}")
        for leak in ("(cu)", "({{Lexi}})", "Echo-transitive", "(?)", "{{Lexi}} ▯"):
            if leak in tmpl[side]:
                raise SystemExit(f"{name}: {side} still shows {leak!r}")
mm.update_dict(nt)

proto = mm.by_name(PROTOTYPE)
if proto is not None:
    n = len(col.find_notes(f'mid:{proto["id"]}'))
    mm.remove(proto["id"])
    print(f"removed notetype {PROTOTYPE!r} and its {n} note(s)")

# Only the first run's input is the pre-restructure deck worth keeping.
if not os.path.exists(BACKUP):
    shutil.copyfile(APKG, BACKUP)
col.export_anki_package(
    out_path=os.path.abspath(APKG),
    options=ExportAnkiPackageOptions(
        with_scheduling=False,
        with_deck_configs=True,
        with_media=True,
        legacy=False,
    ),
    limit=pb.ExportLimit(whole_collection=Empty()),
)
col.close()
shutil.rmtree(workdir, ignore_errors=True)
print(f"wrote {APKG} (previous kept as {BACKUP})")
