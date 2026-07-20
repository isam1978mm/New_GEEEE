# Depth Matched Sentinel-1 Reducer Combine Fix — 2026-07-20

Status: exact live-query construction bug identified and patched on `main`. Verification and rerun remain pending.

## Observed execution result

The exact-manifest dry run passed, but both the one-shot execution and the first 10-image batch failed before writing private feature output.

Observed safe console state:

```text
status = matched_s1_feature_extraction_failed
failed_batch = 1 of 17
private_output_written = false
coordinates_printed = false
image_ids_printed = false
feature_values_printed = false
app_depth_enabled = false
```

This was an execution-expression failure, not evidence that the private site, reviewed background, exact acquisition manifest, or Sentinel-1 coverage was invalid.

## Root cause

The feature extractor built the combined reducer using:

```python
percentile_reducer.combine(count_reducer, True)
```

The Earth Engine contract orders the arguments as:

```text
combine(reducer2, outputPrefix, sharedInputs)
```

Therefore the positional `True` was passed to `outputPrefix`, which requires a string, instead of to `sharedInputs`.

## Fix

The batched launcher now builds the reducer with explicit named arguments:

```python
percentile_reducer.combine(
    reducer2=count_reducer,
    outputPrefix="",
    sharedInputs=True,
)
```

The patch does not change:

- private site or background geometry;
- frozen image identities;
- clean-pre or clean-post membership;
- transition exclusion;
- Sentinel-1 bands;
- border/angle mask thresholds;
- feature formulas;
- percentile/count statistics;
- 10 m reduction scale;
- batching size or order;
- privacy boundaries;
- app depth status.

## Regression coverage

New focused tests lock:

1. `outputPrefix` as an empty string;
2. `sharedInputs=True` as the explicit third contract argument;
3. the batched launcher defaulting to the corrected query implementation.

## Required next step

```text
pull main
→ run the two reducer-contract tests
→ rerun existing batching and extractor tests
→ run the batched dry check
→ execute the 17 live batches
```

No scientific interpretation is permitted until the private extraction completes with all expected rows and statistics present.
