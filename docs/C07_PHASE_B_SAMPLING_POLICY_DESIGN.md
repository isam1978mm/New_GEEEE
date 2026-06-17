# C07 Phase B sampling-policy design

Status: sampling policy ready for private row-writer design

This document defines the C07 mining/disturbance hard-negative sampling policy for a later approved private I1 row creation step.

No source data is downloaded by this document.

No source records are inspected by this document.

No real I1 rows are created by this document.

No I2 pack is assembled.

No validator is run on real data.

No training or inference is started.

## Source

C07 source/version:

```text
Maus mining polygons, operator-selected local version
```

Planned role:

```text
hard_negative
```

Allowed mining/disturbance hard-negative class family:

```text
mining/disturbance non-target only
```

Target row count:

```text
217
```

Sampling seed:

```text
20260616
```

Private folder family:

```text
C:\Dev\New_GEE_PRIVATE\C07_RAW
C:\Dev\New_GEE_PRIVATE\I1_C07
```

## Purpose

C07 provides an additional hard-negative side for the stronger future I2 path.

It is meant to add confusing non-target mining or disturbance examples that help reduce false positives.

C07 must not create target-positive labels.

The initial target count matches the current POS-01 positive, C05 background, and C06 hard-negative private I1 row counts:

```text
POS-01 positive rows: 217
C05 background rows: 217
C06 hard-negative rows: 217
C07 target hard-negative rows: 217
```

## Planned neutral mapping

For accepted C07 hard-negative samples:

| Field family | Planned value |
| --- | --- |
| source role | hard_negative |
| neutral label | Class_HardNegative |
| evidence type | independently_produced_reference |
| split | unassigned initially |
| storage class | LOCAL_SENSITIVE or FILESYSTEM_ONLY |

C07 rows must never use the positive label family.

## Sampling policy

A later private C07 row writer or sampler must sample exactly:

```text
217 hard-negative candidates
```

Sampling must be deterministic using:

```text
seed = 20260616
```

The sampling policy must:

- select mining/disturbance non-target candidates only
- avoid target-positive labeling
- keep all outputs outside Git
- generate private stable identifiers
- assign split as `unassigned` initially
- record aggregate counts only in repo-visible docs
- avoid unlimited hard-negative expansion
- allow later exclusion if a candidate conflicts with a known positive area

## Grouping policy

Each generated C07 candidate must receive private generated identifiers for:

```text
sample_id
area_id
group_id
chip_id
```

Initial rule:

```text
one generated group_id per sampled mining/disturbance candidate unless later grouping rules merge nearby or related samples
```

No final train/validation/test/holdout split is assigned in this phase.

## Exclusion policy

Exclude or hold back any C07 candidate if:

- source/version cannot be confirmed
- mining/disturbance class is not allowed
- candidate lacks required geometry or source reference
- private stable id generation fails
- I1 required fields cannot be populated
- source lineage cannot be recorded
- storage would not remain outside Git
- candidate conflicts with a known positive area under later private checks
- license or attribution rules would prevent private training use

## Required aggregate-only dry-run output

A later C07 private row writer dry-run may report only:

```text
requested_count
candidate_count
eligible_count
selected_count
held_back_count
label_counts
evidence_type_counts
split_counts
storage_class_counts
real_i1_rows_created
```

Dry-run mode must create zero real rows.

## Required write output after explicit approval

If real C07 row creation is explicitly approved later, the writer may create private files only under:

```text
C:\Dev\New_GEE_PRIVATE\I1_C07
```

Recommended private files:

```text
training_examples.c07.private.jsonl
training_examples.c07.private.summary.json
source_lineage.c07.private.json
exclusions.c07.private.summary.json
```

## Stop conditions

Stop immediately if work requires:

```text
committing private I1 files
publishing sampled private records
assembling I2
running validator on real data
training
inference
app/API/frontend changes
```

Those require separate explicit approval.

## Phase B decision

Decision:

```text
c07_sampling_policy_ready
```

## Next phase

Next phase:

```text
C07 Phase C — private row writer design
```

## Current final status

C07 Phase A source/version confirmation is complete.

C07 Phase B sampling-policy design is complete.

C07 real I1 rows are not created.

I2 assembly is not started.

H3 remains blocked.

H4 remains blocked.
