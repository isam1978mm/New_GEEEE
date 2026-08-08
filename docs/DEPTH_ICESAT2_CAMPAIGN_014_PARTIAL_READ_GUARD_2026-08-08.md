# Campaign 014 — Partial ATL08 Read Guard

Date: 2026-08-08
Branch: `claude/depth-measurement-unblock-p2zjpd`
Status: EXECUTION INTEGRITY FIX / CAMPAIGN REMAINS OPEN

## Trigger

The first Campaign 014 live run completed both selected tiles and produced a campaign summary with `failed_tile_count = 0`, but SlideRule printed resource-level H5Coro read failures while those tile queries were running.

Observed alerts included:

- `ATL08_20251226145703_01873002_007_01.h5`, beam `gt3r`;
- `ATL08_20210504235905_06291102_007_01.h5`, all six beams.

The 2021 resource is part of the pre-OU3-earthwork baseline period. The initial Campaign 014 result classified all 30 retained exact segment series as `insufficient_epochs`. Therefore a resource-level read failure could remove an epoch that matters to the minimum-epoch gate.

The initial zero-candidate summary is not accepted as a final scientific closure until the partial-read condition is resolved.

## Fix

The Campaign-014-specific watchdog now captures stdout/stderr from each isolated ATL08 worker process.

A tile is rejected as failed if child output contains either of these resource-read indicators:

- `H5Coro::Future read failure`
- `Failure on resource `

This applies even when SlideRule returns a partial dataframe and the child process exits successfully.

A partial response is therefore not written as a successful tile cache through the normal campaign path.

## Required rerun

The two existing Campaign 014 tile caches were created before this guard existed. They must not be reused for the completeness decision.

Rerun Campaign 014 with `--force` so both selected tiles are rebuilt under the strict partial-read guard.

## Decision rule after strict rerun

- If either tile reports a resource/H5Coro read failure, `failed_tile_count > 0` and Campaign 014 remains incomplete. Do not close as a scientific zero.
- If both tiles complete without resource-read failures, use the rebuilt summary for the normal Campaign 014 decision.
- Do not weaken minimum epochs, step, stability, neighbor, cluster, event-window, finalizer, context, terminal-stability, or temporal-recovery thresholds.

## Protected areas

This change is execution-integrity only. It does not modify:

- classifier behavior;
- frontend behavior;
- Option 5;
- Tyrone Route A;
- `main`;
- Campaign 014 scientific thresholds or EPA event/source gates.

## Current numerical-depth state

Usable calibration rows remain 0. Numerical depth remains blocked.
