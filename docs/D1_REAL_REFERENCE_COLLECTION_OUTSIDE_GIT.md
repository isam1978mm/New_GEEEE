# D1 — Real Frozen Reference Collection (Outside Git)

Date: 2026-06-08
Status: Operator collection workflow prepared — real references still outside Git

## Purpose

D1 moves from scaffold/plan to an **operator-ready** workflow for collecting frozen
notebook reference bundles **outside Git**. It documents the directory layout,
manifest schema, safety rules, and a local validator — without committing any real
reference artifact, manifest, coordinate, geometry, hash, or private path.

This document does **not** mark notebook-value parity as passed. Parity remains
`false` until the real Phase E / E3 / E4 verifiers actually pass against real
outside-Git references.

## Strict Boundary

This workflow:

- Does **not** commit reference artifacts.
- Does **not** commit private notebook outputs.
- Does **not** commit coordinates, geometry, exact locations, bounds, or CRS transforms.
- Does **not** commit hashes or private filesystem paths.
- Is **not** H3 training.
- Is **not** H4 private inference.
- Is **not** ML training of any kind.
- Does **not** add public overlay exposure or artifact-serving routes.
- Is **not** VPS deployment or real auth provider activation.

## Outside-Git Directory Layout

The operator keeps each bundle under the Git-ignored `data/` tree:

```text
data/private_references/notebook_frozen/<bundle_id>/
  manifest.local.json
  artifacts/
  logs/
```

`data/` is Git-ignored and operator-owned. Nothing under
`data/private_references/` is ever committed. (This aligns with the existing
scaffold plan in `docs/FUTURE_SLICE_D1_FROZEN_REFERENCE_BUNDLE_COLLECTION_PLAN.md`,
which uses `data/notebook_references/` for the scaffold helper; both roots live
under the Git-ignored `data/` tree and must stay out of Git.)

## What the Operator Collects Manually

For each frozen reference bundle, the operator records, **outside Git**:

- The exact notebook version identifier (version tag or commit/hash kept locally).
- The input fixture IDs or source run IDs the notebook consumed.
- The expected output artifacts, grouped by family, under `artifacts/`.
- The manifest metadata (see schema below) as `manifest.local.json`.
- Optionally, a local checksum file for the operator's own integrity checks —
  **kept local, never committed**, and never referenced by committed files.

## Minimum Manifest Schema

`manifest.local.json` (local only) must contain at least:

| Field                 | Meaning                                                        |
|-----------------------|----------------------------------------------------------------|
| `bundle_id`           | Stable local identifier for the bundle.                        |
| `notebook_name`       | Name of the source notebook.                                   |
| `notebook_version`    | Version tag / commit identifier (kept local).                  |
| `collected_at`        | ISO timestamp when the bundle was collected.                   |
| `operator`            | Who collected it (local identifier).                           |
| `source_run_id`       | The source run id the references derive from.                  |
| `artifact_families`   | List of family names present in `artifacts/`.                  |
| `local_artifact_paths`| List of **local** paths under `data/private_references/...`.   |
| `notes`               | Free-text operator notes (no coordinates/geometry/hashes).     |

The manifest must **not** contain coordinates, geometry, bounds, bbox, latitude,
longitude, CRS, transform, or hash/sha256 fields. The validator fails on those keys.

A placeholder example (local-only, fake values) is provided at
`docs/examples/d1-reference-manifest.local.example.json`.

## Safety Requirements

- Local filesystem paths only in the local manifest (no URLs).
- No public response exposure of any reference content.
- No artifact-serving route is added or used.
- No notebook-value parity success may be claimed until the real verifier passes.
- Bundle artifacts are `FILESYSTEM_ONLY`: not HTTP-servable, not frontend-visible,
  not downloadable via API.

## Local Manifest Validator

Script: `scripts/d1_validate_reference_manifest.py` (standard library only;
no network; no file writes; never reads artifact contents).

```bash
# Validate a local manifest (human-readable):
uv run python scripts/d1_validate_reference_manifest.py --manifest <path-to-manifest.local.json>

# Strict mode (exit nonzero on any FAIL):
uv run python scripts/d1_validate_reference_manifest.py --manifest <path> --strict

# Machine-readable safe JSON summary:
uv run python scripts/d1_validate_reference_manifest.py --manifest <path> --json
```

The validator:

- Requires all minimum-schema keys.
- Rejects URL-like artifact paths.
- Rejects absolute artifact paths outside `data/private_references` (unless
  `--allow-external` is passed, which downgrades to a warning).
- **Fails** if the manifest carries any suspicious key (`coordinates`, `geometry`,
  `bounds`, `bbox`, `latitude`, `longitude`, `lat`, `lon`, `crs`, `transform`,
  `sha256`, `hash`) anywhere, including nested objects.
- Warns that references are outside Git.
- Prints no artifact contents.

## Collection Checklist

```text
[ ] choose a private bundle root under data/private_references/notebook_frozen/<bundle_id>/ (outside Git)
[ ] create artifacts/ and logs/ subfolders
[ ] record the exact notebook version identifier locally
[ ] record source run id / input fixture ids
[ ] place expected output artifacts under artifacts/, grouped by family
[ ] write manifest.local.json with all minimum-schema fields
[ ] keep any checksum file local and uncommitted
[ ] confirm no coordinates/geometry/hashes appear in the manifest
```

## Validation Checklist

```text
[ ] uv run python scripts/d1_validate_reference_manifest.py --manifest <local manifest> --strict  → OK
[ ] confirm artifact paths are local and under data/private_references
[ ] confirm no suspicious keys present
[ ] confirm nothing under data/private_references is staged for commit
[ ] DO NOT claim notebook-value parity — defer to Phase E / E3 / E4 verifiers
```

## Status Flags

```text
Real frozen references collected:   operator-owned outside Git only
Notebook-value parity verified:     false until real verifier passes
H3 training:                        blocked
H4 private inference:               blocked
Public location overlay exposure:   blocked
```

## Closeout

D1-real provides the operator collection workflow, a local-only manifest example,
and a guarded validator. No real references, manifests, coordinates, geometry,
hashes, or private paths are committed. Notebook-value parity remains **false**
and is decided only by the later real verifiers:

- `app/pipeline/parity/frozen_reference_verifier.py` (Phase E)
- `app/pipeline/parity/semantic_feature_comparator.py` (Phase E3)
- `app/pipeline/parity/private_map_artifact_comparator.py` (Phase E4)

H3/H4 and public location overlay exposure remain blocked.
