# Depth Private Background Candidate Generation Plan

Status: active implementation on `main`.

## Purpose

The qualified controlled-site coverage and exact-acquisition matcher are ready. The next step is to create several private, non-overlapping comparison-window candidates around the reviewed site polygon so one can be visually screened before any Earth Engine match query.

This slice does not approve a background, query Earth Engine, export imagery, calculate signal differences, estimate depth, train a model, import calibration rows, or enable app output.

## Planned utility

```text
scripts/create_depth_background_candidates.py
```

The utility will:

1. read the private site Polygon from outside Git;
2. reject repository-local input and output locations;
3. accept only one simple rectangular Polygon created by the existing site-polygon helper;
4. accept a positive edge-gap distance in metres;
5. create four same-size candidate rectangles north, east, south, and west of the site;
6. keep the requested edge gap between each candidate and the site;
7. reject antimeridian or unsupported-latitude cases;
8. run as a no-write dry run unless `--write` is supplied;
9. refuse to overwrite any existing candidate file;
10. write each candidate as a separate private GeoJSON with empty properties;
11. make no network request;
12. print no coordinates, geometry, or private paths;
13. mark every candidate as pending visual review;
14. leave app depth output unavailable.

## Output contract

Dry run:

```text
status = private_background_candidates_dry_run_ready
candidate_count = 4
output_written = false
```

Write mode:

```text
status = private_background_candidates_written
candidate_count = 4
output_written = true
visual_review_required = true
```

The console result must also state:

```text
coordinates_printed = false
geometry_printed = false
private_paths_printed = false
network_request_made = false
scientific_validation_run = false
training_started = false
app_depth_enabled = false
```

## Candidate files

The private output directory will contain four separate files:

```text
background_north.geojson
background_east.geojson
background_south.geojson
background_west.geojson
```

The files remain outside Git. They contain geometry only and do not claim that any candidate is a valid background.

## Review rule

A candidate may be selected only after local visual review confirms that it:

- does not overlap the controlled site;
- is outside the known construction footprint;
- has reasonably comparable surface and environmental context;
- avoids obvious roads, buildings, water, dense vegetation, or unrelated major construction where practical;
- is treated as a comparison window, not a confirmed no-target calibration record.

The generator does not perform these scientific judgments automatically.

## Planned tests

- repository-local input is rejected;
- repository-local output directory is rejected;
- non-rectangular or malformed site geometry is rejected;
- zero or negative edge gap is rejected;
- dry run writes nothing;
- write mode creates four separate closed Polygon files;
- candidates preserve the site width and height;
- candidates do not overlap the site bounding box;
- existing output files are not overwritten;
- console output contains no coordinates, geometry, or private paths.

## Completion gate

The software slice is complete when:

```text
targeted candidate-generator tests pass
C1 redaction-risk tests pass
full unit suite passes
```

## Checklist

- [x] Confirm the exact-acquisition matcher software gate passed.
- [x] Define four-direction candidate generation.
- [x] Define non-overlap and edge-gap rules.
- [x] Define dry-run-first and private-output behavior.
- [ ] Implement the candidate generator.
- [ ] Add focused tests.
- [ ] Run targeted and full verification.
- [ ] Generate private candidates.
- [ ] Visually review all candidates.
- [ ] Select one background polygon.
- [ ] Run the site-background match dry run.
