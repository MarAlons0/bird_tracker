"""Bird category classification — the single source of truth.

Every consumer reads from here: the live map (`home.html` gets the keywords,
colours, and labels injected via `client_config()`), the newsletter map
(`email_service`), the `/api/sightings` `category` field, and the keyword audit
script (`scripts/audit_categories.py`). Edit keywords/colours here only.

Classification is first-match in TIER1_KEYWORDS order, so the order of the
groups is precedence: "Turkey Vulture" is a raptor only because raptors are
checked before ground-birds.
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
    ],
    'raptors': [
        'eagle', 'hawk', 'falcon', 'owl', 'kite', 'harrier', 'osprey',
        'vulture', 'condor', 'merlin', 'kestrel', 'caracara',
    ],
    'ground-birds': [
        'turkey', 'grouse', 'quail', 'pheasant', 'partridge', 'ptarmigan',
        'prairie-chicken', 'roadrunner', 'bobwhite',
        'pigeon', 'dove', 'parakeet', 'parrot', 'macaw',
        'peafowl', 'junglefowl',
    ],
    'aerial-specialists': [
        'swallow', 'swift', 'martin', 'hummingbird', 'nighthawk', 'nightjar',
        'whip-poor-will', 'chuck-will', 'poorwill',
    ],
    'tree-specialists': [
        'woodpecker', 'sapsucker', 'flicker', 'kingfisher', 'nuthatch', 'creeper',
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
    ],
}


def categorize(com_name):
    """Return the tier-1 group for a bird common name (word-boundary match)."""
    if not com_name:
        return 'other'
    name = com_name.lower()
    for category, keywords in TIER1_KEYWORDS.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', name):
                return category
    return 'other'


def client_config():
    """Classifier data for the live map's JS, injected into `home.html`.

    Everything is emitted as ordered [key, value] pairs rather than dicts:
    Flask's `tojson` sorts dict keys, which would silently reorder keyword
    precedence (Turkey Vulture -> ground bird) and the legend. The JS rebuilds
    each with `Object.fromEntries`, which keeps this order.
    """
    return {
        'keywords': [[cat, kws] for cat, kws in TIER1_KEYWORDS.items()],
        'colors': [[cat, '#' + hex_] for cat, hex_ in GROUP_COLORS.items()],
        'labels': [[cat, label] for cat, label in GROUP_LABELS.items()],
    }
