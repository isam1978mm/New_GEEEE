# ICESat-2 Campaign 009 — Active Reclamation Units Result

Date: 2026-08-07

## Final result

Campaign 009 completed successfully after all focused tests passed.

Validation:

```text
31 passed
```

Scan outcome:

```text
Tiles scanned:                         7
Failed tiles:                          0
Quality segments before polygon gate:  328,574
Quality segments after polygon gate:   44,116
Exact segment series:                  23,912
Insufficient epochs:                   21,455
Irregular or noise:                     1,975
Ramp up:                                  444
Stable:                                    16
Step-down candidates:                       3
Raw step-up candidates:                     19
Spatial clusters before unit gate:           0
Surviving candidate clusters:                0
Records research ready:                  false
Numerical depth unlocked:                false
```

## Controlling interpretation

Campaign 009 materially improved observation coverage compared with Campaign 008 and produced 19 raw `step_up_candidate` segment series. However, none satisfied the existing spatial-neighbour cluster requirement. Therefore no candidate reached the named-unit gate or downstream finalizer.

The official result is:

```text
status = no_surviving_candidates_in_active_reclamation_units
surviving_candidate_count = 0
pre_unit_gate_cluster_count = 0
unit_gate_rejected_count = 0
```

The 19 raw step-up series are not calibration anchors and must not be promoted to records research because the approved Campaign 009 plan requires spatially supported clusters before any downstream records work.

## Closure decision

Campaign 009 is closed.

Do not:

- rerun Campaign 009 with weaker thresholds;
- use `--force` to repeat the completed scan;
- run records research for the 19 isolated raw step-up series;
- change classifier, frontend, Option 5, Tyrone evidence, or production numerical-depth behavior; or
- treat any Campaign 009 observation as a depth anchor.

## Current depth status

```text
Campaign 007:             Closed
Campaign 008:             Closed
Campaign 009:             Closed
Tyrone Route A:           Partially supported; external/global survey control still missing
Usable calibration rows:  0
Numerical depth:           Still blocked
Records research:         Disabled for Campaign 009
```

## Next action

Return to the existing Tyrone Route A survey-control path unless the user explicitly authorizes a new Campaign 010.

A Campaign 010 must be separately approved before implementation or scanning.
