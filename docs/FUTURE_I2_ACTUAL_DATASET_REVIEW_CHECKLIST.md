# Future I2 actual dataset review checklist

Status: planning only

This document defines what must be checked later when an approved source candidate is available for actual dataset review.

This checklist does not inspect any dataset.

This checklist does not download source payloads.

This checklist does not create I1 rows or I2 packs.

H3 and H4 remain blocked.

## Purpose

The actual dataset review is the first future step after source inventory.

It answers one question:

```text
Does the real source content match the metadata-level approval assumptions?
```

It does not answer:

```text
Is I2 assembled?
Can H3 training start?
Can H4 inference start?
```

Those require later steps and validator approval.

## Current source candidates

Positive candidate:

- POS-01

Negative/background candidate:

- C05

Hard-negative candidates:

- C06
- C07

Actual review has not started for any source.

## Actual dataset review phases

### Phase 1 — Access confirmation

Before opening source contents, confirm:

- [ ] source_id matches source inventory
- [ ] source role matches source inventory
- [ ] license or permission is still valid
- [ ] private training permission is still valid
- [ ] storage location is operator-private
- [ ] reviewer understands stop conditions

Stop if permission, license, or storage status changed.

### Phase 2 — File inventory

Record only safe inventory metadata:

- [ ] file count
- [ ] file types
- [ ] approximate record count if visible without exposing records
- [ ] schema/table names if applicable
- [ ] documentation files present
- [ ] license/terms files present
- [ ] readme or method notes present

Do not copy records into repo-visible docs.

### Phase 3 — Schema review

Check the available fields without exposing sensitive values:

- [ ] source identifier field exists
- [ ] evidence or event type field exists
- [ ] label or damage status field exists
- [ ] provenance/source field exists
- [ ] date or version field exists if applicable
- [ ] confidence or uncertainty field exists if applicable
- [ ] fields needed for neutral mapping exist
- [ ] fields needed for do-not-train decisions exist

Do not paste real row values into repo-visible docs.

### Phase 4 — Label definition review

Determine what a positive, negative, or hard-negative record actually means.

For positive sources, check:

- [ ] positive label meaning is clear
- [ ] positive label matches the intended H3/H4 target definition
- [ ] positive label is not merely a weak signal
- [ ] positive label is backed by independent evidence
- [ ] uncertain records can be excluded

For negative/background sources, check:

- [ ] negative label role is background only
- [ ] negative labels are not treated as positive absence truth beyond their role
- [ ] source is not used to create target-positive examples

For hard-negative sources, check:

- [ ] hard-negative role is clear
- [ ] source represents confusing non-target examples
- [ ] source is not used as positive evidence

### Phase 5 — Sensitivity review

Check whether the actual contents contain fields requiring stronger handling:

- [ ] location-bearing fields present or absent
- [ ] named site fields present or absent
- [ ] sensitive identifier fields present or absent
- [ ] free-text fields present or absent
- [ ] fields that could expose vulnerable locations present or absent
- [ ] redaction plan still works
- [ ] repo-visible summaries can remain metadata-only

Do not copy sensitive values into Git.

### Phase 6 — Quality review

Check data quality at a summary level:

- [ ] duplicate records can be identified
- [ ] missing required fields can be counted
- [ ] invalid labels can be counted
- [ ] uncertain records can be excluded
- [ ] source version is clear
- [ ] method notes are consistent with metadata review
- [ ] sample quality is sufficient for later I1 mapping

Only aggregate counts may be documented in repo-visible files.

### Phase 7 — Neutral label mapping review

Map source concepts to neutral labels without exposing source-specific names as model labels.

Allowed neutral families:

```text
Class_A
Background
Hard_Negative
Ignore
Uncertain
```

Checklist:

- [ ] source positive records map to Class_A only if accepted
- [ ] background records map to Background only if accepted
- [ ] hard-negative records map to Hard_Negative only if accepted
- [ ] uncertain records map to Uncertain
- [ ] excluded records map to Ignore
- [ ] mapping preserves source lineage outside Git

### Phase 8 — Exclusion rules

Define records that must not continue to I1 mapping.

Exclude records with:

- [ ] unclear permission
- [ ] unclear provenance
- [ ] unclear label meaning
- [ ] unresolved sensitivity issue
- [ ] insufficient evidence
- [ ] duplicate status unresolved
- [ ] no safe neutral mapping
- [ ] do-not-train requirement

### Phase 9 — Review decision

Allowed decisions:

```text
actual_review_passed
actual_review_passed_with_exclusions
needs_operator_info
blocked_by_permission
blocked_by_sensitivity
blocked_by_schema
blocked_by_label_quality
rejected
```

Rules:

- `actual_review_passed` allows later I1 mapping planning.
- `actual_review_passed_with_exclusions` allows later I1 mapping planning only for accepted records.
- Any blocked/rejected status prevents I1 mapping.

## Required review output

The review output must be metadata-only and repo-safe.

Allowed repo-visible output:

- source_id
- source role
- review decision
- aggregate counts
- field names only if safe
- blocker names
- exclusion rule summaries
- next step

Forbidden repo-visible output:

- raw records
- coordinates
- site lists
- source payloads
- source labels as raw values
- imagery references that expose sensitive locations
- private paths
- private hashes

## Stop conditions

Stop immediately if the review requires:

```text
copying records into Git
publishing location-bearing data
creating training rows
creating chips or masks
assembling I2
running training
running inference
changing app/API/frontend code
```

Those require separate explicit approval.

## Result of this checklist

This checklist completes FUTURE-I2-PLAN-2.

Next planning item:

```text
FUTURE-I2-PLAN-3: Create I1 mapping checklist.
```
