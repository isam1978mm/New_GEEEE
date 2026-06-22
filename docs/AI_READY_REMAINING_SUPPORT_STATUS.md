# AI_READY support stack and remaining standalone target status

Status: corrected.

This document replaces the earlier incorrect blocked wording for the AI_READY support stack. The AI_READY support stack exists, has a private notebook reference, and the matching app run is byte-identical to that reference.

No raster payloads, NPY payloads, private reports, generated outputs, renamed outputs, coordinate-bearing paths, or reference files are included in this document.

## Corrected scope

There are two different AI_READY topics that must not be mixed:

```text
1. AI_READY support stack tensor
   artifact: ai_ready_support_stack.npy
   status: passed against private notebook reference

2. Planned standalone Fraction/MH/AN filenames
   artifacts: AI_READY_640_Fraction_*.tif, AI_READY_640_Metal_Hardness.tif,
              AI_READY_640_Magnetic_Anomaly.tif, AI_READY_640_EM_Anomaly.tif
   status: not the active support-stack parity target; exact standalone files were not found
```

AIREADY-S1 secret layers remain closed separately and are not reopened here.

## AI_READY support stack parity result

Artifact:

```text
ai_ready_support_stack.npy
```

Reference source:

```text
private notebook frozen reference under data/private_references
```

Matching app run:

```text
a11309bf-ed47-4bf5-bbf4-f755b904065c
```

Safe parity result:

```text
reference_exists: true
app_exists: true
reference_shape: [640, 640, 19]
app_shape: [640, 640, 19]
reference_dtype: float32
app_dtype: float32
hash_match: true
same_shape: true
same_dtype: true
same_values_exact: true
compared_count: 7782400
nan_count_ref: 0
nan_count_app: 0
max_abs_diff: 0.0
mean_abs_diff: 0.0
```

Nonmatching app candidate:

```text
e11d3280-a7b7-4c7c-a761-8b08ac9452f2
hash_match: false
max_abs_diff: 1.0
mean_abs_diff: 0.29361279566396
```

The nonmatching app candidate is not used for closeout.

## AI_READY support stack band list

The matching support stack is a 19-channel float32 HWC tensor.

```text
VV_dB
VH_dB
logRatio_dB
incidence
NDVI
NDWI
NDMI
NBR
IRONOX
IRON_SWIR
BSI
slope
aspect
curvature
TPI
TRI
roughness
TWI
lst
```

The stack is used by the focus-analysis stage as:

```text
analysis_source: ai_ready_support_stack
```

## TIF sidecar note

The app also contains:

```text
ai_ready_support_stack.tif
```

That file is not treated as the parity target because the inspected copy is a single-band, ungeoreferenced sidecar:

```text
count: 1
crs: None
nodata: null
```

The verified parity target is the NPY tensor only.

## Planned standalone targets checked

These exact standalone names were searched and were not found as standalone app/reference outputs in the searched D1C bundle/app roots:

```text
AI_READY_640_Fraction_Gold.tif
AI_READY_640_Fraction_Pottery.tif
AI_READY_640_Fraction_Carbon_Age.tif
AI_READY_640_Fraction_Silver_Lead.tif
AI_READY_640_Metal_Hardness.tif
AI_READY_640_Magnetic_Anomaly.tif
AI_READY_640_EM_Anomaly.tif
```

They are not the same target as `ai_ready_support_stack.npy`, and they are not channels in the 19-band support-stack band list.

## Hypercube note for EM/Magnetic anomaly

The app hypercube manifest records that:

```text
AI_READY_640_EM_Anomaly is sourced from DEM_GEO8_TIFS/DEM_640.tif in the patched hypercube context.
AI_READY_640_Magnetic_Anomaly remains unavailable in that manifest.
```

This is not a standalone Fraction/MH/AN verifier pass.

## Boundary

```text
Do not claim all AIREADY parity complete from AIREADY-S1 alone.
Do not alias the 19-channel ai_ready_support_stack.npy as the standalone Fraction/MH/AN files.
Do not alias focus_zone_ai_ready_window.npy as any standalone Fraction/MH/AN output.
Do not use AI_BEH_* rasters as AI_READY remaining support-family equivalents.
Do not use the nonmatching app run for AI_READY support-stack parity.
No fabricated, synthesized, or renamed outputs were used.
No public downloads, HTTP raster/array serving, or map overlays were enabled.
No raster/NPY payloads were committed.
```

## Decision

```text
AI_READY support stack parity: closed / passed
Standalone Fraction/MH/AN filenames: not active support-stack parity targets; no standalone verifier pass claimed
```

## Next recommended gate

```text
Choose the next source-recovery or parity family explicitly.
Recommended candidates:
- D1D object-table outputs
- SAR/S1 remaining support, intermediate, and QA/provenance outputs outside S1-1 and filtered stack
```
