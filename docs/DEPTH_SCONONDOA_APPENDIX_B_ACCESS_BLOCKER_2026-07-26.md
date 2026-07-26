# Sconondoa Appendix B — Access Blocker Resolution — 2026-07-26

**Branch:** `main`  
**Current status:** file-access blocker resolved; candidate closed after review  
**Usable calibration rows:** `0`  
**Numerical depth ready:** `no`

## What changed

The official file was reviewed in a separate working session:

`Report.HW.727008.2021-06-25.FER Appendices A through C-Survey Figures and Photos.pdf`

Appendix B drawings B-1, B-2 and B-3 were inspected.

The earlier access blocker is therefore resolved:

```text
sconondoa_appendix_b_visible = yes
surveyed_cell_geometry_extracted = yes
finite_excavation_measurements_available = yes
```

## Review result

The drawings contain:

- surveyed excavation-cell boundaries;
- northing and easting coordinates;
- pre-excavation elevations;
- post-excavation elevations;
- finite and spatially variable excavation depths;
- professional survey certification and benchmarks.

However, they do not prove that a shallow cell and a deep cell share equivalent final radar-facing conditions.

The mapped final surfaces include or border different combinations of:

- asphalt;
- gravel and gravel drives;
- riprap or surge stone;
- buildings;
- roads;
- utilities;
- drainage structures;
- parking areas;
- vegetation and wooded edges.

The evidence does not confirm the same final material, thickness, compaction, moisture behaviour and later land use across a defensible shallow/deep pair.

## Decision

```text
sconondoa_appendix_b_reviewed = yes
cell_geometry_available = yes
finite_excavation_measurements_available = yes
comparable_shallow_deep_surface_pair_confirmed = no
sconondoa_radar_depth_ordering_candidate = not_good_to_go
earth_engine_query_executed = no
scientific_radar_linkage_outcome = not_evaluated
```

Do not create shallow/deep polygons or run the Sentinel-1 depth-ordering screen from Appendix B alone. That could measure surface construction or infrastructure differences rather than excavation depth.

Detailed review:

`docs/DEPTH_SCONONDOA_APPENDIX_B_REVIEW_2026-07-26.md`

## Current status

```text
usable_calibration_rows = 0
calibration_record_created = false
training_started = false
depth_measured = false
numerical_depth_ready = no
app_depth_enabled = false
```

## Next step

Close Sconondoa for the current route. Any next candidate must have both finite mapped depth zones and documented equivalent final surface construction and later land use before a radar query is allowed.
