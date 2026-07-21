# Blocker 2 — Stage-1 Go East Candidate — 2026-07-21

Status: rejected for direct calibration. Go East Corp Landfill, Washington, has unusually strong public construction documentation, but the closure event is not a clean isolated cap experiment. Blocker 2 remains unresolved. No calibration-pack intake, training, or app-depth enablement is authorized from this candidate.

## Verified public facts

- Washington Ecology identifies the nominal property as approximately 40–41 acres and the historical landfill as approximately 10 acres.
- P&GE consolidated the landfill footprint to approximately 6 acres and completed closure in July 2022.
- The closure work occurred from March 2021 through July 2022.
- A PE-certified Construction Quality Assurance Report is publicly available.
- A separate public Appendix O contains as-built/record drawings prepared from licensed survey work.
- The CQA report states that the as-built drawings show approximate final grades; it does not state a numerical horizontal or vertical survey accuracy in the accessible report text.
- The project included landfill-edge excavation, relocation and consolidation of waste, imported structural fill, final grading, geomembrane installation, stormwater construction, stream diversion, deep dynamic compaction, gas controls, and subdivision-related grading.
- Final topsoil and several surface improvements over the closed landfill were scheduled under a later development phase after the primary closure report.
- Later public monitoring records focus on landfill gas, groundwater, and surface water; no repeat survey-grade landfill-surface dataset suitable for settlement comparison was identified.

## Classification

```text
candidate_id = N1-16
candidate_state = rejected_mixed_construction_event
sentinel_1_era_cap_event = pass
whole_landfill_cap = fail_consolidated_reduced_footprint
large_analysis_footprint = fail_approximately_6_acres
post_closure_review = pass_non_topographic_monitoring
as_built_depth_to_top = approximate_grades_only
numerical_survey_uncertainty = unresolved
observation_date_settlement = unresolved
clean_s1_experiment_unit = fail
R1_depth_measurability = not_tested_candidate_rejected
R5_radar_linkage = not_tested_candidate_rejected
```

## Decision

Reject Go East for direct calibration.

The available as-built documentation is stronger than for most screened candidates, but the physical event is too mixed to isolate a cap-depth signal. Waste was excavated and consolidated, the landfill footprint changed, large quantities of fill were imported, the entire property was regraded, and stormwater, stream, gas-control, compaction, and subdivision work overlapped the closure period. The final cap footprint is also only about 6 acres, limiting the number of independent Sentinel-1 pixels.

Do not treat the publicly available record drawings as sufficient calibration truth. The accessible report describes approximate final grades and does not provide explicit numerical survey accuracy or a later comparable topographic survey.

## Useful method evidence

Go East remains useful as a documentation-quality example because it demonstrates what a strong public closure package can contain:

```text
PE-certified CQA report
+ named licensed surveyor
+ separate record drawings
+ construction chronology
+ material and geomembrane records
+ later regulatory monitoring
```

It must remain excluded from the direct depth-calibration candidate set.

## Next step

Continue screening recent single-unit landfill or CCR closures. Prefer projects where the final-cover construction is isolated from waste relocation, major excavation, subdivision grading, stream work, or other large surface changes, and where both the construction as-built surface and a later repeat topographic survey are public.

## Public references

- Washington Ecology site record: `https://apps.ecology.wa.gov/cleanupsearch/site/4294`
- Construction Quality Assurance Report: `https://apps.ecology.wa.gov/cleanupsearch/document/113990`
- As-Built/Record Drawings: `https://apps.ecology.wa.gov/cleanupsearch/document/113994`
