# Future Slice 13 C06 — Dynamic World Six-Gate Review

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
candidate_id: dynamic_world_landcover_hard_negatives
source_name: Google / WRI Dynamic World landcover
source_type: authoritative_external_dataset
intended_role: hard-negative candidate only
lead_status: unverified_lead
review_status: reviewed
```

## Public metadata reviewed

Google Earth Engine Data Catalog metadata says:

```text
- Dynamic World V1 is a 10 m near-real-time land-use / land-cover dataset.
- It includes class probabilities and labels for nine classes.
- It is available from 2015-06-27 to present.
- It is derived from Sentinel-2 L1C images with cloud percentage less than or equal to 35%.
- Predictions are cloud / cloud-shadow masked using multiple cloud-detection methods.
- Each Dynamic World image corresponds to an individual Sentinel-2 L1C asset.
- Pixels should be selected confidently by thresholding the top-1 class probability.
- All probability bands except the label band collectively sum to 1.
- The label band is the index of the band with the highest estimated probability.
- The dataset is licensed under CC-BY 4.0 with Dynamic World attribution requirements.
```

No dataset tiles, payloads, source rasters, coordinates, masks, chips, local paths, or private source material were downloaded or inspected for this review.

## Gate 1 — Sensitivity / misuse

```text
status: pass
```

Rationale:

```text
The intended role is hard-negative landcover, not heritage-site discovery or positive-class labeling. Public landcover classes do not by themselves expose protected-place records, candidate locations, site registers, or vulnerable target lists. Later I2 assembly must still avoid public location-bearing summaries and must remain outside Git.
```

Restriction:

```text
This pass applies only to hard-negative use. It does not authorize publishing sampled locations, candidate-adjacent negatives, or any public map/list that could reveal private operator areas.
```

## Gate 2 — Independent evidence

```text
status: pass_with_role_restriction
```

Rationale:

```text
Dynamic World is an externally produced landcover product with class probabilities and labels generated independently from the project classifier. It can serve as independent hard-negative evidence for broad non-target classes such as built, bare, vegetation, water, or other landcover contexts that may resemble disturbance. It must not be treated as positive-class evidence, target absence proof near candidate zones, or reviewed-tier evidence for the project target classes.
```

Restriction:

```text
Approved role is hard-negative only. Later I2 assembly must encode this role explicitly, apply confidence thresholds, and avoid leakage into positive labels.
```

## Gate 3 — Provenance / labeling method

```text
status: pass
```

Rationale:

```text
Public metadata documents source sensor lineage, date range, cloud filtering, cloud masking, per-image pairing with Sentinel-2 L1C source assets, class probability semantics, label-band semantics, class list, and algorithm / QA version image properties. This is enough provenance for metadata-only hard-negative source approval.
```

Restriction:

```text
A later I2 assembly task must pin source date window, class mapping, top-1 probability threshold, algorithm-version handling, and QA constraints before creating training examples.
```

## Gate 4 — License / access terms

```text
status: pass
```

Rationale:

```text
Public metadata states that Dynamic World V1 is licensed under CC-BY 4.0 and requires attribution to the Dynamic World Project by Google in partnership with National Geographic Society and the World Resources Institute. The metadata also notes modified Copernicus Sentinel data and points to the Sentinel data legal notice.
```

Restriction:

```text
A later I2 assembly task must carry attribution/citation metadata, preserve required license notices, and record Sentinel data notice handling in dataset manifests.
```

## Gate 5 — Storage / redaction

```text
status: pass
```

Rationale:

```text
The source is public global landcover metadata, and the intended role is hard-negative only. Any later private samples, split groups, derived chips, or dataset-pack artifacts must remain LOCAL_SENSITIVE or FILESYSTEM_ONLY outside Git.
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
The candidate can be represented in the existing I1/I2 schema as a hard-negative source if a later I2 task pins date window, class mapping, probability threshold, algorithm / QA version handling, redaction class, split group rules, evidence source type, feature/metadata references, and leakage controls.
```

Restriction:

```text
This does not authorize I2 assembly now. It only permits opening a later user-approved I2 assembly task for hard-negative examples. It does not unlock H3 without an approved positive/target evidence source.
```

## Six-gate result

```text
sensitivity_misuse: pass
independent_evidence: pass_with_role_restriction
provenance_labeling_method: pass
license_access_terms: pass
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
[ ] pin Dynamic World source date window
[ ] pin selected class mapping for hard-negative examples
[ ] define top-1 probability threshold and cloud / QA constraints
[ ] carry attribution / citation / license metadata
[ ] record Sentinel data notice handling
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
C06 is approved only for hard-negative role. H3 still requires an approved positive/target independent-evidence source and a later private I2 pack that passes the existing readiness validator.
```
