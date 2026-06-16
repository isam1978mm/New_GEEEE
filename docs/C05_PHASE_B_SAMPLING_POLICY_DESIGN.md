# C05 Phase B sampling-policy design

Status: sampling policy ready for private row-writer design

This document defines the C05 negative/background sampling policy for a later approved private I1 row creation step.

No source data is downloaded by this document.

No source records are inspected by this document.

No real I1 rows are created by this document.

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

Private folder family:

```text
C:\Dev\New_GEE_PRIVATE\C05_RAW
C:\Dev\New_GEE_PRIVATE\I1_C05
```

## Purpose

C05 provides the planned background/negative side for future I2.

It balances the current POS-01 positive private I1 row count:

```text
POS-01 positive rows: 217
C05 target background rows: 217
```

C05 must not create target-positive labels.

## Planned neutral mapping

For accepted C05 background samples:

| Field family | Planned value |
| --- | --- |
| source role | negative_background |
| neutral label | Class_Background |
| evidence type | authoritative_external_dataset |
| split | unassigned initially |
| storage class | LOCAL_SENSITIVE or FILESYSTEM_ONLY |

If the validator configuration later uses `Class_Negative`, the mapping may be configured there.

The planning target remains background/negative only.

## Sampling policy

A later private C05 row writer must sample exactly:

```text
217 background candidates
```

Sampling must be deterministic using:

```text
seed = 20260616
```

The sampling policy must:

- select non-target background only
- avoid target-positive labeling
- keep all outputs outside Git
- generate private stable identifiers
- assign split as `unassigned` initially
- record aggregate counts only in repo-visible docs
- avoid unlimited background expansion

## Grouping policy

Each generated C05 candidate must receive private generated identifiers for:

```text
sample_id
area_id
group_id
chip_id
```

Initial rule:

```text
one generated group_id per sampled background candidate unless later grouping rules merge nearby or related samples
```

No final train/validation/test/holdout split is assigned in this phase.

## Exclusion policy

Exclude or hold back any C05 candidate if:

- source/version cannot be confirmed
- background class is not allowed
- private stable id generation fails
- I1 required fields cannot be populated
- source lineage cannot be recorded
- storage would not remain outside Git
- candidate conflicts with a known positive area under later private checks

## Required aggregate-only dry-run output

A later C05 private row writer dry-run may report only:

```text
requested_count
candidate_count
created_count_if_write_enabled
held_back_count
label_counts
evidence_type_counts
split_counts
storage_class_counts
real_i1_rows_created
```

Dry-run mode must create zero real rows.

## Required write output after explicit approval

If real C05 row creation is explicitly approved later, the writer may create private files only under:

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
c05_sampling_policy_ready
```

## Next phase

Next phase:

```text
C05 Phase C — private row writer design
```

## Current final status

C05 Phase A source/version confirmation is complete.

C05 Phase B sampling-policy design is complete.

C05 real I1 rows are not created.

I2 assembly is not started.

H3 remains blocked.

H4 remains blocked.
