# Recomp As-Built Follow-up — 2026-07-25

**Branch:** `main`  
**Status:** documented installed cover, but not a clean or uncertainty-bounded calibration site  
**Calibration rows created:** 0

## Plain-English result

Recomp cannot currently provide a usable numerical-depth calibration row.

The public record confirms that the ash landfill was closed with a two-foot-thick compacted clay cover. It also lists official `G3/G4` as-built drawings.

However, the `G3/G4` package belongs to the temporary ash-storage facility constructed on top of the closed landfill. That later facility added a geomembrane, 18 inches of compacted native soil, and four inches of asphalt above the older clay cover.

The site then remained operational and received additional grading, stormwater work, paving, storage, recycling, transfer-station activity, and later construction near the landfill.

This means the surface seen by Sentinel-1 is not a stable, isolated expression of the original two-foot clay cover.

## Official records checked

Washington Department of Ecology Cleanup Site ID `378` lists:

- Engineering Report: Landfill Closure and Temporary Ash Storage Facility Construction, document `97109`;
- Temporary Ash Storage Facility As-Built Drawings `G3` and `G4`, document `97110`;
- 2020 grading and stormwater record drawings;
- 2021 scale-station construction requests;
- periodic reviews and an environmental covenant.

The official site record states:

- the ash landfill was closed with a two-foot compacted clay cover;
- the temporary ash-storage cells were built on top of the closed landfill;
- the storage-facility liner system placed an HDPE geomembrane over the clay layer;
- 18 inches of compacted native soil and four inches of asphalt were installed above the geomembrane;
- active recycling, storage, material-recovery, and transfer operations continued at the site.

## Drawing retrieval result

The engineering-report PDF was identified, but its pages were not readable through the available public-document renderer. The `G3/G4` document endpoint also failed to return a usable PDF during the bounded retrieval attempt.

No alternate official copy or indexed text supplied:

- measured original clay-cover thickness points;
- before-and-after elevation surfaces for the original landfill closure;
- numerical vertical survey accuracy;
- construction tolerance that can be assigned as final depth uncertainty.

The public site description supports an installed two-foot cover, but not an exact satellite-footprint depth label with a defensible uncertainty interval.

## Timing and surface-confounding decision

Recomp is heavily confounded because later engineered layers and operations occupy the same physical surface:

```text
original_clay_cover = 2.0 ft
later_geomembrane = yes
later_compacted_native_soil = 1.5 ft
later_asphalt = 0.333 ft
later_grading_and_operational_changes = yes
clean_isolated_sentinel1_surface = no
```

Even if the original clay-cover boundary were recovered, the modern radar signal would represent the combined later surface and operational history rather than the original closure layer alone.

## Current evidence state

```text
installed_two_foot_clay_cover = yes
original_cover_as_built_boundary = unresolved
original_cover_measured_surface = no
numerical_vertical_accuracy = no
confirmed_no_target_comparison = no
clean_sentinel1_timing = no
eligible_calibration_row = no
```

## Decision

Close Recomp as a weak evidence-only hold.

Do not:

- use `2.0 ft` as an exact measured depth label;
- treat storage-facility `G3/G4` drawings as proof of the original clay-cover thickness;
- combine the original and later layers into one false target-depth value;
- create a calibration row;
- start training.

## Current status

Recomp documents an installed cover but cannot isolate that cover in a clean modern satellite observation.

```text
usable_recomp_calibration_rows = 0
total_usable_calibration_rows = 0
numerical_depth_training_ready = no
app_depth_output_ready = no
```

## Next step

Inspect the RAMCO cap as-built drawings for actual measured thickness or elevation values, an explicit survey-control bound, and a stable post-construction observation period.