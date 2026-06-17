# C07 actual hard-negative review kickoff

Status: opened, not started

This document opens the actual review phase for C07.

C07 is the planned stronger hard-negative source for future I2.

This document does not download source data.

This document does not inspect source records.

This document does not create I1 rows.

This document does not assemble I2.

This document does not run the dataset readiness validator.

This document does not start training or inference.

## Source

C07:

```text
Maus mining polygons hard-negative candidate
```

Planned role:

```text
hard_negative
```

C07 is not a positive source.

C07 must not create target-positive labels.

## Why C07 is needed

POS-01 provides private positive I1 rows.

C05 provides private negative/background I1 rows.

C06 provides private hard-negative I1 rows from Dynamic World built/bare samples.

C07 is planned to strengthen the hard-negative side with mining/disturbance polygons that may be visually confusing but are not target-positive evidence.

## Current project status

```text
POS-01 private positive I1 rows: created outside Git
C05 private negative/background I1 rows: created outside Git
C06 private hard-negative I1 rows: created outside Git
C07 actual review: opened, not started
C07 real I1 rows: not created
I2 assembly: not started
Validator on real data: not run
H3: blocked
H4: blocked
```

## Required operator decisions before actual C07 review starts

Before any C07 source work starts, decide:

- [ ] exact C07 source/version to use
- [ ] allowed mining/disturbance hard-negative class families
- [ ] target number of hard-negative rows
- [ ] private storage location outside Git
- [ ] deterministic sampling seed
- [ ] split/grouping policy
- [ ] exclusion rules
- [ ] attribution/license note

## Recommended private folder family

If C07 source material or derived private rows are created later, use a private folder outside Git:

```text
C:\Dev\New_GEE_PRIVATE\C07_RAW
C:\Dev\New_GEE_PRIVATE\I1_C07
```

Do not place source data or private I1 outputs inside the repository.

## Phase A — metadata/source-version confirmation

Allowed output:

- source name
- version or release identifier
- license summary
- selected hard-negative class families
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
c07_source_version_ready
c07_needs_operator_info
c07_blocked
c07_rejected
```

## Phase B — sampling-policy design

Allowed output:

- sample count target
- hard-negative class families
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
c07_sampling_policy_ready
c07_sampling_policy_needs_operator_info
c07_sampling_policy_blocked
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
c07_actual_hard_negative_review_opened_not_started
```

## Current final status

C07 actual hard-negative review is opened but not started.

C07 real I1 row creation is not started.

I2 assembly is not started.

H3 remains blocked.

H4 remains blocked.
