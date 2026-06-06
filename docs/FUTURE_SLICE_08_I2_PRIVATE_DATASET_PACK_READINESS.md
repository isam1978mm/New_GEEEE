# Future Slice 08 / I2 Private Dataset Pack Readiness

## Scope

Future Slice 08 (I2) adds private dataset-pack schema validation, manifest gate
checks, and a readiness report for future ML training data. It validates a local,
operator-supplied dataset pack against the binding data gates and records whether
the data gate is satisfied.

I2 creates dataset-pack schema/validator/readiness reporting. It does not create or
commit a real dataset. It does not train. It does not run inference. It does not
download data or weights. It does not scrape the web. It does not add ML
dependencies. It requires independent evidence-backed labels. It keeps datasets
outside git. It keeps dataset artifacts `LOCAL_SENSITIVE` or `FILESYSTEM_ONLY`. It
blocks training until all gates pass. H2, H3, and H4 remain later work.

The binding gates are in `docs/ML_DATA_TRAINING_READINESS_PLAN.md`, with the dataset
contract from `docs/SPECIAL_TRACK_I_DATASET_TRAINING_DESIGN.md` and the revisited
ranking in `docs/FUTURE_SLICE_07_H1_REVISIT_AFTER_I1_J1.md`. Where wording differs,
the strictest gate applies.

## Source Of Truth

The readiness helper is:

```text
app/pipeline/parity/dataset_pack_readiness.py
```

It writes one private JSON readiness report:

```text
data/runs/<run_id>/manifests/future_slice_08_i2_dataset_pack_readiness.json
```

The report path stays under `run_dir`. The validator never writes into the dataset
storage location and never creates a dataset, chips, labels, rasters, NPY files, map
artifacts, coordinate artifacts, public classifier outputs, or training outputs.

## Inputs And Path Safety

I2 takes a local `dataset_manifest.json` path, a local `training_examples.jsonl`
(one JSON object per line) path, a local `run_dir`, a `run_id`, and an optional
validation config. Input paths must be local, must reject path traversal, must not
be public URLs, and must not trigger downloads. An optional `allowed_dataset_root`
constrains inputs to a private dataset root.

## Dataset Manifest Schema Summary

The dataset manifest must include the I1 manifest fields plus the quantitative
training gates: `dataset_id`, `schema_version`, `created_at`, `build_commit`,
`build_command_or_procedure`, `dataset_manifest_hash`, `dataset_content_hash`,
`split_seed`, `split_policy_version`, `data_source_list`, `label_source_list`,
`label_evidence_source_counts`, `label_quality_counts`, `class_prevalence_by_split`,
`storage_path_outside_git`, `artifact_class`, `filesystem_only`, `http_servable`,
`frontend_visible`, `downloadable_via_api`, `redaction_policy`, `dataset_card_ref`,
`known_limitations`, `intended_use`, `unacceptable_use`, `misuse_review_status`,
`minimum_holdout_size`, `minimum_reviewed_tier_label_count_per_class`,
`minimum_negative_background_count`, `minimum_hard_negative_count`,
`preregistered_baseline_margin`, `primary_metric`, and `threshold_selection_policy`.

## Training Example Schema Summary

Each training example must include `schema_version`, `sample_id`, `dataset_id`,
`area_id`, `group_id`, `chip_id`, `split`, `label`, `label_quality`,
`label_evidence_source`, `evidence_source_type`, `evidence_source_version`,
`evidence_review_method`, `reviewer_or_source_reference`, `acquisition_window`,
`sensor_sources`, `grid_version`, `preprocessing_commit`, `features_ref`,
`metadata_ref`, `redaction_class`, and `notes`.

## Independent Evidence Validation Summary

Label quality values are `reviewed_independent`, `reviewed_adjudicated`,
`weak_label`, `synthetic_or_proxy`, `uncertain`, and `excluded`. Only
`reviewed_independent` and `reviewed_adjudicated` count as reviewed-tier, and only
with an independent evidence source type (`field_validation`,
`authoritative_external_dataset`, `expert_adjudication_independent_evidence`, or
`independently_produced_reference`) and a nonblank `label_evidence_source`. The
`unknown_or_missing`, `weak_heuristic_hint`, and `synthetic_proxy` source types
cannot satisfy reviewed-tier evidence. Notebook and heuristic outputs alone cannot
satisfy reviewed-tier evidence. A reviewed-tier claim without independent evidence,
or zero valid reviewed-tier labels, blocks readiness.

## Split And Leakage Validation Summary

Splits must not leak by `group_id` (or `area_id` fallback) across splits. A temporal
or final holdout split must be present. Threshold selection must not use the final
holdout. Reviewed-tier label counts per positive class, holdout size, negative and
background counts, and hard-negative counts must meet the manifest minimums.

## Storage Policy Validation Summary

`artifact_class` must be `LOCAL_SENSITIVE` or `FILESYSTEM_ONLY`; `filesystem_only`
must be `true`; `http_servable`, `frontend_visible`, and `downloadable_via_api` must
be `false`; `storage_path_outside_git` must not be inside the repository root unless
it is a pytest temporary path. Public and redacted summaries must not include exact
coordinates, local paths, private hashes, or raw labels tied to locations.

## Readiness Status Behavior Summary

Allowed statuses: `ready_for_private_training_later`, `not_ready`,
`invalid_manifest`, `invalid_examples`, `independent_evidence_missing`,
`split_policy_failed`, `storage_policy_failed`, `baseline_policy_missing`,
`insufficient_holdout`, `insufficient_reviewed_tier_labels`,
`insufficient_negatives`, `insufficient_hard_negatives`, and `error`.

`dataset_readiness_status` is `ready_for_private_training_later` only when every gate
passes. `training_allowed` is `true` only in that case; otherwise it is `false`.
`inference_allowed` is always `false` in I2. If no independent evidence-backed labels
are supplied, the status is `independent_evidence_missing` (or `invalid_manifest` /
`not_ready` when the pack itself is absent), with `training_allowed=false` and
`inference_allowed=false`.

## Safety Boundary

Future Slice 08 does not:

- create or commit a real dataset, chips, labels, or coordinate-bearing metadata
- train a model or run inference
- download data or model weights, or scrape the web
- add PyTorch, TensorFlow, CUDA, or other heavy ML dependencies
- generate rasters, NPY files, or map artifacts
- call Earth Engine or start backend runs
- change raster, math, or classifier runtime logic
- connect model output to API or frontend
- expose public overlays or change artifact-serving policy
- implement H2, H3, H4, or G2 implementation work

Training stays blocked until all I2 gates pass. H2 remains required before optional
ML dependency sandboxing, and H3/H4 remain blocked until the data and evaluation
gates pass.
