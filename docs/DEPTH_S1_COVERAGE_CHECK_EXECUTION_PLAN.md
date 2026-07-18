# Depth Sentinel-1 Coverage Check Execution Plan

Status: coverage-check implementation and software verification complete on `main`; first private-site execution is pending.

## Purpose

The evidence search has identified controlled physical sites with independently installed or surveyed depth information. The next step is to verify whether each site has usable Sentinel-1 observation coverage before any pre/post feature experiment is attempted.

This slice does not estimate depth, fit a model, import calibration rows, or enable app output.

## Implemented scope

Added a private local utility:

```text
scripts/check_depth_s1_coverage.py
```

The utility now:

1. reads one private GeoJSON site polygon from outside Git;
2. rejects repository-local geometry files;
3. accepts only Polygon or MultiPolygon site geometry;
4. strips GeoJSON properties before the query so private labels are not transmitted;
5. validates an explicit start date, exclusive end date, and optional installation/event date;
6. runs as a no-network dry run unless `--execute` is supplied;
7. queries `COPERNICUS/S1_GRD` only after explicit execution approval;
8. filters to IW mode, VV/VH dual polarization, and the requested ground resolution;
9. returns aggregate acquisition counts, first and last dates, orbit-direction counts, relative-orbit counts, platform counts, and pre/post counts;
10. never prints coordinates, the private geometry, private paths, or image identifiers;
11. optionally writes the aggregate summary only to a path outside Git.

Added focused tests:

```text
tests/unit/test_depth_s1_coverage_check.py
```

## Owner verification

The owner ran the focused and complete unit suites on Windows with Python 3.13.5.

Observed results:

```text
coverage-check tests: 10 passed
C1 redaction-risk tests: 3 passed
full unit suite: 950 passed
failures: 0
warnings: 4 non-blocking
```

The warnings were the existing NumPy entropy warnings, the existing rasterio non-georeferenced test warning, and a pytest cache-write access warning. They did not affect the passing result.

## Privacy and scientific boundaries

- The geometry remains local and private.
- Site coordinates and exact polygons are not committed.
- Output is acquisition metadata only; it is not a signal or depth result.
- Acquisition availability does not prove that the site is detectable.
- Multiple images from one site remain one physical-site group.
- `--execute` performs only coverage discovery. It does not export imagery or features.
- The current app depth output remains `not_available`.

## Output behavior

Dry-run status:

```text
coverage_query_dry_run_ready
```

Executed status:

```text
coverage_query_completed
```

Aggregate fields may include:

```text
collection_id
start_date
end_date_exclusive
event_date
acquisition_count
first_acquisition_date
last_acquisition_date
orbit_pass_counts
relative_orbit_counts
platform_counts
pre_event_count
on_event_date_count
post_event_count
```

The output also states:

```text
coordinates_printed = false
image_ids_printed = false
private_paths_printed = false
scientific_validation_run = false
training_started = false
app_depth_enabled = false
```

## Private polygon helper decision

The controlled-site literature provides a public approximate site center and a documented 50 m by 50 m site size for the first candidate. To avoid hand-writing GeoJSON, the next repository slice is a dry-run-first helper that accepts a center latitude, center longitude, width, height, and an output path outside Git.

The helper must:

- keep all coordinates out of normal output;
- refuse repository-local output;
- refuse overwrite of an existing private file;
- write only after explicit `--write`;
- create a closed GeoJSON Polygon with empty properties;
- make no Earth Engine request;
- mark the polygon as a screening footprint requiring local visual review before execution.

The helper will not hard-code candidate coordinates in Git.

## First private dry run

After the private polygon exists, run without `--execute`:

```powershell
python .\scripts\check_depth_s1_coverage.py `
  --site-geojson "C:\private\candidate_site.geojson" `
  --start-date "2017-01-01" `
  --end-date "2023-01-01" `
  --event-date "2020-03-04"
```

Expected status:

```text
coverage_query_dry_run_ready
query_executed = false
```

No Earth Engine request occurs in this mode.

## First executed query

After the dry run succeeds and the private polygon is visually reviewed:

```powershell
python .\scripts\check_depth_s1_coverage.py `
  --site-geojson "C:\private\candidate_site.geojson" `
  --start-date "2017-01-01" `
  --end-date "2023-01-01" `
  --event-date "2020-03-04" `
  --execute `
  --output "C:\private\candidate_site_s1_coverage.json"
```

The first candidate event date is the documented Texas A&M–Corpus Christi completion date, 2020-03-04. The separate event-date policy excludes February and March 2020 from the first signal comparison because construction activity occurred during those months.

## Completion gate

The coverage-check software slice is complete because the targeted tests, C1 privacy tests, and full unit suite passed.

A passing coverage query means only that suitable Sentinel-1 acquisitions exist. It does not approve evidence import or a depth claim.

## Checklist

- [x] Confirm site-level coverage screening is the next safe software step.
- [x] Define dry-run-first behavior.
- [x] Define aggregate-only output.
- [x] Keep private geometry outside Git.
- [x] Implement the coverage checker.
- [x] Add focused unit tests.
- [x] Recover the first event date: Texas A&M–Corpus Christi completed 2020-03-04.
- [x] Run targeted coverage-check tests: 10 passed.
- [x] Run C1 privacy tests: 3 passed.
- [x] Run the full unit suite: 950 passed.
- [x] Record verification results.
- [ ] Implement and test the private polygon helper.
- [ ] Create the first private screening polygon.
- [ ] Visually review the polygon against the public campus description.
- [ ] Run the dry coverage check.
- [ ] Execute the aggregate coverage query.
- [ ] Record acquisition and orbit support decisions.
