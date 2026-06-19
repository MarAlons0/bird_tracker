# Bird Tracker — Backlog
_Last updated: 2026-06-19_

## 🔴 High
- [ ] **Require `DEFAULT_USER_PASSWORD`** — `routes/auth.py` and `routes/admin.py` fall back to `'user123'`; raise a startup error instead of using a weak default. `[security]`
- [ ] **Remove hardcoded-password scripts** — `scripts/admin/create_admin_user.py`, `create_admin.py`, `create_user.py` hardcode `admin123`/`user123`; the app auto-creates admin from env vars, so delete them. `[security]`
- [ ] **Delete/archive `quarantine/`** — legacy scripts, logs, and `bird_tracker_backup.sql` (may hold user data) sit in a public repo. `[security]`

## 🟡 Medium
- [ ] **Date range filter** — observations are hardcoded to `back=7`; expose 7/14/30-day selector (eBird cap 30). `[feature]`
- [ ] **Persist drill-down state across reloads** — save `drilldownGroup` to `localStorage` and restore on load. `[feature]`
- [ ] **Heatmap v2 (Momentum / VYA modes)** — trend overlay on top of the shipped density heatmap. See [docs/DESIGN.md](docs/DESIGN.md#heatmap-v2--momentum--vya-trend-modes). `[feature]`
- [ ] **Analysis page: show location/radius context** — "Analyzing sightings within 25 mi of Cincinnati, OH" so it's clearly not stale/wrong-area. `[feature]`
- [ ] **Analysis page: loading state on location switch** — wire `#loading-spinner` to the location-change auto-generate. `[bug]`
- [ ] **Enhance newsletter content** — current weekly report is bare stats (total species, total observations, top species) and isn't engaging; make it compelling (e.g. AI narrative, notable/rare sightings, week-over-week trends, photos). Scope TBD — discuss possibilities first. `[feature]`
- [ ] **Move `audit_categories.py` out of repo root** — to `scripts/` or delete (one-off validation tool). `[chore]`

## 🟢 Low / Nice to have
- [ ] **Periodic keyword-list review** — re-run `audit_categories.py` after eBird taxonomy updates (annual, Aug) so renamed species don't silently fall to "Other"; consider a `?debug=1` category overlay. `[chore]`
- [ ] **Scientific-name classification fallback** — add a `sciName` → group secondary lookup so a changed common name doesn't break classification. `[feature]`
- [ ] **Push notifications for rare sightings** — eBird notable-observations endpoint + web push (Service Worker + Push API); uses stored `Location` prefs. `[feature]`
- [ ] **Tokenized one-click unsubscribe** — current unsubscribe is login-gated (toggles `UserPreferences.notification_enabled` for `current_user`); add a signed-token link in the email so recipients opt out without logging in and can't affect other accounts. Proper CAN-SPAM one-click behavior. `[feature]`

## ✅ Shipped
- [x] **Newsletter unsubscribe link** — 2026-06-19
- [x] **Fix `/admin/` 500** — 2026-06-19
- [x] **Newsletter / email report** — 2026-06-19
- [x] **Marker clustering** — 2026-05-30
- [x] **Heatmap v1 (density)** — 2026-04-05
- [x] **Remove debug logging from production** — 2026-04-04
