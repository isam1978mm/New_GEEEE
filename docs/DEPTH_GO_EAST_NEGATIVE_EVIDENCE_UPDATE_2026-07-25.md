# Go East Confirmed-Negative Evidence Update — 2026-07-25

**Branch:** `main`  
**Status:** evidence verified; mapping and timing incomplete  
**Purpose:** record the strongest public no-target evidence found for the numerical-depth calibration route

## Plain-English result

Go East now supplies two physically checked areas where buried landfill material was not left in place:

1. a southeast lot-exploration area outside the landfill where investigators specifically checked for buried landfill material and found none;
2. the excavated wedge area around the former landfill edge, where landfill material was removed and the remaining base and outer sidewalls were confirmed as native soil.

These are stronger than analyst-selected background polygons. They still cannot become calibration rows because their exact mapped footprints have not yet been extracted into private geometry files, and later grading and development make the usable Sentinel-1 observation period uncertain.

## Official source package

The active source package is the Washington Department of Ecology Go East Corp Landfill record:

- Construction Quality Assurance Report, document `113990`;
- Final Interim Action Completion Report, document `107534`;
- As-Built/Record Drawings, document `113994`;
- approved landfill-closure plans and plan sheet 4;
- Construction Summary Report, document `114132`.

Coordinate-bearing geometry must remain outside Git.

## Confirmed-negative area A — southeast lot exploration

The Construction Quality Assurance Report states that:

- the area is outside the landfill in the southeast portion of the site;
- the exploration was required by the approved landfill-closure plan and plan sheet 4;
- the purpose was specifically to confirm that no buried landfill material was present;
- the exploration was completed and no buried landfill material was observed;
- government oversight agencies reviewed the area during confirmation;
- the exact footprint is referenced by plan sheet 4 and the Lot Exploration Plan material in the report appendices.

Current classification:

```text
reference_status = confirmed_no_target_pending_geometry
physical_confirmation = yes
exact_private_geometry_extracted = no
clean_sentinel1_window_verified = no
eligible_calibration_row = no
```

## Confirmed-negative area B — cleared wedge area

The same official package states that:

- landfill material around the former landfill edge was excavated and consolidated into the landfill area that remained;
- landfill material was confirmed to be entirely removed from the wedge area;
- only native soil remained in the base and distal sidewalls;
- confirmation sampling was performed by environmental professionals;
- 59 confirmation samples and 9 resamples were collected;
- areas with an initial exceedance were over-excavated and resampled;
- no resampled soil contained an analyte above the interim action levels;
- the final configuration is referenced in the as-built drawings.

Current classification:

```text
reference_status = confirmed_cleared_area_pending_geometry_and_timing
physical_confirmation = yes
chemical_confirmation = yes
exact_private_geometry_extracted = no
post_clearance_surface_stability_verified = no
eligible_calibration_row = no
```

This area cannot be reused as a separate train, validation, or holdout group from the southeast lot exploration because both belong to the same Go East physical site group.

## Positive-depth evidence at Go East

The source package also confirms:

- a geomembrane cover system was installed;
- the cover required at least two feet (`0.6096 m`) of overlying soil;
- the first approximately one-foot layer was placed under construction observation;
- professional engineers, geotechnical staff, and licensed surveyors participated;
- the project was certified as generally conforming to the approved construction documents.

Still missing for a numerical positive label:

- an extracted exact as-built thickness surface or matched top-and-bottom elevations;
- a numerical vertical survey accuracy or accepted thickness tolerance;
- a stable observation period unaffected by final topsoil placement, roads, drainage, recreation construction, housing development, and vegetation work.

The two-foot requirement must not be converted into a false exact measured depth.

## Elk Plain cross-check completed in the same pass

The official Elk Plain cap map confirms:

- an AHBL as-built comparison of the contaminated-soil surface and clean-cap surface;
- many actual thickness values from approximately `6.00` to `11.08` feet;
- Ecology accepted the map as addressing its cap-thickness request.

The map title block identifies it as a `REVIEW SET` and does not provide a numerical vertical accuracy, survey-control bound, or closure tolerance. The recorded survey number remains the next source for that missing uncertainty evidence.

## Current readiness

```text
physical_site_groups_with_confirmed_negative_evidence = 1
physically_checked_no_target_or_cleared_areas_at_go_east = 2
confirmed_negative_private_footprints_extracted = 0
eligible_negative_calibration_rows = 0
eligible_positive_calibration_rows = 0
relative_depth_training_ready = no
numerical_depth_training_ready = no
app_depth_output_ready = no
```

## Next bounded action

Continue only with these named documents:

1. Go East plan sheet 4 or Lot Exploration Plan appendix to extract the southeast no-target footprint;
2. Go East record drawings to extract the cleared-wedge footprint and any cover-elevation data;
3. Elk Plain Pierce County Record of Survey `202502055001` for survey-control or vertical-accuracy evidence;
4. Sudbury certified as-built drawings and project-specific survey tolerance.

Do not create a calibration record until the mapped footprint, observation timing, and required uncertainty fields are supported. No outreach or generic candidate search was performed.
