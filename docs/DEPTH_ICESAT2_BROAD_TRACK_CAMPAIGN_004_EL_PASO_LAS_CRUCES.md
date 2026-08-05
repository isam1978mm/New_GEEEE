# ICESat-2 Broad Track Campaign 004 — El Paso–Las Cruces

Status: CLOSED. Campaign 004 completed on 2026-08-05 with four persistent large-magnitude terrain-step candidates and zero context-review survivors.

## Final result

The approved scan and mandatory finalizer completed successfully:

```text
completed_tile_count              = 25
failed_tile_count                 = 0
source_spatial_candidate_count    = 4
temporal_recovery_rejected_count  = 0
terminal_stability_rejected_count = 0
context_priority_deferred_count   = 4
context_review_candidate_count    = 0
surviving_candidate_count         = 0
record_lookup_priority            = []
records_research_ready            = false
status                            = all_temporal_survivors_deferred_by_context_priority
```

Candidate median rises:

```text
candidate 001 = 19.07305908203125 m
candidate 002 = 16.53967285156250 m
candidate 003 = 12.45123291015625 m
candidate 004 = 12.67285156250000 m
```

All four candidates passed temporal-recovery and terminal-stability checks. All four were correctly deferred by the unchanged 5 m context-priority magnitude ceiling. None is a measured placed-material thickness or numerical-depth anchor.

No records research, email, or public-records request is authorized from this result.

Authoritative automated output:

```text
data/research/icesat2_broad_track_scan/
southwest_us_earthwork_pilot_v4_el_paso_las_cruces/
campaign_finalized_summary.json
```

## Purpose and identity

Campaign 004 continued independent ATL08 terrain-step discovery after Campaigns 001–003 produced no usable depth anchor.

```text
campaign_id = southwest_us_earthwork_pilot_v4_el_paso_las_cruces
region_id   = el_paso_las_cruces_lower_rio_grande_pilot
```

Configuration:

```text
config/icesat2_broad_track_campaign_v4_el_paso_las_cruces.json
```

Bounds:

```text
west  = -107.25
south =   31.76
east  = -106.05
north =   32.76
```

## Scientific gates used

```text
minimum distinct epochs          = 4
minimum observations per side    = 2
minimum upward step              = 0.30 m
maximum plateau NMAD             = 0.25 m
minimum dominant-jump fraction   = 0.60
neighbour connection distance    = 250 m
minimum neighbouring segments    = 3
maximum cluster step NMAD        = 0.25 m
cross-spot diagnostic distance   = 500 m
maximum context step             = 5.00 m
```

The finalizer also applied:

1. temporal-recovery audit;
2. immediate and terminal stability audit;
3. context-priority audit.

A spatial or temporal survivor was never treated as a depth anchor.

## Reproduction commands

Validation:

```powershell
cd C:\Dev\New_GEE

.\.venv\Scripts\python.exe -m pytest `
  ..\New_GEE_depth\tests\unit\test_icesat2_broad_track_campaign_v4_config.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_broad_track_campaign.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_broad_track_finalizer.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_candidate_terminal_stability.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_candidate_temporal_recovery.py -q
```

Scan:

```powershell
.\.venv\Scripts\python.exe `
  ..\New_GEE_depth\scripts\scan_icesat2_broad_track_campaign.py `
  --campaign-file `
  ..\New_GEE_depth\config\icesat2_broad_track_campaign_v4_el_paso_las_cruces.json `
  --tile-km 25
```

Finalization:

```powershell
.\.venv\Scripts\python.exe `
  ..\New_GEE_depth\scripts\finalize_icesat2_broad_track_candidates.py `
  --campaign-dir `
  .\data\research\icesat2_broad_track_scan\southwest_us_earthwork_pilot_v4_el_paso_las_cruces
```

## Protection boundary

Campaign 004 did not modify:

- classifier behavior;
- frontend result pages;
- Option 5 outputs;
- production numerical-depth output;
- `main`.

Campaign 005 is the active independent geographic search route. Tyrone Route A remains limited to attachments already requested.
