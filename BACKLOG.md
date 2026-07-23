# Bird Tracker — Backlog
_Last updated: 2026-07-14_

## 🔴 High
- _(none — all cleared)_

## 🟡 Medium
- [ ] **Date range filter** — observations are hardcoded to `back=7`; expose 7/14/30-day selector (eBird cap 30). `[feature]`
- [ ] **Persist drill-down state across reloads** — save `drilldownGroup` to `localStorage` and restore on load. `[feature]`
- [ ] **Heatmap v2 (Momentum / VYA modes)** — trend overlay on top of the shipped density heatmap. See [docs/DESIGN.md](docs/DESIGN.md#heatmap-v2--momentum--vya-trend-modes). `[feature]`
- [ ] **Analysis page: show location/radius context** — "Analyzing sightings within 25 mi of Cincinnati, OH" so it's clearly not stale/wrong-area. `[feature]`
- [ ] **Analysis page: loading state on location switch** — wire `#loading-spinner` to the location-change auto-generate. `[bug]`
- [ ] **Consolidate bird classifiers** — there are now three copies of the tier-1 keyword/category logic: `home.html` (JS, app map), `app/services/bird_categories.py` (newsletter), and `audit_categories.py` (root validation script). Point the validation script (and ideally the analyze route) at `app/services/bird_categories.py`, move `audit_categories.py` out of repo root, and treat the shared module as the single Python source of truth. `[chore]`

## 🟢 Low / Nice to have
- [ ] **Periodic keyword-list review** — re-run `audit_categories.py` after eBird taxonomy updates (annual, Aug) so renamed species don't silently fall to "Other"; consider a `?debug=1` category overlay. `[chore]`
- [ ] **Scientific-name classification fallback** — add a `sciName` → group secondary lookup so a changed common name doesn't break classification. `[feature]`
- [ ] **Push notifications for rare sightings** — eBird notable-observations endpoint + web push (Service Worker + Push API); uses stored `Location` prefs. `[feature]`
- [ ] **Tokenized one-click unsubscribe** — current unsubscribe is login-gated (toggles `UserPreferences.notification_enabled` for `current_user`); add a signed-token link in the email so recipients opt out without logging in and can't affect other accounts. Proper CAN-SPAM one-click behavior. `[feature]`
- [ ] **Background the newsletter send** — the weekly-report endpoint runs the AI narrative + notable-observations calls synchronously per user inside the HTTP request. Fine for a handful of subscribers (timeout-bounded), but with a larger list it risks gunicorn's 120s worker timeout. Move the send to a background job/queue when the list grows. `[chore]`

## ✅ Shipped
- [x] **Require `DEFAULT_USER_PASSWORD`** — 2026-07-14 (startup now fails if unset; removed the `user123` fallback and plaintext-password logging)
- [x] **Remove hardcoded-password scripts** — 2026-07-14 (deleted the redundant create-admin/user scripts + `reset_admin_password.py`, all of which hardcoded passwords)
- [x] **Delete/archive `quarantine/`** — 2026-07-14 (removed from repo and purged from git history; the leaked Anthropic key it exposed was rotated)
- [x] **TripPlanner integration — scheduled trip bird reports** — 2026-06-20 (retired 2026-07-14 — TripPlanner now sources eBird directly; code removed in v1.7.0)
- [x] **Enhance newsletter content** — 2026-06-19
- [x] **Newsletter unsubscribe link** — 2026-06-19
- [x] **Fix `/admin/` 500** — 2026-06-19
- [x] **Newsletter / email report** — 2026-06-19
- [x] **Marker clustering** — 2026-05-30
- [x] **Heatmap v1 (density)** — 2026-04-05
- [x] **Remove debug logging from production** — 2026-04-04
