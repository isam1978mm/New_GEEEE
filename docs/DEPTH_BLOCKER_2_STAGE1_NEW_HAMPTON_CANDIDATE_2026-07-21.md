# Blocker 2 — Stage-1 New Hampton Candidate — 2026-07-21

Status: Stage 1 active. New Hampton Landfill, New Hampshire, is retained as `candidate_under_review`. Blocker 2 remains unresolved. No calibration-pack intake, training, or app-depth enablement is authorized.

## Verified public facts

- The Town of Bristol public site map has a dedicated New Hampton Landfill records page under the Conservation Commission.
- Search-indexed official material identifies an HDPE landfill cap, passive gas vents, monitoring wells, and New Hampton landfill closure record plans.
- The indexed official material states the closure system was completed in 2022.
- New Hampshire landfill rules require record drawings after cap construction and require settlement monitoring by visual inspection and topographic survey using established control points.
- The current Bristol public route for the dedicated landfill page did not render through the available retrieval interface.
- Searches of the Bristol public site and indexed NHDES/OneStop material did not expose downloadable 2022 record-plan sheets, final surveyed contours, survey-control notes, numerical horizontal or vertical accuracy, verified cover-thickness tables, or a 2023–2026 repeat topographic settlement survey.
- This is an access result, not evidence that the underlying municipal or NHDES files do not exist.

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

## Public-file inspection result

The dedicated Bristol collection was located through the official site map, but the page itself did not render through the available public retrieval path. Targeted searches of Bristol and NHDES-indexed material did not surface the required drawings or survey tables as separate downloadable files.

No value was inferred from the existence of named record plans, rule requirements, printed contour precision, or general closure descriptions.

## Decision

Retain New Hampton as a promising New Hampshire candidate because the closure occurred in 2022 and official indexed material names completed record plans and a defined HDPE cap system.

Do not promote it. The calibration contract still requires the actual final surveyed surface, explicit survey-control and accuracy metadata, confirmed waste-in-place construction scope, and a later repeat topographic survey from comparable control.

Cross Road Landfill, Exeter, was screened in the same pass and rejected as a modern calibration candidate because public post-closure reports extend back to at least 2013, placing its cap event before the Sentinel-1 era.

## Waiting for

```text
new_hampton_2022_record_plan_pdf_or_native_cad
+ final_as_built_contours_or_survey_points
+ horizontal_and_vertical_datum
+ explicit_survey_accuracy
+ verified_cover_thickness
+ 2023_to_2026_repeat_topographic_settlement_survey
+ confirmation_no_major_waste_relocation
```

## Next step

Stop repeating the same public-web search. Request the named files directly from the Town of Bristol Conservation Commission or NHDES Solid Waste Management Bureau:

1. 2022 New Hampton Landfill closure record plans and all survey appendices.
2. Final as-built contour or survey-point files, preferably native CAD, LandXML, CSV, or GIS.
3. Survey-control report, horizontal and vertical datum, and stated numerical accuracy.
4. Construction-quality records verifying HDPE cap and cover-layer thickness.
5. Every 2023–2026 post-closure topographic or settlement survey using the same control points.
6. Construction narrative confirming whether waste remained in place and identifying any excavation, relocation, or regrading.

## Public references

- Bristol public site map listing the New Hampton Landfill collection: `https://www.bristolnh.gov/sitemap`
- Dedicated collection route identified by the official site map: `https://www.bristolnh.gov/1366/New-Hampton-Landfill`
- New Hampshire landfill closure and post-closure rule: `https://www.law.cornell.edu/regulations/new-hampshire/N-H-Admin-Code-SS-Env-Sw-807.03`
- New Hampshire solid-waste rules, including record-drawing requirements: `https://gc.nh.gov/rules/state_agencies/env-sw800.html`
- Exeter Cross Road Landfill report index used for the rejected fallback screen: `https://www.exeternh.gov/publicworks/cross-road-landfill-reports`
