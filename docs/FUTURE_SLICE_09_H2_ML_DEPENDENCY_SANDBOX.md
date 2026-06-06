# Future Slice 09 / H2 Optional ML Dependency Sandbox

## Scope

Future Slice 09 (H2) adds an optional ML dependency sandbox policy and a checker
that defines how future ML dependencies may be isolated from the base app. Because
no real dataset pack is committed and no real independent-evidence dataset is known
ready, this slice is sandbox readiness / policy only.

H2 is sandbox readiness/policy only. It does not add PyTorch, TensorFlow, CUDA, or
heavy ML dependencies. It does not train. It does not run inference. It does not
download weights. It does not create datasets. It does not change API, frontend, or
artifact-serving behavior. The base app must remain free of required ML packages.
Optional ML dependency groups are allowed only in a later approved slice after the
I2 dataset readiness gate passes. H3 training and H4 private inference remain
blocked.

The binding gates are in `docs/ML_DATA_TRAINING_READINESS_PLAN.md`, with the dataset
readiness gate from `docs/FUTURE_SLICE_08_I2_PRIVATE_DATASET_PACK_READINESS.md` and
the revisited ranking in `docs/FUTURE_SLICE_07_H1_REVISIT_AFTER_I1_J1.md`. Where
wording differs, the strictest gate applies.

## Source Of Truth

The sandbox helper is:

```text
app/pipeline/parity/ml_dependency_sandbox.py
```

It writes one private JSON report:

```text
data/runs/<run_id>/manifests/future_slice_09_h2_ml_dependency_sandbox.json
```

The report path stays under `run_dir`. The helper does not create datasets, model
weights, models, rasters, NPY files, map artifacts, labels, chips, or training
outputs. It does not import any ML package.

## Sandbox Policy Summary

`get_h2_sandbox_rules()` returns the policy:

- the base app must remain ML-free
- optional ML dependencies may be added only in a later approved slice, as an
  optional extra group named `optional_extra`
- optional ML dependencies must not be imported at app startup
- optional ML code must be CLI/private first
- training requires a ready I2 dataset pack
  (`ready_for_private_training_later`)
- inference requires a trained/evaluated model or approved-weight validation
- weight downloads require a source, license, sha256, and model card policy
- training, inference, and weight downloads all remain blocked inside H2; H3
  training and H4 private inference remain blocked

## Checker Behavior And Status Rules

`check_ml_dependency_sandbox(proposed_sandbox, dataset_readiness_status=...)`
returns one status and a blocker list. Structural gates apply to every intent and
take precedence:

- a proposal that changes base dependencies, marks itself as a required base
  dependency, or uses a non-optional dependency group is rejected with
  `blocked_base_dependency_change`
- a proposal that imports at app startup is rejected with `blocked_eager_import`
- a proposal that adds an API or frontend dependency on ML packages is rejected with
  `blocked_api_frontend_dependency`

Intent-specific gates:

- `weights_download` without a complete weights policy is rejected with
  `blocked_missing_weights_policy`; with a complete policy it is recorded as
  `allowed_later_optional_extra`, meaning a later approved slice may pursue it
- `training` without a ready I2 dataset is rejected with `blocked_no_ready_dataset`;
  with a ready dataset it is still `blocked_training_gate` because training is a
  later H3 slice
- `inference` is rejected with `blocked_inference_gate`
- `optional_extra_dependency` that clears the structural gates is recorded as
  `allowed_later_optional_extra`
- `design_only` (or no proposal) is recorded as `sandbox_design_only`

Allowed statuses: `sandbox_design_only`, `allowed_later_optional_extra`,
`blocked_no_ready_dataset`, `blocked_base_dependency_change`,
`blocked_api_frontend_dependency`, `blocked_eager_import`,
`blocked_missing_weights_policy`, `blocked_training_gate`, `blocked_inference_gate`.

`allowed_later_optional_extra` records that a later approved slice may proceed; it
does not add any dependency, training, inference, or weight download now.

## Safety Boundary

Future Slice 09 does not:

- add PyTorch, TensorFlow, CUDA, or other heavy ML dependencies
- add required ML dependencies to the base app
- modify requirements or pyproject dependency lists
- train a model or run inference
- download or commit model weights
- create datasets, chips, or labels
- generate rasters, NPY files, or map artifacts
- call Earth Engine or start backend runs
- change raster, math, or classifier runtime logic
- connect ML output to API or frontend
- expose model output publicly or change artifact-serving policy
- implement H3, H4, or G2 implementation work

The base app stays free of required ML packages. An optional ML dependency group is
permissible only in a later approved slice once the I2 dataset readiness gate
passes. H3 training and H4 private inference remain blocked.
