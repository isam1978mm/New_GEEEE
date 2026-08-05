# ICESat-2 Broad Track Campaign 005 — Tucson–Marana

Status: ACTIVE. Campaign 005 was approved by the user on 2026-08-05 after Campaign 004 completed with four persistent but extreme-magnitude candidates and zero context-review survivors.

## Why Campaign 005 exists

Campaign 004 completed successfully but did not provide a usable calibration candidate:

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
```

The four Campaign 004 rises were persistent, but their median magnitudes were 12.45 m to 19.07 m. They were correctly deferred by the unchanged 5 m context-priority ceiling and were not promoted to depth anchors.

Campaign 005 moves to a new lower-relief Sonoran Desert basin corridor. Development, transportation, flood-control, industrial, agricultural, and open-desert land uses are search context only. They do not prove engineered fill or measured placed-material thickness.

## Campaign identity

```text
campaign_id = southwest_us_earthwork_pilot_v5_tucson_marana
region_id   = tucson_marana_santa_cruz_valley_pilot
```

Configuration:

```text
config/icesat2_broad_track_campaign_v5_tucson_marana.json
```

Bounds:

```text
west  = -111.30
south =   31.90
east  = -110.80
north =   32.75
```

The region is geographically separate from Campaign 004 and is processed in WGS 84 / UTM zone 12N (`EPSG:32612`).

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
  ..\New_GEE_depth\tests\unit\test_icesat2_broad_track_campaign_v5_config.py `
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
  ..\New_GEE_depth\config\icesat2_broad_track_campaign_v5_tucson_marana.json `
  --tile-km 25
```

The tile cache is resumable. Re-running the same command reuses successful cached tiles unless `--force` is supplied.

## Mandatory finalization command

```powershell
.\.venv\Scripts\python.exe `
  ..\New_GEE_depth\scripts\finalize_icesat2_broad_track_candidates.py `
  --campaign-dir `
  .\data\research\icesat2_broad_track_scan\southwest_us_earthwork_pilot_v5_tucson_marana
```

Authoritative automated output:

```text
data/research/icesat2_broad_track_scan/
southwest_us_earthwork_pilot_v5_tucson_marana/
campaign_finalized_summary.json
```

## Decision rules

- No spatial candidates: close Campaign 005.
- All candidates fail temporal or terminal stability: close with zero survivors.
- All temporal survivors exceed context gates: close or defer them without records research.
- Context-review candidates remain: inspect land cover and exact footprint first while keeping records research disabled.

Always keep:

```text
record_lookup_priority = []
records_research_ready = false
candidate_is_depth_anchor = false
```

until a named engineered project, complete supporting line, event window, exact footprint, and measured placed-material thickness are independently documented.

## Protection boundary

Campaign 005 does not modify:

- classifier behavior;
- frontend result pages;
- Option 5 outputs;
- production numerical-depth output;
- `main`;
- Tyrone Route A or Route B records.

No new emails or public-records requests are authorized.
