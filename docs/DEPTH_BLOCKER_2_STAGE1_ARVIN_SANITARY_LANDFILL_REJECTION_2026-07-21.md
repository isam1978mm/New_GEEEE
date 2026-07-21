# Blocker 2 — Stage-1 Arvin Sanitary Landfill Rejection — 2026-07-21

Status: Stage 1 screened and rejected for direct Sentinel-1 depth calibration. Blocker 2 remains unresolved. No calibration-pack intake, training, or app-depth enablement is authorized.

## Verified public facts

- The County of Kern owns and maintains the Arvin Sanitary Landfill in Kern County, California.
- The landfill is a 128-acre closed Class III unit.
- Landfill operations ceased on 30 June 2003 after the unit reached about 97% of design capacity.
- The waste unit was closed with a three-foot-thick evapotranspirative final cover.
- Construction of that final cover was completed in late 2013.
- The facility filed termination of construction stormwater coverage in September 2013 because final-cover construction and cleanup were complete; the Water Board approved the termination in October 2013.
- California post-closure rules may require repeat iso-settlement surveys, but any such later survey cannot create a Sentinel-1 before/after cap-construction sequence because the cap was completed before Sentinel-1 observations began.

## Classification

```text
candidate_id = N1-23
candidate_state = rejected_pre_sentinel_1
closure_event_completed = pass
single_large_landfill_unit = pass
waste_left_in_place = likely_pass
known_final_cover_thickness = pass_3_ft_ET_cover
final_as_built_contours = not_pursued_after_timing_failure
numerical_survey_uncertainty = not_pursued_after_timing_failure
later_repeat_topographic_survey = possible_but_not_material_to_modern_cap_event
sentinel_1_era_cap_event = fail_completed_late_2013
clean_s1_experiment_unit = fail_timing
R1_depth_measurability = not_tested
R5_radar_linkage = not_tested
```

## Decision

Reject Arvin for direct calibration. It is a strong example of a large waste-in-place closure with a defined three-foot ET cover, but the cap construction was complete in late 2013. Therefore Sentinel-1 cannot observe both the pre-cap and immediate post-cap states.

Do not spend additional research time retrieving Arvin's later iso-settlement maps for the current calibration pack. They could support general settlement-method research, but not the required modern cap-event calibration sequence.

## Waiting for

```text
completed_post_2015_single_unit_closure
+ waste_left_in_place
+ public_pre_cap_or_top_of_waste_surface
+ public_final_as_built_surface
+ explicit_datum_and_survey_accuracy
+ later_repeat_topographic_or_settlement_survey
```

## Next step

Continue screening completed post-2015 single-unit closures. Prioritize municipal or CCR sites with a posted final CQA package and a later measured surface survey, not merely visual inspection records or regulatory requirements.

## Public references

- Central Valley Water Board 2021 Arvin Sanitary Landfill WDR package: `https://www.waterboards.ca.gov/centralvalley/board_decisions/tentative_orders/2110/16_uncon_wdrs/16b_arvinlf/arvinlandfill_wdrs.pdf`
- Central Valley Water Board October 2021 meeting page: `https://www.waterboards.ca.gov/centralvalley/board_decisions/tentative_orders/2110/`
- CIWQS facility page for Arvin Sanitary Landfill: `https://ciwqs.waterboards.ca.gov/ciwqs/readOnly/CiwqsReportServlet?placeID=206513&reportName=facilityAtAGlance`

## Retrieval note

The official PDF text was accessible through the public Water Board document interface. A page-image screenshot request was also attempted, but the remote screenshot service returned a cache-miss error; no visual figure or drawing was used as evidence.