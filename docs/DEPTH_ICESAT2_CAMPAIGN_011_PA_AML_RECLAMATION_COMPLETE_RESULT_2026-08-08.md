# Campaign 011 — PA DEP Reclamation-Complete AML Result

Date: 2026-08-08

## Decision

**CLOSED — no surviving candidates.**

Campaign 011 completed successfully after the cached-tile resume. The run produced no raw persistent upward-step series, no spatial clusters, and no surviving candidates. It does not add any usable numerical-depth calibration row.

Numerical depth remains blocked.

## Validation

Focused Campaign 011 validation before the resumed run:

- 12 tests passed
- 0 failed

## Execution clarification

The Pennsylvania bounding-box grid contained 198 possible 25 km tiles, but only 85 tiles intersected the eligible official PA DEP `Reclamation Complete` AML polygons and therefore entered the polygon-constrained scan.

All 85 selected polygon tiles completed successfully:

- selected polygon tiles: 85
- completed polygon tiles: 85
- cached polygon tiles reused on resumed run: 85
- failed tiles: 0
- scanner exit code: 0

The original long-running attempt had already written all 85 selected tile caches. Therefore the earlier working diagnosis that the process had stalled on an uncached "tile 86" was incorrect. The successful watchdog run reused all 85 caches and completed the downstream aggregation/classification stage.

## Scientific result

Campaign ID:

`northeast_us_earthwork_pilot_v11_pa_aml_reclamation_complete`

Region ID:

`pa_dep_reclamation_complete_aml_polygons`

Official spatial/status gate:

- source: Pennsylvania DEP eMapPA AML Polygon Feature
- accepted status: `Reclamation Complete`
- minimum polygon-component envelope screen: 40 m
- status treated only as official spatial/activity context, not as construction date or depth

Final counts:

- bounding-box tile count: 198
- selected polygon tile count: 85
- completed tile count: 85
- failed tile count: 0
- quality segments before polygon filter: 1,850,511
- quality segments after polygon filtering/deduplication: 6,541
- segments rejected outside PA DEP AML polygons: 1,843,970
- exact segment series: 6,291
- classification `insufficient_epochs`: 6,291
- raw step-up segment count: 0
- pre-polygon-identity clusters: 0
- polygon-identity-gate rejections: 0
- surviving step clusters: 0
- surviving candidates: 0

All 6,291 exact segment series failed the minimum repeat-epoch requirement before any upward-step candidate could form.

## Interpretation

This is a valid negative campaign result, not an incomplete run:

- there were no failed selected tiles;
- all eligible polygon-intersecting tiles completed;
- no raw upward-step series survived the repeat-series gate;
- therefore no spatial cluster, finalizer candidate, or records-research candidate exists for Campaign 011.

Do not weaken the minimum-epoch requirement or any other scientific threshold to manufacture a candidate.

## Calibration impact

- new usable calibration rows: 0
- total currently usable calibration rows: 0
- numerical depth unlocked: **NO**
- records research for Campaign 011: **NOT WARRANTED**
- classifier/frontend/Option 5/Tyrone/main: **UNCHANGED**

## Parallel Tyrone route

The separately approved Tyrone Route A remains pending the new EMNRD public-records request. Campaign 011 does not change that route's status.

## Next action

Do not start Campaign 012 automatically. A new independent campaign requires explicit user approval.
