# Phase 7 Classifier Model Parity Contract

Phase 7 covers classifier/model notebook parity as an inventory, private contract,
safety-boundary, and verification-planning phase.

Phase 7 does not train models. It does not run inference. It does not generate
raster, NPY, GeoJSON, KMZ, KML, HTML map, image, coordinate, or model artifact
files. It does not call Earth Engine. It does not add heavy ML dependencies or
download pretrained weights.

Phase 7 does not change science, raster, SAR, optical, DEM, PCA, GRID, object
extraction, or classifier logic. It does not change API, frontend, database, or
artifact serving policy.

Phase 7 does not expose classifier/model artifacts through HTTP, does not add
public downloads, does not add frontend previews, does not add API routes, does
not add database tables, and does not connect the experimental classifier to
BackgroundTasks or the core orchestrator.

## Scope

Phase 7 tracks these private notebook-parity categories:

- `notebook_rule_based_classifier`
- `neutral_label_mapping`
- `experimental_cli_boundary`
- `deep_learning_model_cells`
- `classifier_inputs_outputs`
- `public_exposure_boundary`

The source-of-truth helper is:

- `app/pipeline/parity/classifier_model_inventory.py`

The helper writes only this JSON inventory report:

- `data/runs/<run_id>/manifests/phase_7_classifier_model_inventory.json`

## Safety Boundary

All Phase 7 classifier/model artifacts default to:

- `filesystem_only=true`
- `cli_only=true`
- `requires_enable_experimental=true`
- `http_servable=false`
- `frontend_visible=false`
- `downloadable_via_api=false`
- `called_by_api=false`
- `called_by_background_tasks=false`
- `called_by_core_orchestrator=false`
- `artifact_class=LOCAL_SENSITIVE` or `artifact_class=EXPERIMENTAL_CLASSIFIER_ARTIFACT`

Classifier/model artifacts remain CLI-only and experimental unless a later
user-approved phase changes policy. Phase 7 does not make private notebook
artifacts visible through API routes, frontend UI, artifact downloads, previews,
tiles, or overlays.

Public DTOs must stay redacted. They must not include classifier labels, model
outputs, raw coordinates, geometry, bounds, CRS transforms, filesystem paths, or
hashes for sensitive private artifacts.

## Neutral Labels

App-facing labels must stay neutral. The current experimental module uses
`Class_A`, `Class_B`, `Class_C`, and later neutral class identifiers only.

Original notebook labels remain private documentation only. They must not become
public API behavior, frontend behavior, logs, filenames, or app-source labels.

Any future interpreted model or classifier output must use probability-only
wording such as class score, heuristic score, uncalibrated model probability, or
calibrated model probability when calibration evidence exists.

## Notebook Source Evidence

Notebook and extracted-cell evidence includes rule-based classifier branches,
hard-classifier CSV/JSON/GeoJSON/text outputs, model-input tensor builders,
YOLO/CNN/Swin/SegFormer preparation cells, UnetPlusPlus and ResNet-style model
attempts, and final model-output map/KMZ branches. Some cells depend on optional
ML packages, model weights, training data, or broken notebook code.

The app already has a private experimental package:

- `app/pipeline/stages_experimental/__init__.py`
- `app/pipeline/stages_experimental/classes.py`
- `app/pipeline/stages_experimental/classifier.py`
- `app/pipeline/stages_experimental/inputs.py`
- `app/pipeline/stages_experimental/outputs.py`
- `app/pipeline/stages_experimental/run.py`
- `app/pipeline/stages_experimental/README.md`

That package is env-gated, CLI-only, neutral-label based, and local-output only.
Existing runtime presence is separate from notebook-value parity.

## Category Decisions

| Category | Phase 7 status | Notes |
| --- | --- | --- |
| `notebook_rule_based_classifier` | `source_recovery_needed` | Notebook rule branches need private source and reference mapping before a verifier or writer slice. |
| `neutral_label_mapping` | `covered_by_existing_contract` | App-facing class IDs stay neutral through `Class_A`, `Class_B`, `Class_C`, and later neutral IDs. |
| `experimental_cli_boundary` | `covered_by_existing_contract` | Existing experimental package remains env-gated and CLI-only. |
| `deep_learning_model_cells` | `implementation_later` | Model weights, training data, optional dependencies, and runnable-cell status are deferred. |
| `classifier_inputs_outputs` | `verifier_needed` | Existing local neutral outputs need frozen references and expected schema before any parity claim. |
| `public_exposure_boundary` | `covered_by_existing_contract` | No public/API/frontend/database/artifact-serving exposure is added. |

## Verification Planning

Frozen notebook references are required before notebook-value parity can pass.
Later verifier slices must be source/reference-driven and must preserve the
private boundary. A future private verifier may compare expected input artifact
presence, neutral label schemas, row counts, class-score fields, summary payloads,
and filesystem-only artifact metadata.

That later work must not change public serving behavior unless explicitly
approved by the user in a separate phase.

Phase 7 follows Phase 6 and precedes Phase 8 in the full roadmap.
