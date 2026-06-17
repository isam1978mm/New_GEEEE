# I2 private dataset master checklist

Status: active tracker

This is the single checklist for the private I1/I2 dataset path.

It records what is done, what is blocked, and the exact next step.

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
| C06 hard-negative I1 rows | not started |
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
| C06 | hard-negative | 0 | not created |
| C07 | hard-negative | 0 | not created |

## Active next step

```text
C06 Phase A — source/version confirmation
```

The operator must provide:

```text
C06 source/version:
Allowed hard-negative classes:
Target hard-negative row count:
Private folder:
Sampling seed:
Split/grouping policy:
```

Recommended answer:

```text
C06 source/version: Dynamic World, operator-selected local version
Allowed hard-negative classes: built/bare/confusing non-target only
Target hard-negative row count: 217
Private folder: C:\Dev\New_GEE_PRIVATE\C06_RAW and C:\Dev\New_GEE_PRIVATE\I1_C06
Sampling seed: 20260616
Split/grouping policy: unassigned initially, group_id generated later, no split leakage
```

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
| Phase A source/version confirmation | next |
| Phase B sampling policy | not started |
| Phase C writer design | not started |
| private sample manifest generator | not started |
| private sample manifest write | not started |
| private I1 writer | not started |
| private I1 rows written outside Git | not started |

Current blocker:

```text
C06 Phase A operator settings are missing.
```

### 4. C07 hard-negative source

| Step | Status |
| --- | --- |
| plan | done |
| actual review kickoff | not started |
| Phase A source/version confirmation | not started |
| Phase B sampling policy | not started |
| Phase C writer design | not started |
| private sample manifest generator | not started |
| private I1 writer | not started |
| private I1 rows written outside Git | not started |

### 5. I2 assembly

| Step | Status |
| --- | --- |
| combine private I1 rows | not started |
| create private I2 manifest | not started |
| create private I2 examples file | not started |
| create split policy | not started |
| run dataset readiness validator on real data | not started |

Current blocker:

```text
C06 and C07 hard-negative private I1 rows are not ready.
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
assembling I2 before C06/C07 are ready
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
C06 hard-negative rows: next
C07 hard-negative rows: later
I2: not started
H3/H4: blocked
```
