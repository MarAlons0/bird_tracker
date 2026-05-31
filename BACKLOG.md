# Bird Tracker — Backlog

Last updated: 2026-05-30

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

### ~~Marker clustering for very dense areas~~ ✓ Done (2026-05-30)
- Added `Leaflet.markercluster` as a manual toggle (Cluster button next to Heatmap)
- When active: markers placed at true coordinates inside `L.markerClusterGroup`; zooming in spiderifies clusters so individual sightings are clickable
- Cluster icons: neutral gray in tier-1 (mixed categories), group color in species drilldown
- Mutually exclusive with heatmap; jitter resumes when clustering is turned off

---

## Features — Heatmap ✓ v1 implemented (2026-04-04) · v2 design (2026-04-05)

### Overview
Show a heatmap for a chosen bird category or species to visualize high-density areas and observation trends over time.

### Implementation approach
- **Library:** `leaflet.heat` plugin — lightweight, takes `[lat, lng, intensity]` arrays, overlays directly on the Leaflet map
- **Intensity:** encodes trend direction (0 = strongly decreasing, 0.5 = stable, 1.0 = strongly increasing)
- **Toggle:** compound control — button + mode selector joined as a Bootstrap `input-group`
  - Button label is always the *action*, not the state:
    - At rest (observations visible): shows **"🔥 Heatmap"** — click to switch to heatmap
    - Active (heatmap visible): shows **"⚬ Observations"** — click to switch back
  - Style: `btn-outline-warning` at rest → `btn-warning text-dark` when active
  - This is more intuitive than an on/off toggle because the label always tells the user what will happen, not what mode they're in
  - Selector: two comparison modes (see below)
- **Mode:** replaces dot markers when active (markers hidden via `setStyle({opacity:0, fillOpacity:0})` — NOT `setOpacity()`, which doesn't work on `L.Path`/`circleMarker`)

### Comparison modes

Two modes selectable in the compound control next to the heatmap button:

| Mode | Label | What it compares | Best window |
|---|---|---|---|
| **Momentum** | "Momentum" | 1st half vs 2nd half of the selected time window | 30–180 days — catches recent shifts |
| **VYA** | "VYA" | Current window vs same window 1 year earlier | 60–365 days — year-over-year changes |

**Why two modes matter:** At a 1-year window, Momentum splits the year at the midpoint (summer vs winter) which conflates seasonality with trend. VYA compares apples to apples. At shorter windows (30–60 days), VYA fetches 13–14 months of data which may be sparse; Momentum is more reliable.

**Note:** "VPP" (vs Previous Period) in dashboard terminology means the period immediately before the current one — same length, adjacent. Momentum is *not* VPP; it compares the two halves of the same window, making it more of an acceleration/deceleration indicator.

### Trend computation

```
intensity = (ratio + 1) / 2       where ratio = (recent - older) / (recent + older)
```
- `ratio` ranges −1 (fully decreased) to +1 (fully increased), mapped to 0–1 intensity
- Edge cases: location only in recent window → intensity 0.85; only in older window → 0.15

**For Momentum:** split the selected window at the midpoint
- Recent = days 0 → N/2; Older = days N/2 → N

**For VYA:** fetch `days + 365` in one call, filter into two non-contiguous windows
- Recent = days 0 → N; Older = days 365 → 365+N
- No backend changes needed — use existing `?days=` param with the larger value

### Grid resolution
- Default: `toFixed(2)` ≈ 1km grid (fine enough for bird sightings)
- For sparse data sources, consider `toFixed(1)` ≈ 11km as fallback when total obs < 50

### Sparse data fallback
If filtered observation count < 20, fall back to plain density mode:
- Intensity = normalized count (max location = 1.0)
- Legend updates to "Density only — not enough data for trend view"
- Keeps the heatmap useful rather than showing a meaningless single-color blob

### Data fetch & caching
- Separate fetch from the main map load — triggered only when user activates heatmap
- Cached in `heatObservations` for the current location; cleared on location change or time window change
- `minOpacity: 0.4` required — default (0.05) is nearly invisible with sparse data

### Legend
- Heatmap active: shows mode name, scope (All Groups or drill-down group), color key, and comparison description
- Deactivated: reverts to standard species group / drill-down legend

### Known bugs fixed (applicable to Bird Tracker v2)
| Bug | Root cause | Fix |
|---|---|---|
| Markers don't restore after heatmap off | `circleMarker` is `L.Path` — `.setOpacity()` doesn't exist | Use `.setStyle({opacity:1, fillOpacity:0.85})` |
| Heat layer invisible | Default `minOpacity: 0.05` too low for sparse data | Set `minOpacity: 0.4` |
| Timestamp parse fails in some browsers | Space-separated datetime string | Replace space with `T` before `new Date()` |

### v2 upgrade path for Bird Tracker
Bird Tracker v1 uses a hardcoded 30-day window (eBird API cap). To add Momentum/VYA modes:
- **Momentum** works as-is within the 30-day cap (15 vs 15 days)
- **VYA** requires the eBird historic endpoint (`/data/obs/{regionCode}/historic/{y}/{m}/{d}`) since the geo/recent endpoint is capped at 30 days — different rate limits, needs region code not lat/lng; treat as a separate fetch
- Add the compound `input-group` control (button + mode selector) to replace the current single toggle button

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
