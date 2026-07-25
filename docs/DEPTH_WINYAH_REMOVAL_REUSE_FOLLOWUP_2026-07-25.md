# Winyah Removal and Reuse Follow-up — 2026-07-25

**Branch:** `main`  
**Status:** closure-by-removal confirmed, but former pond footprints were reused or remain operationally altered  
**Calibration rows created:** 0

## Plain-English result

Winyah is not a usable confirmed-empty calibration site.

The official Santee Cooper CCR record confirms closure by removal for multiple Winyah impoundments, including the Unit 2 Slurry Pond, Ash Pond A, Ash Pond B, and the South Ash Pond. State approval of closure is also listed.

The decisive problem is post-removal reuse:

- the closed Unit 2 Slurry Pond footprint was converted into Class 3 Landfill Area 1;
- Class 3 Landfill Area 1 began receiving waste on November 1, 2018;
- Class 3 Landfill Area 2 occupies part of the Ash Pond A footprint;
- portions of Ash Pond A were closed in phases specifically before landfill construction;
- Class 3 Landfill Area 2 began receiving waste on March 28, 2022.

Therefore these areas did not remain dry, unused, and materially unchanged after removal.

## Evidence established

```text
closure_by_removal_confirmed = yes
state_closure_approval_listed = yes
unit_2_slurry_pond_closed = 2017-11-09
unit_2_footprint_reused_as_landfill = yes
landfill_area_1_operation_start = 2018-11-01
ash_pond_A_partly_reused_as_landfill = yes
landfill_area_2_operation_start = 2022-03-28
stable_unchanged_surface = no
usable_negative_calibration_row = no
```

## Geometry and survey decision

Even if final closure surveys can be recovered, the reuse history already disqualifies the former Unit 2 Slurry Pond footprint and the reused portion of Ash Pond A as unchanged negative-control areas.

Ash Pond B and the South Ash Pond also remain inside an active generating-station and remediation setting, with continuing inspection, groundwater, corrective-action, grading, or operational records. No clean multi-year unchanged surface period was established from the public record.

No analyst-drawn polygon, active-landfill footprint, or broad pond boundary may be substituted for a stable confirmed-empty area.

## Current classification

```text
reference_status = confirmed_removal_but_disqualified_by_reuse_and_surface_change
physical_confirmation = strong
exact_final_geometry_needed_for_calibration = not_pursued_further
clean_observation_timing_verified = no
eligible_negative_calibration_row = no
```

## Decision

Close the Winyah route.

Do not spend more time extracting survey coordinates for the Unit 2 Slurry Pond or the landfill-reused portion of Ash Pond A. Their post-removal reuse independently prevents their use as unchanged Sentinel-1 negative controls.

## Current readiness

```text
usable_positive_depth_site_groups = 0
usable_confirmed_negative_site_groups = 0
calibration_records_created = 0
numerical_depth_training_ready = no
app_depth_output_ready = no
```

## Next bounded action

Search for a completed closure-by-removal site where:

1. the final survey drawing is directly readable;
2. the exact removed-area boundary is tied to state-approved completion;
3. numerical survey uncertainty or a governing accuracy standard is available; and
4. the cleared footprint remained dry, unused, and unchanged for a defensible Sentinel-1 period.

Prefer retired rural facilities, isolated disposal units, or regulator-owned cleanup sites. Avoid active power stations, landfill conversions, wetlands, drainage works, and redevelopment properties.