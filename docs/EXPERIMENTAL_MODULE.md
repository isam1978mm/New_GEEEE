# Experimental Module

The experimental classifier is included in v1 only as a quarantined research module.

## Execution boundary

- Import requires `ENABLE_EXPERIMENTAL=1`.
- The only supported invocation is:

```bash
ENABLE_EXPERIMENTAL=1 python -m app.pipeline.stages_experimental.run --run-id <id>
```

- The API must not import or expose it.
- The frontend must not invoke it or display its outputs.
- Background tasks must not invoke it.
- The core orchestrator must not invoke it.

## Inputs

`inputs.py` validates:

- the referenced run exists
- the run status is `done`
- required core artifacts exist
- required artifact classes are acceptable
- required raster and array inputs remain GRID-consistent

Classifier execution stops before `classifier.py` runs if validation fails.

## Outputs

`outputs.py` writes only under:

`./data/runs/<run_id>/experimental/`

Every experimental artifact is recorded as `FILESYSTEM_ONLY` with `http_servable=False`.

These outputs are never listed, previewed, tiled, or downloaded through HTTP.

## Terminology

App-side code, tests, filenames, logs, and outputs use only neutral identifiers such as `Class_A` through `Class_N`.

The mapping to source-notebook classifier labels exists only in [CLASS_MAPPING.md](/C:/Dev/New_GEE/docs/CLASS_MAPPING.md).
