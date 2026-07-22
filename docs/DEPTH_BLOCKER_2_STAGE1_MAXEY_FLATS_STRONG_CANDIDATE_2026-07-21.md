# Blocker 2 — Stage-1 Maxey Flats Strong Candidate — 2026-07-21

Status: Stage 1 active. Maxey Flats Disposal Site (MFDS), Fleming County, Kentucky, remains `strong_candidate_under_review`. It is the strongest publicly documented repeat-elevation lead found so far, but it is not yet a direct cap-depth calibration reference. Blocker 2 remains unresolved. No calibration-pack intake, training, or app-depth enablement is authorized.

## Why this candidate is materially stronger

- Kentucky's official site record describes an approximately 55-acre vegetative final cap over a former low-level radioactive-waste disposal facility.
- Waste was disposed from 1963 through 1977 and remained in place during final closure.
- Final Closure Period construction reached substantial completion in December 2016 and final construction completion in September 2017.
- The 2019 annual report states that EPA approved the April 2018 Final Closure Period Remedial Action Construction Report.
- A separate public EPA approval letter dated 12 July 2018 confirms that EPA reviewed and approved that April 2018 construction report.
- Public cap-design documentation identifies a multilayer final cover including geogrid reinforcement, geosynthetic clay liner, 60-mil HDPE geomembrane, drainage geocomposite, protective soil, and vegetative soil.
- The 2020 annual report publishes a matched elevation table for 34 final-cap monitoring points, with a baseline column labelled 2018 and repeat 2019 and 2020 elevations.
- The same report states that annual monitoring is performed by verifying the elevations of those 34 points.

This is a real monitored, completed, Sentinel-1-era cap with a public numerical repeat-elevation table. It is materially better than a design-only, visual-inspection-only, or future-survey candidate.

## Newly verified survey facts

- The 34 monitoring points duplicate earlier areas of concern that had been prone to subsidence.
- The 2020 report states that Curd Survey collected baseline data for cap subsidence in 2017, while Table 4 labels the baseline elevation column as 2018. This date inconsistency must be resolved from the native survey deliverable.
- Curd Survey also collected drainage-system data in 2018.
- After the original surveyor died, D and L Land Surveying began collecting data in November 2019.
- The 2020 report states that the replacement surveyor's drainage-system data did not compare consistently with the earlier survey data. Although that statement is about drainage cross-sections, it raises a control-continuity concern for all later survey products.
- Table 4 contains the full 34-point elevation series for the baseline, 2019, and 2020.
- Two 2019 values are obvious isolated positive excursions: point 3 is `+0.94 ft` and point 27 is `+0.59 ft` relative to baseline. The remaining 2019 differences range from `-0.13 ft` to `+0.08 ft`.
- All 2020 baseline differences fall between `0.00 ft` and `-0.18 ft`, with a median of approximately `-0.075 ft`.
- The report notes a consistent approximately `-0.05 ft` shift across benchmarks and subsidence points in 2020.
- The report explicitly states that this shift is within the current margin of error for the differential-grade, `<= 1 meter` GPS equipment, using the report's wording.
- Therefore the public 2018-to-2020 point table is useful for locating monitored areas and checking gross stability, but it is not yet precise enough to serve as sub-foot calibration truth.
- The 2017 and 2018 annual reports state that older Interim Maintenance Period subsidence monitoring and surveying had been suspended during the transition to the new final-cap monitoring program.
- A localized depression on the final cap was filled and regraded in 2020; that repair footprint must be masked.

## Construction-report retrieval outcome

- The April 2018 Final Closure Period Remedial Action Construction Report itself was not found as a separately downloadable public file in the Kentucky archive or DOE public index.
- DOE's public archive exposes the July 2018 EPA approval letter, which confirms the report's title, date, review, and approval, but not its as-built drawings or native survey files.
- The Kentucky annual reports repeatedly state that underlying survey appendices and detailed deliverables are available through the MFDS office or on-site records.
- Public annual-report PDFs reference Appendix D survey packages, but those appendices are not exposed as separate downloadable files in the indexed archive.
- Attempts to render the relevant annual-report pages with the public PDF screenshot service returned cache-miss errors. No unrendered figure or drawing was interpreted visually; the assessment uses parsed official text and tables.

## Classification

```text
candidate_id = MAXEY-FLATS-FINAL-CAP-2017
candidate_state = strong_candidate_under_review
something_good_threshold = pass
sentinel_1_era_cap_event = pass
controlled_cap_area = approximately_55_acres
waste_left_in_place = pass
substantial_completion = december_2016
final_construction_completion = september_2017
epa_approved_construction_report = april_2018_report_approved_2018_07_12
final_cap_layers = pass_60mil_hdpe_gcl_geocomposite_geogrid_and_soil
leveling_fill = variable_approximately_2_to_15_ft
pre_cap_or_subgrade_surface = unresolved
certified_final_as_built_surface = referenced_but_not_publicly_retrieved
repeat_settlement_points = pass_34_points
published_repeat_epochs = baseline_labelled_2018_plus_2019_and_2020
narrative_baseline_date = says_2017_requires_reconciliation
native_point_coordinates = unresolved
horizontal_datum = unresolved
vertical_datum = unresolved
survey_control_and_benchmarks = unresolved
stated_positioning_class = differential_grade_gps_le_1m_as_reported
published_subfoot_changes = fail_as_precision_truth
surveyor_continuity = concern_after_2019_change
local_2020_repair = mask_required
perimeter_infrastructure = exclude
clean_interior_polygon = promising_pending_native_drawings
settlement_monitoring_reference = strong
cap_thickness_calibration_reference = not_ready
R1_depth_measurability = not_authorized
R5_radar_linkage = not_tested
depth_estimation_enabled = false
```

## Decision

Retain Maxey Flats as the highest-priority evidence-retrieval target.

It clears the practical "something good" threshold because it is a completed modern cap with waste left in place, explicit engineered cover construction, an EPA-approved construction report, and a public numerical repeat-elevation table for 34 monitoring points.

Do not treat it as calibration-ready. The public monitoring series begins after the cap event, the baseline year is internally inconsistent between narrative and table, the coordinates and datum are missing, survey control continuity is uncertain, and the reported sub-foot changes are smaller than the stated GPS equipment class.

Maxey Flats is currently best classified as a strong settlement-monitoring reference and a promising cap-event candidate, not yet a direct cap-thickness ground-truth pair.

## Waiting for

```text
april_2018_final_closure_period_remedial_action_construction_report
+ certified_final_as_built_contours_or_native_surface
+ pre_cap_interim_cap_or_final_subgrade_surface
+ coordinates_for_all_34_monitoring_points
+ native_2017_or_2018_baseline_survey
+ native_2019_and_2020_repeat_surveys
+ reconciliation_of_2017_vs_2018_baseline_date
+ horizontal_and_vertical_datum
+ explicit_horizontal_and_vertical_accuracy
+ survey_control_and_benchmark_metadata
+ confirmation_of_control_transfer_between_surveyors
+ clean_interior_cap_polygon
+ masks_for_2020_repair_and_all_drainage_road_well_sump_features
```

## Next step

Request the April 2018 construction report and Appendix D survey deliverables directly from the Maxey Flats Disposal Site office or Kentucky open-records system. The request should specifically ask for CAD/GIS or point-file versions of the pre-cap/subgrade surface, certified final as-built surface, the 34 monitoring-point coordinates and baseline elevations, survey control and benchmark sheets, datum, accuracy statement, and 2019-2020 repeat files.

After retrieval, build a clean interior cap mask and test whether the cap event and later deformation can be measured independently with Sentinel-1. Until those files are obtained, do not fit or validate a depth model from the public table alone.

## Public references

- Kentucky Maxey Flats site summary: `https://eec.ky.gov/Environmental-Protection/Waste/superfund/maxey-flats-project/Pages/MaxeyFlatsSection.aspx`
- Kentucky archived documentation index: `https://eec.ky.gov/Environmental-Protection/Waste/superfund/maxey-flats-project/Pages/maxey-flats-documentation.aspx`
- Maxey Flats 2017 Annual Report, official Kentucky archive.
- Maxey Flats 2018 Annual Report, official Kentucky archive.
- Maxey Flats 2019 Annual Report, official Kentucky archive.
- Maxey Flats 2020 Annual Report, official Kentucky archive; includes the 34-point elevation table.
- AECOM final-cap layer detail, official Kentucky archive.
- DOE public archive, EPA approval of the Kentucky remedial action report: `https://lmpublicsearch.lm.doe.gov/LMSites/USEPA%20approval%20of%20KY%20Remedial%20Action%20report_Redacted.pdf`
