# Blocker 2 — Stage-1 Elizabethtown Landfill Rejection — 2026-07-21

Status: Stage 1 remains active. Elizabethtown Landfill is rejected for the modern post-2015 cap-construction lane. Blocker 2 remains unresolved. No calibration-pack intake, model fitting, or app-depth enablement is authorized.

## Verified public facts

- EPA identifies the site as an inactive approximately 16-acre landfill in Pennsylvania.
- The landfill cap itself was completed in 2003.
- EPA records a later remedial-design period from 2016 to 2021 and a final remedial-action period from September 2021 to June 2023.
- EPA's cleanup page states that the later work was construction of the groundwater remedy, not a new landfill cap.
- The site reached construction complete on June 9, 2023 and sitewide-ready status on August 1, 2023.

## Classification

```text
candidate_id = N1-10
candidate_state_for_direct_depth_calibration = rejected_scale_or_sensor_mismatch
modern_cap_construction_event = fail
landfill_cap_completion_date = 2003
later_2021_2023_work = groundwater_remedy
usable_sentinel_1_pre_post_cap_event = fail
as_built_depth_to_top = unavailable_for_modern_event
numerical_survey_uncertainty = unavailable_for_modern_event
observation_date_settlement = unavailable_for_modern_event
R1_depth_measurability = not_tested
R5_radar_linkage = not_tested
```

## Decision

Do not use Elizabethtown as a post-2015 direct depth-positive candidate. The cap predates Sentinel-1 operational coverage; the 2021–2023 construction milestone concerns groundwater treatment rather than a new cap.

## Waiting for

```text
post_2015_whole_cell_cap_construction
+ certified_top_of_waste_or_subgrade_survey
+ certified_final_surface_survey
+ explicit_survey_accuracy
+ later_settlement_or_topography
```

## Next step

Keep North Sanitary Landfill as the strongest active modern lead and continue searching for a second completed 2015–2026 whole-cell cap with smaller accessible as-built files.

## Public references

- EPA cleanup page: `https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.cleanup&id=0301361`
- EPA schedule page: `https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.schedule&id=0301361`
- EPA document page: `https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.docdata&id=0301361`
