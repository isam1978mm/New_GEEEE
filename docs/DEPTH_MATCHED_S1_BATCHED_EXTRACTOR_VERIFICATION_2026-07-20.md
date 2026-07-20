# Depth Matched Sentinel-1 Batched Extractor Verification — 2026-07-20

Status: batched extractor software gate passed; live batched execution is permitted.

This record covers software verification and the no-network dry run only. It does not report feature values, establish a site effect, estimate depth, train a model, import calibration rows, or enable app depth output.

## Focused verification

Observed on Windows with Python 3.13.5:

```text
batched extractor tests = 7 passed
original extractor tests = 13 passed
C1 redaction-risk tests = 3 passed
full unit suite = 1004 passed
failures = 0
warnings = 4 non-blocking
```

The warnings were the existing NumPy entropy warnings, the existing rasterio non-georeferenced test warning, and the pytest cache-write warning.

## Batched dry-run result

```text
status = matched_s1_feature_extraction_dry_run_ready
batching_enabled = true
batch_size = 10
planned_batch_count = 17
executed_batch_count = 0
manifest_pre_count = 80
manifest_post_count = 82
transition_rows_excluded = 5
expected_statistic_count = 6480
query_executed = false
private_output_written = false
```

Privacy and release flags remained false:

```text
coordinates_printed
geometry_printed
private_paths_printed
image_ids_printed
feature_values_printed
scientific_validation_run
training_started
app_depth_enabled
```

## Decision

```text
batched_extractor_software_verified = true
batched_dry_run_passed = true
live_batched_execution_permitted = true
scientific_validation_run = false
app_depth_enabled = false
```

## Next permitted step

Run the batched extractor with `--execute`, the existing private site polygon, reviewed background polygon, frozen exact-match manifest, private output path, and batch size 10.

A complete execution should report 17 executed batches, 80 extracted clean-pre rows, 82 extracted clean-post rows, zero missing images, zero missing statistics, and a private output file. Any failure must remain aggregate-only and must not expose image identities, coordinates, feature values, or private paths.

## Checklist

- [x] Verify seven batching tests.
- [x] Re-verify thirteen original extractor tests.
- [x] Verify C1 privacy tests.
- [x] Verify complete unit suite.
- [x] Run batched no-network dry run.
- [ ] Execute seventeen live batches.
- [ ] Confirm all 162 rows are complete.
- [ ] Assess feature completeness before any effect analysis.
