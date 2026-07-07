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
```

## Still open from D2

```text
D2.1 compatibility mode decision for legacy PCA
D2.2 corrected raw PCA scoring using whitened PC distance or reconstruction error
D2.4 fuller included/excluded band names where band names are available
D2.5 separate raw score from display stretch
D2.6 threshold object candidates from raw score rather than display-stretched score
D2.7 low-valid-fraction blocking
```

## Notes

This is a guardrail patch, not full D2 completion. It prevents degenerate feature channels from participating in PCA fit and makes the exclusion visible in QA.
