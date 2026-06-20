# Changelog

All notable changes to Bird Tracker are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.6.3] – 2026-06-20

### Changed
- **Report deep links open the report's location.** The "View on map" / "See full
  analysis" links in report emails now carry the report's coordinates
  (`?lat&lng&name&radius`), and the map + analysis pages honor those params
  (persisting them as the active location so the whole app follows). Previously
  the links opened the viewer's *last-used* location — wrong for a trip report
  about a different place. Applies to both trip reports and the weekly newsletter.

---

## [1.6.2] – 2026-06-20

### Fixed
- **Restore Flask-Bcrypt** — the v1.6.1 dependency trim removed it, but the
  root-level `extensions.py` imports `flask_bcrypt`, so the app failed to boot
  with `No module named 'flask_bcrypt'` (served the wsgi fallback error page).
  Re-added. A whole-repo import scan confirms it was the only over-trimmed
  package; the other 17 removals stand.

---

## [1.6.1] – 2026-06-20

### Removed
- **Trimmed 18 unused dependencies** from `requirements.txt` — none were imported
  by the app: folium, py-staticmaps, staticmap, Flask-SocketIO, Flask-Security,
  Flask-User, Flask-Admin, Flask-Babel, Flask-Caching, Flask-RESTful,
  Flask-JWT-Extended, Flask-OAuthlib, Flask-Principal, Flask-DebugToolbar,
  Flask-Testing, Flask-Bcrypt, Flask-Marshmallow, Flask-Session, flask-bootstrap.
  Drops the heavy numpy/branca/s2sphere/socketio transitive trees, cutting build
  time and image size to ease free-tier deploys.

---

## [1.6.0] – 2026-06-19

### Added
- **TripPlanner integration — scheduled trip reports.** New endpoints let
  TripPlanner schedule pre-arrival bird reports for a trip's stops:
  `POST /api/trip-reports` (idempotent upsert by `trip_id`) and
  `DELETE /api/trip-reports/<trip_id>`, both authed with a shared
  `TRIP_REPORT_TOKEN` and limited to an allowlisted recipient
  (`TRIP_REPORT_ALLOWED_EMAILS`, default `alonsoencinci@gmail.com`). A new
  `ScheduledReport` model stores each stop with `send_date = arrival_date − 1`,
  and a daily `POST /api/send-due-reports` cron
  (`.github/workflows/trip-reports.yml`) sends the ones due — reusing the weekly
  report pipeline (map + AI narrative + links) via the tracker's new
  `send_report_for_location()`. Contract: `docs/TRIPPLANNER_INTEGRATION.md`.

---

## [1.5.2] – 2026-06-19

### Changed
- **Notable rarities now feed the AI narrative instead of a separate box.** The
  standalone "Notable sightings nearby" box was redundant with the narrative's
  rare-species list, prone to duplicate rows (a lingering rarity logged on
  multiple days), and surfaced messy eBird location strings. The eBird notable
  feed is now deduped by species and passed into the AI prompt, so the
  narrative's "unusual or rare species" section is grounded in eBird's
  authoritative flags with context — and the redundant box is removed.

---

## [1.5.1] – 2026-06-19

### Changed
- **Newsletter map now mirrors the app's categories** — pins use the app's full
  6-group palette via a shared `bird_categories` classifier (kept in sync with
  `home.html`) instead of the earlier 4-group approximation that rendered most
  pins green. Sightings are deduped by location so busy hotspots no longer
  collapse to one pin (up to 40 spots, each colored by its most notable group),
  and a color legend now appears beneath the map.

---

## [1.5.0] – 2026-06-19

### Added
- **Richer weekly newsletter** — the report now leads with a Mapbox static
  **hotspot map** (pins colored by bird group), an **AI-written narrative**
  (summary, rare/migratory species, birds of prey), a **"Notable sightings
  nearby"** box from eBird's geo notable-observations endpoint, and **"View on
  map" / "See full analysis"** deep links back into the app. Adds a
  `get_notable_observations_geo()` eBird client method and a new `MAPBOX_TOKEN`
  env var for the map. Every new section degrades gracefully if its data source
  is unavailable (no token → no map; AI failure → stats only; etc.), and the AI
  call is timeout-bounded so it can't hang the send.

---

## [1.4.4] – 2026-06-19

### Added
- **Newsletter manage/unsubscribe link** — the weekly report email footer now
  links to the subscription page, and `/newsletter-preferences` is reachable
  from the main nav (authenticated users). Basic CAN-SPAM hygiene. The page
  stays login-gated; a tokenized one-click unsubscribe remains a possible
  follow-up.

---

## [1.4.3] – 2026-06-19

### Fixed
- **`/admin/` panel 500** — the admin root view (`admin_panel`) ran raw SQL that
  selected `is_approved` / `newsletter_subscription` columns absent from the
  `users` table. It duplicated the working ORM-based `/admin/users` page (its
  template already posts every form there), so `/admin/` now simply redirects to
  it. Removed the same dead-column references from the registration-approval
  INSERT (`process_registration_request`) and the `--init-db` bootstrap, which
  would have failed identically.

---

## [1.4.2] – 2026-06-19

### Changed
- **Email transport → SendGrid HTTP API.** Render's free tier blocks outbound
  SMTP, so the Gmail/Flask-Mail send hung for 120s and the worker was OOM-killed.
  `EmailService` now sends via the SendGrid HTTP API (`requests`, 10s timeout)
  when `SENDGRID_API_KEY` + `SENDGRID_FROM_EMAIL` are set, mirroring the
  domino-tracker approach. Flask-Mail/SMTP is retained only as a local-dev
  fallback. No new dependency (`requests` was already required).

---

## [1.4.1] – 2026-06-19

### Fixed
- **Weekly report cold-start failures** — the GitHub Actions cron hit the
  spun-down free-tier service and the cold boot collided with the request,
  causing worker OOM kills and transient `psycopg2 SSL error: decryption failed
  or bad record mac` on the first DB query. The workflow now wakes the service
  (auth-free `/favicon.ico` poll) before triggering the report, and SQLAlchemy
  is configured with `pool_pre_ping` + `pool_recycle` so dropped connections
  reconnect transparently.

---

## [1.4.0] – 2026-06-19

### Added
- **Weekly newsletter scheduler** — `POST /api/send-weekly-reports` trigger
  endpoint (bearer-token auth via `REPORT_CRON_TOKEN`, CSRF-exempt) sends the
  weekly bird sighting report to subscribed users. Driven by a GitHub Actions
  cron (`.github/workflows/weekly-report.yml`, Mondays 09:00 UTC) since Render
  has no built-in scheduler. Subscription is stored on
  `UserPreferences.notification_enabled`; users with no preference row default
  to subscribed.
- **Newsletter preferences page** — working subscribe/unsubscribe toggle at
  `/newsletter-preferences` (previously rendered a missing template).

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
