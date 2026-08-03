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

## Conservative filters

When the corresponding ATL08 fields are present, the audit keeps:

- snow-free land segments;
- at least three terrain photons;
- reported terrain-height uncertainty at or below 1.0 m;
- finite terrain median height and coordinates.

Repeat matching is stricter than a generic nearest-neighbour join:

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

A pass would still not prove placed-material thickness. The paired observations
must also fall on the actual target and bracket a known construction event.

## Explicit non-goals

The audit does not:

- create calibration anchors or zones;
- interpolate ATL08 segments into a complete map;
- invoke the local depth engine;
- change the orchestrator or frontend;
- establish depth to a buried object;
- establish that Sentinel-1 predicts depth.
