# Phase 10 Clean vs Parity Decision

## Purpose

Phase 10 closes the current notebook-parity roadmap by locking the boundary between:

1. clean app behavior
2. private notebook-parity behavior
3. experimental CLI-only behavior
4. hidden filesystem-only artifacts
5. future implementation candidates

Phase 10 does not implement runtime behavior.
Phase 10 does not change science, raster, or math logic.
Phase 10 does not change API, frontend, database, or artifact serving policy.

## Scope

The source-of-truth helper is:

`app/pipeline/parity/clean_vs_parity_decision.py`

It records these decision categories:

- `clean_app_core_outputs`
- `private_notebook_parity_outputs`
- `verifier_only_outputs`
- `source_recovered_not_implemented_outputs`
- `private_coordinate_map_outputs`
- `experimental_classifier_outputs`
- `probability_only_model_outputs`
- `future_reference_driven_implementation_candidates`
- `public_api_and_frontend_boundary`
- `artifact_serving_boundary`

The helper writes one JSON report:

`data/runs/<run_id>/manifests/phase_10_clean_vs_parity_decision.json`

That report is metadata only. It must not create raster, tensor, coordinate, map, classifier, model, or CSV artifacts.

## Boundary Decision

### Clean app behavior

Clean app mode includes only defensible, normal runtime behavior:

- core pipeline stages
- run lifecycle
- existing API and frontend behavior
- existing artifact-serving controls

Clean app mode does not absorb private notebook-parity outputs merely because a nearby app output looks similar.

### Private notebook-parity behavior

Private notebook-parity outputs remain private by default.
They may be tracked, compared, and documented for notebook fidelity, but they stay outside public API and frontend behavior unless a later user-approved phase changes policy.

Runtime output presence and notebook-value parity remain separate.
Frozen notebook references are required before notebook-value parity can pass.

### Experimental classifier behavior

Classifier and model artifacts remain:

- CLI-only
- private
- env-gated
- filesystem-only

Phase 10 does not move classifier behavior into API routes, frontend views, BackgroundTasks, or the core orchestrator.

### Probability-only interpretation

Any future model interpretation remains probability-only by default.
Future wording may use probability, likelihood, score, rank, confidence interval, or uncertainty language only.

Phase 10 does not add model scoring or inference.
Phase 10 only locks the interpretation boundary.

### Coordinate and map artifacts

Coordinate-bearing and map artifacts remain private and filesystem-only by default.
They are not HTTP-served, not frontend-visible, and not downloadable through API in Phase 10.

### Artifact serving boundary

Phase 10 makes no serving-policy change.
Existing artifact classes, `can_serve_artifact()`, and `serve_artifact_response()` remain the only approved HTTP boundary.

## Future Work Rule

Future implementation must be source-driven, reference-driven, and user-approved.

That means later work must not:

- guess formulas from nearby outputs
- treat runtime presence as notebook-value parity
- treat verifier availability as public exposure approval
- widen serving policy without a separate explicit phase

## Roadmap Position

Phase 10 closes the current roadmap.
No later phase is created here.
If the user wants more notebook-parity work later, that must start from a new explicit roadmap update.
