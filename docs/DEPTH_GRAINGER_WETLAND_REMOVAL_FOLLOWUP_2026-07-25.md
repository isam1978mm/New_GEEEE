# Grainger Generating Station Removal Follow-up — 2026-07-25

**Branch:** `main`  
**Status:** confirmed removal evidence; not usable as a stable negative calibration record

## Plain-English result

Grainger Ash Ponds 1 and 2 were genuinely closed by removal under South Carolina regulatory oversight.

The public record establishes that:

- Ash Pond 1 completed closure by removal in 2019.
- Ash Pond 2 completed closure by removal in 2020.
- Ponded CCR was removed.
- At least one additional foot of subsurface soil was removed throughout each pond footprint.
- Remaining soil was sampled and tested for total metals.
- Results were submitted to the regulator for approval.
- Dikes were breached and the former pond footprints were restored as wetlands.
- Native wetland vegetation was planted.
- Wetland inspections continued through 2023 for Pond 1 and through 2024 for Pond 2.
- The property is being transferred for public and economic-development uses.

## Why this does not create a calibration row

The removal evidence is physically strong, but the post-removal surface is unsuitable as a clean Sentinel-1 negative control:

- the former pond footprints were deliberately converted into wetlands;
- inundation and wetland hydrology can change radar response;
- vegetation establishment continued after removal;
- inspections and restoration work continued for several years;
- future public redevelopment is planned;
- no final survey-grade excavation polygon or coordinate table was recovered from the public package.

The public applicability maps identify the general pond locations and approximate acreage, but they do not supply an extractable final surveyed removal boundary suitable for a private calibration geometry.

## Current classification

```text
physical_ccr_removal_confirmed = yes
extra_subsurface_soil_removed = yes
regulator_reviewed_residual_soil_testing = yes
post_removal_surface = restored_wetland
stable_dry_control_surface = no
exact_final_survey_boundary_recovered = no
clean_sentinel1_window_verified = no
eligible_negative_calibration_row = no
```

## Decision

Grainger is retained as strong closure-by-removal evidence only. It must not be used as a negative depth-calibration row.

## Next bounded action

Search only for a completed closure-by-removal site that provides all three of the following together:

1. a final survey-grade excavation boundary or coordinate table;
2. independent confirmation that the target material was removed;
3. a dry, unused, stable post-removal surface during a documented Sentinel-1 observation period.

Do not restart broad generic searching and do not create a placeholder calibration record.

## Official sources

- Santee Cooper Grainger CCR Data Rule page: https://www.santeecooper.com/about/ccr-data-rule/grainger/
- Grainger Ash Pond 1 Applicability Report: https://www.santeecooper.com/About/CCR-Data-Rule/Grainger/pdfs/All-Ponds/20241108-GGS-Ash-Pond-1-Applicability-Report.pdf
- Grainger Ash Pond 2 Applicability Report: https://www.santeecooper.com/About/CCR-Data-Rule/Grainger/pdfs/All-Ponds/20241108-GGS-Ash-Pond-2-Applicability-Report%281%29.pdf
- Santee Cooper Grainger transfer and redevelopment update: https://www.santeecooper.com/about/sustainability-report/2025/perception/grainger-transfer/
