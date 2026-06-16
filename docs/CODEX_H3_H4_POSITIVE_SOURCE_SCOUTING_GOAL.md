# Codex Goal — H3/H4 Positive Source Scouting

This is a Codex-ready scouting goal for finding possible positive independent-evidence sources while the operator checks trusted private/authority options.

This is metadata-only discovery.
It must not create data, assemble I2, start training, start inference, add dependencies, or change app behavior.

## Current project state

```text
D1 freeze: done
D1 accepted parity scope: done
Slice 13 known-lead closeout: done
C05 ESA WorldCover: conditionally approved for later I2 negative/background only
C06 Dynamic World: conditionally approved for later I2 hard-negative only
C07 Maus mining polygons: conditionally approved for later I2 hard-negative only
C01 UNOSAT / UNESCO: still under_review, source-specific info required
I2 assembly: not authorized
H3 training: blocked
H4 private inference: blocked
```

## Goal

Find candidate positive independent-evidence sources that could later pass Slice 13 six-gate review.

Positive evidence means a trusted external or field/expert source can support a real positive label, not just background, ranking, or project-generated suspicion.

## Accept candidate source types

```text
field-verified records
authority or government damage records
UN / UNESCO / UNOSAT / UNITAR cultural-heritage damage assessments
expert-adjudicated incident or damage reports
independently produced reference labels with clear method and rights
operator-owned verified records, if only metadata is described
```

## Reject as positive labels

```text
D1 outputs
Phase F scores
candidate zones
classifier outputs
same-app-layer signals
negative/background datasets only
public gazetteers of preserved/vulnerable places
unclear-license sources
sources that expose sensitive records without a safe redaction path
weak imagery-only signals without independent expert review
```

## Hard rules

```text
metadata_only: true
no_payload_downloads: true
no_sensitive_records: true
no_i2_assembly: true
no_training: true
no_inference: true
no_code_changes: true
```

Do not collect or paste record-level material into the repo.
Only record source names, links, owner/authority, method notes, license/access notes, sensitivity notes, missing info, and gate-readiness.

## For each candidate, return this schema

```text
candidate_id:
source_name:
source_link_or_doi:
owner_or_authority:
evidence_type:
why_it_is_positive_evidence:
why_it_is_independent:
method_or_adjudication_notes:
license_or_access_terms:
private_training_permission_known: yes | no | unknown
sensitivity_risk: low | medium | high | unknown
redaction_possible: yes | no | unknown
gate_readiness:
decision: ready_for_6gate_review | needs_operator_info | reject | weak_signal_only
missing_info_needed:
```

## Six gates to pre-screen

```text
G1 sensitivity / misuse
G2 independent evidence
G3 provenance / method
G4 license / access terms
G5 storage / redaction
G6 I2 schema fit
```

## Expected result

A short ranked list of candidate positive sources.

The best candidate should be the one most likely to become a reviewed-tier positive source after human/operator confirmation.

## Important limit

Codex may scout and summarize leads, but Codex must not approve sources.

Final approval still requires a human/operator six-gate review and, later, the existing dataset_pack_readiness validator before H3 can start.

## Current final rule

```text
No approved positive independent evidence -> no real H3.
No approved H3 model -> no real H4.
```
