# Tyrone TP5/TP6 Provisional Sentinel-1 RTC Ordering Test — Preregistration

Date: 2026-07-29

Status: preregistered before the scientific query

## Purpose

Test whether two measured Tyrone 3X cover-depth zones show a stable ordering in raw public Sentinel-1 RTC measurements.

This is a local feasibility test. It is not a global depth model, not a calibration row, and not approval to estimate an unknown AOI in metres.

## Known measured anchors

- Test Plot 5: best 0.68072 m; measured interval 0.65532–0.70612 m.
- Test Plot 6: best 0.94996 m; measured interval 0.85090–1.04902 m.
- TP6 is the deeper measured zone.

## Geometry status

The official 2006 as-built drawing contains the plot boundaries but no standard coordinate grid. The plots were transferred to the 2020 coordinate-grid drawing using a multi-feature registration and then transformed to UTM Zone 12N using multiple mapped tailings facilities and USGS mine-waste polygons.

Checks completed before this preregistration:

- TP5 transformed area differs from its documented 4.06 acres by about 0.6%.
- Independent contour windows agree within about 7–11 m.
- The multi-facility mine-grid-to-UTM fit has a worst group residual of about 35 m.
- Both outer plots fall completely inside the USGS 3X polygon.
- Each test polygon is eroded inward by 40 m before radar extraction.
- The remaining core widths are approximately 36 m for TP5 and 40 m for TP6.

The geometry is therefore labelled `provisional_derived_geometry_40m_core`. It is not an official survey polygon.

## Fixed data source and period

- STAC: Microsoft Planetary Computer.
- Collection: `sentinel-1-rtc`.
- Period: 2018-01-01 through 2023-12-31 (`2024-01-01` exclusive).
- Instrument mode: IW.
- Required polarizations: VV and VH.
- One orbit-state/relative-orbit group is selected using only maximum distinct-month coverage, then acquisition count. Signal values do not affect orbit selection.

## Fixed raster handling

- CRS: EPSG:32612.
- Pixel size: 10 m.
- Fixed common grid covering both preregistered cores.
- Nearest-neighbour source sampling.
- RTC linear power converted to dB using `10 * log10(value)`.
- Multiple acquisitions in one calendar month are combined by per-pixel median.
- A zone-month requires at least 15 valid fixed-grid pixels.

## Preregistered features

Only these raw or directly interpretable radar measurements are evaluated:

1. mean VV backscatter in dB;
2. mean VH backscatter in dB;
3. VV minus VH in dB (`log_ratio_db`).

The monthly comparison is always:

```text
TP6 minus TP5
```

Classifier outputs, target masks, PCA anomaly scores, Option 5 anomaly values, and named treasure/geophysics heuristic layers are prohibited.

## Pass rule

A feature passes the local ordering screen only when all conditions hold:

1. at least 24 usable calendar months;
2. one non-zero TP6-minus-TP5 sign occurs in at least 70% of usable non-zero months;
3. the same sign occurs in at least 60% of usable non-zero months in every season (DJF, MAM, JJA, SON);
4. every season has at least four usable non-zero months.

The workflow also reports the Wilson 95% interval for the dominant-sign fraction, but the interval is descriptive and is not an additional pass criterion.

## Interpretation rules

- If no feature passes: `ordering_not_supported`. Do not create a calibration row, train a model, or enable unknown-AOI depth.
- If a feature passes: `ordering_supported` means provisional local ordering evidence only. It still does not justify interpolation in metres or transfer to another AOI.
- No result from this test may be labelled validated depth.

## Outputs

The workflow writes:

- `result.json`;
- `monthly_features.csv`;
- `selected_source_items.csv`;
- `preregistered_geometry.geojson`.

## Safety flags fixed to false

```text
earth_engine_query_executed = false
classifier_output_used = false
pca_anomaly_used = false
calibration_record_created = false
training_started = false
app_depth_enabled = false
```
