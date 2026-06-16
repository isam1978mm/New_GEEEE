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

The next step is to finish the planning checklists so that, when the operator is ready and has the POS-01 source available, the team knows exactly what to check first and where to stop.

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

Status: next.

Goal: decide how approved records would later become I1 training-example rows.

Checklist:

- [ ] required I1 fields
- [ ] allowed neutral labels
- [ ] source evidence field
- [ ] confidence or review status field
- [ ] do-not-train flag
- [ ] split group field
- [ ] privacy flags
- [ ] source lineage fields

No I1 rows are created in this planning step.

### Step 4 — Define the I2 assembly checklist

Goal: describe what a future I2 pack would need after actual dataset review passes.

Checklist:

- [ ] positive pool source
- [ ] negative pool source
- [ ] hard-negative pool sources
- [ ] manifest rules
- [ ] split rules
- [ ] privacy rules
- [ ] validator command
- [ ] pass/fail decision rule

No I2 pack is assembled in this planning step.

### Step 5 — Review the existing validator

Goal: understand the existing readiness validator before building anything.

Checklist:

- [ ] identify required inputs
- [ ] identify required statuses
- [ ] identify blocker names
- [ ] identify success status
- [ ] document what output is needed before H3 can start

No validator changes are made unless explicitly approved later.

### Step 6 — Tighten acceptance criteria

Goal: make later rejection/approval faster and safer.

Checklist:

- [ ] minimum positive-source rules
- [ ] minimum negative-source rules
- [ ] minimum hard-negative-source rules
- [ ] minimum label-quality rules
- [ ] minimum permission rules
- [ ] minimum redaction rules
- [ ] minimum readiness-validator outcome

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

Create the I1 mapping checklist.

This is documentation only.

No I1 rows will be created.

## Current final status

Future I2 planning may continue.

Actual I2 assembly is not started.

H3 remains blocked.

H4 remains blocked.
