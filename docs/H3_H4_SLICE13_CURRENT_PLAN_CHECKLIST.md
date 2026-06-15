# H3/H4 Slice 13 Current Plan Checklist

This document records the current H3/H4 decision after D1 parity closeout.

It is intentionally a planning/checklist document only.

It does not create a new dataset-readiness contract.
It does not create a new validator.
It does not start training.
It does not start inference.
It does not authorize dataset download or assembly.

## Current decisions

```text
[x] Park the in-progress OperatorPrivateOverlayPanel work before starting H3/H4 work.
[x] Do not finish the panel now.
[x] Do not leave a dirty tree while starting H3/H4.
[x] Reuse the existing I1/I2 dataset-readiness contract.
[x] Reuse the existing dataset-pack readiness validator.
[x] Do not create `scripts/h3_validate_dataset_readiness.py`.
[x] Do not create a duplicate H3/H4 readiness contract.
```

## Current D1 status

```text
[x] D1 real new.ipynb reference freeze is done.
[x] D1 frozen reference bundle remains local/private and outside Git.
[x] D1 manifest validation passed locally.
[x] Real app-vs-reference inventory coverage passed: 126/126 reference names matched.
[x] Required D1 value-parity families passed:
    [x] DEM
    [x] Report
    [x] Private semantic / secret layers
    [x] SAR/S1
    [x] PAN
```

D1 proves app output reproduction for the accepted parity scope.

D1 does not create supervised training truth.

## Immediate housekeeping

Before any Slice 13/H3/H4 work resumes:

```text
[ ] Stash the in-progress OperatorPrivateOverlayPanel client edit.
[ ] Confirm the stash entry exists.
[ ] Confirm `git status --short` is clean.
[ ] Do not commit, finish, push, or discard the panel work unless separately requested.
```

Suggested local command:

```powershell
git stash push -m "WIP OperatorPrivateOverlayPanel client (parked)" -- frontend-v2/src/app/api/client.ts

git status --short
git stash list
```

If other panel-related files still appear, stash only those exact files. Do not use broad cleanup.

## H3/H4 readiness principle

```text
candidate zone != label
classifier score != label
same app layers != independent evidence
D1 output reproduction != training truth
```

The real unlock is an independent-evidence source that can pass the existing Slice 13 gates and then be shaped into the existing I1/I2 dataset-pack schema outside Git.

Preferred evidence path, in descending order:

```text
1. Field validation or operator-owned verified records under redaction.
2. Authoritative external records with documented source/method and acceptable sensitivity posture.
3. Expert adjudication using evidence the heuristic did not see.
4. Independently produced reference labels with clear method, license, and version.
5. Published imagery-derived datasets only as unverified leads or weak signals unless every gate passes.
```

## Existing H3/H4 path to reuse

Use the existing repo path:

```text
[x] Existing I1/I2 design and dataset-readiness documents.
[x] Existing acceptable-source specification.
[x] Existing Slice 13 source-review checklist.
[x] Existing dataset-pack readiness validator.
```

The readiness validator remains the authority for whether a later private dataset pack is ready for private training.

Expected decision terms:

```text
training_allowed: false until the validator allows it
inference_allowed: false until an approved trained model and private inference gate exist
ready_for_private_training_later: required before H3 starts
```

## Slice 13 status

Current Slice 13 sub-slice order:

```text
[x] 13A — Private candidate register scaffold
[x] 13B — First private source review through the six gates
[x] 13C — DAFA-LS sensitivity/misuse decision record
[ ] 13D — Second known-lead review: arXiv:2602.19608
[ ] 13E — Slice 13 closeout
```

Do not change this order without explicit user approval.

## 13D checklist — second known-lead review

13D is source-review only.

Hard boundaries:

```text
[ ] Do not download dataset payloads.
[ ] Do not download coordinate files, masks, labels, chips, imagery, or site lists.
[ ] Do not create labels.
[ ] Do not assemble an I2 pack.
[ ] Do not train.
[ ] Do not run inference.
[ ] Do not call Earth Engine.
[ ] Do not add ML dependencies.
[ ] Do not expose overlays, coordinates, or location-bearing downloads.
```

Review arXiv:2602.19608 through the six existing Slice 13 gates:

### Gate 1 — Sensitivity / misuse

```text
[ ] Does the source expose sensitive locations?
[ ] Does it include preserved, undefended, vulnerable, or location-bearing records?
[ ] Could misuse enable harm, looting, targeting, or unauthorized access?
[ ] Are coordinates, masks, footprints, site IDs, or map tiles coordinate proxies?
[ ] Would redaction be insufficient?
[ ] Decision recorded: sensitivity_pass / sensitivity_reject / sensitivity_needs_human_review.
```

### Gate 2 — Independent evidence

```text
[ ] Identify how labels were produced.
[ ] Identify which sensor/source produced labels.
[ ] Determine whether evidence is independent of the app heuristic.
[ ] Determine whether evidence is independent of the same Sentinel/Landsat/S1-SAR/DEM/Phase-C-style stack.
[ ] Determine whether labels are merely imagery interpretation of similar signals.
[ ] Determine whether field validation, authoritative records, expert adjudication, or independently produced reference labels exist.
[ ] If labels are not independent, mark rejected or weak-signal-only.
```

### Gate 3 — Provenance / labeling method

```text
[ ] Read methods, not only abstract.
[ ] Record who produced labels.
[ ] Record how labels were produced.
[ ] Record whether labeling rules are reproducible.
[ ] Record whether expert review or adjudication exists.
[ ] Record disagreement handling if available.
[ ] Record label dates and source versions if available.
[ ] If unclear, mark rejected or under_review.
```

### Gate 4 — License / access terms

```text
[ ] Record source license.
[ ] Record access terms.
[ ] Record allowed use and forbidden use.
[ ] Record redistribution limits.
[ ] Record citation requirements.
[ ] Record version or release tag.
[ ] Do not record content hashes until a later approved download/assembly phase.
[ ] If unclear or unacceptable, mark rejected.
```

### Gate 5 — Storage / redaction

```text
[ ] Confirm candidate can be stored outside Git.
[ ] Confirm artifact_class can be LOCAL_SENSITIVE or FILESYSTEM_ONLY.
[ ] Confirm filesystem_only=true.
[ ] Confirm http_servable=false.
[ ] Confirm frontend_visible=false by default.
[ ] Confirm downloadable_via_api=false by default.
[ ] Confirm coordinate proxies can be redacted from public summaries.
[ ] Confirm no public DTO will include coordinates, bounds, local paths, private hashes, labels tied to locations, or raw site records.
[ ] If storage/redaction cannot satisfy these rules, mark rejected.
```

### Gate 6 — I2 validator compatibility

```text
[ ] Can the candidate be represented in an I1/I2 dataset manifest later?
[ ] Can it produce training examples later, outside Git?
[ ] Can every reviewed-tier label have label_evidence_source?
[ ] Can each record include required I1/I2 fields expected by the existing validator?
[ ] Can split leakage rules be satisfied?
[ ] Can temporal holdout be defined?
[ ] Can negative/background and hard-negative counts be defined?
[ ] Can baseline margin and primary metric be preregistered later?
[ ] If not, mark rejected or not_ready_for_I2.
```

13D end states:

```text
[ ] rejected
[ ] conditionally_approved_for_I2
[ ] deferred / needs human review
```

`conditionally_approved_for_I2` is not training approval. It only means a separate, later I2 assembly task may be opened.

## 13E checklist — Slice 13 closeout

13E happens after 13D.

Closeout decision:

```text
[ ] If one source passed all six gates:
    [ ] mark source conditionally_approved_for_I2
    [ ] open a separate later user-approved I2 assembly goal
    [ ] assemble dataset files outside Git only in that later phase
    [ ] run the existing dataset-pack readiness validator in that later phase
    [ ] require ready_for_private_training_later before H3

[ ] If no source passed all six gates:
    [ ] record all known leads rejected/deferred
    [ ] record H3 remains blocked
    [ ] record H4 remains blocked
    [ ] continue discovery or request operator-provided independent evidence
```

13E must not route anything to I2 unless all six gates pass.

## Stop conditions

Stop source review immediately if any are true:

```text
[ ] sensitivity/misuse risk is unacceptable
[ ] labels are not independent of the heuristic and input stack
[ ] provenance or labeling method is unclear
[ ] license or access terms are unacceptable
[ ] storage/redaction cannot satisfy LOCAL_SENSITIVE or FILESYSTEM_ONLY
[ ] candidate cannot be shaped into a valid I2 pack
```

If all known candidates stop or reject, H3 and H4 remain blocked.

## Final status rule

```text
H3 training: blocked until a private I2 pack passes the existing readiness validator.
H4 inference: blocked until H3 produces an approved model and private inference gate passes.
No new H3/H4 code is needed before independent evidence exists.
```
