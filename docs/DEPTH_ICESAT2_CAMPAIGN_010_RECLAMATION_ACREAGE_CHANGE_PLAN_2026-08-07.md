# ICESat-2 Campaign 010 — FDEP Reclamation Acreage Change

Date: 2026-08-07

## Approval

The user explicitly approved running both paths in parallel after the existing Tyrone production was fully inspected:

1. Route A: the user will send the narrow EMNRD follow-up for the remaining Tyrone survey-control/stability records; and
2. Campaign 010: continue an independent discovery search without waiting for an EMNRD response.

No email is sent by this campaign. Campaign 010 is independent of Tyrone.

## Campaign 009 result carried forward

Campaign 009 completed with no failed tiles and materially more repeat coverage than Campaign 008:

```text
quality segments after polygon filtering/deduplication = 44,116
exact segment series                                  = 23,912
raw step-up segment series                            = 19
pre-unit-gate spatial clusters                        = 0
surviving candidates                                  = 0
usable calibration rows                               = 0
numerical depth                                       = still blocked
```

Campaign 009 therefore closed scientifically. The 19 individual upward-step series did not satisfy the unchanged spatial-support gate and must not be promoted by weakening neighbour or cluster thresholds.

## Campaign 010 controlling decision

Campaign 010 changes the official activity constraint, not the scientific thresholds.

Instead of selecting reclamation units only from one annual status snapshot, Campaign 010 compares the official FDEP annual Mandatory Phosphate Reclamation Units layers for:

```text
2018 = layer 6
2019 = layer 7
2020 = layer 8
2021 = layer 9
```

A unit is eligible only when the same stable reclamation-unit identity has a documented positive year-over-year increase in the official `TOTALACRECL` field across at least one consecutive annual pair.

Stable identity is based on:

```text
SITE_ID + normalized REC_UNITS
```

Ambiguous duplicate identities within the same annual layer are excluded rather than guessed.

This activity filter is deliberately different from Campaign 009:

- Campaign 009 used `REC_STATUS IN ('WP','WC')` in the 2021 snapshot;
- Campaign 010 uses an observed increase in reported reclaimed acreage across annual official datasets;
- Campaign 010 can therefore include units whose useful reclamation activity is visible in an earlier annual transition even if the 2021 status snapshot alone is not sufficient.

A positive acreage change is still only regulatory/activity evidence. It is not a construction date, placed-material thickness, or depth anchor.

## Official source

```text
FDEP OpenData/MMP_RECLUNITS
https://ca.dep.state.fl.us/arcgis/rest/services/OpenData/MMP_RECLUNITS/MapServer
```

Annual layers used:

```text
2018: /6
2019: /7
2020: /8
2021: /9
```

Relevant official fields include:

```text
MINE_OPERATOR
MINE_NAME
SITE_ID
REC_UNITS
REC_STATUS
GIS_ACRES
AR_YEAR
RELEASESTATUS
MINEDACRES
MINEDANDRECL
DISTANDRECL
TOTALACRECL
COMMENTS
```

The FDEP geometry remains planning/regulatory GIS, not engineering-grade as-built survey evidence. Any final survivor still requires exact plans/as-builts, measured placed-material thickness, clean geometry, and radar comparability before it can become a calibration row.

## Campaign identity

```text
campaign_id = southeast_us_earthwork_pilot_v10_fdep_reclamation_acreage_change
region_id   = fdep_reclamation_acreage_change_2018_2021
```

Scanner:

```text
scripts/scan_icesat2_fdep_reclamation_acreage_change_campaign.py
```

Tests:

```text
tests/unit/test_scan_icesat2_fdep_reclamation_acreage_change_campaign.py
```

## Activity-selection method

Campaign 010 will:

1. query the official 2018, 2019, 2020, and 2021 reclamation-unit layers over the unchanged Central Florida bounds;
2. validate every response as an official polygon FeatureCollection;
3. normalize unit identities with `SITE_ID + REC_UNITS`;
4. reject identities that are duplicated ambiguously within an annual layer;
5. compare `TOTALACRECL` for consecutive available years;
6. retain only units with at least one strictly positive official year-over-year reclaimed-acre increase;
7. retain the latest official polygon associated with a positive transition;
8. attach the full observed annual status/reclaimed-acre history and positive transition metadata;
9. build the normal resumable 25 km tile grid;
10. reject every tile outside the retained activity polygons;
11. query/deduplicate ATL08 observations and reject observations outside those polygons;
12. apply all existing repeat-series, upward-step, neighbour, cluster, context, terminal-stability, and temporal-recovery gates unchanged;
13. require every supporting segment in a surviving cluster to share exactly one stable activity-qualified unit; and
14. keep records research disabled until a candidate survives the mandatory downstream finalizer.

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

Mandatory finalizer remains unchanged:

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

Campaign 010 must not modify:

- classifier behavior;
- frontend result pages;
- Option 5;
- Tyrone evidence or Tyrone production artifacts;
- production numerical-depth output;
- `main`; or
- the EMNRD follow-up request.

Always keep:

```text
records_research_ready = false
numerical_depth_unlocked = false
candidate_is_depth_anchor = false
```

until all downstream evidence gates are independently satisfied.

## Decision after scan

### No spatial candidates

Close Campaign 010 and report the complete counts. Do not weaken thresholds and do not automatically start Campaign 011.

### Spatial candidates found

Run the existing mandatory finalizer. Only a finalized context-review survivor may proceed to exact activity-window verification and official placed-thickness/as-built research.

### Finalized survivor with records support

It is still not a calibration row until measured finite thickness, exact usable geometry, stable radar observation period, and surface comparability all pass.
