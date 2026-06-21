# AI_READY remaining support families status

Status: blocked / source-capture required.

This document records the safe docs-only status for the AI_READY families that remain after AIREADY-S1 secret-layer parity passed.

No raster payloads, private reports, generated outputs, renamed outputs, or reference files are included in this document.

## Scope

This status covers the remaining AI_READY support families only:

```text
AIREADY-FR — Fraction rasters
AIREADY-MH — Metal Hardness
AIREADY-AN — Magnetic / EM anomaly
```

AIREADY-S1 secret layers are already closed separately and are not reopened here.

## Exact targets checked

```text
AI_READY_640_Fraction_Gold.tif
AI_READY_640_Fraction_Pottery.tif
AI_READY_640_Fraction_Carbon_Age.tif
AI_READY_640_Fraction_Silver_Lead.tif
AI_READY_640_Metal_Hardness.tif
AI_READY_640_Magnetic_Anomaly.tif
AI_READY_640_EM_Anomaly.tif
```

## Exact-name search result

```text
D1C reference search: 0 of 7 found
reference_manifest.json mentions: 0 of 7 found
app output search: 0 of 7 found
```

## Broad naming-drift search result

A broad search was run for:

```text
AI_READY|Fraction|Gold|Pottery|Carbon|Silver|Lead|Metal|Hardness|Magnetic|Anomaly|EM
```

The broad search did not find useful alternate notebook-named outputs for the remaining AI_READY families.

It found already-handled or non-equivalent artifacts, including:

```text
already handled:
  AI_READY_640_Secret_* secret-layer rasters
  AI_BEH_* internal rasters
  REPORT_640_Pottery_Report.tif
  DEM/DEM_GEO8 support outputs
  RADAR_* support outputs

not equivalent to the missing remaining AI_READY targets:
  focus_zone_ai_ready_window.npy
  ai_ready_support_stack.npy
  ai_ready_support_stack.tif
```

## Family decisions

```text
AIREADY-FR Fraction rasters:
  status: blocked / source-capture required
  reason: exact D1C references and exact app outputs are missing

AIREADY-MH Metal Hardness:
  status: blocked / source-recovery required
  reason: exact D1C reference and exact app output are missing

AIREADY-AN Magnetic / EM anomaly:
  status: blocked / source-recovery required
  reason: exact D1C references and exact app outputs are missing
```

## Boundary

```text
Do not claim all AIREADY parity complete from AIREADY-S1 alone.
Do not alias ai_ready_support_stack.* as the missing Fraction/MH/AN outputs.
Do not alias focus_zone_ai_ready_window.npy as any missing Fraction/MH/AN output.
Do not use AI_BEH_* rasters as AI_READY remaining support-family equivalents.
Do not fabricate, synthesize, or rename outputs to satisfy these gates.
No public downloads, HTTP raster/array serving, or map overlays were enabled.
No raster/NPY payloads were committed.
```

## Decision

```text
AI_READY remaining support families: blocked / source-capture required
```

## Next recommended gate

```text
Choose the next source-recovery or parity family explicitly.
Recommended candidates:
- D1D object-table outputs
- SAR/S1 remaining support, intermediate, and QA/provenance outputs outside S1-1 and filtered stack
```
