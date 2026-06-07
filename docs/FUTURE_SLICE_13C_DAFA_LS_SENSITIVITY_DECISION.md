# Future Slice 13C DAFA-LS Sensitivity Decision

Slice 13C records the Gate 1 sensitivity/misuse decision for the DAFA-LS
candidate lead.

It is a decision-record slice only. It does not download data, assemble I2, train,
infer, add ML dependencies, call Earth Engine, expose coordinates or overlays, or
change API, frontend, database, or artifact-serving behavior.

## Candidate

```text
candidate_id: dafa_ls_arxiv_2409_09432
source_name: DAFA-LS public metadata lead
prior_review_reference: future_slice_13b_first_source_review
gate_name: sensitivity_misuse
```

## Decision

Decision:

```text
sensitivity_decision: sensitivity_reject
sensitivity_status: reject
misuse_risk_level: high
final_decision: rejected
i2_routing_allowed: false
h3_training_allowed: false
h4_inference_allowed: false
public_exposure_changes: false
```

DAFA-LS remains blocked from I2 routing, H3 training, and H4 inference. The
committed decision record is redacted and contains only source-level metadata. It
does not include coordinates, raw geometry, site lists, raw labels tied to
locations, local paths, private hashes, or dataset contents.

## Rationale

The safe Gate 1 decision is rejection for this lead because the source is tied to
looting and preserved archaeological-place imagery. The Slice 13 policy ranks
sensitivity/misuse first, and Gate 1 can reject a candidate before license,
method, storage, or validator-fit checks.

Gates 2 through 6 are not changed by Slice 13C. The Slice 13B outcomes remain:

```text
independent_evidence: weak_signal_only
provenance_labeling_method: insufficient_information
license_access_terms: insufficient_information
storage_redaction: needs_human_review
i2_validator_compatibility: insufficient_information
```

## Helper

Implemented module:

```text
app/pipeline/parity/dataset_source_sensitivity_decision.py
```

The helper records one of three allowed sensitivity decisions:

```text
sensitivity_reject
sensitivity_needs_restricted_human_governance
sensitivity_pass_with_restrictions
```

Rules:

- `sensitivity_reject` blocks I2 and marks the candidate `rejected`.
- `sensitivity_needs_restricted_human_governance` blocks I2 and keeps the
  candidate `under_review`.
- `sensitivity_pass_with_restrictions` still does not allow I2 unless Gates 2
  through 6 pass later.
- No Slice 13C decision allows H3, H4, or public exposure.

Report path:

```text
data/runs/<run_id>/manifests/future_slice_13c_dafa_ls_sensitivity_decision.json
```

## Safety Boundary

Slice 13C does not:

- download datasets, imagery, masks, chips, labels, site lists, or archives
- inspect or parse coordinate or site payloads
- create a private candidate register in git
- create an I2 pack
- train a model
- run inference
- add ML dependencies
- call Earth Engine
- collect web pages into the repo
- expose overlays or private source material publicly
- change API, frontend, database, or artifact-serving behavior

## Next Step

Because DAFA-LS is rejected at Gate 1, the next Slice 13 step is to review another
candidate lead through the six gates, or use operator-provided independent
evidence under the same redaction and storage boundaries.

H3 and H4 remain blocked until a later source passes Slice 13, an I2 pack is
assembled outside git, and the I2 validator returns `ready_for_private_training_later`.
