# Phase 2 Item #18 — DEM-Matched S2 Masks

Status: App-port / no exact notebook export.

## Canonical notebook cell

```text id="93lwpt"
cell 081:
  CLL 24 DEM-MATCHED AI MASKS 640
  time range: 2022-01-01 to 2026-02-28
  cloud threshold: CLOUDY_PIXEL_PERCENTAGE < 3
  selected bands: B1, B2, B3, B4, B5, B8, B11, B12
  output stack: AIX_2022_2026FEB_CLOUDLT3_DEM_MATCHED_MASKS_STACK_640.npy
```

## Notebook export availability

The downloaded notebook export did not contain exact references for:

```text id="fvutbv"
AIX_2022_2026FEB_CLOUDLT3_DEM_MATCHED_MASKS_STACK_640.npy
AIX_2022_2026FEB_CLOUDLT3_DEM_MATCHED_MASKS_STACK_640.tif
```

So Full exact-file parity is blocked.

## App validation

```text id="2bu2nu"
AIX_2022_2026FEB_CLOUDLT3_DEM_MATCHED_MASKS_STACK_640.npy:
  exists
  shape: 640x640x9
  dtype: float32
  per-band NPY outputs: present
  per-band TIF outputs: present
  stack-vs-band max delta: 0.0
```

Validated band order:

```text id="8e8sbb"
0. AIX_2022_2026FEB_CLOUDLT3_MaskVegetationRoots_Norm01
1. AIX_2022_2026FEB_CLOUDLT3_MaskWaterMoisture_Norm01
2. AIX_2022_2026FEB_CLOUDLT3_IndexIronOxide_Norm01
3. AIX_2022_2026FEB_CLOUDLT3_IndexFerricIron_Norm01
4. AIX_2022_2026FEB_CLOUDLT3_IndexClayThermal_Norm01
5. AIX_2022_2026FEB_CLOUDLT3_MaskCharcoalLead_Norm01
6. AIX_2022_2026FEB_CLOUDLT3_MaskQuartzBasalt_Norm01
7. AIX_2022_2026FEB_CLOUDLT3_MaskCarbonate_Norm01
8. AIX_2022_2026FEB_CLOUDLT3_ThermalTimeSeriesAnomaly_Norm01
```

## Decision

```text id="97kjcn"
No code patch.
Keep app implementation.
Do not mark Full exact-file parity unless exact notebook stack refs appear and private comparison passes.
```
