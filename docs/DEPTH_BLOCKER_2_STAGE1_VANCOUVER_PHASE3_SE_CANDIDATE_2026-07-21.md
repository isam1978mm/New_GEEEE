# Blocker 2 — Stage-1 Vancouver Landfill Phase 3 Southeast Candidate — 2026-07-21

Status: Stage 1 active. Vancouver Landfill Phase 3 Southeast, Delta, British Columbia, is retained as `candidate_under_review`. Blocker 2 remains unresolved. No calibration-pack intake, training, or app-depth enablement is authorized.

## Verified official public facts

- The City of Vancouver's 2017 tender and contract-award records identify a dedicated Phase 3 Southeast closure and landfill-gas project.
- The contract was awarded in April 2017 with an expected six-month term.
- The City's 2017 annual report states that Phase 3 Southeast had entered progressive closure during 2017.
- The City's 2020 annual report records Phase 3 Southeast closure construction during 2017–2018 over 9.7 hectares, with 11 vertical landfill-gas wells installed.
- The same report states that completed phases receive an engineered impermeable geomembrane cover. Closure materials include contouring soil, geomembrane, aggregate above and below the liner, and topsoil.
- The City reports that aerial mapping and analysis have been performed annually since 2000. Annual flights generate contour data, and previous/current contours are used to assess landfill settlement and other operational measures.
- The public annual report therefore verifies a Sentinel-1-era closure footprint and later repeat contour acquisition.

## Evidence and access limitations

- No certified Phase 3 Southeast final CQA report, closure certification, as-built contour file, survey point file, or native CAD/GIS surface was located in the public index.
- The annual reports describe site-wide aerial mapping but do not publish the Phase 3 Southeast elevation-difference surface, datum, horizontal/vertical accuracy, or point density.
- The project combined cover construction with 11 gas wells. A clean interior test polygon must exclude wells, piping, drainage structures, roads, and any later repair work.
- Waste was left within an active, progressively closing landfill. The exact pre-cap/top-of-waste surface and evidence that no substantial waste relocation occurred within the Phase 3 Southeast polygon remain unverified.
- One PDF screenshot request failed with a cache miss. A separate screenshot successfully confirmed the annual aerial-mapping description, but no unavailable drawing or figure was interpreted.

## Classification

```text
candidate_id = VANCOUVER-PHASE3-SE-2017-2018
candidate_state = candidate_under_review
sentinel_1_era_cap_event = pass
closure_completed = pass_2017_to_2018
closure_area = 9_7_hectares
single_defined_phase = pass
waste_left_in_place = promising_but_unverified
final_cover_type = engineered_geomembrane_system
verified_phase_specific_cover_thickness = unresolved
pre_cap_or_top_of_waste_surface = unresolved
certified_final_as_built_surface = unresolved
later_repeat_topography = pass_sitewide_annual_mapping_record
phase_specific_repeat_surface = unresolved
survey_datum = unresolved
survey_accuracy = unresolved
native_contour_or_point_data = unresolved
mixed_gas_infrastructure = present_11_vertical_wells
clean_interior_polygon = possible_but_unverified
R1_depth_measurability = not_tested_pending_evidence
R5_radar_linkage = not_tested_pending_evidence
```

## Decision

Retain Vancouver Phase 3 Southeast. It is one of the stronger public leads because it combines a defined 9.7-hectare closure completed in 2017–2018 with a documented program of annual aerial contour mapping used to assess settlement.

Do not promote it yet. The calibration contract still requires the pre-cap/top-of-waste surface, certified final as-built surface, verified cover thickness, common datum, numerical survey accuracy, native later contour data, and a disturbance mask excluding gas wells and other infrastructure.

## Waiting for

```text
phase3_se_final_cqa_or_closure_report
+ pre_cap_or_top_of_waste_surface
+ certified_2017_2018_as_built_contours_or_points
+ phase_specific_cover_layer_thickness
+ annual_aerial_mapping_surfaces_after_2018
+ common_horizontal_and_vertical_datum
+ explicit_horizontal_and_vertical_accuracy
+ elevation_difference_or_settlement_map
+ phase3_se_polygon
+ gas_well_pipe_drainage_and_road_exclusion_mask
+ confirmation_no_major_waste_relocation
```

## Next step

Request the Phase 3 Southeast final CQA/as-built package and the City's annual aerial-mapping deliverables for 2018 and a later year. Test whether the same survey control was used and whether an undisturbed interior polygon provides a direct constructed-surface-to-later-surface elevation pair.

## Public references

- City tender page: `https://bids.vancouver.ca/bidopp/ITT/ITT-PS20161666.htm`
- City contract-award report: `https://council.vancouver.ca/20170412/documents/cfsc2.pdf`
- 2017 Vancouver Landfill annual report: `https://vancouver.ca/files/cov/vancouver-%20landfill-annual-report-final-2017.pdf`
- 2020 Vancouver Landfill annual report: `https://vancouver.ca/files/cov/2020-vancouver-landfill-annual-report.pdf`
- City annual-report index: `https://vancouver.ca/home-property-development/annual-reports-for-landfill-and-solid-waste-divisions.aspx`
