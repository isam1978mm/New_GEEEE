# Future Slice 13 C01 — Operator / Source-Specific Information Request

This document records exactly what is needed before C01 can be re-reviewed for I2 routing.

C01:

```text
candidate_id: unosat_unitar_ch_damage_assessments
source_name: UNITAR-UNOSAT / UNESCO cultural-heritage damage assessments
current_status: under_review
current_i2_status: not_authorized
current_h3_status: blocked
current_h4_status: blocked
```

This request is metadata-only.

Do not paste or commit coordinates, site lists, raw labels, chips, masks, imagery, source payloads, local private paths, private hashes, private candidate registers, or dataset files.

Do not assemble I2.
Do not start H3 training.
Do not start H4 inference.
Do not call Earth Engine.
Do not add ML dependencies.
Do not change API, frontend, database, or artifact-serving behavior.

## Purpose

C01 is the strongest open positive-candidate family, but it did not pass six gates from metadata-only review.

Before any I2 routing decision can change, the operator must provide source-specific information proving that a safe, approved, reviewed-tier evidence subset exists.

## Required response format

Provide only metadata answers using this structure:

```text
candidate_id:
source_collection_or_item:
source_reference_or_doi:
source_owner_or_authority:
access_status:
permission_or_dua_status:
license_or_terms_summary:
evidence_type:
who_created_assessment:
how_assessment_was_created:
expert_review_or_adjudication:
evidence_independence_summary:
sensitivity_risk_summary:
redaction_plan_summary:
intended_neutral_label_mapping:
allowed_private_training_use:
allowed_derivative_outputs:
notes:
```

Allowed values should be plain text summaries only.

Do not include raw records or source payload content.

## Gate 1 — Sensitivity / misuse information needed

C01 cannot pass Gate 1 until the operator confirms:

```text
[ ] exact source collection or item to review, without committing payloads
[ ] whether the source contains exact coordinates
[ ] whether the source contains footprints, boundaries, or geometry
[ ] whether the source contains site identifiers or names that could identify vulnerable places
[ ] whether the source includes preserved / vulnerable / undefended places
[ ] whether records are limited to already-public damaged/destroyed heritage cases
[ ] whether a redacted summary can be used without exposing sensitive locations
[ ] whether any later private assembly can remain LOCAL_SENSITIVE or FILESYSTEM_ONLY
```

If the source exposes vulnerable-location records that cannot be safely redacted, C01 must remain blocked or rejected.

## Gate 2 — Independent-evidence information needed

C01 cannot pass Gate 2 until the operator confirms:

```text
[ ] who produced the assessment
[ ] what evidence source produced the damage assessment
[ ] whether assessment evidence is independent of the project heuristic
[ ] whether assessment evidence is independent of the same modeled feature stack
[ ] whether expert adjudication occurred
[ ] whether field evidence, authoritative records, or independent expert review exists
[ ] whether the record is reviewed-tier evidence or only weak-signal imagery interpretation
```

Imagery-derived labels on similar visual evidence are not enough by themselves.

## Gate 3 — Provenance / labeling method information needed

C01 cannot pass Gate 3 until the operator confirms:

```text
[ ] source version or release identifier
[ ] assessment date
[ ] source-evidence acquisition date/window
[ ] damage-class definitions
[ ] confidence / quality fields, if any
[ ] expert-review or adjudication workflow
[ ] uncertainty handling
[ ] disagreement handling
[ ] whether label creation rules are reproducible
```

## Gate 4 — License / access terms information needed

C01 cannot pass Gate 4 until the operator confirms:

```text
[ ] source-specific license or access terms
[ ] whether private ML training / validation use is allowed
[ ] whether a DUA, permission, or restricted-access approval is required
[ ] whether derivative outputs are allowed
[ ] whether redistribution is forbidden or limited
[ ] citation / attribution requirements
[ ] whether publication or sharing of trained-model artifacts is restricted
```

## Gate 5 — Storage / redaction information needed

C01 cannot pass Gate 5 until the operator confirms:

```text
[ ] source can be handled outside Git only
[ ] source can be classified LOCAL_SENSITIVE or FILESYSTEM_ONLY
[ ] no source payload will be public DTO-visible
[ ] no source payload will be frontend-visible by default
[ ] no source payload will be downloadable through public APIs
[ ] public summaries can omit locations, bounds, site identifiers, local paths, private hashes, and raw records
[ ] derived labels, chips, samples, and manifests can remain private
```

## Gate 6 — I2 compatibility information needed

C01 cannot pass Gate 6 until the operator confirms:

```text
[ ] source can produce existing I1/I2 training-example rows outside Git
[ ] every reviewed-tier label can include label_evidence_source
[ ] evidence_source_type can be recorded
[ ] neutral label mapping can be used
[ ] label_quality can be recorded
[ ] redaction_class can be recorded
[ ] split_group can be defined without leakage
[ ] temporal holdout can be defined if needed
[ ] features_ref and metadata_ref can be represented without exposing sensitive paths in Git
[ ] the existing dataset_pack_readiness validator can be run later on the private pack
```

## Operator answer template

Use this template when responding:

```text
C01 operator/source-specific answer

candidate_id: unosat_unitar_ch_damage_assessments
source_collection_or_item:
source_reference_or_doi:
source_owner_or_authority:
access_status: public_metadata_only | public_payload_allowed | restricted_access | operator_owned | unknown
permission_or_dua_status: not_needed | needed_not_obtained | obtained | unknown
license_or_terms_summary:
evidence_type: field_validation | authoritative_external | expert_adjudicated_independent | independently_produced_reference | weak_signal_only | unknown
who_created_assessment:
how_assessment_was_created:
expert_review_or_adjudication: yes | no | unknown
evidence_independence_summary:
sensitivity_risk_summary:
redaction_plan_summary:
intended_neutral_label_mapping:
allowed_private_training_use: yes | no | unknown
allowed_derivative_outputs:
notes:
```

## Decision rule after operator response

After the operator provides the metadata-only answers:

```text
[ ] re-review C01 through all six gates
[ ] if all six gates pass, mark conditionally_approved_for_I2
[ ] if any gate remains blocked, keep C01 under_review or reject
[ ] do not assemble I2 until a separate user-approved I2 assembly task exists
[ ] do not start H3/H4 until the existing readiness validator allows it
```

## Current status

```text
C01: under_review
I2 assembly: not authorized
H3 training: blocked
H4 inference: blocked
```
