# Blocker 2 — Stage-1 Contra Costa Sanitary Landfill Rejection — 2026-07-21

Status: Rejected for direct Sentinel-1 depth calibration. Retained only as a method-quality example of a final-cover baseline followed by repeat iso-settlement mapping. Blocker 2 remains unresolved. No calibration-pack intake, training, or app-depth enablement is authorized from this site.

## Verified official public facts

- The Contra Costa Sanitary Landfill stopped receiving waste on 31 March 1992.
- Final-cover closure construction was completed in spring 2002.
- The Central Valley Water Board approved the closure CQA report and issued closure certification on 7 August 2002.
- The constructed cover included engineered foundation fill and either geosynthetic-clay or compacted-clay low-conductivity layers, with vegetative soil above.
- A five-year iso-settlement map was prepared in November 2016.
- The 2016 map reported average settlement of about 1 to 2 feet on the top deck, less than 1 foot on slopes, and localized maximum settlement up to about 5 feet at the eastern end of the top deck.
- The order requires continued five-year iso-settlement mapping and evaluation of cover integrity and positive drainage.
- The official PDF was text-readable, but page-image rendering failed with a cache-miss; the numerical findings therefore come from the regulator's parsed text, not a manually inspected map image.

## Classification

```text
candidate_id = CCSL-2002
candidate_state = rejected_pre_sentinel_1
closure_completed = pass_2002
final_cqa_and_certification = pass
final_cover_layers = pass_documented
later_iso_settlement_survey = pass_2016
settlement_magnitude_reported = pass
sentinel_1_era_cap_event = fail
clean_before_after_s1_sequence = fail
R1_depth_measurability = method_reference_only
R5_radar_linkage = not_testable_for_cap_event
```

## Decision

Reject for direct calibration because the cap event occurred in 2002, well before Sentinel-1 observations began. The later 2016 iso-settlement survey is useful for understanding how regulators document landfill settlement, but it cannot supply the required Sentinel-1 before-cap and after-cap sequence.

This site is not evidence that the app can estimate depth. It is only a strong example of the engineering record format still being sought at a post-2015 closure.

## Waiting for

```text
nothing_from_this_site_for_direct_calibration
```

## Next step

Continue screening post-2015 completed closures for the same evidence quality: certified final as-built surface, explicit survey control/accuracy, and a later repeat iso-settlement or topographic survey over the same isolated cap footprint.

## Public reference

- California Regional Water Quality Control Board, Central Valley Region, Waste Discharge Requirements Order R5-2020-0011, Contra Costa Sanitary Landfill: `https://www.waterboards.ca.gov/rwqcb5/board_decisions/adopted_orders/contra_costa/r5-2020-0011_wdr.pdf`
