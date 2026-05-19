# Experimental Module

This package is local-only, experimental, and env-gated.

## Rules

- Import requires `ENABLE_EXPERIMENTAL=1`.
- The only execution path is `python -m app.pipeline.stages_experimental.run --run-id <id>`.
- No API routes, frontend controls, background task hooks, or orchestrator hooks may invoke this package.
- Neutral class identifiers only: `Class_A` through `Class_N`.
- Outputs write only under `<run_dir>/experimental/` and are always `FILESYSTEM_ONLY`.
- No scientific validation claim is made for this module.

## Current Surface

- `inputs.py` validates a completed core run, required artifacts, allowed artifact classes, and grid consistency before classification.
- `classifier.py` produces neutral class assignments from validated core artifacts.
- `outputs.py` writes local filesystem-only summaries under the run's `experimental/` directory.
