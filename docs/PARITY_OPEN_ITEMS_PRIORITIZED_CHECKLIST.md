# Parity Open Items — Prioritized Checklist

## Purpose

This checklist is a **derived status snapshot**, not the authoritative roadmap. It groups open parity and safety items by actionability so that the next work unit can pick the lowest-risk, highest-value item.

The authoritative notebook-parity roadmap remains:

- `docs/NOTEBOOK_PARITY_FULL_CHECKLIST.md`

Do not treat this file as a scope authority. When in doubt, read `docs/NOTEBOOK_PARITY_FULL_CHECKLIST.md` first.

## Group A — Actionable Now

These items are unblocked and can be picked up immediately.

- [x] Phase 1 — Safe Run File Inspector (`app/services/run_file_inspector.py` + CLI).
- [x] Phase 7 — Run Diagnostics CLI (`app/cli/run_diagnostics.py`).
- [ ] Add cross-links between `docs/SAFE_NOTEBOOK_CAPABILITY_PHASES.md`, `docs/PARITY_OPEN_ITEMS_PRIORITIZED_CHECKLIST.md`, and `docs/V6_PACKAGE_GENERATION_SCOPE.md`.
- [x] Verify all public DTOs pass `verify_redacted()`. (A4 harness: `tests/unit/test_public_safety_harness.py`)
- [x] Verify no API route directly streams files outside `serve_artifact_response()`. (A4 static/AST + integration tests)
- [x] Verify run-name sanitization rejects coordinate-like patterns. (A4 harness + integration tests)
- [x] Verify FastAPI validation errors do not echo request bodies. (A4 integration: `tests/integration/test_public_api_safety.py`)
- [x] Verify no coordinate-bearing CSV columns in public responses. (A4 harness DTO field tests)
- [x] Stale run cleanup: mark `running` runs as `stale_failed` on startup. (Verified: `app/services/run_state.py` + `app/main.py` lifespan; `tests/unit/test_run_state.py`, `tests/integration/test_startup_stale_run_cleanup.py`)
- [x] Disk-usage scan: update `disk_usage_bytes` and `output_file_count` on run completion. (Verified: `app/pipeline/orchestrator.py` persists disk summary on DONE/FAILED; `tests/unit/test_run_disk_summary.py`)

## Group B — Blocked on Frozen Notebook Reference / EE Source

These items have formulas or code in place but cannot claim notebook-value parity until a frozen reference output is available.

- [ ] DEM curvature Laplacian (`curv_laplacian_640.tif`) — runtime implemented, pending reference comparison.
- [ ] DEM plan curvature (`curv_plan_640.tif`) — formula implemented from notebook source, pending reference comparison.
- [ ] DEM profile curvature (`curv_profile_640.tif`) — formula implemented from notebook source, pending reference comparison.
- [ ] SAR ASC/DESC support stack recovery and verification.
- [ ] S1 filtered layers stack parity verification.
- [ ] PAN components parity verification.
- [ ] PAN layers stack parity verification.
- [ ] Private semantic raster family parity verification.
- [ ] Report 640 parity verification.
- [ ] AI-ready anomaly fraction parity verification.
- [ ] AI-ready neutral feature-family parity verification.
- [ ] AI-BEH neutral family parity verification.

## Group C — Blocked by Policy / Safety or Structurally Not Reproduced

These items are either blocked by safety policy, out of scope for v1, or structurally not reproducible in the app.

- [ ] Phase 5 — Offline AI research module only (blocked by policy: no CNN/YOLO/Swin/Unet in live pipeline).
- [ ] V6 paid-archive package — **wishlist / deferred; source-unverified**.
  - Not essential to the app's near-term screening purpose.
  - Not verified as an output of `notebooks/new.ipynb`.
  - Blocked until a separate originating V6 notebook/package is supplied.
  - Do not run B1/V6-G0 or B2/V6-G1 from `notebooks/new.ipynb`; there is no V6 package source to freeze or source-lock there.
- [ ] Public KMZ/GeoJSON download routes (blocked by policy: coordinate-bearing artifacts must remain filesystem-only).
- [ ] Operator overlay private preview (blocked by auth implementation order).
- [ ] PostgreSQL migration (blocked by v1 policy: SQLite only).
- [ ] Docker deployment (blocked by v1 policy: no Docker).
- [ ] Redis/Celery/RQ worker queue (blocked by v1 policy: BackgroundTasks only).

## Track A Status

Track A recovery and safety verification is **complete**. The implemented and verified slices are:

- A2 — Safe Run File Inspector + Run Diagnostics CLI.
- A3 — DEM curvature runtime outputs, with notebook-value parity still pending frozen reference comparison.
- A4 — Public safety verification harness.
- A5 — Stale running-run cleanup verification.
- A6 — Disk-usage scan verification on DONE/FAILED completion.

## V6 Status

V6 paid-archive package generation is no longer a near-term critical path item.

It is now classified as **wishlist / deferred** because the originating notebook/package has not been verified in this repo. `notebooks/new.ipynb` is the in-scope notebook for near-term parity work, and it has not been verified to generate V6 package outputs such as request zones, paid-imagery quotes, or the paid-archive package ZIP.

The existing importer/rebuilder code may remain, but no V6 generation, freezing, or formula-locking work should start until the operator supplies the real V6 source notebook or a real frozen package.

If V6 is revived later, the gated order is:

1. W1 — operator supplies the real V6 notebook/package source.
2. W2 — B1/V6-G0 freezes that package outside Git.
3. W3 — B2/V6-G1 source-locks ranking, zone, and quote formulas.
4. W4 — only then consider V6 generation work.

All V6 outputs must remain `FILESYSTEM_ONLY` and `http_servable=false`. No public API or frontend exposure is allowed.

## Cross-Reference

- `docs/SAFE_NOTEBOOK_CAPABILITY_PHASES.md` — the seven-phase parent safety/capability plan.
- `docs/V6_PACKAGE_GENERATION_SCOPE.md` — V6 wishlist/deferred status and revive gates.
- `docs/NOTEBOOK_PARITY_FULL_CHECKLIST.md` — authoritative notebook-parity roadmap.
- `AGENTS.md` — hard safety rules and redaction contract.

(End of PARITY_OPEN_ITEMS_PRIORITIZED_CHECKLIST.md.)
