# Buto Sentinel-1 Method Test — Execution Plan

**Date:** 2026-07-24  
**Branch:** `main`  
**Status:** completed successfully  
**Broad source search:** stopped

## Plain-English goal

Check whether the current app's neutral Sentinel-1 processing shows a clear spatial difference over the large Buto anomaly reported in the 2026 paper.

This is a detection and spatial-agreement test only.

It does not:

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

The test reused the existing app Sentinel-1 functions in:

```text
app/pipeline/stages/sar_rtc.py
```

The comparison features were limited to:

```text
VV_dB
VH_dB
VV_minus_VH_dB
VH_to_VV_linear_ratio
incidence_angle
```

The current app preprocessing is not claimed to be an exact reproduction of every SNAP setting used by the paper.

## Geometry handling

Two local GeoJSON files were used:

1. an approximate published anomaly / investigation footprint;
2. a nearby comparison footprint with similar size and surface setting.

Both files remained outside Git.

The comparison footprint is only a background comparison. It is not a confirmed negative.

Exact archaeological coordinates, geometry, and local paths were not written into Git or printed to the terminal.

## Local geometry used

The local input package contained:

```text
buto_target_figure5_approx.geojson
buto_background_north_approx.geojson
run_buto_dry_run.ps1
README.md
```

The target boundary was estimated from Figure 5 and the paper's reported 128 m by 62 m size. It is not survey-grade and has an estimated centre uncertainty of about 30 m.

The comparison polygon is a nearby same-size area selected only for the spatial screen. It is not a confirmed negative.

These approximate files are enough for an exploratory method run, but not for calibration intake or a final scientific claim.

## Implemented files

```text
scripts/run_buto_s1_method_screen.py
tests/unit/test_buto_s1_method_screen.py
```

The script:

- defaults to a no-network dry run;
- requires both geometry files to stay outside the repository;
- uses the fixed published date by default;
- queries only neutral Sentinel-1 features;
- keeps detailed feature values out of terminal output;
- marks the comparison area as unconfirmed;
- never creates a calibration record or enables app depth.

## Verification completed

Focused local tests:

```text
8 passed
```

The tests cover:

- dry-run privacy;
- different target and background geometry;
- exact-date acquisition requirements;
- same-orbit stability support;
- incidence angle remaining a control rather than a signal feature;
- too-few-pixel refusal;
- repository-local output refusal;
- detailed output staying outside Git.

No GitHub status check was attached to the direct `main` commits.

## Real Earth Engine execution result

The user ran the real Earth Engine command locally with the repository credentials.

Redacted result:

```text
query_executed = true
status = method_screen_complete_spatial_comparison_only
spatial_agreement_decision = spatial_agreement_supported
exact_date_acquisition_count = 1
usable_exact_date_acquisition_count = 1
support_acquisition_count = 36
same_orbit_support_count = 11
signal_feature_count = 4
stable_feature_count = 4
comparison_area_is_confirmed_negative = false
depth_measured = false
training_started = false
calibration_record_created = false
app_depth_enabled = false
```

## Meaning

The exact published Sentinel-1 date was found and produced a valid target-versus-background comparison.

All four neutral signal features kept a stable direction across 11 nearby same-orbit support acquisitions.

Allowed conclusion:

```text
spatial_radar_anomaly_supported = yes
repeatable_same_orbit_direction = yes
```

Not allowed:

```text
depth_measured = no
depth_calibration_record_ready = no
depth_model_training_ready = no
app_depth_output_ready = no
```

## Result record

The completed result is documented in:

```text
docs/DEPTH_BUTO_METHOD_TEST_RESULT_2026-07-24.md
```

## Completion boundary

This method test is complete.

Numerical depth prediction, calibration-pack intake, and app depth output remain blocked because the project still lacks survey-grade geometry, numerical depth uncertainty, confirmed comparison areas, and separate physical site groups.
