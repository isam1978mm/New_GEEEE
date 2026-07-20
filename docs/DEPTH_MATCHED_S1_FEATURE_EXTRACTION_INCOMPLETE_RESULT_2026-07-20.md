# Depth Matched Sentinel-1 Feature Extraction Incomplete Result — 2026-07-20

Status: the corrected batched Earth Engine extraction completed all planned requests and wrote the private feature table, but 30 required statistics were missing. The output remains incomplete and is not approved for effect analysis yet.

This result does not estimate depth, prove a site effect, classify a target, train a model, import calibration rows, or enable app depth output.

## Verified software state

Observed local verification:

```text
Earth Engine reducer contract tests = 2 passed
batched extractor tests = 7 passed
failures = 0
```

The reducer-combine argument correction was active during the live run.

## Live extraction result

Observed aggregate result:

```text
planned_batch_count = 17
executed_batch_count = 17
manifest_pre_count = 80
manifest_post_count = 82
extracted_pre_count = 80
extracted_post_count = 82
missing_image_count = 0
expected_statistic_count = 6480
missing_statistic_count = 30
all_rows_complete = false
private_output_written = true
status = matched_s1_feature_extraction_incomplete
```

All exact manifest images were processed. No image identity was missing. The incomplete status is caused only by missing required statistics inside one or more private rows.

## Interpretation boundary

The current evidence supports only:

```text
exact-image extraction executed successfully
private detailed output exists
30 required statistics require completeness diagnosis
```

It does not support:

```text
site differs from background
construction caused a signal change
buried-object evidence exists
depth can be estimated
```

Missing feature values must not be replaced with zero, averages, interpolation, or guessed values.

## Completeness audit

A private aggregate-only completeness audit was added. It reads the private feature output outside Git and reports counts by:

```text
period: pre or post
polygon side: site or background
feature
statistic
zero-valid-pixel occurrence
```

It prints no image IDs, coordinates, geometry, private paths, or feature values.

The audit distinguishes:

1. missing percentiles explained by a zero valid-pixel count after the existing mask;
2. missing statistics that remain unexplained and require further code or data investigation.

## Next permitted step

Run the focused completeness-audit tests, then run the aggregate-only audit against the private batched feature output. Do not begin site-effect analysis until the 30 missing statistics have been classified and an explicit exclusion or repair policy has been documented.

## Checklist

- [x] Correct Earth Engine reducer construction.
- [x] Execute all 17 batches.
- [x] Process all 80 clean-pre images.
- [x] Process all 82 clean-post images.
- [x] Write the private feature table.
- [x] Preserve aggregate-only console output.
- [x] Detect 30 missing required statistics.
- [x] Add a private completeness-audit utility.
- [x] Add focused audit tests.
- [ ] Run focused audit tests.
- [ ] Classify the 30 missing statistics.
- [ ] Define exclusion or repair policy without imputation.
- [ ] Reassess readiness for effect analysis.
