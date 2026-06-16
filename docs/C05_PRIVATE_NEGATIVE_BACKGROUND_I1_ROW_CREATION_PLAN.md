# C05 private negative/background I1 row creation plan

Status: planning only

This document defines how a later approved step would create private I1 negative/background rows from C05.

No source data is downloaded by this document.

No real I1 rows are created by this document.

No I2 pack is assembled.

No validator is run on real data.

No training or inference is started.

## Source

C05:

```text
ESA WorldCover negative/background candidate
```

Approved planning role:

```text
negative_background
```

C05 is not a positive source.

C05 must not create target-positive labels.

## Purpose

POS-01 now provides the private positive I1 row pool.

C05 is needed to plan the negative/background side of a future I2 dataset.

This plan answers:

```text
If negative/background I1 row creation is approved later, what rules must C05 follow?
```

It does not approve real row creation.

## Planned private output location

A later approved step may write private C05 I1 rows only outside Git.

Recommended private root:

```text
C:\Dev\New_GEE_PRIVATE\I1_C05
```

Recommended private files:

```text
training_examples.c05.private.jsonl
training_examples.c05.private.summary.json
source_lineage.c05.private.json
exclusions.c05.private.summary.json
```

Rules:

- files stay outside the repository
- files are not committed
- repo-visible docs may record aggregate counts only
- source lineage stays private or metadata-only as appropriate

## Planned neutral mapping

For accepted C05 records, the planned mapping is:

| Field family | Planned value |
| --- | --- |
| source role | negative_background |
| neutral label | Class_Background |
| label quality | reviewed_independent or independently_produced_reference-derived, only if supported by source review |
| evidence type | authoritative_external_dataset |
| redaction class | LOCAL_SENSITIVE or FILESYSTEM_ONLY |
| split | unassigned initially |

The label may also be configured later as `Class_Negative` if the validator configuration uses that naming.

Important:

```text
C05 negative/background records are not proof of target absence everywhere.
They are controlled background examples for training balance and false-positive control.
```

## Required future source review before writing rows

Before real C05 I1 rows may be created, a future private review must confirm:

- [ ] exact C05 source version
- [ ] license and attribution requirements
- [ ] private training use remains allowed
- [ ] intended background classes are selected
- [ ] sampling method is documented
- [ ] records or samples can be kept outside Git
- [ ] no sensitive repo-visible values are produced
- [ ] source can map to I1 required fields

## Sampling policy

C05 row creation must use a controlled sampling policy.

The policy must define:

- [ ] sampling region or area family
- [ ] background class family
- [ ] sample count target
- [ ] minimum distance or separation from positive examples if applicable
- [ ] split grouping rule
- [ ] exclusion rules
- [ ] deterministic seed

C05 must not produce unlimited background rows.

C05 must not dominate the positive source in a way that breaks class balance.

## Required I1 fields

A later C05 private row creation step must populate every required I1 training-example field:

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

C05 may provide background source evidence or sampling strata.

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

A later real C05 I1 row creation step passes only if:

- [ ] accepted rows use neutral background label
- [ ] no C05 row uses target-positive label
- [ ] every emitted row has all required I1 fields
- [ ] every emitted row has source lineage
- [ ] all output stays outside Git
- [ ] repo-visible result contains aggregate counts only
- [ ] sampling policy is documented
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
c05_private_negative_background_i1_row_creation_plan_ready
```

## Current final status

C05 private negative/background I1 row creation plan is ready.

Real C05 I1 rows are not created.

C06 and C07 hard-negative rows are not created.

I2 assembly is not started.

H3 remains blocked.

H4 remains blocked.
