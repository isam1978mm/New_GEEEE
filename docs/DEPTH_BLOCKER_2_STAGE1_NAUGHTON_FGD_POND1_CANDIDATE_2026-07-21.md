# Blocker 2 — Stage-1 Naughton FGD Pond 1 Candidate — 2026-07-21

Status: Stage 1 active. Naughton Power Plant FGD Pond 1, Wyoming, is retained as `candidate_under_review`. Blocker 2 remains unresolved. No calibration-pack intake, training, or app-depth enablement is authorized.

## Verified public facts

- PacifiCorp's official CCR compliance page lists the closure plan, notification of completion of closure, post-closure plan, 2019 annual engineering inspection, and annual-inspection discontinuation letter for Naughton FGD Pond 1.
- The closure-completion notification is dated 14 February 2020 and states that final-cover construction was completed in fall 2019.
- The closure work began in spring 2016, included general fill placed to promote drainage, dewatering through six wells, and installation of a geosynthetic-clay-liner soil cover.
- The engineer certified that closure was completed in accordance with the WDEQ-approved closure plan and permit.
- The notification states that as-built drawings of the final closure configuration were supplied with the closure package.
- The 2019 annual inspection identifies an approximately 40-acre impoundment and describes the completed cover as a 2-foot cover system over as much as 8 feet of general fill.
- The same inspection states that eight settlement plates and seven standpipes were installed for post-closure monitoring.
- The inspection was visual and document-based. It does not publish numerical settlement-plate readings, survey accuracy, a repeat topographic surface, or an elevation-difference map.
- The accessible closure notification did not expose the attached as-built drawings or native survey points through the public crawler.
- Screenshot attempts for the public PDFs returned cache errors. No unrendered drawing, figure, or table was interpreted visually.

## Classification

```text
candidate_id = NAUGHTON-FGD1-2019
candidate_state = candidate_under_review
sentinel_1_era_cap_event = pass
closure_completed = pass_fall_2019
closure_certification = pass_engineer_certified
approximate_area = 40_acres
waste_or_ccr_left_in_place = pass
closure_period = multi_season_2016_to_2019
final_cover_system = 2_ft_cover_plus_up_to_8_ft_general_fill
final_as_built_drawings = pass_referenced_but_not_retrieved
pre_cover_or_top_of_ccr_surface = unresolved
settlement_instrumentation = pass_8_settlement_plates
post_closure_settlement_readings = unresolved_not_publicly_located
repeat_topographic_surface = unresolved
survey_datum_and_accuracy = unresolved
clean_s1_experiment_unit = promising_but_unverified
R1_depth_measurability = not_tested_pending_evidence
R5_radar_linkage = not_tested_pending_evidence
```

## Decision

Retain Naughton FGD Pond 1. It is stronger than a design-only lead because the final cover was completed and engineer-certified, as-built drawings are explicitly referenced, the footprint is about 40 acres, and eight settlement plates were installed.

Do not promote it yet. The closure lasted from 2016 through 2019 and included dewatering plus substantial general-fill placement. The calibration contract still requires the pre-cover/top-of-CCR surface, the certified final as-built surface, explicit survey control and accuracy, and later numerical settlement or repeat topographic measurements from the same footprint.

## Waiting for

```text
closure_package_attachment_with_as_built_drawings
+ native_pre_cover_or_top_of_ccr_surface
+ certified_2019_final_surface_points_or_contours
+ horizontal_and_vertical_datum
+ explicit_horizontal_and_vertical_accuracy
+ settlement_plate_coordinates_and_baseline_elevations
+ later_settlement_plate_readings
+ repeat_topographic_surface_or_elevation_difference_map
+ confirmation_no_later_regrading_or_fill_over_the_test_polygon
```

## Next step

Retrieve the closure-package attachment and post-closure settlement-monitoring records. Determine whether the eight settlement plates or a later survey provide a numerical 2019-to-later elevation pair tied to the same control and whether a clean interior polygon can exclude embankments, wells, and drainage work.

## Public references

- PacifiCorp Naughton CCR compliance index: `https://www.pacificorp.com/environment/environmental-applications-compliance/naughton.html`
- Notification of completion of closure: `https://www.pacificorp.com/content/dam/pcorp/documents/en/pacificorp/ccr/naughton/fgd-pond-1/closure/Naughton%20FGD%20Pond%201%20Notification%20of%20completion%20of%20closure.pdf`
- 2019 annual engineering inspection: `https://www.pacificorp.com/content/dam/pcorp/documents/en/pacificorp/ccr/naughton/fgd-pond-1/operating-criteria/engineering-inspections/2019%20Annual%20Inspection%20Naughton%20FGD%20Pond%201.pdf`
