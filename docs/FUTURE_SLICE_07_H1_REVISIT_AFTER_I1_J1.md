# Future Slice 07 / H1 Revisit After I1 And J1

## Scope

Future Slice 07 is an H1 revisit only. It re-evaluates the Special Track H1
deep-learning/model feasibility ranking using the I1 dataset gates and the J1
Tesla-flow decomposition, now that the Phase C/E semantic feature comparator and
the Phase D/E private map artifact comparator slices exist.

Future Slice 07 is design, feasibility, and policy only. It does not train, does
not run inference, does not download weights, does not add ML dependencies, does
not create a dataset, does not expose model outputs through API or frontend, does
not change artifact serving, and does not call Earth Engine.

The binding gates are in `docs/ML_DATA_TRAINING_READINESS_PLAN.md`. The dataset
gates are binding from `docs/SPECIAL_TRACK_I_DATASET_TRAINING_DESIGN.md`. The
Tesla-flow decomposition is binding from
`docs/SPECIAL_TRACK_J_TESLA_FLOW_DECOMPOSITION.md`. Where wording differs, the
strictest gate applies.

## Source Of Truth

The revisit helper is:

```text
app/pipeline/parity/deep_learning_feasibility_revisit.py
```

It writes one private JSON report:

```text
data/runs/<run_id>/manifests/future_slice_07_h1_revisit_after_i1_j1.json
```

The report is private design metadata only. It must not create model weights,
datasets, labels, chips, rasters, NPY files, map artifacts, coordinate artifacts,
public classifier outputs, or training outputs. The report path stays under
`run_dir`.

## Revisit Questions And Answers

1. Does the original H1 recommended first model still hold? Yes. The private
   feature-summary probability classifier remains the recommended first future ML
   path.
2. Which candidates are still blocked after I1/J1? CNN chips, segmentation masks,
   object detection, pretrained/external-weight inference, the custom Tesla-style
   model attempt, and the research-only bucket.
3. Which candidates became more feasible because Phase C/E and Phase D/E comparator
   slices exist? The feature-summary classifier, because verified, parity-checked
   private tabular features and private map-artifact parity context now exist. The
   image-model paths do not gain training labels from those slices.
4. Which candidates remain blocked by missing independent evidence? All reviewed-
   tier label paths; notebook and heuristic outputs stay weak signals only.
5. Which candidates remain blocked by missing dataset pack? CNN, segmentation, and
   object-detection candidates, pending an I2 dataset pack.
6. Which candidates remain blocked by missing weights? The pretrained/external-
   weight inference candidate, which also needs labeled holdout validation.
7. Which candidates remain blocked by J1 decomposition risks? The custom
   Tesla-style model attempt, which stays blocked until a later J2 or source-lock
   slice isolates a small, evidence-backed substep and the full flow is never
   ported as one engine.
8. What is the safest next ML/data slice? I2 — create a private dataset pack
   outside git, once the independent evidence gate can be satisfied.
9. What must I2 provide before training can be considered? An independent
   evidence-backed labeled dataset pack with `dataset_id`,
   `dataset_manifest_hash`, `dataset_content_hash`, a leakage-safe split with a
   numeric minimum holdout size, a preregistered baseline margin over the Phase F
   baseline, and `LOCAL_SENSITIVE` or `FILESYSTEM_ONLY` storage outside git.
10. What must H2 provide before optional ML dependencies can be considered? An
    optional ML dependency sandbox that keeps the base app free of heavy ML
    packages, justified only after the data and validation gates make a model path
    worthwhile.

## Revisited Recommendation

The recommended first future model remains:

```text
private feature-summary probability classifier
```

unless later real data proves otherwise. It stays the lowest-dependency path, is
easiest to validate against the Phase F baseline and the Phase E references, and
does not require chips, masks, boxes, or model weights.

## Revisit Decisions

- Notebook and heuristic outputs remain weak signals only.
- Reviewed-tier labels remain blocked until independent evidence exists.
- CNN, segmentation, and detector paths remain blocked until I2 proves real dataset
  readiness.
- Approved-weight and foundation-style inference remain blocked until the weights
  policy and a labeled holdout validation exist.
- The custom Tesla-style model attempt remains blocked unless a later J2 or
  source-lock slice isolates a small safe substep.
- Public, API, and frontend model output remains blocked.
- The Phase F heuristic classifier remains the baseline to beat.
- Training remains blocked until the I2 data gates pass.
- Inference remains blocked until training/evaluation or approved-weight validation
  passes.
- I2 is the recommended next ML/data slice.

## Gate References

The revisit measures each candidate against these binding gates:

- I1 independent evidence gate (reviewed-tier labels require an independent
  `label_evidence_source`).
- I1 dataset manifest gate (`dataset_id`, `dataset_manifest_hash`,
  `dataset_content_hash`, storage outside git).
- I1 holdout and baseline-margin gate (numeric minimum holdout size and a
  preregistered margin over the Phase F baseline on an untouched holdout).
- J1 decomposition gate (no monolithic Tesla runtime; ml_model_attempt substeps
  stay behind the H/I gates).

## Safety Boundary

Future Slice 07 does not:

- train a model or run inference
- download or commit model weights
- add PyTorch, TensorFlow, CUDA, or other heavy ML dependencies
- create a dataset, dataset packs, labels, or chips
- generate rasters, NPY files, or map artifacts
- call Earth Engine or start backend runs
- change raster, math, or classifier runtime logic
- connect model output to API or frontend
- expose public overlays or change artifact-serving policy
- implement I2, H2, H3, H4, or G2 implementation work

I2 remains required before training can be considered. H2 remains required before
any optional ML dependency sandboxing. H3 and H4 remain blocked until the data and
evaluation gates pass.
