# Boone County Landfill Test Cell 1 — Historical Evidence Only

Date: 2026-07-26

## Decision

**Status:** closed as unusable for Sentinel-1 depth calibration.

Boone County Test Cell 1 is unusually well documented: EPA records give its dimensions, construction, 0.6 m soil cover, cover layering, and later physical excavation. However, the test cell was dismantled in September 1980. It therefore did not exist during the Sentinel-1 era and cannot be matched to modern radar observations.

## What is confirmed

- Location context: EPA experimental landfill field site in Boone County, Kentucky.
- Test Cell 1 was constructed in June 1971.
- Planned trench dimensions were approximately 45.4 m long by 9.2 m wide.
- The measured refuse/cover surface area was approximately 432.3 square metres.
- A 0.6 m (24 inch) soil cover was placed when the cell was closed.
- Later excavation found two cover layers:
  - approximately 0.13 m upper layer with root penetration;
  - approximately 0.48 m compact blocky clay lower layer.
- EPA documents provide plan and longitudinal-section schematics.
- The test program collected hydrologic and leachate data during the 1970s.
- Test Cell 1 was dismantled in September 1980.

## Why it is not usable

1. The physical target was removed long before Sentinel-1 observations began.
2. There is no unchanged modern surface corresponding to the documented cover.
3. The available 0.6 m value is a whole-cell construction value, not a mapped set of independent point measurements with uncertainty.
4. Historical experimental measurements cannot be paired with present satellite signals after dismantling.

## Candidate classification

```text
candidate_status = closed_historical_test_cell_dismantled_before_sentinel1
known_cover_thickness_m = 0.6
physical_postconstruction_confirmation = yes
modern_surface_exists = no
sentinel1_overlap = no
eligible_calibration_row = no
```

## Readiness impact

```text
usable_calibration_rows_added = 0
numerical_depth_ready = no
```

## Public evidence reviewed

- EPA proceedings describing Hydrologic Simulation on Solid Waste Disposal Sites using Boone County Test Cell 1.
- EPA HELP model verification report with the test-cell construction profile.
- EPA Boone County field-site project summary.
- EPA report documenting dismantling of Test Cell 1 in September 1980.
