# Future I2 I1 mapping checklist

Status: planning only

This document defines how records that pass actual dataset review would later be mapped into I1 training-example rows.

This checklist does not create I1 rows.

This checklist does not inspect source records.

This checklist does not assemble an I2 pack.

H3 and H4 remain blocked.

## Purpose

I1 mapping is the planning step between actual dataset review and future I2 pack assembly.

It answers one question:

```text
If a source record is accepted later, what fields must exist before it can become a training-example row?
```

It does not answer:

```text
Is the source dataset usable?
Is I2 assembled?
Can H3 training start?
Can H4 inference start?
```

Those require later review and validation.

## Required source status before I1 mapping

A source may enter I1 mapping planning only after:

- [ ] source inventory exists
- [ ] actual dataset review passed
- [ ] actual dataset review did not block on permission
- [ ] actual dataset review did not block on sensitivity
- [ ] actual dataset review did not block on schema
- [ ] actual dataset review did not block on label quality

Current status:

```text
No source has entered actual I1 mapping.
```

## Required I1 row fields

Every future I1 training-example row must include:

```text
schema_version
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
source_role
source_id
source_record_reference
source_record_version
review_status
do_not_train
privacy_class
artifact_class
notes
```

Feature fields are not defined by this checklist.

Feature fields are selected later only after I1 source mapping and I2 assembly planning are accepted.

## Label field rules

Allowed neutral labels:

```text
Class_A
Background
Hard_Negative
Ignore
Uncertain
```

Rules:

- POS-01 accepted positive records may map to `Class_A` only after actual dataset review passes.
- C05 accepted negative/background records may map to `Background` only after actual dataset review passes.
- C06 and C07 accepted hard-negative records may map to `Hard_Negative` only after actual dataset review passes.
- Records with unclear meaning map to `Uncertain`.
- Records excluded from training map to `Ignore` or set `do_not_train=true`.
- Source-specific names must not become repo-visible model labels.

## Label quality rules

Allowed values:

```text
reviewed_independent
reviewed_adjudicated
weak_label
synthetic_or_proxy
uncertain
excluded
```

Rules:

- H3 training cannot start from weak labels alone.
- Reviewed-tier labels require independent evidence.
- `weak_label`, `synthetic_or_proxy`, `uncertain`, and `excluded` are not sufficient for H3 training readiness.
- `excluded` must set `do_not_train=true`.

## Evidence fields

Every reviewed-tier I1 row must include:

```text
label_evidence_source
evidence_source_type
evidence_source_version
evidence_review_method
```

Allowed `evidence_source_type` values:

```text
authoritative_external_dataset
expert_adjudication_independent
field_verified
independently_produced_reference
negative_reference
hard_negative_reference
```

Rejected evidence source types:

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
- Same-project layers are not independent evidence.
- Human agreement with app output is not enough unless independent evidence is also recorded.

## Source role mapping

Allowed source roles:

```text
positive
negative_background
hard_negative
context_only
```

Current planned source roles:

| Source | Role | Allowed future label family |
| --- | --- | --- |
| POS-01 | positive | Class_A |
| C05 | negative_background | Background |
| C06 | hard_negative | Hard_Negative |
| C07 | hard_negative | Hard_Negative |

Rules:

- Context-only sources must not create training labels.
- Negative sources must not create positive labels.
- Hard-negative sources must not create positive labels.
- Positive sources must not bypass sensitivity and quality review.

## Split fields

Every future I1 row must include:

```text
area_id
group_id
split
```

Allowed split values:

```text
train
validation
test
holdout_private
unassigned
```

Rules:

- No `sample_id` may appear in more than one split.
- No `group_id` may leak across train, validation, test, and holdout.
- Similar or near-duplicate areas must share the same `group_id`.
- `holdout_private` must not be used for training.
- `unassigned` rows are not training-ready.

## Privacy and storage fields

Every future I1 row must include:

```text
privacy_class
artifact_class
do_not_train
```

Allowed `privacy_class` values:

```text
repo_visible_metadata_only
operator_private
local_sensitive
```

Allowed `artifact_class` values:

```text
LOCAL_SENSITIVE
FILESYSTEM_ONLY
METADATA_ONLY
```

Rules:

- Real training examples must remain outside Git.
- Location-bearing metadata must remain outside Git.
- Repo-visible summaries may contain only aggregate status and safe field names.
- Any row that cannot be stored safely must set `do_not_train=true` or be excluded.

## Do-not-train conditions

Set `do_not_train=true` if any of these apply:

```text
permission unclear
license unclear
source record sensitivity unresolved
label meaning unclear
independent evidence missing
source provenance unclear
schema incomplete
record duplicate unresolved
neutral mapping unavailable
split leakage risk unresolved
operator exclusion required
```

Rows with `do_not_train=true` must not enter H3 training.

## I1 mapping decision values

Allowed source-level I1 mapping decisions:

```text
i1_mapping_ready
i1_mapping_ready_with_exclusions
needs_operator_info
blocked_by_schema
blocked_by_label_quality
blocked_by_independence
blocked_by_sensitivity
blocked_by_permission
rejected
```

Rules:

- `i1_mapping_ready` allows later I2 assembly planning.
- `i1_mapping_ready_with_exclusions` allows later I2 assembly planning only for accepted rows.
- Any blocked/rejected decision stops the source from entering I2 assembly.

## Required repo-visible I1 mapping summary

Allowed summary fields:

- source_id
- source role
- mapping decision
- neutral label families used
- aggregate accepted count
- aggregate excluded count
- blocker names
- next step

Forbidden repo-visible fields:

- raw records
- coordinates
- site names
- sensitive source identifiers
- source payload rows
- private paths
- private hashes
- exact location-bearing row examples

## Stop conditions

Stop immediately if mapping requires:

```text
opening unapproved source records
copying records into Git
creating real I1 rows
creating chips or masks
assembling I2
running training
running inference
changing app/API/frontend code
```

Those require separate explicit approval.

## Result of this checklist

This checklist completes FUTURE-I2-PLAN-3.

Next planning item:

```text
FUTURE-I2-PLAN-4: Create I2 assembly checklist.
```
