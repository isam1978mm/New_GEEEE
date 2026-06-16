# Future I2 acceptance criteria

Status: planning only

This document defines strict pass/fail acceptance criteria for future I2 planning.

No data is downloaded by this document.

No source records are inspected by this document.

No I1 rows are created by this document.

No I2 pack is assembled by this document.

No training or inference is started by this document.

H3 and H4 remain blocked.

## Purpose

The purpose of this document is to make future approval and rejection decisions faster, stricter, and less ambiguous.

It answers one question:

```text
What must be true before a source, label set, or future I2 pack can move forward?
```

It does not authorize future dataset construction.

## Current source candidates

Positive source candidate:

- POS-01

Negative/background source candidate:

- C05

Hard-negative source candidates:

- C06
- C07

These are planning candidates only.

Actual dataset review has not started.

## Global acceptance rule

A future I2 dataset pack may move forward only if all of these are true:

- [ ] at least one positive source passes actual dataset review
- [ ] at least one negative/background source passes actual dataset review
- [ ] at least one hard-negative source passes actual dataset review
- [ ] accepted source records can map to I1 fields
- [ ] reviewed-tier labels have independent evidence
- [ ] storage stays private and outside Git
- [ ] split policy prevents leakage
- [ ] validator requirements are satisfied
- [ ] operator explicitly approves actual I2 assembly

If any required item is missing, I2 assembly remains blocked.

## Positive-source acceptance criteria

A positive source passes only if all are true:

- [ ] source has a known owner or authority
- [ ] source has clear permission for private training or validation use
- [ ] source has clear derivative-output permission
- [ ] source is independent of app outputs and heuristic scores
- [ ] source provides target-positive evidence, not just context
- [ ] source method or upstream authority is documented
- [ ] actual records match metadata-level approval assumptions
- [ ] sensitive fields can be handled safely
- [ ] records can map to neutral label `Class_A`
- [ ] uncertain records can be excluded
- [ ] source lineage can be retained outside Git

Automatic rejection conditions:

```text
private training permission is no or unknown
evidence comes only from app output
evidence is only a candidate zone or score
positive label meaning is unclear
sensitive contents cannot be handled safely
records cannot map to I1 required fields
```

## Negative/background-source acceptance criteria

A negative/background source passes only if all are true:

- [ ] source has clear permission for private training or validation use
- [ ] source supports background or non-target examples only
- [ ] source is not used as positive absence truth beyond its approved role
- [ ] source can map to neutral label `Background`
- [ ] source records can be split without leakage
- [ ] source can remain private or metadata-only as required

Automatic rejection conditions:

```text
source is used as positive evidence
source implies target absence beyond its role
permission is no or unknown
schema cannot map to I1
storage cannot remain private
```

## Hard-negative-source acceptance criteria

A hard-negative source passes only if all are true:

- [ ] source represents confusing non-target examples
- [ ] source has clear permission for private training or validation use
- [ ] source can map to neutral label `Hard_Negative`
- [ ] source is not used as target-positive evidence
- [ ] source supports false-positive suppression
- [ ] source can be split without leakage
- [ ] source can remain private or metadata-only as required

Automatic rejection conditions:

```text
source is used as positive evidence
permission is no or unknown
schema cannot map to I1
source does not represent meaningful hard negatives
storage cannot remain private
```

## Label-quality acceptance criteria

Reviewed-tier labels must satisfy all of these:

- [ ] `label_quality` is `reviewed_independent` or `reviewed_adjudicated`
- [ ] `label_evidence_source` is present and non-empty
- [ ] `evidence_source_type` is an independent evidence type
- [ ] `evidence_source_version` is present
- [ ] `evidence_review_method` is present
- [ ] source lineage is retained outside Git

Rejected as reviewed-tier labels:

```text
weak_label
synthetic_or_proxy
uncertain
excluded
```

Allowed non-reviewed uses:

- weak labels may support QA or exploration only
- synthetic/proxy labels may support pipeline tests only
- uncertain labels must not train
- excluded labels must not train

## Permission acceptance criteria

A source passes permission review only if all are true:

- [ ] license or permission is documented
- [ ] private training or validation use is allowed
- [ ] derivative-output handling is allowed or clearly constrained
- [ ] attribution or notification requirements are recorded
- [ ] upstream source rights are not contradictory

Automatic rejection conditions:

```text
private training permission is unknown
private training permission is no
license conflict is unresolved
upstream rights are unresolved
```

## Redaction and storage acceptance criteria

A source passes storage review only if all are true:

- [ ] real contents remain outside Git
- [ ] repo-visible docs contain only safe summaries
- [ ] storage path is outside the repository
- [ ] artifact class is `LOCAL_SENSITIVE` or `FILESYSTEM_ONLY`
- [ ] filesystem-only handling is true
- [ ] HTTP serving is false
- [ ] frontend visibility is false
- [ ] API download is false
- [ ] redaction plan is documented

Automatic rejection conditions:

```text
source requires repo-visible sensitive contents
source requires public serving
source requires frontend exposure
source cannot be stored outside Git
redaction plan is impossible or missing
```

## Split and leakage acceptance criteria

A future I2 pack passes split review only if all are true:

- [ ] group_id prevents same-area leakage
- [ ] near-duplicate examples stay in the same split
- [ ] final holdout exists
- [ ] temporal holdout exists or is explicitly documented
- [ ] threshold selection avoids final holdout
- [ ] split seed or deterministic split rule is recorded
- [ ] class prevalence is recorded by split

Automatic rejection conditions:

```text
group leakage exists
holdout is missing
threshold policy uses final holdout
split policy is undocumented
```

## Validator acceptance criteria

A future I2 pack passes readiness only if the existing validator reports:

```text
dataset_readiness_status: ready_for_private_training_later
training_allowed: true
inference_allowed: false
```

Any other status blocks H3.

Any blocker blocks H3 until resolved.

H4 remains blocked even when I2 readiness passes.

## Minimum manifest acceptance criteria

The manifest must include all required fields from the existing I1/I2 design.

Required I2 quantitative fields:

```text
minimum_holdout_size
minimum_reviewed_tier_label_count_per_class
minimum_negative_background_count
minimum_hard_negative_count
preregistered_baseline_margin
primary_metric
threshold_selection_policy
```

Rules:

- numeric gates must be set before training
- primary metric must be chosen before training
- baseline margin must be numeric
- threshold policy must avoid holdout contamination

## Minimum examples acceptance criteria

The examples file must:

- [ ] be JSONL
- [ ] contain valid JSON objects
- [ ] contain all required training-example fields
- [ ] contain reviewed-tier positive examples with independent evidence
- [ ] contain negative/background examples
- [ ] contain hard-negative examples
- [ ] contain leakage-safe split fields
- [ ] contain private storage references only

## Final stop/go rule

Proceed to future approved I2 assembly only when:

```text
source_inventory: passed
actual_dataset_review: passed
i1_mapping: passed
acceptance_criteria: passed
operator_i2_assembly_approval: yes
```

Proceed to future H3 training consideration only when:

```text
dataset_readiness_status: ready_for_private_training_later
training_allowed: true
```

Proceed to H4 only after a later approved H3 model and private inference gate.

## Current decision

Current project status:

```text
acceptance_criteria_defined
I2 assembly not authorized
H3 blocked
H4 blocked
```

## Stop conditions

Stop immediately if the work requires:

```text
downloading source data
opening source records
creating real I1 rows
assembling I2
running validator on real data
training
inference
changing app/API/frontend code
```

Those require separate explicit approval.

## Result of this checklist

This checklist completes FUTURE-I2-PLAN-6.

Future I2 planning checklist sequence is complete.

Next possible phase, only after explicit approval:

```text
Actual POS-01 dataset review
```
