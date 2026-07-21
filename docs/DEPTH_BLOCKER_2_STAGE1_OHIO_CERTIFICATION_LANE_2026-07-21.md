# Blocker 2 — Stage-1 Ohio Certification Lane — 2026-07-21

Status: Stage 1 remains active. This note records a new high-yield public-document lane. Blocker 2 remains unresolved. No calibration-pack intake, model fitting, app-depth enablement, contact, or fieldwork is authorized.

## Current decision

```text
stage_1_status = active
new_source_lane = ohio_landfill_cap_construction_certification_reports
contract_complete_positive_records = 0
formal_reopen_status = not_requested
depth_training = blocked
app_depth_enabled = false
```

## Why this lane is promising

Ohio landfill construction rules require professional-engineer certification reports containing survey grids, record drawings, and cap cross-sections. For cap certification, the records must show:

- top elevations of existing waste or industrial/residual material;
- top elevations of the final cap system;
- cap component thickness checks;
- plan views and cross-sections;
- survey points and construction certification records.

This is closer to the Blocker-2 depth-to-top requirement than ordinary closure plans or landfill inventories.

## What is still missing

The regulation proves the required document structure exists. It does not itself provide an eligible calibration record.

A usable facility package still needs:

```text
post_2015_completed_cap_event
+ public_facility_specific_certification_report
+ explicit_survey_accuracy_or_tolerance
+ observation_date_settlement_or_later_topography
+ clean_sentinel_1_pre_and_post_support
+ defensible_whole_site_or_isolated_section_unit
```

## Rejected or limited findings from this pass

- Orange County Landfill, New York: 2021 final engineering report concerns seep corrective measures, not final landfill closure; not a depth-positive record.
- Cuba Municipal Waste Disposal Site, New York: closure construction predates Sentinel-1 operational coverage; method/history only.
- Onondaga Lake sediment cap: contains as-built and later bathymetric monitoring, but the cap is submerged and is not a valid Sentinel-1 landfill-depth candidate.

## Candidate state

```text
source_lane_state = candidate_under_review
R1_depth_measurability = not_tested_pending_stage_3
R5_radar_linkage = not_tested_pending_stage_3
```

## Waiting for

A named Ohio facility with a publicly retrievable post-2015 cap construction certification report and later settlement or topographic records.

## Next step

1. Search Ohio sanitary, industrial, residual, and C&D landfill facility files for completed cap certification reports from 2015–2026.
2. Extract top-of-waste/material elevations, cap elevations, survey spacing, stated accuracy/tolerance, closure dates, and later settlement evidence.
3. Retain only facility-specific records; reject regulation-only, design-only, pre-Sentinel-1, submerged, or corrective-action-only sources.
4. Keep all surviving rows below `direct_calibration_candidate` until Stage 3 radar linkage is demonstrated.

## Public references

- Ohio Administrative Code 3745-27-08 and 3745-27-11.
- Ohio Administrative Code 3745-30-07 and 3745-30-09.
- Ohio Administrative Code 3745-400-08 and 3745-400-12.
