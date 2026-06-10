# Bird Tracker — Design Notes

Detailed design specs for planned/complex backlog items. The backlog keeps a one-line summary
and links here. Shipped features are recorded in `CHANGELOG.md`.

---

## Heatmap v2 — Momentum / VYA trend modes
_Backlog: 🟡 Medium · heatmap v1 (density) already shipped_

Show a heatmap for a chosen bird category/species to visualize density and **trend over time**.

**Library:** `leaflet.heat` — takes `[lat, lng, intensity]` arrays, overlays on the Leaflet map.
**Intensity** encodes trend direction (0 = strongly decreasing, 0.5 = stable, 1.0 = strongly increasing).

**Toggle (compound control — button + mode selector as a Bootstrap `input-group`):**
- Button label is always the *action*, not the state: at rest **"🔥 Heatmap"**; active **"⚬ Observations"**.
- Style: `btn-outline-warning` at rest → `btn-warning text-dark` when active.
- Markers hidden via `setStyle({opacity:0, fillOpacity:0})` — **not** `setOpacity()` (no-op on `L.Path`/`circleMarker`).

**Comparison modes:**

| Mode | Compares | Best window |
|---|---|---|
| **Momentum** | 1st half vs 2nd half of the selected window | 30–180 days — recent shifts |
| **VYA** | Current window vs same window 1 year earlier | 60–365 days — year-over-year |

Why both: at a 1-year window, Momentum splits summer vs winter (conflates seasonality with trend);
VYA compares like-for-like. At short windows VYA fetches 13–14 months (may be sparse); Momentum
is more reliable. (Momentum ≠ VPP: it compares the two halves of the same window — an
acceleration indicator.)

**Trend computation:**
```
intensity = (ratio + 1) / 2   where ratio = (recent - older) / (recent + older)
```
- `ratio` ∈ [−1, +1] → intensity ∈ [0, 1]. Edge cases: recent-only → 0.85; older-only → 0.15.
- **Momentum:** split window at midpoint (recent = 0→N/2, older = N/2→N).
- **VYA:** fetch `days + 365` in one call, filter into two non-contiguous windows (recent 0→N, older 365→365+N) — uses the existing `?days=` param, no backend change.

**Grid resolution:** `toFixed(2)` ≈ 1 km; fall back to `toFixed(1)` ≈ 11 km when total obs < 50.
**Sparse fallback:** if filtered obs < 20, plain density mode (intensity = normalized count),
legend "Density only — not enough data for trend view". `minOpacity: 0.4` required (default 0.05
is invisible with sparse data).
**Fetch/cache:** separate from main map load, triggered on activate; cached in `heatObservations`
for the current location; cleared on location/time-window change.

**Known bugs fixed (v1):**

| Bug | Root cause | Fix |
|---|---|---|
| Markers don't restore after heatmap off | `circleMarker` is `L.Path` — no `.setOpacity()` | `.setStyle({opacity:1, fillOpacity:0.85})` |
| Heat layer invisible | `minOpacity: 0.05` too low | `minOpacity: 0.4` |
| Timestamp parse fails in some browsers | space-separated datetime | replace space with `T` before `new Date()` |

**v2 upgrade path:** Bird Tracker uses a hardcoded 30-day window (eBird cap). Momentum works
as-is (15 vs 15 days). VYA needs the eBird historic endpoint
(`/data/obs/{regionCode}/historic/{y}/{m}/{d}`) since the geo/recent endpoint caps at 30 days —
different rate limits, needs a region code (not lat/lng); treat as a separate fetch. Add the
compound `input-group` control to replace the current single toggle.
