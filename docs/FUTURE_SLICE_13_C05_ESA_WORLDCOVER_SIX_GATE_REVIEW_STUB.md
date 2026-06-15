# Future Slice 13 C05 — ESA WorldCover Six-Gate Review

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
candidate_id: esa_worldcover_landcover_negatives
source_name: ESA WorldCover 10 m landcover
source_type: authoritative_external_dataset
intended_role: negative/background candidate only
lead_status: unverified_lead
review_status: reviewed
```

## Public metadata reviewed

ESA WorldCover public metadata says:

```text
- WorldCover 2020 was produced with algorithm v100.
- WorldCover 2021 was produced with algorithm v200.
- Products are delivered at approximately 10 m resolution.
- Map data can be accessed through public delivery mechanisms.
- ESA WorldCover is provided free of charge and under Creative Commons Attribution 4.0 International terms.
- Publications, models, and derived data products using the dataset require proper acknowledgement / citation.
- Product validation reports are available for the 2020 and 2021 products.
```

No dataset tiles, payloads, source rasters, coordinates, masks, chips, local paths, or private source material were downloaded or inspected for this review.

## Gate 1 — Sensitivity / misuse

```text
status: pass
```

Rationale:

```text
The intended role is negative/background landcover, not heritage-site discovery or positive-class labeling. Public landcover classes do not by themselves expose protected-place records, candidate locations, site registers, or vulnerable target lists. Later I2 assembly must still avoid public location-bearing summaries and must remain outside Git.
```

Restriction:

```text
This pass applies only to broad negative/background use. It does not authorize publishing sampled locations, candidate-adjacent negatives, or any public map/list that could reveal private operator areas.
```

## Gate 2 — Independent evidence

```text
status: pass_with_role_restriction
```

Rationale:

```text
ESA WorldCover is an externally produced authoritative landcover product. It can serve as independent negative/background evidence for broad non-target classes. It must not be treated as positive-class evidence, target absence proof near candidate zones, or reviewed-tier evidence for the project target classes.
```

Restriction:

```text
Approved role is negative/background only. Later I2 assembly must encode this role explicitly and avoid leakage into positive labels.
```

## Gate 3 — Provenance / labeling method

```text
status: pass
```

Rationale:

```text
Public metadata documents product versions, algorithm-version distinction between 2020 and 2021, resolution, delivery format, citation expectations, and validation-report availability. This is enough provenance for a metadata-only negative/background source approval.
```

Restriction:

```text
A later I2 assembly task must pin product year/version and class mapping before creating training examples.
```

## Gate 4 — License / access terms

```text
status: pass
```

Rationale:

```text
Public metadata states that the ESA WorldCover product is free of charge, without restriction of use, and governed by Creative Commons Attribution 4.0 International terms. It also requires proper acknowledgement / citation in publications, models, and data products.
```

Restriction:

```text
A later I2 assembly task must carry attribution/citation metadata and preserve any required license notices in dataset manifests.
```

## Gate 5 — Storage / redaction

```text
status: pass
```

Rationale:

```text
The source is public global landcover metadata, and the intended role is negative/background only. Any later private samples, split groups, derived chips, or dataset-pack artifacts must remain LOCAL_SENSITIVE or FILESYSTEM_ONLY outside Git.
```

Restriction:

```text
No public DTO, report, package, or UI artifact may expose sampled locations, local paths, private hashes, or private operator context.
```

## Gate 6 — I2 validator compatibility

```text
status: pass_for_negative_background_role
```

Rationale:

```text
The candidate can be represented in the existing I1/I2 schema as a negative/background source if a later I2 task pins product version, class mapping, redaction class, split group rules, evidence source type, feature/metadata references, and leakage controls.
```

Restriction:

```text
This does not authorize I2 assembly now. It only permits opening a later user-approved I2 assembly task for negative/background examples. It does not unlock H3 without an approved positive/target evidence source.
```

## Six-gate result

```text
sensitivity_misuse: pass
independent_evidence: pass_with_role_restriction
provenance_labeling_method: pass
license_access_terms: pass
storage_redaction: pass
i2_validator_compatibility: pass_for_negative_background_role
```

## Final decision

```text
final_decision: conditionally_approved_for_I2
approved_role: negative/background only
condition: separate user-approved I2 assembly task required
h3_training_allowed: false
h4_inference_allowed: false
i2_assembly_authorized_now: false
```

## Required later I2 constraints

If the operator opens a later I2 assembly task, it must:

```text
[ ] assemble outside Git only
[ ] pin ESA WorldCover product year/version
[ ] pin class mapping used for negative/background labels
[ ] carry attribution / citation / license metadata
[ ] prevent split leakage by spatial group
[ ] exclude candidate-adjacent or uncertain negatives unless separately reviewed
[ ] keep all derived samples, chips, and manifests LOCAL_SENSITIVE or FILESYSTEM_ONLY as required
[ ] run the existing dataset-pack readiness validator
```

## H3/H4 status

```text
H3 training: blocked
H4 private inference: blocked
```

Reason:

```text
C05 is approved only for negative/background role. H3 still requires an approved positive/target independent-evidence source and a later private I2 pack that passes the existing readiness validator.
```
