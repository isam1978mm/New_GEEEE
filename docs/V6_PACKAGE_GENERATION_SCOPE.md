# V6 Package Generation Scope

## Purpose

This document defines the scope, gates, and boundaries for the V6 paid-archive package generation track. It does not start V6 generation. It does not implement V6-G0 or V6-G1. It exists to scope the work so that Track A can proceed without scope drift.

## V6 Package Overview

The V6 package is a paid-archive request candidate bundle produced by the notebook. It contains 12 component files:

- `lawful_gee_candidate_scout_top_25_<timestamp>.csv` / `.geojson`
- `top25_enhanced_v6.csv` / `.geojson`
- `quality_diagnostics_all_cells_v6.csv`
- `stable_candidate_priority_list_v6.csv`
- `request_zones_v6.csv` / `.geojson`
- `paid_imagery_quote_template_v6.csv`
- `paid_imagery_quote_comparison_v6.csv`
- `paid_archive_request_summary.txt`
- `visual_inspection_map.html`

These files are coordinate-bearing parity artifacts. They are treated as `FILESYSTEM_ONLY` and are never served over HTTP.

## What the App Currently Does

The app currently **imports, validates, and rebuilds** notebook-made v6 packages only. It does **not** generate the 12 component files. This is handled by:

- `app/pipeline/parity/v6_package.py` — import/rebuild logic.
- `docs/V6_PACKAGE_PARITY_CONTRACT.md` — the import/rebuild contract.

The app does not compute:
- candidate rankings,
- zone definitions,
- quote formulas,
- or any v6-specific business logic.

## Gates

### V6-G0 — Frozen Reference Package

Before V6 generation code can begin, the operator must freeze a notebook v6 reference package **outside Git**.

Requirements:
1. A complete notebook v6 package is captured and stored in a reference bundle directory.
2. The reference bundle is versioned and checksum-verified.
3. The reference bundle is accessible to the parity verification harness.

Status: **NOT COMPLETE** — operator must provide the frozen reference package.

### V6-G1 — Source-Lock Formulas

Before V6 generation code can begin, the ranking, zone, and quote formulas must be source-locked from the notebook.

Requirements:
1. The notebook source cells that compute candidate rankings are identified and cited.
2. The notebook source cells that define request zones are identified and cited.
3. The notebook source cells that compute quote values are identified and cited.
4. Formulas are documented with their exact parameters, normalization, and sign conventions.
5. Frozen reference outputs exist for numeric comparison.

Status: **NOT COMPLETE** — formula source-lock is pending.

## Scope Boundaries

What V6 generation will do (when both V6-G0 and V6-G1 are complete):
- Generate the 12 component files from app-computed data.
- Validate minimum CSV columns and GeoJSON shape.
- Compute SHA256 and byte-size records.
- Write `v6_package_import_manifest.json` and update `parity_manifest.json`.
- Optionally rebuild `paid_archive_request_candidate_package_FINAL_v6_ZONES_QUOTES.zip`.
- Mark all entries as `FILESYSTEM_ONLY`, `http_servable=false`, `requires_coordinates=true`.

What V6 generation will NOT do:
- Change raster math, SAR math, Sentinel-2 formulas, DEM formulas, PCA logic, object extraction logic, or classifier logic.
- Run Earth Engine.
- Change API routes, frontend files, database models, migrations, artifact serving policy, or existing output names.
- Add public/shared exposure for v6 package files.
- Decide which parity outputs belong in the clean app UI.
- Implement classifier/model logic.

## Relationship to Existing Contracts

- `docs/V6_PACKAGE_PARITY_CONTRACT.md` — Phase 2 import/rebuild contract.
- `docs/SAFE_NOTEBOOK_CAPABILITY_PHASES.md` — seven-phase parent plan.
- `docs/PARITY_OPEN_ITEMS_PRIORITIZED_CHECKLIST.md` — prioritized open items.
- `AGENTS.md` — hard safety rules and redaction contract.

## Deferral Statement

V6 generation is intentionally deferred until both V6-G0 and V6-G1 are complete. Do not start V6 generation code. Do not create V6 generation routes, BackgroundTasks, or core-orchestrator hooks. Do not add V6 package files to the public DTO schema.

(End of V6_PACKAGE_GENERATION_SCOPE.md.)
