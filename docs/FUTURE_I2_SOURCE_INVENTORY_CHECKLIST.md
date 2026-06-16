# Future I2 source inventory checklist

Status: planning only

This document defines what must be recorded for each future I2 source before any dataset payload is opened, inspected, transformed, or used.

No source data is downloaded by this checklist.

No source records are inspected by this checklist.

No I1 rows or I2 packs are created by this checklist.

H3 and H4 remain blocked.

## Purpose

The source inventory is the first planning gate before future I2 assembly.

It answers one question:

```text
Do we know enough about this source to later review it safely?
```

It does not answer:

```text
Is the actual dataset usable?
Is the dataset I1-ready?
Is the dataset I2-ready?
Can H3 training start?
```

Those require later steps.

## Current approved planning candidates

Positive candidate:

- POS-01

Negative/background candidate:

- C05

Hard-negative candidates:

- C06
- C07

These are source candidates only.

Actual dataset review has not started.

## Inventory record fields

Each future source must have one source inventory record.

Required fields:

```text
source_id
source_name
source_role
source_status
owner_or_authority
source_reference
license_status
private_training_permission
allowed_derivative_outputs
sensitivity_decision
redaction_requirement
storage_location_class
expected_content_type
expected_schema_notes
label_evidence_type
independence_basis
intended_neutral_label_mapping
do_not_use_conditions
operator_approval_required
next_review_step
```

## Allowed source roles

Allowed values:

```text
positive
negative_background
hard_negative
context_only
rejected
under_review
```

Rules:

- A positive source may support future target-positive examples only after actual dataset review passes.
- A negative/background source may support later background examples only.
- A hard-negative source may support later false-positive suppression only.
- A context-only source must not become a training label source.
- A rejected source must not be used.
- An under-review source must not be used until the open blocker is resolved.

## Allowed source statuses

Allowed values:

```text
metadata_reviewed_candidate
conditionally_approved_for_future_review
under_review
blocked
rejected
retired
```

No status means H3 or H4 can start.

## License and permission fields

Each source must record:

```text
license_status
private_training_permission
allowed_derivative_outputs
permission_notes
```

Allowed values for `private_training_permission`:

```text
yes
no
unknown
not_applicable
```

Rules:

- `unknown` blocks later I2 assembly.
- `no` blocks later I2 assembly.
- `yes` still requires actual dataset review.

## Sensitivity and redaction fields

Each source must record:

```text
sensitivity_decision
redaction_requirement
storage_location_class
```

Allowed values for `sensitivity_decision`:

```text
pass
pass_with_redaction
needs_review
blocked
```

Allowed values for `storage_location_class`:

```text
repo_visible_metadata_only
operator_private_storage
not_allowed
```

Rules:

- Actual source payloads must not be repo-visible.
- Location-bearing or sensitive source contents must remain in operator-private storage.
- A source with `blocked` sensitivity cannot be used.

## Evidence and independence fields

Each source must record:

```text
label_evidence_type
independence_basis
```

Allowed evidence types:

```text
authoritative_external
expert_adjudicated
field_verified
independently_produced_reference
negative_reference
hard_negative_reference
context_only
```

Rejected evidence types:

```text
app_output
candidate_zone
classifier_score
same_project_layer
same_signal_guess
```

Rules:

- App outputs are not labels.
- Candidate zones are not labels.
- Classifier scores are not labels.
- Negative sources are not positive sources.

## Neutral label mapping field

Each source must record the intended neutral mapping.

Allowed neutral label families:

```text
Class_A
Background
Hard_Negative
Ignore
Uncertain
```

Rules:

- Source-specific names must not be used directly as model labels in repo-visible files.
- `Ignore` and `Uncertain` are excluded from training by default.
- Final label mapping is not accepted until actual dataset review passes.

## Do-not-use conditions

Each source must explicitly list conditions that would block future use.

Examples:

```text
license conflict
private training not allowed
sensitive fields cannot be redacted
actual records do not match metadata
labels do not match target definition
schema cannot map to I1
quality is too low
source provenance cannot be confirmed
```

## Source inventory acceptance rule

A source inventory record is complete only when all required fields are filled and no required value is `unknown` unless the source status is `under_review` or `blocked`.

A complete inventory record does not authorize I2 assembly.

It only authorizes later actual dataset review.

## Current source inventory planning table

| Source | Role | Planning status | Next review |
| --- | --- | --- | --- |
| POS-01 | positive | conditionally approved for future review | actual dataset review later |
| C05 | negative/background | conditionally approved for future review | actual dataset review later |
| C06 | hard-negative | conditionally approved for future review | actual dataset review later |
| C07 | hard-negative | conditionally approved for future review | actual dataset review later |

## Stop conditions

Stop immediately if the work requires:

```text
downloading source data
opening source records
collecting coordinates
copying labels
creating chips
creating masks
creating I1 rows
assembling an I2 pack
running training
running inference
changing app/API/frontend code
```

Those require separate explicit approval.

## Result of this checklist

This checklist completes FUTURE-I2-PLAN-1.

Next planning item:

```text
FUTURE-I2-PLAN-2: Create actual dataset review checklist.
```
