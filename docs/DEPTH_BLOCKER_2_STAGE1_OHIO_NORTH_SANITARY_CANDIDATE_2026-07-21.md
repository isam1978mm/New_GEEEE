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
construction_report_practical_access = fail_current_public_interface
as_built_depth_to_top = unresolved
numerical_survey_uncertainty = unresolved
observation_date_settlement = unresolved
clean_s1_experiment_unit = unresolved
R1_depth_measurability = not_tested_pending_stage_3
R5_radar_linkage = not_tested_pending_stage_3
```

## Extraction attempt result

The EPA profile and document listing were verified. The 1.04-GB construction report link was then opened through the public EPA interface, but the report could not be fetched or rendered by the available public retrieval path. Search indexing did not expose the required depth tables, as-built drawings, survey tolerance, or settlement measurements.

This is an access limitation, not evidence that the report lacks those fields.

No value may be inferred from the design report, page metadata, map elevations, or printed decimal precision.

## Decision

Retain North Sanitary as a strong lead because its 2022–2023 construction window is fully inside the Sentinel-1 era and the remedy covers a large area.

Do not promote it beyond `candidate_under_review` until an accessible source yields:

- surveyed pre-cap or top-of-waste elevations;
- surveyed final-cap elevations;
- explicit survey accuracy or tolerance;
- as-built layer thickness verification;
- settlement, subsidence, or later topographic measurements;
- a defensible isolated analysis footprint.

Do not spend further Stage-1 time repeatedly retrying the same 1.04-GB link. Revisit only if EPA publishes a segmented, smaller, text-accessible, or alternate official copy.

## Secondary check — Sudbury fallback

The Washington Ecology Sudbury Road Landfill page confirms:

- construction completed in 2017;
- a named 2017 Construction Quality Assurance Certification Report;
- a named 2022 periodic review;
- improved cover over two areas;
- ongoing operation and monitoring.

However, the public document endpoints for the CQA report and periodic review also failed to render during this pass. No new as-built depth, numerical uncertainty, or settlement value was extracted.

Sudbury remains `candidate_under_review` and is not promoted.

## Waiting for

```text
accessible_post_2015_as_built_report
+ certified_top_of_waste_or_subgrade_survey
+ certified_final_surface_survey
+ explicit_survey_accuracy
+ settlement_or_later_topography
```

## Next step

Switch to a smaller or segmented 2015–2026 public final-engineering or construction-completion report. Prioritize sources where the main report, survey appendix, and later review are separately downloadable rather than bundled into a single very large file.

## Public references

- EPA cleanup profile: `https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.cleanup&id=0504693`
- EPA cleanup schedule: `https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.schedule&id=0504693`
- EPA document listing: `https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.docdata&id=0504693`
- EPA SEMS construction report: `https://semspub.epa.gov/work/05/988369.pdf`
- Washington Ecology Sudbury site record: `https://apps.ecology.wa.gov/cleanupsearch/site/2485`
