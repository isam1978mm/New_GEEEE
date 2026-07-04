# Neutral Classifier Module

This package contains the neutral classifier primitives and legacy CLI wrapper.
The normal app workflow invokes the classifier through
`app.pipeline.stages.classifier.ClassifierStage`.

## Rules

- Package import does not require an environment flag.
- Normal pipeline execution runs the classifier after object extraction and before alignment QA.
- The CLI remains available for manual re-runs:
  `python -m app.pipeline.stages_experimental.run --run-id <id>`.
- Neutral class identifiers only: `Class_A` through `Class_N`.
- Outputs write under `<run_dir>/experimental/` and are redacted public artifacts.
- No scientific validation claim is made for this module.

## Current Surface

- `inputs.py` validates a completed core run, required artifacts, allowed artifact classes, and grid consistency before classification.
- `classifier.py` produces neutral class assignments from validated core artifacts.
- `outputs.py` writes redacted public summaries and neutral target-label outputs under the run's `experimental/` directory.
