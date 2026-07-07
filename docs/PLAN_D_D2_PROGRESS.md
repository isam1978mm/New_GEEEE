# Plan D D2 Progress

## Date

2026-07-07

## Scope

Direct local patch for Phase D2 PCA anomaly scoring guardrails.

No private/local-only data was added.

## Completed in this patch

```text
D2.2:
  - PCA raw score now uses whitened projected PC distance.
  - PCA scales component scores by explained variance before distance calculation.
  - PCA report and QA expose raw_score_method=pca_whitened_projected_component_distance.

D2.3 partial:
  - PCA excludes all-nodata feature channels before fitting.
  - PCA excludes near-constant feature channels before fitting.
  - PCA keeps the valid_mask support channel out of feature channels.
  - PCA reports included/excluded feature channels with reasons.
  - PCA QA records input_feature_channel_count, feature_channel_count, excluded_feature_channel_count, and pca_feature_policy.

D2.5 partial:
  - PCA now persists raw whitened PC-distance scores separately as pca_anomaly_raw.npy.
  - Display anomaly TIF remains percentile-stretched to [0, 1].
  - PCA report and QA record raw_score_method, display_stretch_method, and raw_score_range.

D2.6 partial:
  - object_extract now prefers pca_anomaly_raw.npy for candidate thresholding when present.
  - object_extract falls back to display-stretched pca_anomaly.tif for legacy/manual inputs.
  - raw-score candidate thresholding uses a robust MAD threshold with midrange fallback instead of the display floor.
  - target summary and StageResult metadata record candidate score source and threshold policy.

D2.7:
  - PCA blocks low-valid-fraction scenes before fitting.
  - PCA report records valid_pixel_fraction and min_valid_pixel_fraction when a scene passes.

D2.4 partial:
  - PCA reads hypercube_band_order.csv when available.
  - PCA report and QA now expose included/excluded feature channel names.
  - Degenerate-channel exclusion reasons include band_name alongside channel_index.
```

## Still open from D2

```text
D2.1 compatibility mode decision for legacy PCA
D2.6 remaining: evaluate/tune robust raw-score threshold policy against frozen references when available
```

## Notes

This is still not full D2 completion. Degenerate feature channels are excluded before PCA fit, raw PCA whitened-distance scores are persisted separately from display-stretched anomaly values, object extraction now prefers raw PCA scores for candidate thresholding when available, and PCA now reports included/excluded feature band names where hypercube band-order metadata exists. Frozen-reference threshold tuning remains open when reference outputs become available.
