"""
LLM_sense_judge.py — Applicability judgements for Wiktionary senses mapped to Globasa words.

Six-tier pipeline (all write to single 'Tier' column):
  Tier 1: Core meaning match via graph data + translation overlap      → Tier=a
  Tier 2: Register/domain filtering for clear negatives                → Tier=a
  Tier 3: Corpus corroboration via Qdrant for extended meanings        → Tier=a
  Tier 4: Composite scoring (derivation + Spa/Epo cross-validation)    → Tier=a
  Tier 5: WordNet synonym/hypernym expansion + homonym detection       → Tier=a
  Tier 6: Local LLM (Qwen3.5-9B via llama-cpp) for remaining cases    → Tier=l
"""

import csv
import os
import re
import sys
import shutil
from datetime import datetime
from collections import defaultdict

# Preload CUDA libraries for llama-cpp-python GPU offloading
import ctypes
for _lib_name in ["libcublas.so.12", "libcublasLt.so.12", "libcudart.so.12"]:
    _lib_path = f"/usr/local/cuda-12.0/targets/x86_64-linux/lib/{_lib_name}"
    if os.path.exists(_lib_path):
        try:
            ctypes.CDLL(_lib_path, mode=ctypes.RTLD_GLOBAL)
        except OSError:
            pass

import openpyxl
import wn

csv.field_size_limit(sys.maxsize)

# === Paths ===

EXCEL_PATH = "/home/paleos/Nextcloud/Documents/Language/Globasa/GLB_ENG_WiktionarySenses.xlsx"
WORD_LIST_PATH = "word-list.csv"
GRAPH_WORDS_PATH = "kuzu_import/words.csv"
GRAPH_DERIVED_PATH = "kuzu_import/derived_from.csv"
GRAPH_SYNONYMS_PATH = "kuzu_import/synonyms_synonym.csv"
GRAPH_ANTONYMS_PATH = "kuzu_import/antonyms.csv"

QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "globasa_tmx"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
VECTOR_NAME = "fast-paraphrase-multilingual-minilm-l12-v2"

# === NLP constants ===

STOPWORDS = {
    'a', 'an', 'the', 'of', 'to', 'in', 'for', 'is', 'on', 'that', 'by',
    'or', 'and', 'with', 'as', 'it', 'at', 'from', 'be', 'was', 'are',
    'were', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
    'but', 'not', 'this', 'they', 'which', 'their', 'if', 'its', 'into',
    'than', 'more', 'other', 'some', 'such', 'no', 'can', 'will', 'each',
    'about', 'very', 'also', 'may', 'often', 'used', 'one', 'two', 'so',
    'up', 'out', 'who', 'what', 'when', 'where', 'how', 'all', 'would',
    'there', 'could', 'make', 'like', 'long', 'look', 'many',
    'then', 'them', 'these', 'her', 'him', 'his', 'she', 'he', 'we',
    'you', 'your', 'our', 'my', 'me', 'us', 'any', 'only', 'over',
    'most', 'after', 'before', 'between', 'through', 'under', 'same',
    'just', 'too', 'own', 'way', 'because', 'good', 'great', 'well',
    'still', 'should', 'while', 'even', 'new', 'much', 'back', 'old',
    'give', 'go', 'come', 'get', 'take', 'say', 'see', 'know', 'thing',
    'especially', 'particularly', 'usually', 'generally', 'typically',
    'something', 'someone', 'person', 'people', 'state', 'form',
    'act', 'action', 'manner', 'kind', 'type', 'process',
}

REGISTER_MARKERS = {
    'slang', 'vulgar', 'colloquial', 'archaic', 'obsolete', 'dated',
    'derogatory', 'pejorative', 'dialectal', 'informal', 'rare',
    'figuratively', 'figurative', 'jocular', 'humorous', 'euphemistic',
}

DOMAIN_MARKERS = {
    'baseball', 'cricket', 'heraldry', 'pinball', 'bowling', 'billiards',
    'poker', 'chess', 'tennis', 'golf', 'rugby', 'lacrosse', 'volleyball',
    'badminton', 'fencing', 'curling', 'hockey', 'softball', 'darts',
    'squash', 'snooker', 'croquet', 'rowing', 'sailing', 'surfing',
    'skateboarding', 'skiing', 'snowboarding', 'wrestling', 'boxing',
    'karate', 'judo', 'sumo', 'athletics', 'gymnastics',
}

# ---------------------------------------------------------------------------
# Tier 5 (LLM): WordNet-powered synonym expansion + homonym detection
# Uses oewn:2023 (Open English WordNet) for systematic coverage.
# ---------------------------------------------------------------------------

EN_WN = wn.Wordnet('oewn:2023')

_wn_cache = {}  # word -> set of expanded lemmas


def wn_expand(word, core_filter=None):
    """Expand a word via oewn:2023: lemmas + hypernym lemmas, English only.

    If core_filter is provided (set of the Globasa word's CORE translation
    tokens, excluding slang/qualified senses), only include synsets whose
    definition or non-self lemmas overlap with core_filter. This filters
    out homonym senses (e.g. ball-as-dance when the core meaning is ball-
    as-sphere). If core_filter is empty or None, all synsets are included.
    """
    cache_key = (word, frozenset(core_filter) if core_filter else None)
    if cache_key in _wn_cache:
        return _wn_cache[cache_key]
    lemmas = set()
    for ss in EN_WN.synsets(word):
        if core_filter:
            ss_def_words = content_words(ss.definition() or '')
            ss_lemmas = {w.lemma().lower() for w in ss.words()} - {word.lower()}
            if not (core_filter & ss_def_words) and not (core_filter & ss_lemmas):
                continue
        for w in ss.words():
            lemmas.add(w.lemma().lower())
        for hyp in ss.hypernyms():
            for w in hyp.words():
                lemmas.add(w.lemma().lower())
    result = {l for l in lemmas
              if ' ' not in l and l.isascii() and len(l) > 2} - {word.lower()}
    _wn_cache[cache_key] = result
    return result


# Supplemental manual expansions for words poorly covered by WordNet
# or needing domain-specific knowledge
SYNONYM_FIELDS_SUPPLEMENT = {
    # Physical objects / shapes
    'ball': {'sphere', 'spherical', 'round', 'orb', 'globe', 'globular',
             'testicle', 'testis', 'testes', 'scrotum'},
    'stick': {'branch', 'twig', 'rod', 'pole', 'staff', 'wand', 'baton',
              'cane', 'bar'},
    'shell': {'husk', 'casing', 'covering', 'carapace', 'exoskeleton',
              'hull', 'pod', 'rind'},
    'ring': {'circle', 'circular', 'loop', 'band', 'hoop'},
    'block': {'cube', 'cuboid', 'rectangular', 'slab', 'chunk'},
    'point': {'tip', 'sharp', 'pointed', 'apex', 'peak', 'dot', 'spot',
              'mark', 'score', 'unit'},
    'sheet': {'flat', 'thin', 'layer', 'panel', 'plate'},
    'crack': {'fracture', 'fissure', 'split', 'gap', 'opening', 'crevice',
              'snap', 'narrow'},
    'net': {'mesh', 'network', 'web', 'netting', 'grid'},
    'frame': {'framework', 'structure', 'skeleton', 'chassis'},
    'patch': {'repair', 'mend', 'cover'},
    'line': {'cord', 'rope', 'string', 'wire', 'cable', 'row', 'queue',
             'mark', 'stripe', 'boundary', 'border'},
    'band': {'strip', 'strap', 'belt', 'ribbon'},
    'spring': {'coil', 'elastic', 'bounce', 'fountain', 'source', 'well',
               'season'},
    'post': {'pole', 'pillar', 'column', 'stake', 'mail', 'position',
             'station'},
    'plate': {'dish', 'platter', 'slab', 'sheet', 'flat'},
    'pipe': {'tube', 'conduit', 'duct', 'hose', 'channel'},
    'bar': {'rod', 'beam', 'railing', 'counter', 'pub', 'tavern',
            'obstruct', 'prevent', 'prohibit'},
    'key': {'lock', 'unlock', 'lever', 'button', 'crucial', 'essential',
            'important', 'clue', 'solution', 'pitch', 'tone', 'scale'},
    'lock': {'bolt', 'latch', 'fasten', 'secure', 'hair', 'tress', 'curl'},
    'match': {'contest', 'game', 'competition', 'rival', 'equal',
              'correspond', 'pair', 'lighter', 'ignite'},

    # Body / anatomy
    'head': {'skull', 'cranium', 'scalp', 'brain', 'face', 'brow',
             'forehead'},
    'top': {'summit', 'peak', 'apex', 'crown', 'crest', 'upper', 'highest',
            'uppermost', 'lid', 'cap'},
    'hand': {'palm', 'finger', 'fist', 'grasp', 'grip', 'wrist'},
    'foot': {'sole', 'toe', 'heel', 'ankle', 'step', 'tread'},
    'back': {'spine', 'dorsal', 'rear', 'posterior'},
    'neck': {'throat', 'cervical', 'nape'},
    'bone': {'skeletal', 'osseous', 'marrow'},
    'skin': {'dermis', 'epidermis', 'hide', 'peel', 'rind', 'bark',
             'membrane', 'complexion'},
    'tongue': {'lingual', 'taste', 'lick'},
    'tooth': {'dental', 'molar', 'fang', 'tusk', 'canine', 'incisor'},
    'eye': {'ocular', 'visual', 'sight', 'vision', 'iris', 'pupil',
            'retina', 'optic'},
    'ear': {'aural', 'auditory', 'hearing', 'earlobe'},
    'nose': {'nasal', 'nostril', 'olfactory', 'snout', 'smell'},
    'mouth': {'oral', 'lip', 'jaw', 'palate'},
    'heart': {'cardiac', 'coronary', 'heartbeat', 'pulse', 'cardiovascular'},
    'blood': {'sanguine', 'hemorrhage', 'bleed', 'vein', 'artery', 'plasma'},
    'hair': {'strand', 'lock', 'curl', 'follicle', 'scalp', 'tress'},
    'wing': {'feather', 'plume', 'pinion', 'aileron', 'flap'},
    'tail': {'rear', 'hind', 'appendage', 'caudal'},
    'horn': {'antler', 'tusk', 'protrusion', 'trumpet', 'bugle'},
    'claw': {'talon', 'nail', 'paw', 'scratch'},
    'belly': {'abdomen', 'stomach', 'gut', 'tummy', 'midriff'},

    # Leadership / authority
    'chief': {'leader', 'commander', 'authority', 'charge', 'officer',
              'principal', 'primary', 'main', 'foremost'},
    'boss': {'supervisor', 'oversee', 'manage', 'direct', 'employ',
             'authority', 'charge'},
    'master': {'expert', 'skilled', 'proficient', 'authority', 'control',
               'command', 'owner', 'lord'},
    'lead': {'guide', 'conduct', 'ahead', 'front', 'first', 'precede',
             'command', 'charge'},
    'captain': {'commander', 'officer', 'skipper', 'pilot'},
    'king': {'monarch', 'sovereign', 'ruler', 'reign', 'royal', 'throne',
             'crown'},
    'queen': {'monarch', 'sovereign', 'ruler', 'reign', 'royal', 'throne'},
    'president': {'chair', 'preside', 'executive', 'office'},

    # Movement / action
    'run': {'sprint', 'jog', 'dash', 'race', 'gallop', 'flee', 'rush',
            'hurry', 'rapid', 'foot', 'feet', 'leg'},
    'walk': {'stroll', 'stride', 'pace', 'hike', 'trek', 'amble',
             'saunter', 'march'},
    'fly': {'soar', 'glide', 'airborne', 'hover', 'flight', 'aerial',
            'aviation'},
    'swim': {'aquatic', 'paddle', 'stroke', 'dive', 'float'},
    'jump': {'leap', 'bound', 'hop', 'vault', 'skip'},
    'throw': {'toss', 'hurl', 'fling', 'pitch', 'cast', 'lob'},
    'hit': {'strike', 'blow', 'punch', 'slap', 'smack', 'bang', 'knock',
            'impact'},
    'strike': {'blow', 'punch', 'smack', 'impact', 'knock', 'attack'},
    'cut': {'slice', 'chop', 'sever', 'trim', 'carve', 'incise', 'slit'},
    'break': {'fracture', 'crack', 'shatter', 'snap', 'split', 'smash',
              'rupture'},
    'pull': {'drag', 'tug', 'draw', 'haul', 'yank', 'tow'},
    'push': {'shove', 'press', 'thrust', 'propel', 'nudge'},
    'turn': {'rotate', 'revolve', 'spin', 'twist', 'pivot', 'swivel'},
    'fall': {'drop', 'descend', 'tumble', 'plunge', 'collapse', 'topple'},
    'rise': {'ascend', 'climb', 'mount', 'elevate', 'lift'},
    'stand': {'upright', 'erect', 'vertical'},
    'sit': {'seat', 'seated', 'chair', 'bench'},
    'hold': {'grip', 'grasp', 'clutch', 'embrace', 'contain', 'possess'},
    'carry': {'transport', 'haul', 'bear', 'convey', 'bring'},
    'pass': {'passage', 'cross', 'traverse', 'transfer', 'relay', 'exceed',
             'surpass'},
    'catch': {'capture', 'seize', 'grab', 'snatch', 'intercept', 'trap'},
    'pick': {'choose', 'select', 'pluck', 'gather', 'harvest'},
    'drop': {'fall', 'release', 'lower', 'decrease', 'decline', 'drip'},
    'cover': {'wrap', 'coat', 'shield', 'blanket', 'conceal', 'protect',
              'lid'},
    'roll': {'rotate', 'spin', 'tumble', 'cylinder', 'scroll', 'list',
             'register'},
    'touch': {'contact', 'feel', 'tap', 'brush', 'stroke'},
    'press': {'push', 'squeeze', 'compress', 'flatten', 'iron'},
    'fold': {'crease', 'bend', 'pleat', 'wrinkle', 'tuck'},
    'hang': {'suspend', 'dangle', 'drape', 'swing'},
    'pour': {'flow', 'stream', 'spill', 'cascade', 'drain'},
    'mix': {'blend', 'combine', 'stir', 'mingle', 'merge'},
    'spread': {'extend', 'expand', 'scatter', 'distribute', 'smear',
               'stretch'},
    'shake': {'tremble', 'vibrate', 'quiver', 'shudder', 'rattle'},
    'blow': {'gust', 'puff', 'exhale', 'wind'},
    'charge': {'rush', 'attack', 'accuse', 'price', 'cost', 'fee',
               'electricity', 'load', 'fill'},
    'dash': {'rush', 'sprint', 'race', 'hurry', 'bolt'},

    # Properties / adjectives
    'sick': {'ill', 'unwell', 'ailing', 'diseased', 'ailment', 'malady',
             'infirm', 'fever', 'nausea'},
    'strong': {'powerful', 'mighty', 'robust', 'sturdy', 'tough',
               'vigorous', 'potent'},
    'weak': {'feeble', 'frail', 'fragile', 'flimsy', 'delicate',
             'vulnerable'},
    'hard': {'solid', 'firm', 'rigid', 'stiff', 'tough', 'dense',
             'difficult'},
    'soft': {'gentle', 'tender', 'smooth', 'supple', 'pliant', 'flexible'},
    'fast': {'quick', 'rapid', 'swift', 'speedy', 'hasty', 'brisk'},
    'slow': {'gradual', 'leisurely', 'sluggish', 'unhurried'},
    'hot': {'warm', 'heat', 'burning', 'scorching', 'boiling',
            'temperature', 'thermal'},
    'cold': {'cool', 'chill', 'freezing', 'frigid', 'frost', 'icy'},
    'light': {'bright', 'luminous', 'radiant', 'glow', 'shine',
              'illuminate', 'lamp', 'ray', 'beam', 'lightweight'},
    'dark': {'dim', 'shadow', 'shade', 'murky', 'gloomy', 'obscure'},
    'clean': {'pure', 'spotless', 'tidy', 'sanitary', 'hygienic', 'wash'},
    'sharp': {'keen', 'acute', 'blade', 'edge', 'pointed', 'cutting'},
    'flat': {'level', 'even', 'smooth', 'horizontal', 'plain'},
    'round': {'circular', 'spherical', 'curved', 'cylindrical'},
    'dry': {'arid', 'parched', 'dehydrate', 'desiccate'},
    'wet': {'moist', 'damp', 'humid', 'soaked', 'drenched'},
    'thick': {'dense', 'wide', 'broad', 'bulky', 'heavy'},
    'thin': {'slim', 'slender', 'narrow', 'fine', 'lean'},
    'deep': {'profound', 'abyss', 'depth', 'bottom', 'submerged'},
    'heavy': {'weighty', 'hefty', 'massive', 'dense', 'ponderous'},
    'active': {'energetic', 'vigorous', 'dynamic', 'lively', 'busy',
               'brisk', 'agile'},

    # Nature / geography
    'field': {'meadow', 'pasture', 'grassland', 'plain', 'clearing',
              'terrain', 'ground', 'land', 'agricultural', 'cultivat',
              'crop', 'farm'},
    'mountain': {'peak', 'summit', 'hill', 'ridge', 'cliff', 'alpine'},
    'river': {'stream', 'creek', 'brook', 'waterway', 'flow', 'current',
              'tributary'},
    'sea': {'ocean', 'marine', 'maritime', 'naval', 'tide', 'wave',
            'coast'},
    'tree': {'trunk', 'branch', 'leaf', 'root', 'bark', 'wood', 'timber',
             'forest'},
    'flower': {'bloom', 'blossom', 'petal', 'stamen', 'pistil', 'floral',
               'bouquet'},
    'stone': {'rock', 'pebble', 'boulder', 'mineral', 'gravel'},
    'earth': {'soil', 'ground', 'dirt', 'clay', 'terrain', 'land'},
    'sky': {'heaven', 'atmosphere', 'celestial', 'aerial', 'firmament',
            'cloud'},
    'fire': {'flame', 'blaze', 'burn', 'combustion', 'ignite', 'inferno'},
    'water': {'aqua', 'liquid', 'fluid', 'hydro', 'moisture'},
    'wind': {'breeze', 'gale', 'gust', 'draft', 'air'},
    'rain': {'precipitation', 'shower', 'drizzle', 'downpour', 'storm'},
    'snow': {'frost', 'sleet', 'blizzard', 'flake', 'frozen'},
    'ice': {'frozen', 'glacier', 'icicle', 'freeze'},
    'grain': {'seed', 'cereal', 'wheat', 'corn', 'barley', 'rice', 'oat',
              'kernel', 'crop', 'harvest'},
    'dust': {'particle', 'powder', 'fine', 'grit', 'debris'},
    'smoke': {'fume', 'vapor', 'haze', 'smog', 'exhaust'},
    'cloud': {'mist', 'fog', 'haze', 'vapor', 'overcast', 'cumulus'},
    'wave': {'ripple', 'swell', 'surge', 'tide', 'crest', 'trough',
             'undulate'},
    'island': {'isle', 'atoll', 'archipelago'},
    'forest': {'wood', 'woodland', 'jungle', 'grove', 'thicket'},

    # Building / place
    'building': {'structure', 'edifice', 'construction', 'architecture'},
    'room': {'chamber', 'hall', 'compartment', 'space', 'enclosure',
             'walls', 'ceiling', 'floor'},
    'house': {'home', 'dwelling', 'residence', 'abode', 'domicile'},
    'door': {'gate', 'entrance', 'exit', 'portal', 'threshold'},
    'wall': {'partition', 'barrier', 'fence', 'rampart'},
    'floor': {'ground', 'surface', 'storey', 'pavement'},
    'road': {'path', 'street', 'highway', 'route', 'lane', 'trail'},
    'bridge': {'span', 'overpass', 'crossing', 'viaduct'},
    'tower': {'turret', 'spire', 'steeple', 'minaret'},
    'facility': {'building', 'installation', 'complex', 'establishment',
                 'plant', 'center', 'site'},

    # Social / abstract
    'law': {'legal', 'statute', 'legislation', 'regulation', 'rule',
            'ordinance', 'judicial', 'court'},
    'right': {'entitlement', 'privilege', 'freedom', 'liberty', 'claim',
              'prerogative'},
    'power': {'authority', 'control', 'strength', 'force', 'energy',
              'ability', 'capability'},
    'order': {'command', 'instruction', 'directive', 'sequence',
              'arrangement', 'organize'},
    'change': {'alter', 'modify', 'transform', 'shift', 'convert', 'vary',
               'adjust'},
    'set': {'group', 'collection', 'assortment', 'kit', 'suite', 'batch'},
    'work': {'labor', 'toil', 'effort', 'task', 'job', 'employ',
             'occupation'},
    'play': {'game', 'sport', 'recreation', 'amusement', 'fun', 'perform',
             'theatre', 'drama'},
    'passage': {'corridor', 'hallway', 'path', 'route', 'channel',
                'transit'},
    'composition': {'makeup', 'structure', 'arrangement', 'blend',
                    'mixture'},
    'constitution': {'charter', 'fundamental', 'founding', 'basic'},
    'concession': {'grant', 'yield', 'allow', 'permit', 'admit'},
    'rank': {'position', 'grade', 'level', 'tier', 'status', 'standing',
             'hierarchy', 'row', 'file'},
    'record': {'document', 'register', 'log', 'archive', 'entry',
               'account'},
    'recording': {'audio', 'video', 'tape', 'disc', 'track', 'album',
                  'capture', 'sound'},
    'load': {'burden', 'cargo', 'freight', 'weight', 'haul', 'shipment'},
    'impulse': {'urge', 'compulsion', 'drive', 'impetus', 'stimulus',
                'momentum'},
    'sprint': {'dash', 'race', 'burst', 'speed'},
    'day': {'daytime', 'daylight', 'dawn', 'sunrise', 'sunset', 'daily',
            'diurnal', 'morning', 'afternoon', 'evening', 'noon',
            'midnight', 'hour'},
    'document': {'paper', 'certificate', 'file', 'deed', 'instrument',
                 'official'},
    'level': {'degree', 'tier', 'grade', 'stage', 'height', 'flat',
              'even', 'horizontal', 'storey'},
    'language': {'tongue', 'speech', 'dialect', 'idiom', 'parlance',
                 'lingo', 'vocabulary', 'linguistic'},
    'taking': {'seize', 'capture', 'snatch', 'appropriate', 'confiscate'},
    'grab': {'seize', 'snatch', 'clutch', 'grasp', 'grip'},
    'deed': {'feat', 'exploit', 'accomplishment'},
    'troop': {'soldier', 'military', 'army', 'regiment', 'battalion',
              'squad', 'platoon'},
    'art': {'artistic', 'creative', 'aesthetic', 'painting', 'sculpture',
            'music', 'craft'},
    'acrobatics': {'acrobatic', 'gymnastic', 'tumbling', 'agility'},
    'become': {'grow', 'develop', 'evolve'},
    'get': {'obtain', 'acquire', 'receive', 'gain', 'fetch', 'procure'},
    'act': {'deed', 'perform', 'execute', 'behave', 'statute'},
    'sign': {'signal', 'symbol', 'gesture', 'indicate', 'signature',
             'placard', 'notice', 'omen', 'symptom'},
    'mark': {'sign', 'symbol', 'stain', 'spot', 'trace', 'score',
             'grade', 'label', 'brand'},
    'note': {'remark', 'observation', 'comment', 'annotation', 'message',
             'letter', 'tone', 'pitch', 'currency', 'banknote'},
    'check': {'inspect', 'examine', 'verify', 'control', 'restrain',
              'cheque', 'pattern', 'tick'},
    'case': {'container', 'box', 'crate', 'instance', 'example',
             'situation', 'lawsuit', 'trial'},
    'matter': {'substance', 'material', 'issue', 'subject', 'concern',
               'affair', 'topic'},
    'term': {'word', 'expression', 'phrase', 'period', 'duration',
             'condition', 'stipulation'},
    'figure': {'shape', 'form', 'outline', 'silhouette', 'number',
               'digit', 'statue', 'diagram', 'illustration'},
    'scale': {'size', 'proportion', 'ratio', 'range', 'scope',
              'balance', 'weigh', 'climb', 'flake', 'fish'},
    'practice': {'exercise', 'rehearsal', 'drill', 'training', 'habit',
                 'custom', 'routine'},
    'spirit': {'soul', 'ghost', 'phantom', 'essence', 'mood',
               'enthusiasm', 'alcohol', 'liquor'},
    'stock': {'supply', 'inventory', 'reserve', 'share', 'equity',
              'broth', 'livestock', 'cattle'},
    'course': {'path', 'route', 'direction', 'track', 'class', 'lesson',
               'dish', 'meal'},
    'current': {'flow', 'stream', 'present', 'contemporary', 'modern',
                'electricity'},
    'rest': {'relax', 'repose', 'sleep', 'pause', 'remainder',
             'leftover', 'residue'},
    'address': {'location', 'direction', 'speech', 'lecture', 'talk',
                'speak'},
    'train': {'coach', 'railway', 'locomotive', 'teach', 'instruct',
              'exercise', 'drill', 'sequence', 'procession'},
    'service': {'duty', 'assistance', 'ceremony', 'worship', 'repair',
                'maintenance'},
    'trade': {'commerce', 'business', 'exchange', 'swap', 'barter',
              'craft', 'profession', 'occupation'},
    'season': {'spring', 'summer', 'autumn', 'winter', 'period',
               'flavor', 'spice'},
    'character': {'personality', 'trait', 'nature', 'disposition',
                  'letter', 'symbol', 'glyph', 'role', 'fictional'},
    'ground': {'earth', 'soil', 'land', 'terrain', 'surface', 'floor',
               'foundation', 'basis', 'reason'},
    'base': {'foundation', 'bottom', 'basis', 'support', 'pedestal',
             'headquarters', 'station'},
    'sound': {'noise', 'tone', 'audio', 'acoustic', 'resonance', 'healthy',
              'solid', 'reliable'},
    'space': {'room', 'area', 'expanse', 'void', 'gap', 'cosmos',
              'universe', 'outer'},
    'degree': {'extent', 'level', 'measure', 'amount', 'grade',
               'qualification', 'diploma', 'temperature', 'angle'},
}

# Negative domain keywords: if the definition is clearly about an unrelated
# specialized domain, the sense is a homonym → 'n'
NEGATIVE_DOMAINS = {
    'chemical_element': {'chemical element', 'atomic number', 'periodic table',
                         'symbol pb', 'symbol fe', 'symbol sn'},
    'typography': {'typography', 'typographic', 'typeface', 'font', 'kerning',
                   'leading between lines', 'linotype', 'glyph', 'movable type'},
    'card_game': {'card game', 'deck of cards', 'playing card', 'trump card',
                  'trick in card', 'dealer deals', 'ante'},
    'morse_code': {'morse code', 'telegraph'},
    'mining_specific': {'mining', 'lode', 'ore deposit', 'mineshaft'},
    'freemasonry': {'freemasonry', 'masonic', 'masonic lodge'},
    'lacrosse_detail': {'lacrosse stick', 'crosse'},
    'pressure_vessel': {'pressure vessel', 'cylindrically-shaped'},
}

# Semantic domain tags: used to detect cross-domain homonyms.
# If the word's tokens overlap with one domain but the definition overlaps
# with another, it's likely a homonym.
LEADERSHIP_WORDS = frozenset({
    'leader', 'chief', 'boss', 'command', 'authority', 'direct', 'lead',
    'oversee', 'charge', 'supervise', 'manage', 'officer', 'captain',
    'master', 'ruler', 'govern', 'preside', 'head'
})
BODYPART_WORDS = frozenset({
    'skull', 'cranium', 'brain', 'scalp', 'forehead', 'face', 'bone',
    'muscle', 'organ', 'limb', 'tissue', 'anatomy', 'body', 'nerve',
    'joint', 'socket', 'ligament'
})


# === Utility functions ===

def content_words(text):
    """Extract content words from text: lowercase, alpha-only, stopwords removed."""
    if not text:
        return set()
    words = set(re.findall(r'[a-z]+', text.lower()))
    return {w for w in words - STOPWORDS if len(w) > 2}


def parse_translation(trans_eng, core_only=False):
    """Parse a graph/wordlist translation string into content word tokens.

    Handles formats like:
      'n: ball; n (sexual): testicle'
      'adj: sick, ill'
      'recording, record; record'

    If core_only=True, skip semicolon-delimited segments that have a
    parenthetical qualifier (sexual, slang, figurative, etc.) — these
    are non-core senses.
    """
    if not trans_eng:
        return set()
    tokens = set()
    for segment in trans_eng.split(';'):
        # Check for qualifying parentheticals before stripping
        if core_only and re.search(r'\((?:sexual|slang|figurative|vulgar|'
                                   r'informal|archaic|regional)\)', segment,
                                   re.IGNORECASE):
            continue
        clean = re.sub(r'\b[nvbt](\.\w+)*\s*:', '', segment)  # n: v: b: t:
        clean = re.sub(r'\b(adj|adv|sfx|pfx)\s*:', '', clean) # adj: sfx: etc.
        clean = re.sub(r'\([^)]*\)', '', clean)                # parentheticals
        clean = re.sub(r'_[^_]*_', '', clean)                  # italic qualifiers
        for part in re.split(r'[,/]', clean):
            for w in part.strip().lower().split():
                w = w.strip('-')
                if len(w) > 2 and w not in STOPWORDS:
                    tokens.add(w)
    return tokens


def has_unslashed_words(spa_epo_val):
    """Check if a Spa/Epo cross-validation column has matched (unslashed) words."""
    if not spa_epo_val:
        return False
    # Words in /slashes/ are unmatched; words outside slashes are matched
    without_slashed = re.sub(r'/[^/]*/', '', str(spa_epo_val))
    clean = without_slashed.strip(' ,;')
    return bool(clean)


# === Data loaders ===

def load_graph_data():
    """Read kuzu_import CSVs -> word info, derivation map, synonym map."""
    words = {}
    with open(GRAPH_WORDS_PATH, 'r') as f:
        for row in csv.DictReader(f, delimiter='|'):
            w = row['word']
            trans = row['translation_eng']
            words[w] = {
                'translation_eng': trans,
                'word_class': row['word_class'],
                'category': row['category'],
                'tokens': parse_translation(trans),
                'core_tokens': parse_translation(trans, core_only=True),
            }

    derivations = defaultdict(list)
    with open(GRAPH_DERIVED_PATH, 'r') as f:
        for row in csv.DictReader(f, delimiter='|'):
            derivations[row['to']].append({
                'word': row['from'],
                'affix': row['affix'],
                'type': row['affix_type'],
            })

    synonyms = defaultdict(set)
    with open(GRAPH_SYNONYMS_PATH, 'r') as f:
        for row in csv.DictReader(f, delimiter='|'):
            synonyms[row['from']].add(row['to'])
            synonyms[row['to']].add(row['from'])

    antonyms = defaultdict(set)
    with open(GRAPH_ANTONYMS_PATH, 'r') as f:
        for row in csv.DictReader(f, delimiter='|'):
            antonyms[row['from']].add(row['to'])
            antonyms[row['to']].add(row['from'])

    return words, derivations, synonyms, antonyms


def load_word_list():
    """Parse word-list.csv for English translations."""
    translations = {}
    with open(WORD_LIST_PATH, 'r') as f:
        for row in csv.DictReader(f):
            word = row['Word']
            eng = row['TranslationEng'].strip()
            if eng:
                translations[word] = {'raw': eng, 'tokens': parse_translation(eng)}
    return translations


# === Lookup helpers ===

def get_word_tokens(glb_word, graph_words, word_list):
    """Get translation tokens for a Globasa word, trying graph then word list."""
    bare = glb_word.lstrip('-')
    for key in (glb_word, bare):
        if key in graph_words and graph_words[key]['tokens']:
            return graph_words[key]['tokens']
        if key in word_list and word_list[key]['tokens']:
            return word_list[key]['tokens']
    return set()


def get_core_tokens(glb_word, graph_words):
    """Get CORE translation tokens (excluding slang/qualified senses)."""
    bare = glb_word.lstrip('-')
    for key in (glb_word, bare):
        if key in graph_words and graph_words[key].get('core_tokens'):
            return graph_words[key]['core_tokens']
    return set()


def get_derived_forms(glb_word, derivations):
    """Get derivation entries for a Globasa word."""
    bare = glb_word.lstrip('-')
    return derivations.get(bare, [])


def get_derived_tokens(glb_word, graph_words, derivations):
    """Collect translation tokens from all derived forms of a word."""
    tokens = set()
    for d in get_derived_forms(glb_word, derivations):
        if d['word'] in graph_words:
            tokens |= graph_words[d['word']]['tokens']
    return tokens


def get_synonym_tokens(glb_word, graph_words, synonyms):
    """Collect translation tokens from synonyms."""
    bare = glb_word.lstrip('-')
    tokens = set()
    for syn in synonyms.get(bare, set()):
        if syn in graph_words:
            tokens |= graph_words[syn]['tokens']
    return tokens


# === Qdrant corpus checker ===

class QdrantCorpusChecker:
    """Checks corpus evidence via Qdrant semantic search."""

    def __init__(self):
        self._client = None
        self._model = None
        self._cache = {}

    def _ensure_ready(self):
        if self._client is None:
            from qdrant_client import QdrantClient
            self._client = QdrantClient(url=QDRANT_URL)
        if self._model is None:
            from fastembed import TextEmbedding
            print("  Loading embedding model (one-time)...")
            cache_dir = os.path.expanduser("~/.cache/fastembed")
            self._model = TextEmbedding(MODEL_NAME, cache_dir=cache_dir)

    def search(self, query_text, limit=5):
        if query_text in self._cache:
            return self._cache[query_text]

        self._ensure_ready()
        embedding = list(self._model.embed([query_text]))[0]
        response = self._client.query_points(
            collection_name=COLLECTION_NAME,
            query=embedding.tolist(),
            using=VECTOR_NAME,
            limit=limit,
        )

        parsed = []
        for hit in response.points:
            meta = hit.payload.get('metadata', {})
            parsed.append({
                'score': hit.score,
                'globasa_text': meta.get('globasa_text', ''),
                'english_text': meta.get('english_text', ''),
                'source': meta.get('source_context', ''),
            })
        self._cache[query_text] = parsed
        return parsed

    def check_corpus(self, glb_word, definition, examples, derived_forms,
                     min_witnesses=2, min_score=0.4):
        """Search for corpus evidence that the Globasa word is used in the sense
        described by `definition` and `examples`.

        CONSERVATIVE: requires multiple independent corpus witnesses that are
        semantically similar to the sense's example sentences (not just the
        definition). Each witness must:
          - contain the Globasa word (or a derived form)
          - have a similarity score >= min_score
          - share content words with the definition or examples

        Returns (found: bool, witnesses: list[dict]).
        """
        bare = glb_word.lstrip('-')
        is_affix = glb_word.startswith('-')

        forms = {bare}
        if not is_affix:
            for d in derived_forms:
                forms.add(d['word'])

        # Collect content words from definition + examples for relevance check
        sense_words = content_words(definition)
        for ex in examples:
            if ex:
                sense_words |= content_words(ex)

        # Search using each example sentence AND the definition as queries.
        # Deduplicate by corpus Globasa text to avoid counting the same
        # segment found via different queries.
        queries = [definition]
        for ex in examples:
            if ex and len(ex) > 15:
                queries.append(ex)

        seen_glb_texts = set()
        witnesses = []

        for query in queries:
            results = self.search(query, limit=5)
            for result in results:
                if result['score'] < min_score:
                    continue

                glb_text = result['globasa_text']
                if glb_text in seen_glb_texts:
                    continue

                glb_text_lower = glb_text.lower()

                # Check if the Globasa word appears (word boundary)
                word_found = False
                for form in forms:
                    if re.search(r'(?<![a-z])' + re.escape(form) + r'(?![a-z])',
                                 glb_text_lower):
                        word_found = True
                        break
                if not word_found:
                    continue

                # Verify semantic relevance
                eng_words = content_words(result['english_text'])
                relevance = sense_words & eng_words
                if not relevance:
                    continue

                seen_glb_texts.add(glb_text)
                witnesses.append(result)

                if len(witnesses) >= min_witnesses:
                    return True, witnesses

        return False, witnesses


# === Judgement engine ===

def check_register_domain(sense_label):
    """Return (register_marker, domain_marker) found in the sense label."""
    if not sense_label:
        return None, None
    lower = sense_label.lower()
    register = next((m for m in REGISTER_MARKERS if m in lower), None)
    domain = next((m for m in DOMAIN_MARKERS if m in lower), None)
    return register, domain


def judge_row(glb, eng, sense_label, definition, spa, epo,
              graph_words, word_list, derivations, synonyms, qdrant,
              examples=None):
    """
    Three-tier judgement pipeline.

    Returns (judgement, score, tier, reason):
      judgement: 's', 'n', or None (skip)
      score:     numeric confidence
      tier:      1/2/3/4 indicating which tier decided, 0 = skip
      reason:    human-readable explanation
    """
    if not definition:
        return None, 0, 0, "no definition"

    word_tokens = get_word_tokens(glb, graph_words, word_list)
    derived_tokens = get_derived_tokens(glb, graph_words, derivations)
    synonym_tokens = get_synonym_tokens(glb, graph_words, synonyms)
    def_tokens = content_words(definition)

    if not def_tokens:
        return None, 0, 0, "empty definition after tokenization"

    # --- Tier 1: Core Meaning Match ---
    # CONSERVATIVE: only mark 's' with 2+ substantive overlapping words.
    # Single-word overlap is too prone to false positives (e.g. "turn"
    # matching both "become" and "rotate" senses). Let the LLM handle those.
    direct_overlap = word_tokens & def_tokens
    derived_overlap = derived_tokens & def_tokens

    # Filter to substantive overlaps (len >= 4) to avoid matching on
    # short generic words like "set", "run", "get", "act"
    strong_overlap = {w for w in direct_overlap if len(w) >= 4}

    if len(strong_overlap) >= 2:
        return 's', 3, 1, f"strong core: {strong_overlap}"

    # --- Tier 2: Register / Domain Filter ---
    register, domain = check_register_domain(sense_label)
    has_marker = register or domain

    if has_marker and len(direct_overlap) == 0 and len(derived_overlap) == 0:
        marker = register or domain
        return 'n', -2, 2, f"marker '{marker}', no translation overlap"

    # --- Tier 3: Corpus Corroboration ---
    # Requires 2+ independent corpus witnesses semantically similar to
    # the sense's examples, with the Globasa word present in context.
    if qdrant:
        derived_forms = get_derived_forms(glb, derivations)
        found, witnesses = qdrant.check_corpus(
            glb, definition, examples or [], derived_forms)
        if found:
            w0 = witnesses[0]
            return ('s', 3, 3,
                    f"corpus ({len(witnesses)} witnesses): "
                    f"'{w0['english_text'][:50]}' ...")

    # --- Tier 4: Composite — requires multiple corroborating signals ---
    # Raised threshold to +3: needs at least 3 independent signals to
    # mark 's' without LLM review. This prevents false positives from
    # weak coincidental overlaps.
    score = 0
    reasons = []

    if strong_overlap:
        score += 1
        reasons.append(f"overlap: {strong_overlap}")
    if derived_overlap:
        score += 1
        reasons.append(f"derivation: {derived_overlap}")
    if has_unslashed_words(spa):
        score += 1
        reasons.append("Spa match")
    if has_unslashed_words(epo):
        score += 1
        reasons.append("Epo match")
    if register:
        score -= 2
        reasons.append(f"register:{register}")
    if domain:
        score -= 2
        reasons.append(f"domain:{domain}")

    if score >= 3:
        return 's', score, 4, f"composite: {'; '.join(reasons)}"
    if score <= -2:
        return 'n', score, 4, f"composite: {'; '.join(reasons)}"

    return None, score, 0, f"uncertain ({score}): {'; '.join(reasons) or 'no signals'}"


# === Tier 5: LLM semantic reasoning (WordNet + homonym detection) ===

def _expand_with_wn(tokens, core_filter=None):
    """Expand translation tokens via WordNet + supplement dict.

    core_filter: if provided, passed to wn_expand to filter homonym synsets.
    """
    expanded = set(tokens)
    for tok in tokens:
        expanded |= wn_expand(tok, core_filter=core_filter)
        if tok in SYNONYM_FIELDS_SUPPLEMENT:
            expanded |= SYNONYM_FIELDS_SUPPLEMENT[tok]
    return expanded


def _check_negative_domain(def_lower):
    """Check if definition is in a specialized negative domain (homonym trap)."""
    for domain, keywords in NEGATIVE_DOMAINS.items():
        for kw in keywords:
            if kw in def_lower:
                return domain
    return None


def judge_llm(glb, eng, sense_label, definition,
              word_tokens, derived_tokens, synonym_tokens,
              core_filter=None):
    """Tier 5: WordNet-powered semantic reasoning for corner cases.

    Uses synonym/hypernym expansion (filtered to relevant synsets via
    core_filter), homonym detection, and domain-keyword filtering.
    Returns (judgement, score, reason) or (None, 0, reason) to skip.
    """
    if not definition:
        return None, 0, "no definition"

    def_lower = definition.lower()
    def_words = content_words(definition)
    if not def_words:
        return None, 0, "empty definition"

    # Expand via WordNet, using core_filter to skip homonym synsets
    expanded_word = _expand_with_wn(word_tokens, core_filter)
    expanded_derived = _expand_with_wn(derived_tokens, core_filter)
    expanded_all = expanded_word | expanded_derived | _expand_with_wn(
        synonym_tokens, core_filter)

    # CONSERVATIVE: only mark 's' with 2+ substantive WordNet hits.
    # Single-hit matches are too prone to false positives from polysemous
    # expansion. Let the LLM tier handle single-hit cases.

    word_hits = {w for w in (expanded_word & def_words) if len(w) >= 4}
    all_hits = {w for w in (expanded_all & def_words) if len(w) >= 4}

    if len(word_hits) >= 2:
        return 's', 3, f"WN match: {word_hits}"

    # Negative signals — these are safe because false negatives go to LLM

    # Homonym domain check
    neg_domain = _check_negative_domain(def_lower)
    if neg_domain and not all_hits:
        return 'n', -2, f"WN homonym: {neg_domain}"

    # Cross-domain homonym detection (leadership ↔ body part)
    word_is_leadership = bool(word_tokens & LEADERSHIP_WORDS)
    word_is_body = bool(word_tokens & BODYPART_WORDS) or bool(
        word_tokens & {'head', 'hand', 'foot', 'eye', 'ear', 'nose',
                       'mouth', 'neck', 'back', 'tongue', 'tooth'})
    def_about_body = bool(def_words & BODYPART_WORDS)
    def_about_leadership = bool(def_words & LEADERSHIP_WORDS)

    if word_is_leadership and def_about_body and not def_about_leadership:
        return 'n', -2, "WN: leadership word, body-part sense"
    if word_is_body and def_about_leadership and not def_about_body:
        return 'n', -2, "WN: body-part word, leadership sense"

    # Everything else → leave for LLM tier
    return None, 0, "WN: no confident signal"


# === Tier 6: Local LLM (Qwen via llama-cpp) ===
#
# Context sources:
#   - LadybugDB (Kuzu graph): derivations, synonyms, antonyms reveal
#     which senses the language has lexicalized, narrowing which English
#     senses apply. E.g. bimarya (illness), bimargi (make sick) confirms
#     the medical sense of bimar but not the slang "cool" sense.
#   - Qdrant corpus: for each sense's Wiktionary example sentences,
#     search the Globasa parallel corpus. Hits containing the Globasa
#     word in a semantically matching context are evidence the sense
#     is used in Globasa.

QWEN_MODEL_PATH = "/media/paleos/Warehouse2/LLM/-Q8_0.gguf"

LLM_SYSTEM_PROMPT = """\
You are judging whether English Wiktionary senses are applicable translations \
for words in Globasa, an international auxiliary constructed language.

Globasa targets core, universal meanings. A sense is APPLICABLE ('s') if it \
falls within the normal semantic scope of the Globasa word. A sense is NOT \
APPLICABLE ('n') if it is:
- A different homonym (e.g. "ball" as formal dance when the Globasa word means sphere)
- Slang, figurative, or culture-specific usage unrelated to the core meaning
- A specialized domain term unless the Globasa word is in that domain
- A meaning covered by a DIFFERENT Globasa word

You are given two kinds of evidence:
1. LEXICON GRAPH (derivations, synonyms, antonyms): these show which senses \
Globasa has lexicalized. If a derived form exists for a meaning, that meaning \
is part of the word's scope. If a synonym covers a sense, the word may not \
need to cover it. Antonyms hint at the word's semantic axis.
2. CORPUS EVIDENCE: for each sense, I searched example sentences from \
Wiktionary against a Globasa parallel corpus. Hits containing the Globasa \
word in a semantically relevant context support applicability. Absence of \
evidence is NOT evidence against (the corpus is small).

Be conservative: when unsure, answer '?' to skip rather than guessing."""

LLM_USER_TEMPLATE = """\
Globasa word: {glb}
Meaning: {translation}

Lexicon graph:
{graph_context}

{senses_with_evidence}

Reply ONLY with the number and 's', 'n', or '?' (uncertain), one per line."""


class LocalLLM:
    """Qwen3.5-9B via llama-cpp-python, with graph + corpus context."""

    def __init__(self, qdrant_checker, graph_words, derivations, synonyms,
                 antonyms):
        self._llm = None
        self._qdrant = qdrant_checker
        self._graph_words = graph_words
        self._derivations = derivations
        self._synonyms = synonyms
        self._antonyms = antonyms

    def _ensure_ready(self):
        if self._llm is not None:
            return
        from llama_cpp import Llama
        print("  Loading Qwen3.5-9B...")
        self._llm = Llama(
            model_path=QWEN_MODEL_PATH,
            n_ctx=4096,
            n_gpu_layers=-1,
            verbose=False,
        )
        print("  Model loaded.")

    def _build_graph_context(self, glb):
        """Build lexicon graph context showing how the word's senses are
        lexicalized through derivations, synonyms, and antonyms."""
        bare = glb.lstrip('-')
        lines = []

        # Derivations — show what meanings are baked into the language
        derivs = self._derivations.get(bare, [])
        if derivs:
            parts = []
            for d in derivs[:12]:
                info = self._graph_words.get(d['word'], {})
                trans = info.get('translation_eng', '')
                if trans:
                    parts.append(f"  {d['word']} ({d['affix']}): {trans}")
            if parts:
                lines.append("Derived forms (lexicalized senses):\n"
                             + "\n".join(parts))

        # Synonyms — reveal overlapping coverage
        bare_syns = self._synonyms.get(bare, set())
        if bare_syns:
            syn_parts = []
            for s in sorted(bare_syns)[:5]:
                info = self._graph_words.get(s, {})
                trans = info.get('translation_eng', '')
                if trans:
                    syn_parts.append(f"  {s}: {trans}")
            if syn_parts:
                lines.append("Synonyms (overlapping words):\n"
                             + "\n".join(syn_parts))

        # Antonyms — reveal the semantic axis
        bare_ants = self._antonyms.get(bare, set())
        if bare_ants:
            ant_parts = []
            for a in sorted(bare_ants)[:5]:
                info = self._graph_words.get(a, {})
                trans = info.get('translation_eng', '')
                if trans:
                    ant_parts.append(f"  {a}: {trans}")
            if ant_parts:
                lines.append("Antonyms (semantic axis):\n"
                             + "\n".join(ant_parts))

        return "\n".join(lines) if lines else "(no lexicon graph data)"

    def _search_sense_evidence(self, glb, defn, examples):
        """Search Qdrant for corpus witnesses for this sense.

        Uses the same check_corpus method as the script tiers but with
        min_witnesses=1 (the LLM will judge the evidence quality).
        Returns formatted evidence lines for the LLM prompt.
        """
        if not self._qdrant:
            return []
        bare = glb.lstrip('-')
        derived_forms = self._derivations.get(bare, [])
        _, witnesses = self._qdrant.check_corpus(
            glb, defn, examples, derived_forms,
            min_witnesses=3, min_score=0.3)
        return [f"    {w['globasa_text']} → {w['english_text']} "
                f"(score={w['score']:.2f})" for w in witnesses]

    def judge_batch(self, glb, translation, senses_with_examples):
        """Judge a batch of senses for one Globasa word.

        senses_with_examples: list of (row_idx, eng, sense_label, definition,
                                       [example1, example2, example3]) tuples
        Returns: dict {row_idx: ('s'|'n'|None, reason)}
        """
        self._ensure_ready()

        graph_ctx = self._build_graph_context(glb)

        # Build senses block with per-sense corpus evidence
        sense_blocks = []
        for i, (idx, eng, sense_label, defn, examples) in enumerate(
                senses_with_examples, 1):
            label = f" [{sense_label}]" if sense_label else ""
            block = f"{i}. ({eng}){label}: {defn}"

            evidence = self._search_sense_evidence(glb, defn, examples)
            if evidence:
                block += "\n  Corpus evidence:\n" + "\n".join(evidence[:4])
            else:
                block += "\n  (no corpus evidence)"

            sense_blocks.append(block)

        user_msg = LLM_USER_TEMPLATE.format(
            glb=glb,
            translation=translation,
            graph_context=graph_ctx,
            senses_with_evidence="\n\n".join(sense_blocks),
        )

        prompt = (f"<|im_start|>system\n{LLM_SYSTEM_PROMPT}<|im_end|>\n"
                  f"<|im_start|>user\n{user_msg}<|im_end|>\n"
                  f"<|im_start|>assistant\n")

        resp = self._llm(
            prompt,
            max_tokens=len(senses_with_examples) * 8 + 50,
            temperature=0.1,
            stop=["<|im_end|>"],
        )

        text = resp['choices'][0]['text'].strip()
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

        results = {}
        for line in text.split('\n'):
            line = line.strip()
            m = re.match(r'(\d+)\s+([sn?])\b', line)
            if m:
                num = int(m.group(1))
                answer = m.group(2)
                if 1 <= num <= len(senses_with_examples):
                    orig_idx = senses_with_examples[num - 1][0]
                    if answer == '?':
                        results[orig_idx] = (None, "Qwen: uncertain")
                    else:
                        results[orig_idx] = (answer, f"Qwen: {line.strip()}")

        return results


# === Main ===

import signal

_interrupted = False


def _handle_sigint(sig, frame):
    global _interrupted
    _interrupted = True
    print("\n*** Interrupted — will save progress after current word ***")


def _save(wb, excel_path):
    """Backup and save the workbook."""
    backup_dir = os.path.dirname(excel_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"GLB_ENG_WiktionarySenses_backup_{timestamp}.xlsx"
    backup_path = os.path.join(backup_dir, backup_name)
    shutil.copy2(excel_path, backup_path)
    print(f"  Backup: {backup_path}")
    wb.save(excel_path)
    print(f"  Saved:  {excel_path}")


def main():
    global _interrupted

    use_llm = '--no-llm' not in sys.argv

    # --- Load data ---
    print("Loading graph data...")
    graph_words, derivations, synonyms, antonyms = load_graph_data()
    print(f"  {len(graph_words)} words, "
          f"{sum(len(v) for v in derivations.values())} derivations, "
          f"{sum(len(v) for v in synonyms.values())} synonym links, "
          f"{sum(len(v) for v in antonyms.values())} antonym links")

    print("Loading word list...")
    word_list = load_word_list()
    print(f"  {len(word_list)} translations")

    # Qdrant: try to connect, fall back gracefully
    qdrant = None
    try:
        qdrant = QdrantCorpusChecker()
        qdrant._ensure_ready()
        print("Qdrant corpus checker: ready")
    except Exception as e:
        print(f"Qdrant unavailable ({e}) — Tier 3 and corpus evidence disabled")
        qdrant = None

    # --- Load Excel ---
    print(f"Loading Excel: {EXCEL_PATH}")
    wb = openpyxl.load_workbook(EXCEL_PATH)
    ws = wb.active
    headers = [cell.value for cell in ws[1]]

    TIER_COL = 'Tier'
    if TIER_COL not in headers:
        tier_col_idx = len(headers) + 1
        ws.cell(row=1, column=tier_col_idx, value=TIER_COL)
        headers.append(TIER_COL)
        print(f"  Added '{TIER_COL}' column at position {tier_col_idx}")

    col = {h: i for i, h in enumerate(headers)}

    # --- Collect all rows grouped by Globasa word ---
    word_rows = defaultdict(list)  # glb -> [(row_idx, row_obj, eng, sense, defn, spa, epo, ex1, ex2, ex3)]
    already_judged = 0
    no_def = 0
    for idx, row in enumerate(ws.iter_rows(min_row=2), start=2):
        if row[col['App?']].value or row[col[TIER_COL]].value:
            already_judged += 1
            continue
        glb = row[col['Glb']].value or ''
        defn = row[col['Definition']].value
        if not defn:
            no_def += 1
            continue
        eng = row[col['Eng']].value
        sense = row[col['Wiktionary Sense (in Translations)']].value
        spa = row[col['Spa']].value if 'Spa' in col else None
        epo = row[col['Epo']].value if 'Epo' in col else None
        ex1 = row[col['Example']].value if 'Example' in col else ''
        ex2 = row[col['Example 2']].value if 'Example 2' in col else ''
        ex3 = row[col['Example 3']].value if 'Example 3' in col else ''
        word_rows[glb].append((idx, row, eng, sense, defn, spa, epo,
                               ex1 or '', ex2 or '', ex3 or ''))

    # Sort words alphabetically
    sorted_words = sorted(word_rows.keys())
    total_unjudged = sum(len(v) for v in word_rows.values())

    print(f"\n{already_judged} already judged, {no_def} no definition, "
          f"{total_unjudged} unjudged across {len(sorted_words)} words")

    # --- Start prefix ---
    start_prefix = input(
        "Start prefix (hit enter for beginning, or e.g. 'k' to start from k):\n"
    ).strip()

    # --- Init local LLM if needed ---
    local_llm = None
    if use_llm and os.path.exists(QWEN_MODEL_PATH):
        local_llm = LocalLLM(qdrant, graph_words, derivations, synonyms,
                             antonyms)
        print(f"Tier 6 (Qwen LLM): enabled")
    elif use_llm:
        print(f"Tier 6: model not found at {QWEN_MODEL_PATH}")
    else:
        print("Tier 6: disabled (--no-llm)")

    # --- Install signal handler ---
    signal.signal(signal.SIGINT, _handle_sigint)

    # --- Process word by word ---
    stats = defaultdict(int)   # s, n, skip per tier
    tier_counts = defaultdict(lambda: {'s': 0, 'n': 0})
    started = not bool(start_prefix)
    words_done = 0

    for glb in sorted_words:
        if _interrupted:
            break

        if not started:
            if glb.lstrip('-').startswith(start_prefix):
                started = True
            else:
                continue

        senses = word_rows[glb]
        bare = glb.lstrip('-')
        info = graph_words.get(glb, graph_words.get(bare, {}))
        translation = info.get('translation_eng', glb)

        word_s, word_n, word_skip, word_llm_s, word_llm_n = 0, 0, 0, 0, 0

        # --- Tiers 1-5 (Tier=a) ---
        llm_candidates = []  # rows that need Tier 6

        for (idx, row, eng, sense, defn, spa, epo,
             ex1, ex2, ex3) in senses:

            # Tiers 1-4
            examples = [ex1, ex2, ex3]
            judgement, score, tier, reason = judge_row(
                glb, eng, sense, defn, spa, epo,
                graph_words, word_list, derivations, synonyms, qdrant,
                examples=examples,
            )

            # Tier 5: WordNet expansion fallback
            if not judgement:
                wt = get_word_tokens(glb, graph_words, word_list)
                dt = get_derived_tokens(glb, graph_words, derivations)
                st = get_synonym_tokens(glb, graph_words, synonyms)
                cf = get_core_tokens(glb, graph_words)
                judgement, score, reason = judge_llm(
                    glb, eng, sense, defn, wt, dt, st,
                    core_filter=cf or None,
                )
                tier = 5 if judgement else 0

            if judgement:
                row[col['App?']].value = judgement
                row[col[TIER_COL]].value = 'a'
                tier_counts[tier][judgement] += 1
                if judgement == 's':
                    word_s += 1
                else:
                    word_n += 1
            else:
                llm_candidates.append(
                    (idx, row, eng, sense, defn, [ex1, ex2, ex3]))
                word_skip += 1

        # --- Tier 6 (Tier=l) on remaining ---
        if local_llm and llm_candidates and not _interrupted:
            batched = [(idx, eng, sense, defn, exs)
                       for idx, row, eng, sense, defn, exs in llm_candidates]

            for batch_start in range(0, len(batched), 15):
                if _interrupted:
                    break
                batch = batched[batch_start:batch_start + 15]
                try:
                    results = local_llm.judge_batch(glb, translation, batch)
                except Exception as e:
                    print(f"    LLM error: {e}")
                    continue

                for row_idx, (judgement, reason) in results.items():
                    if judgement:
                        # Find the row object from llm_candidates
                        for (cidx, crow, *_) in llm_candidates:
                            if cidx == row_idx:
                                crow[col['App?']].value = judgement
                                crow[col[TIER_COL]].value = 'l'
                                break
                        tier_counts[6][judgement] += 1
                        if judgement == 's':
                            word_llm_s += 1
                        else:
                            word_llm_n += 1
                        word_skip -= 1

        # --- Progress line ---
        words_done += 1
        total_s = word_s + word_llm_s
        total_n = word_n + word_llm_n
        parts = []
        if total_s:
            parts.append(f"\033[32m{total_s}s\033[0m")
        if total_n:
            parts.append(f"\033[31m{total_n}n\033[0m")
        if word_skip:
            parts.append(f"{word_skip}?")
        judgement_str = " ".join(parts) if parts else "skip"

        print(f"  {glb:25s} ({translation[:35]:35s})  "
              f"[{judgement_str}]", flush=True)

        stats['s'] += total_s
        stats['n'] += total_n
        stats['skip'] += word_skip

    # --- Save ---
    print(f"\n{'INTERRUPTED — ' if _interrupted else ''}"
          f"Saving {stats['s']}s + {stats['n']}n "
          f"({stats['skip']} still unjudged, {words_done} words processed)...")
    _save(wb, EXCEL_PATH)

    # --- Summary ---
    print("\nPer tier:")
    for t in sorted(tier_counts):
        ts = tier_counts[t]
        label = {1: "Core match", 2: "Register/domain", 3: "Corpus",
                 4: "Composite", 5: "WordNet", 6: "Qwen LLM"}
        marker = "Tier=l" if t == 6 else "Tier=a"
        print(f"  T{t} {label.get(t, '?'):16s} [{marker:7s}]:"
              f"  s={ts['s']:>5}  n={ts['n']:>5}")


main()
