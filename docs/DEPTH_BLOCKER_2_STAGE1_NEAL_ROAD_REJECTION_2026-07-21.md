# Blocker 2 — Stage-1 Neal Road Rejection — 2026-07-21

Status: Rejected for direct Sentinel-1 cap-depth calibration. Neal Road remains useful only as method evidence for final-cover and repeat iso-settlement survey requirements. Blocker 2 remains unresolved. No calibration-pack intake, model fitting, or app-depth enablement is authorized.

## Verified public facts

- The 2022 Central Valley Water Board order identifies Modules 1, 2, and 3 as closed landfill units.
- Closure of Modules 1, 2, and 3 with a low-permeability cap was completed in March 2007.
- The closure was documented in 2005 Phase 1 and 2007 Phase 2 final partial-closure CQA reports.
- Module 1 is about 23 acres, Module 2 about 16.5 acres, and Module 3 about 26.5 acres.
- The order requires an initial final-cover survey and map after closure.
- It also requires a five-year survey and iso-settlement map showing total elevation change of the low-hydraulic-conductivity layer.
- The accompanying monitoring program states that the next iso-settlement maps for Modules 1, 2, and 3 were due in 2022.
- The public sources reviewed here did not expose the actual 2022 submitted iso-settlement maps, survey-point tables, datum, or numerical survey accuracy.

## Classification

```text
candidate_id = N1-18
candidate_state = rejected_pre_sentinel_1
waste_left_in_place = pass
engineered_final_cover = pass
large_analysis_footprint = pass
initial_final_cover_survey_required = pass
repeat_iso_settlement_survey_required = pass
actual_repeat_map_publicly_extracted = fail_current_public_interface
closure_completion_date = 2007-03
sentinel_1_era_cap_event = fail
clean_s1_before_after_cap_experiment = fail
method_evidence_value = high
R1_depth_measurability = not_tested
R5_radar_linkage = not_tested
```

## Decision

Reject Neal Road for direct cap-construction calibration because the relevant closure was completed in 2007, years before Sentinel-1 acquisition began. A 2022 iso-settlement map could support long-term settlement research, but it cannot provide the required Sentinel-1 before-cap and after-cap sequence for this closure event.

Retain Neal Road only as evidence that a strong public record structure can include:

- an initial final-cover survey and map;
- permanent survey control;
- five-year repeat surveys;
- iso-settlement mapping of the low-hydraulic-conductivity layer;
- closure CQA documentation.

## Missing public records

```text
actual_2022_iso_settlement_map
+ survey_point_or_contour_data
+ horizontal_and_vertical_datum
+ numerical_survey_accuracy
```

Obtaining those records would not change the pre-Sentinel-1 rejection, but they could be useful later for validating settlement-detection methods.

## Next step

Move to a completed post-2015 closure. Prioritize Yorktown follow-up records or a different site whose initial final-cover survey and first repeat survey both fall inside the Sentinel-1 era.

## Public references

- Central Valley Water Board 2022 Neal Road WDR: `https://www.waterboards.ca.gov/centralvalley/board_decisions/tentative_orders/2202/12_uncont_wdr/12b_butteco/nealrd_wdr.pdf`
- Central Valley Water Board 2022 Neal Road monitoring and reporting program: `https://www.waterboards.ca.gov/centralvalley/board_decisions/tentative_orders/2202/12_uncont_wdr/12b_butteco/nealrd_mrp.pdf`
- Butte County Surveys Division: `https://www.buttecounty.net/907/Surveys`
