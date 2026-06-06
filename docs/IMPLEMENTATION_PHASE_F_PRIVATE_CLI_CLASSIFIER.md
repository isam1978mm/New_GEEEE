# Implementation Phase F Private CLI Classifier

Phase F adds a private, CLI-only classifier report path for local operator use.

## Implemented Capability

The implementation module is:

`app/pipeline/parity/private_cli_classifier.py`

The module can be run with:

```text
python -m app.pipeline.parity.private_cli_classifier --run-dir <run_dir> --input-manifest <manifest.json> --run-id <run_id> --enable-experimental-classifier
```

The CLI writes one private JSON report under:

```text
data/runs/<run_id>/manifests/private_neutral_classifier_report.json
```

## Experimental Gate

Phase F requires explicit experimental enablement through either:

- `--enable-experimental-classifier`
- `ENABLE_EXPERIMENTAL_CLASSIFIER=1`

Without one of those controls, the module writes a disabled private report and
does not produce score rows.

## Input Schema

The input manifest is a private local JSON file under the run directory. It uses:

```text
schema_version=phase_f_private_classifier_inputs_v1
```

Each item supplies:

- `input_family`
- `score`

The implementation validates that the manifest stays under the run directory and
rejects path traversal.

## Output Schema

Output rows use neutral labels only:

- `Class_A`
- `Class_B`
- `Class_C`
- later `Class_*` identifiers

Allowed row fields are:

- `class_id`
- `class_label`
- `score`
- `probability`
- `normalized_score`
- `uncertainty`
- `rank`
- `input_family`
- `method`
- `warnings`
- `runtime_output_verified`
- `notebook_value_parity_verified`

The first implementation is a deterministic private score aggregation over local
manifest values. It does not invent model science, train models, or run
deep-learning inference.

## Runtime And Parity Status

`runtime_output_verified` can be true only when the local private report is
written by the enabled CLI path.

`notebook_value_parity_verified` remains false. Frozen notebook references and a
later verifier are still required before notebook-value parity can pass.

## Safety Boundary

Phase F does not:

- expose classifier results through API
- expose classifier results through frontend
- expose classifier results through artifact-serving downloads
- call BackgroundTasks
- call the core run orchestrator
- call the normal live pipeline
- train models
- run deep-learning inference
- download model weights
- add heavy ML dependencies
- use public coordinate overlays
- call Earth Engine
- use Colab
- use Google Drive
- start backend runs
- generate rasters or map artifacts
- change raster or math logic
- implement Special Track G, H, I, or J behavior

The private report redacted summary omits exact coordinates, geometry, local
filesystem paths, download references, hashes, and public serving fields.

Special Track G handles exact-coordinate public overlay access-control design
later. Special Track H handles deep-learning model feasibility later. Special
Track I handles real dataset and training design later. Special Track J handles
full Tesla flow decomposition later.
