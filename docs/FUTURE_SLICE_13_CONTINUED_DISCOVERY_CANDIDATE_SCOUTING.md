# Future Slice 13 Continued Discovery Candidate Scouting

This document records the 13E-authorized continued source discovery pass.

This is metadata-only scouting.

It does not download dataset payloads.
It does not include coordinates, masks, chips, labels, imagery, archives, source payloads, local private paths, private hashes, private candidate registers, or raw site records.
It does not assemble an I2 pack.
It does not start H3 training.
It does not start H4 inference.
It does not call Earth Engine.
It does not add ML dependencies.
It does not change API, frontend, database, or artifact-serving behavior.

The existing I1/I2 contract and `app/pipeline/parity/dataset_pack_readiness.py` validator remain authoritative.
No duplicate contract or duplicate readiness validator is created.

## State

```text
D1: done
D1 parity: accepted scope done
Slice 13 current known leads: closed
H3: blocked
H4: blocked
I2 assembly: not authorized
```

## Graph rule

```text
IndependentEvidence -> Slice13_6Gates -> if_all_pass -> later_I2_assembly -> dataset_pack_readiness -> ready_for_private_training_later -> H3
H3_approved_model -> private_inference_gate -> H4
```

Weak-signal-only inputs are not labels:

```text
D1_outputs -> weak_signal_only -> NOT labels
PhaseF_scores -> candidates_only -> NOT labels
candidate_zones -> candidates_only -> NOT labels
same_app_layers -> weak_signal_only -> NOT independent evidence
```

## Candidate summary

### C01 — unosat_unitar_ch_damage_assessments

Source:

```text
UNITAR-UNOSAT / UNESCO cultural-heritage damage assessments
Reference: HDX UNITAR-UNOSAT organization page
```

Scouting status:

```text
evidence_type: authoritative_external_dataset / expert_adjudication_independent_evidence
independence_assessment: UN expert damage adjudication appears independent of the app heuristic; confirm method independence at Gate 3.
sensitivity_risk: medium-high; site-located damage material requires redaction and careful Gate 1 review.
license_status: favorable-looking but must be confirmed per item.
gate_readiness: ready_for_6gate_review, Gate-1-conditional
decision: ready_for_6gate_review
role: possible positive-class independent evidence candidate
```

### C02 — eamena_disturbance_threat_records

Source:

```text
EAMENA Arches disturbance/threat records
Reference: EAMENA database and ethics publication metadata
```

Scouting status:

```text
evidence_type: authoritative_external_dataset / expert_adjudication_independent_evidence
independence_assessment: expert condition scoring, but substantially remote-sensing-derived; confirm at Gate 3.
sensitivity_risk: high; access-tiered and location-bearing heritage records create targeting-map risk.
license_status: tiered registration; ML reuse rights not established; DUA likely required.
gate_readiness: needs_operator_info
decision: needs_operator_info
```

### C03 — asor_chi_incident_reports

Source:

```text
ASOR Cultural Heritage Initiatives incident reports
Reference: ASOR CHI reports page
```

Scouting status:

```text
evidence_type: expert_adjudication_independent_evidence / field_validation
independence_assessment: strong where ground-based reports exist; non-imagery evidence axis.
sensitivity_risk: high; structured geodata access is restricted and public reports are redacted.
license_status: reuse for structured data requires permission/access review.
gate_readiness: needs_operator_info
decision: needs_operator_info
```

### C04 — operator_field_verified_records

Source:

```text
Operator or authority field-survey records under DUA or ownership.
```

Scouting status:

```text
evidence_type: field_validation / authoritative_external_dataset
independence_assessment: strongest preferred path if operator confirms existence, authorization, and redaction handling.
sensitivity_risk: manageable only under LOCAL_SENSITIVE / FILESYSTEM_ONLY storage and approved redaction.
license_status: depends on ownership or DUA.
gate_readiness: needs_operator_info
decision: needs_operator_info
role: preferred positive evidence path
```

### C05 — esa_worldcover_landcover_negatives

Source:

```text
ESA WorldCover 10 m landcover
Reference: ESA WorldCover data-access page
```

Scouting status:

```text
evidence_type: authoritative_external_dataset
independence_assessment: independent landcover classification; negative/background role only.
sensitivity_risk: clean for negative/background use.
license_status: clean-looking; confirm exact terms during Gate 4.
gate_readiness: ready_for_6gate_review
decision: ready_for_6gate_review
role: negative/background candidate
```

### C06 — dynamic_world_landcover_hard_negatives

Source:

```text
Google / WRI Dynamic World landcover
Reference: Dynamic World paper DOI metadata
```

Scouting status:

```text
evidence_type: authoritative_external_dataset
independence_assessment: independent landcover source; hard-negative role for non-target ground that may resemble disturbance.
sensitivity_risk: clean for hard-negative use.
license_status: clean-looking; confirm exact terms during Gate 4.
gate_readiness: ready_for_6gate_review
decision: ready_for_6gate_review
role: hard-negative candidate
```

### C07 — maus_global_mining_polygons_hard_negatives

Source:

```text
Maus et al. 2022 global mining polygons v2
Reference: PANGAEA DOI metadata
```

Scouting status:

```text
evidence_type: independently_produced_reference
independence_assessment: separate team/method; mining or industrial disturbance that is not the target class can suppress false positives.
sensitivity_risk: clean industrial/public hard-negative role.
license_status: share-alike note requires Gate 4 review.
gate_readiness: ready_for_6gate_review
decision: ready_for_6gate_review
role: hard-negative candidate
```

### C08 — acled_conflict_events_context

Source:

```text
ACLED conflict events
Reference: ACLED terms-of-use page
```

Scouting status:

```text
evidence_type: independently_produced_reference, context only
independence_assessment: strong non-imagery axis but coarse and not target-specific.
sensitivity_risk: moderate.
license_status: non-commercial / registration / EULA constraints need review.
gate_readiness: weak_signal_only
decision: weak_signal_only
role: context/corroboration only
```

## Excluded or unchanged

```text
[x] DAFA-LS / arXiv:2409.09432 remains Gate-1 rejected.
[x] arXiv:2602.19608 remains Gate-1 rejected.
[x] Public coordinate datasets of preserved sites and site gazetteers remain Gate-1/Gate-2 risks.
[x] D1 outputs, Phase F scores, candidate zones, and same-app layers remain not labels.
```

## Recommended next reviews

Open metadata-only six-gate reviews for:

```text
[ ] C05 — ESA WorldCover negative/background role
[ ] C06 — Dynamic World hard-negative role
[ ] C07 — Maus mining polygons hard-negative role
[ ] C01 — UNOSAT/UNESCO damage assessments, Gate-1-conditional positive candidate
```

Request operator information later for:

```text
[ ] C02 — EAMENA access / DUA / subset details
[ ] C03 — ASOR CHI structured-data access / permission details
[ ] C04 — operator/authority field-record existence, ownership, and authorization
```

## Status after scouting

```text
H3 training: blocked
H4 private inference: blocked
I2 assembly: not authorized
Next unlock: one source must pass a metadata-only six-gate Slice 13 review before a separate I2 assembly task can be opened.
```
