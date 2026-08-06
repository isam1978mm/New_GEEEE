# ICESat-2 Campaign 009 — Active Reclamation Units

Date: 2026-08-06

## Approval

The user explicitly approved Campaign 009 with `go` after Campaign 008 completed successfully with zero surviving candidates.

## Campaign 008 result carried forward

Campaign 008 queried two polygon-intersecting tiles and retained 1,360 quality ATL08 segments after polygon filtering and deduplication. Those observations formed 964 exact segment series, but every series was classified `insufficient_epochs`. No raw upward-step segment, spatial cluster, finalized candidate, or records-research target survived.

Therefore:

```text
Campaign 008:          Closed
Surviving candidates: 0
Records research:      Disabled
Usable calibration rows: 0
Numerical depth:       Still blocked
```

## Campaign 009 controlling decision

Campaign 009 is a new independent discovery campaign constrained to official FDEP 2021 mandatory-phosphate reclamation units whose official reclamation status is either:

```text
WP = Work in Progress
WC = Work Complete
```

The campaign excludes:

```text
WF = Work Future
WS = Work Scheduled
ND = Not Disturbed
NMP = Non-Mandatory Programs
OTH = Other
```

This changes only the official polygon target. It does not weaken or alter any temporal, stability, neighbour, cluster, context, or finalization threshold.

## Why this is the next campaign

Campaign 007 used broad active-mine boundaries and produced one finalized terrain candidate, but the candidate fell inside a `Work Future` unit with no supporting event-window activity.

Campaign 008 corrected the geometry to recently released units, but only two 25 km tiles intersected the selected polygons and all 964 retained series lacked enough repeat epochs.

Campaign 009 keeps exact named reclamation-unit geometry while expanding the search to units where FDEP reports reclamation work as in progress or complete. This is broader than the recent-release-year subset without returning to broad mine boundaries or future-work units.

## Official source

```text
FDEP OpenData/MMP_RECLUNITS
Mandatory Phosphate 2021 - Reclamation Units
Layer 9
https://ca.dep.state.fl.us/arcgis/rest/services/OpenData/MMP_RECLUNITS/MapServer/9
```

The layer contains official unit geometry and fields including mine operator, mine name, site ID, reclamation-unit name, reclamation status, GIS acreage, annual-report year, mined acres, reclaimed-acre fields, released-acre fields, and total acres reclaimed.

The layer is conceptual planning and regulatory-status GIS, not engineering-grade survey evidence. Any survivor still requires exact approved plans, annual reports, as-built surveys, and placed-material thickness records before it can become a calibration row.

## Campaign identity

```text
campaign_id = southeast_us_earthwork_pilot_v9_fdep_active_reclamation_units
region_id   = fdep_work_in_progress_complete_phosphate_units
```

Scanner:

```text
scripts/scan_icesat2_fdep_active_reclamation_units_campaign.py
```

Tests:

```text
tests/unit/test_scan_icesat2_fdep_active_reclamation_units_campaign.py
```

## Campaign method

Campaign 009 will:

1. query the official FDEP 2021 reclamation-unit layer;
2. retain only polygons whose `REC_STATUS` is `WP` or `WC`;
3. build the normal resumable 25 km tile grid;
4. reject every tile outside the retained unit polygons;
5. query ATL08 only for retained tiles;
6. deduplicate returned observations;
7. reject every ATL08 observation outside the retained unit polygons;
8. apply all existing repeat-series, step, neighbour, cluster, context, terminal-stability, and temporal-recovery gates unchanged;
9. reject any cluster whose supporting segments do not all share exactly one named official unit; and
10. write unit metadata into candidate and campaign outputs.

## Unchanged scientific gates

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

The mandatory finalizer remains unchanged:

```text
maximum net fraction             = 0.50
minimum recovery fraction        = 0.60
minimum retention fraction       = 0.50
minimum reversal fraction        = 0.60
minimum follow-up fraction       = 0.60
maximum context step             = 5.0 m
minimum context segment count    = 4
maximum context event window     = 730 days
```

## Protection boundary

Campaign 009 must not modify:

- classifier behavior;
- frontend result pages;
- Option 5;
- Tyrone evidence;
- production numerical-depth output;
- `main`; or
- any public-record request.

Always keep:

```text
records_research_ready = false
numerical_depth_unlocked = false
candidate_is_depth_anchor = false
```

until all downstream evidence gates are independently satisfied.

## Validation command

Run from `C:\Dev\New_GEE`:

```powershell
.\.venv\Scripts\python.exe -m pytest `
  ..\New_GEE_depth\tests\unit\test_scan_icesat2_fdep_active_reclamation_units_campaign.py `
  ..\New_GEE_depth\tests\unit\test_scan_icesat2_fdep_recent_released_units_campaign.py `
  ..\New_GEE_depth\tests\unit\test_scan_icesat2_fdep_polygon_campaign.py `
  ..\New_GEE_depth\tests\unit\test_scan_icesat2_fdep_polygon_campaign_tile_fix.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_broad_track_finalizer.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_candidate_terminal_stability.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_candidate_temporal_recovery.py -q
```

Expected after implementation:

```text
31 passed
```

## Scan command

```powershell
.\.venv\Scripts\python.exe `
  ..\New_GEE_depth\scripts\scan_icesat2_fdep_active_reclamation_units_campaign.py `
  --tile-km 25 `
  --timeout-seconds 30
```

Do not use `--force`. The tile cache is resumable.

## Decision after scan

### No unit-constrained spatial candidates

Close Campaign 009. Do not run records research.

### Spatial candidates found

Run the existing mandatory finalizer. Only a finalized context-review survivor may proceed to exact unit/activity-window verification and official records research.
