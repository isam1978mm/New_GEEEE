# C05 Phase A source/version confirmation

Status: confirmed for sampling-policy design

This document records the operator-provided C05 Phase A settings.

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

Allowed background classes:

```text
non-target background only
```

Target negative/background row count:

```text
217
```

Private folder family:

```text
C:\Dev\New_GEE_PRIVATE\C05_RAW
C:\Dev\New_GEE_PRIVATE\I1_C05
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

C05 is planned to provide negative/background examples only.

C05 must not create target-positive labels.

The initial target count matches the POS-01 private positive I1 candidate count:

```text
POS-01 positive I1 rows: 217
C05 target negative/background rows: 217
```

This supports an initial balanced planning target, but it does not assemble I2 and does not start training.

## Phase A decision

Decision:

```text
c05_source_version_ready
```

## Next phase

Next phase:

```text
C05 Phase B — sampling-policy design
```

Phase B must define:

- background sampling class family
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
creating real C05 I1 rows
assembling I2
running validator on real data
training
inference
app/API/frontend changes
```

Those require separate explicit approval.

## Current final status

C05 Phase A source/version confirmation is complete.

C05 Phase B sampling-policy design is next.

C05 real I1 row creation is not started.

I2 assembly is not started.

H3 remains blocked.

H4 remains blocked.
