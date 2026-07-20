# Depth Site–Background Exact Acquisition Match Result — 2026-07-20

Status: exact Sentinel-1 metadata matching completed successfully for the reviewed controlled-site and south-background polygons.

This record confirms only that the same Sentinel-1 source images are available for the site and background during both clean analysis periods. It does not establish a buried-feature signal, a depth relationship, a calibration record, training readiness, or app-depth activation.

## Executed contract

```text
collection = COPERNICUS/S1_GRD
instrument_mode = IW
polarisations = VV and VH
resolution_meters = 10
platform = A
orbit_pass = ASCENDING
relative_orbit = 107
start_date = 2017-01-01
end_date_exclusive = 2023-01-01
clean_pre_end_exclusive = 2020-02-01
clean_post_start = 2020-04-01
background = visually reviewed south candidate
```

All site and background geometry remained outside Git.

## Observed aggregate result

```text
status = site_background_match_completed
query_executed = true
match_decision = site_background_acquisition_match_ready
site_background_exact_match_support = true

site_acquisition_count = 167
background_acquisition_count = 167

site_pre_count = 80
background_pre_count = 80
matched_pre_count = 80
site_pre_unmatched_count = 0
background_pre_unmatched_count = 0
exact_pre_match_support = true

site_transition_count = 5
background_transition_count = 5
matched_transition_count = 5

site_post_count = 82
background_post_count = 82
matched_post_count = 82
site_post_unmatched_count = 0
background_post_unmatched_count = 0
exact_post_match_support = true
```

## Private outputs

```text
aggregate_output_written = true
private_manifest_written = true
private_manifest_contains_image_ids = true
coordinates_printed = false
geometry_printed = false
private_paths_printed = false
image_ids_printed = false
```

The private manifest freezes the exact matched Sentinel-1 image identities and timestamps. It remains outside Git and must not be pasted into repository documentation or console logs.

## Decision

```text
exact_source_image_matching_gate = passed
clean_pre_matched_images = 80
clean_post_matched_images = 82
unmatched_images = 0
matched_feature_extraction_permitted = true
scientific_signal_validation_run = false
training_started = false
app_depth_enabled = false
```

A passing match removes image-availability mismatch as a confounder. It does not prove that any extracted feature will distinguish the site from the background.

## Next permitted slice

Define and implement a private, manifest-driven feature extractor that:

1. uses only the frozen matched image identities;
2. excludes the five transition images from analysis;
3. computes the same simple Sentinel-1 GRD summary features for the site and background on every image;
4. writes detailed per-image values only outside Git;
5. reports aggregate completeness and privacy metadata to the console;
6. performs no depth estimate, classification, model training, or app activation.

## Checklist

- [x] Select and visually review a background candidate.
- [x] Create the canonical private background polygon.
- [x] Pass the no-network matcher dry run.
- [x] Execute the exact Sentinel-1 metadata match.
- [x] Confirm all 80 clean-pre images match exactly.
- [x] Confirm all 82 clean-post images match exactly.
- [x] Freeze the matched-image manifest privately.
- [ ] Define the matched feature family and data-quality contract.
- [ ] Implement private matched feature extraction.
- [ ] Run synthetic and privacy-focused tests.
- [ ] Execute feature extraction only after software verification.
