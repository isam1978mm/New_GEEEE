# Auburn McMaster Street Former MGP — Surveyed Cover Candidate

Date: 2026-07-25

## Decision

**Status:** high-priority positive-depth candidate, not yet a usable calibration row.

Auburn McMaster is the strongest known-cover candidate found in the current search. The official Construction Completion Report confirms that licensed land surveyors performed the construction surveys and that the Appendix A as-built drawings show the actual soil-cover thickness. The site remained vacant and its engineering controls were certified intact through May 2025. It cannot enter the calibration pack until the thickness labels, exact usable subarea geometry, coordinate system, and numerical survey uncertainty are extracted from the large drawing files and construction-quality specifications.

## What is confirmed

- Site: McMaster Street Former Manufactured Gas Plant, Auburn, New York; NYSDEC Site 7-06-010.
- Remediation was completed in four phases from September 2015 through December 2018.
- Approximately 18,000 tons of MGP-impacted soil were removed.
- Upland excavations in Phases 1 and 3 reached bedrock in major areas.
- Limited NYSDEC-approved MGP-impacted reuse material remained as backfill in mapped upland areas.
- A geotextile demarcation layer was placed above remaining reuse material.
- The site-wide cover system is a minimum of 12 inches (0.3048 m) of clean soil.
- The ecological buffer has a separate two-foot (0.6096 m) clean-soil requirement, but this vegetated zone must not be mixed with the simple gravel reference areas.
- The Construction Completion Report explicitly states that the Appendix A as-built drawings show the actual soil-cover thickness.
- Upland areas were surfaced with Type F run-of-crusher stone.
- Thew Associates conducted site surveys and is identified as the licensed land surveyor.
- Appendix A contains the survey map, metes-and-bounds description, construction survey drawings, and as-built drawings.
- The site boundary is fully described by the Appendix A survey map and metes and bounds.
- The 2024–2025 Periodic Review Report describes the property as a vacant compacted-gravel lot and certifies that it was not undergoing development.
- The cover system remained intact, with no observed erosion or bare spots and no cover maintenance required during the May 30, 2024 to May 30, 2025 reporting period.
- The official archive also contains the 98 MB 2014 Remedial Design Report, which includes the Construction Quality Assurance Plan where the required survey accuracy may be stated.

## Why it is not yet usable

1. Appendix A is contained in a 518 MB public file that could not be rendered or downloaded in the current environment.
2. The actual as-built cover-thickness labels and their mapped boundaries have not been extracted.
3. The coordinate reference system, polygon vertices, final surface elevations, demarcation-layer elevations, and survey tolerance/uncertainty have not been extracted.
4. The 12-inch and two-foot values are confirmed minimum requirements; they must not be substituted for the local as-built thickness labels.
5. The buried reference material is heterogeneous MGP-impacted reuse soil rather than a discrete manufactured object; the calibration contract must explicitly allow this reference class.
6. Monitoring wells, NAPL recovery wells, utilities, the ecological buffer, streambank, invasive-species treatment areas, and other locally disturbed features must be excluded.
7. The periodic-review description indicates mixed surface conditions: compacted gravel in the upland area and seeded/vegetated cover in other areas. Each surface class must be isolated rather than averaged together.
8. A stable Sentinel-1 interval must be verified for each exact gravel-covered subarea after final restoration.

## Candidate classification

```text
reference_status = surveyed_known_cover_candidate_pending_as_built_extraction
reference_role = potential_positive_depth_reference
exact_geometry_available = pending_appendix_extraction
physical_condition_confirmed = yes
construction_dates_confirmed = yes
sitewide_cover_minimum_m = 0.3048
ecological_buffer_minimum_m = 0.6096
actual_local_as_built_cover_depth = confirmed_to_exist_but_values_pending
licensed_surveyor_confirmed = yes
numerical_survey_uncertainty_documented = no
stable_post_remediation_surface_confirmed = provisionally_yes_for_selected_upland_subareas
eligible_calibration_row = no
```

## Required next steps

1. Recover Appendix A from `Report.HW.706010.2019-07-30.Construction Completion Report Appendices A thru G.pdf`.
2. Inspect the 2014 Remedial Design Report and its Construction Quality Assurance Plan for the required horizontal and vertical survey accuracy.
3. Extract only simple upland gravel subareas containing mapped reuse material below demarcation fabric.
4. Record for every candidate subarea:
   - exact polygon vertices;
   - coordinate reference system and datum;
   - final surface elevations;
   - demarcation-layer elevations;
   - actual as-built cover thickness;
   - stated survey tolerance or defensible numerical uncertainty from the project survey specification.
5. Exclude wells, recovery systems, utilities, streambank restoration, ecological buffer, vegetation-management zones, and areas without remaining reuse material.
6. Verify an unchanged Sentinel-1 interval beginning after December 2018.
7. Run the depth-calibration validator only after all evidence fields are populated.

## Current readiness impact

- Usable calibration rows added: **0**
- Numerical depth estimation ready: **No**
- Best positive-depth lead: **Auburn McMaster surveyed cover**
- Best surveyed-excavation lead: **Sconondoa Street former MGP**

## Public sources

- NYSDEC file archive for Site 7-06-010
- 2019 Phase I–IV Construction Completion Report main text
- 2019 Construction Completion Report Appendices A through G
- 2014 Remedial Design Report and Construction Quality Assurance Plan
- 2021 Site Management Plan
- 2024–2025 Periodic Review Report
- 2021 through 2024 monitoring and recovery-well annual reports
