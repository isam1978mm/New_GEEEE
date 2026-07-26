# Berks Landfill — Measured Cap-Point Candidate

Date: 2026-07-25

## Decision

**Status:** high-priority measured-point candidate, not yet a usable calibration row.

The Berks Landfill remedial investigation is stronger than a design-only cap record. EPA documents state that investigators directly determined cap thickness by hand excavation and power augering until refuse or refusal was encountered. Measurements were collected across both the eastern and western landfill caps, with additional geotechnical and density/moisture testing at expanded investigation points.

The candidate still cannot enter the calibration pack. The eastern cap was substantially repaired in 2000, inspection trails were added on the western landfill, the original measurement-point map and field table have not been recovered, and no numerical measurement uncertainty has been found. Old measured points therefore cannot be assumed to represent the later Sentinel-1 surface without matching each point to the repair and disturbance history.

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
- EPA revised the remedy in 2000.
- The eastern landfill was cleared, covered with soil, and seeded during the 2000 remedial work.
- Approximately 7,000 feet of inspection trails were constructed on the western landfill.
- Construction was completed in December 2000 and final closeout was recorded in 2008.
- Current institutional controls restrict development and the landfill areas remain primarily vegetated green space.
- EPA records a five-year review completed on July 2, 2025.

## Why it is not yet usable

1. The original field table with point-specific cap thicknesses has not been recovered.
2. The original measurement-point map and coordinate reference system have not been recovered.
3. The eastern cap was altered after the measurements by clearing, soil placement, grading, and seeding in 2000.
4. Western inspection trails and later maintenance may have disturbed some measured locations.
5. The exact limits of the 2000 eastern repair and western trail construction have not been matched to the old measurement points.
6. No point-specific numerical measurement uncertainty or finite bounded interval has been found.
7. Reported landfill-wide averages cannot be used as depth labels for individual Sentinel-1 pixels or features.
8. The auger-refusal endpoint may not always equal the top of refuse; the field method and logs must be reviewed point by point.
9. Settlement, erosion repairs, vegetation management, access routes, gas or monitoring infrastructure, and other disturbed zones must be excluded.
10. A stable Sentinel-1 interval must be proven separately for each surviving candidate point or polygon.

## Candidate classification

```text
candidate_status = measured_cap_points_pending_map_repair_overlay_and_uncertainty
reference_role = potential_positive_depth_reference
measurement_target = depth_to_refuse_or_auger_refusal
actual_depth_measurements_confirmed = yes
point_specific_values_available = pending_original_field_table
exact_point_geometry_available = pending_original_map
post_measurement_surface_change = yes_eastern_cap_and_selected_western_areas
numerical_measurement_uncertainty_documented = no
stable_post_remedy_surface = pending_point_level_review
eligible_calibration_row = no
```

## Required next steps

1. Recover the remedial-investigation cap-thickness field table and measurement logs.
2. Recover the measurement-location figure, including coordinate system and point identifiers.
3. Recover the 2000 remedial-design and as-built drawings showing:
   - eastern cap repair limits;
   - western inspection-trail alignments;
   - grading and soil-placement limits;
   - monitoring and gas-system features.
4. Recover the July 2025 five-year review and recent maintenance records.
5. Identify only measured western points, or any other points, proven to lie outside all later disturbance limits.
6. Establish point-specific depth uncertainty from the field method, logs, or a source-provided finite interval.
7. Verify an unchanged Sentinel-1 observation interval for each surviving point.
8. Add a private calibration record only after geometry, depth-to-top interpretation, uncertainty, and stability pass the validator.

## Current readiness impact

- Usable calibration rows added: **0**
- Numerical depth estimation ready: **No**
- Strongest measured-cover lead: **John Sevier Bottom Ash Pond**
- Strongest vacant gravel-cover lead: **Auburn McMaster**
- Strongest measured-point lead: **Berks Landfill**
- Strongest surveyed-excavation lead: **Sconondoa Street former MGP**

## Public evidence reviewed

- EPA Berks Landfill Record of Decision and remedial-investigation summary
- EPA cleanup and redevelopment summaries
- EPA remedial administrative-record collection index
- EPA five-year-review schedule and site profile
