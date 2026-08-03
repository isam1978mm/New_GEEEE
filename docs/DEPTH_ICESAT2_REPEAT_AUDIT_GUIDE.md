# ICESat-2 ATL08 repeat-point audit

Status: read-only precision audit; no depth, calibration, or app-unblock claim.

## Purpose

GEDI provided real repeated laser observations, but its measured 95% detection
floor remained roughly 2–3 m. ICESat-2 is the last cheap free laser route worth
checking before closing global satellite altimetry for 0.6–1.0 m covers.

This tool queries official ATL08 100 m terrain segments through SlideRule's
`atl08x` service. It does not interpolate sparse points into a raster.

## Optional dependency

The main app does not depend on SlideRule. Install it only in the local virtual
environment used for this audit:

```powershell
cd C:\Dev\New_GEE
.\.venv\Scripts\python.exe -m pip install "sliderule>=5.4.3"
```

## Run

```powershell
cd C:\Dev\New_GEE_depth
git pull

cd C:\Dev\New_GEE
.\.venv\Scripts\python.exe ..\New_GEE_depth\scripts\audit_icesat2_repeat_points.py `
  --run-dir .\data\runs\a4881db6-d92e-4ebc-b628-8a1b089db20b `
  --target-m 0.7
```

The script prints JSON only. It writes nothing to the run.

## Filters and diagnostics

The audit keeps finite snow-free land segments with at least three terrain
photons. ATL08 `h_te_uncertainty` is reported as a distribution and as combined
uncertainty for repeat pairs.

There is no mandatory uncertainty ceiling by default. The first implementation
used a 1.0 m ceiling and rejected every returned segment before repeat precision
could be measured. Apply a ceiling only when explicitly required:

```powershell
  --maximum-uncertainty-m 2.0
```

Repeat matching remains conservative:

1. early and late observations must have the same reference ground track;
2. they must use the same orientation-independent detector spot;
3. they must come from different ICESat-2 cycles;
4. they must be reciprocal nearest neighbours;
5. their centres must be within 5, 10, or 15 m.

## Decision gate

The route is marked ready for a point-change prototype only if one of the 5 m
or 10 m bands has:

- at least 30 unique reciprocal pairs; and
- a measured 95% detection floor at or below the requested target, default
  0.7 m.

The output also reports the ATL08-provided uncertainty distribution. A pass in
measured repeat spread would still require review of those reported uncertainties,
target overlap, and event timing before any thickness interpretation.

A pass would not prove placed-material thickness. The paired observations must
also fall on the actual target and bracket a known construction event.

## Explicit non-goals

The audit does not:

- create calibration anchors or zones;
- interpolate ATL08 segments into a complete map;
- invoke the local depth engine;
- change the orchestrator or frontend;
- establish depth to a buried object;
- establish that Sentinel-1 predicts depth.
