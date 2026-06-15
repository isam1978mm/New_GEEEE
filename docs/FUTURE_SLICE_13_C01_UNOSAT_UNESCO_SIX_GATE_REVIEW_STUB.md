# Future Slice 13 C01 — UNOSAT / UNESCO Damage Assessments Six-Gate Review

This is a metadata-only review for continued Slice 13 source discovery.

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
review_status: reviewed_metadata_only
```

## Public metadata reviewed

The continued-discovery scouting note identifies this lead as a possible source of authoritative external / expert-adjudicated cultural-heritage damage assessment evidence.

Metadata-level strengths:

```text
- The source family appears external to the project heuristic.
- The intended evidence is expert-adjudicated damage assessment, not project-generated candidate scoring.
- The source may be useful for positive-class reviewed evidence if source-specific records pass sensitivity, method, license, storage, and I2 compatibility review.
```

Metadata-level limits:

```text
- No source payload, item-level record, coordinate file, site list, image, mask, chip, archive, or dataset file was downloaded or inspected.
- Source-specific access terms were not verified item-by-item.
- Source-specific method evidence was not verified item-by-item.
- Source-specific redaction feasibility was not verified item-by-item.
- The lead remains Gate-1-conditional because cultural-heritage damage records can be location-bearing and sensitive.
```

## Gate 1 — Sensitivity / misuse

```text
status: needs_human_review
```

Rationale:

```text
This is the main blocker. Cultural-heritage damage assessments can include or imply specific place records, damaged-site locations, site identifiers, footprints, or contextual information that could become location-bearing or targeting-use material. Already-public or damaged-status evidence is not automatic approval.
```

Restriction:

```text
No I2 routing is allowed until a source-specific Gate 1 review confirms that later use can avoid public exposure of vulnerable locations, preserved-place records, or targeting-use details.
```

Required before any I2 assembly task:

```text
[ ] identify the exact assessment item or collection without downloading payloads into Git
[ ] confirm whether it contains coordinates, footprints, site identifiers, or other location proxies
[ ] confirm whether public summaries can be safely redacted
[ ] confirm whether use is limited to already-public damaged/destroyed records or another safe subset
[ ] confirm LOCAL_SENSITIVE or FILESYSTEM_ONLY handling for any later private assembly
```

## Gate 2 — Independent evidence

```text
status: needs_item_specific_method_review
```

Rationale:

```text
The evidence is promising because expert damage assessment could be independent of the project heuristic. However, metadata-only scouting does not prove that any specific assessment item has reviewed-tier evidence independent of the same input signals being modeled.
```

Restriction:

```text
This lead must not be treated as positive-class truth until the exact evidence chain is reviewed. Imagery interpretation alone may remain weak-signal-only unless the source method shows expert adjudication and independence strong enough for I2.
```

Required before any I2 assembly task:

```text
[ ] document who produced the assessment
[ ] document how the damage label was produced
[ ] document whether expert adjudication occurred
[ ] document whether the evidence source is independent of the project heuristic and modeled feature stack
[ ] document whether the label is reviewed-tier or weak-signal-only
```

## Gate 3 — Provenance / labeling method

```text
status: insufficient_information
```

Rationale:

```text
Metadata-only scouting does not yet establish source-specific label creation rules, adjudication process, source evidence, version/date, quality controls, disagreement handling, or reproducibility for the records that would enter I2.
```

Required before any I2 assembly task:

```text
[ ] pin source collection and item/version
[ ] record assessment date and source evidence date/window
[ ] record damage-class semantics and any confidence/quality fields
[ ] record expert-review or adjudication method
[ ] record how uncertainty and disagreement are handled
```

## Gate 4 — License / access terms

```text
status: insufficient_information
```

Rationale:

```text
The scouting pass found the source family favorable-looking, but source-specific access terms, citation requirements, redistribution limits, derived-data limits, and private-training compatibility must be confirmed per item or collection.
```

Required before any I2 assembly task:

```text
[ ] confirm source-specific license or access terms
[ ] confirm private ML training / validation use is allowed
[ ] confirm redistribution and derivative-output limits
[ ] record citation / attribution requirements
[ ] record whether a DUA, permission, or restricted access approval is required
```

## Gate 5 — Storage / redaction

```text
status: needs_human_review
```

Rationale:

```text
The source may be public, but any later derived private samples, split groups, labels, chips, or manifests could become sensitive if linked to locations or operator context. Storage and redaction cannot be approved from metadata-only scouting.
```

Restriction:

```text
Any later private assembly must remain outside Git and must be LOCAL_SENSITIVE or FILESYSTEM_ONLY. No public DTO, report, package, or UI artifact may expose sampled locations, local paths, private hashes, site identifiers, or private operator context.
```

## Gate 6 — I2 validator compatibility

```text
status: insufficient_information
```

Rationale:

```text
A positive-class I2 source requires record-level fields that are not available from metadata-only scouting. The lead may be shapeable into the existing I1/I2 schema later, but only after exact reviewed records, evidence source type, label quality, redaction class, split groups, feature references, metadata references, and leakage controls are defined outside Git.
```

Required before any I2 assembly task:

```text
[ ] define source-specific dataset_id and evidence_source_type
[ ] define reviewed label class mapping using neutral labels only
[ ] define label_quality and uncertainty handling
[ ] define redaction_class and storage mode
[ ] define split_group and leakage controls
[ ] define features_ref and metadata_ref without exposing sensitive paths in Git
[ ] confirm compatibility with the existing dataset-pack readiness validator
```

## Six-gate result

```text
sensitivity_misuse: needs_human_review
independent_evidence: needs_item_specific_method_review
provenance_labeling_method: insufficient_information
license_access_terms: insufficient_information
storage_redaction: needs_human_review
i2_validator_compatibility: insufficient_information
```

## Final decision

```text
final_decision: under_review
approved_role: possible positive-class candidate only after source-specific approval
condition: operator/source-specific information required
conditionally_approved_for_I2: false
h3_training_allowed: false
h4_inference_allowed: false
i2_assembly_authorized_now: false
```

## Required operator/source-specific information

Before this candidate can be re-reviewed for I2 routing, the operator must provide or confirm:

```text
[ ] exact assessment item, collection, or source subset to review
[ ] whether the subset is safe under Gate 1 sensitivity/misuse
[ ] source-specific access terms or permission/DUA status
[ ] method notes showing reviewed-tier expert adjudication or independent evidence
[ ] intended neutral label mapping
[ ] redaction/storage plan
[ ] whether later I2 assembly is allowed outside Git only
```

## H3/H4 status

```text
H3 training: blocked
H4 private inference: blocked
```

Reason:

```text
C01 is the strongest open positive-class candidate family, but it does not pass six gates from metadata-only review. H3 still requires an approved positive/target independent-evidence source and a later private I2 pack that passes the existing readiness validator.
```
