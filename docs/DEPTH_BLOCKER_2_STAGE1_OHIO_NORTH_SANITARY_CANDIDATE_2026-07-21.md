# Blocker 2 — Stage-1 Ohio North Sanitary Candidate — 2026-07-21

Status: Stage 1 active. North Sanitary Landfill (Valleycrest), Dayton, Ohio, is retained as `candidate_under_review`. Blocker 2 remains unresolved. No calibration-pack intake, model fitting, or app-depth enablement is authorized.

## Verified public facts

- EPA identifies the site as a 102-acre landfill with five disposal areas.
- The selected remedy included a multilayer cap over approximately 70 acres.
- EPA approved the final remedial design and final remedial action work plan in March 2022.
- Cleanup construction began in July 2022 and physical construction was completed in October 2023.
- EPA approved the Remedial Action Construction Report in February 2024.
- The official construction report is publicly listed through EPA SEMS as document `988369.pdf` and is approximately 1.04 GB.
- The site is now in post-construction completion and its first five-year review is scheduled for completion in 2027.

## Current classification

```text
candidate_id = N1-08
candidate_state = candidate_under_review
named_public_documents = pass
sentinel_1_era_construction_window = pass
large_analysis_footprint = pass
professional_engineering_record = pass
remedial_action_construction_report = pass_at_metadata_level
as_built_depth_to_top = unresolved
numerical_survey_uncertainty = unresolved
observation_date_settlement = unresolved
clean_s1_experiment_unit = unresolved
R1_depth_measurability = not_tested_pending_stage_3
R5_radar_linkage = not_tested_pending_stage_3
```

## Decision

Retain North Sanitary as the strongest Ohio candidate found so far because its 2022–2023 construction window is fully inside the Sentinel-1 era and the remedy covers a large area.

Do not promote it beyond `candidate_under_review` until the construction report yields:

- surveyed pre-cap or top-of-waste elevations;
- surveyed final-cap elevations;
- explicit survey accuracy or tolerance;
- as-built layer thickness verification;
- settlement, subsidence, or later topographic measurements;
- a defensible isolated analysis footprint.

## Waiting for

```text
construction_report_depth_tables
+ as_built_drawings
+ explicit_survey_accuracy
+ settlement_or_later_topography
```

## Next step

Extract those fields from EPA SEMS document `988369.pdf`. If the report cannot be practically retrieved or does not contain the required fields, keep the site at `candidate_under_review` and continue with another 2015–2026 closure.

## Public references

- EPA cleanup profile: `https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.cleanup&id=0504693`
- EPA cleanup schedule: `https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.schedule&id=0504693`
- EPA document listing: `https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.docdata&id=0504693`
- EPA SEMS construction report: `https://semspub.epa.gov/work/05/988369.pdf`
