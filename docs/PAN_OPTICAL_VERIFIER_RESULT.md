# PAN/optical verifier result

Status: passed.

This document records the safe docs-only result for PAN/optical component and stack real app-vs-reference parity.

No raster payloads, NPY payloads, verifier report payloads, or reference files are included in this document.

## Canonical reference decision

The D1C bundle contains duplicate PAN component filenames in two folder families:

```text
legacy/misplaced component copies:
  GEOTIFF_RADAR_BANDS/PAN_LS_Panchromatic_640.tif
  GEOTIFF_RADAR_BANDS/PAN_S2_Panchromatic_10m_640.tif
  NPY_RADAR_BANDS/PAN_LS_Panchromatic_640.npy
  NPY_RADAR_BANDS/PAN_S2_Panchromatic_10m_640.npy

canonical optical component copies:
  OPT/PAN_TIFS_640/PAN_LS_Panchromatic_640.tif
  OPT/PAN_TIFS_640/PAN_S2_Panchromatic_10m_640.tif
  OPT/PAN_NPY_640/PAN_LS_Panchromatic_640.npy
  OPT/PAN_NPY_640/PAN_S2_Panchromatic_10m_640.npy
```

Duplicate metadata matches, but values differ. The canonical PAN component reference was selected from `OPT/PAN_*` because `PAN_LAYERS_STACK_640.npy` bands match the `OPT/PAN_NPY_640` component arrays exactly.

Stack composition decision:

```text
PAN_LAYERS_STACK_640.npy shape: [640, 640, 2]
stack band 0 equals OPT/PAN_NPY_640/PAN_LS_Panchromatic_640.npy
stack band 1 equals OPT/PAN_NPY_640/PAN_S2_Panchromatic_10m_640.npy
```

The legacy/misplaced `RADAR_BANDS` and `NPY_RADAR_BANDS` copies were not used for PAN parity.

## Verifiers

PAN component verifier:

```text
app.pipeline.parity.pan_components_verify.verify_pan_components_parity
```

PAN stack verifier:

```text
app.pipeline.parity.pan_stack_verify.verify_pan_stack_parity
```

Verifier run ids:

```text
pan-components-d1c-a11309bf-final
pan-stack-d1c-a11309bf-final
```

## PAN-1 component result

```text
overall_status: passed
expected_count: 4
compared_count: 4
counts_by_status:
  passed: 4
raster_value_comparison_available: true
npy_outputs_passed: true
```

Outputs covered:

```text
PAN_LS_Panchromatic_640.tif: passed
PAN_S2_Panchromatic_10m_640.tif: passed
PAN_LS_Panchromatic_640.npy: passed
PAN_S2_Panchromatic_10m_640.npy: passed
```

Value comparison summary:

```text
PAN_LS_Panchromatic_640.tif:
  max_abs_diff: 5.960464477539063e-08
  mean_abs_diff: 1.8605260265758262e-09

PAN_S2_Panchromatic_10m_640.tif:
  max_abs_diff: 0.0
  mean_abs_diff: 0.0

PAN_LS_Panchromatic_640.npy:
  max_abs_diff: 5.960464477539063e-08
  mean_abs_diff: 1.8605260265758262e-09

PAN_S2_Panchromatic_10m_640.npy:
  max_abs_diff: 0.0
  mean_abs_diff: 0.0
```

## PAN-2 stack result

```text
overall_status: passed
status: passed
output_name: PAN_LAYERS_STACK_640.npy
app_exists: true
reference_exists: true
shape_match: true
dtype_match: true
hash_match: false
runtime_output_verified: true
notebook_value_parity_verified: true
```

Value comparison summary:

```text
count_compared_values: 819200
count_nan_or_nodata_values: 0
max_abs_diff: 5.960464477539063e-08
mean_abs_diff: 9.302630132879131e-10
```

The stack hash did not match byte-for-byte, but array shape, dtype, and value parity passed within verifier tolerance.

## Safety boundary

```text
No raster/NPY payloads were committed.
No verifier report payloads were committed.
No public downloads, HTTP raster/array serving, or map overlays were enabled.
No verifier tolerance relaxation was used.
No legacy/misplaced RADAR_BANDS PAN copies were treated as canonical.
No final RTC or SAR/RADAR aliases were treated as PAN equivalents.
```

## Decision

```text
PAN/optical component and stack real app-vs-reference parity: closed / passed
```

## Next recommended gate

```text
Choose the next source-recovery or parity family explicitly.
Recommended candidates:
- AI_READY remaining support families
- D1D object-table outputs
- SAR/S1 remaining support, intermediate, and QA/provenance outputs outside S1-1 and filtered stack
```
