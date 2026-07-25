# Sudbury Report 64264 — Final Public Recovery Result — 2026-07-25

**Branch:** `main`  
**Status:** public recovery exhausted; exact as-built survey values still unavailable  
**Purpose:** record the final bounded attempt to recover the Sudbury Road Landfill Construction Quality Assurance Certification Report and its mapped cover-depth data

## Plain-English result

The official Washington Department of Ecology site still lists the **Construction Quality Assurance Certification Report**, dated April 14, 2017, as document `64264`.

The report's direct Ecology download failed repeatedly. Searches of the City of Walla Walla agenda archive, older Ecology document paths, indexed web copies, and the separately posted operation-and-maintenance appendices did not recover an identical copy or the certified record drawings.

The accessible official construction specifications, document `53360`, prove that the missing survey data was required and created. They require:

- conventional as-built surveying rather than machine-control data alone;
- post-cover surveys of Areas 2 and 5;
- a minimum 50-foot survey grid for the final surface;
- all survey points, digital terrain-model surfaces, and earthwork calculations to be submitted in AutoCAD Civil 3D format;
- established local landfill benchmarks;
- owner independent checks when desired;
- record drawings showing horizontal and vertical constructed locations.

The same specifications contain the Area 2 and Area 5 soil-cover finish-grade acceptance entry using field verification from hand auger / survey staking on a 100-foot grid with a listed `-0.10 foot to 0 foot` control range.

This proves the exact final survey dataset existed. It does **not** provide the actual point elevations, mapped thickness surface, or a complete final depth-uncertainty interval.

## Recovery paths checked

1. Ecology cleanup-search document endpoint for `64264`.
2. Older Ecology `gsp/DocViewer` path searches.
3. Exact-title and exact-document-number web searches.
4. City of Walla Walla council and project archive searches for project `LF09010`.
5. Operation and Maintenance Plan appendices posted beside the report.
6. Search-index phrase recovery for Areas 2 and 5, test pits, digital terrain models, finished grade, and record drawings.

None exposed the certified as-built surface values.

## Evidence state

```text
construction_completed = yes
verified_minimum_cover_m = 1.46304
professional_subgrade_survey = yes
professional_finish_grade_survey = yes
final_50ft_surface_survey_required = yes
survey_points_and_dtm_required = yes
local_benchmarks_required = yes
construction_control_values_available = yes
actual_as_built_point_values_recovered = no
mapped_thickness_surface_recovered = no
final_depth_uncertainty_assigned = no
confirmed_no_target_comparison = no
eligible_calibration_row = no
```

## Decision

Close the public Sudbury recovery path. Do not convert the 4.8-foot minimum or the construction-control tolerances into an exact satellite-footprint depth label.

Sudbury can only advance if the certified survey points, DTM surfaces, or record drawings are obtained from a non-indexed official file source or public-records response.

## Current readiness

```text
usable_calibration_rows = 0
numerical_depth_training_ready = no
app_depth_output_ready = no
```

## Next bounded action

The six named public-site routes are now exhausted. Begin a new narrow candidate screen using standardized public closure packages that are more likely to publish all of the following together:

- certified as-built thickness maps or point tables;
- survey accuracy or bounded uncertainty;
- mapped unchanged comparison areas;
- construction and stable observation dates.

Start with EPA CCR compliance websites and only retain sites whose closure-certification package includes actual as-built survey values rather than design minimums alone.
