# TAMUCC Sentinel-1 Common-Incidence-Support Assessment

Status: completed; focused tests and private execution passed.

## Purpose

The temporal-block assessment found mixed robustness and weak incidence overlap
across many block comparisons. This final TAMUCC whole-site feasibility screen
removes that extrapolation problem by retaining only acquisitions inside the
inclusive incidence range shared by the full pre and post periods.

## Method

1. Read usable pre and post rows from the private matched-feature output.
2. Find the common range of the site-minus-background incidence-angle median.
3. Keep only rows inside that shared range.
4. Require at least eight retained acquisitions in each period.
5. For each radar-feature median:
   - fit the incidence relationship using the restricted pre rows;
   - calculate pre and post residuals;
   - compare residual medians;
   - compare the direction with the full-period adjusted result.
6. Report retained-count categories and feature-direction categories to the
   console. Numeric ranges, slopes, and shifts remain private.

## Interpretation

This is a descriptive support-restriction check. It cannot establish causation,
target detection, or depth.

A radar direction that survives common-support restriction is less likely to be
an artifact of comparing non-overlapping incidence conditions. It is still only a
whole-site feasibility observation.

## Files

```text
scripts/assess_depth_s1_common_incidence_support.py
tests/unit/test_depth_s1_common_incidence_support.py
```

## Dry run

```powershell
python .\scripts\assess_depth_s1_common_incidence_support.py `
  --input "<PRIVATE_DEPTH_ROOT>\tamucc_matched_s1_features.json" `
  --output "<PRIVATE_DEPTH_ROOT>\tamucc_common_incidence_support.json"
```

## Execution

```powershell
python .\scripts\assess_depth_s1_common_incidence_support.py `
  --input "<PRIVATE_DEPTH_ROOT>\tamucc_matched_s1_features.json" `
  --output "<PRIVATE_DEPTH_ROOT>\tamucc_common_incidence_support.json" `
  --execute
```

## Decision after this step

This is the final TAMUCC feasibility check.

- Consistent VH/VV directions with adequate retained rows: retain TAMUCC as
  limited whole-site change evidence.
- Direction reversals or poor retained support: reject TAMUCC as a useful
  Sentinel-1 feasibility reference.

Neither result closes Depth Blocker 2. The workstream must then return to obtaining
contract-ready target-level depths, uncertainty, confirmed negatives, and
independent calibration groups.
## Observed result

The common-incidence restriction retained 64 of 80 usable pre-construction
acquisitions and 77 of 81 usable post-construction acquisitions.

No radar-feature direction changed after restriction to common incidence support.
The VH backscatter difference retained a moderate decrease category. The VV,
polarization-ratio, and VV-minus-VH changes remained small.

Final decision: retain TAMUCC only as limited whole-site Sentinel-1 change evidence.
Do not use it as a known-depth calibration pack, target detector, confirmed-negative
source, scientific validation result, or app depth-enablement basis.
