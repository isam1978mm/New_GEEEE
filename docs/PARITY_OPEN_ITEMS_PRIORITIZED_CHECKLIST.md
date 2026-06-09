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
- [ ] Disk-usage scan: update `disk_usage_bytes` and `output_file_count` on run completion.

## Group B — Blocked on Frozen Notebook Reference / EE Source

These items have formulas or code in place but cannot claim notebook-value parity until a frozen reference output is available.

- [ ] DEM curvature Laplacian (`curv_laplacian_640.tif`) — runtime implemented, pending reference comparison.
- [ ] DEM plan curvature (`curv_plan_640.tif`) — formula implemented from notebook source, pending reference comparison.
- [ ] DEM profile curvature (`curv_profile_640.tif`) — formula implemented from notebook source, pending reference comparison.
- [ ] SAR ASC/DESC support stack recovery and verification.
- [ ] S1 filtered layers stack parity verification.
- [ ] PAN components parity verification.
- [ ] PAN layers stack parity verification.
- [ ] Secret layers parity verification.
- [ ] Report 640 parity verification.
- [ ] AI-ready anomaly fraction parity verification.
- [ ] AI-ready metal hardness parity verification.
- [ ] AI-BEH anchor pattern decision.
- [ ] AI-BEH alloy statue parity verification.
- [ ] AI-BEH rare material parity verification.
- [ ] AI-BEH density artifact parity verification.
- [ ] AI-BEH logic parity verification.
- [ ] AI-BEH extended parity verification.
- [ ] AI-BEH relation parity verification.

## Group C — Blocked by Policy / Safety or Structurally Not Reproduced

These items are either blocked by safety policy, out of scope for v1, or structurally not reproducible in the app.

- [ ] Phase 5 — Offline AI research module only (blocked by policy: no CNN/YOLO/Swin/Unet in live pipeline).
- [ ] V6 package **generation** — blocked until V6-G0 and V6-G1 are complete.
  - V6-G0 = operator freezes notebook v6 reference package **outside Git**.
  - V6-G1 = source-lock ranking / zone / quote formulas from notebook source.
- [ ] Public KMZ/GeoJSON download routes (blocked by policy: coordinate-bearing artifacts must remain filesystem-only).
- [ ] Operator overlay private preview (blocked by auth implementation order).
- [ ] PostgreSQL migration (blocked by v1 policy: SQLite only).
- [ ] Docker deployment (blocked by v1 policy: no Docker).
- [ ] Redis/Celery/RQ worker queue (blocked by v1 policy: BackgroundTasks only).

## Track A Status

Track A (Safe Run File Inspector + Run Diagnostics CLI) is **complete**. The following files are implemented and tested:

- `app/services/run_file_inspector.py`
- `app/cli/__init__.py`
- `app/cli/run_diagnostics.py`
- `tests/unit/test_run_file_inspector.py`
- `tests/unit/test_run_diagnostics_cli.py`

## V6 Generation Status

V6 generation code **must not begin** until both V6-G0 and V6-G1 are complete.

- **V6-G0**: Operator freezes the notebook v6 reference package outside Git. The app currently imports, validates, and rebuilds notebook-made v6 packages only. It does not yet generate the 12 v6 component files.
- **V6-G1**: Source-lock ranking, zone, and quote formulas from the notebook source. The app does not yet compute these values.

All v6 outputs are `FILESYSTEM_ONLY` and `http_servable=false`. No public API or frontend exposure exists.

## Cross-Reference

- `docs/SAFE_NOTEBOOK_CAPABILITY_PHASES.md` — the seven-phase parent safety/capability plan.
- `docs/V6_PACKAGE_GENERATION_SCOPE.md` — V6 generation scope and gating criteria.
- `docs/NOTEBOOK_PARITY_FULL_CHECKLIST.md` — authoritative notebook-parity roadmap.
- `AGENTS.md` — hard safety rules and redaction contract.

(End of PARITY_OPEN_ITEMS_PRIORITIZED_CHECKLIST.md.)
