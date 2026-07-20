# Depth Matched Sentinel-1 Feature Extraction Live Failure — 2026-07-20

Status: the no-network extractor dry run passed, but the first live Earth Engine feature query failed before any private feature output was written.

This is an execution failure only. It does not show that the site and background are incompatible, that the features are missing, that a signal is absent, or that depth can or cannot be estimated.

## Verified dry-run state

```text
status = matched_s1_feature_extraction_dry_run_ready
manifest_pre_count = 80
manifest_post_count = 82
transition_rows_excluded = 5
expected_statistic_count = 6480
exact_manifest_selection = true
query_executed = false
private_output_written = false
```

The private site polygon, reviewed background polygon, and frozen exact-image manifest therefore passed the local contract checks.

## Live failure

The owner then executed the live query and received:

```text
status = matched_s1_feature_extraction_failed
error = Earth Engine matched feature query failed
```

Privacy flags remained false for coordinates, geometry, paths, image identities, and feature values. The utility writes the private output only after all query rows return, so this failure produced no partial scientific dataset.

## Likely execution-scale cause

The first implementation submitted all 162 clean images in one Earth Engine computation graph. Each image requested two polygon reductions over five feature bands with percentile and count reducers. That one-shot request is a plausible execution-scale failure point, but the generic error does not prove the exact server-side cause.

The scientific contract must not be weakened to work around the error. The safe remedy is to submit the same exact images, polygons, masks, bands, reducers, and scale in small deterministic batches and combine the returned rows locally.

## Next permitted action

1. Add a batching wrapper around the existing exact-image query.
2. Keep the original private manifest and feature definitions unchanged.
3. Add focused tests for batch splitting, ordering, safe failure reporting, dry-run behavior, and complete private output.
4. Run the targeted, privacy, and full unit suites.
5. Retry the private extraction using the batched launcher.

## Boundaries

```text
scientific_validation_run = false
training_started = false
app_depth_enabled = false
depth_claim = none
```
