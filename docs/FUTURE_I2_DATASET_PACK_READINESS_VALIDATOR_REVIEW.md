# Future I2 dataset_pack_readiness validator review

Status: planning only

This document reviews the existing dataset-pack readiness validator for future I2 planning.

No validator code is changed by this review.

No dataset pack is created.

No real manifest or training examples are produced.

No training or inference is started.

H3 and H4 remain blocked.

## Validator under review

```text
app/pipeline/parity/dataset_pack_readiness.py::evaluate_dataset_pack_readiness
```

Purpose:

```text
Validate a future private I2 dataset pack and report whether it is ready for later private training consideration.
```

The validator is validation-only. It does not create a dataset, train, run inference, download data or weights, add ML dependencies, call Earth Engine, or expose anything publicly.

## Required inputs

The validator expects:

```text
dataset_manifest_path
training_examples_path
run_dir
run_id
allowed_dataset_root
validation_config
report_relative_path
```

Planning meaning:

- `dataset_manifest_path` points to the future I2 dataset manifest.
- `training_examples_path` points to the future I1/I2 training examples JSONL file.
- `run_dir` is where the private readiness report is written.
- `run_id` identifies the validation run.
- `allowed_dataset_root` restricts input paths to a private allowed root.
- `validation_config` can override negative and hard-negative label names.

## Required manifest fields

The I2 manifest must include all I1 dataset manifest fields plus the I2 quantitative fields.

I2 quantitative fields:

```text
minimum_holdout_size
minimum_reviewed_tier_label_count_per_class
minimum_negative_background_count
minimum_hard_negative_count
preregistered_baseline_margin
primary_metric
threshold_selection_policy
```

The validator rejects a manifest when required fields are missing.

## Required training example fields

The validator requires each training-example row to contain the training example fields defined in the I1 design module.

Core fields include:

```text
schema_version
sample_id
dataset_id
area_id
group_id
chip_id
split
label
label_quality
label_evidence_source
evidence_source_type
evidence_source_version
evidence_review_method
reviewer_or_source_reference
acquisition_window
sensor_sources
grid_version
preprocessing_commit
features_ref
metadata_ref
redaction_class
notes
```

Each row must be a JSON object.

The file must be JSONL.

The examples file must not be empty.

## Label and evidence gates

The validator uses the existing I1 label and evidence constants.

Reviewed-tier label qualities:

```text
reviewed_independent
reviewed_adjudicated
```

Allowed evidence source types include:

```text
field_validation
authoritative_external_dataset
expert_adjudication_independent_evidence
independently_produced_reference
weak_heuristic_hint
synthetic_proxy
unknown_or_missing
```

Only independent evidence source types pass the reviewed-tier gate:

```text
field_validation
authoritative_external_dataset
expert_adjudication_independent_evidence
independently_produced_reference
```

A reviewed-tier label must include a non-empty `label_evidence_source`.

If no reviewed-tier labels with independent evidence exist, readiness fails.

## Storage policy gate

The validator requires:

```text
artifact_class: LOCAL_SENSITIVE or FILESYSTEM_ONLY
filesystem_only: true
http_servable: false
frontend_visible: false
downloadable_via_api: false
storage_path_outside_git: outside repo or pytest tmp
```

This matches the private-only dataset policy.

## Split policy gate

The validator checks:

- `group_id` or `area_id` does not leak across splits.
- a holdout split exists.
- threshold selection does not use final holdout.

Recognized holdout split names:

```text
final_holdout
temporal_holdout
holdout
```

## Count gates

The validator checks:

```text
minimum_reviewed_tier_label_count_per_class
minimum_holdout_size
minimum_negative_background_count
minimum_hard_negative_count
```

Failure statuses include:

```text
insufficient_reviewed_tier_labels
insufficient_holdout
insufficient_negatives
insufficient_hard_negatives
```

## Baseline policy gate

The validator requires `preregistered_baseline_margin` to be numeric.

If missing or non-numeric, readiness fails with:

```text
baseline_policy_missing
```

## Output report

The validator writes a private readiness report under the run directory.

The output includes:

```text
dataset_readiness_status
training_allowed
inference_allowed
independent_evidence_status
reviewed_tier_label_count_status
split_policy_status
temporal_holdout_status
negative_sampling_status
hard_negative_status
holdout_size_status
baseline_margin_status
storage_policy_status
manifest_hash_status
content_hash_status
counts_by_label_quality
counts_by_evidence_source_type
counts_by_split
class_prevalence_by_split
blockers
next_actions
```

## Success condition

The only status that allows future private training consideration is:

```text
ready_for_private_training_later
```

When this status is reached:

```text
training_allowed: true
inference_allowed: false
```

Important:

`inference_allowed` remains false.

H4 still requires a later approved H3 model and private inference gate.

## Readiness statuses

Allowed readiness statuses:

```text
ready_for_private_training_later
not_ready
invalid_manifest
invalid_examples
independent_evidence_missing
split_policy_failed
storage_policy_failed
baseline_policy_missing
insufficient_holdout
insufficient_reviewed_tier_labels
insufficient_negatives
insufficient_hard_negatives
error
```

## Planning conclusion

The existing validator is suitable for future I2 readiness planning.

No new validator is needed now.

No validator code change is needed now.

Future I2 assembly must produce inputs that satisfy this validator.

## Open planning notes

Before real I2 assembly, decide:

- exact neutral label names to pass through validator config
- minimum holdout size
- minimum reviewed-tier label count per class
- minimum negative/background count
- minimum hard-negative count
- primary metric
- preregistered baseline margin
- threshold selection policy
- allowed private dataset root

## Stop conditions

Stop immediately if this work requires:

```text
creating a real dataset manifest
creating real training examples
running the validator on real data
opening source records
assembling I2
training
inference
changing validator code
```

Those require separate explicit approval.

## Result of this review

This checklist completes FUTURE-I2-PLAN-5.

Next planning item:

```text
FUTURE-I2-PLAN-6: Tighten acceptance criteria.
```
