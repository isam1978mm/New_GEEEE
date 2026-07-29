# Feasible Local Numerical Depth MVP Plan

Date: 2026-07-29

## Decision

The depth feature will no longer wait for a complete global calibration dataset before any numerical implementation begins.

The strict global Option 1 research remains useful, but it is no longer the shipping blocker.

The app will first implement a private, local, provisional numerical-depth mode that produces a range in metres only when an operator-controlled calibration package is present.

## Active plan

### Track A — Option 5 remains active

The existing radar anomaly review remains available and must continue to say **NOT DEPTH**.

### Track B — Local numerical-depth MVP becomes active

Implement a private local depth stage after `run_quality` using the architecture already defined in `docs/DEPTH_APP_ARCHITECTURE_SPEC.md`.

Initial output status:

```text
depth_status = calibrated_range
```

This is not `validated_range`.

### Track C — Global Option 1 research becomes background work

Continue finding better measured sites, but do not block the local MVP while waiting for a universal model.

Option 3 remains inactive.

## First calibration package

Use the recovered Tyrone 3X Test Plot 5 and Test Plot 6 measurements as the first provisional local anchors.

```text
Plot 5 mean = 26.8 inches = 0.68072 m
Plot 5 95% interval = 25.8–27.8 inches = 0.65532–0.70612 m

Plot 6 mean = 37.4 inches = 0.94996 m
Plot 6 95% interval = 33.5–41.3 inches = 0.85090–1.04902 m
```

Known limitations must be carried into the package:

```text
geometry_quality = derived_operator_review_required
stability_quality = provisional
transferability = local_only
validation_status = provisional
```

The plot geometry may be manually georeferenced from the official as-built sheet to current imagery, but the app must preserve a warning that the execution geometry is derived rather than official coordinate-controlled geometry.

## What the MVP will estimate

The MVP will estimate a **local cover-depth range** for candidates that are inside the same supported site or an explicitly approved local calibration area.

It will not claim:

- global depth;
- depth for arbitrary buried objects;
- transferability to unrelated soils, vegetation, slopes, climates, or sites;
- physical confirmation;
- validated holdout performance.

## Required calibration-package schema

A private local package should contain:

```text
depth_method_manifest.json
calibration_manifest.json
feature_manifest.json
support_rules.json
calibration_areas.geojson
calibration_rows.csv
checksums.sha256
```

Minimum calibration row fields:

```text
calibration_id
site_group_id
area_id
depth_best_m
depth_min_m
depth_max_m
source_type
source_reference
geometry_quality
stability_quality
surface_family
slope_family
vegetation_family
valid_from
valid_to
```

## MVP behavior

The depth stage remains disabled by default.

Allowed private setting:

```text
depth_mode = off | local_provisional_range
```

When `local_provisional_range` is selected, the stage must:

1. verify the private package and checksums;
2. require a usable upstream run;
3. require the candidate to fall inside the approved local support area;
4. compute the frozen local feature vector;
5. return a wide numerical range rather than a precise point claim;
6. include all provisional warnings;
7. abstain outside local support.

Required warnings for the first Tyrone package:

```text
LOCAL_ONLY
PROVISIONAL_CALIBRATION
DERIVED_GEOMETRY
POST_2014_STABILITY_NOT_FULLY_VERIFIED
NOT_TRANSFERABLE
NOT_PHYSICAL_CONFIRMATION
```

## Output wording

The frontend may display:

```text
Experimental local cover-depth range: 0.XX–0.XX m
Best local estimate: 0.XX m
Quality: provisional
Only valid for this locally calibrated area.
```

It must not display:

```text
Depth confirmed
Validated depth
Global depth
Buried-object depth
```

## Implementation slices

### Slice 1 — Package and stage skeleton

Create:

```text
app/pipeline/stages/depth_estimation.py
app/pipeline/depth/package.py
app/pipeline/depth/schema.py
tests/unit/test_depth_estimation.py
```

Implement package validation, disabled behavior, local-support checks, and provisional output schemas.

### Slice 2 — Tyrone calibration fixture

Create a private/local Tyrone package outside public artifacts. Add test fixtures with synthetic geometries and the measured depth intervals above.

### Slice 3 — Feature extraction and local mapping

Freeze a small nonduplicative feature set from the existing aligned radar, optical, DEM, and run-quality artifacts. Fit only a local mapping. Do not use classifier score or PCA anomaly as the depth target.

### Slice 4 — Private frontend display

Display the provisional range only when `depth_status = calibrated_range`. Preserve `Depth estimate: not available` for all other runs.

### Slice 5 — Validation expansion

Add new independently measured sites when available. Promote to `validated_range` only after a separate frozen-site validation and holdout process passes.

## Definition of done for the first usable depth feature

The MVP is complete when:

- a Tyrone local calibration package loads successfully;
- an in-support test candidate receives a numerical metre range;
- an out-of-support candidate abstains;
- the frontend distinguishes `calibrated_range` from `validated_range`;
- all warnings are visible;
- Option 5 remains unchanged;
- no global-depth claim is made;
- old runs remain readable;
- the full test suite passes.

## Current status

```text
Option 5 = active
Local numerical-depth MVP = active
Global Option 1 research = background, not a blocker
Option 3 = inactive
usable validated global calibration rows = 0
first provisional local anchors = 2 Tyrone plot means with intervals
training started = no
app local depth implementation started = design approved by this plan
```

## Exact next step

Implement Slice 1: the private package loader, schema, stage skeleton, provisional statuses, warnings, and unit tests. Do not run Earth Engine until the Tyrone support geometry is manually reviewed and frozen.
