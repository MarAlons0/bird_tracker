"""Bird category classification — Python mirror of the app map's classifier.

Keeps the keyword lists, group colors, and labels in sync with the inline JS in
`app/templates/home.html` (GROUP_COLORS / TIER1_KEYWORDS), so server-side
consumers like the newsletter colour sightings exactly the way the live map does.
If you edit the keywords/colours in home.html, update them here too.
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
        'roadrunner', 'bobwhite',
        'pigeon', 'dove', 'parakeet', 'parrot', 'macaw',
        'peafowl', 'junglefowl',
    ],
    'aerial-specialists': [
        'swallow', 'swift', 'martin', 'hummingbird', 'nighthawk', 'nightjar',
        'whip-poor-will', 'poorwill',
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
