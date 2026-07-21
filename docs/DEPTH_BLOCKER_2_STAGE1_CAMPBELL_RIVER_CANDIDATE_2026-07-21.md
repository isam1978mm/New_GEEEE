# Blocker 2 — Stage-1 Campbell River Candidate — 2026-07-21

Status: Stage 1 active. Campbell River Waste Management Centre landfill, British Columbia, is retained as `candidate_under_review`. Blocker 2 remains unresolved. No calibration-pack intake, training, or app-depth enablement is authorized.

## Verified public facts

- The official Comox Strathcona Waste Management page states that the Campbell River landfill reached airspace capacity in spring 2022 and that final closure was completed.
- The official page identifies a 2020 Closure and Upgrading Plan covering the final cover system, surface-water controls, landfill-gas controls, and post-closure monitoring.
- The 2020 closure-plan drawing set contains planned final contours and identifies May and November 2019 McElhanney topographic surveys as source surfaces. These are design/baseline records, not the certified constructed final surface.
- The 2021 annual report records a December 3, 2021 topographic survey. It compares that surveyed surface with the planned top-of-final-cover contours and calculates approximately 26,880 cubic metres between them, including approximately 13,460 cubic metres allocated to final cover.
- This December 2021 survey is useful pre-closure evidence, but it is not a clean top-of-waste baseline because waste disposal continued until May 4, 2022.
- The official site publicly lists annual Operations and Monitoring Reports for 2022 through 2025.
- The 2023 report's Section 3.8, `Volume Survey`, states that the landfill had ceased accepting waste on May 4, 2022 and therefore annual airspace consumption was not estimated for 2023.
- Therefore, the 2023 report does not supply the needed repeat cap-surface survey. Its general scope language about a survey with volume changes is a reporting requirement, not proof that a post-closure topographic or settlement survey was performed.
- The public evidence still does not expose the certified 2022 final as-built surface, survey datum and accuracy, or a later measured cap surface suitable for elevation differencing.

## Classification

```text
candidate_id = CRWMC-2022
candidate_state = candidate_under_review
sentinel_1_era_cap_event = pass
closure_completed = pass_public_summary
single_recent_closure_period = promising_but_unverified
waste_left_in_place = promising_but_unverified
closure_plan_public = pass
planned_final_contours = pass_design_level
pre_closure_topographic_surface = pass_2021_12_03
pre_closure_surface_clean_top_of_waste = fail_waste_added_until_2022_05_04
final_cqa_report_publicly_verified = unresolved
final_as_built_contours = unresolved
numerical_survey_uncertainty = unresolved
2023_volume_survey = fail_not_performed_for_airspace
later_repeat_cap_surface_survey = unresolved_not_found
clean_s1_experiment_unit = unresolved
R1_depth_measurability = not_tested_pending_evidence
R5_radar_linkage = not_tested_pending_evidence
```

## Decision

Retain Campbell River because it now has a verified December 2021 surveyed surface tied to planned final-cover contours and a completed Sentinel-1-era closure.

Do not promote it. The 2023 annual report does not provide a repeat cap survey, and the December 2021 surface is not the final pre-cap/top-of-waste condition because filling continued into May 2022. The calibration contract still requires the certified constructed final surface and a later surface measured from comparable control.

## Waiting for

```text
2022_closure_completion_or_cqa_report
+ certified_2022_final_as_built_contours_or_points
+ survey_date_immediately_before_final_cover
+ horizontal_and_vertical_datum
+ explicit_horizontal_and_vertical_accuracy
+ verified_final_cover_thickness
+ 2024_or_2025_repeat_cap_topographic_survey
+ settlement_monument_table_or_elevation_difference_map
+ confirmation_no_major_waste_relocation
```

## Next step

Inspect the 2024 and 2025 Operations and Monitoring Reports for a post-closure topographic survey, settlement monument table, cap elevation comparison, or deformation map. Separately obtain the 2022 closure CQA/as-built package so any later surface can be tied to the constructed baseline.

## Public references

- Official Campbell River Waste Management Centre closure and annual-report index: `https://www.cswm.ca/garbage/campbell-river-waste-management-centre`
- 2020 Closure and Upgrading Plan with planned final contours and survey-source notes: `https://www.cswm.ca/sites/3/files/docs/CRWMC/20200821_ghd_crwmc_closure_and_upgrading_plan-final_draft.pdf`
- 2021 Operations and Monitoring Report with the December 3, 2021 topographic survey: `https://www.cswm.ca/sites/3/files/docs/CRWMC/11209296-rpt-07-2021_annual_report-campbell_river-final.pdf`
- 2023 Operations and Monitoring Report, including Section 3.8 Volume Survey: `https://www.cswm.ca/sites/3/files/2024-05/2023%20CRWMC%20Operations%20and%20Monitoring%20Report.pdf`
