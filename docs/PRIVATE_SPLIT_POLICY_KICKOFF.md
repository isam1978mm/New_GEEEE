# Private split policy kickoff

Status: opened

This document opens the private split policy phase for the stronger I2 path.

No private rows are included.

No private identifiers are included.

No source payload contents are included.

No split assignment is written by this document.

No I2 pack is assembled by this document.

No validator is run by this document.

No model or inference step is started.

## Current row inventory

| Source | Role | Private I1 rows | Status |
| --- | --- | ---: | --- |
| POS-01 | positive | 217 | created outside Git |
| C05 | background | 217 | created outside Git |
| C06 | hard-negative | 217 | created outside Git |
| C07 | hard-negative | 217 | created outside Git |

Total private I1 rows available for stronger I2 planning:

```text
868
```

## Current item checklist

Current item:

```text
Private split policy path
```

Checklist:

```text
[x] kickoff
[ ] split/group leakage rules       ← NEXT
[ ] train/val/test/holdout policy
[ ] private split assignment script design
[ ] private split assignment dry-run
[ ] private split assignment write outside Git
[ ] I2 assembly plan
```

## Purpose

The private split policy phase defines how the existing private I1 rows will later be assigned to train, validation, test, or holdout splits.

The policy must prevent leakage between splits.

The policy must respect generated group identifiers.

The policy must keep all private row files outside Git.

## Required design topics

The next policy document must define:

```text
group leakage rules
source balancing rules
train/val/test/holdout ratios
holdout rules
random seed
source-specific constraints
aggregate-only reporting rules
```

## Initial policy direction

Recommended starting policy:

```text
split unit: group_id
random seed: 20260616
initial split labels: train, val, test, holdout
no sample_id may cross splits
no group_id may cross splits
repo-visible output: aggregate counts only
private split assignment output: outside Git only
```

## Stop conditions

Stop before any step that would:

```text
write private split assignments without approval
commit private row files
commit source datasets
assemble I2 without explicit approval
run validator before I2 exists
start model work
start inference work
change app/API/frontend code
```

## Decision

```text
private_split_policy_phase_opened
```

## Next step

```text
Define split/group leakage rules
```
