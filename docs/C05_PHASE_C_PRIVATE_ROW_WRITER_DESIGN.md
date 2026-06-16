# C05 Phase C private row writer design

Status: writer design ready

This document defines the design for a later C05 private negative/background I1 row writer.

No source data is downloaded by this document.

No source records are inspected by this document.

No real I1 rows are created by this document.

No script is added by this document.

No I2 pack is assembled.

No validator is run on real data.

No training or inference is started.

## Source

C05 source/version:

```text
ESA WorldCover 10m, operator-selected local version
```

Planned role:

```text
negative_background
```

Allowed background class family:

```text
non-target background only
```

Target row count:

```text
217
```

Sampling seed:

```text
20260616
```

Private output folder family:

```text
C:\Dev\New_GEE_PRIVATE\I1_C05
```

## Purpose

The future C05 row writer should create private negative/background I1 rows outside Git, matching the sampling policy defined in Phase B.

The writer must default to dry-run mode.

A write must require an explicit `--write` flag.

## Proposed script name

```text
scripts/c05_write_private_i1_rows.py
```

## Required behavior

Default command:

```text
python scripts/c05_write_private_i1_rows.py
```

Expected behavior:

```text
dry-run only
write zero private rows
print aggregate JSON summary
```

Write command, only after explicit approval:

```text
python scripts/c05_write_private_i1_rows.py --write
```

Expected behavior:

```text
write private files under C:\Dev\New_GEE_PRIVATE\I1_C05
print aggregate JSON summary
```

## Required dry-run output

The dry-run summary must include:

```text
status
source_id
dataset_id
requested_count
candidate_count
held_back_count
planned_label_counts
planned_label_quality_counts
planned_evidence_type_counts
split_counts
redaction_class_counts
real_i1_rows_created
i2_pack_assembled
validator_run_on_real_data
training_started
inference_started
```

Dry-run must always report:

```text
real_i1_rows_created: 0
i2_pack_assembled: false
validator_run_on_real_data: false
training_started: false
inference_started: false
```

## Planned private write files

If write mode is explicitly approved later, the writer may create:

```text
training_examples.c05.private.jsonl
training_examples.c05.private.summary.json
source_lineage.c05.private.json
exclusions.c05.private.summary.json
```

All files must remain outside Git.

## Planned I1 mapping

For accepted C05 rows:

| Field family | Planned value |
| --- | --- |
| source role | negative_background |
| neutral label | Class_Background |
| evidence type | authoritative_external_dataset |
| split | unassigned |
| redaction class | LOCAL_SENSITIVE |

The validator configuration may later map background labels to accepted negative/background names if needed.

C05 rows must never use the positive label family.

## Required generated I1 fields

The writer must create rows with every required I1 field:

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

Rows missing any required field must be held back or rejected.

## Identifier rule

The writer must generate private stable identifiers.

Rules:

- generated ids must be deterministic from private sampling input plus seed
- generated ids must not expose source-specific values
- generated ids must support later split grouping
- initial split remains `unassigned`

## Sampling rule

The writer must target:

```text
217 negative/background rows
```

using:

```text
seed = 20260616
```

If fewer than 217 eligible candidates are available, the writer must fail dry-run or report a held-back count rather than silently lowering the target.

If more than 217 candidates are available, the writer must sample deterministically.

## Boundary rules

The writer must not:

```text
assemble I2
run validator on real data
train
infer
change app/API/frontend code
write files inside Git
```

## Acceptance criteria for future script

The future script is acceptable only if:

- [ ] dry-run creates zero files
- [ ] write mode requires `--write`
- [ ] output directory is outside Git
- [ ] target count is configurable but defaults to 217
- [ ] seed is configurable but defaults to 20260616
- [ ] all emitted rows satisfy the I1 required field list
- [ ] all emitted rows use negative/background label family
- [ ] repo-visible reporting remains aggregate-only
- [ ] no I2 assembly occurs

## Phase C decision

Decision:

```text
c05_private_row_writer_design_ready
```

## Next possible phase

Next possible phase:

```text
Create C05 private row writer script
```

That future phase adds a script only.

It still must default to dry-run and must not write real rows unless `--write` is explicitly used later.

## Current final status

C05 Phase A source/version confirmation is complete.

C05 Phase B sampling-policy design is complete.

C05 Phase C private row writer design is complete.

C05 real I1 rows are not created.

I2 assembly is not started.

H3 remains blocked.

H4 remains blocked.
