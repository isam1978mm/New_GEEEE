# Tyrone multi-placement public RTC sensitivity protocol v2

Date: 2026-07-29

Status: preregistered before reading TP5/TP6 radar values

## Why protocol v2 exists

Protocol v1 targeted Google Earth Engine `COPERNICUS/S1_GRD`, but both the pull-request and branch-push runs returned `auth_required`. Historical review confirmed that this repository never had a usable Earth Engine credential; the earlier RMA auth workflow also completed with `AUTH_REQUIRED`.

Protocol v2 preserves the scientific geometry and pass thresholds but changes the execution source to the anonymously accessible Microsoft Planetary Computer `sentinel-1-rtc` collection.

The source substitution was selected from metadata only. Before this protocol was written:

- the public STAC catalog was queried;
- collection IDs, orbit metadata, projection, asset keys, nodata, dtype, and byte-range accessibility were inspected;
- no TP5/TP6 radar pixels or ordering values were read.

## Fixed measured anchors

```text
TP5: 0.65532–0.70612 m; best 0.68072 m
TP6: 0.85090–1.04902 m; best 0.94996 m
```

## Geometry ensemble

The geometry ensemble is unchanged from protocol v1.

Nine source-to-2020 translation hypotheses:

```text
(484, 504)  best local chamfer placement
(481, 477)  (493, 477)  (505, 477)
(481, 492)              (505, 492)
(481, 507)  (493, 507)  (505, 507)
```

Four independent 2020-image-to-ground similarity transforms:

1. least-squares fit to USGS centroids for No. 3, No. 3X, and No. 2;
2. exact two-control fit using No. 3 and No. 3X;
3. exact two-control fit using No. 3X and No. 2;
4. exact two-control fit using No. 3 and No. 2.

Total:

```text
9 translations × 4 ground transforms = 36 placements
```

Each TP5 and TP6 hypothesis receives a 20 m inward buffer before extraction.

## Public radar source

```text
STAC API = https://planetarycomputer.microsoft.com/api/stac/v1
collection = sentinel-1-rtc
instrument mode = IW
polarizations = VV and VH
period = 2018-01-01 through 2023-12-31
```

The source probe confirmed:

```text
asset dtype = float32
asset nodata = -32768
asset spatial resolution = 10 m
sample projection at Tyrone = EPSG:32613
asset scale = linear intensity
scale factor = 1
add offset = 0
```

The RTC product is calibrated and radiometrically terrain corrected. Linear values are converted to decibels using:

```text
VV_dB = 10 × log10(VV_linear)
VH_dB = 10 × log10(VH_linear)
```

Only finite values greater than zero are converted. Nodata, zero, negative, and nonfinite values remain invalid.

## Orbit selection

Relative orbit and pass are selected once using metadata only:

1. greatest number of distinct acquisition months across the full period;
2. greatest acquisition count as tie-breaker;
3. deterministic orbit-state and relative-orbit ordering as final tie-breaker.

Radar values are not used to select the orbit.

## Fixed analysis grid

All selected assets are read onto one fixed grid:

```text
CRS = EPSG:32613
pixel size = 10 m
bounds = snapped outward to the union of all buffered placement polygons
resampling = nearest neighbour
```

The fixed grid prevents acquisition-specific pixel shifts from changing the polygon samples.

## Monthly processing

For each selected-orbit month:

1. read every available VV and VH RTC acquisition on the fixed grid;
2. convert each acquisition from linear intensity to decibels;
3. calculate the per-pixel monthly median separately for VV_dB and VH_dB;
4. calculate:

```text
log_ratio_db = monthly_median_VV_dB - monthly_median_VH_dB
```

5. reduce the monthly image over TP5 and TP6 for every placement;
6. require at least 20 valid log-ratio pixels in both polygons;
7. compute:

```text
difference = TP6_log_ratio_db - TP5_log_ratio_db
```

A zero difference supports neither sign.

## Incidence-control substitution

Planetary Computer RTC exposes no incidence-angle asset or item property for this collection. Therefore the v1 numerical incidence-difference gate cannot be reproduced.

It is replaced before value inspection by all of the following fixed controls:

- TP5 and TP6 are always read from the same RTC acquisition;
- all acquisitions share one selected relative orbit and pass;
- data are radiometrically terrain corrected;
- all acquisitions are resampled to one fixed 10 m grid;
- both polygons must independently meet the valid-pixel threshold;
- orbit, CRS, resolution, source item ID, and acquisition date are retained in the private result package.

No claim is made that these controls are equivalent to a measured incidence-angle layer. This limitation must remain in the final interpretation.

## Primary feature

```text
log_ratio_db = VV_dB - VH_dB
```

This is a neutral polarization contrast. It is not penetration, mass, metal, target strength, or physical depth.

## Placement pass rule

Unchanged from protocol v1. A placement passes only when:

```text
usable months >= 24
dominant sign fraction >= 0.70
all four seasons have >= 4 usable months
each season retains the placement's dominant sign in >= 0.60 of its usable months
```

The dominant sign may be positive or negative, but it must be stable across placements and seasons.

## Overall pass rule

Unchanged from protocol v1:

```text
at least 29 of 36 placements pass
all counted passing placements share the same dominant sign
```

## Result states

```text
ordering_supported
ordering_inconsistent
insufficient_data
source_unavailable
query_error
```

## Consequences

If `ordering_supported`:

- record a provisional local method screen;
- allow implementation of a two-anchor local interpolation experiment with wide uncertainty;
- keep the output labelled local, provisional, and non-transferable;
- do not create a global calibration row.

For any other state:

- retain the reviewed known-zone lookup only;
- create no interpolation model;
- create no calibration row;
- keep app depth disabled for unknown candidates.

## Forbidden evidence and changes

```text
classifier output = prohibited
PCA anomaly = prohibited
target masks = prohibited
report layers = prohibited
post-result orbit selection = prohibited
post-result threshold changes = prohibited
global training = prohibited
app depth enablement = prohibited
```
