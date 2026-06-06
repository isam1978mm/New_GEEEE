# ML Data And Training Readiness Plan

This document explains when model training, inference, model weights, ML dependencies, app integration, overlay exposure, and Tesla-flow work may happen.

It is a reading and planning document only.

It does not start Special Track H, I, or J.

It does not implement training, inference, model weights, public overlays, app API integration, or Tesla-flow runtime behavior.

## Current Position

The implementation roadmap has completed:

- Phase A: map point picker and ROI/grid preview
- Phase B: controlled backend Earth Engine planning flow
- Phase C: first defensible semantic feature writer slice
- Phase D: first private map-artifact writer slice
- Phase E: private frozen-reference verifier
- Phase F: private neutral CLI classifier
- Special Track G1: controlled location overlay policy
- Special Track G2: operator-only generated-overlay UI design

Remaining later tracks:

- Special Track H: deep-learning model feasibility with good data and weights
- Special Track I: training cells with a real dataset
- Special Track J: full Tesla inference-flow decomposition and implementation decision

## Plain-English Rule

No real ML work should happen until the data gate is satisfied.

The project should not train, infer, download weights, add required ML dependencies, connect model outputs to API/frontend, expose generated overlay locations, or port the Tesla flow as a single engine until the required design and data gates pass.

## When Each Deferred Item Can Happen

| Deferred item | Earliest allowed stage | Required gate |
|---|---|---|
| Train a model | After H1 and I1 | Dataset schema, labels, split policy, metrics, and storage policy accepted |
| Run inference | After a trained or approved-weight model exists | Private CLI inference boundary and evaluation criteria accepted |
| Download model weights | After H1 weights policy | License, version, source, hash, storage, and reproducibility policy accepted |
| Add PyTorch/TensorFlow or similar | After H1 dependency policy | Optional dependency group only; normal app startup must not require it |
| Connect model output to API/frontend | After private CLI evaluation passes | Access control, redaction, DTO, audit, and exposure policy accepted |
| Generated location overlays in UI | After G2 implementation approval | Operator-only auth, role checks, per-run authorization, audit, and default-off config |
| Public location overlays | After a separate public-exposure approval | Serving policy, audit, redaction, and user approval accepted |
| Full Tesla flow | After J1 decomposition | Split into small approved modules; no single monolithic engine |

## What H1 Should Decide

Special Track H1 should answer:

1. Which notebook model attempts exist?
2. Which model paths are realistic?
3. Which paths are blocked by missing data?
4. Which paths are blocked by missing weights?
5. Which dependencies are acceptable?
6. Which metrics prove usefulness?
7. Which outputs stay private?
8. Which candidate should be the first ML implementation path?

H1 should not train or run inference.

H1 should produce:

- a model-attempt inventory
- candidate model ranking
- data requirements
- weights policy
- dependency policy
- metrics policy
- private inference boundary
- blockers and next actions

## What I1 Should Decide

Special Track I1 should define the real training dataset.

I1 should answer:

1. What is one training example?
2. What is one label?
3. Who or what provides labels?
4. What label quality levels exist?
5. How are train, validation, and test splits made?
6. How do we prevent geographic leakage?
7. Where is the dataset stored?
8. What metadata is required?
9. What is allowed in git and what must stay outside git?
10. What minimum dataset size is required before training?

I1 should not train.

I1 should produce:

- dataset schema
- label schema
- label QA policy
- split policy
- metadata policy
- storage policy
- dataset readiness checklist

## What J1 Should Decide

Special Track J1 should decompose the full Tesla inference flow.

J1 should answer:

1. What are all notebook substeps?
2. Which substeps are data acquisition?
3. Which substeps are grid alignment?
4. Which substeps are feature writers?
5. Which substeps are classifier logic?
6. Which substeps are model attempts?
7. Which substeps are map artifacts?
8. Which substeps are overlay or UI related?
9. Which substeps are duplicate or unsupported?
10. Which substeps should become future implementation slices?

J1 should not implement the runtime flow.

J1 should prevent copying the full Tesla flow as one large app engine.

## Training Data: What To Train On

A real training dataset should contain examples built from app-controlled, versioned inputs.

Good training inputs may include:

- Sentinel-2 bands or derived indices
- Landsat bands or derived indices
- Sentinel-1 VV/VH support layers
- DEM and terrain derivatives
- selected Phase C semantic feature layers
- grid metadata
- ROI/chip metadata
- acquisition date and sensor metadata
- preprocessing version
- pipeline commit hash

The notebook outputs should not be treated as ground truth by themselves.

Notebook outputs may be used as:

- weak signals
- candidate features
- review hints
- QA inputs
- reference comparison inputs

They should not be the only source of labels.

## Label Requirements

Labels must be neutral.

Allowed label style:

- Class_A
- Class_B
- Class_C
- Class_D

A label record should include:

- sample id
- class label
- label source
- label quality level
- reviewer or source reference when available
- timestamp or version
- notes

Label quality levels should distinguish:

- reviewed
- weak_label
- synthetic_or_proxy
- uncertain
- excluded

Training should start only after enough reviewed or accepted-quality labels exist.

## Negative And Background Examples

The dataset must include negative/background examples.

These should include:

- visually similar non-class areas
- different soil/terrain/vegetation cases
- urban/background cases if relevant
- sensor-noise or cloud/shadow edge cases
- false-positive-like examples from earlier heuristics

Without negative/background examples, a model can learn to over-score everything.

## Split Policy

Train/validation/test splits should be geographic, not random pixels.

Recommended split logic:

- training areas
- validation areas
- final holdout areas

Do not allow the same local area, chip family, or near-duplicate pixels to appear in both train and test.

The final holdout set should stay untouched until evaluation.

## First Model Recommendation

The first practical model should not be a large segmentation or object-detection model.

Recommended first model:

- private probability classifier over verified feature summaries

Why:

- easier to validate
- lower dependency risk
- works with tabular feature summaries
- can stay CLI-only and private
- easier to calibrate
- easier to compare against a frozen reference

Later model options may include:

- CNN over fixed raster chips
- segmentation model over labeled masks
- object detector over bounding-box labels

Those later options need much stronger datasets.

## Example Training Row

```json
{
  "schema_version": "training_example_v1",
  "sample_id": "sample_0001",
  "area_id": "area_001",
  "split": "train",
  "label": "Class_A",
  "label_quality": "reviewed",
  "features": {
    "semantic_feature_1_mean": 0.62,
    "semantic_feature_2_mean": 0.41,
    "semantic_feature_3_mean": 0.55,
    "sar_vv_mean": -12.3,
    "sar_vh_mean": -18.7,
    "dem_slope_mean": 4.2
  },
  "metadata": {
    "pixel_size_m": 10,
    "grid_version": "local_grid_v1",
    "preprocessing_commit": "<commit-sha>",
    "sensor_window": "<date-range>"
  }
}
```

The placeholders in this example are documentation placeholders only. Codex prompts must replace them with real values before execution.

## Model Weights Policy

No model weights should be committed to git.

Any future model weights must have:

- approved source
- license review
- version pin
- sha256 hash
- storage path outside git
- reproducibility notes
- dependency requirements
- model card or internal equivalent

Random or unpinned model downloads should not be used.

## Dependency Policy

ML dependencies should be optional.

The normal app should not require PyTorch, TensorFlow, CUDA, or other heavy ML packages just to start.

Recommended structure:

- base app dependencies remain lightweight
- optional ML dependency group for training/inference tools
- CLI-only private inference first
- no API/frontend dependency on ML packages until later approval

## Evaluation Metrics

For probability/classifier models:

- precision
- recall
- F1
- ROC-AUC
- PR-AUC
- Brier score
- calibration curve
- confusion matrix

For segmentation models:

- IoU
- Dice score
- precision and recall by class
- false-positive analysis
- false-negative analysis

For ranking outputs:

- top-k precision
- ranking stability
- calibration by score bucket

Evaluation reports must use neutral class names and probability/score language.

## Output Boundary

Future ML outputs must remain private by default.

Allowed fields:

- class id
- neutral class label
- probability
- score
- uncertainty
- rank
- method
- model version
- dataset version
- evaluation summary

Not allowed without later approval:

- public location overlays
- raw generated geometry in public DTOs
- local filesystem paths in public DTOs
- private hashes in public DTOs
- app-facing hard claims
- field-action recommendations

## Suggested Roadmap After This Document

Recommended order:

1. H1 — deep-learning/model feasibility and candidate ranking
2. I1 — dataset and training design
3. J1 — full Tesla flow decomposition
4. H2 — optional ML dependency sandbox, if H1 approves it
5. I2 — create dataset pack outside git, if I1 approves it
6. H3 — baseline training, if data gate passes
7. H4 — private CLI inference, if training/evaluation passes
8. G2 implementation slice, if operator UI exposure is still desired and approved

## Stop Conditions

Do not proceed to training if:

- labels are not defined
- label quality is weak or unknown
- train/validation/test split is not defined
- dataset storage policy is missing
- evaluation metrics are missing
- weights policy is missing
- dependency policy is missing
- output boundary is unclear

Do not proceed to API/frontend integration if:

- private CLI inference is not validated
- access control is not implemented
- redaction is not implemented
- audit logging is not implemented
- serving policy has not been reviewed

## Summary

The next ML step should be H1, but H1 should be a feasibility and readiness design only.

The most important requirement is the real dataset.

No real model should be trained until I1 defines the dataset schema, label policy, split policy, metadata policy, storage policy, and evaluation gates.
