# Depth Sentinel-1 Coverage Check Execution Plan

Status: active implementation on `main`.

## Purpose

The evidence search has identified controlled physical sites with independently installed or surveyed depth information. The next step is to verify whether each site has usable Sentinel-1 observation coverage before any pre/post feature experiment is attempted.

This slice does not estimate depth, fit a model, import calibration rows, or enable app output.

## Scope

Add a private local utility:

```text
scripts/check_depth_s1_coverage.py
```

The utility will:

1. read one private GeoJSON site polygon from outside Git;
2. reject repository-local geometry files;
3. accept only Polygon or MultiPolygon site geometry;
4. validate an explicit start date, exclusive end date, and optional installation/event date;
5. run as a no-network dry run unless `--execute` is supplied;
6. query `COPERNICUS/S1_GRD` only after explicit execution approval;
7. filter to IW mode, VV/VH dual polarization, and the requested ground resolution;
8. return aggregate acquisition counts, first and last dates, orbit-direction counts, relative-orbit counts, platform counts, and pre/post counts;
9. never print coordinates, the private geometry, private paths, or image identifiers;
10. optionally write the aggregate summary only to a path outside Git.

## Privacy and scientific boundaries

- The geometry remains local and private.
- Site coordinates and exact polygons are not committed.
- Output is acquisition metadata only; it is not a signal or depth result.
- Acquisition availability does not prove that the site is detectable.
- Multiple images from one site remain one physical-site group.
- `--execute` performs only coverage discovery. It does not export imagery or features.
- The current app depth output remains `not_available`.

## Planned output

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

The output must also state:

```text
coordinates_printed = false
image_ids_printed = false
training_started = false
app_depth_enabled = false
```

## Planned tests

- repository-local geometry is rejected;
- Point and LineString geometry are rejected;
- Polygon and MultiPolygon geometry are accepted;
- invalid and reversed dates are rejected;
- dry run performs no Earth Engine call;
- execution requires an injected or real query function;
- aggregate orbit and pre/post counts are correct;
- result contains no coordinates, private path, or image identifiers;
- optional output path must remain outside Git.

## Completion gate

The software slice is complete when the targeted tests, C1 privacy tests, and full unit suite pass.

A passing coverage query means only that suitable Sentinel-1 acquisitions exist. It does not approve evidence import or a depth claim.

## Checklist

- [x] Confirm site-level coverage screening is the next safe software step.
- [x] Define dry-run-first behavior.
- [x] Define aggregate-only output.
- [x] Keep private geometry outside Git.
- [ ] Implement the coverage checker.
- [ ] Add focused unit tests.
- [ ] Run targeted tests.
- [ ] Run C1 privacy tests.
- [ ] Run the full unit suite.
- [ ] Create private polygons for approved candidate sites.
- [ ] Recover exact installation/event dates.
- [ ] Execute site coverage queries.
- [ ] Record acquisition and orbit support decisions.
