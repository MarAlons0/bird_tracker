"""
Audit bird category classification across multiple ecosystems.

Fetches recent eBird sightings for a few contrasting regions and prints every
species grouped by the app's classifier, plus everything that falls to "Other"
— the list to mine for missing keywords. Uses the app's single source of truth,
app/services/bird_categories.py, so it audits exactly what the map and the
newsletter do. Re-run after eBird's annual taxonomy update (August).

Usage (from the repo root, with the project venv):
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
