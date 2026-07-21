# Blocker 2 — Stage-1 Foothill LF-1 Rejection — 2026-07-21

Status: rejected for direct calibration. Foothill Landfill LF-1, San Joaquin County, California, is retained only as evidence that strong survey requirements do not automatically produce a clean Sentinel-1 calibration event.

## Verified public facts

- LF-1 is an approximately 84-acre unlined landfill unit.
- Its top deck was already partially closed with an evapotranspiration cover in 2006.
- The remaining side slopes were required to be fully closed by November 2018.
- California required a final-cover survey after closure and five-year iso-settlement surveys using the closure survey as the baseline.
- The unit is physically and operationally tied to the surrounding LF-2 expansion; some LF-1 side slopes may function as both LF-1 final cover and LF-2 side-slope liner.
- The governing order allowed inert material or relocation of existing waste within LF-1 under approved closure work.
- No publicly indexed final 2018 as-built contour package or later five-year iso-settlement map was located during this screen.

## Classification

```text
candidate_id = N1-18
candidate_state = rejected_direct_calibration
sentinel_1_era_cap_event = partial_only
whole_landfill_single_event = fail
waste_left_in_place = mixed_or_unresolved
public_as_built_contours = required_but_not_located
public_repeat_surface_survey = required_but_not_located
survey_control_framework = pass_at_regulatory_level
clean_s1_experiment_unit = fail
R1_depth_measurability = not_tested
R5_radar_linkage = not_tested
```

## Decision

Reject Foothill LF-1 for direct calibration.

The site has an unusually strong regulatory survey framework, but the physical event is not clean enough. The top deck predates Sentinel-1, later work applies mainly to remaining slopes, portions overlap the active LF-2 development, and the closure authorization allows some material relocation. Even if the missing survey files become accessible, the event would remain difficult to interpret as one known cap-depth change over one stable waste mass.

## Waiting for

Nothing for direct calibration. Do not spend further Stage-1 time trying to recover Foothill LF-1 survey files unless the project later needs a method-only example of California settlement-survey practice.

## Next step

Continue screening post-2015 single-unit closures where the entire analysis footprint was capped in one event, waste remained in place, and both the final as-built surface and later repeat survey are directly downloadable.

## Public references

- California Central Valley Water Board Order R5-2015-0058: `https://www.waterboards.ca.gov/centralvalley/board_decisions/adopted_orders/san_joaquin/r5-2015-0058.pdf`
- California final-cover and five-year iso-settlement survey rule: `https://www.law.cornell.edu/regulations/california/27-CCR-21090`
