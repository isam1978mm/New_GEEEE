# Walsh Landfill — ET Forest Cover, Design Minimums Only

Date: 2026-07-26

## Decision

**Status:** closed as unsuitable for numerical depth calibration.

Walsh Landfill has a completed full-scale evapotranspiration cover and no obvious commercial redevelopment. However, the public record provides minimum design thicknesses rather than point-specific measured depths. The cover is also a deliberately changing forest with mowing, replanting, monitoring equipment, vents, wells, access paths, and recurring O&M activity. It cannot provide a simple unchanged soil-surface reference for Sentinel-1.

## What is confirmed

- Site: Walsh Landfill, also known as Welsh Road/Barkman Landfill, Pennsylvania.
- EPA ID: `PAD980829527`.
- The site covers approximately seven acres.
- ET-cover construction started in 2005 and achieved construction-completion status on August 16, 2006.
- Approximately 40,000 cubic yards of topsoil and subsoil were imported as the rooting layer.
- The published cover requirements were:
  - minimum four feet on slopes less than or equal to 10 percent;
  - minimum three feet on slopes greater than 10 percent.
- Approximately 4,090 trees were planted in May 2006:
  - about 90 percent hybrid poplar;
  - about 10 percent native species.
- The cover contains stormwater controls, a monitoring system, landfill-gas monitoring infrastructure, groundwater wells, fencing, and maintained access paths.
- Early O&M included frequent inspections, mowing, localized tree replacement, and repair of a damaged data logger.
- The 2011 inspection reported no visible cap erosion and generally healthy trees, but also documented localized replanting and continued mowing until canopy closure.
- EPA reports that most planted trees later reached approximately 16 to 20 feet and that the site remains in O&M.
- EPA completed its sixth five-year review in April 2026 and concluded that the remedy remained protective.

## Why it is not usable

1. The three-foot and four-foot values are minimum design requirements, not extracted point-specific as-built measurements.
2. No public table of local accepted cover thicknesses was recovered.
3. No numerical construction tolerance, measurement precision, survey uncertainty, or finite two-sided depth interval was recovered.
4. The cover intentionally changes as thousands of trees grow and canopy closure develops.
5. Mowing, tree replacement, monitoring equipment, landfill-gas vents, wells, access paths, drainage features, and routine O&M create spatial and temporal radar confounders.
6. The cover-depth value cannot be assigned to individual radar pixels without a measured as-built surface and an exact disturbance overlay.
7. A protective-remedy finding does not prove that the radar surface is physically unchanged or suitable for depth calibration.

## Candidate classification

```text
candidate_status = closed_design_minimums_and_dynamic_forest_surface
published_cover_minimum_m_gentle_slopes = 1.2192
published_cover_minimum_m_steep_slopes = 0.9144
point_specific_actual_depths = no
numerical_uncertainty_documented = no
stable_unchanged_radar_surface = no
eligible_calibration_row = no
```

## Readiness impact

```text
usable_calibration_rows_added = 0
numerical_depth_ready = no
```

## Public evidence reviewed

- EPA Walsh Landfill current cleanup and reuse profiles.
- EPA second and third Five-Year Review reports.
- EPA OU1 administrative-record index.
- EPA site chronology and 2026 Five-Year Review announcement.

The PDF screenshot service returned cache-miss errors. No claim in this note relies on unseen figures or maps; only parsed text was used.
