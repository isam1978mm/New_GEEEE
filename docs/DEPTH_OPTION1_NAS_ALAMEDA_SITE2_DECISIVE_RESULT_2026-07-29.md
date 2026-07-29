# Option 1 decisive result — NAS Alameda IR Site 2

Date: 2026-07-29

## Decision

**NOT GOOD TO GO for numerical-depth calibration.**

This is **Option 1 evidence research**. Option 3 is not active.

## What the official completion report proves

The January 2017 Final Remedial Action Completion Report provides unusually strong construction records:

- approximately 79 acres of final landfill cover;
- one common final cover assembly consisting of an 18-inch compacted soil layer plus a 6-inch vegetative-soil layer;
- final soil-cover verification monuments on an approximately 100-foot by 100-foot grid;
- unique point identifiers and northing/easting coordinates;
- surveyed pre-cover plywood elevations and final cover elevations;
- calculated cover thickness at 341 recovered monument rows;
- final topographic survey verified by a licensed land surveyor;
- cover thickness of at least 2 feet at every monument;
- average measured thickness of approximately 2.2 feet.

Recovered thickness values span approximately 2.0 to 3.1 feet. Most measurements are between 2.0 and 2.4 feet.

## Why it still fails the calibration gate

The measured variation does not define two independent constructed depth treatments or official final depth polygons.

- The remedy is one uniform two-foot minimum cover design over the entire landfill.
- The values above two feet are local overfill and settlement-related construction variation, not separate named shallow and deep treatment areas.
- The official report publishes point measurements. It does not certify broad polygons as having one uniform final depth.
- Creating shallow/deep polygons by interpolating or thresholding the 100-foot grid would create analyst-derived geometry and analyst-derived labels.
- The report states that additional settlement was anticipated and that drainage, settlement, erosion, vegetation, and extraordinary repairs would be managed through post-closure operations and maintenance.
- The public completion report does not establish a later repair-free, polygon-specific Sentinel-1 observation period for any derived shallow/deep zones.

The coordinate grid and measured values are excellent quality-control evidence, but they cannot honestly be converted into two polygon-level calibration labels without adding unsupported spatial interpolation assumptions.

## Safety decision

```text
candidate_status = not_good_to_go
usable_calibration_rows_added = 0
earth_engine_query_executed = false
calibration_record_created = false
training_started = false
numerical_depth_ready = false
app_depth_enabled = false
option_3_active = false
```

## Reopening condition

Reopen only if an official later record publishes:

1. certified broad final depth zones derived from the survey grid;
2. numerical uncertainty for those polygon-level depths; and
3. mapped post-2014 repairs and a stable observation interval for the exact zones.
