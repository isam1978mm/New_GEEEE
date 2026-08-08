# Campaign 013 — Virginia DMLR Regraded Excess-Material Fills

Date: 2026-08-08
Branch: `claude/depth-measurement-unblock-p2zjpd`
Status: APPROVED / PLAN LOCKED

## Objective

Continue the independent public/official calibration-anchor search after Campaign 012 without weakening any scientific gate and without changing application behavior.

Campaign 013 leaves the Florida, Pennsylvania, and OSMRE source routes. It targets Virginia Department of Energy, Division of Mined Land Repurposing (DMLR) official polygon data for:

1. **Excess Material Disposal (Fills)**; and
2. exact reclamation-status polygons whose coded status is **`reg` = Regraded**.

The purpose is to search for persistent ICESat-2 ATL08 upward terrain steps inside engineered mine-fill footprints that are also spatially supported by an official regraded reclamation polygon from the same permit.

## Official sources

Virginia DMLR Current Permits FeatureServer:

- Reclamation Status, layer 0:
  `https://energy.virginia.gov/gis/rest/services/DMLR/CurrentPermits/FeatureServer/0/query`
- Excess Material Disposal (Fills), layer 6:
  `https://energy.virginia.gov/gis/rest/services/DMLR/CurrentPermits/FeatureServer/6/query`

The source service identifies Reclamation Status as polygon data with coded values:

- `dis` = Disturbed
- `reg` = Regraded
- `veg` = Vegetated

The Excess Material Disposal layer is polygon geometry with permit and fill-component identifiers.

## Why this campaign is materially different

Campaigns 007-010 used Florida FDEP phosphate-mine/reclamation data.
Campaign 011 used Pennsylvania completed AML polygons.
Campaign 012 attempted dated OSMRE Phase-I bond-release polygons but closed before ICESat-2 because the in-scope Phase-I records lacked usable bond-status dates.

Campaign 013 instead combines two live Virginia DMLR polygon layers:

- the exact engineered fill footprint; and
- the exact current regraded reclamation-status footprint.

This is intended to improve physical targeting. A fill polygon represents an excess-material disposal area rather than a whole mine or broad reclamation unit, while `Regraded` directly describes a ground-shaping reclamation state.

## Scientific interpretation limits

`Regraded` is **activity/status evidence only**. It does not prove:

- the date regrading occurred;
- placed-material thickness;
- measured depth;
- that an ATL08 upward step was caused by reclamation;
- radar-depth transferability;
- a clean 30-40 m calibration area.

A surviving cluster remains only a terrain-step candidate until all mandatory finalization, records, geometry, measured-thickness, stability, and radar-comparability gates pass.

## Source construction

1. Query all Virginia DMLR Reclamation Status polygons inside the campaign envelope where `Rec_Stat = 'reg'`.
2. Build the set of permit IDs represented by those regraded polygons.
3. Query official Excess Material Disposal (Fills) polygons in the same envelope.
4. Retain only fill polygons whose permit appears in the regraded-permit set.
5. Retain only polygon components whose WGS84 envelope is at least 40 m in both dimensions. This is only a cheap pre-screen and does not prove clean usable width.
6. Preserve both the fill polygons and the regraded polygons in campaign output for audit.

## Spatial integrity gate

ATL08 acquisition and exact-series scanning are constrained to the retained fill polygons.

After normal spatial clustering, every supporting segment in a surviving cluster must:

1. share exactly one official excess-material fill polygon;
2. share exactly one official `Regraded` polygon;
3. have the fill and regraded polygons tied to the same DMLR permit.

Clusters failing any of these conditions are rejected before records research.

## Campaign envelope

Southwest Virginia coal region:

- west: -83.75
- south: 36.45
- east: -80.15
- north: 37.65

These are discovery bounds only. Exact official polygons control retained ATL08 segments.

## Existing scientific gates — unchanged

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

All existing mandatory finalizer, terminal-stability, temporal-recovery, context, and evidence gates remain unchanged.

No scientific threshold may be weakened merely to create a survivor.

## Execution safety

Campaign 013 includes the per-tile subprocess watchdog from the start:

- one live ATL08 tile receives a hard 300-second wall-clock limit;
- completed tiles remain cached and resumable;
- a timed-out tile becomes a recorded failed tile rather than hanging the whole campaign.

A campaign with any failed tile is incomplete and cannot be closed as a scientific zero-result until the failure is resolved or explicitly documented as unrecoverable.

## Decision rules

### A. Official source produces no eligible fill/regraded targets

Close Campaign 013 as a source-target zero. Do not describe this as zero ICESat-2 candidates.

### B. Failed ATL08 tiles > 0

Campaign remains incomplete. Retry/fix only the failures; preserve all completed cache.

### C. No raw upward steps and no failed tiles

Close Campaign 013 with 0 candidates and 0 usable calibration rows. Numerical depth remains blocked.

### D. Raw steps exist but no spatial clusters

Close Campaign 013 as isolated steps rejected by the unchanged neighbour rule. Do not weaken the rule.

### E. Clusters fail fill/regraded identity gate

Close with explicit rejection counts and reasons. No records research.

### F. One or more clusters survive the exact fill + exact regraded + same-permit gate

Treat each as a provisional candidate only. Run the existing mandatory finalizer/terminal-stability/temporal-recovery/context gates before any records research.

### G. Finalized survivor

Research official Virginia DMLR permit/construction/as-built records for:

- construction/regrading dates;
- measured or as-built fill/cover thickness;
- survey control / exact geometry;
- stable post-event area at least roughly 30-40 m wide;
- surface construction and radar comparability.

Only a record-supported measured-thickness site can become a usable calibration row.

## Protected areas

Campaign 013 may not modify:

- classifier behavior or classifier result pages;
- frontend application behavior;
- Option 5 outputs;
- Tyrone Route A records work;
- `main`.

All Campaign 013 work remains isolated on the protected depth branch.

## Numerical-depth rule

Numerical depth remains blocked unless at least two independent usable measured-depth anchors satisfy every required calibration gate.
