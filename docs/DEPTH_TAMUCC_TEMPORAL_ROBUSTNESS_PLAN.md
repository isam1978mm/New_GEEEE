# TAMUCC Sentinel-1 Temporal-Block Robustness Screen

Status: completed; focused tests and private execution passed.

## Purpose

The incidence-adjusted whole-period assessment found that all four radar-feature
directions remained after nuisance adjustment. This screen tests whether those
directions are distributed across time rather than being driven by a small number
of unusual dates.

## Method

1. Sort usable pre-construction acquisitions by time.
2. Split them into four chronological blocks.
3. Sort usable post-construction acquisitions by time.
4. Split them into four chronological blocks.
5. For each of the sixteen pre/post block combinations and each radar feature:
   - fit the incidence relationship using that pre block;
   - calculate pre and post residuals;
   - compare the median residuals;
   - record direction, IQR-scaled magnitude, and incidence-range overlap.
6. Report the dominant direction and its consistency across all sixteen
   comparisons.
7. Also report consistency among comparisons where at least 75% of post incidence
   values lie within the corresponding pre-block incidence range.

## Interpretation

This is a descriptive sensitivity check.

```text
all_blocks_consistent
at_least_75_percent_consistent
at_least_50_percent_consistent
under_50_percent_consistent
```

A consistent result supports continued whole-site feasibility work. It does not
establish causation, target detection, or depth calibration.

## Files

```text
scripts/assess_depth_s1_temporal_robustness.py
tests/unit/test_depth_s1_temporal_robustness.py
```

## Dry run

```powershell
python .\scripts\assess_depth_s1_temporal_robustness.py `
  --input "<PRIVATE_DEPTH_ROOT>\tamucc_matched_s1_features.json" `
  --output "<PRIVATE_DEPTH_ROOT>\tamucc_temporal_robustness.json"
```

## Execution

```powershell
python .\scripts\assess_depth_s1_temporal_robustness.py `
  --input "<PRIVATE_DEPTH_ROOT>\tamucc_matched_s1_features.json" `
  --output "<PRIVATE_DEPTH_ROOT>\tamucc_temporal_robustness.json" `
  --execute
```

## Blocker status

Depth Blocker 2 remains open regardless of this result because target-level known
depths, uncertainties, confirmed negatives, and independent calibration groups are
still unavailable.
## Observed result

The VH and VV backscatter directions were fairly consistent across the temporal
block comparisons. The polarization-ratio and VV-minus-VH results were less stable.

Fewer than half of the block comparisons met the strong incidence-overlap
qualification, so the temporal-block result was not accepted as robust standalone
evidence. A full-period common-support restriction was required.
