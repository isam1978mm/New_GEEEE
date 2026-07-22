# Blocker 2 — Stage-1 Maxey Flats Strong Candidate — 2026-07-21

Status: Stage 1 active. Maxey Flats Disposal Site (MFDS), Fleming County, Kentucky, is promoted to `strong_candidate_under_review`. This is the first screened site with a public numerical repeat-elevation table tied to a Sentinel-1-era final cap. Blocker 2 remains unresolved. No calibration-pack intake, training, or app-depth enablement is authorized yet.

## Why this candidate is materially stronger

- Kentucky's official site record describes a controlled area with an approximately 55-acre vegetative cap over a former low-level radioactive-waste disposal facility.
- Waste was disposed from 1963 through 1977 and remained in place during final closure.
- Final Closure Period construction began after stabilization, reached substantial completion in December 2016, and reached final construction completion in September 2017.
- The 2019 annual report states that EPA approved the Final Closure Period Remedial Action Construction Report, dated April 2018.
- Public cap-design documentation identifies a multilayer final cover including a 60-mil HDPE geomembrane, geosynthetic clay liner, drainage geocomposite, geogrid reinforcement, approximately 1.3 feet of protective soil, and approximately 0.7 feet of vegetative soil.
- The 2020 annual report publishes an elevation table for 34 cap-subsidence monitoring points, with a 2018 baseline and repeat 2019 and 2020 elevations.
- The same report states that a licensed surveyor performed the 2020 survey and describes the positioning equipment as differential-grade GPS with an accuracy class of no better than approximately one metre.

This combination — a completed modern cap, an approved construction report, explicit cap layers, and a public matched repeat-elevation table — makes Maxey Flats a genuinely useful lead rather than a design-only or inspection-only candidate.

## Verified public facts

- The controlled area includes an approximately 55-acre vegetative cap.
- Final Closure Period construction was completed in September 2017 after substantial completion in December 2016.
- EPA approved the April 2018 Final Closure Period Remedial Action Construction Report.
- The final cap includes geogrid reinforcement, a geosynthetic clay layer, a 60-mil HDPE geomembrane, drainage geocomposite, protective soil, and vegetative soil.
- Design documentation indicates that leveling fill or subgrade thickness varies spatially, approximately 2 to 15 feet in places. Therefore, cap-to-waste depth cannot be represented by one uniform thickness.
- Subsidence monitoring uses 34 monitoring points on the final cap.
- The public 2020 report includes 2018 baseline elevations and repeat 2019 and 2020 elevations for those points.
- Most reported changes are sub-foot and the 2020 report itself notes that the common approximately -0.05-foot shift is within the margin of error of the differential-grade GPS equipment.
- Two 2019 point values were flagged by the report as inconsistent, so they must not be treated as verified deformation without source QA.
- A localized depression was repaired in 2020. That repair footprint must be excluded from any clean radar-to-survey comparison.
- Closure construction also included drainage, roads, basins, wells, sumps, and perimeter work. Only an interior cap polygon isolated from those features should be considered.
- The accessible public reports reference the approved construction report and survey appendices, but the native as-built surface, point coordinates, datum, and detailed survey-control metadata have not yet been retrieved.
- Attempts to render the relevant public PDF pages as screenshots through the available crawler returned cache errors. No unrendered figure or drawing was interpreted visually; this assessment is based on parsed official text and tables.

## Classification

```text
candidate_id = MAXEY-FLATS-FINAL-CAP-2017
candidate_state = strong_candidate_under_review
measurement_pair_found = pass_public_34_point_2018_2019_2020_table
sentinel_1_era_cap_event = pass
controlled_cap_area = approximately_55_acres
waste_left_in_place = pass
substantial_completion = december_2016
final_construction_completion = september_2017
epa_approved_construction_report = april_2018
final_cap_layers = pass_60mil_hdpe_gcl_geocomposite_geogrid_2ft_soil
leveling_fill = variable_approximately_2_to_15_ft
pre_cap_or_subgrade_surface = referenced_but_native_surface_not_retrieved
final_as_built_surface = referenced_in_epa_approved_report_but_not_retrieved
repeat_settlement_points = pass_34_points
repeat_epochs = 2018_2019_2020
native_point_coordinates = unresolved
horizontal_datum = unresolved
vertical_datum = unresolved
stated_positioning_class = differential_grade_gps_le_1m
explicit_horizontal_accuracy = unresolved_beyond_equipment_class
explicit_vertical_accuracy = unresolved_beyond_equipment_class
subfoot_settlement_truth = fail_pending_better_accuracy_metadata
local_2020_repair = mask_required
perimeter_infrastructure = exclude
clean_interior_polygon = promising_pending_native_drawings
special_waste_site_transferability = must_be_tested
R1_depth_measurability = promising_not_yet_authorized
R5_radar_linkage = not_tested
depth_estimation_enabled = false
```

## Decision

Promote Maxey Flats to `strong_candidate_under_review`.

It clears the practical "something good" threshold because it is a Sentinel-1-era completed cap with waste left in place, explicit cover construction, an EPA-approved construction report, and a public numerical repeat-elevation table for 34 monitoring points.

Do not promote it to a calibration-ready reference yet. The public table alone is insufficient because the monitoring-point coordinates, native as-built and subgrade surfaces, common datum, and survey accuracy are unresolved. The reported sub-foot changes also appear smaller than the stated differential-GPS equipment class, so they cannot yet be treated as precise ground truth.

Blocker 2 therefore remains open, but Maxey Flats is now the highest-priority evidence-retrieval target.

## Waiting for

```text
april_2018_final_closure_period_remedial_action_construction_report
+ certified_final_as_built_contours_or_native_surface
+ pre_cap_interim_cap_or_subgrade_surface
+ coordinates_for_all_34_monitoring_points
+ 2018_2019_2020_native_survey_files
+ horizontal_and_vertical_datum
+ explicit_horizontal_and_vertical_accuracy
+ survey_control_and_benchmark_metadata
+ clean_interior_cap_polygon
+ masks_for_2020_repair_and_all_drainage_road_well_sump_features
```

## Next step

Retrieve the EPA-approved April 2018 construction report and the native Appendix D survey deliverables. Extract the 34 point coordinates, baseline/as-built relationship, horizontal and vertical datum, survey control, and accuracy. Build an interior cap mask that excludes perimeter infrastructure and the repaired depression. Only then test whether Sentinel-1 coherence or deformation features correspond to independently measured elevation change.

## Public references

- Kentucky Energy and Environment Cabinet, Maxey Flats Disposal Site: `https://eec.ky.gov/Environmental-Protection/Waste/superfund/Pages/Maxey-Flats.aspx`
- Kentucky archived Maxey Flats documentation index: `https://eec.ky.gov/Environmental-Protection/Waste/superfund/Pages/Maxey-Flats-Archived-Documents.aspx`
- Maxey Flats 2016 Annual Report, official archive.
- Maxey Flats 2017 Annual Report, official archive.
- Maxey Flats 2019 Annual Report, official archive.
- Maxey Flats 2020 Annual Report, official archive; includes the 34-point 2018–2020 elevation table.
- AECOM final-cap layer detail, official Kentucky archive.
- EPA Maxey Flats Disposal Site profile: `https://cumulis.epa.gov/supercpad/cursites/csitinfo.cfm?id=0402081`
