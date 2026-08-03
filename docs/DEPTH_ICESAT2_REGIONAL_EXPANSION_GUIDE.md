# ICESat-2 regional expansion scan

Status: read-only candidate discovery; no depth or cause claim.

## Why this exists

The scan-first audit completed successfully across all nine existing completed
runs and found zero persistent upward-step clusters. Several runs represent the
same geography, so repeating the same AOIs would add no evidence.

The next bounded step is to expand around each unique run geography and scan the
surrounding terrain before doing any record research.

## What the regional scanner does

The scanner:

1. discovers completed run directories;
2. groups nearly identical run grids into one geography;
3. expands each unique grid by 10 km on every side by default;
4. divides the expanded square into 10 km projected tiles;
5. queries ATL08 terrain histories for each tile;
6. combines and deduplicates observations returned at tile boundaries;
7. applies the existing flat-jump-flat, plateau and neighbour-agreement tests;
8. excludes candidates inside the already-scanned source AOI from the research
   priority list;
9. ranks only surviving regional candidates.

It does not use records during the scan.

## Why the first expansion is 10 km

This is a bounded first ring, not an arbitrary global search. It expands the
measured search area substantially while keeping the number and size of remote
queries controlled. If the first ring produces no candidates, a later run can
increase `--buffer-km` without changing the scientific thresholds.

Do not lower the step or neighbour thresholds merely to create candidates.

## Tests

```powershell
cd C:\Dev\New_GEE_depth
git pull

cd C:\Dev\New_GEE

.\.venv\Scripts\python.exe -m pytest `
  ..\New_GEE_depth\tests\unit\test_icesat2_regional_expansion.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_step_scan.py -q
```

## Run the first expansion ring

```powershell
cd C:\Dev\New_GEE

.\.venv\Scripts\python.exe ..\New_GEE_depth\scripts\scan_icesat2_regional_expansion.py `
  --runs-dir .\data\runs `
  --buffer-km 10 `
  --tile-km 10
```

The combined summary is written to:

```text
C:\Dev\New_GEE\data\runs\icesat2_regional_expansion\icesat2_regional_expansion_summary.json
```

Each unique geography also receives a private JSON result and GeoJSON candidate
file under the same directory.

## Decisive fields

```text
unique_geography_count
duplicate_run_count
completed_geography_scan_count
failed_geography_count
surviving_candidate_count
record_lookup_priority
```

Interpretation:

- `no_surviving_candidates_in_regional_expansion`: do no record lookup for this
  ring;
- `regional_surviving_candidates_found`: research only the ranked survivors;
- nonzero `failed_geography_count`: inspect failures before treating the ring as
  complete.

## Scientific boundary

A surviving result is still only a persistent terrain-step candidate. It does
not establish engineered fill, placed thickness, buried-object depth, or a
radar-to-depth relationship.

Records are used only after the terrain history survives, to determine:

- what construction occurred;
- the event dates;
- the mapped footprint;
- the placed or removed thickness;
- whether the ATL08 segment was sufficiently covered by the work.

The narrow laser strip remains a limitation. Transferring a measured step to
nearby radar pixels is a separate spatial-uniformity assumption that must be
stated and tested.
