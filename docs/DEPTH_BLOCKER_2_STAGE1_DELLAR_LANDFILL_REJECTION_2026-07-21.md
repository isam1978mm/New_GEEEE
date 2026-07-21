# Blocker 2 — Stage-1 Dellar Landfill Rejection — 2026-07-21

Status: Stage 1 screened. Dellar Landfill, Sacramento County, California, is rejected for the current Sentinel-1 depth-calibration candidate set. Blocker 2 remains unresolved. No calibration-pack intake, training, or app-depth enablement is authorized.

## Verified public facts

- The Central Valley Water Board identifies Dellar as an unclassified/closed landfill subject to closure, post-closure maintenance, and corrective-action monitoring.
- Waste disposal ceased in 1963, making the landfill a closed/abandoned/inactive unit long before Sentinel-1.
- Cleanup and Abatement Order R5-2008-0705 required closure as a corrective action, including imported soil, grading, an engineered cover, drainage controls, and post-closure monitoring.
- The 2008 closure schedule called for engineered-cover construction to begin on 1 June 2010, finish by 30 October 2010, and submit the closure-certification/CQA/as-built package by 15 December 2010.
- The 2015 Waste Discharge Requirements state that final cover had been installed over most of the approximately 23.9-acre landfill footprint under a 2011 partial closure plan, while remaining areas still required closure.
- City of Sacramento records in 2025 still identify a combined Cannon-Scollan Landfill and Dellar Slope Closure project, confirming that closure work remained phased and incomplete as a single event.

## Evidence and access limitations

- The 2008 official PDF was text-readable through the public index. A page screenshot was attempted but the host returned a cache-miss error.
- The 2015 official PDF was search-indexed but its direct PDF endpoint also returned a cache-miss error during retrieval.
- No public survey-grade before/after pair with common datum, explicit accuracy, and a later repeat cap surface was located.

## Classification

```text
candidate_id = DELLAR-CA
candidate_state = rejected
waste_disposal_ended = 1963
sentinel_1_era_primary_cap_event = fail
primary_engineered_cover_period = 2010_to_2011_pre_sentinel_1
closure_completed_as_one_event = fail_phased
corrective_action_and_remediation = present
single_clean_cap_only_footprint = fail
final_as_built_surface_publicly_verified = unresolved
later_repeat_surface_survey = unresolved
survey_datum_and_accuracy = unresolved
R1_depth_measurability = not_tested_rejected
R5_radar_linkage = not_tested_rejected
```

## Decision

Reject Dellar for direct depth calibration. Its main engineered-cover construction occurred before Sentinel-1, and the remaining work has continued as phased corrective-action and slope-closure construction rather than one isolated modern cap event. Even if later surveys are found, they would not provide the required clean pre-cap/post-cap Sentinel-1 sequence.

## Waiting for

```text
nothing_for_current_candidate_screen
```

## Next step

Continue screening a landfill with one completed 2016–2021 final-cover event and an already available five-year repeat survey or settlement map tied to the same survey control.

## Public references

- Central Valley Water Board adopted-orders index for Dellar Landfill: `https://www.waterboards.ca.gov/rwqcb5/board_decisions/adopted_orders/`
- Cleanup and Abatement Order R5-2008-0705: `https://www.waterboards.ca.gov/centralvalley/board_decisions/adopted_orders/sacramento/r5-2008-0705_enf.pdf`
- Waste Discharge Requirements R5-2015-0051: `https://www.waterboards.ca.gov/centralvalley/board_decisions/adopted_orders/sacramento/r5-2015-0051.pdf`
- City of Sacramento 2025 Cannon-Scollan Landfill and Dellar Slope Closure item: `https://sacramento.granicus.com/GeneratedAgendaViewer.php?event_id=5463&view_id=22`
