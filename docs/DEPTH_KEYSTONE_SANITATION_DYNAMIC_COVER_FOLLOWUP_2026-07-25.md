# Keystone Sanitation Landfill — Dynamic Cover Follow-up

Date: 2026-07-25

## Decision

**Status:** closed as a numerical-depth calibration route.

Keystone initially looked promising because EPA required a grid-based investigation of existing soil-cover thickness and upgrades to maintain at least two feet of cover across the landfill. The completed remedy, however, does not provide a stable unchanged reference surface. EPA's September 10, 2025 Five-Year Review reports ongoing ponding and subsidence, two rounds of subsidence repairs, continuing cover monitoring, mature and maturing woody vegetation, and additional cover or vegetation alternatives still under evaluation.

## What is confirmed

- Site: Keystone Sanitation Landfill, Union Township, Adams County, Pennsylvania; EPA ID PAD054142781.
- The inactive landfill covers approximately 40 acres.
- EPA's 2000 Record of Decision Amendment required a comprehensive grid-based investigation of the existing soil-cover thickness.
- Areas with less than two feet of cover were to be upgraded to at least:
  - 18 inches of low-permeability soil; and
  - a minimum six-inch erosion layer.
- Cover and stormwater upgrades were constructed between October 14, 2003 and June 4, 2004.
- EPA issued construction-completion status on September 13, 2004.
- Institutional controls restrict construction and activities that could interfere with the cover or remedy.
- The September 10, 2025 Five-Year Review states that:
  - the cover has areas of ponding and subsidence;
  - subsidence areas were repaired on two occasions;
  - monitoring of the cover continues;
  - mature and maturing woody vegetation covers parts of the landfill;
  - potential cover and vegetation alternatives are still being evaluated;
  - ponding likely associated with subsidence may increase infiltration and leachate generation;
  - cover repairs and vegetation improvements remain possible operation, maintenance or optimization activities.
- EPA plans a further remedial decision process concerning 1,4-dioxane and related source-control issues.

## Why it is not usable

1. The original grid-based cover-thickness results and completed construction survey were not recovered.
2. The two-foot requirement is a minimum design/acceptance threshold, not an extracted point-specific measured depth.
3. No numerical measurement or survey uncertainty was recovered.
4. The surface experienced subsidence and ponding after construction.
5. Subsidence repairs occurred on two occasions, changing local cover depth and geometry.
6. Cover monitoring and possible additional repairs remain ongoing.
7. Woody vegetation has expanded and is now being considered as part of future remedy optimization rather than removed uniformly.
8. Gas extraction wells, leachate monitoring points, stormwater controls, treatment infrastructure, access routes and occupied structures create extensive radar confounders.
9. A single stable Sentinel-1 interval cannot be assigned to the full landfill cover.
10. Even if the original grid were recovered, every point would require a repair and disturbance overlay before it could be considered.

## Candidate classification

```text
candidate_status = closed_dynamic_surface_and_missing_point_values
original_grid_investigation_required = yes
completed_point_values_recovered = no
minimum_cover_m = 0.6096
minimum_value_is_exact_depth_label = no
post_construction_subsidence = yes
post_construction_repairs = yes_twice
ongoing_cover_change = yes
numerical_uncertainty_documented = no
eligible_calibration_row = no
```

## Readiness impact

```text
usable_calibration_rows_added = 0
numerical_depth_ready = no
```

## Public evidence reviewed

- 2000 EPA Record of Decision Amendment
- EPA site cleanup, schedule and institutional-control pages
- September 10, 2025 Sixth Five-Year Review Report

## PDF access note

The 2025 review text was readable through EPA's parsed PDF record. Required screenshot attempts for the relevant pages failed with an EPA cache miss. No unseen visual geometry was used.
