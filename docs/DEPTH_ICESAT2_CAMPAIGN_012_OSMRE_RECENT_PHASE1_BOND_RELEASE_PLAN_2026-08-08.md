# Depth ICESat-2 Campaign 012 — OSMRE Recent Phase I Bond Release

Date: 2026-08-08

## Decision

Campaign 012 is approved by the user and remains isolated on the protected numerical-depth branch.

Campaign 012 leaves the Florida FDEP and Pennsylvania AML routes used by Campaigns 007-011. It targets a different official federal aggregation: the U.S. Office of Surface Mining Reclamation and Enforcement (OSMRE) GeoMine **Reclamation Bond Status** polygon layer.

The specific campaign screen is:

- reclamation bond status = **Phase I Release**;
- reclamation bond status date = **2019-01-01 through 2024-12-31**;
- regulatory-authority contact code = **1, 2, or 3** (Virginia, West Virginia, Kentucky in the OSMRE layer domain);
- geometry intersecting the central-Appalachia campaign bounds;
- retained polygon components must have at least a 40 m WGS84 envelope span in both directions before ATL08 scanning.

Campaign ID:

`central_appalachia_earthwork_pilot_v12_osmre_recent_phase1_bond_release`

Region ID:

`osmre_recent_phase1_bond_release_central_appalachia`

## Why this is materially different

Campaign 011 used Pennsylvania DEP abandoned-mine-land polygons whose status was `Reclamation Complete`. That source had useful official geometry, but the status itself did not provide a dedicated reclamation-stage date.

Campaign 012 uses OSMRE's national coal-mining reclamation schema. The official `Bond Status` layer provides:

- polygon geometry;
- `reclamation_bond_status`;
- `reclamation_bond_status_date`;
- permit and incremental-area identifiers;
- calculated/reported area;
- regulatory-authority contact; and
- related permit metadata.

OSMRE describes Phase I as the first bond-release stage after the permittee completes backfilling, regrading, and drainage control. This makes a recent Phase I release a stronger regulatory indicator of a completed earthwork/regrading phase than a generic reclaimed-area status.

Official source:

`https://geoservices.osmre.gov/arcgis/rest/services/GeoMine/ReclamationBondStatus/MapServer/0`

OSMRE reclamation-bond explanation:

`https://www.osmre.gov/resources/reclamation-bonds`

## What the Phase I date means — and does not mean

The campaign treats `reclamation_bond_status_date` as an official regulatory date associated with the Phase I release.

It is useful evidence that the applicable bonded area had reached the Phase I reclamation stage by that date.

It is **not** assumed to be:

- the exact day soil or spoil was placed;
- a measured thickness;
- an as-built depth;
- a radar-depth calibration value;
- proof that every point inside the polygon was regraded on one date; or
- proof of a clean 30-40 m calibration footprint.

Any surviving ICESat-2 terrain-step candidate still requires the existing finalizer, temporal-stability/context checks, official record recovery, measured finite thickness, usable geometry, and radar comparability before it can become a calibration row.

## Geographic scope

Default WGS84 bounds:

- west: -85.00
- south: 36.45
- east: -77.00
- north: 40.65

The source query is additionally constrained to OSMRE contact codes 1, 2, and 3, corresponding in the layer domain to:

1. Virginia regulatory authority
2. West Virginia regulatory authority
3. Kentucky regulatory authority

This prevents the bounding rectangle from silently turning Campaign 012 into another Pennsylvania campaign.

## Date scope

Phase I release dates are restricted to 2019-01-01 through 2024-12-31.

Reasons:

- the period overlaps the ICESat-2 operational era;
- it leaves useful post-release observation time through the existing 2026 ATL08 query endpoint;
- it avoids treating very recent 2025-2026 releases as if adequate repeat post-event observations must already exist.

The bond-release date is a screen and metadata anchor, not a substituted construction date.

## Geometry gates

Before querying ATL08, official OSMRE features are filtered to polygon or multipolygon geometry.

For multipolygons, only components with an approximate WGS84 envelope span of at least 40 m in both directions are retained.

This is only a cheap pre-screen. It does **not** prove that a final clean 30-40 m usable calibration footprint exists after removing roads, drains, berms, highwalls, pits, structures, water, or edges.

All ATL08 segments must fall inside retained official OSMRE geometry before repeat-series classification.

Every spatially supported cluster must then have all of its supporting segments inside exactly one common OSMRE Phase I bond-release polygon.

## Scientific thresholds — unchanged

Campaign 012 does not lower any scientific threshold.

The existing terrain-step thresholds remain:

- minimum distinct epochs: 4
- minimum observations per side: 2
- minimum upward step: 0.30 m
- maximum plateau NMAD: 0.25 m
- minimum dominant-jump fraction: 0.60
- neighbour connection distance: 250 m
- minimum neighbouring segments: 3
- maximum cluster step NMAD: 0.25 m
- cross-spot diagnostic distance: 500 m

The existing downstream finalizer/terminal-stability/temporal-recovery rules remain controlling. Campaign 012 must not weaken them to obtain a survivor.

## Execution protection

Campaign 011 demonstrated that a live SlideRule ATL08 call can stall without a wall-clock request timeout.

Campaign 012 therefore ships with a campaign-specific subprocess watchdog from the start:

- completed tiles remain cached;
- cached tiles are reused on restart;
- each uncached ATL08 tile receives a hard wall-clock timeout;
- a timed-out tile becomes a recorded failed tile rather than freezing the full campaign;
- a campaign with any failed tile remains incomplete and cannot be closed as a scientific zero-result.

The default watchdog limit is 300 seconds per uncached ATL08 tile.

This changes execution reliability only. It changes no scientific threshold.

## Required outputs

The campaign must write:

- the retained official OSMRE Phase I polygon GeoJSON;
- tile cache files;
- regional scan JSON;
- candidate GeoJSON;
- campaign summary JSON.

The summary must explicitly report:

- bounding-box tile count;
- selected polygon-intersecting tile count;
- cached/completed/failed tile counts;
- segments before and after polygon filtering;
- exact repeat-series count;
- classification counts;
- raw step-up count;
- pre-identity-gate cluster count;
- identity-gate rejection count;
- surviving candidate count;
- `records_research_ready = false` until a downstream-finalized survivor exists;
- `numerical_depth_unlocked = false` unless the separate two-anchor requirement is actually satisfied.

## Decision rules

### A. Failed tiles

If `failed_tile_count > 0`, Campaign 012 is incomplete. Retry/fix only the failed execution path. Do not interpret incomplete coverage as a scientific zero-result.

### B. No raw step-ups / no clusters / no survivors

If all selected tiles complete with zero failed tiles and no survivor, close Campaign 012 with 0 usable calibration rows. Numerical depth remains blocked. Do not automatically start Campaign 013.

### C. Clusters fail exact polygon identity

Close the candidate path and report the exact rejection count/reason. Do not start records research for rejected clusters.

### D. A survivor remains

A surviving cluster is only a candidate. It must pass the existing finalizer, terminal-stability, temporal-recovery, context, geometry, records, measured-thickness, and radar-comparability gates before it can become a usable calibration row.

### E. Depth unlock

Never state that numerical depth is unlocked unless at least two independent usable measured-depth anchors satisfy the full calibration requirements.

## Protected areas

Campaign 012 must not modify:

- classifier behavior or classifier UI;
- frontend behavior;
- Option 5 outputs;
- Tyrone records analysis;
- the main branch;
- numerical-depth scientific thresholds.

The Tyrone EMNRD request continues independently in parallel.

## Stop condition

Campaign 012 ends when either:

1. the complete polygon-constrained scan closes with no surviving candidate; or
2. a surviving candidate moves into the already-approved finalizer/records-evidence path.

A Campaign 013 requires separate explicit user approval.