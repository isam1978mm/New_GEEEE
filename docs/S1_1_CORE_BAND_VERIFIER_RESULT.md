# S1-1 core-band verifier result

Status: passed.

This document records the safe docs-only result for S1-1 core-band Sentinel-1 ASC/DESC filtered real app-vs-reference parity.

No raster payloads, NPY payloads, verifier report payloads, or reference files are included in this document.

## Verifier

Current SAR ASC/DESC support verifier used:

```text
app.pipeline.parity.sar_asc_desc_verify.verify_sar_asc_desc_support_stack_parity
```

Verifier run id:

```text
s1-1-d1c-a11309bf-final
```

## Final summary

```text
overall_status: passed
expected_count: 8
compared_count: 8
counts_by_status:
  passed: 8
raster_value_comparison_available: true
npy_outputs_passed: true
```

All compared outputs reported zero value differences:

```text
max_abs_diff: 0.0
mean_abs_diff: 0.0
```

## Outputs covered

```text
GEOTIFF_RADAR_BANDS/S1_ASC_VV_Filtered_640.tif: passed
GEOTIFF_RADAR_BANDS/S1_ASC_VH_Filtered_640.tif: passed
GEOTIFF_RADAR_BANDS/S1_DESC_VV_Filtered_640.tif: passed
GEOTIFF_RADAR_BANDS/S1_DESC_VH_Filtered_640.tif: passed
NPY_RADAR_BANDS/S1_ASC_VV_Filtered_640.npy: passed
NPY_RADAR_BANDS/S1_ASC_VH_Filtered_640.npy: passed
NPY_RADAR_BANDS/S1_DESC_VV_Filtered_640.npy: passed
NPY_RADAR_BANDS/S1_DESC_VH_Filtered_640.npy: passed
```

## Reference gates completed

```text
D2 reference bundle validation: passed
S1-1 reference GeoTIFF count: 4
S1-1 reference NPY count: 4
reference manifest mentions: 8 of 8
safe reference metadata inspected: true
TIF/NPY pair shape and dtype consistency: passed
```

Safe reference metadata summary:

```text
GeoTIFF CRS: EPSG:32637
GeoTIFF size: 640 x 640
GeoTIFF band count: 1
GeoTIFF dtype: float32
GeoTIFF nodata: -9999.0
NPY shape: [640, 640]
NPY dtype: float32
finite values per output: 409600
nan count per output: 0
nodata count per output: 0
```

## App/source boundary

The app-side candidate contained the eight required S1-1 files plus a S1 filtered export manifest.

The source/export contract records the notebook-compatible S1 filtered support path:

```text
collection: COPERNICUS/S1_GRD
date range: 2022-01-01 to 2026-03-01
mode: IW
polarizations: VV and VH
orbit passes: ASCENDING and DESCENDING
source selection: newest image per pass by descending system:time_start
filter: focal_mean(radius=1.5, kernelType='circle', units='pixels')
per-band outputs: GeoTIFF and NPY
```

Important boundary:

```text
S1-1 is limited to the eight per-band ASC/DESC filtered core-band files.
S1_FILTERED_LAYERS_STACK_640.npy remains a separate stack/tensor gate unless explicitly closed separately.
Final app RTC outputs are not treated as S1-1 equivalents.
RADAR_*_640_app aliases are not treated as S1-1 equivalents.
No public downloads, HTTP raster/array serving, or map overlays were enabled.
No raster/NPY payloads were committed.
No verifier tolerance relaxation was used.
```

## Decision

```text
S1-1 core-band real app-vs-reference parity: closed / passed
```

## Next recommended gate

```text
Choose the next source-recovery or parity family explicitly.
Recommended candidates:
- S1 filtered stack tensor gate, if promoted separately
- PAN/optical component and stack parity
- AI_READY remaining support families
- D1D object-table outputs
```
