# Option 5 — Cluster-Zone Comparison and Disturbance Review

Date: 2026-08-01

## Decision

This slice continues the approved combined Option 1 + Option 5 plan.

It does **not** reopen or modify the deferred operator calibration panel.

## What this slice adds

The existing public-safe `objects_index.csv` artifact already contains:

- object ID;
- cluster ID;
- object area in pixels;
- mean PCA anomaly;
- maximum PCA anomaly.

The frontend now groups those existing objects by cluster ID and shows a within-run comparison table containing:

- cluster-zone ID;
- object count;
- total object area in pixels;
- share of all reported anomaly-object area;
- area-weighted mean anomaly;
- strongest peak anomaly;
- relative disturbance-review priority.

The relative review priority is rank-based inside the current run only:

- `higher`;
- `medium`;
- `lower`;
- `only zone` when one cluster is available.

No physical unit or universal threshold is attached to these labels.

## Required visible boundaries

The panel states that the output is:

- **WITHIN RUN**;
- **NOT MEASURED CHANGE**;
- a review-priority comparison;
- not measured displacement;
- not settlement;
- not temporal surface change;
- not physical confirmation;
- not depth.

## Surface-change status

A real surface-change output is still **NOT GOOD TO GO** from the current single-run `objects_index.csv` artifact.

A measured temporal result requires a validated before/after radar pair with compatible:

- acquisition geometry;
- orbit and polarization;
- preprocessing;
- pixel grid;
- valid-pixel support;
- observation periods;
- uncertainty and quality checks.

The UI therefore reports:

```text
surface_change_status = Not available
```

It does not convert a single-run anomaly score into a false temporal-change claim.

## Data and privacy boundary

This slice:

- reads no new artifact;
- adds no Earth Engine processing;
- exposes no coordinates;
- exposes no private paths;
- creates no depth stage;
- creates no calibration row;
- starts no model training;
- does not use the operator calibration feature.

## Option 1 parallel status

Option 1 remains targeted background evidence recovery.

Current global state remains:

```text
usable_global_calibration_rows = 0
global_training_started = false
global_numerical_depth_ready = false
```

The Tyrone/EMNRD agency-record route remains the highest-value pending evidence dependency. Broad unbounded site searching is not restarted by this slice.

## Validation required before merge

- production frontend build;
- synchronized `frontend-v2/dist`;
- focused Option 5 contract tests;
- complete repository test suite;
- authentication safety guard;
- direct-file-streaming guard;
- notebook safety guard.
