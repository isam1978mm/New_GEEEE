# Public As-Built and Open-Trench Dataset Screen — 2026-07-21

Status: public-only evidence search continued. No author contact, survey request, fieldwork request, calibration import, model training, or app-depth enablement occurred.

## Current decision

```text
approved_known_depth_positive_records = 0
approved_confirmed_negative_records = 0
relative_depth_baseline_status = not_fitted
app_depth_enabled = false
```

## Candidate A — OpenTrench3D

Primary sources:

- CVPR Workshops 2024 paper: `10.1109/CVPRW63382.2024.00760`
- public repository referenced by the paper

Verified public facts:

- 310 fully annotated photogrammetric point clouds;
- 7 distinct construction areas;
- 5 water-utility areas and 2 district-heating areas;
- utilities are physically exposed in open trenches;
- classes include main utility, other utility, inactive utility, trench, and miscellaneous;
- suitable for geometry, segmentation, excavation-truth, and cross-area generalisation research.

Qualification:

```text
independent_physical_visibility = yes_open_trench
multiple_area_groups = yes_7
buried_state_observed = no_open_trench_only
matched_sentinel_1_observations = no
numerical_depth_to_top_table = not_verified
confirmed_negative_buried_site = no
method_research_usable = yes
sentinel_1_depth_calibration_usable = no
```

Reason for exclusion from the depth calibration pack:

The dataset records utilities while trenches are open. It therefore verifies utility geometry and class, but it does not provide the matched buried-state Sentinel-1 observations required by the current app-depth research question.

## Candidate B — Municipal sewer and utility GIS

Public examples screened:

- City of Chilliwack sanitary utility line data with upstream and downstream invert elevations;
- City of Windsor sewer and manhole data with manhole top and invert elevations;
- Alberta rural low-pressure gas distribution as-built data with pipe material and year built;
- Ontario and Canadian open utility-line datasets with public line geometry;
- Main Roads Western Australia underground-utility survey extents.

Useful properties:

- public geospatial geometry;
- in some cases invert elevations, manhole depth, construction year, pipe material, or as-built provenance;
- potentially useful for excluding known infrastructure from background-control polygons;
- potentially useful for testing whether a candidate area overlaps mapped utilities.

Qualification:

```text
public_geometry = yes_for_selected_datasets
construction_or_invert_attributes = partial
exact_depth_to_top = usually_not_available
reference_uncertainty = not_reported
buried_object_presence = infrastructure_map_not_independent_detection_label
matched_pre_post_sentinel_1 = no
confirmed_empty_ground = no
background_screening_usable = potentially_yes
sentinel_1_depth_calibration_usable = no
```

Use rule:

These datasets may be used only as supporting exclusion/context evidence after checking licence, date, geometry accuracy, and attribute definitions. Absence of a mapped utility must not be treated as proof of empty ground.

## Candidate C — Public pipeline depth-of-cover demo services

A public ArcGIS `Pipeline_Asbuilt` demo service exposes layers including `Depth_of_Cover`, route, weld, valve, and crossing layers.

Qualification:

```text
service_type = demo
scientific_provenance = not_established
independent_depth_reference = not_established
licence_and_version = not_established
calibration_import = prohibited
```

This service is not approved evidence and is retained only as an example of the attributes a valid as-built package would need.

## Search boundary confirmed

The public search still has not found a source combining all of the following:

```text
1. independently measured buried depth to a defined target reference;
2. numerical uncertainty;
3. multiple independent physical sites;
4. defensible positive and confirmed-negative records;
5. acquisition dates and stable site grouping;
6. matched Sentinel-1 observations at a supportable spatial scale;
7. public reuse terms.
```

## Next public-only work

1. inspect public sewer/as-built schemas for usable depth-to-top derivations only where surface elevation and invert/diameter definitions are explicit;
2. search for public pre-construction and post-construction utility corridors with exact dates;
3. search for public large-area controlled sites whose disturbance footprint is resolvable at Sentinel-1 scale;
4. keep GPR, photogrammetry, municipal GIS, and Sentinel-1 evidence roles separate;
5. import nothing until the calibration contract passes.
