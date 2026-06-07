# Future Slice D1 Frozen Reference Bundle Collection Plan

D1 creates a scaffold and operator collection plan only. It does not collect,
download, generate, or commit real frozen notebook references.

Frozen references must stay outside git and remain private/filesystem-only. Missing
references are not success. Notebook-value parity remains false until real Phase
E, E3, or E4 comparisons pass.

## Bundle Layout Template

The operator-owned private bundle layout is:

```text
data/notebook_references/<bundle_id>/
  manifest.json
  references/
    report_640/
    secret_layers/
    dem_curvature/
    sar_asc_desc/
    s1_filtered_stack/
    pan_stack/
    pan_components/
    hypercube_res25/
    semantic_rasters/
    private_map_artifacts/
    phase_c_semantic_feature_writers/
    phase_d_private_geojson_writer/
    phase_d2_private_kmz_writer/
    phase_d3_private_heatmap_json_writer/
```

This layout is a template only. No real files under
`data/notebook_references/` are committed by D1.

## Manifest Template

The required manifest fields are:

```text
bundle_id
schema_version
created_at
created_by
source_notebook_name
source_notebook_version
source_notebook_commit_or_hash
source_run_id
source_grid_id
source_roi_id_redacted
collection_method
collection_environment
artifact_class
filesystem_only
http_servable
frontend_visible
downloadable_via_api
redaction_policy
families
family_inventory
expected_artifact_counts
hashes_available
tolerance_policy_ref
notes
```

The manifest must use `schema_version=frozen_notebook_reference_bundle_v1`.

## Storage And Redaction

Bundle storage rules:

- `artifact_class` is `LOCAL_SENSITIVE` or `FILESYSTEM_ONLY`
- `filesystem_only=true`
- `http_servable=false`
- `frontend_visible=false`
- `downloadable_via_api=false`
- the bundle root is outside git, except pytest temporary paths used by tests
- public summaries exclude exact coordinates, raw shapes, filesystem references,
  private digests, and artifact payloads

## Operator Checklist

The operator collection checklist is:

```text
choose_private_bundle_root_outside_git
capture_manifest_with_required_fields
create_references_subfolders_for_expected_families
record_per_family_artifact_inventory
classify_bundle_local_sensitive_or_filesystem_only
keep_public_summaries_redacted
run_phase_e_e3_e4_verifiers_later
```

D1 does not run the notebook, Earth Engine, Colab, or Drive. It does not generate
app outputs, rasters, tensors, map artifacts, datasets, labels, chips, model
files, or classifier outputs.

## Helper

Implemented module:

```text
app/pipeline/parity/frozen_reference_bundle_scaffold.py
```

The helper provides:

- `get_frozen_reference_bundle_scaffold()`
- `validate_frozen_reference_bundle_manifest(...)`
- `write_frozen_reference_bundle_scaffold_report(...)`

The report path is:

```text
data/runs/<run_id>/manifests/d1_frozen_reference_bundle_scaffold.json
```

The report is collection-plan metadata only:

```text
collection_plan_only=true
real_references_collected=false
artifact_generation=false
runtime_output_verified=false
notebook_value_parity_verified=false
earth_engine_calls_added=false
public_exposure_changes=false
```

## Validator Behavior

Validator statuses:

```text
scaffold_defined
not_collected
invalid_manifest
invalid_storage_policy
ready_for_operator_collection
ready_for_later_verifier_run
```

Missing manifests and missing references are not success. Empty bundles do not
mark notebook-value parity true.

## Handoff To Verifiers

Later consumers are:

- Phase E private frozen-reference verifier:
  `app/pipeline/parity/frozen_reference_verifier.py`
- Phase E3 semantic feature comparator:
  `app/pipeline/parity/semantic_feature_comparator.py`
- Phase E4 private map artifact comparator:
  `app/pipeline/parity/private_map_artifact_comparator.py`

Those later verifiers remain responsible for real comparisons. D1 does not mark
notebook-value parity true.

## Safety Boundary

D1 does not:

- collect or commit real frozen references
- add files under `data/notebook_references/`
- download reference artifacts
- generate app outputs
- run Earth Engine, Colab, or Drive behavior
- change raster/math logic or comparator tolerances
- train models, run inference, or add ML dependencies
- expose private artifacts publicly
- change API, frontend, database, or artifact-serving policy
- mark H3/H4 or public exposure work complete
