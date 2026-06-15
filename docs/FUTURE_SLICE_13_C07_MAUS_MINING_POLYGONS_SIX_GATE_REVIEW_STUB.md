# Future Slice 13 C07 — Maus Mining Polygons Six-Gate Review

This is a metadata-only review for continued Slice 13 source discovery.

It does not download dataset payloads.
It does not include project coordinates, masks, chips, labels, imagery, archives, source payloads, local private paths, private hashes, private candidate registers, or raw site records.
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
intended_role: hard-negative candidate only
lead_status: unverified_lead
review_status: reviewed
```

## Public metadata reviewed

PANGAEA public metadata says:

```text
- The dataset is `Global-scale mining polygons (Version 2)`.
- It was published in 2022 by Maus et al.
- It updates the prior global-scale mining polygons Version 1 dataset.
- It contains polygon features for land used by the global mining industry.
- Covered mining-related features include open cuts, tailing dams, waste rock dumps, water ponds, processing infrastructure, and other mining-related land-cover types.
- The data was derived by visual interpretation of satellite images using the 2019 Sentinel-2 cloudless mosaic as the main input, with Google Satellite and Microsoft Bing imagery consulted as additional information.
- The main dataset is described as a GeoPackage with polygon geometry in WGS84.
- Derived grid datasets are available at coarser grid resolutions.
- Independent validation used stratified random control points for mine / no-mine classes.
- Reported validation metrics include overall accuracy, Kappa, F1 score, producer's accuracy, and user's accuracy.
- The dataset license is Creative Commons Attribution-ShareAlike 4.0 International.
```

No dataset files, GeoPackages, tables, polygons, coordinates, control points, grids, chips, local paths, or private source material were downloaded or inspected for this review.

## Gate 1 — Sensitivity / misuse

```text
status: pass_with_role_restriction
```

Rationale:

```text
The intended role is industrial/mining hard-negative use, not heritage-site discovery or positive-class labeling. Public mining polygons do not by themselves expose protected-place records, private candidate locations, site registers, or vulnerable target lists.
```

Restriction:

```text
This pass applies only to industrial hard-negative use. Later I2 assembly must not publish sampled locations, candidate-adjacent hard negatives, private operator areas, or any public map/list that could reveal private project context.
```

## Gate 2 — Independent evidence

```text
status: pass_with_role_restriction
```

Rationale:

```text
The source is produced by an external research team and represents industrial/mining land-use polygons. For hard-negative training, mining disturbance is useful because it can resemble non-target disturbance while not representing the project positive classes. It must not be treated as positive-class evidence, target absence proof near candidate zones, or reviewed-tier evidence for the project target classes.
```

Restriction:

```text
Approved role is hard-negative only. Later I2 assembly must encode this role explicitly and prevent leakage into positive labels.
```

## Gate 3 — Provenance / labeling method

```text
status: pass
```

Rationale:

```text
Public metadata documents dataset version, publication date, source imagery basis, interpretation method, feature scope, file types, derived grid products, and independent validation design and metrics. This is enough provenance for metadata-only hard-negative source approval.
```

Restriction:

```text
A later I2 assembly task must pin dataset version, selected feature classes or grid representation, temporal assumptions, and hard-negative sampling rules before creating training examples.
```

## Gate 4 — License / access terms

```text
status: pass_with_share_alike_restriction
```

Rationale:

```text
Public metadata states that the dataset is licensed under Creative Commons Attribution-ShareAlike 4.0 International. This is usable for a later private I2 hard-negative source only if the assembly manifest preserves attribution and share-alike obligations.
```

Restriction:

```text
A later I2 assembly task must carry attribution/citation/license metadata, record share-alike implications, and avoid mixing this source into any derived public artifact unless the license obligations are explicitly satisfied.
```

## Gate 5 — Storage / redaction

```text
status: pass
```

Rationale:

```text
The source is public industrial/mining metadata, and the intended role is hard-negative only. Any later private samples, split groups, derived chips, or dataset-pack artifacts must remain LOCAL_SENSITIVE or FILESYSTEM_ONLY outside Git.
```

Restriction:

```text
No public DTO, report, package, or UI artifact may expose sampled locations, local paths, private hashes, or private operator context.
```

## Gate 6 — I2 validator compatibility

```text
status: pass_for_hard_negative_role
```

Rationale:

```text
The candidate can be represented in the existing I1/I2 schema as a hard-negative source if a later I2 task pins dataset version, feature-class scope, grid-or-polygon representation, redaction class, split group rules, evidence source type, feature/metadata references, and leakage controls.
```

Restriction:

```text
This does not authorize I2 assembly now. It only permits opening a later user-approved I2 assembly task for hard-negative examples. It does not unlock H3 without an approved positive/target independent-evidence source.
```

## Six-gate result

```text
sensitivity_misuse: pass_with_role_restriction
independent_evidence: pass_with_role_restriction
provenance_labeling_method: pass
license_access_terms: pass_with_share_alike_restriction
storage_redaction: pass
i2_validator_compatibility: pass_for_hard_negative_role
```

## Final decision

```text
final_decision: conditionally_approved_for_I2
approved_role: hard-negative only
condition: separate user-approved I2 assembly task required
h3_training_allowed: false
h4_inference_allowed: false
i2_assembly_authorized_now: false
```

## Required later I2 constraints

If the operator opens a later I2 assembly task, it must:

```text
[ ] assemble outside Git only
[ ] pin Maus et al. global mining polygons Version 2
[ ] choose polygon or coarser-grid representation explicitly
[ ] define selected feature-class scope for hard-negative examples
[ ] carry attribution / citation / license metadata
[ ] record Creative Commons Attribution-ShareAlike 4.0 implications
[ ] prevent split leakage by spatial group
[ ] exclude candidate-adjacent or uncertain hard negatives unless separately reviewed
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
C07 is approved only for hard-negative role. H3 still requires an approved positive/target independent-evidence source and a later private I2 pack that passes the existing readiness validator.
```
