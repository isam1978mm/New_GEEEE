# Depth TAMUCC Sentinel-1 Coverage Result — 2026-07-20

Status: aggregate coverage gate passed for the first controlled-site pre/post experiment. This result does not estimate depth, prove a physical effect, import calibration rows, train a model, or enable app depth output.

## Query contract

```text
collection = COPERNICUS/S1_GRD
instrument_mode = IW
polarisations = VV and VH
resolution_meters = 10
start_date = 2017-01-01
end_date_exclusive = 2023-01-01
event_date = 2020-03-04
clean_pre_end_exclusive = 2020-02-01
clean_post_start = 2020-04-01
analysis_window_mode = conservative_pre_transition_post
```

## Aggregate result

```text
status = coverage_query_completed
query_executed = true
coverage_decision = coverage_ready_for_matched_pre_post_feature_screening
acquisition_count = 169
clean_pre_acquisition_count = 82
transition_acquisition_count = 5
clean_post_acquisition_count = 82
pre_post_relative_orbit_support = true
reusable_platform = A
reusable_orbit_pass = ASCENDING
reusable_relative_orbit = 107
output_written = true
coordinates_printed = false
image_ids_printed = false
private_paths_printed = false
scientific_validation_run = false
training_started = false
app_depth_enabled = false
```

## Decision

The site has sufficient Sentinel-1 metadata coverage to proceed to exact site/background image-identity matching using platform A, ascending pass, and relative orbit 107.

This does not establish detectability or depth. Multiple acquisitions remain repeated observations of one physical site, not independent calibration sites.

## Next governed step

Use the already reviewed private background polygon and execute:

```text
scripts/check_depth_s1_site_background_match.py
```

The match must use the same frozen clean windows and the selected A / ASCENDING / 107 contract. It must write the exact matched-image manifest outside Git and expose only aggregate counts at the console.

Feature extraction remains blocked until exact shared images exist in both clean periods.

## Checklist

- [x] Run conservative-window no-network dry check.
- [x] Execute aggregate Sentinel-1 coverage query.
- [x] Confirm nonzero clean pre acquisitions.
- [x] Confirm nonzero clean post acquisitions.
- [x] Confirm reusable relative-orbit support.
- [x] Select A / ASCENDING / 107 for the first matched experiment.
- [ ] Execute exact site/background image-identity match.
- [ ] Freeze the matched-image manifest privately.
- [ ] Review matched clean-pre and clean-post counts.
- [ ] Run matched feature extraction only if the exact match passes.
