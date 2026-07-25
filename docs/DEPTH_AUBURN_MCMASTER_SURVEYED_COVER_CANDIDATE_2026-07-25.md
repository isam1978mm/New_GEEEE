# Auburn McMaster Street Former MGP — Surveyed Cover Candidate

Date: 2026-07-25

## Decision

**Status:** high-priority positive-depth candidate, not yet a usable calibration row.

Auburn McMaster is the strongest known-cover candidate found in the current search. The site is a vacant compacted-gravel lot, is not currently undergoing development, has a professionally surveyed as-built record, contains precisely mapped remaining material below a demarcation layer, and has an intact long-term cover system. It cannot enter the calibration pack until the as-built cover-thickness drawings and numerical survey uncertainty are extracted.

## What is confirmed

- Site: McMaster Street Former Manufactured Gas Plant, Auburn, New York; NYSDEC Site 7-06-010.
- Remediation was completed in four phases from September 2015 through December 2018.
- Approximately 18,000 tons of MGP-impacted soil were removed.
- Upland excavations in Phases 1 and 3 reached bedrock in major areas.
- Limited NYSDEC-approved MGP-impacted reuse material remained as backfill in mapped upland areas.
- A geotextile demarcation layer was placed above remaining reuse material.
- The cover system is a minimum of 12 inches of clean backfill; the Construction Completion Report states that the as-built drawings show the actual soil-cover thickness.
- Upland areas were restored with Type F run-of-crusher stone at the surface.
- Thew Associates, licensed land surveyors, performed the construction surveying.
- The report states that excavation boundaries were surveyed and that Appendix A contains excavation geometries, backfill geometries, demarcation areas, and soil-cover thickness.
- The 2024–2025 Periodic Review Report describes the property as a vacant compacted-gravel lot.
- The property was certified as not undergoing development.
- The cover system remained intact and unchanged, with no observed erosion or bare spots and no cover maintenance required during the May 30, 2024 to May 30, 2025 reporting period.

## Why it is not yet usable

1. Appendix A is contained in a 518 MB public file that could not be rendered or downloaded in the current environment.
2. The actual cover-thickness values for each mapped subarea have not been extracted.
3. The coordinate reference system, polygon vertices, survey elevations, and survey tolerance/uncertainty have not been extracted.
4. The public text gives a minimum design value of 12 inches, not a measured point value with uncertainty.
5. The buried reference material is heterogeneous MGP-impacted reuse soil rather than a discrete manufactured object; the calibration contract must explicitly allow this reference class.
6. Monitoring wells, NAPL recovery wells, utility features, the ecological buffer, streambank, and vegetation-treatment areas must be excluded.
7. A stable Sentinel-1 interval must be verified for each exact gravel-covered subarea after final restoration.

## Candidate classification

```text
reference_status = surveyed_known_cover_candidate_pending_as_built_extraction
reference_role = potential_positive_depth_reference
exact_geometry_available = pending_appendix_extraction
physical_condition_confirmed = yes
construction_dates_confirmed = yes
cover_design_minimum_m = 0.3048
actual_measured_cover_depth = pending
licensed_surveyor_confirmed = yes
numerical_survey_uncertainty_documented = no
stable_post_remediation_surface_confirmed = provisionally_yes
eligible_calibration_row = no
```

## Required next steps

1. Recover Appendix A from `Report.HW.706010.2019-07-30.Construction Completion Report Appendices A thru G.pdf`.
2. Extract only simple upland gravel subareas containing mapped reuse material below demarcation fabric.
3. Record for every candidate subarea:
   - exact polygon vertices;
   - coordinate reference system and datum;
   - final surface elevations;
   - demarcation-layer elevations;
   - measured cover thickness;
   - stated survey tolerance or defensible numerical uncertainty from the project survey specification.
4. Exclude wells, recovery systems, utilities, streambank restoration, ecological buffer, vegetation-management zones, and areas without remaining reuse material.
5. Verify an unchanged Sentinel-1 interval beginning after December 2018.
6. Run the depth-calibration validator only after all evidence fields are populated.

## Current readiness impact

- Usable calibration rows added: **0**
- Numerical depth estimation ready: **No**
- Best positive-depth lead: **Auburn McMaster surveyed cover**
- Best surveyed-excavation lead: **Sconondoa Street former MGP**

## Public sources

- NYSDEC file archive: `https://extapps.dec.ny.gov/data/DecDocs/706010/`
- 2019 Phase I–IV Construction Completion Report main text
- 2019 Construction Completion Report Appendices A through G
- 2024–2025 Periodic Review Report
- 2021 monitoring and recovery-well annual report
