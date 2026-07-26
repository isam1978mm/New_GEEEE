# Auburn McMaster Street Former MGP — Surveyed Cover Candidate

Date: 2026-07-25

## Decision

**Status:** high-priority positive-depth candidate, not yet a usable calibration row.

Auburn McMaster is the strongest known-cover candidate found in the current search. The official Construction Completion Report confirms that licensed land surveyors performed the construction surveys, that the Appendix A as-built drawings show the actual soil-cover thickness, and that approved reuse material was placed more than two feet below final grade beneath a geotextile demarcation layer. A separate recorded environmental-easement drawing provides a legal metes-and-bounds description for the controlled parcel. The site remained vacant and its engineering controls were certified intact through May 2025.

This still cannot enter the calibration pack. The documented greater-than-two-foot condition is only a lower bound, not a point depth or bounded interval accepted by the current dataset contract. The exact local thickness labels, target-subarea geometry, datum, and numerical survey uncertainty remain unreadable in the large Appendix A and design-report files.

## What is confirmed

- Site: McMaster Street Former Manufactured Gas Plant, Auburn, New York; NYSDEC Site 7-06-010.
- Remediation was completed in four phases from September 2015 through December 2018.
- Approximately 18,000 tons of MGP-impacted soil were removed.
- Upland excavations in Phases 1 and 3 reached bedrock in major areas.
- Limited NYSDEC-approved MGP-impacted reuse material remained as backfill in mapped upland areas.
- The official report states that soils accepted for reuse as general fill were placed at depths greater than two feet below final grade, with significant reuse material placed during Phase 3.
- A geotextile demarcation layer was placed over the reuse material before clean backfill was installed.
- The site-wide cover system is a minimum of 12 inches (0.3048 m) of clean soil.
- The ecological buffer has a separate two-foot (0.6096 m) clean-soil requirement, but this vegetated zone must not be mixed with the simple gravel reference areas.
- The Construction Completion Report explicitly states that Appendix A shows the actual soil-cover thickness.
- Upland excavation and backfill areas were surfaced with Type F run-of-crusher stone.
- Thew Associates conducted the site surveys and is identified as the licensed land surveyor.
- Excavation boundaries were surveyed against the design drawings.
- Appendix A contains the survey map, tax maps, excavation and restoration as-builts, and soil-cover thickness information.
- The controlled parcel has a recorded legal metes-and-bounds description in a small public environmental-easement drawing. The drawing describes approximately 1.2 acres, but this whole-parcel boundary is not a substitute for the exact reuse-material subareas.
- The 2024–2025 Periodic Review Report describes the property as a vacant compacted-gravel lot and certifies that it was not undergoing development.
- The cover system remained intact, with no observed erosion or bare spots and no cover maintenance required during the May 30, 2024 to May 30, 2025 reporting period.
- The official archive contains the 98 MB 2014 Remedial Design Report, including the Construction Quality Assurance Plan where required survey accuracy may be stated.

## Why it is not yet usable

1. Appendix A is contained in a 518 MB public file that could not be rendered or downloaded in the current environment.
2. The actual as-built cover-thickness labels and their mapped boundaries have not been extracted.
3. The exact reuse-material subarea polygons, coordinate reference system, datum, final surface elevations, demarcation-layer elevations, and survey tolerance/uncertainty have not been extracted.
4. The documented greater-than-two-foot placement condition is a one-sided lower bound. It is not a point depth and it is not a finite bounded interval under the current calibration contract.
5. The 12-inch and two-foot design values must not be substituted for the local as-built thickness labels.
6. The environmental-easement metes-and-bounds survey solves only the controlled-parcel boundary, not the target-specific geometry needed for calibration.
7. The buried reference material is heterogeneous MGP-impacted reuse soil rather than a discrete manufactured object; the calibration contract must explicitly allow this reference class before fitting.
8. Monitoring wells, NAPL recovery wells, utilities, the ecological buffer, streambank, invasive-species treatment areas, and other locally disturbed features must be excluded.
9. Mixed surface conditions must be isolated: compacted gravel upland areas cannot be averaged with seeded or vegetated areas.
10. A stable Sentinel-1 interval must be verified for each exact gravel-covered subarea after final restoration.

## Candidate classification

```text
candidate_status = surveyed_known_cover_candidate_pending_as_built_extraction
reference_role = potential_positive_depth_reference
controlled_parcel_geometry_available = yes_legal_metes_and_bounds
exact_target_subarea_geometry_available = pending_appendix_extraction
physical_condition_confirmed = yes
construction_dates_confirmed = yes
sitewide_cover_minimum_m = 0.3048
ecological_buffer_minimum_m = 0.6096
reuse_material_depth_lower_bound_m = greater_than_0.6096
actual_local_as_built_cover_depth = confirmed_to_exist_but_values_pending
licensed_surveyor_confirmed = yes
numerical_survey_uncertainty_documented = no
stable_post_remediation_surface_confirmed = provisionally_yes_for_selected_upland_subareas
eligible_calibration_row = no
```

## Required next steps

1. Recover Appendix A from `Report.HW.706010.2019-07-30.Construction Completion Report Appendices A thru G.pdf`.
2. Inspect the 2014 Remedial Design Report and its Construction Quality Assurance Plan for required horizontal and vertical survey accuracy.
3. Extract only simple upland gravel subareas containing mapped reuse material below demarcation fabric.
4. Match the target subareas to the recorded controlled-parcel survey without copying exact geometry into Git.
5. Record privately for every candidate subarea:
   - exact polygon vertices;
   - coordinate reference system and datum;
   - final surface elevations;
   - demarcation-layer elevations;
   - actual as-built cover thickness;
   - stated survey tolerance or defensible numerical uncertainty from the project survey specification.
6. Exclude wells, recovery systems, utilities, streambank restoration, ecological buffer, vegetation-management zones, and areas without remaining reuse material.
7. Verify an unchanged Sentinel-1 interval beginning after December 2018.
8. Run the depth-calibration validator only after all evidence fields are populated.

## Current readiness impact

- Usable calibration rows added: **0**
- Numerical depth estimation ready: **No**
- Strongest positive-depth lead: **Auburn McMaster surveyed cover**
- Strongest surveyed-excavation lead: **Sconondoa Street former MGP**

## Public sources

- NYSDEC file archive for Site 7-06-010
- 2019 Phase I–IV Construction Completion Report main text
- 2019 Construction Completion Report Appendices A through G
- 2014 Remedial Design Report and Construction Quality Assurance Plan
- 2016 environmental-easement survey drawing
- 2021 Site Management Plan
- 2024–2025 Periodic Review Report
- 2021 through 2024 monitoring and recovery-well annual reports
