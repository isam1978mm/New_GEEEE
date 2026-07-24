# Go East Confirmed-Negative Evidence Update — 2026-07-25

**Branch:** `main`  
**Status:** evidence verified; geometry and clean observation timing incomplete  
**Purpose:** record the strongest public no-target evidence found for the numerical-depth calibration route

## Plain-English result

Go East supplies two physically checked areas where buried landfill material was not left in place:

1. a southeast lot-exploration area outside the landfill where investigators specifically checked for buried landfill material and found none;
2. the excavated wedge area around the former landfill edge, where landfill material was removed and the remaining base and outer sidewalls were confirmed as native soil.

These are stronger than analyst-selected background polygons. They still cannot become calibration rows because their exact mapped footprints have not been extracted into private geometry files and the site remained under active development after landfill closure.

The later official monitoring reports also strengthen the positive-depth evidence: the completed engineered cover is described as having at least 12 inches of topsoil, 12 inches of onsite sand, a geocomposite, a geomembrane, and a 6-inch bottom sand layer. This supports a constructed minimum soil thickness of 30 inches (`0.762 m`) above the underlying waste. It does not provide an exact measured thickness surface or a complete uncertainty interval.

## Official source package

The active Washington Department of Ecology Go East Corp Landfill package includes:

- Construction Quality Assurance Report, document `113990`;
- Final Interim Action Completion Report, document `107534`;
- As-Built/Record Drawings, document `113994`;
- approved landfill-closure plans and plan sheet 4;
- Construction Summary Report, document `114132`;
- 2024 Annual Report: Landfill Gas Performance Monitoring, document `156805`;
- 2025 Annual Monitoring Report for Groundwater and Surface Water, document `157747`.

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
reference_status = confirmed_no_target_pending_geometry_and_timing
physical_confirmation = yes
exact_private_geometry_extracted = no
clean_sentinel1_window_verified = no
eligible_calibration_row = no
```

## Confirmed-negative area B — cleared wedge area

The official package states that:

- landfill material around the former landfill edge was excavated and consolidated into the landfill area that remained;
- landfill material was confirmed to be entirely removed from the wedge area;
- only native soil remained in the base and distal sidewalls;
- confirmation sampling was performed by environmental professionals;
- 59 confirmation samples and 9 resamples were collected;
- areas with an initial exceedance were over-excavated and resampled;
- no resampled soil contained an analyte above the interim action levels;
- the final configuration is referenced in the as-built drawings;
- 2025 monitoring records continue to identify wells beneath areas where landfill material was excavated.

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

The later official monitoring report states that the completed engineered cover contains, from top to bottom:

- minimum 12 inches (`0.3048 m`) of topsoil;
- minimum 12 inches (`0.3048 m`) of onsite sand;
- geocomposite;
- geomembrane;
- minimum 6 inches (`0.1524 m`) of bottom onsite sand.

This supports:

```text
constructed_minimum_soil_cover_m = 0.762
engineered_cover_installed = yes
exact_as_built_thickness_surface_extracted = no
final_depth_uncertainty_m = not_assigned
```

The public record also confirms professional engineering, geotechnical observation, licensed survey participation, and certification of the closure work.

The `0.762 m` value is a constructed minimum from the listed layer requirements. It must not be represented as an exact average depth for the landfill or for any satellite-scale polygon.

## Observation-timing review

The new monitoring records resolve the earlier timing question in the negative.

The site was not in a clean unchanged condition immediately after closure:

- residential and utility development continued around the landfill after the July 2022 closure;
- the final plat was approved in 2023;
- 55 homes were constructed in 2024;
- one perimeter probe was unintentionally buried beneath asphalt during driveway construction;
- that probe was inaccessible because of construction blockage from March through December 2024;
- the 2025 groundwater report still described the surrounding residential development as being developed;
- several monitoring-well casing heights were adjusted in May 2023 to match modified ground-surface elevations.

Therefore:

```text
clean_post_closure_sentinel1_window_2022_to_2024 = no
clean_2025_window_verified = no
surface_construction_confounding = confirmed
```

A future stable period may exist after all surrounding construction is complete, but it has not yet been verified from the public record.

## Elk Plain cross-check completed in the same pass

The official Elk Plain cap map confirms:

- an AHBL as-built comparison of the contaminated-soil surface and clean-cap surface;
- many actual thickness values from approximately `6.00` to `11.08` feet;
- Ecology accepted the map as addressing its cap-thickness request.

The official cap inspection plan maps a borrow area used for clean cap soil. That borrow area is not independently confirmed as a no-target comparison and must not be used as a negative row.

The map title block identifies the cap map as a `REVIEW SET` and does not provide a numerical vertical accuracy, survey-control bound, or closure tolerance. The recorded survey number remains the next source for that missing uncertainty evidence.

## Current readiness

```text
physical_site_groups_with_confirmed_negative_evidence = 1
physically_checked_no_target_or_cleared_areas_at_go_east = 2
confirmed_negative_private_footprints_extracted = 0
constructed_minimum_positive_depth_m_at_go_east = 0.762
clean_go_east_observation_window_verified = no
eligible_negative_calibration_rows = 0
eligible_positive_calibration_rows = 0
relative_depth_training_ready = no
numerical_depth_training_ready = no
app_depth_output_ready = no
```

## Decision

Go East remains the strongest confirmed-negative public lead and is now also a stronger bounded-minimum positive-depth lead.

It is still not calibration-ready because:

1. the negative footprints remain unextracted;
2. the positive thickness surface remains unextracted;
3. no full numerical uncertainty is assigned;
4. active construction prevents a clean Sentinel-1 timing window.

## Next bounded action

Continue only with these named documents:

1. Go East plan sheet 4 or Lot Exploration Plan appendix to extract the southeast no-target footprint;
2. Go East record drawings to extract the cleared-wedge footprint and any cover-elevation data;
3. Elk Plain Pierce County Record of Survey `202502055001` for survey-control or vertical-accuracy evidence;
4. Sudbury certified as-built drawings and project-specific survey tolerance;
5. a post-development Go East report that explicitly confirms the surrounding construction is complete and the monitored surface is stable.

Do not create a calibration record until the mapped footprint, observation timing, and required uncertainty fields are supported. No outreach or generic candidate search was performed.