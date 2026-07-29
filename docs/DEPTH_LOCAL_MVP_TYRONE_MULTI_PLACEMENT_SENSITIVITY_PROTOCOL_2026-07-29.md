# Tyrone multi-placement raw Sentinel-1 sensitivity protocol

Date: 2026-07-29

Status: preregistered before Earth Engine execution

## Purpose

Test whether the deeper measured Tyrone zone (TP6) and shallower measured zone (TP5) retain one consistent local Sentinel-1 polarization ordering despite the remaining map-registration uncertainty.

This is a local method screen. It is not global model training and it does not enable app depth output.

## Fixed measured anchors

```text
TP5: 0.65532–0.70612 m; best 0.68072 m
TP6: 0.85090–1.04902 m; best 0.94996 m
```

## Geometry ensemble

The 2006 figure scale and north orientation are locked. No free rescaling or rotation is allowed during the scientific query.

Nine source-to-2020 translation hypotheses are used:

```text
(484, 504)  best local chamfer placement
(481, 477)  (493, 477)  (505, 477)
(481, 492)              (505, 492)
(481, 507)  (493, 507)  (505, 507)
```

Four independent 2020-image-to-ground similarity transforms are used:

1. least-squares fit to USGS centroids for No. 3, No. 3X, and No. 2;
2. exact two-control fit using No. 3 and No. 3X;
3. exact two-control fit using No. 3X and No. 2;
4. exact two-control fit using No. 3 and No. 2.

Total geometry hypotheses:

```text
9 translations × 4 ground transforms = 36 placements
```

TP5 and TP6 outlines are manually digitized from the official rendered 2006 drawing and adjusted only enough to match the official printed areas (approximately 4.06 and 4.50 acres).

## Earth Engine collection

```text
COPERNICUS/S1_GRD
instrumentMode = IW
polarizations include VV and VH
period = 2018-01-01 through 2023-12-31
```

The relative orbit and pass are selected once using acquisition/month coverage across the union of all placement polygons. Signal values are not used for orbit selection.

## Primary feature

```text
log_ratio_db = VV_dB - VH_dB
```

This is a neutral polarization contrast. It is not called penetration, mass, metal, target strength, or depth.

## Diagnostic fields

```text
VV_dB
VH_dB
incidence angle
valid-pixel count
```

Classifier outputs, PCA anomaly, target masks, report layers, and heuristic target features are forbidden as depth evidence.

## Monthly extraction

For each selected-orbit month:

1. create the monthly median image;
2. reduce TP5 and TP6 for every geometry hypothesis at 10 m;
3. require at least 20 valid VV/VH pixels in both polygons;
4. require the TP5/TP6 mean-incidence difference to be no more than 0.5 degrees;
5. compute:

```text
difference = TP6_log_ratio_db - TP5_log_ratio_db
```

A zero difference does not support either sign.

## Placement pass rule

A placement passes only when all conditions hold:

```text
usable months >= 24
dominant sign fraction >= 0.70
all four seasons have >= 4 usable months
each season retains the placement's dominant sign in >= 0.60 of its usable months
```

The dominant sign may be positive or negative. It is not selected in advance because the known anchors determine which local sign corresponds to the deeper zone. The sign must nevertheless remain consistent across placements and seasons.

## Overall pass rule

The method screen is supported only when:

```text
at least 29 of 36 placements pass
all counted passing placements share the same dominant sign
```

This is equivalent to at least 80% placement support, rounded up.

## Result states

```text
ordering_supported
ordering_inconsistent
insufficient_data
auth_required
query_error
```

## Consequences

If `ordering_supported`:

- record a provisional local method screen;
- allow implementation of a two-anchor local interpolation experiment with wide uncertainty;
- keep the output labelled local, provisional, and non-transferable;
- do not create a global calibration row.

If any other state:

- retain the known-zone lookup only;
- create no interpolation model;
- create no calibration row;
- keep app depth disabled for unknown candidates.

## Safety state

```text
global_training = prohibited
app_depth_enablement = prohibited
secret_printing = prohibited
interactive_ee_authentication = prohibited
notebook_or_classifier_outputs_as_depth_evidence = prohibited
```
