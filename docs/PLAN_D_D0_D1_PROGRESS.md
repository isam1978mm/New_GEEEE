# Plan D D0-D1 Progress

## Date

2026-07-07

## Scope of this progress note

Direct commits on `main` only.

No private/local-only data was added.

## Completed so far

```text
D0 tests added/updated:
  - classifier ignores invalid pixels where valid_mask is 0
  - cluster dominant_class_id uses most-common class instead of alphabetical first
  - PCA excludes binary valid_mask channel and keeps invalid pixels nodata
  - hypercube invalid source pixels stay invalid through normalization
  - hypercube valid_mask policy is explicit and tested as all_feature_channels_finite
  - object extraction ignores high anomaly pixels where valid_mask is 0
  - focus hard classifier value extraction excludes nodata sentinels
  - SAR local RTC rejects pixels where angle is nodata

D1 behavior patched:
  - app/pipeline/stages/classifier.py now computes object features through valid_mask-aware helper
  - app/pipeline/stages/classifier.py now uses most-common cluster dominant_class_id with deterministic tie-break
  - app/pipeline/stages_experimental/run.py now uses the same valid_mask-aware feature helper
  - app/pipeline/stages/pca_anomaly.py now auto-detects a binary final valid_mask channel, excludes it from PCA feature channels, fits only valid pixels, and writes nodata for invalid anomaly pixels
  - PCA QA now records feature_channel_count, valid_pixel_count, used_valid_mask_channel, and valid_mask_policy
  - app/pipeline/stages/hypercube.py no longer converts invalid source pixels to 0.0 before normalization
  - app/pipeline/stages/hypercube.py now persists invalid feature pixels as nodata and sets valid_mask from all feature channels finite
  - Hypercube StageResult metadata now records valid_mask_policy
  - app/pipeline/stages/object_extract.py now thresholds only valid hypercube pixels and can exclude nodata anomaly pixels from percentile calculations
  - ObjectExtract StageResult metadata now records valid_pixel_count and valid_mask_policy
  - app/pipeline/stages/focus_mask.py _hard_get_vals now excludes nodata sentinel values
  - app/pipeline/stages/sar_rtc.py local RTC valid mask now requires finite non-nodata angle
```

## Commits

```text
18822c7 fix: make classifier use valid mask for features
ac46928 test: cover Plan D classifier guard behavior
fc02ee2 fix: exclude valid mask from PCA feature channels
6567803 test: cover Plan D PCA valid-mask guard
5f1b060 test: fix Plan D PCA guard syntax
afb9cdc fix: make experimental classifier CLI use valid mask
b0a7e34 fix: keep hypercube invalid pixels out of normalization
bf85761 test: update hypercube invalid-pixel policy
2b9fa3c fix: gate object extraction by valid mask
894c1a2 test: cover object extraction valid-mask gate
```

## Local verification checklist

```text
Run before push:
  - pytest tests/unit/test_focus_mask.py::test_hard_get_vals_excludes_nodata_sentinel tests/unit/test_sar_rtc.py::test_apply_local_dem_rtc_rejects_pixels_where_angle_is_nodata -q
  - pytest tests/unit/test_focus_mask.py tests/unit/test_sar_rtc.py -q

D0/D1 remaining after this local patch:
  - none known, pending local pytest pass
```

## Notes

The root hypercube invalid-pixel normalization blocker is now patched. Object extraction is now valid-mask gated. The final local D1 patch covers focus sentinel filtering and SAR angle nodata handling.
