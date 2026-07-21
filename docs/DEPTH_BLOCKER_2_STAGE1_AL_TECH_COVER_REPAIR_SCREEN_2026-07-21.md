# Blocker 2 — Stage-1 AL Tech Cover Repair Screen — 2026-07-21

Status: Stage 1 active. The AL Tech Specialty Steel Waste Management Area cover-repair report was screened. It is not usable for direct Sentinel-1 depth calibration. Blocker 2 remains unresolved.

## Verified facts

- NYSDEC published a Construction Completion Report for landfill-cover repairs completed in July 2016.
- The closed landfill area is approximately 31 acres.
- The documented event was an unauthorized excavation approximately 3 feet in diameter and 7 feet deep.
- The repair used flowable fill to within 3 feet of finished grade, followed by 12 inches of clay and 6 inches of sand below the membrane.
- The membrane was patched, then covered with 12 inches of protective soil and 6 inches of topsoil.
- No explicit survey accuracy, tolerance, settlement measurement, or certified whole-site top-of-waste survey was found.

## Classification

```text
candidate_id = N1-09
direct_s1_calibration_state = rejected_scale_or_sensor_mismatch
document_method_state = method_research_only
sentinel_1_era_event = pass
whole_site_or_large_section_experiment = fail
contract_depth_to_top = fail
numerical_uncertainty = fail
observation_date_settlement = fail
R1_depth_measurability = not_tested
R5_radar_linkage = not_tested
```

## Decision

The report provides useful construction-layer documentation, but the repaired footprint is far below a defensible Sentinel-1 experiment unit. It must not be converted into a whole-landfill depth label.

Retain only as method-research evidence showing that smaller segmented public reports can be accessible and detailed.

## Waiting for

```text
accessible_post_2015_whole_cell_as_built_report
+ certified_top_of_waste_or_subgrade_survey
+ certified_final_surface_survey
+ explicit_survey_accuracy
+ settlement_or_later_topography
```

## Next step

Continue with segmented final-engineering packages where the main report, as-built survey appendix, and later monitoring report are separately downloadable. Reject localized repairs and design-only records immediately.

## Public reference

- NYSDEC AL Tech report: `https://extapps.dec.ny.gov/data/DecDocs/401003/Report.HW.401003.2019-01-03.Al%20Tech%20WMA%20LF%20Cover%20Repair%20CCR.pdf`
