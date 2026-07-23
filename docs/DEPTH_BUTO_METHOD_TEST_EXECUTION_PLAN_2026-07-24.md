# Buto Sentinel-1 Method Test — Execution Plan

**Date:** 2026-07-24  
**Branch:** `main`  
**Status:** authorized bounded method test  
**Broad source search:** stopped

## Plain-English goal

Check whether the current app's neutral Sentinel-1 processing shows a clear spatial difference over the large Buto anomaly reported in the 2026 paper.

This is a detection and spatial-agreement test only.

It will not:

- train a depth model;
- calculate wall depth from Sentinel-1;
- treat a nearby comparison area as a confirmed no-target site;
- enable app depth output;
- restart broad source searching.

## Fixed evidence from the paper

The test is based on the published Buto / Tell el-Fara'in study:

- Sentinel-1 GRD acquisition date: **2018-05-05**;
- mode: Interferometric Wide Swath;
- polarisations: VV and VH;
- reported large oval anomaly: about **128 m by 62 m**;
- ground follow-up: ERT, total-station survey, boreholes, and excavation;
- excavation-confirmed mudbrick wall tops: about **3.1 to 4.1 m** below the local surface.

The paper used SNAP processing including orbit correction, thermal-noise removal, calibration, multilooking, speckle filtering, terrain correction, and conversion to dB.

## Repository method used

The test will reuse the existing app Sentinel-1 functions in:

```text
app/pipeline/stages/sar_rtc.py
```

The comparison features are limited to:

```text
VV_dB
VH_dB
VV_minus_VH_dB
VH_to_VV_linear_ratio
incidence_angle
```

The current app preprocessing is not claimed to be an exact reproduction of every SNAP setting used by the paper.

## Geometry handling

Two local GeoJSON files are required:

1. the published large anomaly / investigation footprint;
2. a nearby comparison footprint with similar size and surface setting.

Both files must remain outside Git.

The comparison footprint is only a background comparison. It is not a confirmed negative unless independent evidence later proves that it contains no buried feature.

Exact archaeological coordinates, geometry, and local paths must not be written into Git or printed to the terminal.

## Test steps

1. Validate both local polygons and the fixed image date.
2. Query Sentinel-1 acquisitions covering the polygons around 2018-05-05.
3. Require an acquisition on the exact published date.
4. Process each usable acquisition with the current neutral app SAR functions.
5. Calculate target and background pixel counts and median feature values.
6. Calculate target-minus-background differences for the exact date.
7. Use nearby same-orbit acquisitions only as a stability check.
8. Write detailed numbers only to a local output file outside Git.
9. Print only a redacted status summary to the terminal.

## Pass and stop meanings

### Method-screen pass

```text
method_screen_complete_spatial_comparison_only
```

This means the exact published date was found and a valid target-versus-background comparison was produced.

It does not mean that Sentinel-1 measured depth.

### Useful positive result

A useful result would show that one or more neutral features have a repeatable target-versus-background direction on the published date and supporting same-orbit dates.

The interpretation remains:

```text
spatial_radar_anomaly_supported
```

not:

```text
depth_measured
```

### Failure or hold states

The test stops without interpretation when:

- no exact-date Sentinel-1 acquisition is available;
- either polygon has too few valid pixels;
- no same-orbit support exists;
- geometry is missing or invalid;
- Earth Engine cannot be queried;
- results depend only on one unstable feature or one image.

## Completion boundary

After implementation and local execution, the allowed conclusion is one of:

```text
spatial_agreement_supported
spatial_agreement_not_supported
method_screen_inconclusive
```

Numerical depth prediction, calibration-pack intake, and app depth output remain blocked regardless of this test result.
