# Marker Clustering — Implementation Guide

*Implemented in Bird Tracker on 2026-05-30. This doc explains what was done
and how to replicate it in Megafauna Tracker.*

---

## What was built

A **Cluster toggle button** (next to the existing Heatmap button) that switches
the map between two density modes:

| Mode | Behaviour |
|---|---|
| **Off (default)** | Golden-angle jitter (~39 m radius) — spreads stacked markers so every dot is individually clickable |
| **On** | Markers snap to true coordinates, grouped by `L.markerClusterGroup`. Clicking a cluster zooms in; at max zoom it spiderifies. |

Additional behaviour:
- Cluster and Heatmap are **mutually exclusive** — turning one on silently turns the other off.
- Cluster icons are **neutral gray** when all categories are shown (mixed colors), and switch to the **active group's color** in species drill-down mode.
- Icon size scales with count: 30 px (< 10) → 38 px (< 100) → 46 px (100+).
- When a new location loads, the cluster layer is rebuilt (mode preference is kept).
- When filters change while heatmap is active, the observation layer stays hidden correctly.

---

## Files changed in Bird Tracker

All changes are in a single file: `app/templates/home.html`.

---

## Step-by-step for Megafauna Tracker

Megafauna's architecture is actually **cleaner** for this feature than Bird
Tracker's. Bird Tracker manages markers in a plain array and adds them
directly to the map; Megafauna uses `markerLayer = L.layerGroup()` and
`markerLayer.addLayer(marker)`. Because `L.markerClusterGroup` implements
the same `addLayer` interface as `L.layerGroup`, the only structural change
is **how `clearMarkers()` creates `markerLayer`** — `renderMarkers()` itself
needs no changes at all.

### 1 — Add Leaflet.markercluster CSS (`templates/base.html`)

After the existing Leaflet CSS line:

```html
<!-- Leaflet -->
<link href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" rel="stylesheet">
```

Add:

```html
<!-- Leaflet MarkerCluster -->
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />
```

### 2 — Add Leaflet.markercluster JS (`templates/base.html`)

After the existing Leaflet JS lines:

```html
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
```

Add:

```html
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
```

### 3 — Add the Cluster button (`templates/index.html`)

The Heatmap toggle in Megafauna is a Bootstrap `input-group` (button + mode
selector). Add the Cluster button as a sibling `col-auto` **before** the
Heatmap toggle column:

```html
<!-- Cluster Toggle -->
<div class="col-auto">
    <button id="btn-cluster" class="btn btn-outline-secondary btn-sm"
            title="Group nearby markers into clusters">
        <i class="fas fa-layer-group me-1"></i>Cluster
    </button>
</div>

<!-- Heatmap Toggle (existing — unchanged) -->
<div class="col-auto">
    <div class="input-group input-group-sm">
        <button id="btn-heatmap" class="btn btn-outline-warning" ...>
        ...
    </div>
</div>
```

### 4 — Add cluster state variables (`templates/index.html` JS)

Near the existing heatmap state block:

```js
// Cluster state
let clusterActive = false;
```

> Note: no need for a separate `markerCluster` variable — Megafauna already
> uses `markerLayer` as the canonical layer reference for both marker management
> and heatmap hide/show.

### 5 — Add `createClusterIcon()` helper

Paste this near the top of the script, alongside other utility functions:

```js
// Custom cluster icon.
// Neutral gray in all-groups mode (markers are mixed colors);
// switches to the active group's color in drill-down mode.
function createClusterIcon(cluster) {
    const count = cluster.getChildCount();
    // SPECIES_GROUPS[drillGroup].color — adapt key name if Megafauna uses a different variable
    const color = drillGroup ? (SPECIES_GROUPS[drillGroup].color || '#555') : '#555';
    const size  = count < 10 ? 30 : count < 100 ? 38 : 46;
    const fs    = size < 38 ? 12 : 14;
    return L.divIcon({
        html: `<div style="width:${size}px;height:${size}px;border-radius:50%;` +
              `background:${color};border:2.5px solid rgba(255,255,255,0.75);` +
              `display:flex;align-items:center;justify-content:center;` +
              `color:#fff;font-weight:700;font-size:${fs}px;` +
              `box-shadow:0 2px 6px rgba(0,0,0,0.45);">${count}</div>`,
        className: '',
        iconSize:   [size, size],
        iconAnchor: [size / 2, size / 2],
    });
}
```

### 6 — Add `hideObservationLayer()` / `showObservationLayer()` helpers

These replace the two inline `markerLayer.eachLayer(setStyle)` calls that
currently live inside `toggleHeatmap()`. Add them near `clearMarkers()`:

```js
function hideObservationLayer() {
    if (clusterActive) {
        map.removeLayer(markerLayer);   // cluster layer hides as a unit
    } else {
        markerLayer.eachLayer(m => m.setStyle({ opacity: 0, fillOpacity: 0 }));
    }
}

function showObservationLayer() {
    if (clusterActive) {
        map.addLayer(markerLayer);
    } else {
        markerLayer.eachLayer(m => m.setStyle({ opacity: 1, fillOpacity: 0.85 }));
    }
}
```

### 7 — Update `clearMarkers()` to create the right layer type

Current Megafauna `clearMarkers()`:

```js
function clearMarkers() {
    if (markerLayer) map.removeLayer(markerLayer);
    markerLayer = L.layerGroup().addTo(map);
}
```

Replace with:

```js
function clearMarkers() {
    if (markerLayer) map.removeLayer(markerLayer);
    markerLayer = clusterActive
        ? L.markerClusterGroup({
              iconCreateFunction: createClusterIcon,
              maxClusterRadius:   60,
              spiderfyOnMaxZoom:  true,
              showCoverageOnHover: false,
              zoomToBoundsOnClick: true,
              animate:            true,
          })
        : L.layerGroup();
    map.addLayer(markerLayer);
}
```

> `renderMarkers()` needs **no changes** — it already uses
> `markerLayer.addLayer(marker)`, which works identically on both a
> `L.layerGroup` and a `L.markerClusterGroup`.
>
> Jitter is automatically bypassed in cluster mode because when `clusterActive`
> is true, `clearMarkers()` creates a cluster group — you may optionally also
> skip the `jitterCoords()` call in `renderMarkers()` when `clusterActive` is
> true so markers land at true coordinates (better for clustering):
>
> ```js
> const [jLat, jLng] = clusterActive
>     ? [obs.lat, obs.lng]
>     : jitterCoords(obs.id || 0, obs.lat, obs.lng);
> ```

### 8 — Add `toggleCluster()` function

```js
function toggleCluster() {
    const btn = document.getElementById('btn-cluster');
    clusterActive = !clusterActive;

    if (clusterActive) {
        btn.classList.replace('btn-outline-secondary', 'btn-secondary');
        btn.innerHTML = '<i class="fas fa-layer-group me-1"></i>Uncluster';

        // Mutually exclusive with heatmap — turn it off silently
        if (heatmapActive) {
            heatmapActive = false;
            if (heatLayer) { map.removeLayer(heatLayer); heatLayer = null; }
            const hBtn = document.getElementById('btn-heatmap');
            hBtn.classList.replace('btn-warning', 'btn-outline-warning');
            hBtn.classList.remove('text-dark');
            hBtn.title = 'Switch to heatmap view';
            hBtn.innerHTML = '<i class="fas fa-fire me-1"></i>Heatmap';
            updateMapLegend();
        }
    } else {
        btn.classList.replace('btn-secondary', 'btn-outline-secondary');
        btn.innerHTML = '<i class="fas fa-layer-group me-1"></i>Cluster';
    }

    // clearMarkers() creates the correct layer type; renderMarkers re-populates it
    clearMarkers();
    renderMarkers(allObservations);
    updateMapLegend();
}
```

### 9 — Update `toggleHeatmap()` to use the shared helpers

Inside `toggleHeatmap()`, replace:

```js
// OLD — hide
markerLayer.eachLayer(m => m.setStyle({ opacity: 0, fillOpacity: 0 }));
```

with:

```js
// NEW
hideObservationLayer();
```

And replace:

```js
// OLD — show
markerLayer.eachLayer(m => m.setStyle({ opacity: 1, fillOpacity: 0.85 }));
```

with:

```js
// NEW
showObservationLayer();
```

### 10 — Wire up the button (event listener)

Add alongside the existing heatmap listener:

```js
document.getElementById('btn-cluster').addEventListener('click', toggleCluster);
```

### 11 — Reset cluster layer on new data load

In the section that resets heatmap state when a new fetch completes (after
`heatObservations = []` etc.), add:

```js
// Cluster layer is rebuilt by the subsequent clearMarkers() → renderMarkers() call;
// nothing extra needed unless you want to collapse clusters to mode-off on navigation.
// Optionally reset to off:
// clusterActive = false;
// document.getElementById('btn-cluster').classList.replace('btn-secondary','btn-outline-secondary');
// document.getElementById('btn-cluster').innerHTML = '<i class="fas fa-layer-group me-1"></i>Cluster';
```

The simplest safe approach is to leave `clusterActive` as-is — `clearMarkers()`
will automatically rebuild the correct layer type on the next render.

---

## Summary of differences from Bird Tracker

| | Bird Tracker | Megafauna Tracker |
|---|---|---|
| Marker container | `markers[]` array, added directly to map | `markerLayer = L.layerGroup()`, `addLayer()` |
| `renderMarkers()` changes needed | Yes — had to detect cluster mode and call `clusterGroup.addLayer()` vs `.addTo(map)` | **No** — `markerLayer.addLayer()` already works for both types |
| Heatmap hide in cluster mode | `map.removeLayer(markerCluster)` (separate variable) | `map.removeLayer(markerLayer)` (same variable) |
| State variable | `let markerCluster = null` (separate from marker array) | No extra variable — `markerLayer` holds whichever type is active |
| Where CSS goes | `{% block head %}` in `home.html` | `base.html` (shared head) |
| Where JS goes | `{% block scripts %}` in `home.html` | `base.html` (shared scripts) |
| Jitter key | Loop index `i` | `obs.id` (already deterministic — no change needed) |
| Leaflet version | 1.7.1 | 1.9.4 (both compatible with markercluster 1.5.3) |
