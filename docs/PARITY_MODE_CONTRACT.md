# Notebook Parity Mode Contract

## Purpose And Scope

Faithful notebook conversion is the objective. Notebook parity mode is a private output architecture for preserving notebook output families, names, folders, and artifacts where technically feasible while the core app keeps its existing defensible behavior.

Phase 1 defines the contract and helper surface only. It does not change raster math, Earth Engine calls, stage formulas, candidate scoring, API behavior, frontend behavior, database models, migrations, artifact serving policy, classifier behavior, or existing pipeline outputs.

Original notebook names are preserved for parity where feasible. They are recorded as parity output names, not as product claims. File existence is not parity proof: runtime output presence and notebook-value parity remain separate manifest fields and must be verified from source inspection or parity harness evidence.

## Mode Separation

| Mode | Purpose | Phase 1 exposure |
| --- | --- | --- |
| `core_app` | Existing defensible app outputs and behavior. | Unchanged. |
| `notebook_parity` | Private notebook-compatible aliases, folders, semantic rasters, reports, and manifests. | Filesystem architecture only. Not integrated into the live pipeline in Phase 1. |
| `experimental_private` | CLI-only, filesystem-only experimental/classifier artifacts and notebook-only research outputs. | No API, frontend, BackgroundTasks, or orchestrator integration. |
| `public_shared` | Any future shared/public-safe output surface. | No public/shared exposure decision is made in Phase 1. |

Notebook parity mode must not weaken the app's existing artifact-serving policy. Coordinate-bearing artifacts, classifier outputs, KMZ/KML/GeoJSON exports, and local-only experimental artifacts remain private unless a later phase explicitly adds a reviewed redaction or preview path.

## Output Root Layout

Recommended Phase 1 run-local layout:

```text
data/runs/<run_id>/
  app_native/
  parity/
    root/
    DEM_GEO8_TIFS/
    GEOTIFF_RADAR_BANDS/
    NPY_RADAR_BANDS/
    NPY_STACKS/
    OPT/
    QA/
    kmz/
    maps/
    navigation/
    experimental/
  manifests/
```

The `app_native/` directory is a future organization point for existing app outputs if a later phase needs it. Phase 1 helpers create only the standard parity and manifest directories requested by this contract. They do not write rasters or call the pipeline.

All helper-resolved paths must stay under `data/runs/<run_id>/`. Path traversal and absolute output paths are invalid.

## Manifest Schema

Parity manifests are JSON files written under:

```text
data/runs/<run_id>/manifests/parity_manifest.json
```

Minimum schema:

| Field | Meaning |
| --- | --- |
| `schema_version` | Manifest schema identifier. Current value: `parity_manifest_v1`. |
| `run_id` | Run identifier supplied by the caller. |
| `created_at` | ISO-8601 timestamp for manifest write time. |
| `parity_root` | Run-relative parity root, currently `parity`. |
| `entries` | Array of parity output entries. |

Each entry must support:

| Field | Meaning |
| --- | --- |
| `source_path` | Run-relative app-native or source artifact path when known. |
| `parity_path` | Run-relative parity artifact path or intended alias path. |
| `notebook_name_or_pattern` | Original notebook output name or pattern preserved for parity. |
| `family` | Output family from the Phase 0 inventory. |
| `classification` | Output classification such as notebook-parity, QA/provenance, coordinate-bearing, semantic/report raster, app-native, experimental/private, or probability-classifier output. |
| `target_mode` | One of `core_app`, `notebook_parity`, `experimental_private`, `public_shared`, or `not_applicable`. |
| `artifact_class` | One of `LOCAL_SENSITIVE`, `REDACTED_PUBLIC`, `PREVIEW_ONLY`, or `FILESYSTEM_ONLY`. |
| `http_servable` | Whether this parity entry is allowed for HTTP serving. Phase 1 helpers default this to `false`. |
| `requires_coordinates` | Whether the artifact contains or trivially recovers coordinates. |
| `probability_only_required` | Whether interpreted classifier/model output wording must be probability-only. |
| `runtime_output_verified` | Whether runtime output presence has been proven. |
| `notebook_value_parity_verified` | Whether notebook-value parity has been proven. |
| `notes` | Free-form private implementation or verification notes. |

The manifest may add fields in later phases, but Phase 1 helpers must not default any entry to public/shared exposure.

## Artifact Classification Expectations

Every parity manifest entry records both a mode and an artifact class. The artifact class describes storage and serving policy; the mode describes why the entry exists.

Phase 1 does not alter the existing app artifact taxonomy:

| Class | Phase 1 parity expectation |
| --- | --- |
| `LOCAL_SENSITIVE` | Private local artifacts that may only be considered for existing loopback-safe serving policy in later phases. |
| `REDACTED_PUBLIC` | Redacted artifacts only. Phase 1 does not create any. |
| `PREVIEW_ONLY` | Non-georeferenced previews only. Phase 1 does not create any. |
| `FILESYSTEM_ONLY` | Local-only artifacts, including classifier outputs, KMZ/KML, coordinate-bearing map exports, and experimental/private outputs. |

No artifact may be written without a class. Phase 1 helper manifests record intended classes only; they do not register DB artifact rows and do not serve files.

## Coordinate-Bearing Handling

Coordinate-bearing artifacts include KMZ/KML, GeoJSON, exact map exports, coordinate-bearing CSV columns, geometry, bounds, CRS transforms, and any output that exposes or trivially recovers exact coordinates.

Phase 1 handling rules:

- Coordinate-bearing parity entries must set `requires_coordinates=true`.
- Coordinate-bearing parity entries must not default to HTTP serving.
- KMZ/KML/GeoJSON parity outputs belong in filesystem-only private paths unless a later reviewed phase defines a redacted replacement.
- Public/shared exposure is not decided in Phase 1.

## Classifier And Model Wording

Classifier/model interpreted outputs must use probability-only wording. Future classifier/model parity entries may express class probabilities, probability bands, heuristic scores, uncalibrated model probabilities, or calibrated model probabilities.

Classifier/model entries that represent interpreted outputs must set `probability_only_required=true`. Calibration is a separate later-phase design decision and is not implied by Phase 1.

## Semantic And Report Raster Stages

`app/pipeline/stages/secret_layers.py` is classified for parity planning as a notebook-parity semantic raster stage, not clean defensible core by default.

`app/pipeline/stages/report_640.py` is classified for parity planning as a notebook-parity report/semantic raster stage, not clean defensible core by default.

These classifications are recorded so later phases can preserve notebook semantics without silently promoting those outputs into the public/shared or defensible-core surface.

## Phase 1 Non-Goals

Phase 1 does not:

- integrate parity mode into the live pipeline;
- write real raster, tensor, CSV, GeoJSON, KMZ, KML, or model outputs;
- call Earth Engine;
- change stage formulas or data-selection rules;
- change candidate scoring or classifier behavior;
- change API routes, frontend files, database models, migrations, or artifact serving helpers;
- rename, remove, or sanitize existing app outputs;
- decide public/shared exposure for notebook-parity artifacts.

The Phase 1 helper surface exists so later phases can add notebook-compatible aliases and manifests consistently after separate implementation review.
