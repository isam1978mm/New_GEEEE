# Blocker 2 — Stage-1 Vancouver Landfill Phase 4 South Candidate — 2026-07-21

Status: Stage 1 active. Vancouver Landfill Phase 4 South, Delta, British Columbia, is retained as `candidate_under_review`. Blocker 2 remains unresolved. No calibration-pack intake, training, or app-depth enablement is authorized.

## Verified public facts

- The City of Vancouver's official 2021 annual report states that Phase 4 South was closed with an engineered cover system during 2020 and lists approximately 10.8 hectares as the closed area.
- The same report lists substantial closure infrastructure in the Phase 4 South work: 19 vertical gas wells, 28 horizontal gas collectors, and a stormwater retention pond with approximately 100,000 cubic metres of capacity.
- The report also states that closure work continued into 2021, including 6.3 hectares of liner construction in Phase 4 South plus additional remaining Phase 4 South and pond areas.
- Phase 4 North remained active and partially open through 2021, with a further 4 hectares deferred to 2022. This means the broader Phase 4 project was progressive rather than one single site-wide closure event.
- The City's official tender page describes the project as `Phase 4 Closure and Gas System Upgrades`, confirming that cover construction was combined with major gas-system work.
- The official annual report states that aerial mapping and analysis has been completed annually since 2000, using consecutive contour surfaces to assess landfill settlement, compaction, airspace consumption, and related operational parameters.
- Public annual reports therefore confirm a Sentinel-1-era cap event and a continuing annual surface-survey program.
- The public reports do not expose the certified construction-completion surface, native annual contour files, survey-control data, explicit horizontal/vertical accuracy, phase-specific cover thickness, or a Phase 4 South elevation-difference map.
- Attempts to render the relevant annual-report pages through the available PDF screenshot tool failed with cache errors. No unrendered drawing, table, or figure was interpreted visually.

## Classification

```text
candidate_id = VANCOUVER-PH4S-2020
candidate_state = candidate_under_review
sentinel_1_era_cap_event = pass
reported_closed_area = approximately_10_8_hectares
closure_timeframe = 2020_with_follow_on_work_in_2021
closure_project_type = engineered_cover_plus_gas_and_stormwater_infrastructure
waste_left_in_place = promising_but_unverified
single_recent_closure_period = partial_pass_phase4s_only
broader_phase4_progressive_closure = confounder
final_as_built_surface = unresolved
native_repeat_topography = pass_program_exists_but_files_not_retrieved
repeat_surface_frequency = annual
survey_datum = unresolved
numerical_survey_accuracy = unresolved
verified_cover_thickness = unresolved
elevation_difference_or_settlement_map = unresolved
later_regrading_or_infrastructure_work = possible_confounder
clean_s1_experiment_unit = promising_only_if_interior_phase4s_polygon_can_be_isolated
R1_depth_measurability = not_tested_pending_evidence
R5_radar_linkage = not_tested_pending_evidence
```

## Decision

Retain Phase 4 South as a cautious candidate. It is stronger than a design-only lead because the City confirms a 2020 engineered-cover closure over approximately 10.8 hectares and an annual aerial contour program designed in part to measure settlement.

Do not promote it yet. The closure was embedded in a broader progressive Phase 4 project, continued into 2021, and included gas wells, horizontal collectors, and a large stormwater pond. A usable calibration unit would require a clean interior Phase 4 South polygon that excludes the pond, gas-system construction, temporary closure areas, Phase 4 North activity, roads, and any later repairs or regrading.

## Waiting for

```text
phase4_south_final_cqa_or_completion_report
+ certified_phase4_south_as_built_contours_or_native_surface
+ pre_cover_or_top_of_waste_surface
+ annual_post_closure_contour_surfaces_for_same_polygon
+ common_horizontal_and_vertical_datum
+ explicit_horizontal_and_vertical_accuracy
+ verified_final_cover_layer_thickness
+ phase4_south_polygon
+ exclusion_masks_for_gas_wells_collectors_pond_roads_and_phase4_n
+ confirmation_no_later_regrading_or_fill_in_test_polygon
+ phase_specific_elevation_difference_or_settlement_map
```

## Next step

Request the Phase 4 South CQA/as-built package and the native 2020, 2021, and later aerial contour surfaces. Test whether an interior cap-only polygon can be isolated from the stormwater pond, gas infrastructure, Phase 4 North work, and later maintenance. Continue screening another candidate with publicly downloadable matched surfaces.

## Public references

- City of Vancouver annual-report index: `https://vancouver.ca/home-property-development/annual-reports-for-landfill-and-solid-waste-divisions.aspx`
- 2021 Vancouver Landfill Annual Report: `https://vancouver.ca/files/cov/2021-vancouver-landfill-annual-report.pdf`
- Phase 4 closure and gas-system-upgrades tender: `https://bids.vancouver.ca/bidopp/ITT/ITT-PS20191496.htm`
