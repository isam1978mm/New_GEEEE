# SAR summary-stat reconciliation result

Status: closed / report-summary schema and formatting mismatch documented.

This document records a safe docs-only summary from a local comparison of the app SAR summary CSV against the D1C notebook radar summary CSV.

No CSV rows, SAR JSON bodies, image identifiers, raster payloads, NPY payloads, coordinates, or per-pixel values are included.

## Scope

App run:

```text
a11309bf-ed47-4bf5-bbf4-f755b904065c
```

Notebook/reference roots checked:

```text
D1C_NEW_IPYNB_REFERENCE_2026_06_10
new_ipynb_d1_20260615_local artifacts/report
```

Notebook summary selected by the local check:

```text
QA/SUMMARY_RADAR_..._DBONLY_LOCALDEM_v5.csv
```

App summary selected:

```text
QA/sar/sar_summary.csv
```

## Schema comparison

The app summary schema is:

```text
band_name
valid_count
nodata_count
nodata_fraction
min
max
mean
```

The notebook summary schema is:

```text
band
min
max
mean
nodata_px
```

Band-name mapping is:

```text
VV_dB -> VV_dB
VH_dB -> VH_dB
logRatio_dB -> logRatio_dB
incidence -> angle
```

## Mismatch classification

The prior SAR processing parity report marked summary rows as mismatched because its summary comparator checks only these fields:

```text
min
max
mean
nodata_count
```

The D1C notebook summary uses `nodata_px`, not `nodata_count`, so `nodata_count` appears blank on the notebook side even when both sides have zero nodata pixels.

The remaining numeric differences are tiny formatting/precision deltas from rounded CSV strings versus full-precision notebook CSV values.

Examples of safe aggregate deltas:

```text
VV_dB mean delta: approximately -1.2281494e-06
VH_dB mean delta: approximately -8.9794922e-07
logRatio_dB mean delta: approximately -2.8387451e-07
incidence/angle mean delta: approximately 3.6496582e-06
```

Min and max differences were within 1e-6 for all four inspected bands. Mean differences were within small report-formatting scale and do not indicate a raster/NPY value failure.

## Recomputed app NPY statistics

The app final NPY arrays existed for all inspected bands:

```text
VV_dB.npy
VH_dB.npy
logRatio_dB.npy
incidence.npy
```

Recomputed aggregate stats from those app NPY files matched the app CSV summary values at the expected rounded precision scale.

The underlying SAR raster and NPY parity had already passed for all four core SAR bands, so this summary mismatch is not treated as a final SAR value parity failure.

## Decision

```text
SAR summary-stat reconciliation: closed / report-summary schema and formatting mismatch
Underlying SAR raster/NPY parity: remains closed / passed
Recommended code cleanup: optional comparator normalization for nodata_px -> nodata_count and small rounded-summary tolerances
```

## Safety boundary

```text
No CSV rows were committed.
No SAR JSON bodies were committed.
No image identifiers were committed.
No raster or NPY payloads were committed.
No per-pixel values were committed.
Only safe aggregate schema names, field classifications, and aggregate numeric deltas were recorded.
No public downloads, HTTP table/array serving, or map overlays were enabled.
```
