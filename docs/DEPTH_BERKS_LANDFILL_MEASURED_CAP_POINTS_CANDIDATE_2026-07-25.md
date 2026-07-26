# Berks Landfill — Measured Cap-Point Candidate

Date: 2026-07-25

## Decision

**Status:** high-priority measured-point candidate, not yet a usable calibration row.

The Berks Landfill remedial investigation is stronger than a design-only cap record. EPA documents state that investigators directly determined cap thickness by hand excavation and power augering until refuse or refusal was encountered. Measurements were collected across both the eastern and western landfill caps, with additional geotechnical and density/moisture testing at expanded investigation points.

The selected remedy gives one potentially preservable subset: forested and maturing portions of the western landfill were deliberately left as-is regardless of cap thickness, while the eastern landfill and non-forested western areas received repair or construction work. Later five-year reviews continued to describe the western landfill as mostly forested and did not identify a protectiveness problem in that forested cap. This improves the stability case but does not make a row usable. The original point map and field table are still missing, the 7,000 feet of western inspection trails and later access-road/drainage repairs must be excluded, and no numerical measurement uncertainty has been recovered.

## What is confirmed

- Site: Berks Landfill Superfund Site, Spring Township, Berks County, Pennsylvania.
- The site contains separate eastern and western closed municipal landfills.
- The remedial investigation evaluated cap thickness by excavating or augering until refuse or refusal was encountered.
- Initial cap investigations included 17 locations on the eastern landfill and 6 locations on the western landfill.
- Nine additional borings were completed on the western landfill.
- An expanded investigation included 24 additional eastern locations and 6 additional western locations.
- At the expanded locations, power augering was used to estimate cap thickness and nuclear methods were used to evaluate density and moisture; geotechnical samples were also collected.
- EPA reported an average pre-remedy cap thickness of approximately 24.7 inches on the western landfill and 18.7 inches on the eastern landfill.
- Large eastern areas and five of seven sampled southern and central western areas reportedly had at least 24 inches of cover.
- More than half of the overall site reportedly had more than 12 inches of cover.
- The measurement target was physical depth to refuse or auger refusal, not a satellite-derived estimate.
- The selected remedy required the eastern landfill and non-forested western areas to meet the repaired-cover requirement.
- Forested and maturing western landfill areas were explicitly left as-is regardless of existing cap thickness so the woodland could remain and mature.
- EPA revised the remedy in 2000.
- The eastern landfill was cleared, covered with soil, graded, and seeded during the remedial work.
- Approximately 7,000 feet of inspection trails were constructed on the western landfill.
- Later remedy descriptions state that cover thickness was verified during construction.
- Construction was completed in December 2000 and final closeout was recorded in 2008.
- The 2015 five-year review described the western landfill as predominantly forested or maturing forest, except for an open meadow at the crown.
- The 2015 review reported periodic inspection of the western crown and did not identify a protectiveness issue in the forested cap.
- Repairs described for the 2010–2015 period focused on eastern seeps and cover, gas vents, access roads, and drainage features rather than a documented wholesale repair of the forested western cap.
- The 2020 five-year review again described the western landfill as mainly forested with an open-meadow crown and reported no protectiveness issue from routine inspections.
- Storm-related work in 2019–2020 affected the central drainageway and eastern and western access roads; these corridors must be excluded from any stable western-cap subset.
- Current institutional controls restrict development and the landfill areas remain primarily vegetated green space.
- EPA records a five-year review completed on July 2, 2025, but the full 2025 report has not yet been recovered.
- The public administrative-record index identifies three exact March 1995 Revised Draft Remedial Investigation volumes and their page ranges, plus later design and construction reports.
- The final closeout report identifies the September 1999 Final Remedial Action Design Report and 2001 Remedial Action Construction Report as the key as-built evidence chain.

## Why it is not yet usable

1. The original field table with point-specific cap thicknesses has not been recovered.
2. The original measurement-point map and coordinate reference system have not been recovered.
3. The ROD identifies the cap-thickness figure, but its visual page could not be rendered; unseen point geometry must not be used.
4. The eastern cap was altered after the measurements by clearing, soil placement, grading, and seeding in 2000.
5. Non-forested western areas, inspection trails, access roads, drainage corridors, monitoring features, and later repair zones may have disturbed measured locations.
6. The exact limits of the forested western subset and all later disturbance corridors have not been matched to the old measurement points.
7. No point-specific numerical measurement uncertainty or finite bounded interval has been found.
8. Reported landfill-wide averages cannot be used as depth labels for individual Sentinel-1 pixels or features.
9. The auger-refusal endpoint may not always equal the top of refuse; the field method and logs must be reviewed point by point.
10. Settlement, erosion repairs, vegetation management, access routes, gas or monitoring infrastructure, and other disturbed zones must be excluded.
11. A stable Sentinel-1 interval must be proven separately for each surviving forested western point or polygon.
12. The July 2025 five-year review must be checked for recent repairs or changes before a current stable interval is accepted.

## Candidate classification

```text
candidate_status = measured_cap_points_pending_map_repair_overlay_and_uncertainty
reference_role = potential_positive_depth_reference
measurement_target = depth_to_refuse_or_auger_refusal
actual_depth_measurements_confirmed = yes
point_specific_values_available = pending_original_field_table
exact_point_geometry_available = pending_original_map
post_measurement_surface_change = yes_eastern_and_nonforested_western_areas
forested_western_subset_preserved_by_remedy = yes_in_principle
construction_cover_verification_confirmed = yes_but_values_pending
numerical_measurement_uncertainty_documented = no
stable_post_remedy_surface = provisionally_supported_for_selected_forested_western_areas_pending_overlay
eligible_calibration_row = no
```

## Required next steps

1. Recover the March 1995 remedial-investigation cap-thickness field table and measurement logs from the indexed RI volumes.
2. Recover the measurement-location figure, including coordinate system and point identifiers.
3. Recover the February 19, 1997 Topographic Site Plan.
4. Recover the September 15, 1999 Final Remedial Action Design Report and design drawing package.
5. Recover the 2001 Remedial Action Construction Report and as-built drawings showing:
   - eastern cap repair limits;
   - non-forested western repair limits;
   - western inspection-trail alignments;
   - access-road and drainage corridors;
   - grading and soil-placement limits;
   - monitoring and gas-system features;
   - construction cover-verification results.
6. Recover the July 2025 five-year review and recent maintenance records.
7. Identify only measured forested-western points proven to lie outside all construction, trail, road, drainage, monitoring, and repair limits.
8. Establish point-specific depth uncertainty from the field method, logs, or a source-provided finite interval.
9. Verify an unchanged Sentinel-1 observation interval for each surviving point.
10. Add a private calibration record only after geometry, depth-to-top interpretation, uncertainty, and stability pass the validator.

## Current readiness impact

- Usable calibration rows added: **0**
- Numerical depth estimation ready: **No**
- Strongest measured-cover lead: **John Sevier Bottom Ash Pond**
- Strongest vacant gravel-cover lead: **Auburn McMaster**
- Strongest measured-point lead: **Berks Landfill forested western subset**
- Strongest surveyed-excavation lead: **Sconondoa Street former MGP**

## Public evidence reviewed

- EPA Berks Landfill Record of Decision and remedial-investigation summary
- EPA administrative-record index identifying the March 1995 RI volumes
- EPA final closeout report and its design/construction bibliography
- EPA first, third, and fourth five-year review reports
- EPA cleanup and redevelopment summaries
- EPA five-year-review schedule and site profile
