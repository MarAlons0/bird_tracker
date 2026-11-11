"""Bird category classification — the single source of truth.

Every consumer reads from here: the live map (`home.html` gets the keywords,
colours, and labels injected via `client_config()`), the newsletter map
(`email_service`), the `/api/sightings` `category` field, and the keyword audit
script (`scripts/audit_categories.py`). Edit keywords/colours here only.

Classification looks at the name's head noun first — English bird names put
the kind of bird last ("Crane Hawk", "Turkey Vulture", "Parrot-billed
Seedeater", "Hawk-Cuckoo") — and only falls back to the whole name when the head
matches no keyword ("Chuck-will's-widow", "Greater Prairie-Chicken"). Within
each pass, the first group in TIER1_KEYWORDS order wins. The JS copy of this
rule is `getBirdCategory` in home.html; keep the two in step.

Check changes with `scripts/audit_categories.py --taxonomy`, which classifies
every US/Canada species and compares against eBird's taxonomic families.
"""
import re

# Hex without the leading '#' (Mapbox static markers want bare hex).
GROUP_COLORS = {
    'waterbirds':         '377eb8',
    'raptors':            'e41a1c',
    'ground-birds':       'a0522d',
    'aerial-specialists': 'ff69b4',
    'tree-specialists':   '228b22',
    'perching-birds':     '4daf4a',
    'other':              'ff7f00',
}

GROUP_LABELS = {
    'waterbirds':         'Waterbirds',
    'raptors':            'Raptors',
    'ground-birds':       'Ground Birds',
    'aerial-specialists': 'Aerial Specialists',
    'tree-specialists':   'Tree Specialists',
    'perching-birds':     'Perching Birds',
    'other':              'Other',
}

# Most-notable first — used to pick a representative colour when one map spot
# holds several groups (a hawk shouldn't be hidden under a flock of sparrows).
CATEGORY_PRIORITY = [
    'raptors', 'waterbirds', 'ground-birds', 'aerial-specialists',
    'tree-specialists', 'perching-birds', 'other',
]

TIER1_KEYWORDS = {
    'waterbirds': [
        'duck', 'goose', 'geese', 'swan', 'teal', 'mallard', 'pintail', 'shoveler',
        'gadwall', 'wigeon', 'scaup', 'canvasback', 'redhead', 'bufflehead',
        'merganser', 'scoter', 'eider', 'goldeneye',
        'heron', 'egret', 'bittern', 'ibis', 'spoonbill', 'stork',
        'sandpiper', 'plover', 'dowitcher', 'yellowlegs', 'dunlin', 'knot',
        'turnstone', 'godwit', 'curlew', 'whimbrel', 'snipe', 'woodcock',
        'avocet', 'stilt', 'phalarope', 'oystercatcher',
        'killdeer', 'sanderling', 'willet',
        'gull', 'tern', 'skimmer', 'jaeger', 'kittiwake',
        'grebe', 'loon',
        'cormorant', 'pelican', 'anhinga', 'gannet', 'booby', 'frigatebird',
        'tropicbird', 'skua', 'murre', 'puffin', 'razorbill', 'guillemot', 'auklet',
        'coot', 'gallinule', 'moorhen', 'rail', 'sora', 'swamphen',
        'crane', 'limpkin',
        'brant', 'smew', 'garganey', 'shelduck', 'pochard', 'flamingo', 'jabiru',
        'noddy', 'crake', 'jacana', 'thick-knee', 'pratincole', 'darter',
        'ruff', 'stint', 'redshank', 'greenshank', 'tattler', 'surfbird',
        'dotterel', 'lapwing', 'murrelet', 'dovekie',
        'albatross', 'shearwater', 'petrel', 'fulmar',
    ],
    'raptors': [
        'eagle', 'hawk', 'falcon', 'owl', 'kite', 'harrier', 'osprey',
        'vulture', 'condor', 'merlin', 'kestrel', 'caracara',
        'goshawk', 'sparrowhawk', 'buzzard', 'gyrfalcon', 'hobby', 'boobook',
    ],
    'ground-birds': [
        'turkey', 'grouse', 'quail', 'pheasant', 'partridge', 'ptarmigan',
        'prairie-chicken', 'roadrunner', 'bobwhite',
        'pigeon', 'dove', 'parakeet', 'parrot', 'macaw',
        'peafowl', 'junglefowl',
        'chukar', 'francolin', 'spurfowl', 'snowcock', 'chachalaca', 'guineafowl',
        'sandgrouse', 'tinamou',
        'amazon', 'parrotlet', 'lovebird', 'lorikeet', 'lory', 'rosella',
        'budgerigar', 'cockatiel', 'cockatoo', 'corella', 'galah', 'eclectus',
    ],
    'aerial-specialists': [
        'swallow', 'swift', 'martin', 'hummingbird', 'nighthawk', 'nightjar',
        'whip-poor-will', 'chuck-will', 'poorwill',
        'pauraque', 'swiftlet', 'needletail',
        'woodstar', 'starthroat', 'violetear', 'mountain-gem', 'mango',
    ],
    'tree-specialists': [
        'woodpecker', 'sapsucker', 'flicker', 'kingfisher', 'nuthatch', 'creeper',
        'wryneck', 'trogon', 'quetzal',
    ],
    'perching-birds': [
        'sparrow', 'finch', 'warbler', 'thrush', 'robin', 'blackbird', 'oriole',
        'jay', 'crow', 'raven', 'magpie', 'wren', 'chickadee', 'titmouse',
        'flycatcher', 'phoebe', 'pewee', 'kingbird', 'vireo', 'tanager',
        'grosbeak', 'bunting', 'towhee', 'junco', 'lark', 'pipit',
        'mockingbird', 'catbird', 'thrasher', 'starling', 'waxwing',
        'shrike', 'kinglet', 'gnatcatcher', 'bluebird', 'veery', 'solitaire',
        'redstart', 'ovenbird', 'waterthrush', 'siskin', 'crossbill',
        'redpoll', 'goldfinch', 'grackle', 'cowbird', 'cardinal',
        'parula', 'yellowthroat', 'longspur', 'bushtit', 'verdin',
        'phainopepla', 'cuckoo', 'chat', 'meadowlark', 'pyrrhuloxia',
        'dickcissel', 'bobolink', 'wrentit', 'dipper', 'nutcracker', 'jackdaw',
        'kiskadee', 'tyrannulet', 'elaenia', 'tyrant', 'becard', 'tityra',
        'antshrike', 'ani', 'oropendola', 'troupial', 'cacique',
        'skylark', 'accentor', 'wagtail', 'tit', 'wheatear', 'bluethroat',
        'stonechat', 'bluetail', 'rubythroat', 'shama', 'fieldfare', 'redwing',
        'chiffchaff', 'whitethroat', 'whitestart', 'yellowhammer',
        'laughingthrush', 'leiothrix', 'leafbird', 'parrotbill', 'bulbul',
        'finchbill', 'myna', 'white-eye',
        'canary', 'chaffinch', 'brambling', 'hawfinch', 'bullfinch', 'greenfinch',
        'rosefinch', 'linnet', 'serin', 'seedeater', 'grassquit', 'honeycreeper',
        'bananaquit', 'spindalis',
        'waxbill', 'munia', 'mannikin', 'silverbill', 'firefinch', 'cordonbleu',
        'avadavat', 'firetail', 'pytilia', 'twinspot', 'weaver', 'bishop', 'fody',
        'quelea', 'widowbird', 'whydah', 'indigobird',
    ],
}


_PATTERNS = [
    (category, [re.compile(r'\b' + re.escape(kw) + r'\b') for kw in keywords])
    for category, keywords in TIER1_KEYWORDS.items()
]


def _first_match(text):
    for category, patterns in _PATTERNS:
        if any(p.search(text) for p in patterns):
            return category
    return None


def categorize(com_name):
    """Return the tier-1 group for a bird common name.

    Head noun first (last word, last hyphen part), then the whole name.
    """
    words = (com_name or '').lower().split()
    if not words:
        return 'other'
    head = words[-1].split('-')[-1]
    return _first_match(head) or _first_match(' '.join(words)) or 'other'


def client_config():
    """Classifier data for the live map's JS, injected into `home.html`.

    Everything is emitted as ordered [key, value] pairs rather than dicts:
    Flask's `tojson` sorts dict keys, which would silently reorder group
    precedence and the legend. The JS rebuilds each with `Object.fromEntries`,
    which keeps this order.
    """
    return {
        'keywords': [[cat, kws] for cat, kws in TIER1_KEYWORDS.items()],
        'colors': [[cat, '#' + hex_] for cat, hex_ in GROUP_COLORS.items()],
        'labels': [[cat, label] for cat, label in GROUP_LABELS.items()],
    }
