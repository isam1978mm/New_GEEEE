# Plan D D2 Progress

## Date

2026-07-07

## Scope

Direct local patch for Phase D2 PCA anomaly scoring guardrails.

No private/local-only data was added.

## Completed in this patch

```text
D2.3 partial:
  - PCA excludes all-nodata feature channels before fitting.
  - PCA excludes near-constant feature channels before fitting.
  - PCA keeps the valid_mask support channel out of feature channels.
  - PCA reports included/excluded feature channels with reasons.
  - PCA QA records input_feature_channel_count, feature_channel_count, excluded_feature_channel_count, and pca_feature_policy.

D2.5 partial:
  - PCA now persists raw projected-magnitude scores separately as pca_anomaly_raw.npy.
  - Display anomaly TIF remains percentile-stretched to [0, 1].
  - PCA report and QA record raw_score_method, display_stretch_method, and raw_score_range.
```

## Still open from D2

```text
D2.1 compatibility mode decision for legacy PCA
D2.2 corrected raw PCA scoring using whitened PC distance or reconstruction error
D2.4 fuller included/excluded band names where band names are available
D2.5 downstream consumers still use display-stretched pca_anomaly.tif until D2.6
D2.6 threshold object candidates from raw score rather than display-stretched score
D2.7 low-valid-fraction blocking
```

## Notes

This is still not full D2 completion. Degenerate feature channels are excluded before PCA fit, and raw PCA projected-magnitude scores are now persisted separately from display-stretched anomaly values. Object extraction still needs D2.6 to threshold candidates from raw score rather than display-stretched score.
