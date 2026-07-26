# Numerical Depth Estimation — Radar-Linkage Feasibility Execution Closeout — 2026-07-26

**Branch:** `main`  
**Status:** bounded four-site sequence completed; no executable radar-depth experiment found  
**Scientific radar-linkage outcome:** not evaluated

## Current status

```text
bounded_candidate_sequence_complete = yes
sites_reviewed = 4
sites_ready_for_radar_query = 0
earth_engine_site_queries_executed = 0
usable_calibration_rows = 0
numerical_depth_ready = no
app_depth_enabled = false
```

## Plain-English result

River Road, Auburn, John Sevier and Sconondoa were reviewed in the fixed order required by the execution plan.

No Sentinel-1 depth test was run.

The first three sites failed before the query because exact geometry or usable local depth zones could not be recovered. Sconondoa supplied real geometry and real depth measurements, but failed because no shallow/deep pair had confirmed equivalent final radar-facing surface conditions.

This is not evidence that Sentinel-1 has no depth-related surface response. The scientific relationship remains untested because no candidate satisfied the experiment-input rules.

## Site outcomes

### River Road

```text
site_surface_response_decision = site_screen_inconclusive
reason = final_cover_and_pit_map_not_visibly_recoverable
```

The record confirms 129 surveyed certification pits and a minimum three-foot cover, but the accepted pit values and survey drawing remain unreadable. An approximate property centroid and dimensions were not converted into a cap polygon.

### Auburn McMaster

```text
site_surface_response_decision = site_screen_inconclusive
site_depth_ordering_decision = site_depth_ordering_not_supported_or_inconclusive
reason = local_as_built_thickness_and_polygon_pages_not_visibly_recoverable
```

The record confirms that local cover thicknesses and mapped demarcation areas exist, and the later surface is stable. The readable text provides only a general 12-inch minimum and a different two-foot ecological-buffer condition. Those are not a controlled measured-depth pair.

### John Sevier

```text
site_surface_response_decision = site_screen_inconclusive
reason = exact_eastern_cap_polygon_and_matched_comparison_unavailable
```

The record confirms an actual 24-inch cover profile over an approximately 19-acre eastern cap and a stable inspection period. Published inspection extents are approximate, the construction-history file timed out, and no exact cap polygon or numerical tolerance was recovered.

### Sconondoa

```text
sconondoa_appendix_b_reviewed = yes
cell_geometry_available = yes
finite_excavation_measurements_available = yes
comparable_shallow_deep_surface_pair_confirmed = no
site_depth_ordering_decision = not_good_to_go
reason = comparable_final_surface_not_confirmed
```

Appendix B drawings B-1, B-2 and B-3 were reviewed.

The drawings provide professional survey geometry, coordinates, pre-excavation elevations, post-excavation elevations and finite excavation-depth variation. For example, verified Cell 2 calculations range from 13.8 ft to 20.7 ft at reviewed points.

However, the final mapped setting includes different combinations of asphalt, gravel, gravel drives, roads, buildings, utilities, drainage, riprap, parking and vegetation. The drawings do not prove that any shallow/deep cell pair shares the same final material, thickness, compaction, moisture behaviour and later land use.

Running the radar test would therefore risk measuring surface or infrastructure differences rather than excavation depth.

Detailed review:

`docs/DEPTH_SCONONDOA_APPENDIX_B_REVIEW_2026-07-26.md`

## Overall feasibility decision

The execution plan's scientific `PASS`, `MIXED` and `FAIL` outcomes require completed Sentinel-1 measurements. None applies.

```text
radar_linkage_feasibility_screen = no_valid_experiment_input
bounded_candidate_sequence_complete = yes
earth_engine_site_queries_executed = 0
scientific_radar_linkage_outcome = not_evaluated
cross_site_depth_linkage_decision = not_evaluated
```

Do not label this as a radar `FAIL`. The radar relationship was never measured.

## What this sequence established

Geometry and measured depth are not enough.

A candidate may advance to a radar query only when it has all of the following:

1. exact mappable boundaries;
2. finite measured or calculable local depths;
3. at least two depth zones with clear ordering;
4. documented equivalent final surface material and construction;
5. documented comparable later land use and maintenance;
6. enough clean interior area after excluding roads, utilities, drainage, structures and mixed pixels;
7. observation dates suitable for repeated same-orbit Sentinel-1 comparisons.

Sconondoa failed requirements 4 through 6.

## Next step

Do not retry Sconondoa and do not run the Earth Engine query from its cells.

Start a **targeted uniform-surface candidate search**, not a generic landfill search.

Search only for completed projects where public records already show:

```text
multiple mapped zones with different measured depths
+ one documented uniform final surface system across those zones
+ stable later land use
+ enough clean area for Sentinel-1 pixels
```

Priority document types:

- as-built excavation or cover-thickness grids;
- final grading and restoration drawings;
- material-placement specifications proving the same top layer;
- completion certifications;
- later inspection or aerial evidence showing unchanged use.

Reject a candidate immediately when the different depth zones have different asphalt, gravel, vegetation, drainage, compaction or infrastructure conditions.

## Implementation available

```text
scripts/run_depth_radar_linkage_feasibility_screen.py
tests/unit/test_depth_radar_linkage_feasibility_screen.py
.github/workflows/depth-radar-linkage-screen.yml
docs/DEPTH_RADAR_LINKAGE_FEASIBILITY_EXECUTION_PLAN_2026-07-26.md
docs/DEPTH_RIVER_ROAD_RADAR_LINKAGE_RUNBOOK_2026-07-26.md
docs/DEPTH_SCONONDOA_APPENDIX_B_REVIEW_2026-07-26.md
```

The runner remains ready, but must not be used until a candidate passes the full experiment-input gate.

## Numerical-depth boundary

```text
usable_calibration_rows = 0
calibration_record_created = false
training_started = false
depth_measured = false
numerical_depth_ready = no
app_depth_enabled = false
```
