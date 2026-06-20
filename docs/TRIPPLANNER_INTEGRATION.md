# TripPlanner ↔ Bird Tracker Integration

Design spec + API contract for sending a Bird Tracker report ahead of each stop
on a TripPlanner itinerary. This is the coordination artifact: the TripPlanner
agent builds against the **API contract** section; Bird Tracker builds the
**internal** section.

## Goal

When the user activates bird reports for a trip in TripPlanner, Bird Tracker
emails a weekly-style report (hotspot map + AI narrative + links) for each trip
site, delivered **one day before arrival** at that site.

## Scope (v1 — keep it small)

- **Single user:** `alonsoencinci@gmail.com` (server-side allowlist for now).
- **High-level itinerary only:** one destination ("to") per stop with an arrival
  date. TripPlanner's finer per-day internal itinerary is out of scope for v1 —
  the same contract can carry more stops later.
- **Shared-secret token auth** between the two apps (same pattern as the existing
  `REPORT_CRON_TOKEN`).

> **Sender vs recipient — don't conflate these two addresses:**
> - **Recipient = `alonsoencinci@gmail.com`** — the allowlisted user who *receives*
>   the reports. TripPlanner sends it as `email` / `BIRD_TRACKER_EMAIL`, and it
>   must match Bird Tracker's `TRIP_REPORT_ALLOWED_EMAILS`. **This is the address
>   used throughout this contract.**
> - **Sender = `mariobirdtracker@gmail.com`** — Bird Tracker's verified SendGrid
>   `SENDGRID_FROM_EMAIL` (the "From" on the emails). Internal to Bird Tracker,
>   **not part of this contract**; TripPlanner never references it.

## Architecture — who owns what

- **TripPlanner** owns the itinerary and the user action. On "Activate bird
  reports" it POSTs the trip's stops to Bird Tracker **once**. No recurring
  scheduler needed on its side.
- **Bird Tracker** owns scheduling + delivery. It stores each stop as a
  `ScheduledReport` (`send_date = arrival_date − 1 day`); a **daily cron** sends
  the ones due today, reusing the existing report generator for the stop's
  location.

Rationale: one POST on activation, no duplicated scheduler, and Bird Tracker
reuses infrastructure it already has (GitHub Actions cron + report generator).

## API contract (TripPlanner → Bird Tracker)

### Activate / schedule trip reports

```
POST /api/trip-reports
Authorization: Bearer <TRIP_REPORT_TOKEN>
Content-Type: application/json

{
  "email": "alonsoencinci@gmail.com",
  "trip_id": "tp_abc123",
  "stops": [
    {
      "name": "Yellowstone NP, WY",
      "lat": 44.4280,
      "lng": -110.5885,
      "arrival_date": "2026-07-10",
      "radius_miles": 25
    }
  ]
}
```

- `arrival_date`: ISO `YYYY-MM-DD`, the day the user arrives. The report sends on
  `arrival_date − 1`.
- `radius_miles`: optional, default `25`. Bird Tracker clamps to eBird's max.
- Re-POSTing the same `trip_id` **replaces** that trip's existing schedule
  (idempotent upsert) — so editing a trip just re-sends the full itinerary.

Response `200`:

```json
{ "scheduled": 1, "trip_id": "tp_abc123" }
```

Errors: `401` bad/missing token · `403` email not on allowlist · `400` invalid
payload (missing lat/lng or arrival_date).

> **Cold start:** Bird Tracker runs on Render's free tier and spins down when
> idle, so the **first** call after a quiet period can take 30–60 s to wake.
> Clients must use a request timeout of **≥60 s** (or warm the service with a
> cheap GET, e.g. `/favicon.ico`, before POSTing) — otherwise the initial
> activation times out with a "Read timed out" error even though everything is
> configured correctly.

### Deactivate / cancel a trip

```
DELETE /api/trip-reports/<trip_id>
Authorization: Bearer <TRIP_REPORT_TOKEN>
```

Response `200`: `{ "cancelled": <n> }` (number of pending reports removed).

## Internal (Bird Tracker only — not part of the contract)

- **Data model:** `ScheduledReport(email, trip_id, name, lat, lng, radius_miles,
  send_date, arrival_date, sent_at NULL)`.
- **Daily cron:** GitHub Actions → `POST /api/send-due-reports`
  (`Authorization: Bearer <REPORT_CRON_TOKEN>`). For each row with
  `send_date == today` and `sent_at IS NULL`: generate the report for
  `(lat, lng, radius_miles, name)`, send to `email`, set `sent_at`. Warm-up
  step first (same as the weekly workflow).
- **Refactor:** extract the per-recipient send body from `send_weekly_reports`
  into `send_report_for_location(email, lat, lng, radius, name)`, reused by both
  the weekly newsletter and trip reports (map + AI narrative + notable + links).

## Auth

- New shared secret `TRIP_REPORT_TOKEN` (Bird Tracker env var; TripPlanner stores
  the same value in its own secrets). Compared with `hmac.compare_digest`, same
  as `REPORT_CRON_TOKEN`.

## What Bird Tracker needs from the TripPlanner agent

1. Confirm each stop can provide **lat/lng + arrival_date** (high-level "to" per
   stop). If only place names are available, Bird Tracker would need to geocode —
   flag this so we add a geocoding step.
2. A stable **`trip_id`** per trip to support replace/cancel.
3. Where TripPlanner will store the shared **`TRIP_REPORT_TOKEN`**.
4. Time zone assumption for "one day before arrival" (default: the report's send
   uses UTC date math unless TripPlanner sends a tz).

## Rollout & joint verification

Both apps are built and **verified to match this contract** (Bird Tracker
endpoints ↔ TripPlanner `app/birdtracker.py`). To go live without diverging,
both sides follow this one checklist; the user provisions both services and
relays the joint-test result back to each agent. This section is the single
source of truth for the rollout — don't keep a second copy in either chat.

### Operator runbook (the human — do these in order)

Plain-language version of the steps below. No terminal needed — everything is in
the two Render dashboards and the TripPlanner UI. Do them top to bottom; don't
skip ahead.

**A. Get one shared secret.** Ask either agent for a token value (a long random
string), or reuse the `TRIP_REPORT_TOKEN` already set on Bird Tracker if you set
one for v1.6.0. You'll paste the *same* value into both apps. Keep it private —
never commit it to a repo.

**B. Set it on Bird Tracker (Render → the Bird Tracker service → Environment).**
- `TRIP_REPORT_TOKEN` = the shared secret from step A.
- Save. Render redeploys automatically — wait for "Live".

**C. Set the three values on TripPlanner (Render → the TripPlanner service →
Environment).** Use exactly the values in the table below:
- `TRIP_REPORT_TOKEN` = the **same** secret as step B (must match character-for-character).
- `BIRD_TRACKER_URL` = `https://bird-tracker.onrender.com`
- `BIRD_TRACKER_EMAIL` = `alonsoencinci@gmail.com`
- Save. Wait for TripPlanner to show "Live".

**D. Smoke test (the real check).** In TripPlanner, open a trip that has at least
one day with a destination and date → click **Activate bird reports**.
- ✅ Success looks like a green banner: *"Bird reports activated — N stops scheduled."*
- ❌ If you instead see a red banner, copy its exact wording and send it back —
  it names the problem (token mismatch, email not allow-listed, URL wrong, or a
  stop missing coordinates). See "If it fails" below.

**E. Turn it off to confirm cancel works.** Click the small ✕ next to "Bird
reports on". Expect *"Bird reports cancelled — N pending reports removed."*

**F. Tell both agents the result.** Paste back: the exact banner text from D (and
E), and — if you can grab them — the matching Bird Tracker log lines
(`Scheduled N trip reports…` / `Cancelled N…`). That's the green light for each
agent to tag its release.

**If it fails (what the red banner means):**
- *"rejected the token (401)"* → the two `TRIP_REPORT_TOKEN` values don't match,
  or one wasn't saved. Re-paste the same value on both, wait for redeploys.
- *"not on Bird Tracker's allowlist (403)"* → `BIRD_TRACKER_EMAIL` doesn't match
  Bird Tracker's allow-list. Both should be `alonsoencinci@gmail.com`.
- *"not configured"* → `BIRD_TRACKER_URL` or `TRIP_REPORT_TOKEN` is missing on
  TripPlanner. Re-check step C.
- *"rejected the payload (400)"* → a stop has no coordinates and couldn't be
  geocoded; the banner lists which day. Open that day, set/verify its
  destination, then Activate again.
- *"Could not reach Bird Tracker … Read timed out"* → Bird Tracker (free tier)
  was asleep and didn't wake within the client's timeout. Open
  `https://bird-tracker.onrender.com/` in a browser, wait for it to load (that
  wakes it), then Activate again — it responds in ~1 s while warm. Permanent fix
  is on the TripPlanner side: raise the request timeout to ≥60 s and/or warm the
  service with a cheap GET before the POST.

You are never the weak link here — if any step is unclear or a banner is
confusing, paste it back verbatim and the agents take it from there.

### Environment variables (canonical)

| Service | Variable | Value |
|---|---|---|
| Bird Tracker | `TRIP_REPORT_TOKEN` | shared secret — `openssl rand -hex 32` |
| Bird Tracker | `TRIP_REPORT_ALLOWED_EMAILS` | optional; defaults to `alonsoencinci@gmail.com` |
| TripPlanner | `TRIP_REPORT_TOKEN` | **same value** as Bird Tracker |
| TripPlanner | `BIRD_TRACKER_URL` | `https://bird-tracker.onrender.com` |
| TripPlanner | `BIRD_TRACKER_EMAIL` | `alonsoencinci@gmail.com` |

### Joint test (run in order)

1. Set the env vars above on both Render services; wait for both redeploys.
2. Liveness: `curl -X POST https://bird-tracker.onrender.com/api/trip-reports`
   returns **401** (token now set) — not 404, not 503.
3. In TripPlanner, open a trip and click **Activate bird reports**.
   - Expected: success in the UI; TripPlanner sets `bird_reports_active`.
   - Bird Tracker log: `Scheduled N trip reports for tp_<id> (alonsoencinci@gmail.com)`.
4. (Optional) Real send: activate a trip whose next stop arrives **tomorrow**,
   then run Bird Tracker → Actions → **Daily Trip Reports → Run workflow**.
   - Expected: `{"sent": 1, ...}` and the email arrives.
5. Cancel: toggle bird reports off in TripPlanner → Bird Tracker log
   `Cancelled N pending trip reports for tp_<id>`.

### Release gate

Each side tags its release **only after the joint test (steps 3–4) passes** —
don't release before it works end-to-end. Bird Tracker rides its rolling
`v1.6.x`; TripPlanner holds `v1.9.0` until step 3 (ideally 4) succeeds.

## Later / out of scope for v1

- Per-day **internal** itinerary (multiple sites/day) — same contract, more stops.
- Multi-user (drop the email allowlist), per-user frequency, time-zone-aware send.
- Geocoding fallback when a stop lacks lat/lng.
