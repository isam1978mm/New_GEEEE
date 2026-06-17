# C06 Phase A source/version confirmation

Status: confirmed for sampling-policy design

This document records the C06 Phase A settings.

No source data is downloaded by this document.

No source records are inspected by this document.

No real I1 rows are created by this document.

No I2 pack is assembled.

No validator is run on real data.

No training or inference is started.

## Source

C06 source/version:

```text
Dynamic World, operator-selected local version
```

Planned role:

```text
hard_negative
```

Allowed hard-negative classes:

```text
built/bare/confusing non-target only
```

Target hard-negative row count:

```text
217
```

Private folder family:

```text
C:\Dev\New_GEE_PRIVATE\C06_RAW
C:\Dev\New_GEE_PRIVATE\I1_C06
```

Sampling seed:

```text
20260616
```

Split/grouping policy:

```text
unassigned initially, group_id generated later, no split leakage
```

## Interpretation

C06 is planned to provide hard-negative examples only.

C06 must not create target-positive labels.

C06 examples are intended to represent confusing non-target conditions for false-positive suppression.

The initial target count matches the current positive and background private I1 row counts:

```text
POS-01 positive I1 rows: 217
C05 background I1 rows: 217
C06 target hard-negative rows: 217
```

This supports the minimum I2-readiness path once C06 rows are created and later split/I2 validation steps pass.

## Phase A decision

Decision:

```text
c06_source_version_ready
```

## Next phase

Next phase:

```text
C06 Phase B — sampling-policy design
```

Phase B must define:

- hard-negative class families
- row count target
- deterministic seed use
- grouping rule
- split rule
- exclusion rule summaries
- private output behavior

## Stop conditions

Stop immediately if work requires:

```text
downloading source data into Git
creating real C06 I1 rows
assembling I2
running validator on real data
training
inference
app/API/frontend changes
```

Those require separate explicit approval.

## Current final status

C06 Phase A source/version confirmation is complete.

C06 Phase B sampling-policy design is next.

C06 real I1 row creation is not started.

I2 assembly is not started.

H3 remains blocked.

H4 remains blocked.
