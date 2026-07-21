# Blocker 2 — Stage-1 Johns-Manville Waukegan Candidate — 2026-07-21

Status: rejected for direct calibration. Johns-Manville Corp. OU1 in Waukegan, Illinois, does not provide a clean isolated post-2015 cap experiment. Blocker 2 remains unresolved. No calibration-pack intake, training, or app-depth enablement is authorized from this candidate.

## Verified public facts

- EPA describes the property as approximately 350 acres, including an approximately 150-acre waste-disposal area identified as OU1.
- EPA records OU1 construction completion in 2018, with the main excavation and capping work completed in 2017.
- The 2017 closeout covered several different site elements: the on-site landfill, wastewater-treatment areas, manufacturing areas, perimeter roads, and related areas.
- The work used multiple interventions, including excavation, rock cover, vegetated cover, clean soil, roadway material, and a new stormwater-drainage system.
- EPA held closure inspections in 2018 and lists a Final Closure Report for the Non-Asbestos-Containing On-Site Landfill.
- EPA's 2023 five-year-review summary states that the cover remains intact and the OU1 remedy is functioning as intended.
- The publicly indexed EPA material reviewed did not expose numerical survey accuracy, an extractable final as-built surface, or a later repeat topographic survey suitable for settlement measurement.
- The large EPA PDF endpoints did not load successfully in the review environment, so no missing survey values were inferred from inaccessible attachments.

## Classification

```text
candidate_id = N1-15
candidate_state = rejected_direct_calibration
sentinel_1_era_cap_event = pass
whole_landfill_cap = fail_mixed_ou1_closeout
large_analysis_footprint = pass
post_closure_review = pass
as_built_depth_to_top = unresolved
numerical_survey_uncertainty = unresolved
observation_date_settlement = unresolved
clean_s1_experiment_unit = fail
R1_depth_measurability = not_tested
R5_radar_linkage = not_tested
```

## Decision

Reject Johns-Manville Waukegan for direct calibration.

The timing and footprint are attractive, and a named final closure report exists. However, EPA describes the 2017–2018 event as a broad OU1 closeout involving multiple physical interventions across several site components rather than one isolated whole-landfill cap installation. Excavation, different cover materials, road work, vegetation, and stormwater construction would overlap in the Sentinel-1 signal and prevent a defensible cap-depth label.

Do not promote the candidate merely because the later review confirms that the remedy remains intact. Cover integrity is not a survey-grade depth or settlement measurement.

## Reuse value

```text
method_or_negative_control = possible
clean_direct_depth_calibration = no
future_reconsideration = only_if_report_exposes_a_separate_isolated_landfill_polygon_with_certified_surveys
```

## Next step

Continue screening modern single-unit landfill or CCR closures where one clearly bounded cap was installed and the construction certification includes accessible as-built contours, stated survey accuracy, and a later comparable surface survey.

## Public references

- EPA cleanup page: `https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.cleanup&id=0500197`
- EPA documents page: `https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.docdata&id=0500197`
- Final Closure Report endpoint listed by EPA: `https://semspub.epa.gov/src/document/05/944773`
- Sixth Five-Year Review endpoint listed by EPA: `https://semspub.epa.gov/src/document/05/981906`
