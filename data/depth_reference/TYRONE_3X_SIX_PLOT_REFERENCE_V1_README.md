# Tyrone 3X Six-Plot Depth Reference v1

Date: 2026-08-18

## Purpose

This dataset is the source-controlled reference for the Tyrone 3X cover-depth test plots TP1, TP2, TP3, TP5, TP6, and TP7.

It is intended for scientific screening of replacement numerical-depth methods. It must not be used to claim that the existing NB depth proxy is a validated depth measurement.

## Official source

Primary geometry/plot source:

- `3X_CQAR_010_R0.pdf`
- drawing title: `TAILING IMPOUNDMENT TEST PLOTS AS-BUILT`
- source page: 1

The drawing explicitly labels:

| Plot | Nominal treatment | Official printed acreage |
|---|---:|---:|
| TP1 | 2 ft | 4.9 ac |
| TP2 | 3 ft | 5.4 ac |
| TP3 | 4 ft | 4.7 ac |
| TP5 | 2 ft | 4.1 ac |
| TP6 | 3 ft | 4.5 ac |
| TP7 | 4 ft | 2.3 ac |

## Measured cover-depth references

| Plot | Surface | Samples (in) | Mean (m) | Min (m) | Max (m) |
|---|---|---|---:|---:|---:|
| TP1 | outslope | 27, 27, 26, 27, 32 | 0.70612 | 0.66040 | 0.81280 |
| TP2 | outslope | 36, 34, 39, 42, 36 | 0.94996 | 0.86360 | 1.06680 |
| TP3 | outslope | 50, 49, 54, 52, 47 | 1.28016 | 1.19380 | 1.37160 |
| TP5 | top surface | 28, 26, 26, 28, 26 | 0.68072 | 0.66040 | 0.71120 |
| TP6 | top surface | 40, 35, 42, 36, 34 | 0.94996 | 0.86360 | 1.06680 |
| TP7 | top surface | 50, 50, 52, 51, 54 | 1.30556 | 1.27000 | 1.37160 |

## Geometry provenance

The polygons in `tyrone_3x_six_plot_reference_v1.geojson` are digitized from the visible plot-boundary centerlines on the official coordinate-controlled AS-BUILT drawing.

Important limitations:

- They are **not original CAD/survey vertices**.
- Coordinates are in the drawing's **local Tyrone mine grid in feet**.
- Westing labels are represented as signed negative W values; northing is positive N.
- No EPSG code is assigned because no global CRS transform has been verified in this artifact.
- The GeoJSON is therefore a **source-grid reference**, not WGS84 web-map geometry.
- Do not overlay it directly on Sentinel/Landsat/DEM rasters until the local-grid-to-run-raster transform is independently verified.

## Acreage QA

The official printed acreage is retained independently from the digitized planimetric polygon area. The geometry was **not adjusted to force an acreage match**.

| Plot | Official (ac) | Digitized planimetric (ac) | Difference |
|---|---:|---:|---:|
| TP1 | 4.9 | 4.8261 | -1.51% |
| TP2 | 5.4 | 5.3456 | -1.01% |
| TP3 | 4.7 | 4.6250 | -1.60% |
| TP5 | 4.1 | 3.9941 | -2.58% |
| TP6 | 4.5 | 4.3725 | -2.83% |
| TP7 | 2.3 | 2.1934 | -4.63% |

The source material available here does not establish why printed acreage and digitized planimetric area differ. Do not silently interpret the printed acreages as slope-corrected surface area, CAD area, or another quantity without supporting records.

## Completed Tyrone run

Reference run ID:

`0c6d05ab-798b-40d4-b608-e01deabd6cb8`

The completed run outputs are not committed in the repository. The reference dataset therefore records the run ID but leaves `pixel_count` empty until the verified global transform and run rasters are available together.

## NB numerical-depth status

**CLOSED / FAILED VALIDATION.**

The existing NB route failed:

- raw absolute numerical depth;
- TP5/TP6 exact-drawing-geometry numerical accuracy;
- two-anchor calibration;
- unseen TP7 holdout;
- independent TP1/TP2/TP3 depth ordering;
- same-depth replicate consistency across surface types;
- individual NB component monotonicity screening.

Raw NB may remain only as an **uncalibrated notebook-derived proxy**. It must not be presented as measured or validated depth in metres.

## Replacement-method gate

Do not train a replacement model yet. First recover/verify the local-mine-grid to completed-run raster transform, then extract raw or less-derived physical features for all six plots, excluding `NB_DEPTH` as the starting variable.

Initial feature families:

- Sentinel-1 VV and VH;
- VV/VH or dB difference/ratio;
- ascending/descending differences where available;
- temporal SAR variation where available;
- incidence angle;
- DEM elevation, slope, aspect, roughness, TPI, curvature;
- thermal/LST and thermal change where available;
- optical vegetation/surface variables where defensible.

For each plot, retain mean, median, standard deviation, Q25, Q75, and pixel count.

The first scientific question is: **after accounting for surface type, does any raw physical feature change consistently with measured depth?**
