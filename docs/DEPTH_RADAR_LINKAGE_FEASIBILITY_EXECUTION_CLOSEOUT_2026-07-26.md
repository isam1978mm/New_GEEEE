# Numerical Depth Estimation — Radar-Linkage Feasibility Execution Closeout — 2026-07-26

**Branch:** `main`  
**Status:** bounded four-site sequence completed; Sconondoa remains open for one final evidence check  
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
sconondoa_restoration_record_review_complete = no
```

## Plain-English result

River Road, Auburn, John Sevier and Sconondoa were reviewed in the fixed order.

No Sentinel-1 depth test was run.

The first three sites remain inconclusive because exact geometry or usable local depth zones could not be recovered.

Sconondoa is different: Appendix B provides real geometry and real excavation-depth measurements. However, Appendix B alone does not establish whether two named cells received the same final radar-facing surface assembly.

The previous final `NOT GOOD TO GO` decision for Sconondoa was too strong because the main restoration specifications and construction records were not yet checked. Sconondoa is now on a provisional hold.

## Site outcomes

### River Road

```text
site_surface_response_decision = site_screen_inconclusive
reason = final_cover_and_pit_map_not_visibly_recoverable
```

### Auburn McMaster

```text
site_depth_ordering_decision = site_screen_inconclusive
reason = local_as_built_thickness_and_polygon_pages_not_visibly_recoverable
```

### John Sevier

```text
site_surface_response_decision = site_screen_inconclusive
reason = exact_eastern_cap_polygon_and_matched_comparison_unavailable
```

### Sconondoa

```text
sconondoa_appendix_b_reviewed = yes
cell_geometry_available = yes
finite_excavation_measurements_available = yes
comparable_shallow_deep_surface_pair_confirmed = unresolved
site_depth_ordering_decision = pending_restoration_record_review
```

Appendix B review findings were supplied from a separate chat that could access the PDF. The current working session did not directly inspect the 90 MB file.

Appendix B supports:

- mappable excavation-cell boundaries;
- coordinates and control points;
- pre-excavation and post-excavation elevations;
- finite, spatially variable depths.

Appendix B does not by itself prove that two selected cells share the same final surface material, thickness, compaction, drainage treatment and later use.

That question must be answered from the main Final Engineering Report and its construction/restoration records.

Detailed corrected review:

`docs/DEPTH_SCONONDOA_APPENDIX_B_REVIEW_2026-07-26.md`

## Overall feasibility decision

The scientific `PASS`, `MIXED` and `FAIL` outcomes require completed Sentinel-1 measurements. None applies.

```text
radar_linkage_feasibility_screen = blocked_before_query
scientific_radar_linkage_outcome = not_evaluated
cross_site_depth_linkage_decision = not_evaluated
```

Do not label this as a radar failure.

## Next step

Do not start a new candidate search yet.

Inspect the Sconondoa main report and supporting construction/restoration records for an explicit statement that two named cells received the same final surface assembly.

Priority evidence:

- restoration specifications;
- general-fill and subbase placement requirements;
- gravel or top-course specifications;
- compaction requirements and test results;
- final grading or restoration drawings;
- completion certifications;
- change orders or field directives;
- later inspection records showing unchanged surface use.

Advance Sconondoa only if the records explicitly map the same final surface assembly to two cells or subareas with different measured depths and enough clean interior area for Sentinel-1 pixels.

Reject Sconondoa only after this restoration-record review is completed and comparable surfaces still cannot be established.

## Numerical-depth boundary

```text
usable_calibration_rows = 0
calibration_record_created = false
training_started = false
depth_measured = false
numerical_depth_ready = no
app_depth_enabled = false
```
