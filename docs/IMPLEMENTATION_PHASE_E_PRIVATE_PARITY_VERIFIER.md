# Implementation Phase E Private Parity Verifier

Phase E adds private frozen-reference verifier capability.

## Implemented Capability

The implementation module is:

`app/pipeline/parity/frozen_reference_verifier.py`

It validates a frozen notebook reference bundle and runs private read-only parity checks where existing verifier-backed families are available. It wraps the Phase 9 end-to-end harness instead of duplicating family verifier logic.

## Frozen Reference Bundle Layout

The expected private bundle layout is:

```text
data/notebook_references/<bundle_id>/
  manifest.json
  references/
    <family_id>/
      ...
```

The manifest must be a JSON object with:

- `schema_version`
- `bundle_id`
- `captured_at` or `created_at`
- `notebook_source`
- `families`
- `files`
- optional `sha256` values
- optional metadata expectations
- `notes`

The Phase E validator does not require real frozen references to be committed to the repository. Tests create tiny fake bundles under pytest temporary directories only.

## Supported Families

Phase E supports selected-family filtering for:

- `report_640`
- `secret_layers`
- `dem_curvature`
- `sar_asc_desc`
- `s1_filtered_stack`
- `pan_stack`
- `pan_components`
- `hypercube_res25`
- `semantic_rasters`
- `private_map_artifacts`
- `phase_c_semantic_feature_writers`
- `phase_d_private_geojson_writer`

Verifier-backed families delegate to the Phase 9 harness and existing read-only verifier modules.

Inventory-only families remain inventory-only and do not set notebook-value parity true.

Phase C and Phase D implementation families validate frozen reference presence and app output presence, but remain `verifier_not_available` until a dedicated value comparator is approved and implemented.

## Status Rules

Missing frozen references are not success.

Missing app outputs are not success.

Missing comparison dependencies are reported as `comparison_unavailable`, not success.

Runtime output presence and notebook-value parity remain separate.

`notebook_value_parity_verified` can be true only when every selected verifier-backed family passes.

## Safety Boundary

Phase E does not:

- generate app outputs
- run the live pipeline
- call Earth Engine
- use Colab
- use Google Drive
- change science, raster, or math logic
- expose private outputs through API, frontend, or artifact serving
- add public downloads
- add new writers
- add classifier, model, training, or inference behavior
- implement Phase F, G, H, I, or J behavior

The Phase E report is private JSON metadata written under:

`data/runs/<run_id>/manifests/private_frozen_reference_verifier_report.json`

Phase F will handle the optional private CLI classifier later.
