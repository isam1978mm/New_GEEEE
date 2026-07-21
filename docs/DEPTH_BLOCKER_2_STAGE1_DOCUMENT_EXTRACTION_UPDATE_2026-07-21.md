# Blocker 2 — Stage-1 Document Extraction Update — 2026-07-21

Status: Stage 1 remains active. This update records document-level findings for Sudbury Road Landfill and Brookfield Avenue Landfill. Blocker 2 remains unresolved. No calibration-pack intake, model fitting, app-depth enablement, contact, or fieldwork is authorized.

Read with:

- `docs/DEPTH_BLOCKER_2_LANDFILL_CQA_CANDIDATE_SCREENING_PLAN_2026-07-21.md`
- `docs/DEPTH_BLOCKER_2_PUBLIC_LANDFILL_SOURCE_MAP_AND_STAGE1_START_2026-07-21.md`
- `docs/DEPTH_CALIBRATION_DATASET_CONTRACT.md`

## Current decision

```text
stage_1_status = active
blocker_2_status = unresolved
contract_complete_positive_records = 0
contract_complete_negative_records = 0
formal_reopen_status = not_requested
depth_training = blocked
app_depth_enabled = false
```

## Finding 1 — Sudbury Road Landfill provides a strong design-depth lead, but not yet an as-built calibration record

Public source:

- Washington Department of Ecology, `Construction Plans and Specs - Vol III CQA - Final`, January 2016.
- Washington Department of Ecology site record lists a separate `Construction Quality Assurance Certification Report`, dated April 14, 2017, and `Sudbury Landfill Periodic Review 2022`, dated July 5, 2022.

Document-level findings from the CQA manual:

- the closure work covered Areas 2 and 5;
- the cover subgrade elevations were designed at 5 feet below finished grade;
- the manual required a minimum 4.8 feet of soil cover;
- the CQA monitor was required to verify soil-cover thickness;
- an as-built survey of final grade was required;
- final-grading tolerance had to be checked, but no numerical tolerance was recovered from the reviewed manual.

Current classification:

```text
candidate_id = N1-02
candidate_state = candidate_under_review
design_depth_reference = pass
as_built_depth_to_top = unresolved
numerical_uncertainty = unresolved
observation_date_settlement = unresolved
sentinel_1_pre_post_support = not_yet_screened
R1_depth_measurability = not_tested_pending_stage_3
R5_radar_linkage = not_tested_pending_stage_3
```

Decision:

- retain Sudbury as the highest-priority Washington candidate;
- do not use 4.8 feet as `known_depth_top_m` until the final CQA report or record drawings prove the installed condition;
- do not treat a stated design tolerance requirement as numerical uncertainty;
- continue searching for the 2017 as-built survey material and the 2022 later-condition evidence.

## Finding 2 — Brookfield Avenue proves that the desired public record structure exists

Public source:

- New York State Department of Environmental Conservation, `Brookfield Avenue Landfill Remediation — Final Engineering Report`, October 2014.

Document-level findings:

- the landfill property covered approximately 272 acres, with approximately 128 acres receiving a Part 360 cap;
- the contractor's surveyor performed a certified top-of-waste topographic survey before imported cover material was placed;
- the certified top-of-waste survey was used as the baseline for later layer thickness and settlement review;
- a separate certified top-of-intermediate-subgrade survey was produced;
- the intermediate-subgrade record drawing used a 50-foot grid and reported elevations to the hundredth of a foot;
- the cap included a minimum 12-inch intermediate layer, geosynthetics, a minimum 12-inch barrier-protection layer, and topsoil;
- GPS-guided equipment, surveyed liner elevations, grade stakes, and periodic test holes were used during later layer placement;
- public post-closure reports exist for later years, but no survey-grade settlement table or numerical measurement uncertainty was extracted in this pass.

Important uncertainty rule:

```text
reported_elevation_resolution = 0.01_ft
reported_elevation_resolution_is_not_measurement_uncertainty = true
```

A coordinate printed to the hundredth of a foot does not by itself establish survey accuracy, tolerance, or a contract-valid uncertainty interval.

## Brookfield temporal mismatch with Sentinel-1

The engineering report states that the primary landfill closure milestone was substantially complete on December 31, 2013. Public Sentinel-1A operational data became available in October 2014.

Therefore Brookfield cannot provide the approved Sentinel-1 pre-construction versus post-construction experiment for the main cap event.

Current classification:

```text
candidate_id = N1-07
source_record_quality = strong
depth_reference_geometry = strong
numerical_uncertainty = unresolved
observation_date_settlement = unresolved
sentinel_1_pre_event_availability = fail_for_main_closure_event
candidate_state_for_direct_s1_calibration = rejected_scale_or_sensor_mismatch
candidate_state_for_document_method_research = method_research_only
R1_depth_measurability = not_tested
R5_radar_linkage = not_tested
```

Decision:

- do not import Brookfield into the Sentinel-1 calibration pack;
- retain it as method-research evidence showing that public final-engineering reports can contain certified top-of-waste and layer-elevation surveys;
- use its document structure as the template for screening newer post-2015 closures.

## Stage-1 consequence

This pass improves the source-class assessment but does not produce an eligible calibration record.

```text
new_contract_complete_records = 0
new_direct_calibration_candidates = 0
new_method_research_only_sources = 1
new_high_priority_candidate_under_review = 1
blocker_2_reopened = false
```

## Waiting for

A public post-2015 facility package containing all of the following:

```text
certified_top_of_waste_or_subgrade_survey
+ certified_final_surface_or_layer_survey
+ explicit_numerical_survey_accuracy_or_tolerance
+ observation_date_settlement_or_later_topography
+ clean_sentinel_1_pre_and_post_acquisitions
+ defensible_whole_site_or_isolated_section_support
```

## Next step

1. Continue recovery of Sudbury's 2017 final CQA/as-built material and 2022 periodic-review surface evidence.
2. Search newer state and CCR facility records for the same certified survey structure demonstrated by Brookfield.
3. Prioritize closure events completed from 2015 onward.
4. Reject any candidate whose only evidence is a design thickness, whose uncertainty is inferred from printed decimal precision, or whose closure predates Sentinel-1 operational coverage.
5. Keep all surviving candidates at `candidate_under_review` until the required document fields are verified.

## Source references

- Washington Ecology Sudbury site record: `https://apps.ecology.wa.gov/cleanupsearch/site/2485`
- Washington Ecology Sudbury CQA manual: `https://apps.ecology.wa.gov/cleanupsearch/document/53362`
- NYSDEC Brookfield public file listing: `https://extapps.dec.ny.gov/data/DecDocs/243006/`
- NYSDEC Brookfield Final Engineering Report: `https://extapps.dec.ny.gov/data/DecDocs/243006/Report.HW.243006.2014-10-01.FinalFER.Brookfield.volume1.october2014.pdf`
- Copernicus Sentinel-1A operational availability notice: `https://sentinels.copernicus.eu/-/first-copernicus-satellite-now-operational`
