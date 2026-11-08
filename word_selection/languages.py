"""Source languages, families and the methodology's ordering rules."""

# code: our canonical code. wikt: codes used in English-Wiktionary translation
# tables (Mandarin appears as both). dump: lang_code of entries in the dump.
# wiki: Wikipedia / Wikidata language code. basa: name used in LexiliAsel.
LANGS = [
    {"code": "en",  "wikt": ["en"],        "dump": "en", "wiki": "en", "basa": "Englisa",    "family": "Ewropali", "latin": True},
    {"code": "es",  "wikt": ["es"],        "dump": "es", "wiki": "es", "basa": "Espanisa",   "family": "Ewropali", "latin": True},
    {"code": "fr",  "wikt": ["fr"],        "dump": "fr", "wiki": "fr", "basa": "Fransesa",   "family": "Ewropali", "latin": True},
    {"code": "de",  "wikt": ["de"],        "dump": "de", "wiki": "de", "basa": "Doycisa",    "family": "Ewropali", "latin": True},
    {"code": "ru",  "wikt": ["ru"],        "dump": "ru", "wiki": "ru", "basa": "Rusisa",     "family": "Ewropali", "latin": False},
    {"code": "cmn", "wikt": ["cmn", "zh"], "dump": "zh", "wiki": "zh", "basa": "Putunhwa",   "family": "Putunhwa", "latin": False},
    {"code": "ja",  "wikt": ["ja"],        "dump": "ja", "wiki": "ja", "basa": "Niponsa",    "family": "Niponsa",  "latin": False},
    {"code": "ko",  "wikt": ["ko"],        "dump": "ko", "wiki": "ko", "basa": "Koreasa",    "family": "Koreasa",  "latin": False},
    {"code": "vi",  "wikt": ["vi"],        "dump": "vi", "wiki": "vi", "basa": "Vyetnamsa",  "family": "Vyetnamsa", "latin": True},
    {"code": "hi",  "wikt": ["hi"],        "dump": "hi", "wiki": "hi", "basa": "Hindi",      "family": "Hindi",    "latin": False},
    {"code": "te",  "wikt": ["te"],        "dump": "te", "wiki": "te", "basa": "Telugusa",   "family": "Telugusa", "latin": False},
    {"code": "ar",  "wikt": ["ar"],        "dump": "ar", "wiki": "ar", "basa": "Arabisa",    "family": "Arabisa",  "latin": False},
    {"code": "sw",  "wikt": ["sw"],        "dump": "sw", "wiki": "sw", "basa": "Swahilisa",  "family": "Swahilisa", "latin": True},
    {"code": "fa",  "wikt": ["fa"],        "dump": "fa", "wiki": "fa", "basa": "Parsisa",    "family": "Parsisa",  "latin": False},
    {"code": "tr",  "wikt": ["tr"],        "dump": "tr", "wiki": "tr", "basa": "Turkisa",    "family": "Turkisa",  "latin": True},
    {"code": "id",  "wikt": ["id"],        "dump": "id", "wiki": "id", "basa": "Indonesisa", "family": "Indonesisa", "latin": True},
]

BY_CODE = {l["code"]: l for l in LANGS}
CODES = [l["code"] for l in LANGS]
BASA_TO_CODE = {l["basa"]: l["code"] for l in LANGS}
# Spellings seen in older data / v2 automator
BASA_TO_CODE.update({"Hangusa": "ko", "Doycesa": "de", "Rusesa": "ru"})
DUMP_TO_CODE = {l["dump"]: l["code"] for l in LANGS}
WIKT_TO_CODE = {w: l["code"] for l in LANGS for w in l["wikt"]}
WIKI_TO_CODE = {l["wiki"]: l["code"] for l in LANGS}

# Historical sources still present in LexiliAsel: parsed, never counted.
HISTORICAL = {"Pilipinasa": "tl"}

EUROPEAN = {"en", "es", "fr", "de", "ru"}
EAST_ASIAN = {"cmn", "ja", "ko", "vi"}
INDO_EUROPEAN = EUROPEAN | {"hi", "fa"}   # a-priori vowel -e (-i for English verbs)

# Extra languages fetched for the dossier only (never counted as sources).
DOSSIER_LANGS = ["eo"]


def family(code):
    return BY_CODE[code]["family"] if code in BY_CODE else None


def families(codes):
    return {family(c) for c in codes if c in BY_CODE}


# Tie-breaks, in order, when clusters have the same number of families.
def _tb_east_asian(c):  return len(c & EAST_ASIAN) >= 2
def _tb_arabic(c):      return "ar" in c and len(families(c)) >= 2
def _tb_hindi(c):       return "hi" in c and len(families(c)) >= 2
def _tb_european(c):    return bool(c & EUROPEAN) and len(families(c)) >= 2
def _tb_fa_tr(c):       return {"fa", "tr"} <= c


TIE_BREAKS = [
    ("two or more East Asian languages", _tb_east_asian),
    ("Arabic plus any other", _tb_arabic),
    ("Hindi plus any other", _tb_hindi),
    ("European plus any other", _tb_european),
    ("Persian and Turkish", _tb_fa_tr),
]

# Last resort when no source has agreement (Mandarin: two-character words only).
FALLBACK_ORDER = ["cmn", "vi", "te", "sw", "ar", "hi"]
