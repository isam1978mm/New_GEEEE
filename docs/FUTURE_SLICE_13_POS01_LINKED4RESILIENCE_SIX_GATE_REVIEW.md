# Future Slice 13 POS-01 — Linked4Resilience Six-Gate Review

This is a metadata-only six-gate review for POS-01.

This file is documentation only.
It does not create data, assemble I2, start training, start inference, add dependencies, or change app behavior.

No source payloads, record-level material, private operator records, imagery, masks, chips, archives, or training labels are added here.

## Candidate

```text
candidate_id: POS-01
source_name: Linked4Resilience Annotated Dataset of Damaged Cultural Sites and Infrastructures during the Russian invasion of Ukraine
source_link_or_doi: https://zenodo.org/records/14569340
source_type: annotated damaged cultural-site / infrastructure dataset
intended_role: possible positive independent-evidence source
review_status: metadata_only_review_complete
```

## Public metadata reviewed

Public Zenodo metadata says:

```text
- Published December 29, 2024, version v1.
- Resource type: Dataset.
- Title: Annotated Dataset of Damaged Cultural Sites and Infrastructures during the Russian invasion of Ukraine.
- The dataset is associated with the Linked4Resilience paper presented at SCIA 2024.
- The dataset consists of annotated cultural sites damaged in Ukraine during the Russian invasion.
- UNESCO and ScienceAtRisk webpages are identified as source families.
- Of 351 damaged cultural properties published by UNESCO, 211 met the authors' criteria and were included.
- Annotation criteria and other details are in the paper.
- The description states: license is CC-BY NC 4.0 and authors should be informed of derivation/use.
- The Zenodo rights section lists Creative Commons Attribution 4.0 International.
- Files are listed on the public metadata page, but no files were downloaded or inspected for this review.
```

Codex scouting reported POS-01 as the closest package-like positive-source lead, with blockers around license ambiguity, private-training permission, sensitivity/redaction, source derivation rights, and H3/H4 target fit.

## Gate 1 — Sensitivity / misuse

```text
status: needs_human_review
```

Rationale:

```text
The candidate concerns damaged cultural sites and infrastructures. Even though the source is public metadata, the dataset is likely location-bearing or linkable to sensitive cultural-property records. Gate 1 cannot pass without a safe-subset and redaction decision.
```

Still needed:

```text
[ ] confirm whether the intended subset contains coordinates, geometry, names, identifiers, or other location proxies
[ ] decide whether the subset is safe because it is already-public damaged/destroyed material, or whether it remains too sensitive
[ ] define redaction plan before any private data handling
[ ] ensure no public output exposes sensitive review context
```

## Gate 2 — Independent evidence

```text
status: pass_as_candidate_with_caveat
```

Rationale:

```text
The source is external to this project and is derived from UNESCO and ScienceAtRisk source families, not from project outputs, candidate zones, classifier scores, or same-app-layer signals. It is therefore a plausible independent positive evidence candidate.
```

Caveat:

```text
Independence is not final until the paper/source method confirms how records were selected, annotated, and adjudicated, and whether the labels are reviewed-tier evidence rather than weak copied source assertions.
```

## Gate 3 — Provenance / labeling method

```text
status: insufficient_information
```

Rationale:

```text
Zenodo metadata says the annotation criteria and other details are in the paper, but this review did not inspect payload contents and does not yet establish exact label rules, reviewer workflow, uncertainty handling, or suitability for H3/H4 target definitions.
```

Still needed:

```text
[ ] review the paper/method notes at metadata level
[ ] document inclusion/exclusion criteria
[ ] document annotator/reviewer workflow
[ ] document class semantics and confidence/quality fields
[ ] decide whether the dataset supports the intended H3/H4 positive label or only generic damaged-site context
```

## Gate 4 — License / access terms

```text
status: blocker
```

Rationale:

```text
The license metadata is internally inconsistent at the source page level: the description says CC-BY NC 4.0, while the Zenodo rights section lists CC BY 4.0. Private ML training permission is not established, and the authors request being informed of derivation and use.
```

Still needed:

```text
[ ] resolve CC-BY-NC-4.0 vs CC-BY-4.0 conflict
[ ] confirm whether private ML training / validation use is allowed
[ ] confirm whether source derivation from UNESCO / ScienceAtRisk permits this use
[ ] record attribution, notification, derivative-output, and redistribution requirements
```

## Gate 5 — Storage / redaction

```text
status: needs_human_review
```

Rationale:

```text
Even if later use becomes legally allowed, any derived private samples, manifests, split groups, labels, or review artifacts must be handled outside Git with strict redaction. No storage/redaction plan is approved yet.
```

Still needed:

```text
[ ] define storage mode
[ ] define redaction class
[ ] define public-summary limits
[ ] define private artifact handling rules
[ ] confirm no sensitive source-derived content enters public app outputs
```

## Gate 6 — I2 validator compatibility

```text
status: insufficient_information
```

Rationale:

```text
The candidate may be shapeable into existing I1/I2 rows, but this review has not established exact source records, neutral label mapping, label quality, split groups, temporal holdout, feature references, metadata references, or leakage controls.
```

Still needed:

```text
[ ] define dataset_id
[ ] define evidence_source_type
[ ] define neutral label mapping
[ ] define label_quality and uncertainty rules
[ ] define redaction_class
[ ] define split_group rules
[ ] define validator-ready private metadata fields
```

## Six-gate summary

```text
sensitivity_misuse: needs_human_review
independent_evidence: pass_as_candidate_with_caveat
provenance_labeling_method: insufficient_information
license_access_terms: blocker
storage_redaction: needs_human_review
i2_validator_compatibility: insufficient_information
```

## Final decision

```text
POS-01: under_review
positive_source_approved: false
conditionally_approved_for_I2: false
i2_assembly_authorized_now: false
h3_training_allowed: false
h4_inference_allowed: false
```

## Plain English result

```text
POS-01 is a good lead.
POS-01 is not approved yet.
The biggest immediate blocker is license / private-training permission.
The second blocker is sensitivity / redaction.
The third blocker is method and target-fit detail.
```

## Next unlock for POS-01

Before POS-01 can be re-reviewed toward conditional I2 approval, the operator must resolve:

```text
[ ] Which license controls the usable source subset: CC-BY-NC-4.0 or CC-BY-4.0?
[ ] Is private ML training / validation allowed?
[ ] Are derivative outputs allowed, and under what terms?
[ ] Do UNESCO / ScienceAtRisk derivation rights permit this use?
[ ] Can a safe redacted subset be defined?
[ ] Does the method support reviewed-tier positive labels for the H3/H4 target?
```

## Current H3/H4 status

```text
H3 training: blocked
H4 private inference: blocked
```

Reason:

```text
No positive/target independent-evidence source is approved yet. C05/C06/C07 remain useful only for later negative/background or hard-negative roles.
```
