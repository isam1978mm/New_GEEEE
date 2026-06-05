# Phase 8 Probability-Only Classifier Design

## Purpose

Phase 8 locks the design contract for future private classifier/model outputs that are interpreted as probabilities, likelihoods, ranks, uncertainty values, or scores.

This phase is design, safety-boundary, and verification planning only. It does not train models. It does not run inference. It does not implement classifier scoring. It does not calculate probabilities. It does not generate classifier output files.

Phase 8 follows Phase 7 and precedes Phase 9 in the notebook parity roadmap.

## Scope

Phase 8 covers six design categories:

| Category | Status |
| --- | --- |
| `probability_output_schema` | `design_contract_only` |
| `neutral_class_probability_labels` | `design_contract_only` |
| `threshold_and_uncertainty_policy` | `design_contract_only` |
| `private_cli_only_boundary` | `design_contract_only` |
| `forbidden_wording_policy` | `design_contract_only` |
| `future_reference_and_verifier_requirements` | `reference_needed` |

The source-of-truth helper is:

```text
app/pipeline/parity/probability_only_classifier_design.py
```

The helper can write an inventory report under:

```text
data/runs/<run_id>/manifests/phase_8_probability_only_classifier_design.json
```

That report is metadata only. It must not create raster, tensor, map, CSV, or model artifacts.

## Probability-Only Policy

Future classifier/model outputs must use probabilities, likelihood values, scores, ranks, uncertainty values, or confidence intervals only.

Allowed app-facing wording includes:

```text
probability
likelihood
score
confidence_interval
uncertainty
class_probability
rank
```

Future app-facing labels must stay neutral:

```text
Class_A
Class_B
Class_C
```

and later neutral class IDs that follow the same pattern.

Original notebook label wording is private documentation only. It must not become app-facing API, frontend, logs, filenames, or public DTO content.

## Safety Boundary

Future classifier/model/probability artifacts must default to:

```text
filesystem_only=true
cli_only=true
requires_enable_experimental=true
http_servable=false
frontend_visible=false
downloadable_via_api=false
called_by_api=false
called_by_background_tasks=false
called_by_core_orchestrator=false
artifact_class=LOCAL_SENSITIVE or EXPERIMENTAL_CLASSIFIER_ARTIFACT
```

Phase 8 does not expose classifier/model/probability artifacts through HTTP. It does not add API routes, frontend previews, public download endpoints, database tables, or artifact-serving changes.

Public DTOs must stay redacted. They must not include classifier labels, probability outputs, model outputs, coordinates, geometry, bounds, CRS transforms, local paths, or hashes for sensitive private artifacts.

## Runtime And Parity Separation

Runtime output presence and notebook-value parity are separate states.

Phase 8 does not mark runtime output verification as true. Phase 8 does not mark notebook-value parity as true.

Frozen notebook references are required before notebook-value parity can pass. A later verifier slice must compare private app outputs against frozen notebook references and must check schema, neutral labels, values, calibration metadata, and wording policy.

## Non-Goals

Phase 8 does not:

- train models;
- run inference;
- implement classifier scoring;
- calculate probabilities;
- download model weights;
- add heavy ML dependencies;
- generate rasters;
- generate NPY arrays;
- generate classifier CSV outputs;
- call Earth Engine;
- change science, raster, SAR, optical, DEM, PCA, GRID, object extraction, or classifier runtime logic;
- change `app/pipeline/stages_experimental` runtime behavior;
- change API, frontend, database, or artifact serving policy;
- rename existing outputs.

## Future Work Requirements

Any later implementation or verifier slice must be source/reference-driven.

Before a future implementation can write probability artifacts, it must lock:

- frozen notebook reference artifacts;
- source-cell mapping;
- expected private schema;
- neutral class label mapping;
- calibration or uncalibrated-score status;
- value tolerance policy;
- private report location;
- artifact class and serving boundary.

Until those inputs are locked, Phase 8 remains a design contract and planning layer only.
