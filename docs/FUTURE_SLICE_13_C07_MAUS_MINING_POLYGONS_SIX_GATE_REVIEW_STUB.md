# Future Slice 13 C07 — Maus Mining Polygons Six-Gate Review Stub

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
candidate_id: maus_global_mining_polygons_hard_negatives
source_name: Maus et al. 2022 global mining polygons v2
source_type: independently_produced_reference
intended_role: hard-negative candidate
lead_status: unverified_lead
review_status: opened_stub
```

## Scouting basis

```text
evidence_type: independently_produced_reference
independence_assessment: separate team/method; mining or industrial disturbance that is not the target class can suppress false positives
sensitivity_risk: clean industrial/public hard-negative role
license_status: share-alike note requires Gate 4 review
gate_readiness: ready_for_6gate_review
```

## Gate 1 — Sensitivity / misuse

```text
status: pending_review
question: Does industrial/mining hard-negative use expose sensitive locations or vulnerable records?
initial_note: Expected low risk for industrial/public hard-negative role, but must still be reviewed.
```

## Gate 2 — Independent evidence

```text
status: pending_review
question: Is this evidence independent of the app heuristic and same feature stack for the intended hard-negative role?
initial_note: Expected independent for hard-negative use only. It must not be treated as positive-class evidence.
```

## Gate 3 — Provenance / labeling method

```text
status: pending_review
question: Are source methodology, version, temporal coverage, and polygon-generation rules documented well enough for I2 hard-negative use?
```

## Gate 4 — License / access terms

```text
status: pending_review
question: Are access terms, citation requirements, redistribution constraints, share-alike implications, and private-training compatibility acceptable?
```

## Gate 5 — Storage / redaction

```text
status: pending_review
question: Can any later private use remain LOCAL_SENSITIVE or FILESYSTEM_ONLY with no public location-bearing exposure?
```

## Gate 6 — I2 validator compatibility

```text
status: pending_review
question: Can the candidate be represented in the existing I1/I2 schema for hard-negative examples without leakage?
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
