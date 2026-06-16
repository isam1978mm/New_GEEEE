# POS-01 I1 mapping dry-run design

Status: planning only

This document defines the next safe planning step after POS-01 actual review passed with exclusions.

No real I1 rows are created here.

No I2 pack is assembled here.

No training or inference is started here.

## Starting point

POS-01 actual review decision:

```text
actual_review_passed_with_exclusions
```

Aggregate counts:

| Metric | Count |
| --- | ---: |
| Accepted aggregate records | 233 |
| Complete candidate records | 217 |
| Needs-review or exclusion records | 16 |

Only the 217 complete candidate records may continue to a later private mapping dry-run.

The 16 needs-review records must not continue automatically.

## Purpose

The dry-run design asks:

```text
Can POS-01 accepted candidates be represented in the existing I1 schema using private generated identifiers and neutral labels?
```

It does not create the rows.

## Required existing I1 fields

A later private I1 mapping must satisfy the existing training-example schema, including:

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

## Planned POS-01 neutral mapping

Planned role:

```text
positive
```

Planned neutral label:

```text
Class_A
```

Planned label quality candidate:

```text
reviewed_independent
```

Planned evidence source type candidate:

```text
authoritative_external_dataset
```

Planned storage class:

```text
LOCAL_SENSITIVE or FILESYSTEM_ONLY
```

These are dry-run targets only.

## Dry-run rules

A later private dry-run may output only aggregate counts:

```text
candidate_count
mappable_count
excluded_count
missing_required_field_counts
label_family_counts
evidence_type_counts
storage_class_counts
blocker_counts
```

The dry-run must not write private source values to Git.

The dry-run must not write real I1 JSONL rows.

The dry-run must not assemble I2.

## Required checks for later private dry-run

The later private dry-run must verify:

- [ ] the 217 complete candidates can receive private generated ids
- [ ] the 217 complete candidates can map to Class_A
- [ ] the 217 complete candidates can retain private evidence lineage
- [ ] the 217 complete candidates can set reviewed-tier evidence fields
- [ ] the 217 complete candidates can set private storage class
- [ ] the 16 needs-review records are excluded or held back
- [ ] repo-visible output remains aggregate-only

## Dry-run decision values

Allowed decisions:

```text
i1_mapping_dry_run_ready
i1_mapping_dry_run_ready_with_exclusions
i1_mapping_needs_operator_info
i1_mapping_blocked
i1_mapping_rejected
```

Expected planning decision:

```text
i1_mapping_dry_run_ready_with_exclusions
```

## Stop conditions

Stop if the work requires:

```text
real I1 row creation
I2 assembly
validator run on real data
training
inference
app or API changes
```

Those require separate explicit approval.

## Current decision

```text
pos01_i1_mapping_dry_run_design_ready
```

## Current final status

POS-01 actual review passed with exclusions.

POS-01 I1 mapping dry-run design is ready.

Real I1 row creation is not started.

I2 assembly is not started.

H3 remains blocked.

H4 remains blocked.
