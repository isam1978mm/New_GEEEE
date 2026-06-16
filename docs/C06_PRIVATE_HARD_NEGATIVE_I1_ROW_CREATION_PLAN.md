# C06 private hard-negative I1 row creation plan

Status: planning only

This document defines how a later approved step would create private I1 hard-negative rows from C06.

No source data is downloaded by this document.

No real I1 rows are created by this document.

No I2 pack is assembled.

No validator is run on real data.

No training or inference is started.

## Source

C06:

```text
Dynamic World hard-negative candidate
```

Approved planning role:

```text
hard_negative
```

C06 is not a positive source.

C06 must not create target-positive labels.

## Purpose

POS-01 provides the private positive I1 row pool.

C05 is planned for negative/background rows.

C06 is planned for hard-negative examples that help suppress false positives.

This plan answers:

```text
If hard-negative I1 row creation is approved later, what rules must C06 follow?
```

It does not approve real row creation.

## Planned private output location

A later approved step may write private C06 I1 rows only outside Git.

Recommended private root:

```text
C:\Dev\New_GEE_PRIVATE\I1_C06
```

Recommended private files:

```text
training_examples.c06.private.jsonl
training_examples.c06.private.summary.json
source_lineage.c06.private.json
exclusions.c06.private.summary.json
```

Rules:

- files stay outside the repository
- files are not committed
- repo-visible docs may record aggregate counts only
- source lineage stays private or metadata-only as appropriate

## Planned neutral mapping

For accepted C06 records, the planned mapping is:

| Field family | Planned value |
| --- | --- |
| source role | hard_negative |
| neutral label | Class_HardNegative |
| label quality | reviewed_independent or independently_produced_reference-derived, only if supported by source review |
| evidence type | authoritative_external_dataset |
| redaction class | LOCAL_SENSITIVE or FILESYSTEM_ONLY |
| split | unassigned initially |

Important:

```text
C06 hard-negative records are confusing non-target examples.
They are not target-positive evidence.
```

## Required future source review before writing rows

Before real C06 I1 rows may be created, a future private review must confirm:

- [ ] exact C06 source version
- [ ] license and attribution requirements
- [ ] private training use remains allowed
- [ ] selected hard-negative class families are documented
- [ ] sampling method is documented
- [ ] samples can remain outside Git
- [ ] no sensitive repo-visible values are produced
- [ ] source can map to I1 required fields

## Hard-negative sampling policy

C06 row creation must use a controlled hard-negative sampling policy.

The policy must define:

- [ ] hard-negative class family
- [ ] source version
- [ ] sample count target
- [ ] deterministic seed
- [ ] grouping rule
- [ ] split-holdout rule
- [ ] exclusion rules
- [ ] relationship to POS-01 positive areas if applicable

C06 must not produce unlimited hard negatives.

C06 must not be treated as positive evidence.

## Required I1 fields

A later C06 private row creation step must populate every required I1 training-example field:

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

Rows missing any required field must be excluded or held back.

## Feature reference rule

C06 may provide hard-negative source evidence or sampling strata.

It does not by itself create app feature artifacts.

Therefore these fields remain pending until later approved feature generation:

```text
features_ref
metadata_ref
acquisition_window
sensor_sources
grid_version
preprocessing_commit
```

## Row creation acceptance criteria

A later real C06 I1 row creation step passes only if:

- [ ] accepted rows use neutral hard-negative label
- [ ] no C06 row uses target-positive label
- [ ] every emitted row has all required I1 fields
- [ ] every emitted row has source lineage
- [ ] all output stays outside Git
- [ ] repo-visible result contains aggregate counts only
- [ ] hard-negative sampling policy is documented
- [ ] no I2 pack is assembled by the row-creation step

## Allowed aggregate report after real row creation

Repo-visible reporting may include only:

```text
rows_created_count
rows_excluded_count
label_family_counts
label_quality_counts
evidence_type_counts
split_counts
missing_required_field_counts
private_output_exists_true_false
```

## Stop conditions

Stop immediately if the step requires:

```text
committing private I1 files
publishing source records
assembling I2
running validator on real data
training
inference
app/API/frontend changes
```

Those require separate explicit approval.

## Current decision

```text
c06_private_hard_negative_i1_row_creation_plan_ready
```

## Current final status

C06 private hard-negative I1 row creation plan is ready.

Real C06 I1 rows are not created.

C07 hard-negative row plan is not created.

I2 assembly is not started.

H3 remains blocked.

H4 remains blocked.
