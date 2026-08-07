# ICESat-2 Campaign 010 — FDEP Reclamation Acreage Change Result

Date: 2026-08-07

## Decision

**Campaign 010 is closed with no surviving candidate. Numerical depth remains blocked.**

The live scan completed all polygon-intersecting tiles with `failed_tile_count = 0`, so this is a complete scientific closure rather than an incomplete scan.

Campaign 010 used official FDEP 2018-2021 reclamation-unit polygons whose `TOTALACRECL` increased across at least one consecutive annual pair. It preserved all previously approved ICESat-2 temporal, stability, neighbour, cluster, context, terminal-stability, and temporal-recovery thresholds.

## Validation

```text
36 tests passed in 4.13 s
```

## Live scan result

```text
bounding-box tiles                         = 35
polygon-intersecting / completed tiles      = 5
failed tiles                                = 0
quality segments before polygon filtering   = 228,059
segments rejected outside official polygons = 218,009
quality segments after filtering/dedup       = 10,050
exact segment series                         = 7,097
```

Classification counts:

```text
insufficient_epochs       = 6,900
irregular_or_noise        =   132
ramp_up                   =    50
stable                    =    12
step_down_candidate       =     2
step_up_candidate         =     1
```

Downstream candidate counts:

```text
raw step-up segment series        = 1
pre-unit-gate spatial clusters    = 0
unit-gate rejected clusters       = 0
surviving step clusters           = 0
surviving candidates              = 0
record lookup priority            = []
records research ready            = false
usable calibration rows           = 0
numerical depth unlocked          = false
```

## Interpretation

Campaign 010 produced one isolated raw upward-step segment series, but it did not satisfy the unchanged spatial-support requirement and therefore did not form a candidate cluster.

The isolated series must not be promoted by weakening the neighbour connection distance, minimum neighbouring segment count, cluster consistency gate, or any later finalizer threshold.

The H5Coro read alerts printed during the live scan did not produce a failed tile. The campaign summary reports `failed_tile_count = 0`, so they do not invalidate this closure.

A reported increase in `TOTALACRECL` is regulatory/activity evidence only. It does not prove a construction date, engineered fill, placed-material thickness, buried-object depth, radar depth prediction, or transferability beyond the ICESat-2 laser strip.

## Protected-scope result

```text
app_behavior_changed        = false
candidate_cause_confirmed   = false
candidate_is_depth_anchor   = false
records_research_ready      = false
numerical_depth_unlocked    = false
```

No classifier, frontend, Option 5, Tyrone evidence, production numerical-depth behavior, or `main` change is authorized by this result.

## Current project status after Campaign 010

```text
Campaign 007      = closed
Campaign 008      = closed
Campaign 009      = closed
Campaign 010      = closed
Tyrone Route A    = pending new EMNRD records request
usable depth rows = 0
numerical depth   = still blocked
```

## Next-action rule

Do not start Campaign 011 automatically. A new independent discovery campaign requires explicit user approval.

The currently active parallel path is Tyrone Route A, where a new EMNRD records request has been submitted for the missing coordinate-system / survey-control transformation and post-2014 TP5/TP6 stability records.
