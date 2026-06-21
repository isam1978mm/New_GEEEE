# SAR processing parity result

Status: core SAR band processing parity passed; intermediate first-divergence stage identified.

This document records a safe docs-only summary from local-only SAR processing parity reports.

No SAR JSON bodies, CSV rows, image identifiers, raster payloads, NPY payloads, private report files, coordinate-bearing values, or per-pixel values are included.

## Scope

The SAR processing parity reports were run for the app run:

```text
a11309bf-ed47-4bf5-bbf4-f755b904065c
```

The reports used notebook/reference roots and the prior SAR source-selection report as input.

A first pass used the existing app intermediate manifest. A second pass used a newly exported local-only full app Cell 25 intermediate manifest.

## Source-selection prerequisite

The SAR source-selection gate had already classified the source identity as matched with a remaining processing-delta class:

```text
source_identity_classification: SOURCE_ID_MATCH_PROCESSING_DELTA_REMAINS
```

The processing-path mismatch was classified as a metadata-detail/documentation gap because notebook source cells contain the relevant processing terms, while the D1C metadata is less detailed than the app `processing_path` metadata.

## Core SAR band parity

The core SAR band raster and NPY comparisons passed for all four inspected bands:

```text
VV_dB raster: MATCH
VV_dB npy: MATCH
VH_dB raster: MATCH
VH_dB npy: MATCH
logRatio_dB raster: MATCH
logRatio_dB npy: MATCH
incidence raster: MATCH
incidence npy: MATCH
```

Safe aggregate metrics for the core band comparisons:

```text
raw_matching_percent: 100.0 for all 8 core raster/NPY checks
common_valid_matching_percent: 100.0 for all 8 core raster/NPY checks
mask_overlap_percent: 100.0 for all 8 core raster/NPY checks
recommended_next_action: No action required.
```

Mean-difference scale:

```text
VV_dB mean_diff: approximately 3.8124e-08
VH_dB mean_diff: approximately 2.5082e-08
logRatio_dB mean_diff: approximately 1.3039e-08
incidence mean_diff: approximately -2.794e-11
```

Decision for this slice:

```text
SAR core band processing parity: closed / passed
```

## Initial report summary

The initial processing report used the existing app intermediate manifest.

```text
report_type: sar_processing_parity
artifact_class: FILESYSTEM_ONLY
local_only: true
app_file_count: 11
notebook_file_count: 11
row_count: 122
```

Initial status counts:

```text
MATCH: 54
DIAGNOSTIC: 57
MISMATCH: 4
MISSING_APP_INTERMEDIATE: 4
FIRST_DIVERGENCE_BLOCKED: 1
DOWNSTREAM_DIAGNOSTIC: 1
FOUND: 1
```

At that stage, first-divergence localization was blocked because these app intermediates were missing:

```text
intermediate_per_image_products_db: MISSING_APP_INTERMEDIATE
intermediate_pair_median: MISSING_APP_INTERMEDIATE
intermediate_final_median_pre_rtc: MISSING_APP_INTERMEDIATE
intermediate_post_sample_pre_rtc: MISSING_APP_INTERMEDIATE
first_divergence_stage: FIRST_DIVERGENCE_BLOCKED
```

## Full app intermediate export

A local-only full app Cell 25 intermediate manifest was exported outside Git using the app run and live Cell 25 replay mode.

The exported manifest was used only as a local diagnostic input. The manifest and NPY payloads were not committed.

## Full-intermediate report summary

The processing report was rerun with the full app intermediate manifest.

```text
report_type: sar_processing_parity
app_run_id: a11309bf-ed47-4bf5-bbf4-f755b904065c
row_count: 122
```

Full-intermediate status counts:

```text
MATCH: 54
DIAGNOSTIC: 58
MISMATCH: 8
DOWNSTREAM_DIAGNOSTIC: 1
FOUND: 1
```

## Intermediate first-divergence result

The first divergent intermediate candidate is now identified:

```text
first_divergence_stage: DIAGNOSTIC
likely_cause: FIRST_DIVERGENCE_PER_IMAGE_FILTER
raw_matching_percent: 0.030566
common_valid_matching_percent: 0.030566
mean_diff: 0.3334584954269105
recommended_next_action: Treat per_image_products_db as the first divergent intermediate candidate before changing downstream SAR logic.
```

Intermediate stage checks from the full-intermediate report:

```text
intermediate_per_image_products_db:
  status: MISMATCH
  likely_cause: PER_IMAGE_PRODUCTS_DB_NUMERIC_DELTA
  raw_matching_percent: 0.030566
  common_valid_matching_percent: 0.030566
  mean_diff: 0.3334584954269105

intermediate_pair_median:
  status: MISMATCH
  likely_cause: PAIR_MEDIAN_NUMERIC_DELTA
  raw_matching_percent: 0.059419
  common_valid_matching_percent: 0.059419
  mean_diff: 0.2138574094841321

intermediate_final_median_pre_rtc:
  status: MISMATCH
  likely_cause: FINAL_MEDIAN_PRE_RTC_NUMERIC_DELTA
  raw_matching_percent: 0.064799
  common_valid_matching_percent: 0.064799
  mean_diff: 0.19426894253684696

intermediate_post_sample_pre_rtc:
  status: MISMATCH
  likely_cause: POST_SAMPLE_PRE_RTC_NUMERIC_DELTA
  raw_matching_percent: 0.064799
  common_valid_matching_percent: 0.064799
  mean_diff: 0.19426894253684696

intermediate_post_rtc:
  status: MATCH
  likely_cause: POST_RTC_MATCH
  raw_matching_percent: 100.0
  common_valid_matching_percent: 100.0
  mean_diff: 5.307706305757165e-07
```

Interpretation:

```text
The final post-RTC SAR outputs match, but earlier live-replayed app intermediates diverge from notebook intermediate references starting at per_image_products_db.
Treat per_image_products_db as the first divergence candidate.
Do not change downstream SAR stack logic based on this result alone.
```

## Summary-stat mismatch note

The SAR summary-stat rows remain mismatched:

```text
sar_summary_VV_dB: MISMATCH
sar_summary_VH_dB: MISMATCH
sar_summary_logRatio_dB: MISMATCH
sar_summary_incidence: MISMATCH
likely_cause: SUMMARY_STATS_MISMATCH
```

Because the underlying raster and NPY checks passed at 100 percent matching, these summary-stat mismatches are not treated as core SAR band value failures. They remain report-summary reconciliation items.

## Diagnostic rows

The report contains diagnostic rows for edge/interior deltas, nodata edge overlap, angle delta distribution, residual distributions, sign balance, regression residuals, and F23 context checks.

These are diagnostic-only rows and are not treated as failures of the core SAR raster/NPY parity pass.

The diagnostic rows consistently point to low-amplitude residual/profile analysis and recommend not changing SAR formulas or tolerances based on these diagnostics alone.

## Radar support stack status

The downstream radar support stack remains diagnostic:

```text
radar_linear_support_stack: DOWNSTREAM_DIAGNOSTIC
raw_matching_percent: 25.0
common_valid_matching_percent: 25.0
mean_diff: 5.588461368247964
likely_cause: DOWNSTREAM_FROM_SAR_BANDS
```

This is not closed by the core SAR band parity pass. Stack assembly/contract should be handled as a separate downstream gate.

## Decision

```text
SAR core band processing parity: closed / passed
SAR source-selection identity: closed / matched
SAR processing-path metadata: notebook-source-supported; D1C metadata less detailed
SAR first-divergence localization: closed / first candidate identified at per_image_products_db
SAR summary-stat reconciliation: open / report-summary issue
Radar linear support stack parity: open / downstream diagnostic
```

## Safety boundary

```text
No SAR JSON bodies were committed.
No CSV rows were committed.
No image identifiers were committed.
No raster or NPY payloads were committed.
No per-pixel values were committed.
Only safe aggregate status counts, pass/fail classifications, and aggregate metrics were recorded.
No public downloads, HTTP table/array serving, or map overlays were enabled.
```

## Next recommended gate

```text
Investigate per_image_products_db as the first divergent intermediate candidate.
Do not change downstream stack assembly, SAR formulas, or tolerances before that targeted investigation.
```
