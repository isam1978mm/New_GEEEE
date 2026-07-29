# Operator-Calibrated Local AOI Depth — App Guide

Date: 2026-07-29

## What this feature does

The app can estimate a **local calibrated depth range** for candidate polygons when the operator provides measured anchor polygons from the same area.

It does not estimate depth without measured anchors. It does not create a global model. It does not transfer a calibration from one site to another.

The feature:

- reads the canonical run `logRatio_dB` raster;
- measures the mean signal inside reviewed polygons after optional boundary erosion;
- uses at least two measured anchor zones;
- interpolates only inside the measured anchor signal range;
- widens the metre range using the anchor depth ranges and within-polygon signal uncertainty;
- abstains outside local support.

## Enable the backend

The backend is disabled by default.

Set:

```text
OPERATOR_LOCAL_DEPTH_APP_ENABLED=true
```

For local loopback development, the existing local-operator authentication bypass applies when:

```text
ALLOW_NETWORK_BIND=false
OPERATOR_AUTH_OIDC_ENABLED=false
```

For a network deployment, use the existing trusted proxy or OIDC operator authentication and configure per-run authorization. Do not expose this endpoint as an unauthenticated public API.

## Show the operator panel

In the app:

1. Open **Settings**.
2. Turn on **Operator private tools**.
3. Open a completed run.
4. Expand **Local depth calibration — operator only**.

The browser visibility switch does not enable backend access. The backend flag and operator authorization are still required.

## Required run files

The selected run must be completed and contain:

```text
logRatio_dB.tif
QA/run_quality/run_quality_summary.json
```

Run quality should normally be `PASS`. A usable `WARNING` may be accepted only when the operator explicitly selects that option.

## GeoJSON requirements

Upload one reviewed GeoJSON `FeatureCollection`.

It must contain:

- at least two `anchor` features;
- at least one `candidate` feature;
- non-overlapping Polygon or MultiPolygon geometries;
- the coordinate reference system entered in the panel.

### Anchor properties

Each measured anchor requires:

```json
{
  "feature_id": "anchor_shallow",
  "role": "anchor",
  "depth_min_m": 0.90,
  "depth_best_m": 1.00,
  "depth_max_m": 1.10
}
```

The depth range must satisfy:

```text
0 <= depth_min_m <= depth_best_m <= depth_max_m
```

### Candidate properties

Each candidate requires:

```json
{
  "feature_id": "candidate_01",
  "role": "candidate"
}
```

## Minimal example

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "feature_id": "anchor_shallow",
        "role": "anchor",
        "depth_min_m": 0.90,
        "depth_best_m": 1.00,
        "depth_max_m": 1.10
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[0, 0], [100, 0], [100, 100], [0, 100], [0, 0]]]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "feature_id": "candidate_01",
        "role": "candidate"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[120, 0], [220, 0], [220, 100], [120, 100], [120, 0]]]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "feature_id": "anchor_deep",
        "role": "anchor",
        "depth_min_m": 2.90,
        "depth_best_m": 3.00,
        "depth_max_m": 3.10
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[240, 0], [340, 0], [340, 100], [240, 100], [240, 0]]]
      }
    }
  ]
}
```

The coordinates above are illustrative only. Enter the correct CRS for the real reviewed geometry.

## Panel fields

- **Site ID:** private local site label.
- **Calibration dataset version:** version of the measured anchor evidence.
- **GeoJSON coordinate system:** usually `EPSG:4326`, or the projected CRS used by the file.
- **Boundary erosion:** removes edge pixels before extracting the signal. Default: 2 pixels.
- **Minimum valid pixels:** minimum clean pixels required per polygon. Default: 20.
- **Permit WARNING:** optional and explicit.
- **Replace existing:** required to overwrite prior private local-depth inputs for the same run.
- **Review confirmation:** mandatory.

## Results

A supported candidate returns:

```text
depth_status = calibrated_range
estimated_depth_min_m
estimated_depth_best_m
estimated_depth_max_m
```

An unsupported candidate returns no metre values and a status such as:

```text
insufficient_data
```

Common abstention reasons include:

- candidate signal outside measured anchor support;
- too few valid pixels;
- unsupported run quality;
- invalid or overlapping polygons;
- insufficient anchor separation.

## Privacy and safety

- Uploaded geometry remains in run-local private storage.
- The API response does not return geometry, coordinates, local paths, or download URLs.
- Outputs are filesystem-only.
- Existing reviewed inputs are preserved unless replacement is explicitly selected.
- The feature is disabled by default.
- The output is local and provisional, not transferable and not a global depth model.
- Classifier output and PCA anomaly are not used as depth evidence.
