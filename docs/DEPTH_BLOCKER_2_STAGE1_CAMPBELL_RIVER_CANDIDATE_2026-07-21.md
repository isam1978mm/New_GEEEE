# Blocker 2 — Stage-1 Campbell River Candidate — 2026-07-21

Status: Stage 1 active. Campbell River Waste Management Centre landfill, British Columbia, is retained as `candidate_under_review`. Blocker 2 remains unresolved. No calibration-pack intake, training, or app-depth enablement is authorized.

## Verified public facts

- The official Comox Strathcona Waste Management page states that the Campbell River landfill reached airspace capacity in spring 2022 and that final closure was completed.
- The same official page identifies a 2020 Closure and Upgrading Plan covering the final cover system, surface-water controls, landfill-gas controls, and post-closure environmental monitoring.
- A 2019 official closure FAQ describes a planned final top elevation of 194 metres above mean sea level and a final geomembrane cover installed over the waste. This is design-level evidence, not an as-built survey.
- The official page publicly lists annual Operations and Monitoring Reports for 2022, 2023, 2024, and 2025.
- Search-indexed text from the official 2023 Operations and Monitoring Report states that the annual-report scope includes closure works completed and a survey including volume changes on the required frequency.
- That wording proves that a survey/volume-change record exists in the annual reporting workflow, but it does not yet prove a repeat survey of the closed cap surface, settlement monuments, an elevation-difference map, or a surface model tied to the final as-built survey.
- The public interface still does not expose a final construction-quality-assurance report, certified as-built contour set, pre-cap/top-of-waste survey, numerical survey accuracy, or a verified later cap-settlement survey.

## Classification

```text
candidate_id = CRWMC-2022
candidate_state = candidate_under_review
sentinel_1_era_cap_event = pass
closure_completed = pass_public_summary
single_recent_closure_period = promising_but_unverified
waste_left_in_place = promising_but_unverified
closure_plan_public = pass
planned_final_top_elevation = 194_m_AMSL_design_only
annual_volume_change_survey = pass_at_report_scope
annual_volume_survey_purpose = unresolved_capacity_vs_cap_surface
final_cqa_report_publicly_verified = unresolved
final_as_built_contours = unresolved
pre_cap_or_top_of_waste_surface = unresolved
numerical_survey_uncertainty = unresolved
later_repeat_topographic_survey = unresolved_not_proven_by_volume_wording
clean_s1_experiment_unit = unresolved
R1_depth_measurability = not_tested_pending_evidence
R5_radar_linkage = not_tested_pending_evidence
```

## Decision

Retain Campbell River because it is a completed 2022 landfill closure and the official site maintains a multi-year reporting trail through 2025. The 2023 report is stronger than previously known because it explicitly includes a survey with volume changes.

Do not promote it. A landfill volume survey may measure capacity or operational earthwork and is not automatically a repeat settlement/topographic survey of the final cover. The calibration contract still requires the actual final surveyed surface, comparable pre-cap/top-of-waste elevations, explicit datum and accuracy, verified cover thickness, and a later measured cap surface from comparable control.

## Waiting for

```text
2022_closure_completion_or_cqa_report
+ certified_final_as_built_contours_or_survey_points
+ pre_cap_or_top_of_waste_surface
+ horizontal_and_vertical_datum
+ explicit_survey_accuracy
+ verified_final_cover_thickness
+ 2023_volume_survey_appendix_or_native_surface
+ proof_volume_survey_covers_closed_cap_surface
+ later_elevation_difference_or_settlement_map
+ confirmation_no_major_waste_relocation
```

## Next step

Obtain the 2023 survey appendix or native survey deliverable and determine whether it maps the closed final-cover surface or only calculates landfill volume/capacity. If it covers the cap, compare it with the 2022 final as-built surface and extract datum, accuracy, dates, and elevation differences.

## Public references

- Official Campbell River Waste Management Centre closure and annual-report index: `https://www.cswm.ca/garbage/campbell-river-waste-management-centre`
- Official 2019 closure FAQ: `https://www.cswm.ca/sites/3/files/docs/cswm_faqs_final.pdf`
- Direct 2023 annual-report link listed by the official page: `https://www.cswm.ca/sites/3/files/2024-05/2023%20CRWMC%20Operations%20and%20Monitoring%20Report.pdf`
- Direct 2022 annual-report link listed by the official page: `https://www.cswm.ca/sites/3/files/2023-08/2022%20Operations%20and%20Monitoring%20Report%20CR_0.pdf`
