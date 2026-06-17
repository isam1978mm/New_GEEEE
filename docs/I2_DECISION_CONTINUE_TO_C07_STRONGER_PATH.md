# I2 decision: continue to C07 stronger path

Status: decision recorded

The operator selected:

```text
Option 2: continue to C07 first
```

This means the project will continue the stronger hard-negative path before attempting I2 assembly.

No source data is downloaded by this document.

No private rows are created by this document.

No I2 pack is assembled.

No validator is run on real data.

No training or inference is started.

## Current row inventory at decision time

| Source | Role | Private I1 rows | Status |
| --- | --- | ---: | --- |
| POS-01 | positive | 217 | created outside Git |
| C05 | negative/background | 217 | created outside Git |
| C06 | hard-negative | 217 | created outside Git |
| C07 | hard-negative | 0 | not created |

## Decision

Decision:

```text
i2_continue_to_c07_stronger_hard_negative_path
```

## Consequence

Minimum I2 assembly remains possible but is deferred.

The active next source becomes C07.

C07 is planned as:

```text
Maus mining polygons hard-negative candidate
```

C07 must remain hard-negative only.

C07 must not create target-positive labels.

## Next step

```text
C07 actual hard-negative review kickoff
```

## Current final status

POS-01 private positive I1 rows exist outside Git.

C05 private negative/background I1 rows exist outside Git.

C06 private hard-negative I1 rows exist outside Git.

C07 private hard-negative I1 rows are not created.

I2 assembly is not started.

H3 remains blocked.

H4 remains blocked.
