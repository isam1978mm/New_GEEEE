# Blocker 2 — Stage-1 Cobble Hill Candidate — 2026-07-21

Status: Stage 1 closed. Cobble Hill Holdings Landfill, British Columbia, is rejected for direct relative-depth calibration and retained only as method/reference evidence. Blocker 2 remains unresolved. No calibration-pack intake, training, or app-depth enablement is authorized.

## Verified public facts

- The Province of British Columbia identifies the site as a contaminated-soil landfill that entered permanent closure under Spill Prevention Order MO1701.
- The updated final closure plan was approved on June 26, 2019, and closure construction was completed in fall 2020.
- The regulator publishes a September 2020 construction wrap-up report and later post-closure monitoring reports.
- The 2019 Quality Management Plan required the contractor to maintain as-built surveys and drawings.
- The same plan required completed construction works to be surveyed in place before the next construction stage so accurate as-built drawings could be produced.
- The plan does not state a numerical horizontal or vertical survey accuracy in the accessible text.
- The final closure works were not a single simple fill event. They included soil relocation, a stabilizing buttress, liner opening and repair, drainage layers, subsoil, growing medium, ditching, and erosion control.
- The plan states that the three-dimensional Permanent Encapsulation Area was less than 9,000 square metres, making the usable footprint marginal for Sentinel-1 analysis.
- Post-closure inspections were observational rather than repeat topographic surveys.
- In February 2022, inspectors observed a localized area of soil subsidence in the northeast corner of the cap. It was approximately 2 m by 2 m and approximately 0.3 m below the surrounding grade.
- The same feature remained approximately the same size in the 2022 Q2 report and showed no significant change in the 2022 Q3 report.
- The reports do not provide surveyed coordinates, repeat surface elevations, numerical measurement uncertainty, or a survey-grade settlement table for that feature.
- A 2 m by 2 m localized feature is substantially smaller than a native Sentinel-1 10 m pixel and cannot support direct pixel-level depth calibration.
- The regulator's 71 MB construction wrap-up endpoint repeatedly failed during retrieval, so no unavailable values were inferred from it.

## Classification

```text
candidate_id = N1-12
candidate_state = rejected_direct_calibration_method_only
sentinel_1_era_cap_event = pass
whole_landfill_cap = pass
large_analysis_footprint = marginal_less_than_9000_m2
post_closure_review = pass_visual_only
as_built_depth_to_top = referenced_but_not_extractable
numerical_survey_uncertainty = fail_not_stated
observation_date_settlement = fail_visual_estimate_only
clean_s1_experiment_unit = fail_mixed_closure_construction
localized_change_s1_resolvability = fail_2m_by_2m
R1_depth_measurability = fail
R5_radar_linkage = fail
```

## Decision

Reject Cobble Hill for direct calibration.

The record proves that construction QA and as-built surveying were part of the closure process, but the accessible package does not provide an extractable survey-grade final cap surface with stated uncertainty and a comparable later survey. The only numerical post-closure surface change is a visually estimated, localized 2 m by 2 m subsidence area, which is below Sentinel-1 spatial resolution and is not suitable as depth ground truth.

Retain Cobble Hill only as method evidence showing useful document types and terminology:

```text
quality_management_plan
+ staged_as_built_surveys
+ construction_wrap_up_report
+ qualified_professional_oversight
+ repeated_post_closure_geotechnical_inspections
```

## Waiting for

```text
third_clean_post_2015_cap_candidate
+ accessible_final_as_built_surface
+ explicit_horizontal_and_vertical_accuracy
+ later_comparable_topographic_survey
+ Sentinel_1_resolvable_change_or_known_layer_depth
```

## Next step

Resume the candidate search. Prioritize modern whole-cell caps with downloadable construction-completion packages and repeat survey or settlement monitoring tables, rather than visual inspection-only post-closure reports.

## Public references

- Province of British Columbia site record: `https://www2.gov.bc.ca/gov/content/environment/air-land-water/site-permitting-compliance/sia`
- Construction wrap-up report listing: `https://www2.gov.bc.ca/assets/gov/environment/air-land-water/site-permitting-and-compliance/sia/spo/2020-09-30_construction_wrap_up_report_red.pdf`
- Quality Management Plan: `https://www2.gov.bc.ca/assets/gov/environment/air-land-water/site-permitting-and-compliance/sia/spo/cobble_hill_landfill_quality_management_plan_-_december_13_2019.pdf`
- 2022 Q1 post-closure report: `https://www2.gov.bc.ca/assets/gov/environment/air-land-water/site-permitting-and-compliance/sia/spo/2022_q1_post_closure_rpt.pdf`
- 2022 Q2 post-closure report: `https://www2.gov.bc.ca/assets/gov/environment/air-land-water/site-permitting-and-compliance/sia/spo/2022_q2_post_closure_rpt.pdf`
- 2022 Q3 post-closure report: `https://www2.gov.bc.ca/assets/gov/environment/air-land-water/site-permitting-and-compliance/sia/spo/2022_q3_post_closure_rpt.pdf`
