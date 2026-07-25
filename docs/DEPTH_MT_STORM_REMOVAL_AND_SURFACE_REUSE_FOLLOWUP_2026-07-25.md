# Mt. Storm Removal and Surface-Reuse Follow-up — 2026-07-25

**Branch:** `main`  
**Status:** closure by removal confirmed; calibration timing and surface stability fail  
**Calibration rows created:** 0

## Plain-English result

The former Mt. Storm Low Volume Waste Settling Ponds A, B, C, and D were formally closed by removal of coal-combustion residuals.

The official closure notification establishes that:

- visible CCR and visibly impacted subsoil were removed;
- the excavations were inspected by the Construction Quality Assurance professional engineer or representative;
- the areas were verified visually free of CCR;
- closure construction was completed on December 20, 2018;
- groundwater results from August 19, 2019 did not show statistically significant levels above the applicable protection standards;
- a West Virginia Professional Engineer certified closure by removal in October 2023.

This is strong physical removal evidence.

## Why it is not a calibration control

The land was not left as stable unused ground:

- new Ponds A and B were reconstructed in the footprint of former Ponds A, B, and C;
- the rebuilt ponds include active liners, piping, gradient controls, and operating infrastructure;
- Pond D was backfilled with structural clean fill and vegetated;
- the post-closure plan explicitly states that the former pond area would continue to be used for general station operations, including laydown, storage, and possible new-building construction.

Therefore, the post-removal Sentinel-1 signal would include new ponds, structural fill, grading, drainage, stored material, vehicles, equipment, and possible construction. It cannot serve as an unchanged empty-ground reference.

## Geometry limit

The public closure documents provide approximate station coordinates, approximate pond acreage, NAVD 88 elevations, and removal descriptions. The detailed November 2019 Construction Documentation Report is identified as being in the operating record but is not included in the public closure-notification package.

No exact private calibration geometry was created.

## Current classification

```text
physical_CCR_removal_confirmed = yes
professional_engineer_verification = yes
groundwater_closure_standard_met = yes
exact_public_as_built_boundary = no
post_removal_surface_stable_and_unused = no
clean_sentinel1_window_verified = no
eligible_negative_calibration_row = no
```

## Decision

Close Mt. Storm as a depth-calibration route. It is useful evidence that closure by removal occurred, but the immediate reconstruction and continued operational use make the radar comparison physically confounded.

## Next bounded action

Search only for a completed closure-by-removal site where:

1. the final as-built or verification-grid boundary is public;
2. the cleared area was not rebuilt or reused;
3. later reports confirm a stable vegetated or natural surface for a usable Sentinel-1 period.
