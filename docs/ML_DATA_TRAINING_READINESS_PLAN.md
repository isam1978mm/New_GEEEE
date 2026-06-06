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

Notebook outputs and heuristic outputs may be useful as features, weak signals, review hints, or QA inputs. They are not enough to create reviewed labels by themselves.

A reviewed-tier label must have at least one independent evidence source that did not come only from the heuristic pipeline being modeled.

## Single Source Of Truth: ML Gate Table

This table is the authoritative gate table. Other roadmap wording should refer back to this table to avoid drift.

| Deferred item | Earliest allowed stage | Required gate |
|---|---|---|
| H1 feasibility design | Now, if requested | Design only. Must inventory model attempts, define data requirements, define weights/dependency policy, define metrics, and name blockers. No training or inference. |
| I1 dataset/training design | After or alongside H1 | Must define dataset schema, label schema, independent evidence policy, split policy, dataset manifest, storage class, metrics, baseline, and stop conditions. No training. |
| Approved-weight inference | After H1 and I1 | Even approved weights require a labeled holdout with independent evidence and a baseline comparison. No unlabeled zero-validation inference. |
| Download model weights | After H1 weights policy | Source, license, version, hash, storage, reproducibility notes, and model card are accepted. No random or unpinned downloads. |
| Add PyTorch/TensorFlow or similar | After H1 dependency policy | Optional dependency group only. Normal app startup must not require heavy ML packages. |
| Train a model | After H1 and I1 | Independent ground-truth gate passes, dataset manifest exists, split policy exists, metrics are preregistered, threshold policy exists, and baseline comparison rule is accepted. |
| Private CLI inference | After training/evaluation or approved-weight validation passes | Must beat the preregistered baseline by the preregistered margin on the untouched holdout. Output stays private and probability/score-only. |
| Connect model output to API/frontend | After private CLI evaluation passes | Requires access control, redaction, DTO policy, audit logging, serving-policy review, and intended-use / acceptable-use / misuse review. |
| Generated overlay UI for operators | After G2 implementation approval | Operator-only auth, role checks, per-run authorization, audit logging, and default-off config. No general public visibility. |
| Public location overlays | After a separate public-exposure approval | Requires serving-policy review, redaction review, audit policy, intended-use / acceptable-use / misuse review, and explicit user approval. |
| Full Tesla flow runtime | After J1 decomposition | Must be split into small approved modules. No single monolithic engine. |

## Hard Gates Before Any Reviewed-Tier Label Count

A label may count as `reviewed_independent` or `reviewed_adjudicated` only if it has at least one independent evidence source.

Allowed independent evidence examples:

- field validation
- authoritative external dataset
- expert adjudication using evidence the heuristic pipeline did not see
- independently produced reference labels with documented source and method

Not enough by itself:

- the notebook heuristic output
- the Phase F classifier output
- the same Sentinel/SAR/DEM/feature stack used by the heuristic, reviewed without independent evidence
- a human simply agreeing with the heuristic output without independent support

Every label record must include `label_evidence_source`.

Every dataset manifest must count labels by evidence source and label quality.

## H1 And I1 Feedback Loop

H1 feasibility depends on what data can realistically be obtained. I1 defines that data more precisely.

Therefore:

- H1 rankings are provisional.
- H1 must feed data requirements into I1.
- H1 must be revisited after I1 if the real dataset differs from H1 assumptions.
- No model path should be treated as final until I1 has defined real label sources, split rules, dataset storage, and evaluation gates.

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
9. Which independent evidence sources would be required for each candidate?
10. What baseline must a future model beat?

H1 should not train or run inference.

H1 should produce:

- a model-attempt inventory
- candidate model ranking
- data requirements
- independent evidence requirements
- weights policy
- dependency policy
- metrics policy
- baseline comparison policy
- private inference boundary
- blockers and next actions

## What I1 Should Decide

Special Track I1 should define the real training dataset.

I1 should answer:

1. What is one training example?
2. What is one label?
3. What independent evidence source supports each reviewed-tier label?
4. What label quality levels exist?
5. How are train, validation, and test splits made?
6. How do we prevent geographic, group, and temporal leakage?
7. Where is the dataset stored?
8. What metadata is required?
9. What is allowed in git and what must stay outside git?
10. What minimum dataset size is required before training?
11. What class prevalence/base rate exists in each split?
12. How are negatives and hard negatives sampled?
13. How are thresholds selected without contaminating the holdout?
14. How are adjudication disagreements handled, and is inter-rater agreement recorded when multiple reviewers are involved?

I1 should not train.

I1 should produce:

- dataset schema
- label schema
- independent evidence policy
- label QA policy
- adjudication and reviewer-disagreement policy
- split policy
- metadata policy
- dataset manifest policy
- storage and artifact-class policy
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

A label record must include:

- sample_id
- area_id
- group_id
- class_label
- label_quality
- label_evidence_source
- evidence_source_type
- evidence_source_version
- evidence_review_method
- reviewer_or_source_reference when available
- timestamp or version
- notes

`label_evidence_source` is mandatory for reviewed-tier labels.

Label quality levels should distinguish:

- reviewed_independent
- reviewed_adjudicated
- weak_label
- synthetic_or_proxy
- uncertain
- excluded

Training should start only after enough `reviewed_independent` or `reviewed_adjudicated` labels exist.

## Negative And Background Examples

The dataset must include negative/background examples.

These should include:

- visually similar non-class areas
- different soil/terrain/vegetation cases
- urban/background cases if relevant
- sensor-noise or cloud/shadow edge cases
- false-positive-like examples from earlier heuristics

This is hard-negative mining and should be documented explicitly in the dataset manifest.

Every split must record:

- class prevalence/base rate
- number of positive examples per class
- number of negative/background examples
- hard-negative sampling method
- geographic coverage summary
- temporal coverage summary

Without negative/background examples, a model can learn to over-score everything.

## Split Policy

Train/validation/test splits must prevent geographic, group, and temporal leakage.

Required split logic:

- group by `area_id` or a stronger `group_id`
- keep the same local area, chip family, and near-duplicate pixels in only one split
- prevent the same area across different dates from leaking across splits unless explicitly designed and documented
- reserve a final untouched holdout set
- include a temporal holdout rule where the final holdout uses later or otherwise separated acquisition windows
- document all split seeds and deterministic split rules

Threshold selection must use training/validation data only.

The final holdout must not be used for:

- threshold selection
- feature selection
- model selection
- hyperparameter tuning
- calibration tuning
- manual cherry-picking

The final holdout set should stay untouched until final evaluation.

## Dataset Provenance And Storage Policy

Dataset provenance must be as strict as weights provenance.

No training dataset, labeled chips, coordinate-bearing metadata, or generated overlays should be committed to git.

Every dataset pack must have a dataset manifest with:

- dataset_id
- schema_version
- created_at
- build_commit
- build_command or build procedure
- content hash or manifest hash
- split seed and split policy version
- data source list
- label source list
- label evidence source counts
- class prevalence by split
- storage path outside git
- artifact_class
- filesystem_only flag
- redaction policy
- dataset card or internal equivalent
- known limitations

Dataset storage classification:

- `artifact_class=LOCAL_SENSITIVE` or `FILESYSTEM_ONLY`
- `filesystem_only=true`
- `http_servable=false`
- `frontend_visible=false` unless a later operator-only design approves it
- `downloadable_via_api=false` unless a later explicit serving-policy phase approves it

Area identifiers, chip identifiers, local paths, bounds, and grid metadata can be coordinate proxies. They must follow the same redaction rules as private map artifacts.

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
- easier to compare against a baseline and frozen references

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
  "group_id": "area_001_all_dates",
  "split": "train",
  "label": "Class_A",
  "label_quality": "reviewed_independent",
  "label_evidence_source": "external_reference_dataset_v1:item_12345",
  "evidence_source_type": "authoritative_external_dataset",
  "evidence_source_version": "external_reference_dataset_v1",
  "evidence_review_method": "direct_match_to_external_reference",
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
    "preprocessing_commit": "real-commit-sha",
    "sensor_window": "2025-01-01_to_2025-03-31"
  }
}
```

The identifiers above are examples. Codex prompts must replace example values with real values before execution.

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

Approved weights do not bypass dataset validation. Any approved-weight inference still requires a labeled holdout with independent evidence and a baseline comparison.

## Dependency Policy

ML dependencies should be optional.

The normal app should not require PyTorch, TensorFlow, CUDA, or other heavy ML packages just to start.

Recommended structure:

- base app dependencies remain lightweight
- optional ML dependency group for training/inference tools
- CLI-only private inference first
- no API/frontend dependency on ML packages until later approval

## Evaluation Metrics And Baseline Policy

Every model evaluation must specify a primary metric before training.

For rare-class or low-prevalence problems, PR-AUC, recall at fixed precision, and calibration are usually more informative than ROC-AUC alone.

For probability/classifier models:

- precision
- recall
- F1
- PR-AUC
- recall at fixed precision
- Brier score
- calibration curve
- confusion matrix
- ROC-AUC as secondary context only when class prevalence is reported

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

Every metric table must include:

- class prevalence/base rate
- split name
- sample count
- label evidence source counts
- confidence intervals or bootstrap uncertainty when feasible

Baseline requirement:

- The Phase F private heuristic classifier is the default baseline for neutral probability/score outputs.
- The Phase E frozen-reference verifier remains the private reference-comparison boundary where applicable.
- A future ML model must outperform the Phase F baseline on the untouched holdout by a preregistered margin on the primary metric, or it is not adopted.
- The preregistered margin must clear holdout noise. For example, the model lower confidence bound should exceed the baseline point estimate, or a paired bootstrap should support the gain.
- If the model does not beat the baseline by the preregistered margin, keep the simpler Phase F path.

Threshold policy:

- decision thresholds must be chosen on training/validation only
- thresholds must not be chosen on the final holdout
- threshold choice must be recorded before final holdout evaluation

Evaluation reports must use neutral class names and probability/score language.

## Inference-Time Drift Monitoring

Input-distribution drift after deployment is a later separate concern.

Any future serving or recurring private inference path must define monitoring for new sensors, new regions, new acquisition windows, preprocessing changes, and feature-distribution shifts before it is treated as production-ready.

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

## Public Exposure And Use/Misuse Review

Any later API/frontend/public overlay exposure must pass more than technical access-control gates.

It must include:

- intended-use review
- acceptable-use review
- misuse review
- redaction review
- access-control review
- audit logging review
- serving-policy review

Without this review, model outputs and generated overlays remain private/offline.

## Suggested Roadmap After This Document

Recommended order:

1. H1 — deep-learning/model feasibility and candidate ranking
2. I1 — dataset and training design
3. J1 — full Tesla flow decomposition
4. H1 revisit — update feasibility ranking after I1 defines real data constraints
5. H2 — optional ML dependency sandbox, if H1 approves it
6. I2 — create dataset pack outside git, if I1 approves it
7. H3 — baseline training, if data gate passes
8. H4 — private CLI inference, if training/evaluation beats the baseline gate
9. G2 implementation slice, if operator UI exposure is still desired and approved

## Stop Conditions

Do not proceed to training if:

- labels are not defined
- reviewed-tier labels lack independent evidence
- `label_evidence_source` is missing
- label quality is weak or unknown
- class prevalence/base rate is not recorded
- negative/background sampling is undefined
- hard-negative sampling is undefined for rare-class tasks
- group split policy is missing
- temporal holdout policy is missing
- final holdout is not protected
- threshold selection policy is missing
- dataset manifest/hash is missing
- dataset storage classification is missing
- evaluation metrics are missing
- Phase F baseline comparison rule is missing
- weights policy is missing
- dependency policy is missing
- output boundary is unclear

Do not proceed to approved-weight inference if:

- no labeled holdout exists
- independent evidence is missing
- no baseline comparison is defined
- weights source/license/hash/version are missing

Do not proceed to API/frontend integration if:

- private CLI inference is not validated
- model does not meet the baseline-beating gate
- access control is not implemented
- redaction is not implemented
- audit logging is not implemented
- serving policy has not been reviewed
- intended-use / acceptable-use / misuse review is missing

## Summary

The next ML step should be H1, but H1 should be a feasibility and readiness design only.

The central requirement is not just data volume. The central requirement is independent evidence-backed labels.

No real model should be trained until I1 defines the dataset schema, label policy, independent evidence gate, split policy, metadata policy, dataset manifest, storage classification, baseline comparison, and evaluation gates.
