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
[x] Stash/check the in-progress OperatorPrivateOverlayPanel client edit.
[x] Confirm `git status --short` is clean.
[x] Do not commit, finish, push, or discard the panel work unless separately requested.
```

Observed local result:

```text
No local changes to save.
Working tree clean.
Existing unrelated older stashes remain untouched.
```

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
[x] 13D — Second known-lead review: arXiv:2602.19608
[x] 13E — Slice 13 closeout for current known-lead set
```

Do not change this order without explicit user approval.

## 13D result — second known-lead review

13D was source-review only.

Hard boundaries held:

```text
[x] No dataset payloads downloaded.
[x] No coordinate files, masks, labels, chips, imagery, or site lists downloaded.
[x] No labels created.
[x] No I2 pack assembled.
[x] No training started.
[x] No inference started.
[x] No Earth Engine calls added.
[x] No ML dependencies added.
[x] No overlays, coordinates, or location-bearing downloads exposed.
```

Review result for arXiv:2602.19608:

```text
final_decision: rejected
sensitivity_misuse: reject
independent_evidence: weak_signal_only
provenance_labeling_method: insufficient_information
license_access_terms: insufficient_information
storage_redaction: needs_human_review
i2_validator_compatibility: insufficient_information
```

`conditionally_approved_for_I2` was not granted.

## 13E result — Slice 13 closeout

13E closed the current known-lead set.

Closeout decision:

```text
[x] Path B — no current known lead passed all six gates.
```

13E result:

```text
[x] DAFA-LS / arXiv:2409.09432 rejected by Gate 1 sensitivity/misuse.
[x] arXiv:2602.19608 rejected by Gate 1 sensitivity/misuse and other non-passing gates.
[x] No current known lead is conditionally_approved_for_I2.
[x] No I2 assembly is authorized from current known leads.
[x] H3 remains blocked.
[x] H4 remains blocked.
```

13E references:

```text
docs/FUTURE_SLICE_13C_DAFA_LS_SENSITIVITY_DECISION.md
docs/FUTURE_SLICE_13D_ARXIV_2602_19608_SOURCE_REVIEW.md
docs/FUTURE_SLICE_13E_CLOSEOUT.md
```

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
