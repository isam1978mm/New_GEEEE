# Blocker 2 — Stage-1 New Hampton Candidate — 2026-07-21

Status: Stage 1 active. New Hampton Landfill, New Hampshire, is retained as `candidate_under_review`. Blocker 2 remains unresolved. No calibration-pack intake, training, or app-depth enablement is authorized.

## Verified public facts

- A Bristol, New Hampshire public-record page has a dedicated New Hampton Landfill section.
- Search-indexed official material identifies an HDPE landfill cap, passive gas vents, monitoring wells, and New Hampton landfill closure record plans.
- The indexed official material states the closure system was completed in 2022.
- New Hampshire landfill rules require record drawings after cap construction and require settlement monitoring by visual inspection and topographic survey using established control points.
- The available public index did not expose the actual record-plan sheets, surveyed final contours, numerical horizontal or vertical survey accuracy, cover-thickness verification, or a later repeat topographic settlement survey.

## Classification

```text
candidate_id = N1-14
candidate_state = candidate_under_review
sentinel_1_era_cap_event = pass
whole_landfill_cap = promising_but_unverified
waste_left_in_place = promising_but_unverified
record_drawings_exist = pass_at_metadata_level
record_drawings_publicly_extractable = fail_current_public_interface
final_as_built_contours = unresolved
numerical_survey_uncertainty = unresolved
observation_date_settlement = unresolved
clean_s1_experiment_unit = unresolved
R1_depth_measurability = not_tested_pending_stage_3
R5_radar_linkage = not_tested_pending_stage_3
```

## Decision

Retain New Hampton as a promising New Hampshire candidate because the closure occurred in 2022 and official indexed material names completed record plans and a defined HDPE cap system.

Do not promote it. The calibration contract still requires the actual final surveyed surface, explicit survey-control and accuracy metadata, confirmed waste-in-place construction scope, and a later repeat topographic survey from comparable control.

Cross Road Landfill, Exeter, was screened in the same pass and rejected as a modern calibration candidate because public post-closure reports extend back to at least 2013, placing its cap event before the Sentinel-1 era.

## Waiting for

```text
new_hampton_record_plan_access
+ final_as_built_contours_or_survey_points
+ horizontal_and_vertical_datum
+ explicit_survey_accuracy
+ verified_cover_thickness
+ later_repeat_topographic_settlement_survey
+ confirmation_no_major_waste_relocation
```

## Next step

Inspect the Bristol New Hampton Landfill document collection and NHDES OneStop file for the 2022 closure record plans, then search 2023–2026 post-closure filings for a repeat topographic survey using the same control points.

## Public references

- Bristol public site map listing the New Hampton Landfill collection: `https://www.bristolnh.gov/sitemap`
- New Hampshire landfill closure and post-closure rule: `https://www.law.cornell.edu/regulations/new-hampshire/N-H-Admin-Code-SS-Env-Sw-807.03`
- New Hampshire solid-waste rules, including record-drawing requirements: `https://gc.nh.gov/rules/state_agencies/env-sw800.html`
- Exeter Cross Road Landfill report index used for the rejected fallback screen: `https://www.exeternh.gov/publicworks/cross-road-landfill-reports`
