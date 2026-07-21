# Blocker 2 — Stage-1 Campbell River Candidate — 2026-07-21

Status: Stage 1 active. Campbell River Waste Management Centre landfill, British Columbia, is retained as `candidate_under_review`. Blocker 2 remains unresolved. No calibration-pack intake, training, or app-depth enablement is authorized.

## Verified public facts

- The official Comox Strathcona Waste Management page states that the Campbell River landfill reached airspace capacity in spring 2022 and that final closure was completed.
- The same official page identifies a 2020 Closure and Upgrading Plan covering the final cover system, surface-water controls, landfill-gas controls, and post-closure environmental monitoring.
- The official page publicly lists annual Operations and Monitoring Reports for 2022, 2023, 2024, and 2025.
- The public index does not itself expose a final construction-quality-assurance report, certified as-built contour set, pre-cap/top-of-waste survey, numerical survey accuracy, or a later repeat topographic/settlement survey.
- The annual-report links are promising evidence containers, but the currently accessible public interface did not allow verification that they include measured repeat surface elevations rather than groundwater, surface-water, gas, and leachate monitoring only.

## Classification

```text
candidate_id = CRWMC-2022
candidate_state = candidate_under_review
sentinel_1_era_cap_event = pass
closure_completed = pass_public_summary
single_recent_closure_period = promising_but_unverified
waste_left_in_place = promising_but_unverified
closure_plan_public = pass
final_cqa_report_publicly_verified = unresolved
final_as_built_contours = unresolved
pre_cap_or_top_of_waste_surface = unresolved
numerical_survey_uncertainty = unresolved
later_repeat_topographic_survey = unresolved
clean_s1_experiment_unit = unresolved
R1_depth_measurability = not_tested_pending_evidence
R5_radar_linkage = not_tested_pending_evidence
```

## Decision

Retain Campbell River because it is a completed 2022 landfill closure and the official site maintains a multi-year post-closure reporting trail through 2025.

Do not promote it. The calibration contract still requires the actual final surveyed surface, comparable pre-cap/top-of-waste elevations, explicit datum and accuracy, verified cover thickness, and a later measured surface survey from comparable control.

## Waiting for

```text
2022_closure_completion_or_cqa_report
+ certified_final_as_built_contours_or_survey_points
+ pre_cap_or_top_of_waste_surface
+ horizontal_and_vertical_datum
+ explicit_survey_accuracy
+ verified_final_cover_thickness
+ 2023_to_2025_repeat_topographic_or_settlement_survey
+ confirmation_no_major_waste_relocation
```

## Next step

Retrieve the 2022 closure-completion/CQA and as-built package, then inspect the 2023–2025 Operations and Monitoring Reports for a survey appendix, contour comparison, settlement monument table, or repeat surface model tied to the same control.

## Public references

- Official Campbell River Waste Management Centre closure and annual-report index: `https://www.cswm.ca/garbage/campbell-river-waste-management-centre`
- Direct 2023 annual-report link listed by the official page: `https://www.cswm.ca/sites/3/files/2024-05/2023%20CRWMC%20Operations%20and%20Monitoring%20Report.pdf`
- Direct 2022 annual-report link listed by the official page: `https://www.cswm.ca/sites/3/files/2023-08/2022%20Operations%20and%20Monitoring%20Report%20CR_0.pdf`
