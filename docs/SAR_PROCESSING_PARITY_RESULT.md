# SAR processing parity result

Status: core SAR band processing parity passed; intermediate first-divergence capture remains open.

This document records a safe docs-only summary from the local-only SAR processing parity report.

No SAR JSON bodies, CSV rows, image identifiers, raster payloads, NPY payloads, private report files, coordinate-bearing values, or per-pixel values are included.

## Scope

The local-only SAR processing parity report was run for the app run:

```text
a11309bf-ed47-4bf5-bbf4-f755b904065c
```

The report used notebook/reference roots and the prior SAR source-selection report as input.

## Report-level summary

```text
report_type: sar_processing_parity
artifact_class: FILESYSTEM_ONLY
local_only: true
app_file_count: 11
notebook_file_count: 11
row_count: 122
```

Status counts:

```text
MATCH: 54
DIAGNOSTIC: 57
MISMATCH: 4
MISSING_APP_INTERMEDIATE: 4
FIRST_DIVERGENCE_BLOCKED: 1
DOWNSTREAM_DIAGNOSTIC: 1
FOUND: 1
```

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

## Summary-stat mismatch note

The SAR summary-stat rows remain mismatched:

```text
sar_summary_VV_dB: MISMATCH
sar_summary_VH_dB: MISMATCH
sar_summary_logRatio_dB: MISMATCH
sar_summary_incidence: MISMATCH
likely_cause: SUMMARY_STATS_MISMATCH
```

Because the underlying raster and NPY checks passed at 100 percent matching, these summary-stat mismatches are not treated as core SAR band value failures in this closeout. They remain report-summary reconciliation items.

## Diagnostic rows

The report contains diagnostic rows for edge/interior deltas, nodata edge overlap, angle delta distribution, residual distributions, sign balance, regression residuals, and F23 context checks.

These are diagnostic-only rows and are not treated as failures of the core SAR raster/NPY parity pass.

The diagnostic rows consistently point to low-amplitude residual/profile analysis and recommend not changing SAR formulas or tolerances based on these diagnostics alone.

## Intermediate first-divergence status

First-divergence staging is not closed because matching app intermediate stages are missing:

```text
intermediate_per_image_products_db: MISSING_APP_INTERMEDIATE
intermediate_pair_median: MISSING_APP_INTERMEDIATE
intermediate_final_median_pre_rtc: MISSING_APP_INTERMEDIATE
intermediate_post_sample_pre_rtc: MISSING_APP_INTERMEDIATE
first_divergence_stage: FIRST_DIVERGENCE_BLOCKED
```

Recommended action from the report:

```text
Export matching app intermediate stages locally before claiming a first divergence stage.
```

## Radar support stack status

The downstream radar support stack remains diagnostic:

```text
radar_linear_support_stack: DOWNSTREAM_DIAGNOSTIC
raw_matching_percent: 25.0
common_valid_matching_percent: 25.0
likely_cause: DOWNSTREAM_FROM_SAR_BANDS
```

This is not closed by the core SAR band parity pass. Stack assembly/contract should be handled as a separate downstream gate.

## Decision

```text
SAR core band processing parity: closed / passed
SAR summary-stat reconciliation: open / report-summary issue
SAR first-divergence intermediate staging: open / app intermediates missing
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
Export or locate matching app intermediate stages for:
- per_image_products_db
- pair_median
- final_median_pre_rtc
- post_sample_pre_rtc

Then rerun the SAR processing parity report to identify the first divergence stage.
```
