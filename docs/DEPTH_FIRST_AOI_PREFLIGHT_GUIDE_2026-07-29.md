# First AOI local-depth preflight guide

## Status

The app can run operator-calibrated local AOI depth, but only when the operator supplies reviewed same-site measured anchors.

This guide prepares the first real GeoJSON and explains the new browser preflight.

## Enable the private panel

Add this to `.env` and restart the app:

```text
OPERATOR_LOCAL_DEPTH_APP_ENABLED=true
```

The repository `.env.example` now lists the flag, but it remains false by default.

## Start from the safe template

Use either:

- the **Download blank GeoJSON template** button in the app; or
- `docs/examples/operator_local_depth_first_aoi_template.geojson`.

The template intentionally contains:

- `template_only: true`;
- placeholder feature IDs;
- `null` coordinates.

It cannot pass preflight until all placeholders are replaced and `template_only` is removed.

## Minimum contents

One file must contain:

- at least two measured anchor polygons;
- at least one candidate polygon;
- unique non-empty `feature_id` values;
- `role: anchor` or `role: candidate` on every feature;
- Polygon or MultiPolygon geometry;
- closed rings with finite numeric coordinates;
- anchor depth ranges in metres satisfying:

```text
depth_min_m <= depth_best_m <= depth_max_m
```

The measured anchors must include at least two distinct `depth_best_m` values.

## What browser preflight now rejects

Before the request is sent, the panel rejects:

- unfinished `template_only` files;
- placeholder IDs;
- duplicate IDs;
- unsupported roles;
- missing or malformed geometry;
- unclosed or degenerate rings;
- nonnumeric coordinates;
- missing, negative, or nonfinite anchor depth values;
- incorrectly ordered depth ranges;
- fewer than two anchors;
- no candidates;
- anchors with only one repeated best depth.

A passing file displays:

- total feature count;
- anchor count;
- candidate count;
- anchor ID summary;
- candidate ID summary;
- minimum-to-maximum measured anchor support in metres.

## What browser preflight does not prove

The backend still performs the decisive checks:

- polygon intersection with the completed run raster;
- boundary erosion;
- minimum valid pixel count;
- nonoverlapping eroded interiors;
- usable run quality;
- anchor signal monotonicity;
- candidate signal support;
- no extrapolation.

Passing browser preflight means the file is structurally ready to submit. It does not guarantee that every candidate will receive a metre range.

## First real run checklist

1. Complete a normal app run and confirm `logRatio_dB.tif` and the run-quality summary exist.
2. Obtain at least two measured depth areas from the same site and observation context.
3. Draw conservative interior polygons away from boundaries and disturbed infrastructure.
4. Add one or more candidate polygons from that same local site.
5. Complete the template and remove `template_only`.
6. Open **Settings** and show **Operator private tools**.
7. Open the completed run and expand **Local depth calibration — operator only**.
8. Upload the GeoJSON and require **Preflight passed**.
9. Enter the site ID and calibration dataset version.
10. Confirm operator review and run the calibration.

## Scientific boundary

This remains local interpolation only. It does not create a global radar-to-depth model, does not transfer between sites, and does not infer depth without measured local anchors.
