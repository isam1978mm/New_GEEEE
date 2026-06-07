# Future Slice 13 — Execution Checklist

This checklist turns `docs/FUTURE_SLICE_13_DATASET_DISCOVERY_AND_SOURCE_APPROVAL.md` into an operator-facing execution plan.

Slice 13 is not training. It is not inference. It is not data download. It is not dataset assembly. It is a source-discovery and source-approval phase that decides whether a candidate source may be routed to the I2 dataset-pack validator.

## Hard Boundary

```text
Future Slice 13 does not:
- download dataset files
- scrape data from the web
- create or commit a dataset
- create or commit labels, chips, coordinates, masks, or site registers
- train a model
- run inference
- download weights
- add PyTorch, TensorFlow, CUDA, or heavy ML dependencies
- call Earth Engine
- expose overlays or coordinates publicly
- change API/frontend/artifact-serving behavior
```

Every candidate starts as:

```text
unverified_lead
```

No candidate is approved because it is public, published, cited, or available on GitHub.

## Slice 13 Sub-Slice Sequence

These sub-slices make the Slice 13 execution order explicit. Do not add new sub-slices or change this order without first telling the user.

```text
[x] 13A — Private candidate register scaffold
[x] 13B — First private source review through the six gates
[x] 13C — DAFA-LS sensitivity/misuse decision record
[ ] 13D — Second known-lead review: arXiv:2602.19608
[ ] 13E — Slice 13 closeout: all known leads rejected/deferred or one routed to I2
```

13D must stay source-review only. 13E must not route anything to I2 unless the candidate passed every Slice 13 gate.

## Phase 13.0 — Setup The Private Review Workspace

Checklist:

```text
[ ] Choose a private dataset root outside git.
[ ] Create a private candidate-register folder outside git.
[ ] Confirm the private root is not inside the repository.
[ ] Confirm no candidate register, coordinate file, label file, site list, chip, mask, or dataset artifact will be committed.
[ ] Confirm artifact class for all review material is LOCAL_SENSITIVE or FILESYSTEM_ONLY.
[ ] Confirm public summaries must not include coordinates, local paths, private hashes, raw labels tied to locations, or candidate file contents.
```

Suggested private layout, outside git:

```text
<PRIVATE_DATASET_ROOT>/
  candidate_register/
    candidates.jsonl
    reviews/
      <candidate_id>/
        sensitivity_review.md
        independence_review.md
        provenance_review.md
        license_review.md
        storage_review.md
        i2_compatibility_review.md
```

Do not commit this folder.

## Phase 13.1 — Candidate Register Schema

Each candidate review record should include:

```text
candidate_id
source_name
source_reference
source_url_or_doi
source_type
lead_status
review_status
sensitivity_status
sensitivity_decision
sensitivity_blocker
independence_status
independence_decision
independence_blocker
provenance_status
provenance_decision
provenance_blocker
license_status
license_decision
license_blocker
storage_status
storage_decision
storage_blocker
i2_compatibility_status
i2_compatibility_decision
i2_compatibility_blocker
final_decision
final_blocker
reviewer
review_date
notes
```

Allowed candidate lifecycle values:

```text
unverified_lead
under_review
rejected
conditionally_approved_for_I2
```

`conditionally_approved_for_I2` is not training approval. It only means the source may be assembled outside git into a private I2 pack for machine validation.

## Phase 13.2 — Discovery Rules

Checklist:

```text
[ ] Record only metadata/provenance/license leads in the candidate register.
[ ] Do not download dataset payloads in Slice 13.
[ ] Do not download coordinate files, masks, labels, chips, imagery, or site lists in Slice 13.
[ ] Do not scrape web pages into the repo.
[ ] Do not store candidate data in git.
[ ] Treat every dataset as unverified_lead until every gate passes.
```

Allowed discovery work:

```text
- identify candidate source metadata
- read abstracts and methods sections
- inspect license text or repository license metadata
- inspect dataset-card or paper methodology text
- record source/version/license/provenance notes in the private register
```

Not allowed in Slice 13:

```text
- bulk download
- dataset mirroring
- chip extraction
- mask extraction
- coordinate parsing
- training-example assembly
- I2 pack creation
```

## Phase 13.3 — Gate 1: Sensitivity / Misuse Review

This gate is first and can reject a candidate on its own.

Checklist:

```text
[ ] Does the source expose sensitive locations?
[ ] Does it include preserved, undefended, vulnerable, or location-bearing heritage records?
[ ] Could misuse of the data enable harm, looting, targeting, or unauthorized access?
[ ] Are coordinates, masks, footprints, site IDs, or map tiles coordinate proxies?
[ ] Would redaction be insufficient to reduce risk?
[ ] If risk is unacceptable, mark rejected and stop review.
```

Decision values:

```text
sensitivity_pass
sensitivity_reject
sensitivity_needs_human_review
```

Rule:

```text
A perfectly licensed and published dataset can still be rejected at Gate 1.
```

## Phase 13.4 — Gate 2: Independent-Evidence Review

Independent evidence means:

```text
independent of our heuristic
AND independent of the same input stack being modeled
```

Checklist:

```text
[ ] Identify how labels were produced.
[ ] Identify which sensor/source was used to produce labels.
[ ] Determine whether label evidence is independent of our Sentinel/Landsat/S1-SAR/DEM/Phase-C feature stack.
[ ] Determine whether labels are merely imagery interpretation of a similar signal.
[ ] Determine whether field validation, authoritative external records, expert adjudication against independent evidence, or independently produced reference labels exist.
[ ] If labels are not independent, mark rejected or weak-signal-only.
```

Important:

```text
Different sensor data may help, but it does not automatically prove independence.
Imagery-derived labels on similar visual evidence are not reviewed-tier evidence by themselves.
```

## Phase 13.5 — Gate 3: Provenance / Labeling-Method Review

Checklist:

```text
[ ] Read the methods section, not only the abstract.
[ ] Record who produced labels.
[ ] Record how labels were produced.
[ ] Record whether labeling rules are reproducible.
[ ] Record whether there was expert review or adjudication.
[ ] Record whether disagreement handling is documented.
[ ] Record whether label dates and source versions are documented.
[ ] If label method is unclear, mark rejected or under_review.
```

## Phase 13.6 — Gate 4: License / Access-Terms Review

Checklist:

```text
[ ] Record source license.
[ ] Record access terms.
[ ] Record allowed use and forbidden use.
[ ] Record redistribution limits.
[ ] Record citation requirements.
[ ] Record version or release tag.
[ ] Record content hash only after a later approved download/assembly phase, not during Slice 13.
[ ] If license/access terms are unclear or unacceptable, mark rejected.
```

## Phase 13.7 — Gate 5: Storage / Redaction Review

Checklist:

```text
[ ] Confirm candidate can be stored outside git.
[ ] Confirm artifact_class can be LOCAL_SENSITIVE or FILESYSTEM_ONLY.
[ ] Confirm filesystem_only=true.
[ ] Confirm http_servable=false.
[ ] Confirm frontend_visible=false by default.
[ ] Confirm downloadable_via_api=false by default.
[ ] Confirm coordinate proxies can be redacted from public summaries.
[ ] Confirm no public DTO will include coordinates, bounds, local paths, private hashes, labels tied to locations, or raw site records.
[ ] If storage/redaction cannot satisfy these rules, mark rejected.
```

## Phase 13.8 — Gate 6: I2 Validator Compatibility

Checklist:

```text
[ ] Can the candidate be represented in an I1/I2 dataset_manifest.json?
[ ] Can it produce training_examples.jsonl later, outside git?
[ ] Can every reviewed-tier label have label_evidence_source?
[ ] Can each record include dataset_id, group_id, split, label_quality, evidence_source_type, acquisition_window, sensor_sources, preprocessing_commit, features_ref, metadata_ref, and redaction_class?
[ ] Can split leakage rules be satisfied?
[ ] Can temporal holdout be defined?
[ ] Can negative/background and hard-negative counts be defined?
[ ] Can baseline margin and primary metric be preregistered later?
[ ] If not, mark rejected or not_ready_for_I2.
```

The field list above is representative, not exhaustive. The authoritative I1/I2 training-example and dataset-manifest schema is defined in `app/pipeline/parity/dataset_pack_readiness.py` and `docs/SPECIAL_TRACK_I_DATASET_TRAINING_DESIGN.md`; defer to those to prevent field-list drift.

## Phase 13.9 — Candidate Decision

Only two end states matter:

```text
rejected
conditionally_approved_for_I2
```

A candidate may be conditionally approved for I2 only if all six gates pass.

Checklist:

```text
[ ] Gate 1 sensitivity/misuse passed.
[ ] Gate 2 independent evidence passed.
[ ] Gate 3 provenance/method passed.
[ ] Gate 4 license/access passed.
[ ] Gate 5 storage/redaction passed.
[ ] Gate 6 I2 compatibility passed.
[ ] Final decision recorded in private candidate register.
[ ] Public summary contains no sensitive details.
```

## Phase 13.10 — Handoff To I2

If a candidate is conditionally approved:

```text
[ ] Open a separate, later user-approved I2 assembly goal.
[ ] Assemble dataset files outside git only.
[ ] Run evaluate_dataset_pack_readiness.
[ ] Require ready_for_private_training_later before opening H3.
```

If no candidate passes:

```text
[ ] Record that H3 remains blocked.
[ ] Record that H4 remains blocked.
[ ] Continue discovery or request operator-provided independent evidence.
```

## Preferred Evidence Path

Preferred evidence sources, in descending order:

```text
1. Field validation or operator-owned verified records under redaction.
2. Authoritative external records with documented source/method and acceptable sensitivity posture.
3. Expert adjudication using evidence our heuristic did not see.
4. Independently produced reference labels with clear method, license, and version.
5. Published imagery-derived datasets only as unverified leads or weak signals unless they pass every gate.
```

Notebook outputs, Phase F outputs, and labels inferred from the same input stack remain weak signals only.

## Worked Lead Review Notes

These leads remain unverified until reviewed through the checklist:

```text
- arXiv:2602.19608
- arXiv:2409.09432 / DAFA-LS
```

For both, expect Gate 1 sensitivity/misuse to be difficult because preserved-site or vulnerable-location data can be high-risk. Do not download, assemble, train on, or infer from these sources during Slice 13.

## Stop Conditions

Stop Slice 13 review for a candidate if:

```text
[ ] sensitivity/misuse risk is unacceptable
[ ] labels are not independent of our heuristic and input stack
[ ] provenance or labeling method is unclear
[ ] license or access terms are unacceptable
[ ] storage/redaction cannot satisfy LOCAL_SENSITIVE or FILESYSTEM_ONLY
[ ] candidate cannot be shaped into a valid I2 pack
```

If all candidates stop or reject, H3 training and H4 private inference remain blocked.

## Completion Criteria For Slice 13

Slice 13 is complete when:

```text
[ ] private candidate register structure exists outside git
[ ] candidate review schema is defined
[ ] at least one candidate source has been reviewed through the six gates, or all currently known leads are explicitly rejected/deferred
[ ] no dataset files were downloaded or committed
[ ] no training or inference was started
[ ] no ML dependencies were added
[ ] no public exposure or artifact-serving change was made
[ ] next action is either I2 assembly for a conditionally approved source, or continued discovery if all candidates are rejected/deferred
```
