# F197 — Tangerine public-lidar execution result

Date: 2026-08-21

## Decision

The bounded Tangerine execution required by F195 has now been run against the actual public USGS 1-meter bare-earth DEM products covering the target.

**The frozen stable-ground residual gates FAIL.**

Therefore, under the stop rule frozen before execution:

> **Close the free-public-lidar depth route. Do not interpret the Tangerine target difference as cover depth, and do not launch another landfill search.**

This result does not undo the earlier timing, coverage, or published-accuracy screening passes. It shows that those screening passes were not sufficient to produce a stable enough actual 2015-to-2021 elevation difference at Tangerine.

## Official source products actually executed

The National Map Access API returned exactly one standard 1-meter DEM tile from each required epoch over the bounded Tangerine analysis area.

### PRE — 2015

Project/product:

`AZ_Eastern_PimaCO_2015`

Tile:

`USGS_one_meter_x48y359_AZ_Eastern_PimaCO_2015.tif`

USGS staged product:

`https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/AZ_Eastern_PimaCO_2015/TIFF/USGS_one_meter_x48y359_AZ_Eastern_PimaCO_2015.tif`

### POST — 2021

Project/product:

`AZ_PimaCounty_2021_B21`

Tile:

`USGS_1M_12_x48y359_AZ_PimaCounty_2021_B21.tif`

USGS staged product:

`https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/AZ_PimaCounty_2021_B21/TIFF/USGS_1M_12_x48y359_AZ_PimaCounty_2021_B21.tif`

The 2021 public EPT project `AZ_PimaCo_2_2021` had already been confirmed to cover Tangerine. The National Map standard DEM service exposes the intersecting 2021 one-meter product under the staged product name above.

The first F196 live attempt also established that the 2021 EPT endpoint is live, while the 2015 Eastern Pima project is not mirrored under the assumed public EPT alias. The execution therefore used the official USGS standard one-meter DEM products, consistent with the F195 preference to use official bare-earth DEMs when available.

## Surface normalization

Both downloaded source rasters were:

- CRS: `EPSG:26912` (NAD83 / UTM zone 12N)
- source resolution: `1.0 m`
- source nodata: `-999999`
- same 10 km USGS distribution cell `x48y359`

USGS standard one-meter DEM products are bare-earth elevations in decimal meters referenced to NAVD88.

Both epochs were bilinearly reprojected/resampled onto the exact same F195 execution grid:

- CRS: `EPSG:32612`
- resolution: `1.0 m`
- bounds: `[480825.0, 3585903.0, 484016.0, 3588681.0]`
- width: `3191`
- height: `2778`

Normalized source sanity statistics over the analysis grid:

| Epoch | Min (m) | Median (m) | Max (m) | Valid pixels |
|---|---:|---:|---:|---:|
| 2015 | 590.0662 | 616.7206 | 635.3987 | 8,864,598 |
| 2021 | 587.6589 | 616.7196 | 635.8374 | 8,864,598 |

## Co-registration result

Bounded horizontal search selected:

- post shift X: **+1.25 m**
- post shift Y: **-0.25 m**

Robust stable-ground plane fit:

- fitted offset: **-0.02546 m**
- X edge delta: **-0.04849 m**
- Y edge delta: **+0.00189 m**
- fit points: **149,210**

The final stable-ground evaluation used **8,297,843 pixels**.

## Frozen residual gates

| Gate | Frozen threshold | Measured | Result |
|---|---:|---:|---|
| Stable RMSE | `<= 0.15 m` | **1.5070 m** | **FAIL** |
| Absolute median residual | `<= 0.05 m` | **0.00095 m** | PASS |
| p95 absolute residual | `<= 0.30 m` | **1.1339 m** | **FAIL** |
| Plane drift across target | `<= 0.10 m` | **0.01140 m** | PASS |

Overall:

`all_frozen_residual_gates_pass = false`

The failure is decisive because two frozen residual gates fail by large margins. The median and planar-drift corrections are small, but the residual spread over nominally stable ground is much too large for a defensible sub-meter cover-thickness inference.

## Target values are diagnostic only

The runner produced target-area statistics, but F195 explicitly forbids interpreting them when the stable-ground gates fail.

Diagnostic values only:

- target mean change: `0.5161 m`
- target median change: `0.4434 m`
- p05: `-0.2271 m`
- p10: `-0.0776 m`
- p90: `1.2558 m`
- p95: `1.5299 m`
- nominal regulatory/design cover: `0.9144 m`

These numbers are **not a depth result** and must not be used to claim that Tangerine has approximately 0.44 m or 0.52 m of cover. The stable-ground residual field is too noisy under the frozen acceptance rules.

The OSM landfill geometry also remains provisional and was never promoted to final claim geometry; `RS-33-039` remains the official geometry reference.

## Reproducibility record

One-shot execution PR:

`#159 — Run Tangerine live lidar execution`

Successful decisive workflow:

- workflow: `Tangerine live lidar execution`
- run id: `32544381870`
- artifact: `tangerine-live-result`
- artifact id: `9468037514`
- artifact SHA-256: `b65d5d60e0bacf0ec50a042af054a1d3cb733296c6cc6169b3b830372a983e7b`

The artifact contains:

- `prepare_summary.json`
- `tangerine_target.geojson`
- `dem_normalization.json`
- `tangerine_analysis_result.json`

PR #159 is execution-only and must not be merged into `main`.

## Final route status

```text
Waste end before pre-lidar        PASS
Pre-lidar before cover            PASS
Post-lidar after closure          PASS
2021 same-footprint coverage      PASS
Published precision screen        PASS
Official elevation files          OBTAINED
Datum / units normalization       PASS
Stable-ground median gate         PASS
Stable-ground plane-drift gate    PASS
Stable-ground RMSE gate           FAIL
Stable-ground p95 gate            FAIL
Actual depth recovery             INVALID / DO NOT INTERPRET
Unknown-site depth validation     NOT ACHIEVED
Free-public-lidar route           CLOSED
```

## Stop rule applied

F195 froze the following rule before seeing the numerical result:

> If the actual stable-ground residual gates fail: close the free-public-lidar route; do not launch another site search.

That condition is now met.

**No new landfill candidate search is authorized.**
