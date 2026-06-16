# POS-01 private I1 row creation plan

Status: planning only

This document defines how a later approved step would create private I1 rows from POS-01.

No real I1 rows are created by this document.

No source records are copied into Git.

No I2 pack is assembled.

No validator is run on real data.

No training or inference is started.

## Starting point

POS-01 actual dataset review passed with exclusions.

POS-01 I1 mapping dry-run aggregate check passed with exclusions.

Aggregate counts:

| Metric | Count |
| --- | ---: |
| Accepted records total | 233 |
| I1 candidate records | 217 |
| Held back records | 16 |
| Real I1 rows created | 0 |

## Purpose

This plan answers:

```text
If real I1 row creation is approved later, where would the private output go and what rules must it follow?
```

It does not approve real row creation.

## Private output location

A later approved step may write private I1 rows only outside Git.

Recommended private root:

```text
C:\Dev\New_GEE_PRIVATE\I1_POS01
```

Recommended files:

```text
training_examples.pos01.private.jsonl
training_examples.pos01.private.summary.json
source_lineage.pos01.private.json
exclusions.pos01.private.summary.json
```

Rules:

- files stay outside the repository
- files are not committed
- repo-visible docs may record aggregate counts only
- real source lineage stays private

## Candidate pool rule

Only the 217 complete candidate records may be used for later private I1 row creation.

The 16 held-back records must not enter automatically.

Held-back records require a separate operator review or exclusion decision.

## Planned neutral mapping

For the 217 candidate records, the planned mapping is:

| Field family | Planned value |
| --- | --- |
| source role | positive |
| neutral label | Class_A |
| label quality | reviewed_independent |
| evidence type | authoritative_external_dataset |
| redaction class | LOCAL_SENSITIVE or FILESYSTEM_ONLY |
| split | unassigned initially |

The initial split must remain `unassigned` until a later split-policy step assigns train/validation/test/holdout safely.

## Private generated identifiers

A later approved local script must generate private stable identifiers for:

```text
sample_id
area_id
group_id
chip_id
```

Rules:

- identifiers must not be source names
- identifiers must not expose private source values
- identifiers must be stable across repeated local builds
- identifiers must support leakage-safe grouping
- `chip_id` may remain a placeholder until approved feature/chip generation exists

## Required I1 fields

A later private row creation step must populate every required I1 training-example field:

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

Rows missing any required field must be excluded from the private output or written only to a private rejection summary.

## Evidence lineage rule

Every reviewed-tier row must have a non-empty private evidence reference.

Repo-visible docs may describe the evidence family only.

The private output must retain enough source lineage for audit and reproducibility.

## Feature reference rule

POS-01 provides label/evidence candidates, not app feature tensors.

Therefore:

```text
features_ref
metadata_ref
acquisition_window
sensor_sources
grid_version
preprocessing_commit
```

must remain pending or reference later approved app-controlled feature artifacts.

Real H3 training cannot start until feature references and split policy are complete.

## Row creation acceptance criteria

A later real I1 row creation step passes only if:

- [ ] exactly 217 candidate rows are considered
- [ ] 16 held-back records are excluded or separately flagged
- [ ] every emitted row has all required I1 fields
- [ ] every emitted row uses neutral label Class_A
- [ ] every reviewed-tier row has private evidence lineage
- [ ] all output stays outside Git
- [ ] repo-visible result contains aggregate counts only
- [ ] no I2 pack is assembled by the row-creation step

## Allowed aggregate report after real row creation

Repo-visible reporting may include only:

```text
rows_created_count
rows_excluded_count
held_back_count
label_family_counts
label_quality_counts
evidence_type_counts
split_counts
missing_required_field_counts
private_output_exists_true_false
```

## Not allowed in repo-visible output

Do not record:

```text
raw source rows
private identifiers
source-specific row values
private output paths beyond approved folder family
training example JSONL contents
```

## Stop conditions

Stop immediately if the step requires:

```text
committing private I1 files
assembling I2
running validator on real data
training
inference
app/API/frontend changes
```

Those require separate explicit approval.

## Current decision

```text
pos01_private_i1_row_creation_plan_ready
```

## Current final status

POS-01 private I1 row creation plan is ready.

Real I1 rows are not created.

I2 assembly is not started.

H3 remains blocked.

H4 remains blocked.
