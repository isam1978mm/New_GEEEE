# Depth Private Background Candidate Generation Plan

Status: implementation complete on `main`; local verification and private candidate generation are pending.

## Purpose

The qualified controlled-site coverage and exact-acquisition matcher are ready. The next step is to create several private, non-overlapping comparison-window candidates around the reviewed site polygon so one can be visually screened before any Earth Engine match query.

This slice does not approve a background, query Earth Engine, export imagery, calculate signal differences, estimate depth, train a model, import calibration rows, or enable app output.

## Implemented utility

```text
scripts/create_depth_background_candidates.py
tests/unit/test_depth_background_candidates.py
```

The utility:

1. reads the private site Polygon from outside Git;
2. rejects repository-local input and output locations;
3. accepts only one simple axis-aligned rectangular Polygon;
4. accepts an explicit positive edge-gap distance in metres;
5. creates four same-size candidate rectangles north, east, south, and west of the site;
6. keeps the requested edge gap between each candidate and the site;
7. verifies that each generated candidate does not overlap the site bounding box;
8. rejects antimeridian and unsupported-latitude cases;
9. runs as a no-write dry run unless `--write` is supplied;
10. refuses to overwrite any existing candidate file;
11. writes each candidate as a separate private GeoJSON with empty properties;
12. cleans up newly written files if the multi-file write fails;
13. makes no network request;
14. prints no coordinates, geometry, or private paths;
15. marks every candidate as pending visual review;
16. leaves app depth output unavailable.

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

The console result also states:

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

The private output directory contains:

```text
background_north.geojson
background_east.geojson
background_south.geojson
background_west.geojson
```

The files remain outside Git. They contain geometry only and do not claim that any candidate is a valid background.

## Focused test coverage

The 11 focused cases cover:

- repository-local site input rejection;
- repository-local output-directory rejection;
- malformed or non-rectangular geometry rejection;
- zero, negative, and non-finite edge-gap rejection;
- dry-run no-write behavior;
- four closed private Polygon outputs;
- preserved site width and height;
- non-overlap with the site rectangle;
- existing-file overwrite refusal;
- aggregate-only, privacy-safe output.

## Verification commands

```powershell
python -m pytest tests/unit/test_depth_background_candidates.py -v
python -m pytest tests/unit/test_plan_c_redaction_risk_allowlist.py -v
python -m pytest tests/unit -q
```

## First private dry run

Use an explicit screening edge gap. The initial software workflow uses 100 metres; this is a candidate-generation spacing choice, not a scientific approval rule.

```powershell
python .\scripts\create_depth_background_candidates.py `
  --site-geojson "<PRIVATE_DEPTH_ROOT>\tamucc_site.geojson" `
  --output-dir "<PRIVATE_DEPTH_ROOT>\tamucc_background_candidates" `
  --edge-gap-m 100
```

Expected:

```text
status = private_background_candidates_dry_run_ready
candidate_count = 4
output_written = false
```

Only after the dry run succeeds:

```powershell
python .\scripts\create_depth_background_candidates.py `
  --site-geojson "<PRIVATE_DEPTH_ROOT>\tamucc_site.geojson" `
  --output-dir "<PRIVATE_DEPTH_ROOT>\tamucc_background_candidates" `
  --edge-gap-m 100 `
  --write
```

Expected:

```text
status = private_background_candidates_written
candidate_count = 4
output_written = true
visual_review_required = true
```

## Review rule

A candidate may be selected only after local visual review confirms that it:

- does not overlap the controlled site;
- is outside the known construction footprint;
- has reasonably comparable surface and environmental context;
- avoids obvious roads, buildings, water, dense vegetation, or unrelated major construction where practical;
- is treated as a comparison window, not a confirmed no-target calibration record.

The generator does not perform these scientific judgments automatically.

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
- [x] Implement the candidate generator.
- [x] Add focused tests.
- [ ] Run targeted and full verification.
- [ ] Generate private candidates.
- [ ] Visually review all candidates.
- [ ] Select one background polygon.
- [ ] Run the site-background match dry run.
