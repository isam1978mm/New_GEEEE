# ICESat-2 scan-first workflow across all existing runs

Status: read-only candidate discovery; no depth or cause claim.

## Purpose

The single-run scanner found no persistent upward step in run
`a4881db6-d92e-4ebc-b628-8a1b089db20b`. That run should not receive any record
research.

The next correct action is to run the same conservative scan across every
existing completed AOI, then research records only for surviving clusters.

## Which runs are selected

By default, a directory is selected only when it contains:

- `grid_manifest.json`; and
- at least one normal completed-run marker:
  - `logRatio_dB.tif`, or
  - `objects_index.csv`.

This prevents partial or failed run directories from triggering remote ATL08
queries. Older grid-only layouts can be included explicitly with
`--include-grid-only`.

The script does not write to the app database or change run status.

## Resume behavior

Each run result is stored privately inside its run directory:

```text
icesat2_step_scan.json
icesat2_step_candidates.geojson
```

A valid existing `icesat2_step_scan.json` is reused automatically. Therefore,
the run already scanned in the previous step is not queried again.

Use `--force` only to deliberately repeat every live query.

## Run the focused tests

```powershell
cd C:\Dev\New_GEE_depth
git pull

cd C:\Dev\New_GEE

.\.venv\Scripts\python.exe -m pytest `
  ..\New_GEE_depth\tests\unit\test_icesat2_all_runs_step_scan.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_step_scan.py -q
```

## Scan all completed runs

```powershell
cd C:\Dev\New_GEE

.\.venv\Scripts\python.exe ..\New_GEE_depth\scripts\scan_all_icesat2_terrain_steps.py `
  --runs-dir .\data\runs
```

Progress is printed to the error stream while the final JSON summary is printed
to the normal output stream.

The combined private summary is written to:

```text
data/runs/icesat2_step_scan_all_runs.json
```

A failed SlideRule query for one run is recorded and the batch continues. The
command returns a non-zero exit code when one or more runs failed, but the
completed results and combined summary are still preserved.

## Decisive fields

```text
selected_run_count
completed_run_count_scanned
failed_run_count
surviving_candidate_count
record_lookup_priority
run_summaries
failures
skipped_directories
```

Interpretation:

- `surviving_candidate_count = 0`: do not research records for these runs;
- greater than zero: research only `record_lookup_priority` in rank order;
- failures greater than zero: rerun normally; cached successful runs will be
  reused and only failed or missing results will query again;
- unexpectedly low `selected_run_count`: rerun once with `--include-grid-only`
  to include older run layouts.

## Candidate ranking

Ranking prefers:

1. support from another detector spot;
2. more neighbouring agreeing segments;
3. lower variation in the measured step;
4. larger measured upward step.

This is only record-research priority. It is not a probability of fill and not
a depth confidence score.

## Scientific boundary

The batch scan does not:

- identify engineered fill;
- prove placed thickness;
- establish depth to a buried object;
- connect ICESat-2 change to radar;
- assume that the laser measurement applies outside the laser strip;
- modify the classifier, frontend, Option 5, orchestrator, or production depth
  engine.

Records are required only after a candidate survives, to confirm what happened,
when it happened, its mapped footprint, and its measured thickness.
