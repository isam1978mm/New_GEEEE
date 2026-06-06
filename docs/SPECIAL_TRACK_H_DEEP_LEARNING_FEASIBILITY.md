# Special Track H1 Deep-Learning Feasibility

Special Track H1 is design, feasibility, policy, and inventory only.

It does not train models, run inference, retrieve weights, add PyTorch,
TensorFlow, CUDA, or other heavy ML dependencies, connect model output to API or
frontend surfaces, expose public overlays, call Earth Engine, change raster or
math logic, or implement the Tesla flow.

The binding source for H1 is:

```text
docs/ML_DATA_TRAINING_READINESS_PLAN.md
```

If any older roadmap wording differs from that readiness plan, the readiness
plan wins.

## Source Of Truth

The H1 helper is:

```text
app/pipeline/parity/deep_learning_feasibility.py
```

It writes one private metadata report:

```text
data/runs/<run_id>/manifests/special_track_h1_deep_learning_feasibility.json
```

The report must not create model weights, datasets, rasters, NPY files, map
artifacts, coordinate artifacts, public classifier outputs, or training outputs.

## Candidate Ranking

H1 inventories these model candidate paths:

| Candidate type | Feasibility status | Default position |
| --- | --- | --- |
| `private_tabular_feature_summary_probability_classifier` | `best_first_candidate` | Safest first future ML path after I1 defines the dataset gate. |
| `cnn_fixed_raster_chips` | `blocked_missing_dataset` | Needs fixed chip schema, independent labels, and split policy from I1. |
| `segmentation_labeled_masks` | `blocked_missing_dataset` | Needs labeled masks, mask QA, and much stronger data than H1 has. |
| `object_detector_boxes_regions` | `blocked_missing_dataset` | Needs independently supported box or region labels. |
| `pretrained_external_weight_inference_candidate` | `blocked_missing_weights` | Needs weight source, license, version, hash, model card, and holdout validation. |
| `notebook_custom_tesla_style_model_attempt` | `blocked_until_j1_decomposition` | Needs J1 decomposition before any model path can be evaluated. |
| `research_only_or_blocked` | `research_only` | Keeps unclear, duplicate, broken, or dependency-heavy attempts out of runtime behavior. |

The recommended first future ML path is:

```text
private probability classifier over verified feature summaries
```

Reasons:

- lower dependency risk
- easier to validate against neutral tabular features
- easier to compare against the Phase F private CLI baseline
- can remain private and CLI-only
- does not require segmentation masks or object-detection boxes

CNN, segmentation, and object-detection paths are not first implementation
candidates unless I1 demonstrates that the required data exists.

## Model Inventory Policy

Notebook model attempts include CNN-style chip paths, segmentation-style paths,
object-detector style paths, pretrained/external-weight attempts, custom
Tesla-style model attempts, and broken or unclear variants.

H1 records these as candidates only. It does not turn them into runtime code.

Each candidate records:

- notebook evidence context
- candidate architecture class
- feasibility status
- blocker
- recommended next action

## Data Requirement Policy

Future reviewed-tier labels need independent evidence.

Notebook outputs, heuristic outputs, and Phase F classifier outputs may be used
as weak signals, review hints, or features. They are not enough by themselves to
create reviewed-tier labels.

Every reviewed-tier label must include:

```text
label_evidence_source
```

I1 must define:

- one training example
- one neutral label
- allowed label quality values
- independent evidence policy
- dataset schema
- label schema
- negative and hard-negative sampling
- split policy
- storage class
- dataset manifest
- dataset identity and content hashes
- quantitative minimum holdout size
- preregistered baseline margin

Future datasets must include:

```text
dataset_id
dataset_manifest_hash
dataset_content_hash
```

Dataset storage must be `LOCAL_SENSITIVE` or `FILESYSTEM_ONLY` and outside git.

## Weights Policy

No model weights are committed to git.

Future weights require:

- approved source
- license review
- version pin
- sha256 hash
- storage path outside git
- reproducibility notes
- dependency requirements
- model card or internal equivalent

Random or unpinned weight retrieval is blocked.

Approved weights do not bypass validation. Any approved-weight inference still
requires a labeled holdout with independent evidence and a baseline comparison.

## Dependency Policy

The base app must not require PyTorch, TensorFlow, CUDA, or heavy ML packages.

An optional ML dependency group may be considered only in a later approved slice.
Normal app startup must remain free of heavy ML imports.

## Evaluation Policy

Every future model evaluation must preregister a primary metric before training.

For rare or low-prevalence classes, useful metrics include:

- PR-AUC
- recall at fixed precision
- calibration
- Brier score
- precision
- recall
- F1

ROC-AUC is secondary unless class prevalence is reported.

Every metric table must include:

- class prevalence or base rate
- split name
- sample count
- label evidence source counts
- confidence intervals or bootstrap uncertainty when feasible

Any future ML model must beat the Phase F private neutral classifier baseline on
the untouched holdout by an I1-preregistered margin. The margin must clear
holdout noise using confidence intervals or paired bootstrap-style evidence.

If the future model does not clear that gate, the simpler Phase F path remains
the safer path.

## Threshold Policy

Thresholds must be selected on train and validation data only.

The final holdout must not be used for:

- threshold selection
- feature selection
- model selection
- hyperparameter tuning
- calibration tuning
- manual cherry-picking

## Output Traceability Policy

Future model outputs must include:

- `dataset_id`
- `dataset_manifest_hash`
- `dataset_content_hash`
- `model_id`
- `model_version`
- `weights_hash` if weights are used
- `evaluation_summary`

Outputs remain private by default.

## Private Boundary

H1 does not add API routes, frontend views, artifact-serving changes, public
overlays, coordinate-bearing public DTOs, training jobs, or inference jobs.

Future model artifacts must remain private, CLI-first, and probability/score
only unless a later user-approved phase changes the boundary after intended-use,
acceptable-use, misuse, redaction, access-control, audit, and serving review.

## H1 To I1

H1 rankings are provisional.

H1 feeds requirements into I1. H1 must be revisited after I1 if real data
constraints differ from these assumptions.

I1 must define the quantitative minimum holdout size and preregistered baseline
margin before training can be considered.
