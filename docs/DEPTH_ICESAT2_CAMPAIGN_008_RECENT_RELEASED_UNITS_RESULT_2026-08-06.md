# ICESat-2 Campaign 008 — Final Result and Closure

Date: 2026-08-06

## Controlling decision

Campaign 008 is complete and closed.

The official FDEP recent released-reclamation-unit scan produced no persistent
upward terrain-step candidate, no spatial cluster, and no finalized survivor.

Do not run records research for Campaign 008. Do not spend more time on this
route unless a materially different official data source or method is explicitly
approved.

Numerical depth remains blocked.

## Validation result

The protected-branch focused test set passed:

```text
26 passed in 0.99s
```

## Executed scan

The scan was run from `C:\Dev\New_GEE` with:

```powershell
.\.venv\Scripts\python.exe `
  ..\New_GEE_depth\scripts\scan_icesat2_fdep_recent_released_units_campaign.py `
  --tile-km 25 `
  --timeout-seconds 30
```

Campaign identity:

```text
campaign_id = southeast_us_earthwork_pilot_v8_fdep_recent_released_units
region_id   = fdep_recent_released_phosphate_units
release-year window = 2019–2024
```

## Final scan evidence

```text
bounding-box tiles                         35
official-polygon-intersecting tiles         2
completed tiles                             2
failed tiles                                0
cached tiles                                0
quality segments before polygon filter  82,937
quality segments after deduplication     1,360
segments rejected outside polygons      81,577
exact segment series                       964
series classified insufficient epochs      964
raw upward-step segments                      0
pre-unit-gate clusters                        0
unit-gate rejected clusters                   0
surviving candidate clusters                  0
```

Final machine status:

```text
status = no_surviving_candidates_in_recent_released_units
records_research_ready = false
numerical_depth_unlocked = false
surviving_candidate_count = 0
record_lookup_priority = []
```

## Interpretation

All 964 exact segment series failed at the existing minimum-epoch requirement.
No series reached the upward-step stage, so there was nothing to cluster,
finalize, or investigate through official records.

The scan therefore does not identify a usable reclamation event, placed-material
thickness record target, radar-comparison zone, or calibration row.

No scientific threshold was weakened and no app behavior changed.

## Protected scope remains unchanged

Campaign 008 made no change to:

- classifier behavior;
- frontend result pages;
- Option 5 outputs;
- Tyrone Route A evidence;
- production numerical-depth output;
- `main`; or
- public-record requests.

## Current project status

```text
Campaign 007:              Closed
Campaign 008:              Closed — zero surviving candidates
Tyrone Route A:            Partially supported; external survey control missing
Records research:          Disabled
Usable calibration rows:   0
Numerical depth:           Still blocked
```

## Next action

Stop Campaign 008 work.

Continue only the existing Tyrone Route A survey-control path when new external
coordinate transformation, survey control, or equivalent official evidence is
available.

A Campaign 009 or any new discovery route requires explicit user approval before
implementation or scanning.
