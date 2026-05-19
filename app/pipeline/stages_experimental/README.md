# Experimental Module

This package is local-only, experimental, and env-gated.

## Rules

- Import requires `ENABLE_EXPERIMENTAL=1`.
- No API routes, frontend controls, background task hooks, or orchestrator hooks may invoke this package.
- Neutral class identifiers only: `Class_A` through `Class_N`.
- No scientific validation claim is made for this module at M14.

## Milestone Scope

- M14 provides only the import gate, neutral class vocabulary, and neutral classifier surface.
- CLI entrypoints, input validation, and filesystem outputs are deferred to M15.
