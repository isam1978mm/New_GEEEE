# Campaign 012 — OSMRE live-source compatibility fix

Date: 2026-08-08

## Trigger

The first live Campaign 012 execution passed all 14 local tests but stopped before ICESat-2 acquisition with:

`no eligible OSMRE 2019-2024 Phase I release polygons intersect the bounds`

No `campaign_summary.json` or tile cache was created. Scanner exit code was 2.

## Interpretation

This is a source-selection/preflight failure, not a scientific terrain-step result. The live OSMRE layer exposes the expected fields and coded values, but the original implementation placed the entire Phase-I + contact + date filter in the ArcGIS server-side `where` clause. A zero response therefore did not distinguish a true zero-target result from server-side SQL/date-filter behavior.

## Compatibility change

Campaign 012 now requests only official OSMRE records with:

`reclamation_bond_status = 1`

inside the approved Central Appalachia bounds. It then applies the already-approved gates locally:

- contact code in 1, 2, or 3 (Virginia, West Virginia, Kentucky);
- reclamation bond status date from 2019-01-01 through 2024-12-31;
- unique official identity;
- polygon component envelope at least 40 m in both dimensions.

The compatibility fetch reports exact raw/retained/rejection counts if no target survives.

## What did not change

- Campaign 012 geography;
- Phase I status requirement;
- approved states/contact codes;
- 2019-2024 date window;
- 40 m footprint pre-screen;
- ICESat-2 repeat-series thresholds;
- neighbour/cluster thresholds;
- context/finalizer/terminal-stability/temporal-recovery gates;
- records-research gate;
- classifier, frontend, Option 5, Tyrone, or main.

## Decision rule

If the compatibility run still yields zero retained OSMRE polygons, Campaign 012 closes as a source-screen zero with the printed rejection counts. Do not broaden the date window, states, status code, or 40 m screen without explicit approval.

If eligible polygons exist, continue the approved Campaign 012 ICESat-2 scan with the existing per-tile watchdog. A surviving terrain-step cluster remains only a candidate, not a depth anchor.
