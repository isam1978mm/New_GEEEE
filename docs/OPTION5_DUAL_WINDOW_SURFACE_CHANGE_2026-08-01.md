# Option 5 — Guarded Dual-Window Radar Surface-Change Review

Date: 2026-08-01

## Purpose

This slice implements the unfinished temporal part of Option 5 without touching the deferred local-depth calibration panel.

The result is a **radar backscatter surface-change review indicator**. It is not:

- measured ground displacement;
- settlement;
- elevation change;
- physical confirmation;
- numerical depth.

## Why a new stage is required

The existing SAR RTC stage produces one final median composite for one configured date window. The existing `objects_index.csv` is also a single-run anomaly artifact. Neither can support a temporal claim by itself.

The new `surface_change` stage therefore obtains a second, immediately preceding Sentinel-1 window and compares it with the current SAR window.

## Window rule

The current SAR window remains the **after** window.

The **before** window:

- has the same duration as the after window;
- ends when the after window starts;
- must be at least 28 days long.

For the current default SAR window:

```text
after  = 2026-01-01 to 2026-03-01
before = 2025-11-02 to 2026-01-01
```

## Mandatory compatibility gates

The stage abstains unless:

1. both windows contain at least two selected ASC/DESC pairs;
2. ascending and descending relative-orbit track signatures match exactly;
3. both products use the same authoritative run grid;
4. both use the same local DEM RTC calculation;
5. at least 1,000 pixels pass nodata and incidence-angle compatibility checks;
6. before/after incidence differs by no more than 1.5 degrees at retained pixels.

An abstention writes a public-safe summary with a reason code and does not fail the entire run.

## Indicator calculation

The comparison uses:

```text
logRatio_dB = VV_dB - VH_dB
```

For compatible pixels:

1. calculate after minus before log-ratio;
2. remove the scene-wide median difference;
3. calculate robust scale from median absolute deviation;
4. set the review threshold to the larger of:
   - 1.0 dB;
   - three robust standard deviations;
5. report the fraction of valid pixels exceeding that threshold.

The local indicator raster is:

```text
absolute centered log-ratio difference / review threshold
```

Values at or above `1` meet the run-specific review threshold.

## Outputs

Public-safe:

- `option5_surface_change_summary.json`

Local-sensitive and not HTTP-served:

- `option5_surface_change_indicator.tif`
- `option5_logratio_delta_db.tif`

The public summary contains dates, pair counts and aggregate statistics only. It contains no coordinates, geometry, CRS transform, private path or raster values.

## Product wording

The frontend labels the output:

- `DUAL-WINDOW RADAR SURFACE-CHANGE REVIEW`;
- `RADAR BACKSCATTER ONLY`;
- `NOT DEPTH OR SETTLEMENT`.

It states that moisture, vegetation and surface roughness may contribute.

## Execution control

Configuration:

```text
OPTION5_SURFACE_CHANGE_ENABLED=true
```

The stage is inserted only when:

```text
OPTION5_SURFACE_CHANGE_ENABLED=true
EE_REAL_EXECUTION_ENABLED=true
```

This preserves deterministic/offline test pipelines and prevents an unexpected Earth Engine request when real execution is disabled.

## Older runs

Existing completed runs do not contain the new public summary. They must be rerun after this stage is merged and enabled.

## Option 1 boundary

This work does not create any depth-calibration row and does not change the current Option 1 result:

```text
usable_global_calibration_rows = 0
global_training_started = false
global_numerical_depth_ready = false
```
