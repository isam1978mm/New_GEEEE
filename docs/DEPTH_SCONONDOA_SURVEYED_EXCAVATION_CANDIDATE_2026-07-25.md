# Sconondoa Street Former MGP - Surveyed Excavation Candidate

Date: 2026-07-25

## Decision

**Status:** high-priority candidate, not yet a usable calibration row.

This is the strongest public candidate found in the current search because the record supports licensed construction surveying, known excavation depths, exact construction phases, post-construction surveys, and a largely vacant post-remediation property. It must not be entered into the calibration pack until the survey appendix is successfully extracted and the stable Sentinel-1 comparison window is verified.

## What is confirmed

- Site: former manufactured gas plant at 215 Sconondoa Street, Oneida, New York; NYSDEC Site No. 7-27-008.
- Remediation occurred in three phases between January 2008 and December 2012.
- The work excavated approximately 65,337 cubic yards of soil and debris.
- Reported excavation depths ranged from approximately 5 to 20 feet below grade.
- Thew Associates PE-LS, PLLC performed construction surveys.
- Horizontal and vertical survey control was established on:
  - a minimum 20-foot by 20-foot grid for Phase 1;
  - a minimum 15-foot by 15-foot grid for Phases 2 and 3.
- Survey control was maintained during excavation, backfilling, and restoration.
- Post-construction topographic surveys documented final as-built conditions.
- The official NYSDEC archive lists a 90 MB appendix containing property survey maps, as-built survey drawings, and project photographs.
- The 2023 periodic review report, covering conditions through January 2024, still described the 2.1-acre property as containing a vacant office/garage building, surrounded by fencing, with vacant City-owned land to the north and west.
- Some restored areas received topsoil and grass seed; other areas were gravel, asphalt, riprap, or engineered cover.

## Why it is not yet usable

1. The survey appendix is publicly listed but could not be rendered or downloaded in the current environment.
2. The coordinate system, survey notes, drawing scale, point coordinates, and stated numerical survey accuracy have not yet been extracted.
3. The surface is mixed: grass, gravel, asphalt, riprap, structures, utilities, and an active gas regulator station. Only a carefully isolated subcell could be considered.
4. Groundwater monitoring and periodic site review continue. A stable, unchanged Sentinel-1 interval must be demonstrated for the exact subcell.
5. The public record documents excavation depth and remaining impacts, but it does not by itself prove that Sentinel-1 backscatter can recover numerical buried depth.

## Candidate classification

```text
reference_status = surveyed_excavation_candidate_pending_appendix_extraction_and_stability_review
exact_geometry_available = pending
physical_condition_confirmed = yes
construction_dates_confirmed = yes
vertical_excavation_limits_documented = yes
survey_grid_documented = yes
numerical_survey_uncertainty_documented = no
stable_post_remediation_surface_confirmed = pending
eligible_calibration_row = no
```

## Required next steps

1. Recover `Report.HW.727008.2021-06-25.FER Appendices A through C-Survey Figures and Photos.pdf` from the NYSDEC archive.
2. Extract the licensed survey sheets and record:
   - coordinate reference system and datum;
   - exact excavation-cell polygon vertices;
   - final surface elevations;
   - bottom-of-excavation elevations or depth annotations;
   - surveyor certification and any stated accuracy/tolerance.
3. Select only grassed or otherwise simple cells, excluding buildings, asphalt, riprap, access roads, utilities, wells, and the gas regulator station.
4. Check Sentinel-1 and optical imagery from 2014 onward for an unchanged interval.
5. Create a calibration row only if the exact cell geometry, numerical uncertainty, and stable interval all pass the validator.

## Current readiness impact

- Usable calibration rows added: **0**
- Numerical depth estimation ready: **No**
- Best next lead: **Sconondoa survey appendix recovery**

## Public sources

- NYSDEC file archive: https://extapps.dec.ny.gov/data/DecDocs/727008/
- Final Engineering Report text and figures: https://extapps.dec.ny.gov/data/DecDocs/727008/Report.HW.727008.2021-06-25.Final%20Engineering%20Report%20Text%20and%20Figures.pdf
- Survey appendix listing: `Report.HW.727008.2021-06-25.FER Appendices A through C-Survey Figures and Photos.pdf`
- 2023 Periodic Review Report: https://extapps.dec.ny.gov/data/DecDocs/727008/Report.HW.727008.2024-04-03.2023%20Periodic%20Review%20Report.pdf
