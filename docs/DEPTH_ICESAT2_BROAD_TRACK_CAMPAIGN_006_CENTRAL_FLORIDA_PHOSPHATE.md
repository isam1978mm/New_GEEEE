# ICESat-2 Broad Track Campaign 006 — Central Florida Phosphate District

Status: ACTIVE. Campaign 006 follows Campaign 005, which completed with eight successful tiles, three isolated step-up segments, zero spatial clusters, and zero surviving candidates.

## Why Campaign 006 exists

Campaign 005 completed successfully but did not provide a usable calibration candidate:

```text
completed_tile_count           = 8
failed_tile_count              = 0
raw_step_up_segment_count      = 3
surviving_step_cluster_count   = 0
surviving_candidate_count      = 0
record_lookup_priority         = []
```

The three step-up segments were isolated and correctly rejected by the unchanged neighbour filter. No temporal, stability, context, parcel, or records work is needed for Campaign 005.

Campaign 006 moves to the low-relief Central Florida Bone Valley phosphate mining and reclamation district. Active mines, reclaimed lands, wetlands, agriculture, industrial facilities, and developed land are discovery context only. They do not prove engineered fill or measured placed-material thickness.

## Campaign identity

```text
campaign_id = southeast_us_earthwork_pilot_v6_central_florida_phosphate
region_id   = central_florida_bone_valley_phosphate_pilot
```

Configuration:

```text
config/icesat2_broad_track_campaign_v6_central_florida_phosphate.json
```

Bounds:

```text
west  = -82.20
south =  27.20
east  = -81.55
north =  28.20
```

The region is geographically separate from Campaigns 001–005 and is processed in WGS 84 / UTM zone 17N (`EPSG:32617`).

## Unchanged first-stage scientific gates

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
```

The unchanged later gates remain mandatory:

1. temporal-recovery audit;
2. immediate and terminal stability audit;
3. context-priority audit with the 5 m magnitude ceiling;
4. Earth Engine land-cover context only for a surviving context-review candidate;
5. exact project-footprint review before any records research.

A spatial or temporal survivor is not a depth anchor.

## Validation command

From `C:\Dev\New_GEE`:

```powershell
.\.venv\Scripts\python.exe -m pytest `
  ..\New_GEE_depth\tests\unit\test_icesat2_broad_track_campaign_v6_config.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_broad_track_campaign.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_broad_track_finalizer.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_candidate_terminal_stability.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_candidate_temporal_recovery.py -q
```

## Scan command

```powershell
.\.venv\Scripts\python.exe `
  ..\New_GEE_depth\scripts\scan_icesat2_broad_track_campaign.py `
  --campaign-file `
  ..\New_GEE_depth\config\icesat2_broad_track_campaign_v6_central_florida_phosphate.json `
  --tile-km 25
```

The tile cache is resumable. Re-running the same command reuses successful cached tiles unless `--force` is supplied.

## Mandatory finalization command

Run only if the scan produces one or more spatial candidates:

```powershell
.\.venv\Scripts\python.exe `
  ..\New_GEE_depth\scripts\finalize_icesat2_broad_track_candidates.py `
  --campaign-dir `
  .\data\research\icesat2_broad_track_scan\southeast_us_earthwork_pilot_v6_central_florida_phosphate
```

Authoritative automated output:

```text
data/research/icesat2_broad_track_scan/
southeast_us_earthwork_pilot_v6_central_florida_phosphate/
campaign_finalized_summary.json
```

## Decision rules

- No spatial candidates: close Campaign 006.
- All candidates fail temporal or terminal stability: close with zero survivors.
- All temporal survivors exceed context gates: defer them without records research.
- Context-review candidates remain: inspect land cover and exact footprint first while keeping records research disabled.

Always keep:

```text
record_lookup_priority = []
records_research_ready = false
candidate_is_depth_anchor = false
```

until a named engineered project, complete supporting line, event window, exact footprint, and measured placed-material thickness are independently documented.

## Protection boundary

Campaign 006 does not modify:

- classifier behavior;
- frontend result pages;
- Option 5 outputs;
- production numerical-depth output;
- `main`;
- Tyrone Route A or Route B records.

No new emails or public-records requests are authorized.
