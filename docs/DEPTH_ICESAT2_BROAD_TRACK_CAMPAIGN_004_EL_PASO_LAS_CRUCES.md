# ICESat-2 Broad Track Campaign 004 — El Paso–Las Cruces

Status: configured on the protected depth branch and ready for local validation and execution.

## Purpose

Campaign 004 continues independent ATL08 terrain-step discovery after:

- Campaign 001 produced one spatial candidate that failed temporal-recovery review;
- Campaign 002 produced isolated step-up series but no valid spatial clusters;
- Campaign 003 produced 19 spatial candidates, of which one survived automated context screening and was then closed after Earth Engine and parcel review.

Campaign 003 now has:

```text
context_review_candidate_count = 0
surviving_candidate_count      = 0
record_lookup_priority          = []
records_research_ready          = false
```

Campaign 004 does not alter the scientific thresholds and does not assume that its search area contains a usable thickness anchor.

## Campaign identity

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

The approximately 110 km discovery box covers the US lower Rio Grande corridor around El Paso and Las Cruces. It contains a mixture of urban growth, industrial land, flood-control works, open desert, and agricultural land. Those land uses are search context only; they do not establish an engineered project or measured thickness.

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

The following later gates remain mandatory:

1. temporal-recovery audit;
2. immediate and terminal stability audit;
3. context-priority audit;
4. Earth Engine land-cover context where a candidate survives;
5. exact parcel or project-footprint review before any records research.

A spatial or temporal survivor is not a depth anchor.

## Test command

From `C:\Dev\New_GEE`:

```powershell
.\.venv\Scripts\python.exe -m pytest `
  ..\New_GEE_depth\tests\unit\test_icesat2_broad_track_campaign_v4_config.py `
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
  ..\New_GEE_depth\config\icesat2_broad_track_campaign_v4_el_paso_las_cruces.json `
  --tile-km 25
```

The tile cache is resumable. Re-running the same command reuses successful cached tiles unless `--force` is supplied.

## Mandatory finalization command

```powershell
.\.venv\Scripts\python.exe `
  ..\New_GEE_depth\scripts\finalize_icesat2_broad_track_candidates.py `
  --campaign-dir `
  .\data\research\icesat2_broad_track_scan\southwest_us_earthwork_pilot_v4_el_paso_las_cruces
```

Authoritative automated output:

```text
data/research/icesat2_broad_track_scan/
southwest_us_earthwork_pilot_v4_el_paso_las_cruces/
campaign_finalized_summary.json
```

## Decision rules

### No spatial candidates

Close Campaign 004. No dossier, context audit, parcel review, or records research is needed.

### All spatial candidates fail temporal or stability gates

Close Campaign 004 with zero survivors. Do not research records.

### Automated context-review candidates remain

Only candidates in `context_review_priority` may proceed to land-cover and exact-footprint review. Keep:

```text
record_lookup_priority = []
records_research_ready = false
candidate_is_depth_anchor = false
```

Records research may begin only after one named engineered project matches the complete supporting line, the event window, and a documented measured placed-material thickness.

## Protection boundary

This campaign does not modify:

- classifier behavior;
- frontend result pages;
- Option 5 outputs;
- production numerical-depth output;
- `main`.
