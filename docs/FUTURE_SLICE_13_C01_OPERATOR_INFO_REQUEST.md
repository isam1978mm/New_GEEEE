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

## Completed metadata-only answer

This answer is completed only at source-family metadata level. It does not approve C01 for I2.

```text
candidate_id: unosat_unitar_ch_damage_assessments
source_collection_or_item: UNITAR-UNOSAT / UNESCO cultural-heritage monitoring and damage-assessment source family; exact item/subset not selected yet.
source_reference_or_doi: UNITAR UNOSAT official page and UNITAR news page for UNOSAT/UNESCO cultural heritage monitoring in Ukraine; no DOI identified for the exact reviewed subset.
source_owner_or_authority: UNITAR-UNOSAT / UNESCO collaboration; Ukrainian heritage professionals and authorities appear as stakeholders for the Ukraine training/monitoring context.
access_status: public_metadata_only
permission_or_dua_status: unknown
license_or_terms_summary: source-family public pages are readable, but source-specific data license, reuse terms, derivative-output rights, and ML training permission are not established. Do not assume HDX or public page terms apply to a future item-level source subset.
evidence_type: authoritative_external / expert_adjudicated_independent candidate, but not yet proven at item level.
who_created_assessment: unknown for the exact future I2 subset. Public metadata supports UNOSAT/UNESCO involvement in cultural-heritage monitoring and damage-assessment training, but does not identify a specific reviewed label set for I2.
how_assessment_was_created: source-family metadata says satellite imagery and geospatial technologies are used for heritage documentation, damage assessment, and environmental monitoring. Exact item-level assessment workflow is unknown.
expert_review_or_adjudication: unknown at item level.
evidence_independence_summary: promising but not sufficient. UNOSAT is external to this project and provides satellite analysis for UN agencies and Member States, but item-level independence from the project feature stack and label process still must be proven.
sensitivity_risk_summary: medium-high. Cultural-heritage monitoring/damage assessment can become location-bearing and must be handled as sensitive unless a safe redacted subset is explicitly approved.
redaction_plan_summary: not yet approved. Later review must define a safe subset, neutral labels, private-only storage, and public summaries that omit sensitive location-bearing details.
intended_neutral_label_mapping: TODO after exact source subset is selected; use neutral class names only.
allowed_private_training_use: unknown
allowed_derivative_outputs: unknown
notes: Metadata supports keeping C01 as the strongest positive-candidate family, but it does not satisfy the six gates. C01 must be re-reviewed after exact source subset, terms, method, redaction, and neutral label mapping are known.
```

Public metadata basis:

```text
- UNITAR describes UNOSAT as providing satellite analysis, training, and capacity development to UN funds, programmes, specialized agencies, and Member States.
- UNITAR describes UNOSAT's mission as evidence-based decision making for peace, security, and resilience using geospatial information technologies.
- UNITAR reports that UNOSAT and UNESCO conducted cultural and natural heritage monitoring training in Ukraine with sessions on heritage documentation, damage assessment, environmental monitoring, mapping archaeological sites, physical-damage assessment, flood/fire detection, and ground reporting.
```

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

## Decision rule after operator response

After the operator provides the missing source-specific answers:

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
C01 request: completed at source-family metadata level only
C01 conditionally_approved_for_I2: false
I2 assembly: not authorized
H3 training: blocked
H4 inference: blocked
```
