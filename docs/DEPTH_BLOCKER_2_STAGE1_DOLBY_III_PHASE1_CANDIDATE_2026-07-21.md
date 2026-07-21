# Blocker 2 — Stage-1 Dolby III Phase 1 Candidate — 2026-07-21

Status: Stage 1 active. Dolby III Phase 1 final-cover upgrade, East Millinocket, Maine, is retained as `candidate_under_review`. Blocker 2 remains unresolved. No calibration-pack intake, training, or app-depth enablement is authorized.

## Verified public facts

- Maine's official state-owned-landfill page states that Phase 1 final cover at Dolby III covered approximately 25.2 acres and was completed in fall 2016.
- The same official record states that later closure phases were completed in 2022, 2023, and 2024. Phase 1 therefore has a potentially separable 2016-to-2021 observation window before the later phase construction began.
- The official 2017 annual report describes the 2016 upgraded cover as a 6-inch gas-transmission layer, 40-mil geomembrane, drainage geocomposite and drainage piping, 14 inches of cover soil, and 4 inches of vegetative soil.
- Official 2024 site plans identify a 15 October 2015 aerial-survey base map using Maine State Coordinate System East Zone, NAD 83.
- Those plans identify later aerial topography dated 4 May 2021 for landfill areas outside Phases 2 through 4. This should include the older Phase 1 footprint, but the exact polygon must still be verified from the native drawings.
- The same site plans state a vertical datum of `NAVD 1929` exactly as written in the public drawing notes; this datum wording requires verification because standard naming is normally NGVD 1929 or NAVD 88.
- The official 2025 Post-Closure Monitoring and Maintenance Plan states that topographic surveys of Dolby II and Dolby III are performed once every five years and that the most recent survey was completed in 2022.
- Public search-indexed records therefore establish a pre-construction 2015 surface, a 2016 cap event, later 2021 aerial topography, and a 2022 five-year topographic survey requirement/completion record.
- The certified 2016 as-built final-cover surface, native 2021/2022 survey points, explicit survey accuracy, and an elevation-difference or settlement map have not yet been retrieved.
- Attempts to render the large annual-report PDFs and drawing screenshots through the available public crawler failed despite the files being publicly listed. No unrendered figure or table was interpreted visually.

## Classification

```text
candidate_id = DOLBY-III-PHASE1-2016
candidate_state = candidate_under_review
sentinel_1_era_cap_event = pass
phase1_area = approximately_25_2_acres
closure_completed = pass_fall_2016
single_recent_closure_period = pass_for_phase1_subject_to_polygon_confirmation
waste_left_in_place = promising_but_unverified
verified_cover_layers = pass_public_2017_report
pre_construction_surface = pass_2015_10_15_aerial_survey
final_as_built_surface_2016 = unresolved
later_topographic_surface_2021 = pass_public_drawing_note
five_year_topographic_survey_2022 = pass_completion_record_only
native_repeat_survey_points = unresolved
horizontal_datum = NAD83_maine_state_coordinate_system_east_zone
vertical_datum = public_note_says_NAVD_1929_requires_verification
numerical_survey_accuracy = unresolved
elevation_difference_or_settlement_map = unresolved
later_phase_construction_confounding = avoidable_for_2016_to_2021_window_subject_to_polygon_check
clean_s1_experiment_unit = promising_but_unverified
R1_depth_measurability = not_tested_pending_evidence
R5_radar_linkage = not_tested_pending_evidence
```

## Decision

Retain Dolby III Phase 1. It is one of the strongest candidates found because it combines a Sentinel-1-era 25.2-acre cap event, a documented engineered cover thickness, a pre-construction aerial surface, later 2021 topography, and a recorded 2022 five-year topographic survey.

Do not promote it yet. The calibration contract still requires the certified 2016 constructed surface or as-built points, the native 2021 or 2022 repeat survey, explicit horizontal and vertical accuracy, a verified common datum, and proof that the Phase 1 polygon did not include major waste relocation or later construction disturbance.

## Waiting for

```text
2016_phase1_final_cqa_or_closure_certification
+ certified_2016_as_built_contours_or_survey_points
+ native_2015_pre_cap_surface
+ native_2021_aerial_topography
+ 2022_five_year_topographic_survey_deliverable
+ common_horizontal_and_vertical_datum_confirmation
+ explicit_horizontal_and_vertical_accuracy
+ elevation_difference_or_settlement_map
+ phase1_polygon_and_later_phase_exclusion_mask
+ confirmation_no_major_waste_relocation_within_phase1
```

## Next step

Retrieve the 2016 Phase 1 CQA/as-built package and the 2022 topographic-survey memo or native surface. Confirm the Phase 1 polygon, survey control, accuracy, dates, and whether the 2021 or 2022 surface can be differenced directly against the constructed 2016 baseline without contamination from the 2022-2024 closure phases.

## Public references

- Maine state-owned landfill summary: `https://www.maine.gov/dafs/bgs/maines-state-owned-landfills`
- Dolby Landfill official document index: `https://www.maine.gov/dafs/bgs/maines-state-owned-landfills/dolby-landfill`
- 2017 annual report: `https://www.maine.gov/decd/sites/maine.gov.decd/files/inline-files/2018%2817%29KPC_WQ-compressed.pdf`
- 2025 Post-Closure Monitoring and Maintenance Plan, Part 1: `https://www.maine.gov/dafs/bgs/sites/maine.gov.dafs.bgs/files/inline-files/Post-Closure%20Monitoring%20and%20Maintenance%20Plan%20%231_Part1.pdf`
- 2024 Dolby site plans: `https://www.maine.gov/dafs/bgs/sites/maine.gov.dafs.bgs/files/inline-files/3754%20Site%20Plans%20Dolby%20Landfill.pdf`
