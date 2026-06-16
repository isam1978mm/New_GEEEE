# C05 actual negative/background review kickoff

Status: opened, not started

This document opens the actual review phase for C05.

C05 is the planned negative/background source for future I2.

This document does not download source data.

This document does not inspect source records.

This document does not create I1 rows.

This document does not assemble I2.

This document does not run the dataset readiness validator.

This document does not start training or inference.

## Source

C05:

```text
ESA WorldCover negative/background candidate
```

Planned role:

```text
negative_background
```

C05 is not a positive source.

C05 must not create target-positive labels.

## Why C05 is needed

POS-01 now provides the private positive I1 row pool.

Future I2 cannot rely on positives only.

C05 is needed to provide controlled background/negative examples for balance and false-positive control.

## Current project status

```text
POS-01 private positive I1 rows: created outside Git
C05 actual review: opened, not started
C05 real I1 rows: not created
C06 real I1 rows: not created
C07 real I1 rows: not created
I2 assembly: not started
Validator on real data: not run
H3: blocked
H4: blocked
```

## Required operator decisions before actual C05 review starts

Before any source work starts, decide:

- [ ] exact C05 source/version to use
- [ ] allowed background class families
- [ ] target number of negative/background rows
- [ ] private storage location outside Git
- [ ] deterministic sampling seed
- [ ] split/grouping policy
- [ ] exclusion rules
- [ ] attribution/license note

## Recommended private folder family

If C05 source material or derived private rows are created later, use a private folder outside Git:

```text
C:\Dev\New_GEE_PRIVATE\C05_RAW
C:\Dev\New_GEE_PRIVATE\I1_C05
```

Do not place source data or private I1 outputs inside the repository.

## Phase A — metadata/source-version confirmation

Allowed output:

- source name
- version or release identifier
- license summary
- selected background class families
- planned sample count
- planned private folder family

Forbidden output:

- source payload rows
- private samples
- private identifiers
- I1 JSONL rows
- I2 files

Decision values:

```text
c05_source_version_ready
c05_needs_operator_info
c05_blocked
c05_rejected
```

## Phase B — sampling-policy design

Allowed output:

- sample count target
- background class families
- deterministic seed
- split/grouping rule
- exclusion rule summaries

Forbidden output:

- real sampled rows
- private sample identifiers
- feature/chip files
- I1 JSONL rows

Decision values:

```text
c05_sampling_policy_ready
c05_sampling_policy_needs_operator_info
c05_sampling_policy_blocked
```

## Phase C — private row writer design

This phase starts only after source-version and sampling policy are accepted.

Allowed output:

- script design
- aggregate-only expected output fields
- private folder family
- stop conditions

Forbidden output:

- real row creation
- I2 assembly
- validator run on real data

## Stop conditions

Stop immediately if work requires:

```text
downloading source data into Git
creating private rows without approval
assembling I2
running validator on real data
training
inference
app/API/frontend changes
```

Those require separate explicit approval.

## Current decision

```text
c05_actual_negative_background_review_opened_not_started
```

## Current final status

C05 actual negative/background review is opened but not started.

C05 real I1 row creation is not started.

I2 assembly is not started.

H3 remains blocked.

H4 remains blocked.
