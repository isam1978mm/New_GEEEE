# Plan B1 Raw Notebook Export Source-Recovery Scan

## Date

2026-07-03

## Scope

After the strict frozen-reference audit found zero notebook references for the remaining B1 Partial tensor/stack items, a broader source-recovery scan was run outside the repo run directory.

Searched roots:

```text
C:\Users\isam7\Downloads
C:\Users\isam7\Downloads\Compressed
C:\Dev\New_GEE_PRIVATE
```

Expected reference names searched:

```text id="lm7wor"
NANO_GEOPHYSICS_STACK_640.npy
TREASURE_GEOPHYSICS_STACK_640.npy
RAD_S0_MASTER_STACK_640.npy
RAD_MASTER_CUBE_640.npy
GPHYS_MASTER_STACK_640.npy
MASTER_RTC_REFINED_STACK_640.npy
ARCH_TARGETS_STACK_640.npy
ULTIMATE_GPHYS_SCAN_640.npy
AUX_BONUS_FEATURES_STACK_640.npy
SIM_GEOPHYSICAL_STACK_640.npy
AIX_2022_2026_CLOUDLT3_EXTRA_TENSORS_STACK_640.npy
AI_FULL_52B_FLOAT32_640.npy
YOLOV11_RGB_640.npy
CNN_MULTI_24B_640.npy
SWINSEGFORMER_16B_640.npy
PCA_RGB_640.npy
AI_NEGATIVE_MASK_640.npy
YOLOV11_RGB_VISUAL.tif
```

## Result

```text id="uobb59"
total_hits: 0
```

No raw notebook/export reference files were found for #8, #9, #15, #17, or #29.

## Decision

No remaining B1 Partial item can be promoted to Full notebook numeric parity from the currently available local/private files.

The blocked items remain:

```text id="tn985m"
#8  Partial / no notebook reference found
#9  Partial / no notebook reference found
#15 Partial / no notebook reference found
#17 Partial / no notebook reference found
#29 Partial / no notebook reference found
```

This is not an app-output failure. The app outputs exist and prior app-output or stack-order proofs passed. Full notebook parity requires external action: supply exact frozen notebook exports or rerun the notebook/export process to create the missing reference files.

## Private report

```text id="fymum2"
C:\Dev\New_GEE_PRIVATE\FROZEN_NOTEBOOK_REFS\b1_frozen_reference_pass\comparison_reports\b1_raw_notebook_export_source_recovery_scan.json
```
