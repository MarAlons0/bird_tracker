"""
Audit bird category classification against eBird data.

Two modes, both using the app's single source of truth,
app/services/bird_categories.py, so they audit exactly what the map and the
newsletter do. Re-run after eBird's annual taxonomy update (August).

  --taxonomy  (the thorough check) Classifies every species on eBird's US and
              Canada lists and compares each against the group implied by its
              taxonomic order/family. Reports species that fall to "Other" and
              species put in the WRONG group. Catches renames (e.g. Painted
              Redstart -> Painted Whitestart) and keyword collisions
              (e.g. "Crane Hawk" -> waterbirds) that the regional sample misses.
  (default)   Fetches the last 14 days of sightings at four contrasting sites
              and prints every species by group, plus everything in "Other" —
              a quick look at what is actually being seen right now.

Usage (from the repo root, with the project venv):
    EBIRD_API_KEY=your_key python3 scripts/audit_categories.py --taxonomy
    EBIRD_API_KEY=your_key python3 scripts/audit_categories.py
"""
import os
import sys
from collections import defaultdict

import requests

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from app.services.bird_categories import GROUP_LABELS, categorize  # noqa: E402

EBIRD_API_KEY = os.getenv('EBIRD_API_KEY')
BASE_URL = 'https://api.ebird.org/v2'

# Ground truth for --taxonomy: the group each taxonomic order/family should land
# in, following the app's own conventions (shorebirds, seabirds and rails are
# waterbirds; parrots and pigeons are ground birds; kingfishers, nuthatches and
# creepers are tree specialists; swallows are aerial specialists; cuckoos are
# perching birds except the roadrunner). Orders absent here (ratites, hornbills,
# turacos, hoopoes) are escaped exotics with no group, so "Other" is correct.
ORDER_GROUP = {
    **dict.fromkeys(['Accipitriformes', 'Falconiformes', 'Strigiformes',
                     'Cathartiformes'], 'raptors'),
    **dict.fromkeys(['Anseriformes', 'Gaviiformes', 'Podicipediformes',
                     'Pelecaniformes', 'Suliformes', 'Charadriiformes', 'Gruiformes',
                     'Ciconiiformes', 'Procellariiformes', 'Phaethontiformes',
                     'Phoenicopteriformes'], 'waterbirds'),
    **dict.fromkeys(['Galliformes', 'Columbiformes', 'Psittaciformes',
                     'Tinamiformes', 'Pterocliformes'], 'ground-birds'),
    **dict.fromkeys(['Apodiformes', 'Caprimulgiformes'], 'aerial-specialists'),
    **dict.fromkeys(['Piciformes', 'Coraciiformes', 'Trogoniformes'],
                    'tree-specialists'),
    'Passeriformes': 'perching-birds',
}
FAMILY_GROUP = {
    'Hirundinidae': 'aerial-specialists',   # swallows
    'Sittidae': 'tree-specialists',         # nuthatches
    'Certhiidae': 'tree-specialists',       # treecreepers
}
TAXONOMY_REGIONS = ['US', 'CA']


def expected_group(taxon):
    if taxon['familySciName'] in FAMILY_GROUP:
        return FAMILY_GROUP[taxon['familySciName']]
    if taxon['order'] == 'Cuculiformes':
        return 'ground-birds' if 'roadrunner' in taxon['comName'].lower() else 'perching-birds'
    return ORDER_GROUP.get(taxon['order'])


def ebird_get(path, **params):
    r = requests.get(f'{BASE_URL}{path}', params=params,
                     headers={'X-eBirdApiToken': EBIRD_API_KEY}, timeout=60)
    r.raise_for_status()
    return r.json()


def audit_taxonomy():
    taxonomy = {t['speciesCode']: t for t in
                ebird_get('/ref/taxonomy/ebird', fmt='json', cat='species')}
    codes = set()
    for region in TAXONOMY_REGIONS:
        codes |= set(ebird_get(f'/product/spplist/{region}'))
    species = [taxonomy[c] for c in codes if c in taxonomy]

    other, wrong = defaultdict(list), []
    for t in species:
        expected, actual = expected_group(t), categorize(t['comName'])
        if expected and actual == 'other':
            other[f"{expected} / {t['familyComName']}"].append(t['comName'])
        elif expected and actual != expected:
            wrong.append(f"{t['comName']} ({t['familyComName']}): "
                         f"expected {expected}, got {actual}")

    n_other = sum(len(v) for v in other.values())
    print(f"{len(species)} species on eBird's {'+'.join(TAXONOMY_REGIONS)} lists: "
          f"{n_other} fall to Other, {len(wrong)} in the wrong group")
    print(f"\nWRONG GROUP ({len(wrong)}) — fix these first")
    for line in sorted(wrong):
        print(f"  - {line}")
    print(f"\nFALL TO OTHER ({n_other}) — add a keyword unless it's an exotic or "
          f"Hawaiian endemic not worth one")
    for key in sorted(other):
        print(f"  {key}: {'; '.join(sorted(other[key]))}")

LOCATIONS = [
    ('Magee Marsh, Ohio (Midwest)',          41.46, -83.17),
    ('Bosque del Apache, NM (Semi-arid)',    33.78, -106.90),
    ('Great Smoky Mtns, TN (Temperate)',     35.65, -83.50),
    ('Corkscrew Swamp, FL (Tropical)',       26.37, -81.61),
]


def fetch_observations(lat, lng, radius=25, days_back=14):
    url = f'{BASE_URL}/data/obs/geo/recent'
    params = {'lat': lat, 'lng': lng, 'dist': radius, 'back': days_back, 'fmt': 'json'}
    headers = {'X-eBirdApiToken': EBIRD_API_KEY}
    r = requests.get(url, params=params, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()


def audit_location(name, lat, lng):
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    obs = fetch_observations(lat, lng)
    species_seen = {}
    for o in obs:
        cn = o.get('comName', '')
        if cn and cn not in species_seen:
            species_seen[cn] = categorize(cn)

    by_category = defaultdict(list)
    for species, cat in species_seen.items():
        by_category[cat].append(species)

    total = len(species_seen)
    for cat in GROUP_LABELS:
        items = sorted(by_category[cat])
        pct = len(items) / total * 100 if total else 0
        print(f"\n{cat.upper()} ({len(items)}, {pct:.0f}%)")
        for s in items:
            print(f"  - {s}")

    other = by_category['other']
    pct_other = len(other) / total * 100 if total else 0
    print(f"\n--- SUMMARY: {total} unique species, {len(other)} unclassified ({pct_other:.0f}%) ---")
    return other


if __name__ == '__main__':
    if not EBIRD_API_KEY:
        print("ERROR: Set EBIRD_API_KEY environment variable")
        sys.exit(1)

    if '--taxonomy' in sys.argv[1:]:
        audit_taxonomy()
        sys.exit(0)

    all_others = []
    for name, lat, lng in LOCATIONS:
        others = audit_location(name, lat, lng)
        all_others.extend(others)

    unique_others = sorted(set(all_others))
    print(f"\n{'='*60}")
    print(f"ALL UNCLASSIFIED SPECIES ACROSS ALL LOCATIONS ({len(unique_others)})")
    print(f"{'='*60}")
    for s in unique_others:
        print(f"  - {s}")
