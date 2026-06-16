# Future I2 assembly checklist

Status: planning only

This document defines what a future I2 dataset pack would need after actual dataset review and I1 mapping pass.

This checklist does not assemble an I2 pack.

This checklist does not create I1 rows.

This checklist does not inspect source records.

This checklist does not train or run inference.

H3 and H4 remain blocked.

## Purpose

I2 assembly is the future step that would combine approved I1-ready examples into a private dataset pack and run the existing readiness validator.

This planning checklist answers one question:

```text
What must be true before a future I2 pack can be built and validated?
```

It does not authorize:

```text
source download
source inspection
I1 creation
I2 creation
training
inference
API/frontend exposure
```

Those require separate explicit approval.

## Required prior gates

Before future I2 assembly can begin, all must be true:

- [ ] source inventory checklist passed
- [ ] actual dataset review passed
- [ ] I1 mapping checklist passed
- [ ] accepted positive examples exist
- [ ] accepted negative/background examples exist
- [ ] accepted hard-negative examples exist
- [ ] storage location is outside Git
- [ ] operator explicitly approves I2 assembly

Current status:

```text
I2 assembly is not authorized yet.
```

## Planned source pools

Positive pool:

- POS-01

Negative/background pool:

- C05

Hard-negative pool:

- C06
- C07

Rules:

- POS-01 may only contribute positive examples after actual dataset review and I1 mapping pass.
- C05 may only contribute negative/background examples after actual dataset review and I1 mapping pass.
- C06 and C07 may only contribute hard-negative examples after actual dataset review and I1 mapping pass.
- No source may skip actual dataset review.
- No source may skip I1 mapping review.

## I2 pack required components

A future I2 pack must include:

```text
dataset_manifest.json
training_examples.jsonl
source_inventory_summary.json
review_summary.json
split_policy.json
dataset_card.md or internal equivalent
```

All real dataset contents must remain outside Git.

Repo-visible docs may contain only safe summaries.

## Dataset manifest requirements

The manifest must include all required I1 manifest fields plus the I2 quantitative readiness fields.

Required quantitative fields:

```text
minimum_holdout_size
minimum_reviewed_tier_label_count_per_class
minimum_negative_background_count
minimum_hard_negative_count
preregistered_baseline_margin
primary_metric
threshold_selection_policy
```

Manifest storage fields must show:

```text
artifact_class: LOCAL_SENSITIVE or FILESYSTEM_ONLY
filesystem_only: true
http_servable: false
frontend_visible: false
downloadable_via_api: false
storage_path_outside_git: present and outside repo
```

## Training examples requirements

The future training examples file must be JSONL.

Each row must satisfy the I1 mapping checklist.

Each row must include the required training-example fields, including:

```text
sample_id
area_id
group_id
split
label
label_quality
label_evidence_source
evidence_source_type
evidence_source_version
evidence_review_method
```

Rules:

- Reviewed-tier rows must have independent evidence.
- Weak labels alone are not enough.
- Excluded rows must not enter training.
- Source lineage must be retained outside Git.

## Split policy requirements

The future I2 pack must prevent leakage.

Checklist:

- [ ] no sample appears in more than one split
- [ ] group_id does not leak across splits
- [ ] near-duplicate areas share a group_id
- [ ] final holdout exists
- [ ] temporal holdout exists or is explicitly documented
- [ ] threshold selection does not use final holdout
- [ ] split seed or deterministic split rule is recorded

Allowed split names:

```text
train
validation
test
final_holdout
temporal_holdout
holdout
```

## Source balance requirements

The future I2 pack must include:

- [ ] enough positive reviewed-tier examples per class
- [ ] enough negative/background examples
- [ ] enough hard-negative examples
- [ ] class prevalence by split
- [ ] counts by label quality
- [ ] counts by evidence source type
- [ ] counts by split

The exact minimum counts must be set in the manifest before validation.

## Baseline and metric requirements

The future I2 manifest must include:

```text
primary_metric
preregistered_baseline_margin
threshold_selection_policy
```

Rules:

- The primary metric must be chosen before training.
- The baseline margin must be numeric.
- Threshold selection must not use final holdout.
- H3 training cannot start unless the readiness validator passes first.

## Validator command planning

The existing readiness validator is:

```text
app/pipeline/parity/dataset_pack_readiness.py::evaluate_dataset_pack_readiness
```

Future validator inputs:

```text
dataset_manifest_path
training_examples_path
run_dir
run_id
allowed_dataset_root
```

Expected successful status:

```text
ready_for_private_training_later
```

Expected successful flags:

```text
training_allowed: true
inference_allowed: false
```

Important:

A successful I2 readiness result still does not authorize H4 inference.

H4 requires a later approved H3 model and private inference gate.

## Readiness blocker categories

The future I2 pack must be prepared to resolve these blocker families:

```text
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
```

## I2 assembly decision values

Allowed planning decisions:

```text
i2_planning_ready
i2_planning_ready_with_open_items
i2_not_authorized
i2_blocked_by_source_review
i2_blocked_by_i1_mapping
i2_blocked_by_storage
i2_blocked_by_validator_requirements
```

Current decision:

```text
i2_not_authorized
```

## Stop conditions

Stop immediately if the work requires:

```text
downloading source data
opening source records
creating real training examples
creating chips or masks
writing an I2 pack
running the readiness validator on real data
training
inference
changing app/API/frontend code
```

Those require separate explicit approval.

## Result of this checklist

This checklist completes FUTURE-I2-PLAN-4.

Next planning item:

```text
FUTURE-I2-PLAN-5: Review existing dataset_pack_readiness validator.
```
