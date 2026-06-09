# Safe Notebook Capability Phases

## Purpose

This document is the parent safety/capability plan for the GEE Screening App. It defines seven capability phases that separate what is safe to run on a local PC (private research mode) from what is safe to deploy on a VPS (safe deployment mode). Each phase is ordered by dependency and risk, not by estimated duration.

## Deployment Modes

- **Local PC = private research mode**: Full notebook-parity diagnostics, raw classifier outputs, local-only KMZ/GeoJSON, and offline AI research modules are permitted. No public exposure.
- **VPS = safe deployment mode**: Only redacted public outputs, defensible pipeline stages, and approved artifact serving. No coordinate-bearing outputs, no raw classifier artifacts, no notebook-parity files exposed over HTTP.

## The Seven Phases

### Phase 1 — Safe Run File Inspector

Goal: give operators a local-only, safe way to inspect run directories and diagnose missing artifacts, extra files, disk-usage drift, and manifest consistency without exposing coordinates, paths, or hashes.

Scope:
- `app/services/run_file_inspector.py` — run-directory scanner that reads only `./data/runs/<run_id>/`.
- `app/cli/run_diagnostics.py` — CLI entrypoint `python -m app.cli.run_diagnostics --run-id <id>`.
- Redacted public diagnostic DTOs that pass the redaction contract.
- No arbitrary filesystem scanning; every path is validated against the run boundary.
- No exact coordinates in any public API/frontend response.
- Diagnostic output is local-safe; if reused publicly it must be redacted first.

Status: **Implemented.**

### Phase 2 — Safe Map Point Picker

Goal: implement a safe ROI selection UI that never exposes exact coordinates in public responses.

Status: **Deferred.** Depends on Phase 1 completion.

### Phase 3 — Local-only KMZ / GeoJSON / Field Package

Goal: generate private map artifacts and field-operation packages that are never served over HTTP.

Scope:
- Private KMZ/GeoJSON writers under `app/pipeline/parity/private_map_artifact_writers.py`.
- All outputs are `FILESYSTEM_ONLY` with `http_servable=false`.
- No public API routes or frontend download links.

Status: **Deferred.** Depends on Phase 2 and frozen reference outputs.

### Phase 4 — Local-private Raw Classifier plus VPS-safe Separation

Goal: implement the neutralized experimental classifier as a CLI-only, filesystem-only module that is never called by the web API or frontend.

Scope:
- `app/pipeline/stages_experimental/` contains all classifier logic.
- Requires `ENABLE_EXPERIMENTAL=1`.
- Runs only through `python -m app.pipeline.stages_experimental.run --run-id <id>`.
- Uses only neutral class identifiers (`Class_A`, `Class_B`, etc.).
- Writes outputs under `./data/runs/<run_id>/experimental/`.
- Never serves, lists, previews, tiles, or downloads classifier outputs through HTTP.

Status: **Implemented.**

### Phase 5 — Offline AI Research Module Only

Goal: provide a safe sandbox for AI/ML research that does not touch the live pipeline, public API, or production database.

Scope:
- No CNN, YOLO, Swin, or Unet code in the live pipeline.
- No automatic imagery ordering.
- No model training hooks in the core orchestrator.
- Any AI research code is confined to offline notebooks or isolated research directories.

Status: **Blocked by policy.** Not permitted in v1.

### Phase 6 — Stable Formula Contracts for Deferred Feature Stacks

Goal: lock all notebook-parity formulas (DEM, SAR, S2, PAN, secret layers, etc.) so that later stages can be built with confidence.

Scope:
- `docs/NOTEBOOK_PARITY_FULL_CHECKLIST.md` remains the authoritative source of truth.
- Each formula must have either `authoritative_formula_found` or `exact_formula_found` status.
- Frozen reference outputs must be collected outside Git.
- Numeric tolerance contracts must be defined before value parity is claimed.

Status: **In progress.** See `docs/PARITY_OPEN_ITEMS_PRIORITIZED_CHECKLIST.md`.

### Phase 7 — Run Diagnostics CLI

Goal: provide a standalone CLI tool for operators to diagnose run health, disk usage, and artifact consistency.

Scope:
- `app/cli/run_diagnostics.py` — the CLI entrypoint.
- `python -m app.cli.run_diagnostics --run-id <id>`.
- JSON output to stdout on success, stderr on failure.
- Exit code 0 on success, 1 on failure.
- Default output is redacted and passes `verify_redacted()`.
- No API routes, no frontend UI, no BackgroundTasks.

Status: **Implemented.**

## Cross-Reference

- `docs/PARITY_OPEN_ITEMS_PRIORITIZED_CHECKLIST.md` — derived status snapshot of open parity items grouped by actionability.
- `docs/V6_PACKAGE_GENERATION_SCOPE.md` — scope and gating for the V6 paid-archive package track.
- `docs/NOTEBOOK_PARITY_FULL_CHECKLIST.md` — authoritative notebook-parity roadmap.
- `AGENTS.md` — hard safety rules and redaction contract.

(End of SAFE_NOTEBOOK_CAPABILITY_PHASES.md.)
