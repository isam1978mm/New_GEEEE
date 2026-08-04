# ICESat-2 Broad Track Campaign 003 — Imperial Valley

Status: configured and ready for local validation and execution.

## Purpose

Campaign 003 continues independent ATL08 terrain-step discovery after:

- Campaign 001 produced one spatial candidate that was rejected as temporal recovery;
- Campaign 002 produced 25 isolated step-up series and zero spatial clusters.

This campaign does not alter thresholds and does not search records before finalization.

## Campaign identity

```text
campaign_id = southwest_us_earthwork_pilot_v3_imperial_valley
region_id   = imperial_valley_salton_south_pilot
```

Configuration:

```text
config/icesat2_broad_track_campaign_v3_imperial_valley.json
```

Bounds:

```text
west  = -116.35
south =   32.72
east  = -115.25
north =   33.62
```

The box is an independent discovery heuristic. Its selection is not evidence that a usable thickness anchor exists there.

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

The temporal-recovery finalizer remains mandatory.

## Test command

From `C:\Dev\New_GEE`:

```powershell
.\.venv\Scripts\python.exe -m pytest `
  ..\New_GEE_depth\tests\unit\test_icesat2_broad_track_campaign_v3_config.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_broad_track_campaign.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_broad_track_finalizer.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_candidate_temporal_recovery.py -q
```

## Scan command

```powershell
.\.venv\Scripts\python.exe `
  ..\New_GEE_depth\scripts\scan_icesat2_broad_track_campaign.py `
  --campaign-file `
  ..\New_GEE_depth\config\icesat2_broad_track_campaign_v3_imperial_valley.json `
  --tile-km 25
```

The tile cache is resumable. Re-running the same command reuses successful cached tiles unless `--force` is supplied.

## Mandatory finalization command

```powershell
.\.venv\Scripts\python.exe `
  ..\New_GEE_depth\scripts\finalize_icesat2_broad_track_candidates.py `
  --campaign-dir `
  .\data\research\icesat2_broad_track_scan\southwest_us_earthwork_pilot_v3_imperial_valley
```

Authoritative output:

```text
data/research/icesat2_broad_track_scan/
southwest_us_earthwork_pilot_v3_imperial_valley/
campaign_finalized_summary.json
```

## Decision rules

### No spatial clusters

```text
status = no_surviving_candidates_in_broad_track_campaign
```

Close Campaign 003. No dossier, recovery audit, or records research is needed.

### Spatial clusters found, all recovery-like

```text
status = all_spatial_candidates_rejected_by_temporal_recovery
record_lookup_priority = []
```

Close the candidates. Do not research records.

### Finalized survivor remains

```text
surviving_candidate_count > 0
record_lookup_priority is not empty
```

Only then extract the dossier and begin exact-footprint records research. A finalized survivor is still not a depth anchor until cause, footprint, and measured thickness are confirmed.

## Protection boundary

This campaign must not modify:

- classifier behavior;
- frontend result pages;
- Option 5 outputs;
- production numerical depth output;
- `main`.
