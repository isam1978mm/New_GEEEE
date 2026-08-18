# Tyrone 3X Six-Plot Depth Reference v1

Date: 2026-08-18

## Purpose

This is the source-controlled Tyrone 3X reference for TP1, TP2, TP3, TP5, TP6 and TP7. It supports scientific screening of replacement numerical-depth methods.

It must **not** be used to claim the existing NB proxy is a validated depth measurement.

## Official plot source

Primary plot geometry source:

- `3X_CQAR_010_R0.pdf`
- `TAILING IMPOUNDMENT TEST PLOTS AS-BUILT`

| Plot | Surface | Nominal | Measured mean (m) | Official drawing acreage |
|---|---|---:|---:|---:|
| TP1 | outslope | 2 ft | 0.70612 | 4.9 |
| TP2 | outslope | 3 ft | 0.94996 | 5.4 |
| TP3 | outslope | 4 ft | 1.28016 | 4.7 |
| TP5 | top surface | 2 ft | 0.68072 | 4.1 |
| TP6 | top surface | 3 ft | 0.94996 | 4.5 |
| TP7 | top surface | 4 ft | 1.30556 | 2.3 |

All individual measured samples/min/max remain recorded in `tyrone_3x_six_plot_reference_v1.csv` and the local-grid GeoJSON.

## Geometry layers

### Local source-grid layer

`tyrone_3x_six_plot_reference_v1.geojson`

- Tyrone Mine local drawing grid in feet;
- W values represented as negative eastings;
- boundaries digitized from official AS-BUILT drawing centerlines;
- not original CAD/survey vertices.

Digitized planimetric acreage was not adjusted to force agreement with printed acreage:

| Plot | Official (ac) | Digitized (ac) | Difference |
|---|---:|---:|---:|
| TP1 | 4.9 | 4.8261 | -1.51% |
| TP2 | 5.4 | 5.3456 | -1.01% |
| TP3 | 4.7 | 4.6250 | -1.60% |
| TP5 | 4.1 | 3.9941 | -2.58% |
| TP6 | 4.5 | 4.3725 | -2.83% |
| TP7 | 2.3 | 2.1934 | -4.63% |

### WGS84 raster-screening layer — VERIFIED

`tyrone_3x_six_plot_reference_v1_wgs84.geojson`

The previously missing Tyrone Mine grid → global transform has now been independently validated from an official 2024 Freeport-McMoRan Tyrone Emma exploration application containing **34 rows with both WGS84 longitude/latitude and local Easting/Northing**.

A separate official 2021 Tyrone Emma hydrogeologic report explicitly identifies local Northing/Easting as being in the **Tyrone Mine coordinate system**.

Validation design:

- fit only four spatially distributed control rows: EM24-07, EM24-14, EM24-26, EM24-33;
- hold out the other 30 official coordinate pairs;
- maximum holdout residual: `0.002533 m`;
- no depth/NB values used in transform fitting or validation.

After validation passed, the similarity transform was refit to all 34 pairs. Final maximum residual: `0.001657 m`.

Artifacts:

- `tyrone_mine_grid_wgs84_controls_v1.csv`
- `tyrone_mine_grid_to_global_transform_v1.json`
- `tyrone_3x_six_plot_reference_v1_wgs84.geojson`

Intermediate CRS: `EPSG:32612` — WGS84 / UTM Zone 12N.

The transform is more than adequate for the intended **10 m raster screening**. The limiting spatial uncertainty is now the drawing-digitized plot boundary, not the grid/global transform.

Do **not** describe the WGS84 vertices as original survey/CAD vertices.

## Completed Tyrone run

Reference run ID:

`0c6d05ab-798b-40d4-b608-e01deabd6cb8`

The global six-plot geometry is now raster-ready. Pixel counts remain to be populated during raw-feature extraction from the completed run or existing sensor assets.

## NB numerical-depth status

**CLOSED / FAILED VALIDATION.**

Raw NB may remain only as an **uncalibrated notebook-derived proxy**. Resolving the geometry transform does not reopen or validate NB numerical depth.

## Replacement-method status

The geometry gate is now **PASSED**.

Do not train a replacement model yet. The next scientific step is raw/less-derived feature extraction for all six plots, excluding `NB_DEPTH`, followed by same-depth replicate screening:

- TP1 ↔ TP5
- TP2 ↔ TP6
- TP3 ↔ TP7

Candidate feature families:

- Sentinel-1 VV and VH;
- VV/VH or dB difference/ratio;
- ascending/descending differences where available;
- temporal SAR variation where available;
- incidence angle;
- DEM elevation, slope, aspect, roughness, TPI, curvature;
- thermal/LST and thermal change where available;
- optical surface variables where defensible.

For each plot retain mean, median, standard deviation, Q25, Q75 and pixel count.

First scientific question: **after accounting for surface type, does any raw physical feature change consistently with measured depth?**
