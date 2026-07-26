# Sconondoa Authoritative Control Check — 2026-07-26

## What was checked

The provisional Phase 3 QA polygons were checked against the exact Appendix A environmental-easement boundary reconstructed from the recorded metes-and-bounds description.

That comparison cannot be used as a pass/fail georeference test for the Phase 3 polygons.

The Final Engineering Report states that:

- the on-site property is the approximately 2.1-acre triangular parcel at 215 Sconondoa Street;
- the off-site area is approximately 4.4 acres on adjacent properties;
- the Phase 3 remedial action was performed both on the Site and in the adjacent portion of the off-site Tailrace area.

Therefore, a Phase 3 polygon extending beyond the Appendix A easement parcel is not by itself evidence that its georeference is wrong.

## Result

```text
appendix_a_easement_containment_test = not_valid_for_phase3_full_area
qa_geojson_rejected_by_this_test = no
qa_geojson_execution_ready = no
authoritative_external_placement_check_completed = no
earth_engine_query_executed = no
```

The provisional GeoJSON remains QA-only. The current affine fit has not been independently validated against a common control that is authoritative for both the on-site and adjacent off-site Phase 3 area.

## Evidence still required

Use one of the following:

1. a correctly georeferenced 2022 or 2017 NYS orthophoto overlay showing the Service Center Building, Sconondoa Street, and the Phase 3 area; or
2. a separate survey/control point with coordinates in an authoritative CRS that is also identifiable in Appendix B-3.

The validation must check the polygon placement error against the inward buffer and the nominal 20 m Sentinel-1 support area.

## Current status

```text
usable_calibration_rows = 0
numerical_depth_ready = no
app_depth_enabled = false
earth_engine_query_executed = no
site_document_screen = good_to_go
replacement_polygon_size_gate = passed
qa_geojson_status = QA_ONLY_NOT_EXECUTION_READY
authoritative_placement_validation = blocked_missing_independent_common_control
```

## Next step

Obtain one independent authoritative georeferenced control for the Phase 3 area, measure the placement residual, and only then freeze the GeoJSON and run the Sentinel-1 coverage dry run.
