# Depth Blocker 2 — Cobble Hill Holdings Landfill Screen — 2026-07-21

Status: `strong_closure_documentation_under_review`; not calibration-ready.

No email, form, operator contact, agency contact, or records request was sent.

## Confirmed official evidence

The British Columbia Ministry of Environment public archive confirms that the Cobble Hill Holdings contaminated-soil landfill at 460 Stebbings Road, Shawnigan Lake, was permanently closed rather than removed.

- The permit was cancelled in February 2017.
- Minor construction works were completed in fall 2017 while the full closure plan remained under review.
- The updated final closure plan was approved in June 2019.
- Final closure construction was completed in fall 2020.
- The Spill Prevention Order was amended in February 2021 to reflect post-closure status.
- The official archive publicly lists a September 2020 construction wrap-up report, a final closure construction quality-management plan, a detailed construction plan, 2017 as-built plans/specifications, and annual post-closure reports for 2021 and 2022.

This is materially stronger closure documentation than an inspection-only candidate.

## Critical limitations

### No matched repeat topographic survey retrieved

The public archive lists annual post-closure environmental monitoring reports, but the accessible official page and indexed snippets do not establish that those reports contain a repeat topographic surface, settlement-monument elevation table, iso-settlement map, or stated survey datum/accuracy.

The reports appear focused on environmental monitoring, drainage, cover condition, erosion and inspections. Visual or condition inspections do not satisfy the calibration requirement.

### Final construction report could not be rendered

The official 71 MB September 2020 construction wrap-up PDF and the 2021/2022 post-closure PDFs are linked directly by the Ministry. The current public PDF fetch path returned cache/HTTP errors, so no unrendered drawing, contour map, table or figure was interpreted. Their existence is verified; their unseen contents were not guessed.

### Closure was not perfectly one-event

Minor construction works occurred in 2017 before the 2019–2020 final closure project. The final 2020 construction event may still contain a clean polygon, but the 2017 work boundary must be separated from the 2020 final works.

## Classification

```text
candidate_id = COBBLE-HILL-HOLDINGS-2020
candidate_state = strong_closure_documentation_under_review
waste_left_in_place = pass
final_closure_completed = fall_2020
public_construction_wrap_up_report = pass_exists_not_rendered
public_CQA_plan = pass
public_as_built_documents = pass_exists
post_closure_reports_2021_2022 = pass_exist
matched_repeat_topographic_surface = fail_not_retrieved
settlement_monument_elevation_series = unresolved
horizontal_vertical_datum = unresolved
survey_accuracy = unresolved
one_event_final_cap = qualified_due_2017_minor_works
clean_test_polygon = unresolved
cap_depth_calibration_ready = false
external_contact_authorized = false
```

## Decision

Retain Cobble Hill Holdings as a strong closure-record retrieval target, but do not call it usable. The publicly listed construction/as-built package is promising; the required later matched survey has not been demonstrated.

## Waiting for

```text
September_2020_construction_wrap_up_report_contents
+ certified_final_as_built_surface_and_contours
+ pre_cap_or_final_subgrade_surface
+ cover_layer_thickness
+ common_horizontal_and_vertical_datum
+ construction_survey_accuracy
+ quantitative_2021_or_2022_repeat_topographic_surface
+ settlement_monument_coordinates_and_elevations_if_any
+ 2017_minor_works_boundary
+ clean_2020_final_closure_polygon
```

## Next step

Continue public-only screening for a post-2015 one-event cap with an openly retrievable as-built surface and a later matched survey. Revisit Cobble Hill if the large official PDFs become renderable or separately indexed attachments are found.

## Official reference

- British Columbia Ministry of Environment, South Island Aggregates: Cobble Hill Holdings Landfill in Shawnigan Lake: `https://www2.gov.bc.ca/gov/content/environment/air-land-water/site-permitting-compliance/sia`
