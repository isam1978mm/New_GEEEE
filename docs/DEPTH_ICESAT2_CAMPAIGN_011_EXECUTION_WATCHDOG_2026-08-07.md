# Campaign 011 execution watchdog — 2026-08-07

## Why this execution-only fix exists

The first live Campaign 011 run completed and cached 85 official-polygon scan tiles, then stopped creating new cache files for approximately four hours. This indicates one uncached SlideRule ATL08 tile request stalled rather than the whole scientific campaign failing.

The original `--timeout-seconds` argument protects the PA DEP ArcGIS polygon request. It does not impose a wall-clock timeout on the underlying SlideRule `atl08x` request used for each ICESat-2 tile.

## Approved scope

This fix changes Campaign 011 execution only. It does not change:

- ICESat-2 temporal thresholds;
- minimum step height;
- plateau stability thresholds;
- step dominance;
- 250 m neighbour distance;
- minimum neighbouring-segment count;
- cluster NMAD gate;
- context/finalizer requirements;
- PA DEP `Reclamation Complete` polygon gate;
- the 40 m eventual-footprint envelope pre-screen;
- the classifier, frontend, Option 5, Tyrone route, or main application behavior.

## Mechanism

`scripts/run_icesat2_pa_aml_campaign_011_with_tile_watchdog.py` imports the approved Campaign 011 scanner and replaces only its live ATL08 query hook.

Each uncached ATL08 tile query runs in a separate subprocess with a 300-second wall-clock timeout.

- Successful tiles are returned to the existing Campaign 011 scanner and written to the normal cache.
- Existing successful cache files remain valid and are reused.
- A query exceeding 300 seconds is terminated and becomes a normal failed-tile record instead of hanging the statewide campaign indefinitely.
- Other child-process query errors are surfaced to the existing per-tile failure handling.

## Scientific decision rule remains unchanged

A run with any failed tile is incomplete and cannot be closed scientifically. Only the failed tile(s) should be retried. A zero-failed-tile run can be interpreted under the existing Campaign 011 candidate/cluster/finalizer rules.

## First interrupted-run state

Observed before the watchdog fix:

- cached completed tiles: 85;
- newest cache timestamp: 2026-08-07 17:18:56 local time;
- user stopped the still-running process after more than four hours with no additional tile cache written;
- Campaign 011 scientific result: not yet decided;
- usable calibration rows: 0;
- numerical depth: blocked.
