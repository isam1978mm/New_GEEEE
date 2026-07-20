# Depth Matched Sentinel-1 Feature Extraction Plan

Status: implementation planned on `main` after the exact site–background acquisition-match gate passed.

## Purpose

The reviewed controlled site and south-background polygon have 80 exact shared clean-pre Sentinel-1 images and 82 exact shared clean-post images. The private match manifest freezes those image identities.

The next slice extracts the same neutral Sentinel-1 GRD summary features from the site and background for every frozen image. This is an exploratory feasibility dataset only.

This slice does not estimate depth, classify targets, prove a buried-feature effect, train a model, import calibration records, expose coordinates or image identities in console output, or enable app depth output.

## Inputs

All inputs remain outside Git:

```text
private site Polygon
private reviewed background Polygon
private exact-match manifest
private detailed feature output
```

The manifest must use:

```text
schema_version = depth_s1_site_background_match_v1
status = site_background_acquisition_match_ready
matched_pre = non-empty
matched_post = non-empty
matched_transition_excluded = provenance only
```

Only `matched_pre` and `matched_post` are analyzed. The transition rows are counted and excluded.

## Exact acquisition contract

The extractor must preserve the frozen manifest contract:

```text
collection = COPERNICUS/S1_GRD
instrument_mode = IW
polarisations = VV and VH
resolution_meters = 10
platform = A
orbit_pass = ASCENDING
relative_orbit = 107
clean_pre_end_exclusive = 2020-02-01
clean_post_start = 2020-04-01
```

It loads each image by exact manifest identity. It does not issue a new date-window selection.

## First feature family

The first screen uses five neutral pixel-level bands:

```text
vv_db = Sentinel-1 VV band
vh_db = Sentinel-1 VH band
incidence_deg = Sentinel-1 angle band
vv_minus_vh_db = VV - VH
vh_to_vv_linear_ratio = 10 ^ ((VH - VV) / 10)
```

These are measurements or deterministic transforms. None is a depth measurement.

For every feature and polygon, the extractor records:

```text
p25
median
p75
valid_pixel_count
```

The median is the primary robust location summary. The interquartile range can later help identify unstable or mixed windows. Pixel counts are quality metadata, not physical evidence.

The 10 m value is collection pixel spacing. It must not be described as 10 m independent spatial resolution.

## Private row contract

One private row is written for each exact clean-pre or clean-post image. Each row contains:

```text
period
image_id
timestamp
site feature summaries
background feature summaries
site-minus-background differences for numeric summaries
```

The private output also records the selection contract and the excluded transition-row count.

The detailed output:

- remains outside Git;
- may contain exact image identities;
- contains no coordinates or geometry;
- is not an app artifact;
- is not a calibration pack;
- is not a scientific conclusion.

## Console contract

Console output remains aggregate-only:

```text
status
manifest_pre_count
manifest_post_count
transition_rows_excluded
extracted_pre_count
extracted_post_count
feature_names
expected_statistic_count
missing_statistic_count
all_rows_complete
query_executed
private_output_written
```

Privacy and release fields remain:

```text
coordinates_printed = false
geometry_printed = false
private_paths_printed = false
image_ids_printed = false
feature_values_printed = false
scientific_validation_run = false
training_started = false
app_depth_enabled = false
```

## Quality decisions

Executed with complete rows:

```text
matched_s1_feature_extraction_complete
```

Executed with one or more missing required statistics:

```text
matched_s1_feature_extraction_incomplete
```

A complete extraction means only that the private per-image feature table was produced. It does not mean the site differs from the background.

## Implementation boundaries

The utility will:

1. run as a no-network dry run unless `--execute` is supplied;
2. require all paths to remain outside the repository;
3. validate and deduplicate manifest image identities;
4. reject overlap between pre and post image sets;
5. exclude transition rows from analysis;
6. sanitize GeoJSON properties;
7. load exact Sentinel-1 images by identity;
8. compute the same features and reducers for both polygons;
9. write detailed values only to a private output;
10. print no identities, values, geometry, coordinates, or paths.

The utility will not use:

- classifier scores or classes;
- target masks or generated labels;
- PCA or downstream report layers;
- notebook depth labels;
- coherence, because `COPERNICUS/S1_GRD` does not directly provide interferometric coherence;
- numerical depth claims.

## Focused tests

Tests must cover:

- repository-local input/output rejection;
- wrong manifest schema or status rejection;
- empty clean-pre or clean-post rejection;
- duplicate and overlapping image identities;
- transition rows excluded;
- no-network/no-write dry run;
- exact private-row construction from injected synthetic query results;
- missing-statistic incomplete decision;
- private output isolation;
- aggregate-only privacy-safe result.

## Completion gate

```text
targeted extractor tests pass
C1 redaction-risk tests pass
full unit suite passes
```

Only after the software gate passes may the real private extraction run.

## Checklist

- [x] Qualify clean site coverage.
- [x] Review and select a background polygon.
- [x] Freeze exact matched image identities privately.
- [x] Define the first neutral feature family.
- [x] Define private detailed-output boundaries.
- [ ] Implement the manifest-driven extractor.
- [ ] Add focused tests.
- [ ] Run targeted and full verification.
- [ ] Execute private feature extraction.
- [ ] Assess feature completeness before any effect analysis.
