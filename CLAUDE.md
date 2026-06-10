# Bird Tracker — agent guide

eBird + Google Places + Claude explorer with an interactive Leaflet map, tier classification, and
admin panel. Flask, deployed on Render. The app code lives under `app/` (templates in
`app/templates`, static in `app/static`).

## Project standards (read these before related work)
This repo follows shared standards documented at its root:
- **VERSIONING.md** — when shipping a feature, bump `VERSION`, add a `CHANGELOG.md` entry (Keep a Changelog), and tag per SemVer.
- **BACKLOG_FORMAT.md** — keep `BACKLOG.md` in the standard format (priority sections, checkbox status, type tags, ✅ Shipped). Long design specs go in `docs/`.
- **FAVICON.md** — favicon kit + root serving + Safari rules.

These three docs are synced from the `project-dashboard` repo (the source of truth) — don't edit
them here; change the master there and run its `sync-standards.sh`.
