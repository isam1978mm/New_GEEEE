# ICESat-2 regional near-miss audit

Status: read-only diagnostic. The accepted 250 m neighbour rule is unchanged.

## Why this exists

The 10 km regional expansion found no surviving step cluster, but four
geographies produced a total of eight raw upward-step segments. Those segments
were rejected because they did not form an accepted group of at least three
neighbouring segments with one event window and consistent step magnitude.

Before expanding the search farther, this audit checks whether the raw segments
were truly isolated or whether the 250 m neighbour radius was the binding
screen.

## What it does

The tool reads the existing regional summary and automatically selects only
geographies with:

```text
raw_step_up_segment_count > 0
surviving_step_cluster_count = 0
```

It re-queries those geographies using the same 10 km buffer, quality filters,
step threshold, plateau threshold and four-epoch requirement.

For each raw step it records:

- coordinates and exact ATL08 segment ID;
- RGT, spot and early/late event cycles;
- terrain-height timeline;
- estimated step and plateau spread;
- nearest same-event segment on the same spot;
- nearest same-event segment on either spot;
- cross-spot support.

It then checks connected groups at:

```text
250 m  accepted strict radius
500 m  diagnostic only
1000 m diagnostic only
```

The 500 m and 1000 m checks do not authorize a candidate. They only explain
why the strict screen failed.

## Run tests

```powershell
cd C:\Dev\New_GEE_depth
git pull

cd C:\Dev\New_GEE

.\.venv\Scripts\python.exe -m pytest `
  ..\New_GEE_depth\tests\unit\test_icesat2_regional_near_misses.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_regional_expansion.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_step_scan.py -q
```

## Run the audit

```powershell
.\.venv\Scripts\python.exe ..\New_GEE_depth\scripts\run_icesat2_regional_near_miss_audit.py `
  --runs-dir .\data\runs `
  --buffer-km 10 `
  --tile-km 10
```

The summary is written to:

```text
data/runs/icesat2_regional_near_miss_audit/
  icesat2_regional_near_miss_summary.json
```

## Decision

### `isolated_steps_confirmed_not_clustered_within_1km`

The raw steps remain isolated even under diagnostic distances. Do not research
records for them and do not lower the accepted threshold. The current regional
search is closed.

### `near_miss_groups_require_scientific_review`

At least three same-track, same-spot, same-event segments become a consistent
connected group at 500 m or 1000 m, but not at 250 m. This does not make them an
anchor. Review their actual spacing, timelines and terrain context before
deciding whether the 250 m rule was physically too strict for ATL08 sampling.

## Boundary

This audit does not prove fill, identify a construction cause, establish placed
thickness, create a depth anchor or validate radar transfer. Records remain a
final confirmation step only after a scientifically accepted spatial group
exists.
