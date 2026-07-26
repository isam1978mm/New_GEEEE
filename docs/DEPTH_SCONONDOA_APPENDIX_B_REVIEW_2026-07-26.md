# Sconondoa Appendix B Review — 2026-07-26

**Branch:** `main`  
**Decision:** `PROVISIONAL HOLD`  
**Reason:** Appendix B proves geometry and measured excavation depths, but Appendix B alone does not prove or disprove that two named cells received the same final radar-facing surface assembly.

## Current status

```text
sconondoa_appendix_b_reviewed = yes
review_basis = summary_from_separate_pdf_review_session
cell_geometry_available = yes
finite_excavation_measurements_available = yes
comparable_shallow_deep_surface_pair_confirmed = not_yet_checked_in_restoration_records
earth_engine_query_executed = no
usable_calibration_rows = 0
numerical_depth_ready = no
app_depth_enabled = false
```

## Important correction

The working session that wrote this repository record did not directly inspect the 90 MB Appendix PDF. It relied on the detailed findings supplied from a separate chat that had access to the PDF.

Those findings support statements about what Appendix B contains. They do not support a final site rejection until the main report's restoration specifications, construction records and completion certifications are separately checked.

The earlier `NOT GOOD TO GO` wording was too strong and is superseded by this document.

## What Appendix B establishes

Appendix B is organized into Phase 1, Phase 2 and Phase 3 survey sets.

It establishes:

- surveyed excavation-cell boundaries;
- grid-point identifiers;
- northing and easting coordinates;
- pre-excavation or pre-construction elevations;
- post-excavation elevations;
- finite, spatially variable excavation depths;
- licensed-surveyor certification and benchmarks;
- enough geometry to digitize individual cells.

Examples reported from Phase 2 Cell 2 include calculated depths from 13.8 ft to 20.7 ft at reviewed survey points.

## What Appendix B does not establish by itself

Appendix B visibly distinguishes several surface and infrastructure conditions, including asphalt, gravel, gravel drives, roads, buildings, utilities, drainage, riprap, parking and vegetation.

From Appendix B alone, the review could not confirm that two selected cells received:

- the same final surface material;
- the same material thickness;
- the same compaction specification;
- the same drainage treatment;
- the same later land use and maintenance;
- enough clean interior area after exclusions.

This is an unresolved evidence question, not a proven negative.

## Required next evidence check

Inspect the main Final Engineering Report and its construction/restoration records for an explicit statement tying two named cells to the same final surface assembly.

Search for cell-specific language in:

- restoration specifications;
- general-fill placement records;
- subbase placement records;
- gravel or top-course specifications;
- compaction requirements and test results;
- final grading plans;
- restoration or surface-finish drawings;
- construction completion certifications;
- change orders and field directives;
- material tickets or quantity summaries;
- later inspection records showing unchanged surface use.

The evidence must name or clearly map the relevant cells. A general project-wide material specification is insufficient unless it explicitly applies to both selected cells without exceptions.

## Decision rule after that review

`GOOD TO GO` only when two cells or subareas have:

1. different finite measured or calculable depths;
2. exact mappable boundaries;
3. the same documented final radar-facing surface assembly;
4. comparable later land use and maintenance;
5. enough clean interior area after removing roads, utilities, drainage, structures and mixed pixels.

`NOT GOOD TO GO` only when the restoration and construction records have been reviewed and either:

- explicitly show different final surface assemblies; or
- fail to provide enough evidence to establish an equivalent pair.

## Current decision

```text
site = sconondoa
radar_depth_ordering_candidate = pending_restoration_record_review
comparable_surface_pair = unresolved
earth_engine_query_executed = no
scientific_radar_linkage_outcome = not_evaluated
```

## Next step

Review the main report's restoration specifications and construction records. Do not create shallow/deep GeoJSON polygons and do not run the Sentinel-1 screen until that review is complete.
