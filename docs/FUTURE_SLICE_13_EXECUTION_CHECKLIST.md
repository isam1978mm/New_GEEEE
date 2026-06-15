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

These sub-slices make the Slice 13 execution order explicit.

```text
[x] 13A — Private candidate register scaffold
[x] 13B — First private source review through the six gates
[x] 13C — DAFA-LS sensitivity/misuse decision record
[x] 13D — Second known-lead review: arXiv:2602.19608
[x] 13E — Slice 13 closeout: current known leads rejected/deferred; no source routed to I2
```

13E did not route anything to I2 because no current known lead passed every Slice 13 gate.

## Phase 13.0 — Setup The Private Review Workspace

Checklist:

```text
[x] Keep private dataset/candidate material outside git.
[x] Do not commit candidate registers, coordinate files, label files, site lists, chips, masks, or dataset artifacts.
[x] Treat review material as LOCAL_SENSITIVE or FILESYSTEM_ONLY when it exists outside git.
[x] Keep public summaries redacted: no coordinates, local paths, private hashes, raw labels tied to locations, or candidate file contents.
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

`conditionally_approved_for_I2` is not training approval. It only means the source may be assembled outside git into a private I2 pack for machine validation in a separate, later, user-approved task.

## Phase 13.2 — Discovery Rules

Checklist:

```text
[x] Record only metadata/provenance/license leads in repo-visible docs.
[x] Do not download dataset payloads in Slice 13.
[x] Do not download coordinate files, masks, labels, chips, imagery, or site lists in Slice 13.
[x] Do not scrape web pages into the repo.
[x] Do not store candidate data in git.
[x] Treat every dataset as unverified_lead until every gate passes.
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

## Six-Gate Review Checklist

A source can be conditionally approved for I2 only if all six gates pass.

### Gate 1: Sensitivity / Misuse Review

```text
[ ] Does the source expose sensitive locations?
[ ] Does it include preserved, undefended, vulnerable, or location-bearing heritage records?
[ ] Could misuse of the data enable harm, looting, targeting, or unauthorized access?
[ ] Are coordinates, masks, footprints, site IDs, or map tiles coordinate proxies?
[ ] Would redaction be insufficient to reduce risk?
[ ] If risk is unacceptable, mark rejected and stop review.
```

Rule:

```text
A perfectly licensed and published dataset can still be rejected at Gate 1.
```

### Gate 2: Independent-Evidence Review

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

### Gate 3: Provenance / Labeling-Method Review

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

### Gate 4: License / Access-Terms Review

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

### Gate 5: Storage / Redaction Review

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

### Gate 6: I2 Validator Compatibility

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

## Known Lead Results

### DAFA-LS / arXiv:2409.09432

```text
final_decision: rejected
sensitivity_misuse: reject
i2_routing_allowed: false
h3_training_allowed: false
h4_inference_allowed: false
```

Reference:

```text
docs/FUTURE_SLICE_13C_DAFA_LS_SENSITIVITY_DECISION.md
```

### arXiv:2602.19608

```text
final_decision: rejected
sensitivity_misuse: reject
independent_evidence: weak_signal_only
provenance_labeling_method: insufficient_information
license_access_terms: insufficient_information
storage_redaction: needs_human_review
i2_validator_compatibility: insufficient_information
```

Reference:

```text
docs/FUTURE_SLICE_13D_ARXIV_2602_19608_SOURCE_REVIEW.md
```

## 13E Closeout Decision

Closeout path:

```text
[x] Path B — no current known lead passed all six gates.
```

Result:

```text
[x] No current known lead is conditionally_approved_for_I2.
[x] No I2 assembly is authorized from current known leads.
[x] H3 training remains blocked.
[x] H4 private inference remains blocked.
[x] Next unlock is operator-provided or newly discovered independent evidence that can pass the existing Slice 13/I1/I2 path.
```

Reference:

```text
docs/FUTURE_SLICE_13E_CLOSEOUT.md
```

## Handoff To I2

No handoff to I2 is authorized from the current known-lead set.

If a future candidate is conditionally approved:

```text
[ ] Open a separate, later user-approved I2 assembly goal.
[ ] Assemble dataset files outside git only.
[ ] Run evaluate_dataset_pack_readiness.
[ ] Require ready_for_private_training_later before opening H3.
```

If no future candidate passes:

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

## Completion Criteria For Slice 13 Current Known-Lead Set

Slice 13 current known-lead set is complete when:

```text
[x] candidate review schema is defined
[x] known candidate sources have been reviewed or decision-recorded through Slice 13 gates
[x] all current known leads are explicitly rejected/deferred
[x] no dataset files were downloaded or committed
[x] no training or inference was started
[x] no ML dependencies were added
[x] no public exposure or artifact-serving change was made
[x] next action is continued discovery or operator-provided independent evidence
```
