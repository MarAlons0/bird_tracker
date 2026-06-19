# Changelog

All notable changes to Bird Tracker are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.3.1] – 2026-06-18

### Fixed
- AI Analysis page returning 500 error — updated Claude model from deprecated
  `claude-sonnet-4-20250514` to `claude-sonnet-4-6`.

---

## [1.3.0] – 2026-05-30

### Added
- **Marker clustering** — Cluster toggle button (next to Heatmap) groups dense
  observations using Leaflet.markercluster. Zooming in spiderifies clusters so
  every individual sighting is clickable. Cluster icons are neutral gray in
  all-groups view, switch to the active group's color in drill-down mode.
  Mutually exclusive with Heatmap mode.

---

## [1.2.0] – 2026-04-05

### Added
- **Species drill-down** — clicking a category in the filter panel zooms into
  that group and colors each species individually using a 20-color palette.
  Back button returns to tier-1 group view.
- **Trend heatmap** — Heatmap toggle overlays a blue→white→red heat layer
  showing whether sightings at each location are increasing, stable, or
  decreasing (compares days 1–15 vs 16–30 of the 30-day window).
- **Category filter panel** — checkboxes to show/hide individual bird groups;
  counts update live as observations load.
- **Golden-angle jitter** — stacked markers at the same hotspot are spread into
  a ~39 m sunflower pattern so every dot is individually clickable.
- **Heatmap legend** — context-sensitive legend updates to show trend scale
  when heatmap is active and reverts to group/species legend otherwise.
- **New favicon** — bird/map-pin icon replacing the default browser icon.

### Changed
- Map markers use category-matched colors (waterbirds blue, raptors red, etc.)
  instead of a single color.
- Heatmap button label always shows the *action* ("Heatmap" at rest,
  "Observations" when active) rather than the current state.

### Fixed
- Heatmap markers not restoring after toggle off (`circleMarker` is `L.Path` —
  fixed by using `setStyle` instead of `setOpacity`).
- Heatmap layer invisible with sparse data (raised `minOpacity` to 0.4).

---

## [1.1.0] – 2026-01-11

### Added
- **Render deployment** — app ported from Heroku to Render with gunicorn,
  PostgreSQL, and proper static/template path resolution.
- **User-specific locations** — each user's selected location and radius are
  stored independently in the database.
- **Radius selector** — 1 / 5 / 25 / 50 mile options (25 miles default).
- **Admin panel** — create, activate, and manage users; view all locations.
- **Password reset** — email-based reset flow using Flask-Mail.

### Changed
- Session cookies set to `SameSite=Lax` and `Secure` in production.
- Database migrations managed via Flask-Migrate.

---

## [1.0.0] – 2025-03-23

### Added
- Initial release: eBird API integration fetching observations within a
  configurable radius over the past 7 days.
- Interactive Leaflet map with circle markers per sighting.
- Claude AI analysis summarizing recent sightings.
- User authentication (login, register, logout).
- Email report scheduler (Heroku deployment).
