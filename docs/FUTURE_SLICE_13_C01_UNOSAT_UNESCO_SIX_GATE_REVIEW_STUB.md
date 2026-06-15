# Future Slice 13 C01 — UNOSAT / UNESCO Damage Assessments Six-Gate Review Stub

This is a metadata-only review stub for continued Slice 13 source discovery.

It does not download dataset payloads.
It does not include coordinates, masks, chips, labels, imagery, archives, source payloads, local private paths, private hashes, private candidate registers, or raw site records.
It does not assemble an I2 pack.
It does not start H3 training.
It does not start H4 inference.
It does not call Earth Engine.
It does not add ML dependencies.
It does not change API, frontend, database, or artifact-serving behavior.

## Candidate

```text
candidate_id: unosat_unitar_ch_damage_assessments
source_name: UNITAR-UNOSAT / UNESCO cultural-heritage damage assessments
source_type: authoritative_external_dataset / expert_adjudication_independent_evidence
intended_role: possible positive-class independent evidence candidate
lead_status: unverified_lead
review_status: opened_stub
```

## Scouting basis

```text
evidence_type: authoritative_external_dataset / expert_adjudication_independent_evidence
independence_assessment: UN expert damage adjudication appears independent of the app heuristic; confirm method independence at Gate 3
sensitivity_risk: medium-high; site-located damage material requires redaction and careful Gate 1 review
license_status: favorable-looking but must be confirmed per item
gate_readiness: ready_for_6gate_review, Gate-1-conditional
```

## Gate 1 — Sensitivity / misuse

```text
status: pending_review
question: Can the source be reviewed and later handled without exposing vulnerable locations, preserved-place records, or targeting-use details?
initial_note: Gate 1 is conditional and must be decided before any I2 routing. Redaction and already-public/damage-assessment rationale are not automatic approval.
```

## Gate 2 — Independent evidence

```text
status: pending_review
question: Are expert damage assessments independent of the app heuristic and the same input stack being modeled?
initial_note: Potentially positive, but must be proven by source method and evidence chain.
```

## Gate 3 — Provenance / labeling method

```text
status: pending_review
question: Are label creation, expert adjudication, source evidence, version/date, and disagreement handling documented well enough for reviewed-tier I2 use?
```

## Gate 4 — License / access terms

```text
status: pending_review
question: Are source-specific access terms, citation requirements, redistribution constraints, and private-training compatibility acceptable?
```

## Gate 5 — Storage / redaction

```text
status: pending_review
question: Can any later private use remain LOCAL_SENSITIVE or FILESYSTEM_ONLY with no public location-bearing exposure?
```

## Gate 6 — I2 validator compatibility

```text
status: pending_review
question: Can the candidate be represented in the existing I1/I2 schema for reviewed-tier examples without leakage?
```

## Current decision

```text
final_decision: under_review
conditionally_approved_for_I2: false
h3_training_allowed: false
h4_inference_allowed: false
i2_assembly_authorized: false
```

## Next step

Complete the six-gate metadata review. Only if all six gates pass may a separate, later, user-approved I2 assembly task be opened.
