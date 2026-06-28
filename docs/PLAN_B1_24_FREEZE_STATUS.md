# Plan B1 Item #24 — Freeze / Parity Status

Status: Partial — notebook references are frozen, but app logic does not match notebook output on the same export.

## Scope

```text
Plan B item: #24 Hard classifier
Canonical notebook cell: cell index 128 in notebooks/new.ipynb
Notebook output family:
  AI_HARD_TYPE_CLASSIFIER_CORE9.csv
  AI_HARD_TYPE_CLASSIFIER_CORE9.json
  AI_HARD_TYPE_CLASSIFIER_CORE9.txt
App owner stage: FocusMaskStage
App source: app/pipeline/stages/focus_mask.py
Privacy: FILESYSTEM_ONLY
```

## Completed

```text
[x] notebook output files located in downloaded notebook export
[x] notebook output files copied to private frozen-reference folder
[x] notebook reference hashes recorded
[x] app source owner identified as FocusMaskStage
[x] same-export raster inputs located
[x] same-export raster metadata checked
[x] same-export app-logic harness run
```

## Frozen notebook hashes

```text
AI_HARD_TYPE_CLASSIFIER_CORE9.csv
30FA7CFC954A26993C4E11FCCB0B1C0F2A254F93DCFA03952D6DAF330326A487

AI_HARD_TYPE_CLASSIFIER_CORE9.json
66BD86531AE92D9B6AFCE98EA71F7BD3382999D86E656B861DA75A7A5EFEBBCF

AI_HARD_TYPE_CLASSIFIER_CORE9.txt
250109618456D7E3B16D7402EC8B99D46E70A55CBBA9D9E058FCEE7FAFB4D2F5
```

## Initial app-run comparison result

The first comparison used an existing app run under `data/runs` and the downloaded notebook export. That comparison was invalid for parity because the manifests differed.

```text
Notebook RUN_MANIFEST hash:
70FB3BCF06483F1CACBCAD49659F6B4039207C959087CFD4DA6E3989488EB3AC

App RUN_MANIFEST hash:
1AC1C96CB13919E33C9306B0AFB26652142F0A83DC4A30A4783E89A01A59C962

Notebook grid_manifest hash:
C76FF3AC8FB18983FF5BBCD6E8C973DFC452D3EB8517051F2E9D3312671E799F

App grid_manifest hash:
9250EB3203D3ABA86C769443A573A7BFC2C86796C6C05C4F15E4F161354A16DB
```

Decision: do not use that run-to-run mismatch as algorithm proof.

## Same-export inputs

The downloaded notebook export contains the raster inputs needed to run the app classifier logic on the same exported notebook grid:

```text
FOCUS_MASK_17m_inside_640.tif
REPORT_640_FINAL_Zero_Point_Targets.tif
REPORT_640_Mass_Report.tif
REPORT_640_Pottery_Report.tif
AI_READY_640_Secret_Gold_Halo.tif
AI_READY_640_Secret_Silver_Oxide.tif
AI_READY_640_Secret_Tunnel_Ceiling.tif
AI_READY_640_Secret_Thermal_Inertia.tif
AI_READY_640_Secret_Chemical_Protector.tif
AI_READY_640_Secret_Hidden_Doors.tif
```

All checked rasters were 640 x 640, single-band, EPSG:32637, and shared the same transform.

## Same-export app logic result

The same-export harness ran `build_hard_type_classifier_products(...)` using the notebook export rasters and compared the app record against the frozen notebook CSV.

```text
common_column_count: 29
notebook_column_count: 29
app_record_key_count: 33
columns_only_in_notebook: NONE
columns_only_in_app: Far_Ring_Pixels, Near_Ring_Pixels, Source_Cell, Wide_Ring_Pixels
shared_value_mismatch_count: 22
shared_values_match: False
```

Mismatched shared fields:

```text
Core_Mask_Source
Primary_Class
Void_Type
Final_Confidence
Void_Probability
Metal_Probability
Fill_Probability
Entrance_Probability
Surface_Exclusion
Directionality_Strength
Entrance_Score
Shaft_Score
Chamber_Score
Drain_Void_Score
Gold_Like_Score
Silver_Like_Score
Dense_Metal_Score
Coins_Score
Ingots_Score
Statues_Score
Pottery_Treasures_Score
General_Antiquities_Score
```

## Decision

```text
#24 remains Partial.
Reason: notebook references are frozen, and same-export inputs are available, but app classifier logic does not match the notebook result.
```

This is not only a schema issue. The app currently has extra output fields and a wrapped JSON shape, but the same-export comparison also shows 22 shared-value mismatches.

## Next work item

Patch the app implementation to match notebook cell index 128 formulas and output contract.

Required order:

```text
[ ] compare notebook cell 128 formula-by-formula against build_hard_type_classifier_products
[ ] patch algorithm only where formulas/thresholds differ
[ ] patch CSV output to notebook column contract
[ ] patch JSON output to notebook flat contract or emit a notebook-compatible alias
[ ] patch TXT output to notebook text contract or emit a notebook-compatible alias
[ ] rerun same-export harness
[ ] mark Full only if same-export comparison passes
```

## Privacy note

This public status document records file names, hashes, schema-level findings, and mismatch field names only. It does not include raw rows, coordinates, geometries, private raster values, or private output contents.
