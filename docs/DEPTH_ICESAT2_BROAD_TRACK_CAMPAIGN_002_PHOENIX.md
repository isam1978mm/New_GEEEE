# ICESat-2 broad track Campaign 002 — Phoenix / Lower Gila

Status: ready for local test and live scan on the safe depth branch.

## Decision carried forward from Campaign 001

Campaign 001 found one spatially supported ATL08 terrain-step cluster, but the
mandatory temporal-recovery audit rejected it. All five supporting segments
were closer to the later plateau in the oldest available cycle than to the
immediately pre-event low plateau.

Authoritative Campaign 001 outcome:

```text
source spatial candidates:       1
temporal-recovery rejections:    1
surviving candidates:            0
record lookup priority:          []
numerical depth ready:           no
```

Campaign 002 therefore continues independent candidate discovery. It does not
research Candidate 001 and does not expand around the Campaign 001 footprint.

## Campaign 002 configuration

Campaign file:

```text
config/icesat2_broad_track_campaign_v2_phoenix.json
```

Campaign ID:

```text
southwest_us_earthwork_pilot_v2_phoenix
```

Region ID:

```text
west_phoenix_lower_gila_pilot
```

Bounds:

```text
west  = -113.35
south =   33.10
east  = -112.20
north =   34.00
```

The region is an independent approximately 100 × 100 km discovery box west and
southwest of Phoenix. The location is a search heuristic only. It is not a
claim that a measured earthwork thickness or depth anchor exists there.

## Scientific gates

The initial spatial scanner retains the existing strict gates:

```text
minimum distinct epochs          = 4
minimum observations per side    = 2
minimum upward step              = 0.30 m
maximum plateau NMAD             = 0.25 m
minimum dominant-jump fraction   = 0.60
neighbour distance               = 250 m
minimum neighbouring segments    = 3
maximum cluster step NMAD        = 0.25 m
```

No gate may be lowered to create candidates.

## Mandatory temporal-recovery gate

A spatial survivor is provisional. Before any records research, every survivor
must pass:

```text
scripts/finalize_icesat2_broad_track_candidates.py
```

Default recovery rules:

```text
maximum oldest-to-later net fraction of apparent step = 0.50
minimum recovery-like supporting-segment fraction      = 0.60
```

Only this file is authoritative for records decisions:

```text
data/research/icesat2_broad_track_scan/
  southwest_us_earthwork_pilot_v2_phoenix/
  campaign_finalized_summary.json
```

The raw `campaign_summary.json` remains an audit trail. It must not be used by
itself to start permit, parcel or as-built records research.

## Test command

Run from the main worktree while reading code from the safe depth worktree:

```powershell
cd C:\Dev\New_GEE_depth
git pull

cd C:\Dev\New_GEE

.\.venv\Scripts\python.exe -m pytest `
  ..\New_GEE_depth\tests\unit\test_icesat2_broad_track_campaign_v2_config.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_broad_track_campaign.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_broad_track_finalizer.py `
  ..\New_GEE_depth\tests\unit\test_icesat2_candidate_temporal_recovery.py -q
```

## Live scan command

```powershell
.\.venv\Scripts\python.exe `
  ..\New_GEE_depth\scripts\scan_icesat2_broad_track_campaign.py `
  --campaign-file `
  ..\New_GEE_depth\config\icesat2_broad_track_campaign_v2_phoenix.json `
  --tile-km 25
```

The scanner stores successful tile results under the Campaign 002 directory.
If the process is interrupted or a remote tile fails, rerun the same command.
Successful tile caches will be reused.

## Finalization command

Run this after the spatial scan completes:

```powershell
.\.venv\Scripts\python.exe `
  ..\New_GEE_depth\scripts\finalize_icesat2_broad_track_candidates.py `
  --campaign-dir `
  .\data\research\icesat2_broad_track_scan\southwest_us_earthwork_pilot_v2_phoenix
```

## Interpretation

### No spatial candidates

```text
status = no_surviving_candidates_in_broad_track_campaign
```

Close the region. No records research is warranted.

### Spatial candidates, all rejected by recovery

```text
status = all_spatial_candidates_rejected_by_temporal_recovery
record_lookup_priority = []
```

Close those candidates. No records research is warranted.

### Finalized survivors remain

```text
surviving_candidate_count > 0
record_lookup_priority is not empty
```

Only then inspect the final candidate dossiers and begin targeted official
records research for the exact coordinates and event windows.

A finalized survivor still means only:

```text
spatially supported, lasting ATL08 terrain-step candidate
```

It does not prove:

- engineered fill;
- placed material thickness;
- depth to a buried object;
- radar depth prediction;
- spatial transfer beyond the laser strip.

## Protection boundary

Campaign 002 must not modify:

- the classifier;
- frontend result pages;
- Option 5 surface-change behavior;
- production numerical depth output;
- `main`;
- the Campaign 001 audit trail.
