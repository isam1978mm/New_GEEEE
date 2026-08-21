# F195 — Route A: ship reviewed recorded measured depth

Date: 2026-08-21

## Purpose

Ship the already-implemented Tyrone recorded-depth lookup into the private operator app without turning recorded measurements into a predictive depth model.

This follows closure of the free-public-lidar permanent-cover validation route at F194.

## Hard scientific contract

Route A reports only official recorded measurements for reviewed Tyrone zones.

It does **not**:

- predict depth from the current run;
- interpolate between Tyrone plots;
- extrapolate to unknown zones;
- calibrate the NB formula;
- change the classifier;
- change the NB formula;
- claim global numerical-depth validation.

The method kind remains:

`operator_recorded_zone_lookup_v1`

## Existing measured records used

The existing reviewed package builder is unchanged.

### Tyrone TP5

- mean: **0.68072 m**
- 95% CI: **0.65532–0.70612 m**
- sample range: **0.6604–0.7112 m**
- sample count: **5**
- reported design depth: **0.6096 m**
- source: official 2006 3X as-built report
- method: five confirmation pits
- timing: after cover placement and before seeding

### Tyrone TP6

- mean: **0.94996 m**
- 95% CI: **0.85090–1.04902 m**
- sample range: **0.8636–1.0668 m**
- sample count: **5**
- reported design depth: **0.9144 m**
- source: official 2006 3X as-built report
- method: five confirmation pits
- timing: after cover placement and before seeding

## Safety repair added in F195

A manual TP5/TP6 dropdown would allow an operator to select a Tyrone measurement while viewing an unrelated run. F195 therefore does not use a free-form or manual zone selector.

Instead, the backend loads the already-reviewed WGS84 Tyrone six-plot geometry and the run's private processing footprint. A recorded value is eligible only when the complete reviewed TP5 or TP6 polygon is contained inside that run footprint.

If neither reviewed polygon is contained in the run footprint:

- status is `not_available`;
- recorded measurement count is zero;
- no metre value is returned;
- warning includes `no_reviewed_recorded_zone_in_run_footprint` and `no_predictive_extrapolation`.

No coordinates or geometry are returned through the API.

## API separation

A new endpoint is added:

`POST /runs/{run_id}/operator/recorded-depth`

The existing calibration endpoint remains separate:

`POST /runs/{run_id}/operator/local-depth`

This prevents recorded-measurement semantics from being mixed with calibrated-estimate semantics.

The recorded endpoint requires the same private operator authentication and per-run authorization as the existing local-depth endpoint, plus explicit operator review confirmation.

## UI behavior

`OperatorLocalDepthPanel` was previously disabled with `return null` after the old calibration UI was intentionally removed.

F195 restores that panel only for Route A recorded measurements.

The panel:

- is titled **Recorded measured depth**;
- says **REVIEWED ZONES ONLY**;
- requires explicit confirmation that this is a record lookup, not an estimate;
- shows only recorded mean, 95% CI, sample range/count, design depth, method, and timing;
- states prediction = no, interpolation = no, extrapolation = no;
- contains no calibration anchors, GeoJSON upload, signal interpolation controls, or candidate-depth estimation form.

## Files changed

- `app/services/operator_recorded_depth_app.py`
- `app/api/operator_local_depth.py`
- `frontend-v2/src/app/api/operatorRecordedDepth.ts`
- `frontend-v2/src/app/components/OperatorLocalDepthPanel.tsx`
- `tests/unit/test_operator_recorded_depth_app.py`
- this document

## Regression guards

Tests enforce:

1. only TP5 and TP6 map to reviewed recorded package zones;
2. a reviewed polygon must be fully inside the run bounds;
3. payloads use `recorded_depth_*` fields and contain no `estimated_depth_best_m`;
4. `no_predictive_extrapolation` is preserved;
5. the UI contains no calibration/anchor/GeoJSON controls;
6. the recorded endpoint remains separate from the calibration endpoint.

## F195 decision

**Route A is implemented for shipping as a bounded recorded-measurement lookup.**

It provides honest metres now for reviewed Tyrone TP5/TP6 records when those fixed reviewed zones are inside the selected run footprint. It provides no metre value for unknown runs/zones.

This is useful product functionality, but it does not resolve the separate scientific goal of globally predictive numerical depth.
