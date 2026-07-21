# Blocker 2 — Stage-1 Indian River County Landfill Screen — 2026-07-21

Status: The historical Segment 2 partial closure is rejected for Sentinel-1-era direct calibration. The proposed Segment 3 Cell 1/2 closure is retained only as a future-watch item because design was approved in December 2025 but closure construction and final as-built surveys are not yet complete. Blocker 2 remains unresolved. No calibration-pack intake, training, or app-depth enablement is authorized.

## Verified public facts

- Indian River County's 2014 Solid Waste Management Plan states that partial closure of the side slopes of the Infill Area and Segment 2 was completed in October 2009.
- October 2009 predates the Sentinel-1 operational archive used by this project, so that closure event cannot provide the required before/during/after Sentinel-1 calibration sequence.
- A 2022 county work order describes Segment 1/Infill/Segment 2 as the closed vertical expansion and Segment 3 as the active lateral expansion.
- The same 2022 work order confirms that historical and recent aerial surveys, DWG files, GPS observations, waste-grade drawings, and cross-year volumetric comparisons exist for the operating landfill.
- The existence of recurring topographic surveys is useful evidence that the county maintains a survey trail, but it does not fix the 2009 timing problem for Segment 2.
- On December 9, 2025, the county approved engineering design services for partial closure of the north face and temporary closure of the south face of Segment 3 Cells 1 and 2.
- The 2025 board record lists bidding and construction services as potential future actions. Therefore the newer Segment 3 closure was not a completed, certified closure at the time of that approval.
- The county capital-improvement schedule allocates closure funding to Segment 3 Cells 1 and 2 in FY2025/26, further supporting that this is a current/future project rather than an already completed calibration reference.

## Classification

```text
candidate_id = N1-IR-01
site = Indian_River_County_Landfill
historical_unit = Segment_2_partial_closure
historical_closure_date = 2009-10
historical_unit_state = rejected_pre_sentinel_1
historical_final_as_built_survey = likely_exists_but_not_needed_for_current_calibration
historical_repeat_topography = pass_at_facility_practice_level

future_unit = Segment_3_Cell_1_and_Cell_2_partial_closure
future_unit_state = future_watch_not_completed
future_design_authorized = pass_2025-12-09
future_construction_complete = fail_not_yet_verified
future_final_as_built_contours = not_yet_available
future_later_repeat_survey = not_yet_possible
waste_left_in_place = promising_but_final_design_unverified
clean_s1_experiment_unit = unresolved_until_final_scope_and_construction
R1_depth_measurability = not_tested
R5_radar_linkage = not_tested
```

## Decision

Reject the old Segment 2 partial closure as a direct calibration candidate because its documented completion date is October 2009, outside the Sentinel-1 era.

Do not promote the newer Segment 3 Cell 1/2 project. It may become a strong candidate after construction because the county already uses aerial/topographic surveys and native CAD records, but the currently public record shows design and future construction planning rather than a completed closure with final as-built contours.

The earlier research summary that presented Indian River as a current completed candidate mixed together two different timelines:

1. the old Segment 2 partial closure, completed in 2009; and
2. the new Segment 3 Cell 1/2 closure project, approved for design in 2025.

Those timelines must not be combined into one calibration case.

## Future promotion requirements

Revisit Segment 3 Cells 1 and 2 only after all of the following exist:

```text
construction_completion_certification
+ final_CQA_report
+ surveyed_top_of_waste_or_pre_cap_surface
+ surveyed_final_cap_surface
+ horizontal_and_vertical_datum
+ explicit_survey_accuracy
+ verified_final_cover_thickness
+ later_repeat_topographic_survey_from_comparable_control
+ confirmation_no_major_waste_relocation_or_confounding_regrading
```

## Next step

Move to Neal Road Landfill, California. It is the remaining lead with an explicit legal requirement for an initial final-cover survey and later five-year iso-settlement maps. Search for the actual completed module closure packet and submitted settlement maps rather than relying only on the regulatory requirement.

## Public references

- Indian River County Solid Waste Management Plan, 2014 Update and CIP: `https://indianriver.gov/Document%20Center/Services/Solid%20Waste%20Disposal%20District/2014-Update-CIP.pdf?t=202308311426090`
- Indian River County 2022 Work Order 17, Segment 3 Cell 1 Top of Waste Grades Evaluation: `https://ircdocs.indian-river.org/WebLink/DocView.aspx?dbid=0&id=252152&repo=CBCC`
- Indian River County 2025 Segment 3 Cell 1/2 partial-closure design agenda item: `https://ircgov.legistar.com/LegislationDetail.aspx?FullText=1&GUID=E40035BA-724B-40F5-93BE-A978A751BCB5&ID=7770141`
- Indian River County capital-improvement schedule: `https://www.indianriver.gov/APPENDIX%20A.pdf`
- Indian River County landfill topographic-survey practice described by MMT Surveying: `https://www.mmtsurveying.com/projects/indian-river-county/`
- Florida DEP Indian River County Landfill document catalog, facility ID 19134: `https://prodenv.dep.state.fl.us/DepNexus/public/electronic-documents/19134/gis-facility!search`
