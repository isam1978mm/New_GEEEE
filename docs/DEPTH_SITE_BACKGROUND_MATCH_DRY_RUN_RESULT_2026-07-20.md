# Depth Site–Background Match Dry-Run Result — 2026-07-20

Status: dry-run gate passed; executed Sentinel-1 metadata matching is now permitted.

This result records workflow readiness only. It does not calculate a signal difference, estimate depth, train a model, import calibration rows, or enable app depth output.

## Reviewed geometry state

```text
site polygon = private and outside Git
selected background = south candidate from the 300 m eight-direction set
canonical background file created = true
background visual review confirmed = true
```

The selected background remains a comparison window only. It is not an independently confirmed no-target calibration record.

## Dry-run result

```text
status = site_background_match_dry_run_ready
query_executed = false
background_visual_review_confirmed = true
selected_platform = A
selected_orbit_pass = ASCENDING
selected_relative_orbit = 107
start_date = 2017-01-01
end_date_exclusive = 2023-01-01
pre_end_exclusive = 2020-02-01
post_start = 2020-04-01
collection_id = COPERNICUS/S1_GRD
instrument_mode = IW
required_polarisations = VV, VH
resolution_meters = 10
```

Privacy and release flags remained:

```text
coordinates_printed = false
geometry_printed = false
private_paths_printed = false
image_ids_printed = false
aggregate_output_written = false
private_manifest_written = false
scientific_validation_run = false
training_started = false
app_depth_enabled = false
```

## Decision

```text
dry_run_gate_passed = true
executed_metadata_match_permitted = true
feature_extraction_permitted = false
scientific_signal_validation_run = false
app_depth_enabled = false
```

The next permitted action is to execute the exact site-background Sentinel-1 identity match, write an aggregate summary outside Git, and freeze the exact shared image identities in a private manifest outside Git.

A successful executed match will prove only that exact Sentinel-1 source images are shared by both polygons in the clean pre and clean post periods. It will not prove any physical or depth effect.

## Checklist

- [x] Select and review the south background candidate.
- [x] Create the canonical private background file.
- [x] Run the no-network matcher dry run.
- [x] Confirm the dry-run gate passed.
- [ ] Execute the exact metadata match.
- [ ] Write the aggregate summary privately.
- [ ] Freeze the exact shared-image manifest privately.
- [ ] Review matched pre/post counts before any feature extraction.
