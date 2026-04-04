# Bird Tracker — Backlog

Last updated: 2026-04-04

---

## Bugs / Polish

### ~~Remove debug logging from production~~ ✓ Done (2026-04-04)
- Replaced `const DEBUG = true` with `const DEBUG = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'`

### Move audit script out of repo root
- `audit_categories.py` is sitting in the project root
- Should be moved to `scripts/` or deleted — it's a one-off validation tool, not app code

---

## Features — Map

### Persist drill-down state across page reloads
- Currently, navigating away and back (or reloading) resets the map to tier 1 group view
- Fix: save `drilldownGroup` to `localStorage` and restore on page load
- Already partially addressed by intercepting the Map tab click (closes filters instead of reloading), but a full reload still resets state

### Date range filter
- Observations are hardcoded to `back=7` days in the API call
- Could expose a selector: 7 days / 14 days / 30 days
- The eBird API supports up to 30 days (`back` param max = 30)
- On the Analysis page, the timeframe is also hardcoded

### Marker clustering for very dense areas
- Golden-angle jitter (~39m radius) works well for moderate density
- In urban hotspots with hundreds of overlapping observations, even jitter produces a dense blob
- Consider adding `Leaflet.markercluster` as an optional mode, or auto-switching when marker count exceeds a threshold (e.g. > 200 in viewport)

---

## Features — Heatmap (new)

### Overview
Show a heatmap for a chosen bird category or species to visualize high-density areas and observation trends over time.

### Implementation approach
- **Library:** `leaflet.heat` plugin — lightweight, takes `[lat, lng, intensity]` arrays, overlays directly on the Leaflet map
- **Intensity:** weighted by observation count per location (locations with more reports = hotter)
- **Trigger:** a "Heatmap" toggle button in the filters panel, or a new map mode selector
- **Mode:** overlay on top of regular markers (toggle between heatmap and dot markers) — not exclusive replacement

### Trend visualization
Three trend states per location: **increasing**, **stable**, **decreasing**

**How to compute:**
- Split the available observation window into two equal periods (e.g. days 1–15 vs days 16–30)
- Compare observation count per location between the two periods
- Define thresholds: e.g. >20% increase = increasing, >20% decrease = decreasing, otherwise stable

**Visualization options (pick one):**

| Option | Description | Pros | Cons |
|---|---|---|---|
| **Color-coded heat** | Warm (red/orange) = increasing, cool (blue/purple) = decreasing, white/yellow = stable | Most elegant, single view | Requires enough data to be reliable; color meaning not obvious without legend |
| **Separate heatmaps** | Toggle between "current density" heatmap and "trend direction" heatmap | Cleaner to interpret | Two separate mental models |
| **Side-by-side time slices** | Two small maps: period 1 vs period 2 | Most honest representation of raw data | Poor on mobile — too small |

**Recommendation:** Start with Option 1 (color-coded heat) for mobile elegance. Fall back to Option 2 if trend data is too sparse to be meaningful.

### API constraints
- eBird's recent observations endpoint (`/data/obs/geo/recent`) only goes back **30 days maximum**
- This is sufficient for short-term trends (2-week vs 2-week comparison)
- For longer historical trends (seasonal, year-over-year), the eBird API has a regional species endpoint (`/data/obs/{regionCode}/historic/{y}/{m}/{d}`) — different rate limits, requires region code not lat/lng
- **Recommended scope for v1:** 30-day window only, split into two 15-day periods, using the existing geo/recent endpoint

### Scope for v1
1. Add `leaflet.heat` to the page
2. Add a "Heatmap" toggle in the filters panel
3. When active: fetch 30 days of observations, compute per-location counts for each 15-day half, render color-coded heatmap
4. Legend updates to show: 🔴 Increasing · ⚪ Stable · 🔵 Decreasing
5. Heatmap applies to whichever tier is active (all groups, or drill-down group)

---

## Features — Analysis Page

### Show location and radius context
- The analysis page generates a summary but doesn't visibly show which location/radius it's based on
- User has no way to know if the analysis is stale or for the wrong area without checking the map
- Fix: show "Analyzing sightings within 25 miles of Cincinnati, OH" at the top of the analysis card

### Loading state when switching locations
- When the user changes location on the map and then navigates to Analysis, the page auto-generates a new analysis — but there's no indication it's working
- The existing spinner (`#loading-spinner`) is in the HTML but may not be wired to the location-change event

---

## Features — Classification

### Periodic keyword list review
- eBird occasionally updates common names as taxonomy changes (e.g. species splits, lumps)
- The keyword lists in `getBirdCategory()` are hardcoded — if a common name changes, the bird silently drops to "Other"
- Mitigation: re-run `audit_categories.py` after each eBird taxonomy update (typically annual, in August)
- Consider adding a `?debug=1` URL param that shows each marker's classified category in its popup to make misclassifications visible

### Scientific name fallback
- eBird returns both `comName` (common name) and `sciName` (scientific name) in the API response
- Classification currently uses only `comName`
- Edge case: if a common name changes but `sciName` stays stable, classification would break
- Future option: maintain a `sciName` → group mapping as a secondary lookup

---

## Infrastructure / Cleanup

### Delete or archive `quarantine/` directory
- Contains legacy scripts, logs, old HTML files, and backup SQL from early development
- Is a public repo — log files and old code add noise and may contain incidental data
- Recommend: delete entirely, or move to a private archive branch
- Files of note: `bird_tracker.log`, `bird_tracker_backup.sql` (may contain user data)

### Remove hardcoded password scripts
- `scripts/admin/create_admin_user.py`, `create_admin.py`, `create_user.py` all hardcode `admin123` or `user123`
- These are no longer needed — the app auto-creates the admin user from env vars on startup
- Safe to delete

### Make `DEFAULT_USER_PASSWORD` a required env var
- `routes/auth.py` and `routes/admin.py` fall back to `'user123'` if `DEFAULT_USER_PASSWORD` is not set
- This is a security risk if the env var is accidentally omitted in a new deployment
- Fix: raise a startup error if `DEFAULT_USER_PASSWORD` is not set, rather than silently using a weak default

---

## Longer Term

### Newsletter / email report (currently disabled)
- The email report infrastructure exists (`app/send_report.py`, `app/services/email_service.py`, `app/scheduler.py`)
- Was working on Heroku but scheduler/Redis dependency makes it non-trivial on Render
- Render does not support background workers on the free tier — would need a paid instance or a cron-based alternative (e.g. GitHub Actions scheduled workflow calling an API endpoint)

### Push notifications for rare sightings
- eBird has a "notable observations" endpoint (`/data/obs/{regionCode}/recent/notable`)
- Could trigger a push notification when a rare species is reported within the user's radius
- Requires web push (Service Worker + Push API) — significant implementation effort
- Dependency: need persistent user location preferences (already stored in DB via `Location` model)
