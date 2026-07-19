# Depth Sentinel-1 Coverage Check Execution Plan

Status: coverage checker and private polygon helper are implemented and locally verified on `main`; the first private screening polygon and no-network coverage dry run are complete. Visual footprint review and the executed aggregate coverage query remain pending.

## Purpose

The evidence search identified controlled physical sites with independently installed or surveyed depth information. This workflow checks whether a candidate site has usable Sentinel-1 acquisition coverage before any pre/post feature experiment is attempted.

This slice does not estimate depth, fit a model, import calibration rows, or enable app output.

## Implemented tools

```text
scripts/create_depth_site_polygon.py
scripts/check_depth_s1_coverage.py
tests/unit/test_depth_site_polygon.py
tests/unit/test_depth_s1_coverage_check.py
```

The polygon helper:

- accepts runtime center latitude and longitude plus width and height in metres;
- hard-codes no candidate coordinates in Git;
- creates a closed rectangular GeoJSON Polygon with empty properties;
- runs as dry-run unless `--write` is supplied;
- refuses repository-local output and refuses overwrite;
- makes no network request;
- prints no coordinates or private path;
- marks the result as a screening footprint requiring visual review.

The coverage checker:

- reads a private Polygon or MultiPolygon outside Git;
- strips GeoJSON properties before the query;
- validates start, end, and optional event dates;
- performs no Earth Engine request unless `--execute` is supplied;
- queries `COPERNICUS/S1_GRD` in IW mode with VV/VH and the requested resolution;
- returns aggregate acquisition, date, orbit-pass, relative-orbit, platform, and pre/post counts;
- never prints coordinates, private geometry, private paths, or image identifiers;
- can write only an aggregate JSON summary outside Git.

## Owner verification

The owner ran the focused and complete unit suites on Windows with Python 3.13.5.

Observed results after the polygon-helper addition:

```text
polygon-helper tests: 10 passed
C1 redaction-risk tests: 3 passed
full unit suite: 960 passed
failures: 0
warnings: 4 non-blocking
```

The warnings were the existing NumPy entropy warnings, the existing rasterio non-georeferenced test warning, and the pytest cache-write access warning. They did not affect the passing result.

Earlier coverage-check verification also passed:

```text
coverage-check tests: 10 passed
```

## First private polygon result

The owner successfully ran the polygon helper in dry-run and write modes using the public screening center and documented 50 m by 50 m site size.

Observed aggregate statuses:

```text
private_site_polygon_dry_run_ready
output_written = false

private_site_polygon_written
output_written = true
screening_footprint_requires_visual_review = true
```

The private polygon remains outside Git. Its coordinates and path were not printed by the tool.

## First coverage dry-run result

The owner ran the checker without `--execute` for the 2017-01-01 to 2023-01-01 window with event date 2020-03-04.

Observed result:

```text
status = coverage_query_dry_run_ready
query_executed = false
collection_id = COPERNICUS/S1_GRD
instrument_mode = IW
required_polarisations = VV, VH
resolution_meters = 10
coordinates_printed = false
image_ids_printed = false
private_paths_printed = false
scientific_validation_run = false
training_started = false
app_depth_enabled = false
```

No Earth Engine request occurred.

## Privacy and scientific boundaries

- The geometry remains local and private.
- Site coordinates and exact polygons are not committed.
- The generated rectangle is a screening footprint, not a surveyed boundary.
- The footprint must be visually reviewed before `--execute`.
- Acquisition availability is metadata only; it does not prove detectability.
- Multiple acquisitions from one site remain one physical-site group.
- The executed coverage query exports no imagery or features.
- The current app depth output remains `not_available`.

## First executed query

After visual review of the private footprint, run:

```powershell
python .\scripts\check_depth_s1_coverage.py `
  --site-geojson "C:\Dev\New_GEE_PRIVATE\DEPTH_CALIBRATION\tamucc_site.geojson" `
  --start-date "2017-01-01" `
  --end-date "2023-01-01" `
  --event-date "2020-03-04" `
  --execute `
  --output "C:\Dev\New_GEE_PRIVATE\DEPTH_CALIBRATION\tamucc_site_s1_coverage.json"
```

Expected status:

```text
coverage_query_completed
query_executed = true
```

The Texas A&M–Corpus Christi completion date is 2020-03-04. The separate event policy excludes February and March 2020 from the later signal comparison because construction activity occurred during those months.

## Coverage decision after execution

The aggregate result must be reviewed for:

```text
nonzero pre-event acquisitions
nonzero post-event acquisitions
comparable orbit directions
at least one reusable relative-orbit group across periods
usable acquisition dates outside the construction-transition interval
```

A successful coverage query means only that suitable acquisitions exist. It does not approve evidence import, feature extraction, a model, or a depth claim.

## Checklist

- [x] Implement the private polygon helper.
- [x] Implement the aggregate Sentinel-1 coverage checker.
- [x] Run polygon-helper tests: 10 passed.
- [x] Run coverage-check tests: 10 passed.
- [x] Run C1 privacy tests: 3 passed.
- [x] Run the full unit suite after all changes: 960 passed.
- [x] Create the first private screening polygon.
- [x] Run the no-network coverage dry check.
- [ ] Visually review the private footprint.
- [ ] Execute the aggregate coverage query.
- [ ] Record acquisition and orbit support decisions.
- [ ] Define a separately screened background window.
- [ ] Begin matched pre/post feature extraction only if coverage support passes.
