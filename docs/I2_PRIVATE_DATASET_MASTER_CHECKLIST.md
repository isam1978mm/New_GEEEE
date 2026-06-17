# I2 private dataset master checklist

Status: active tracker

This is the single checklist for the private I1/I2 dataset path.

It records what is done, what is blocked, what is coming next, and when this I2 readiness path can finish.

No private rows are included.

No private identifiers are included.

No source payload contents are included.

No I2 pack is assembled by this document.

No validator is run by this document.

No training or inference is started by this document.

## Current top-level status

| Area | Status |
| --- | --- |
| D1 freeze | complete |
| D1 parity | complete |
| POS-01 positive I1 rows | complete outside Git |
| C05 negative/background I1 rows | complete outside Git |
| C06 hard-negative I1 rows | complete outside Git |
| C07 hard-negative I1 rows | not started |
| I2 assembly | not started |
| Dataset readiness validator on real data | not run |
| H3 training | blocked |
| H4 inference | blocked |

## Current row inventory

| Source | Role | Private I1 rows | Status |
| --- | --- | ---: | --- |
| POS-01 | positive | 217 | created outside Git |
| C05 | negative/background | 217 | created outside Git |
| C06 | hard-negative | 217 | created outside Git |
| C07 | hard-negative | 0 | not created |

## Current item checklist

Current item:

```text
C07 hard-negative source path
```

Checklist:

```text
[x] plan
[x] actual review kickoff
[ ] Phase A source/version confirmation       ← NEXT
[ ] Phase B sampling policy
[ ] Phase C writer design
[ ] private sample manifest generator
[ ] private sample manifest write
[ ] private I1 writer
[ ] private I1 rows written outside Git
```

## Finish line options

There are two possible finish levels.

### Minimum I2-readiness path

This path is possible but deferred by operator decision.

Required:

- [x] POS-01 positive private I1 rows exist
- [x] C05 negative/background private I1 rows exist
- [x] at least one hard-negative private I1 source exists, C06
- [ ] private split policy exists
- [ ] private I2 pack is assembled outside Git
- [ ] dataset readiness validator runs on the private I2 pack
- [ ] validator returns `ready_for_private_training_later`

Operator selected the stronger path before minimum I2 assembly.

### Stronger I2-readiness path

This is the active path now.

Required:

- [x] POS-01 positive private I1 rows exist
- [x] C05 negative/background private I1 rows exist
- [x] C06 hard-negative private I1 rows exist
- [ ] C07 hard-negative private I1 rows exist
- [ ] private split policy exists
- [ ] private I2 pack is assembled outside Git
- [ ] dataset readiness validator runs on the private I2 pack
- [ ] validator returns `ready_for_private_training_later`

This path finishes after C07 is ready and the validator passes.

## Active next step

```text
C07 Phase A — source/version confirmation
```

The operator must provide:

```text
C07 source/version:
Allowed mining/disturbance hard-negative classes:
Target hard-negative row count:
Private folder:
Sampling seed:
Split/grouping policy:
```

Recommended answer:

```text
C07 source/version: Maus mining polygons, operator-selected local version
Allowed mining/disturbance hard-negative classes: mining/disturbance non-target only
Target hard-negative row count: 217
Private folder: C:\Dev\New_GEE_PRIVATE\C07_RAW and C:\Dev\New_GEE_PRIVATE\I1_C07
Sampling seed: 20260616
Split/grouping policy: unassigned initially, group_id generated later, no split leakage
```

## What is coming next

### C07 path

1. C07 Phase A source/version confirmation.
2. C07 Phase B sampling policy design.
3. C07 Phase C writer design.
4. C07 private sample manifest or sampler script.
5. C07 private I1 writer dry-run.
6. C07 private I1 rows written outside Git.
7. Then return to private split policy and I2 assembly.

### After C07 is ready

1. Create private split policy.
2. Create private I2 assembly plan.
3. Assemble private I2 pack outside Git.
4. Run dataset readiness validator on private I2 pack.
5. If validator passes, I2 readiness phase is complete.
6. H3 remains a separate explicit decision after I2 readiness.
7. H4 remains blocked until after a later approved H3 model and private inference gate.

## Detailed checklist

### 1. POS-01 positive source

| Step | Status |
| --- | --- |
| metadata review | done |
| actual dataset review | done with exclusions |
| aggregate label review | done |
| private I1 mapping dry-run | done |
| private I1 row writer | done |
| private I1 rows written outside Git | done |

Result:

```text
217 private positive I1 rows created outside Git
16 records held back
```

### 2. C05 negative/background source

| Step | Status |
| --- | --- |
| Phase A source/version confirmation | done |
| Phase B sampling policy | done |
| Phase C writer design | done |
| private sample manifest generator | done |
| WorldCover raster private input | done |
| private sample manifest write | done |
| private I1 writer dry-run with manifest | done |
| private I1 rows written outside Git | done |

Result:

```text
217 private negative/background I1 rows created outside Git
```

### 3. C06 hard-negative source

| Step | Status |
| --- | --- |
| kickoff | done |
| Phase A source/version confirmation | done |
| Phase B sampling policy | done |
| Phase C writer design | done |
| private sample manifest generator | done |
| private sample manifest write | done |
| private I1 writer | done |
| private I1 writer dry-run | done |
| private I1 rows written outside Git | done |

Result:

```text
217 private hard-negative I1 rows created outside Git
```

### 4. C07 hard-negative source

| Step | Status |
| --- | --- |
| plan | done |
| actual review kickoff | done |
| Phase A source/version confirmation | next |
| Phase B sampling policy | not started |
| Phase C writer design | not started |
| private sample manifest generator | not started |
| private sample manifest write | not started |
| private I1 writer | not started |
| private I1 rows written outside Git | not started |

Current blocker:

```text
C07 Phase A operator settings are missing.
```

### 5. I2 assembly

| Step | Status |
| --- | --- |
| C07 stronger hard-negative path | active |
| create private split policy | not started |
| combine private I1 rows | not started |
| create private I2 manifest | not started |
| create private I2 examples file | not started |
| run dataset readiness validator on real data | not started |

Current blocker:

```text
C07 hard-negative private I1 rows are not ready.
```

### 6. H3 and H4

| Step | Status |
| --- | --- |
| H3 training | blocked |
| H4 inference | blocked |

Reason:

```text
I2 has not been assembled and has not passed the readiness validator.
```

## Stop conditions

Stop immediately if work requires:

```text
committing private I1 files
committing source rasters
publishing private sample rows
assembling I2 without explicit approval
running validator on real data before I2 exists
training
inference
app/API/frontend changes
```

Those require separate explicit approval.

## Short answer: where we are

```text
POS-01 positive rows: done
C05 background rows: done
C06 hard-negative rows: done
C07 Phase A: next
I2: not started
H3/H4: blocked
```
