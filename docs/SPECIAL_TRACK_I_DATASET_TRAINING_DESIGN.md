# Special Track I1 Dataset Training Design

Special Track I1 is design, schema, and policy only. It does not create a dataset,
train a model, run inference, retrieve weights, add ML dependencies, expose outputs
publicly, or implement the Tesla flow.

I1 defines the dataset contract that any future training phase must satisfy. The
binding gates in `docs/ML_DATA_TRAINING_READINESS_PLAN.md` apply here. The H1
candidate rankings in `docs/SPECIAL_TRACK_H_DEEP_LEARNING_FEASIBILITY.md` remain
provisional and must be revisited after the I1 dataset gates are applied to real
candidate data.

## Training Example Schema

One training example is one fixed GRID-consistent private chip or feature-summary
sample tied to one neutral label. The required fields are:

- `schema_version`
- `sample_id`
- `dataset_id`
- `area_id`
- `group_id`
- `chip_id`
- `split`
- `label`
- `label_quality`
- `label_evidence_source`
- `evidence_source_type`
- `evidence_source_version`
- `evidence_review_method`
- `reviewer_or_source_reference`
- `acquisition_window`
- `sensor_sources`
- `grid_version`
- `preprocessing_commit`
- `features_ref`
- `metadata_ref`
- `redaction_class`
- `notes`

`area_id`, `chip_id`, GRID metadata, local references, and related identifiers are
coordinate proxies. They remain private and are redacted from public summaries.

## Label Schema

Allowed label quality values are:

- `reviewed_independent`
- `reviewed_adjudicated`
- `weak_label`
- `synthetic_or_proxy`
- `uncertain`
- `excluded`

Only `reviewed_independent` and `reviewed_adjudicated` count as reviewed-tier
labels. Those values require independent evidence and a nonblank
`label_evidence_source`.

Allowed evidence source types are:

- `field_validation`
- `authoritative_external_dataset`
- `expert_adjudication_independent_evidence`
- `independently_produced_reference`
- `weak_heuristic_hint`
- `synthetic_proxy`
- `unknown_or_missing`

`unknown_or_missing`, notebook outputs, and heuristic outputs cannot pass as
reviewed-tier evidence. They may be weak signals only.

## Label QA And Adjudication

Label QA requires disagreement records, reviewer/source references, disagreement
notes, and an inter-rater agreement metric or a written deferral reason. Adjudicated
labels require multiple-reviewer or independent adjudication records. If no
agreement is reached, the sample is escalated and then excluded from reviewed-tier
accounting if still unresolved.

## Split And Leakage Policy

Splits must group by `group_id` or at least `area_id`. The same area, chip family,
near-duplicate pixels, and date-linked area variants must not cross
train/validation/test/final-holdout splits unless a written exception is approved
before dataset construction.

The split policy requires:

- deterministic split seed
- split manifest hash
- temporal holdout
- untouched final holdout
- no threshold selection on final holdout
- no feature, model, hyperparameter, or calibration tuning on final holdout

## Negative And Hard-Negative Sampling

Datasets require negative/background examples and hard negatives. Sampling must
include visually similar non-class areas, terrain/vegetation/soil/background
variety, cloud/shadow/sensor-noise edge cases where relevant, and false-positive-
like cases from earlier heuristics. Class prevalence, base rate, and positive and
negative counts per class must be recorded per split.

## Dataset Manifest And Storage

The dataset manifest must include:

- `dataset_id`
- `schema_version`
- `created_at`
- `build_commit`
- `build_command_or_procedure`
- `dataset_manifest_hash`
- `dataset_content_hash`
- `split_seed`
- `split_policy_version`
- `data_source_list`
- `label_source_list`
- `label_evidence_source_counts`
- `label_quality_counts`
- `class_prevalence_by_split`
- `storage_path_outside_git`
- `artifact_class`
- `filesystem_only`
- `http_servable`
- `frontend_visible`
- `downloadable_via_api`
- `redaction_policy`
- `dataset_card_ref`
- `known_limitations`
- `intended_use`
- `unacceptable_use`
- `misuse_review_status`

Datasets, labels, chips, coordinate-bearing metadata, generated overlays, and
model-ready tensors must not be committed to git. Storage is `LOCAL_SENSITIVE` or
`FILESYSTEM_ONLY`, with `filesystem_only=true`, `http_servable=false`,
`frontend_visible=false`, and `downloadable_via_api=false` by default.

## Evaluation And Baseline Policy

The primary metric must be preregistered before training. Rare-class evaluation
must prioritize PR-AUC, recall at fixed precision, and calibration. ROC-AUC is
secondary unless prevalence and base rate are reported.

Every metric table must include split name, sample count, class prevalence, base
rate, label evidence counts, and uncertainty or bootstrap interval when feasible.
Any future model must beat the Phase F private CLI classifier baseline by a
preregistered margin on untouched holdout. That margin must clear holdout
uncertainty. If it does not, Phase F remains the safer baseline.

## Threshold Policy

Thresholds may be selected only on train/validation data. The final holdout is
never used for threshold selection. The threshold choice must be recorded before
final holdout evaluation.

## Quantitative Gates

Before training begins, the dataset readiness record must set numeric values for:

- minimum holdout size
- minimum reviewed-tier label count per class
- minimum negative/background count
- minimum hard-negative count
- preregistered baseline margin
- minimum prevalence reporting requirement
- minimum confidence or uncertainty reporting requirement

## Readiness Stop Conditions

Training remains blocked if any of these are missing:

- independent evidence for reviewed-tier labels
- dataset manifest
- `dataset_manifest_hash`
- `dataset_content_hash`
- leakage-safe split policy
- untouched holdout
- numeric holdout-size gate
- preregistered baseline margin
- valid `LOCAL_SENSITIVE` or `FILESYSTEM_ONLY` storage class
- intended-use, unacceptable-use, and misuse review before public exposure

Notebook and heuristic outputs may help triage candidates, but they cannot be the
only reviewed-tier label evidence.

## Report Helper

`app.pipeline.parity.dataset_training_design` provides the I1 design objects and
writes a private JSON report at:

`data/runs/<run_id>/manifests/special_track_i1_dataset_training_design.json`

The report is a design manifest only. It does not create datasets, chips, labels,
rasters, NPY files, model artifacts, map artifacts, public classifier outputs, or
coordinate artifacts.
