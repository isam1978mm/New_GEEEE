# Blocker 2 — Stage-1 Cummings Road Landfill Rejection — 2026-07-21

Status: Stage 1 rejected. Cummings Road Landfill, Humboldt County, California, is not eligible for the current clean Sentinel-1 cap-event calibration screen. Blocker 2 remains unresolved. No calibration-pack intake, training, or app-depth enablement is authorized.

## Verified official public facts

- Humboldt Waste Management Authority states that the landfill contains roughly 1,450,000 cubic yards of waste and was closed through a phased program.
- Phase 1 covered approximately 21.5 acres and was completed in 2012.
- During 2014, approximately 91,000 cubic yards of burn-ash debris from an adjacent site were excavated and relocated into the Phase 2 area inside the landfill footprint.
- Phase 2 covered approximately 10.5 acres and underwent final closure in summer 2015.
- Closure certification was approved in mid-February 2017; the Authority separately summarizes construction closure activities as completed in 2016.
- The Water Board order required each closure report to include final CQA documentation and an as-built topographic map at 1 inch = 100 feet with 2-foot contours.
- The order required iso-settlement maps by January 2018 and January 2023, tied to the closure-report baseline surface and showing total lowering of the low-hydraulic-conductivity layer.
- Four survey monument control points were established outside the waste footprint.

## Evidence and access limitations

- Public web searches did not locate the actual 2018 or 2023 iso-settlement map submissions or their native survey points.
- The Water Board PDF text was retrievable and indexed, but screenshot rendering failed with a cache-miss error. No map or drawing was visually interpreted from that failed render.
- The rejection does not depend on the missing repeat-survey files because the construction history already fails the clean-event requirement.

## Classification

```text
candidate_id = CUMMINGS_ROAD_2015
candidate_state = rejected_mixed_phased_relocation
sentinel_1_era_cap_event = partial_pass_phase2_2015
closure_completed = pass_2016_summary_and_2017_certification
single_recent_closure_period = fail_phased_2012_and_2015
waste_left_in_place = fail_2014_burn_ash_relocation_into_phase2
clean_cap_only_surface_change = fail
final_cqa_as_built_required = pass_requirement_only
survey_monuments = pass_four_off_footprint_controls
2018_iso_settlement_required = pass_requirement_only
2023_iso_settlement_required = pass_requirement_only
actual_repeat_surveys_publicly_verified = unresolved_not_found
clean_s1_experiment_unit = fail
R1_depth_measurability = not_tested_rejected_event
R5_radar_linkage = not_tested_rejected_event
```

## Decision

Reject Cummings Road from direct depth calibration.

The site has unusually strong survey requirements and would be useful as a documentation-method example, but the target surface was created through phased closure and was preceded by major waste excavation and relocation into the Phase 2 footprint. Any Sentinel-1 change would mix capping, imported/relocated waste mass, grading, drainage work, and different closure years rather than represent one isolated cap-only event.

## Waiting for

```text
nothing_for_current_candidate
```

The 2018 and 2023 iso-settlement maps could still be useful later for method development, but they cannot repair the failed event-isolation criterion.

## Next step

Screen another post-2015 landfill where closure occurred in one isolated footprint, waste remained in place, and both the final as-built surface and a later repeat survey are publicly retrievable.

## Public references

- Official Humboldt Waste Management Authority Cummings Road Landfill history and closure summary: `https://www.hwma.net/cummings-road-landfill`
- Official Humboldt Waste Management Authority organization summary noting closure-construction completion in 2016: `https://www.hwma.net/about-us`
- North Coast Regional Water Quality Control Board Order R1-2012-0063: `https://www.waterboards.ca.gov/northcoast/board_info/board_meetings/08_2012/pdf/hwma/12_0063_WDR_CummingsRoad_SWDS.pdf`
