# ICESat-2 scan-first terrain-step workflow

Status: read-only candidate discovery; no depth or cause claim.

## Why this exists

The earlier audits proved that ICESat-2 ATL08 terrain segments repeat with
sub-metre precision across multiple independent cycles at the current run.
The next step is therefore to scan the measured tracks first and research only
places where the terrain history looks like a persistent upward step.

Records are not used during this scan.

## What the scanner does

For every exact ATL08 segment identity, the scanner orders the terrain-height
observations through time and tests all possible interior change points.

It classifies each history as:

- `step_up_candidate`: flat before, one dominant upward jump, flat after;
- `ramp_up`: gradual increase spread across several epochs;
- `stable`: no material change;
- `step_down_candidate`: persistent downward step;
- `irregular_or_noise`: inconsistent or reversible movement;
- `insufficient_epochs`: fewer than four distinct cycles.

A segment-level step is not enough. Surviving clusters must also have:

- at least three neighbouring step segments;
- the same early-cycle/late-cycle event window;
- centres connected within 250 m by default;
- consistent step magnitudes with cluster NMAD no greater than 0.25 m.

The output reports whether another detector spot shows the same event window
nearby, but cross-spot support is not mandatory because a narrow target may be
intersected by only one spot.

## Default screening thresholds

```text
minimum epochs                 = 4
minimum observations per side  = 2
minimum upward step            = 0.30 m
maximum plateau NMAD            = 0.25 m
minimum jump dominance          = 0.60
neighbour connection distance   = 250 m
minimum neighbouring segments   = 3
maximum cluster step NMAD        = 0.25 m
```

These thresholds are discovery filters, not a physical definition of fill.

## Run

```powershell
cd C:\Dev\New_GEE_depth
git pull

cd C:\Dev\New_GEE

.\.venv\Scripts\python.exe ..\New_GEE_depth\scripts\scan_icesat2_terrain_steps.py `
  --run-dir .\data\runs\a4881db6-d92e-4ebc-b628-8a1b089db20b `
  --output-json .\data\runs\a4881db6-d92e-4ebc-b628-8a1b089db20b\icesat2_step_scan.json `
  --output-geojson .\data\runs\a4881db6-d92e-4ebc-b628-8a1b089db20b\icesat2_step_candidates.geojson
```

The two output files are private run-local research artifacts. They are not
registered as app downloads and are not displayed in the frontend.

## Decisive fields

```text
status
classification_counts
raw_step_up_segment_count
surviving_step_cluster_count
surviving_step_clusters
record_lookup_priority
```

Interpretation:

- `no_persistent_upward_steps`: no step pattern survived the time-series test;
- `isolated_steps_rejected_by_neighbor_filter`: apparent steps existed but
  neighbouring terrain did not agree;
- `spatially_supported_step_candidates_found`: research only the listed
  survivors to learn what happened there.

## Scientific boundary

ATL08 terrain classification reduces canopy contamination, and the multi-epoch
shape distinguishes a persistent step from a gradual ramp. It does not prove
that the cause was engineered fill. Buildings, grading, excavation/backfill,
landfill work and other construction can also produce steps.

Records are required only after a candidate survives, to confirm:

- what happened;
- the construction dates;
- the mapped footprint;
- the placed or removed thickness;
- whether the 100 m ATL08 segment was sufficiently covered by the work.

The laser strip remains narrow. Transferring a measured step to surrounding
radar pixels is a separate spatial-uniformity assumption that must be stated
and tested.
