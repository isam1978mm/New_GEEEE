# Future I2 planning — current status and next steps

Status: planning only

This document explains the next steps after POS-01 passed metadata-level candidate review.

## Current status

D1 is complete.

D1 app-vs-reference parity for the accepted scope is complete.

Slice 13 source scouting is complete enough to define a future I2 planning path.

Approved source candidates for later planning:

- POS-01: positive source candidate
- C05: negative/background candidate
- C06: hard-negative candidate
- C07: hard-negative candidate

Not started:

- actual dataset review
- source payload inspection
- I1 row creation
- I2 dataset pack assembly
- H3 training
- H4 private inference

Current permission state:

- I2 assembly is not authorized yet.
- H3 remains blocked.
- H4 remains blocked.

## Plain English next step

The next step is not to build a dataset.

The future I2 planning checklist sequence is now complete. When the operator is ready and has the POS-01 source available, the next separate phase would be actual POS-01 dataset review.

That later phase requires explicit approval before any source payload is opened or inspected.

## Next steps checklist

### Step 1 — Define the future source inventory checklist

Status: done.

Document:

```text
docs/FUTURE_I2_SOURCE_INVENTORY_CHECKLIST.md
```

Goal: decide what must be recorded about each source before any data is used.

Checklist:

- [x] source id
- [x] source role: positive, negative, or hard-negative
- [x] owner or authority
- [x] license or permission status
- [x] allowed private training use
- [x] sensitivity handling decision
- [x] redaction requirement
- [x] expected schema or fields
- [x] do-not-use conditions

No source files are opened in this step.

### Step 2 — Define the actual dataset review checklist

Status: done.

Document:

```text
docs/FUTURE_I2_ACTUAL_DATASET_REVIEW_CHECKLIST.md
```

Goal: prepare the review questions for later, when POS-01 is available.

Checklist:

- [x] what files are present
- [x] what fields exist
- [x] what counts as a positive example
- [x] whether any sensitive fields exist
- [x] whether records match the source metadata
- [x] whether labels match the H3/H4 target definition
- [x] whether records can be mapped to neutral labels
- [x] whether any records must be excluded

No dataset is inspected in this planning step.

### Step 3 — Define the I1 mapping checklist

Status: done.

Document:

```text
docs/FUTURE_I2_I1_MAPPING_CHECKLIST.md
```

Goal: decide how approved records would later become I1 training-example rows.

Checklist:

- [x] required I1 fields
- [x] allowed neutral labels
- [x] source evidence field
- [x] confidence or review status field
- [x] do-not-train flag
- [x] split group field
- [x] privacy flags
- [x] source lineage fields

No I1 rows are created in this planning step.

### Step 4 — Define the I2 assembly checklist

Status: done.

Document:

```text
docs/FUTURE_I2_ASSEMBLY_CHECKLIST.md
```

Goal: describe what a future I2 pack would need after actual dataset review passes.

Checklist:

- [x] positive pool source
- [x] negative pool source
- [x] hard-negative pool sources
- [x] manifest rules
- [x] split rules
- [x] privacy rules
- [x] validator command
- [x] pass/fail decision rule

No I2 pack is assembled in this planning step.

### Step 5 — Review the existing validator

Status: done.

Document:

```text
docs/FUTURE_I2_DATASET_PACK_READINESS_VALIDATOR_REVIEW.md
```

Goal: understand the existing readiness validator before building anything.

Checklist:

- [x] identify required inputs
- [x] identify required statuses
- [x] identify blocker names
- [x] identify success status
- [x] document what output is needed before H3 can start

No validator changes are made unless explicitly approved later.

### Step 6 — Tighten acceptance criteria

Status: done.

Document:

```text
docs/FUTURE_I2_ACCEPTANCE_CRITERIA.md
```

Goal: make later rejection/approval faster and safer.

Checklist:

- [x] minimum positive-source rules
- [x] minimum negative-source rules
- [x] minimum hard-negative-source rules
- [x] minimum label-quality rules
- [x] minimum permission rules
- [x] minimum redaction rules
- [x] minimum readiness-validator outcome

## Stop conditions

Stop immediately if any step requires:

- downloading a source payload
- inspecting source records
- collecting coordinates
- creating labels
- creating chips or masks
- creating I1 rows
- assembling I2
- training
- inference
- app or API changes

Those actions require a separate explicit user approval.

## Next concrete task

Future I2 planning checklist sequence is complete.

The next possible phase is actual POS-01 dataset review, but only after explicit approval and only when the operator has the source available.

No dataset, validator, training, or inference work is started by this planning closeout.

## Current final status

Future I2 planning checklist sequence is complete.

Actual POS-01 dataset review is not started.

Actual I2 assembly is not started.

H3 remains blocked.

H4 remains blocked.
