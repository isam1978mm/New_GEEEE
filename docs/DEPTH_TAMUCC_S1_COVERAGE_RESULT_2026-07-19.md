# Texas A&M–Corpus Christi Sentinel-1 Coverage Result — 2026-07-19

Status: **qualified coverage passed** for a matched clean pre/post feature-screening experiment. This is acquisition-metadata readiness only. It does not establish a buried-feature signal, estimate depth, import calibration records, train a model, or enable app output.

## Query contract

The private aggregate checker was executed with:

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
```

The private screening polygon and aggregate output remained outside Git. Coordinates, private paths, geometry, and image identifiers were not printed.

## Software verification

Before the qualified query, the owner ran:

```text
hardened coverage-check tests = 12 passed
C1 redaction-risk tests = 3 passed
full unit suite = 962 passed
failures = 0
warnings = 4 non-blocking
```

The warnings were the existing NumPy entropy warnings, the existing rasterio non-georeferenced test warning, and the pytest cache-write warning.

## Qualified aggregate result

```text
status = coverage_query_completed
query_executed = true
analysis_window_mode = conservative_pre_transition_post
coverage_decision = coverage_ready_for_matched_pre_post_feature_screening
pre_post_relative_orbit_support = true

acquisition_count = 169
first_acquisition_date = 2017-01-06
last_acquisition_date = 2022-12-30

clean_pre_count = 82
transition_excluded_count = 5
clean_post_count = 82
```

### Clean pre-construction period

```text
orbit_pass_counts:
  ASCENDING = 80
  DESCENDING = 2

relative_orbit_counts:
  107 = 80
  143 = 1
  41 = 1

platform_counts:
  A = 81
  B = 1
```

### Excluded construction-transition period

```text
observation_count = 5
orbit_pass = ASCENDING
relative_orbit = 107
platform = A
```

These five observations remain excluded from the first signal comparison.

### Clean post-construction period

```text
orbit_pass_counts:
  ASCENDING = 82

relative_orbit_counts:
  107 = 82

platform_counts:
  A = 82
```

### Reusable acquisition geometry

```text
reusable_orbit_passes = ASCENDING
reusable_relative_orbits = 107
reusable_platforms = A
```

The primary matched experiment can therefore use:

```text
platform = Sentinel-1A
orbit_pass = ASCENDING
relative_orbit = 107
clean_pre_available = 80
clean_post_available = 82
```

## Decision

```text
site_coverage_available = true
clean_pre_post_coverage_available = true
matched_relative_orbit_support = true
selected_relative_orbit_candidate = 107
selected_orbit_pass_candidate = ASCENDING
selected_platform_candidate = A
coverage_ready_for_feature_screening = true
scientific_signal_validation_run = false
depth_model_training_started = false
app_depth_enabled = false
```

The unequal 80-versus-82 selected-orbit counts do not prevent a matched experiment. The feature workflow must use only acquisition dates available for both the site and a separately screened background window, and must keep period balancing explicit.

## What this establishes

The controlled site has sufficient Sentinel-1 acquisition support to continue to a matched site-versus-background pre/post feature-screening experiment using the same platform, orbit direction, and relative orbit.

This removes acquisition availability as the current stopping point.

## What this does not establish

This result does not show that Sentinel-1 detected the buried targets. It does not distinguish burial effects from excavation, soil disturbance, vegetation, moisture, surface change, or nearby infrastructure.

The next experiment must therefore include:

1. a separately reviewed background polygon;
2. exact acquisition-time intersection between site and background;
3. the same platform, orbit pass, and relative orbit;
4. exclusion of the February–March 2020 transition period;
5. approved SAR features only;
6. explicit confounder and stability checks;
7. no numerical depth claim.

## Next execution slice

```text
create and visually review background candidate
→ verify background Sentinel-1 coverage
→ intersect exact acquisition timestamps
→ freeze matched pre and post acquisition manifests privately
→ extract approved site and background features
→ compare difference-in-differences and stability diagnostics
```

## Checklist

- [x] Create the private site screening polygon.
- [x] Run the no-network coverage dry check.
- [x] Execute the aggregate Earth Engine coverage query.
- [x] Exclude the February–March 2020 construction interval.
- [x] Confirm 82 clean pre and 82 clean post observations.
- [x] Confirm reusable ascending relative orbit 107 on platform A.
- [x] Pass the qualified coverage decision.
- [x] Preserve aggregate-only console output.
- [ ] Define and visually review a separate background polygon.
- [ ] Verify background coverage using the same query contract.
- [ ] Freeze exact matched acquisition timestamps privately.
- [ ] Extract approved matched site/background features.
- [ ] Run a confounder-aware feature-screening experiment.
- [ ] Keep app depth output unavailable unless later validation gates pass.
