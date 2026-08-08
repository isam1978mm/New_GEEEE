# Campaign 014 — Partial-Read Retry Layer

Date: 2026-08-08
Branch: `claude/depth-measurement-unblock-p2zjpd`
Status: EXECUTION RECOVERY / CAMPAIGN STILL OPEN

## Trigger

The strict Campaign 014 rebuild correctly rejected both selected ATL08 tiles because SlideRule returned partial data while reporting H5Coro resource-read failures.

Observed strict result:

- selected tiles: 2
- completed tiles: 0
- failed tiles: 2
- scanner exit code: 1
- campaign status: `epa_hidden_lane_recent_earthwork_scan_incomplete`

The important failed resources were:

- `ATL08_20251226145703_01873002_007_01.h5`, with a `gt3r` latitude read failure;
- `ATL08_20210504235905_06291102_007_01.h5`, with latitude read failures across all six beams on the second tile.

The 2021 resource is in the pre-OU3 baseline period. Because the earlier partial-data run classified all retained exact series as `insufficient_epochs`, accepting that partial result could hide a valid repeat history.

## Recovery change

Campaign 014 now gives every live ATL08 tile up to three independent full-query attempts.

For each attempt:

1. run the existing ATL08 tile request in the existing subprocess watchdog;
2. preserve the existing 300-second wall-clock limit;
3. capture worker stdout/stderr;
4. reject the attempt if SlideRule reports `Failure on resource` or `H5Coro::Future read failure`;
5. retry the full tile after a partial-read alert;
6. cache the tile only if one attempt returns with no resource/H5Coro read alert.

If all three attempts remain partial, the tile is recorded as failed and Campaign 014 remains incomplete.

## Scientific scope

This is execution recovery only. It does not change:

- minimum distinct epochs;
- minimum observations per side;
- minimum upward step;
- plateau NMAD limit;
- dominant-jump fraction;
- neighbour distance or neighbour count;
- cluster NMAD;
- cross-spot diagnostic distance;
- mandatory finalizer;
- terminal-stability or temporal-recovery gates;
- EPA Hidden Lane polygon gate;
- documented OU3 2023-09-11 through 2025-11-06 event-window gate;
- classifier/frontend/Option 5/Tyrone/main.

## Decision after retry

### One clean attempt per tile

Use the rebuilt campaign summary as the scientific Campaign 014 result.

### One or more tiles still partial after three attempts

Campaign 014 remains incomplete on the SlideRule ATL08 route. Do not describe it as zero candidates. The next recovery step must be a different data-access route or a documented unrecoverable-source decision; scientific thresholds must not be weakened.
