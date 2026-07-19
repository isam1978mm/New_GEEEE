# Depth Site–Background Acquisition Match Plan

Status: implementation complete on `main`; local verification and first private background execution are pending.

## Purpose

The controlled site passed the qualified Sentinel-1 coverage gate using clean pre-construction and clean post-construction periods. The next step is to ensure that the site and a separately reviewed background polygon are compared using the **same Sentinel-1 images**, not merely similar dates or orbit totals.

This slice does not export imagery, calculate signal differences, estimate depth, train a model, import calibration rows, or enable app output.

## Implemented utility

```text
scripts/check_depth_s1_site_background_match.py
tests/unit/test_depth_s1_site_background_match.py
```

The utility now:

1. reads one private site polygon and one private background polygon from outside Git;
2. rejects repository-local geometry and output paths;
3. rejects an exactly identical site/background geometry pair;
4. strips all GeoJSON properties before any query;
5. runs as a no-network dry run unless `--execute` is supplied;
6. requires `--background-reviewed` before execution;
7. queries Sentinel-1 IW VV/VH metadata for one selected platform, orbit pass, and relative orbit;
8. uses the clean pre and clean post windows while excluding the construction-transition interval;
9. matches site and background by exact Sentinel-1 image identity;
10. prints only aggregate counts and readiness decisions;
11. optionally writes a private matched-acquisition manifest outside Git containing exact image identities and timestamps;
12. never prints coordinates, geometry, private paths, or image identities;
13. leaves app depth output unavailable.

## First query contract

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
```

## Output decisions

Dry run:

```text
site_background_match_dry_run_ready
```

Executed and exact shared images exist in both clean periods:

```text
site_background_acquisition_match_ready
```

Executed but one clean period has no exact shared images:

```text
site_background_acquisition_match_not_ready
```

Aggregate output fields include:

```text
site_pre_count
background_pre_count
matched_pre_count
site_post_count
background_post_count
matched_post_count
site_transition_count
background_transition_count
site_pre_unmatched_count
background_pre_unmatched_count
site_post_unmatched_count
background_post_unmatched_count
exact_pre_match_support
exact_post_match_support
site_background_exact_match_support
match_decision
private_manifest_written
```

The console result also states:

```text
coordinates_printed = false
geometry_printed = false
private_paths_printed = false
image_ids_printed = false
scientific_validation_run = false
training_started = false
app_depth_enabled = false
```

## Private manifest

When explicitly requested, the private manifest contains:

```text
matched clean-pre Sentinel-1 image identities and timestamps
matched transition identities, retained only as excluded provenance
matched clean-post Sentinel-1 image identities and timestamps
selected platform, orbit pass, and relative orbit
query and transition-window contract
```

The manifest:

- remains outside Git;
- is never printed;
- contains no coordinates or geometry;
- is not an app artifact;
- is not scientific proof of a signal;
- exists only to freeze exact source-image identity for later feature extraction.

## Background requirements

The background polygon must be reviewed separately. It must not be approved merely because it is nearby.

Before feature extraction, document that the background candidate:

- does not overlap the controlled site;
- is outside the known construction footprint;
- has reasonably comparable surface and environmental context;
- shows no obvious unrelated major construction transition during the experiment window;
- is treated as a comparison window, not an independently confirmed no-target calibration record.

## Focused test coverage

The new tests cover:

- repository-local geometry rejection;
- identical site/background geometry rejection;
- invalid clean-window rejection;
- no-network/no-write dry-run behavior;
- explicit background-review enforcement;
- exact pre, transition, and post image matching;
- unmatched image counts;
- no-clean-post refusal;
- duplicate image-identity rejection;
- private manifest isolation;
- aggregate output privacy;
- repository-local output rejection.

## Verification commands

```powershell
python -m pytest tests/unit/test_depth_s1_site_background_match.py -v
python -m pytest tests/unit/test_plan_c_redaction_risk_allowlist.py -v
python -m pytest tests/unit -q
```

## First private dry run

After creating and reviewing a private background polygon:

```powershell
python .\scripts\check_depth_s1_site_background_match.py `
  --site-geojson "<PRIVATE_DEPTH_ROOT>\tamucc_site.geojson" `
  --background-geojson "<PRIVATE_DEPTH_ROOT>\tamucc_background.geojson" `
  --start-date "2017-01-01" `
  --end-date "2023-01-01" `
  --pre-end-exclusive "2020-02-01" `
  --post-start "2020-04-01" `
  --orbit-pass "ASCENDING" `
  --relative-orbit 107 `
  --platform "A"
```

Expected:

```text
status = site_background_match_dry_run_ready
query_executed = false
```

## First executed match

Only after local visual review of the background:

```powershell
python .\scripts\check_depth_s1_site_background_match.py `
  --site-geojson "<PRIVATE_DEPTH_ROOT>\tamucc_site.geojson" `
  --background-geojson "<PRIVATE_DEPTH_ROOT>\tamucc_background.geojson" `
  --start-date "2017-01-01" `
  --end-date "2023-01-01" `
  --pre-end-exclusive "2020-02-01" `
  --post-start "2020-04-01" `
  --orbit-pass "ASCENDING" `
  --relative-orbit 107 `
  --platform "A" `
  --background-reviewed `
  --execute `
  --output "<PRIVATE_DEPTH_ROOT>\tamucc_site_background_match_summary.json" `
  --private-manifest "<PRIVATE_DEPTH_ROOT>\tamucc_site_background_matched_images.json"
```

Desired decision:

```text
match_decision = site_background_acquisition_match_ready
site_background_exact_match_support = true
matched_pre_count > 0
matched_post_count > 0
```

## Completion gate

The software slice is complete when:

```text
targeted matcher tests pass
C1 redaction-risk tests pass
full unit suite passes
```

A passing match means only that exact source images are available for a controlled comparison. It does not establish a buried-feature effect or depth relationship.

## Checklist

- [x] Qualify clean pre/post site coverage.
- [x] Select the first platform/orbit contract: A / ASCENDING / 107.
- [x] Define exact image-identity matching.
- [x] Define aggregate-only console output.
- [x] Define private manifest boundaries.
- [x] Implement the site-background matcher.
- [x] Add focused tests.
- [ ] Run targeted and full verification.
- [ ] Define and visually review the background polygon.
- [ ] Run the no-network match dry run.
- [ ] Execute the exact acquisition match.
- [ ] Freeze the matched acquisition manifest privately.
- [ ] Begin approved feature extraction only after the match passes.
