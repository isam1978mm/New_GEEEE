# Blocker 2 — Stage-1 Yorktown Ash Landfill Candidate — 2026-07-21

Status: Stage 1 active. Dominion Energy's Yorktown Power Station Ash Landfill, York County, Virginia, is retained as `candidate_under_review`. Blocker 2 remains unresolved. No calibration-pack intake, model fitting, or app-depth enablement is authorized.

## Verified official public facts

- Virginia DEQ identifies the unit as an existing captive industrial landfill and an existing CCR landfill under the EPA CCR Rule.
- Virginia DEQ states that Solid Waste Permit SWP457 was modified in August 2020 to incorporate closure, post-closure care, groundwater monitoring, recordkeeping, and other CCR-rule requirements.
- Dominion identifies the Yorktown landfill as closed and states that landfill closure was completed in September 2020.
- Dominion's CCR compliance index publicly lists all of the following named records for the landfill:
  - Yorktown Landfill Closure Plan;
  - Yorktown Landfill Post Closure Care Plan;
  - Yorktown Landfill Notice of Intent to Close;
  - Yorktown Landfill Closure Extension Demonstration;
  - Yorktown Landfill Construction Completion Certification;
  - Yorktown Landfill Closure Plan Notification.
- The same official index provides annual groundwater-monitoring reports through 2025, but it does not list a separate post-closure topographic survey, settlement survey, or iso-settlement map.

## Evidence supplied in the preceding research note

The research note supplied for this screening reports that the public Yorktown records describe:

- approximately 48 acres;
- approximately 1.4 million cubic yards of CCR at closure;
- 24 inches of final-cover soils;
- a planned survey plat showing final closure grades;
- post-closure inspection for settlement, subsidence, or displacement.

These details are treated as strong leads, not fully extracted calibration evidence in this repository pass. The Dominion PDF endpoints were publicly linked, but the available web retrieval interface could not render the files. Therefore the actual survey plat, surveyed elevations, datum, numerical survey accuracy, and drawing sheets were not independently inspected here.

## Classification

```text
candidate_id = N1-15
candidate_state = candidate_under_review
sentinel_1_era_closure = pass
closure_completed = pass
closure_completion_year = 2020
large_analysis_footprint = pass_from_supplied_research
waste_left_in_place = promising_but_requires_document_confirmation
known_cover_thickness = promising_from_supplied_research
professional_engineer_completion_certification = pass_at_document_index_level
final_grade_survey_plat = referenced_but_not_extracted
final_as_built_contours = unresolved
pre_cap_or_top_of_waste_surface = unresolved
horizontal_and_vertical_datum = unresolved
numerical_survey_accuracy = unresolved
later_repeat_topographic_survey = fail_not_found
post_closure_settlement_inspection = pass_but_visual_or_maintenance_only
clean_s1_experiment_unit = promising_but_unverified
R1_depth_measurability = not_tested_pending_stage_3
R5_radar_linkage = not_tested_pending_stage_3
```

## Decision

Retain Yorktown as one of the strongest completed-project leads because the closure is recent, the unit is large, the official construction-completion certification is publicly indexed, and the supplied research points to known cover thickness and final-grade survey documentation.

Do not promote Yorktown to calibration-ready status. Inspection language concerning settlement or subsidence is not equivalent to a repeat elevation survey. The current public index does not expose the three-surface chain required for direct depth calibration:

1. measured pre-cap or top-of-waste surface;
2. measured final as-built cap surface;
3. later repeat topographic surface from comparable control.

## Exact missing records

```text
yorktown_final_grade_survey_plat
+ native_or_high_resolution_as_built_contours
+ pre_cap_or_top_of_waste_survey
+ survey_control_and_datum_report
+ explicit_horizontal_and_vertical_accuracy
+ verified_cover_thickness_measurements
+ post_2020_repeat_topographic_or_settlement_survey
+ confirmation_no_major_waste_relocation_or_regrading
```

## Next step

Request the following records from Virginia DEQ Tidewater Regional Office or Dominion's Yorktown operating record:

- the complete construction completion certification and all attachments;
- the final closure survey plat and record drawings;
- native CAD, GIS, LandXML, or survey-point files if maintained;
- the pre-cap/top-of-waste or prepared-subgrade survey;
- the survey-control report, coordinate system, vertical datum, and stated accuracy;
- any post-September-2020 topographic, settlement, subsidence, or deformation survey.

If no later repeat elevation survey exists, Yorktown may remain useful for cap-event classification but cannot provide direct settlement-calibration truth.

## Public references

- Virginia DEQ Yorktown Power Station page: `https://www.deq.virginia.gov/news-info/shortcuts/permits/waste/coal-ash/yorktown-power-station`
- Dominion CCR compliance index: `https://www.dominionenergy.com/about/delivering-energy/electric-projects/coal-ash/ccr-rule-compliance-data-and-information/2015-ccr-rule`
- Dominion coal-ash overview stating Yorktown closure completion: `https://www.dominionenergy.com/about/delivering-energy/electric-projects/coal-ash`
