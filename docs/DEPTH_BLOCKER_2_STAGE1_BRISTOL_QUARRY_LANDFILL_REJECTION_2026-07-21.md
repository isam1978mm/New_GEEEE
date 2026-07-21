# Blocker 2 — Stage-1 Bristol Quarry Landfill Rejection — 2026-07-21

Status: Stage-1 screen complete. Bristol Quarry Landfill, Bristol, Virginia, is classified `rejected_mixed_remediation_not_completed_cap`. Blocker 2 remains unresolved. No calibration-pack intake, training, or app-depth enablement is authorized from this site.

## Verified official public facts

- The City of Bristol states that the quarry landfill stopped accepting waste on September 9, 2022.
- The 2022 Virginia DEQ-convened Expert Panel reviewed four top-of-waste surveys collected from June 2020 through November 2021, using more than 300 grid survey points across the landfill surface.
- Those surveys showed strong ongoing and spatially variable settlement while waste placement was still occurring; the June-to-November 2021 comparison indicated a net volume decrease of nearly 13,000 cubic yards despite continued waste receipt.
- The Expert Panel recommended monthly settlement monitoring, settlement plates, drone or GPS surveys, extensive grading, a temporary geomembrane cover, expanded gas and leachate systems, and later permanent closure.
- The City completed intermediate cover in October 2022 and continued major remediation work involving grading, gas extraction, leachate extraction, stormwater work, sidewall sealing, soil placement, and cover-system planning.
- A March 2024 City update states that the landfill surface had been deliberately reshaped and that this work caused settlement beyond normal waste aging. The proposed geomembrane cover was delayed so experts could measure the settlement rate first.
- In March 2026, the City stated that the landfill continued to experience settlement and that the exact timing for permanent geomembrane installation had not been determined.
- The January 2026 amended consent decree still conditions geomembrane installation on future settlement criteria and then allows twelve months for installation after those criteria are met.
- July 2026 City updates still describe active gas-system and remediation work, not completed final-cover construction.

## Classification

```text
candidate_id = BRISTOL-QUARRY-2022
candidate_state = rejected_mixed_remediation_not_completed_cap
sentinel_1_era_waste_cessation = pass_2022_09_09
final_cover_completed = fail_as_of_2026_07
repeat_topographic_surveys = pass_2020_to_2021_operational_surface
survey_grid_density = promising_more_than_300_points
clean_pre_cap_surface = fail_waste_placement_and_surface_shaping_overlap
clean_post_cap_surface = fail_no_permanent_cap_yet
single_cap_event = fail
abnormal_elevated_temperature_landfill = confounder
ongoing_regrading_and_soil_placement = confounder
ongoing_gas_leachate_and_stormwater_work = confounder
natural_settlement_separable_from_remediation = fail
final_cqa_report = not_applicable_not_completed
final_as_built_contours = not_available_not_completed
later_repeat_cap_surface = not_available_not_completed
R1_depth_measurability = not_eligible
R5_radar_linkage = not_eligible
```

## Decision

Reject Bristol Quarry Landfill as a calibration candidate.

The site has unusually strong survey evidence, but it measures an active, abnormal, highly settling waste mass during and after operational shutdown. The surface was repeatedly reshaped, covered with intermediate materials, regraded, repaired with additional soil, and modified for gas, leachate, sidewall, and stormwater systems. The permanent geomembrane cap was still not installed as of March 2026.

Therefore, any Sentinel-1 change would combine waste placement history, elevated-temperature behavior, rapid settlement, regrading, added soil, temporary/intermediate cover, gas and leachate construction, and other remediation. It cannot isolate a known final-cover thickness or a clean buried-mass depth response.

## Waiting for

Nothing for the current calibration screen. Reconsideration would require a future completed permanent cap, certified final CQA/as-built surface, and a later repeat survey after major remediation and regrading have ceased. Even then, the abnormal settlement history would remain a major exclusion risk.

## Next step

Continue screening another 2016–2021 completed closure where the permanent final cap was built in one separable event and a five-year repeat survey is already public.

## Public references

- City of Bristol landfill status and closure date: `https://www.bristolva.gov/641/Landfill-Solid-Waste`
- Official Expert Panel report with 2020–2021 survey evidence and settlement findings: `https://www.bristolva.gov/649/Bristol-Landfill-Expert-Panel-Report`
- City November 2022 remediation and intermediate-cover timeline: `https://www.bristolva.gov/Blog.aspx?IID=84`
- City March 2024 cover-delay and settlement update: `https://bristolva.gov/Blog.asp?IID=175`
- City March 2026 amended-cover and ongoing-settlement update: `https://www.bristolva.gov/Blog.aspx?IID=296`
- Current City landfill-update index through July 2026: `https://www.bristolva.gov/Blog.aspx?CID=1`
- Virginia DEQ Bristol Landfill page: `https://www.deq.virginia.gov/news-info/shortcuts/topics-of-interest/bristol-landfill`
