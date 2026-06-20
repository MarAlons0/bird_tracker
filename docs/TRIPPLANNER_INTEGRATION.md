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

## Later / out of scope for v1

- Per-day **internal** itinerary (multiple sites/day) — same contract, more stops.
- Multi-user (drop the email allowlist), per-user frequency, time-zone-aware send.
- Geocoding fallback when a stop lacks lat/lng.
