# C07 Phase A source/version confirmation

Status: confirmed for sampling-policy design

This document records the C07 Phase A settings.

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

Allowed mining/disturbance hard-negative classes:

```text
mining/disturbance non-target only
```

Target hard-negative row count:

```text
217
```

Private folder family:

```text
C:\Dev\New_GEE_PRIVATE\C07_RAW
C:\Dev\New_GEE_PRIVATE\I1_C07
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

C07 is planned to provide additional hard-negative examples only.

C07 must not create target-positive labels.

C07 examples are intended to represent confusing non-target mining or disturbance polygons for false-positive suppression.

The initial target count matches the current positive, background, and C06 hard-negative private I1 row counts:

```text
POS-01 positive I1 rows: 217
C05 background I1 rows: 217
C06 hard-negative I1 rows: 217
C07 target hard-negative rows: 217
```

This supports the stronger I2-readiness path once C07 rows are created and later split/I2 validation steps pass.

## Phase A decision

Decision:

```text
c07_source_version_ready
```

## Next phase

Next phase:

```text
C07 Phase B — sampling-policy design
```

Phase B must define:

- mining/disturbance hard-negative class families
- row count target
- deterministic seed use
- grouping rule
- split rule
- exclusion rule summaries
- relationship to positive areas if applicable
- private output behavior

## Stop conditions

Stop immediately if work requires:

```text
downloading source data into Git
creating real C07 I1 rows
assembling I2
running validator on real data
training
inference
app/API/frontend changes
```

Those require separate explicit approval.

## Current final status

C07 Phase A source/version confirmation is complete.

C07 Phase B sampling-policy design is next.

C07 real I1 row creation is not started.

I2 assembly is not started.

H3 remains blocked.

H4 remains blocked.
