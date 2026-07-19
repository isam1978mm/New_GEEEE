# Texas A&M–Corpus Christi Sentinel-1 Coverage Result — 2026-07-19

Status: first aggregate Earth Engine coverage query completed successfully. Coverage availability is confirmed. Matched clean pre/post relative-orbit qualification requires one rerun with the conservative construction-exclusion window.

This document records acquisition metadata only. It does not report a signal difference, estimate depth, import calibration records, train a model, or enable app output.

## Executed query

The owner executed the private aggregate checker for:

```text
collection = COPERNICUS/S1_GRD
instrument_mode = IW
polarisations = VV and VH
resolution_meters = 10
start_date = 2017-01-01
end_date_exclusive = 2023-01-01
event_date = 2020-03-04
```

The private screening polygon and output remained outside Git. Coordinates, private paths, and image identifiers were not printed.

## Observed aggregate result

```text
status = coverage_query_completed
query_executed = true
acquisition_count = 169
first_acquisition_date = 2017-01-06
last_acquisition_date = 2022-12-30
pre_event_count = 85
on_event_date_count = 0
post_event_count = 84

orbit_pass_counts:
  ASCENDING = 167
  DESCENDING = 2

relative_orbit_counts:
  107 = 167
  143 = 1
  41 = 1

platform_counts:
  A = 168
  B = 1
```

Privacy and release flags remained:

```text
coordinates_printed = false
image_ids_printed = false
private_paths_printed = false
scientific_validation_run = false
training_started = false
app_depth_enabled = false
```

## What this establishes

The site has substantial Sentinel-1 IW VV/VH coverage across both sides of the documented completion date.

The overall metadata is strongly dominated by:

```text
orbit_pass = ASCENDING
relative_orbit = 107
platform = A
```

This makes relative orbit 107 the leading candidate for a matched pre/post experiment.

## What this result does not yet establish

The first summary counted observations before and after 2020-03-04, but it did not break relative-orbit counts down by period.

It also treated observations after the completion date as post-event even when they occurred during March 2020. The documented construction policy excludes all February and March 2020 observations because excavation, placement, grading, and restoration may have occurred during that interval.

Therefore the first result alone does not prove that relative orbit 107 has nonzero observations in both clean periods:

```text
clean_pre = dates before 2020-02-01
transition_excluded = 2020-02-01 through 2020-03-31
clean_post = dates on or after 2020-04-01
```

No matched-orbit approval is inferred from aggregate totals alone.

## Checker hardening

The checker now supports:

```text
--pre-end-exclusive
--post-start
```

It reports clean pre, transition, and clean post counts by:

```text
orbit direction
relative orbit
platform
```

It also reports:

```text
reusable_relative_orbits
reusable_orbit_passes
reusable_platforms
pre_post_relative_orbit_support
coverage_decision
```

The coverage decision becomes ready only when at least one relative orbit has nonzero observations in both clean periods.

## Required rerun

After updating `main`, rerun:

```powershell
python .\scripts\check_depth_s1_coverage.py `
  --site-geojson "C:\Dev\New_GEE_PRIVATE\DEPTH_CALIBRATION\tamucc_site.geojson" `
  --start-date "2017-01-01" `
  --end-date "2023-01-01" `
  --event-date "2020-03-04" `
  --pre-end-exclusive "2020-02-01" `
  --post-start "2020-04-01" `
  --execute `
  --output "C:\Dev\New_GEE_PRIVATE\DEPTH_CALIBRATION\tamucc_site_s1_coverage_matched.json"
```

The desired decision is:

```text
coverage_decision = coverage_ready_for_matched_pre_post_feature_screening
pre_post_relative_orbit_support = true
```

The exact reusable orbit must come from the rerun output. It must not be assumed from the overall counts.

## Checklist

- [x] Create the private site screening polygon.
- [x] Run the no-network dry check.
- [x] Execute the first aggregate Earth Engine coverage query.
- [x] Confirm nonzero overall pre-event and post-event acquisitions.
- [x] Confirm one dominant orbit direction and relative-orbit group overall.
- [x] Preserve aggregate-only private output.
- [x] Harden the checker for conservative clean pre/transition/clean post periods.
- [x] Add reusable-relative-orbit qualification logic.
- [ ] Run the hardened checker tests.
- [ ] Rerun the private coverage query with the construction interval excluded.
- [ ] Confirm at least one reusable relative orbit across clean periods.
- [ ] Define a separately screened background polygon.
- [ ] Begin matched pre/post feature extraction only if the qualified coverage decision passes.
