# Numerical Depth Estimation — Radar-Linkage Feasibility Execution Closeout — 2026-07-26

**Branch:** `main`  
**Status:** bounded four-site sequence completed at pre-query evidence gate  
**Scientific radar-linkage outcome:** not evaluated

## Plain-English result

River Road, Auburn, John Sevier and the Sconondoa substitute were screened in the fixed order required by the execution plan.

No real Sentinel-1 site comparison was launched. Every candidate stopped before the radar query because the public evidence available in the current environment could not supply both:

1. visibly reviewable geometry that maps the documented feature to radar pixels; and
2. a defensible target/comparison or shallow/deep zone pair with finite local labels.

This is an evidence-access result. It is not evidence that Sentinel-1 lacks a depth-related surface response.

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

### Sconondoa substitute

```text
site_surface_response_decision = site_screen_inconclusive
site_depth_ordering_decision = site_depth_ordering_not_supported_or_inconclusive
reason = surveyed_cell_geometry_unavailable
```

Sconondoa is the strongest restart candidate. The report confirms finite within-site depth variation, professionally surveyed cells and multiple cells with comparable gravel restoration. Appendix B contains the needed as-built survey drawings, but the 90 MB public appendix could not be rendered or downloaded. No separate mirror or archive copy was found.

## Overall feasibility decision

The execution plan's `PASS`, `MIXED` and `FAIL` outcomes require actual repeated Sentinel-1 measurements. None applies here.

```text
radar_linkage_feasibility_screen = blocked_before_query
bounded_candidate_sequence_complete = yes
earth_engine_site_queries_executed = 0
scientific_radar_linkage_outcome = not_evaluated
cross_site_depth_linkage_decision = not_evaluated
broad_candidate_search = paused
broad_document_search = paused
```

Do not label this result as `FAIL`. A failure decision would require valid site geometries, matched acquisitions and a completed analysis showing no stable relationship or a confounder-driven relationship.

## Exact restart point

Do not restart generic candidate searching.

Restart with:

```text
Site: Sconondoa Street former MGP
Document: Report.HW.727008.2021-06-25.FER Appendices A through C-Survey Figures and Photos.pdf
Required section: Appendix B as-built survey drawings, especially B-1, B-2 and B-3
```

Required extraction:

- visible cell boundaries;
- coordinate system and datum;
- final surface elevations;
- bottom-of-excavation elevations or finite depth annotations;
- mapping between cell names and the comparable gravel-restored zones;
- any stated survey accuracy or tolerance.

After the Sconondoa geometry is recovered:

1. select at least two simple gravel-restored cells with finite depth ordering;
2. exclude buildings, asphalt, utilities, wells, drainage and the gas-regulator area;
3. create the private shallow/deep GeoJSON files outside Git;
4. screen at least two accepted anchor dates and six same-orbit support acquisitions;
5. run `scripts/run_depth_radar_linkage_feasibility_screen.py` with `site_id=sconondoa` and `site_role=depth_ordering`;
6. only then decide whether an independent replication site should be retried.

## Implementation produced during this sequence

```text
scripts/run_depth_radar_linkage_feasibility_screen.py
tests/unit/test_depth_radar_linkage_feasibility_screen.py
.github/workflows/depth-radar-linkage-screen.yml
docs/DEPTH_RADAR_LINKAGE_FEASIBILITY_EXECUTION_PLAN_2026-07-26.md
docs/DEPTH_RIVER_ROAD_RADAR_LINKAGE_RUNBOOK_2026-07-26.md
examples/depth_radar_linkage/river_road_acquisition_screen.example.json
```

Focused tests and the workflow were committed, but no attached GitHub status check became visible and the local clone attempt was blocked by runtime DNS. No passing-test claim is made.

## Numerical-depth boundary

```text
usable_calibration_rows = 0
calibration_record_created = false
training_started = false
depth_measured = false
numerical_depth_ready = no
app_depth_enabled = false
```
