# V6 Package — Generation Scope

## Purpose

Scope what it would take to **generate** the v6 paid-archive candidate package from a
completed core run, closing the highest-value open parity family.

This is a scope/feasibility document for a future, separately-approved slice. It does **not**
reopen the closed Phase 10 roadmap and is **not** approval to build. It complements (does not
replace) `docs/V6_PACKAGE_PARITY_CONTRACT.md`, which covers the already-implemented *import*
side.

## Current state vs the gap

**Done (Phase 2 — import/validate/rebuild).** `app/pipeline/parity/v6_package.py`
(`import_v6_package`) ingests a v6 package the **notebook already produced** (directory or
zip), validates filenames + minimal CSV columns (`CSV_REQUIRED_COLUMN_GROUPS`) + GeoJSON
`FeatureCollection` shape (`_validate_geojson`), copies files into `parity/root/` +
`parity/maps/`, hashes them, writes `v6_package_import_manifest.json`, and can rebuild the
zip (`_write_rebuilt_zip`). It explicitly **does not run Earth Engine, generate candidate
rankings, or interpret claims**.

**Missing (generation).** The app cannot *produce* any of the 12 component files from a run.
Today it can only re-package notebook-made outputs. Closing the family means building the
computation that turns a core run into candidates → rankings → request zones → quotes →
summary → inspection map → package.

## Hard dependencies (gate the whole family)

1. **Frozen notebook v6 reference package** (operator-owned, outside git) to lock the *exact*
   full schemas and provide value-parity ground truth. The current CSV validation is
   deliberately minimal (identifying columns only); the full field sets are unknown.
   See `docs/D1_REAL_REFERENCE_COLLECTION_OUTSIDE_GIT.md`.
2. **Formula source-lock.** The ranking, zone-clustering, and quote-row formulas must be
   recovered from the notebook source, not guessed (Phase 10 Future Work Rule: "do not guess
   formulas from nearby outputs"). Mirror the DEM-curvature recovery pattern
   (`docs/DEM_CURVATURE_PARITY_RECONSTRUCTION.md`).

Until both exist, generation cannot reach proven notebook-value parity.

## File-by-file output spec

12 component files + the rebuilt zip. "Known" columns come from
`v6_package.py:CSV_REQUIRED_COLUMN_GROUPS`; "lock" columns come from `gaps.md` §7.2–7.4 and
must be confirmed against the frozen reference before implementation.

| File | Family | Format | Known columns | Columns to source-lock |
|---|---|---|---|---|
| `lawful_gee_candidate_scout_top_25_<timestamp>.csv` | candidate/ranking | CSV | one of `candidate_id`/`object_id`/`id` | full ranking field set |
| `lawful_gee_candidate_scout_top_25_<timestamp>.geojson` | coordinate/map | GeoJSON FC | — | feature props |
| `top25_enhanced_v6.csv` | candidate/ranking | CSV | id + (`candidate_score`/`review_priority_score`) | `quality_adjusted_score`, `confidence_score_all`, `stability_score`, `season_*`, `balanced_rank`, `visibility/contrast/terrain_heavy_rank`, `score_gap_*`, `false_positive_warning_count` |
| `top25_enhanced_v6.geojson` | coordinate/map | GeoJSON FC | — | feature props |
| `stable_candidate_priority_list_v6.csv` | candidate/ranking | CSV | id + (`review_priority_score`/`candidate_score`) | stability/season aggregation fields |
| `quality_diagnostics_all_cells_v6.csv` | candidate/ranking | CSV | one of `cell_id`/`candidate_id`/`object_id`/`id` | per-cell diagnostics |
| `request_zones_v6.csv` | request-zone | CSV | `zone_id` | geometry, centroid, area, member candidate IDs/count, max score, mean review-priority, max confidence, min false-positive count, reason summary, recommended imagery specs |
| `request_zones_v6.geojson` | coordinate/map | GeoJSON FC | — | zone feature props |
| `paid_imagery_quote_template_v6.csv` | quote | CSV | `zone_id` | provider, sensor, resolution, acquisition date, cloud cover, off-nadir, license, price, delivery time, coverage score, metadata completeness, notes |
| `paid_imagery_quote_comparison_v6.csv` | quote | CSV | `zone_id` | per-provider comparison fields |
| `paid_archive_request_summary.txt` | v6 package | text | — | summary template |
| `visual_inspection_map.html` | coordinate/map | HTML | — | static/offline render |
| `paid_archive_request_candidate_package_FINAL_v6_ZONES_QUOTES.zip` | v6 package | zip | — | member set = the files above |

The required input set is encoded today in `v6_package.py:V6_REQUIRED_INPUT_FILES` +
`TIMESTAMPED_TOP25_PREFIX`; generation must produce every one of those.

## Inputs from a core run

- Candidate seeds: `app/pipeline/stages/object_extract.py` → `objects_index.csv`,
  `clusters_summary.csv`, `objects/object_mask.npy` (note: app-native, **not** a v6 ranking
  replacement).
- Anomaly energy: `app/pipeline/stages/pca_anomaly.py` → `pca_anomaly.tif`.
- Features for scoring: the hypercube (`app/pipeline/stages/hypercube.py`).
- Geo/grid for centroids + GeoJSON/HTML: `grid_manifest.json` + `app/services/grid.py`.

## Data model / persistence

All v6 outputs are coordinate-bearing → `ArtifactClass.FILESYSTEM_ONLY`,
`http_servable=False` (`app/db/models/enums.py`; enforced by
`app/services/artifact_policy.can_serve_artifact`, which blocks `FILESYSTEM_ONLY` always).
The quote CSVs are not coordinate-bearing but stay package-private for consistency.

**Recommendation:** filesystem-parity-only first (matches the Phase 2 import contract and
the `parity/` tree), deferring any DB candidate/zone/quote records to a later slice. This
keeps generation aligned with existing redaction and serving policy and adds no public
surface.

## Suggested sub-phases (each a separately-approved slice)

| Slice | Scope | Effort |
|---|---|---|
| **V6-G0** | Freeze a notebook v6 reference package (operator, outside git). Prereq for all below. | S (operator) |
| **V6-G1** | Source-lock ranking + zone-clustering + quote formulas → recovery doc. | M |
| **V6-G2** | Candidate ranking generation: `top25_enhanced_v6.*`, `stable_candidate_priority_list_v6.csv`, `quality_diagnostics_all_cells_v6.csv`, `lawful_gee_candidate_scout_top_25_<timestamp>.*`. | L |
| **V6-G3** | Request-zone generation: cluster candidates → `request_zones_v6.csv/.geojson`. | L |
| **V6-G4** | Quote template + comparison + `paid_archive_request_summary.txt`. | M |
| **V6-G5** | `visual_inspection_map.html` (offline, no CDN). | M |
| **V6-G6** | `V6GenerationStage` wiring + rebuild zip + Phase 9 value-parity vs frozen reference. | M |

G2/G3 are gated on G0+G1; nothing reaches proven parity before G0.

## Stage wiring

Add a `V6GenerationStage` after `ObjectExtractStage`/`PcaAnomalyStage` in the stage list in
`app/api/runs.py` (`enqueue_core_pipeline_run`, ~L379–410). Implement against the `Stage`
base in `app/pipeline/_base.py` (set `name`, `parity_category`, return `StageResult` with
`StageArtifact`s carrying an explicit `artifact_class`); the orchestrator validates the
registry and persists artifacts (`app/pipeline/orchestrator.py`).

Reuse existing helpers — do not re-derive:

- `app/pipeline/parity/v6_package.py`: `_write_rebuilt_zip`, import manifest writer,
  `_validate_csv_columns`, `_validate_geojson`.
- `app/pipeline/parity/__init__.py`: `ensure_standard_parity_dirs`,
  `resolve_parity_output_path`, `write_parity_manifest`, `ParityManifestEntry`
  (mark `requires_coordinates=true`, `artifact_class=FILESYSTEM_ONLY`,
  `target_mode=notebook_parity`, `http_servable=false`).
- Output layout: `parity/root/` for CSV/TXT/zip, `parity/maps/` for the HTML.

## Test plan

- **Schema (unit):** extend `CSV_REQUIRED_COLUMN_GROUPS` to the full locked schema; assert
  every generated CSV has it. Reuse `_validate_geojson` for the three GeoJSON files.
- **Determinism:** same run → identical ranking (stable sort by id) and identical zone IDs.
- **Round-trip:** generate → `import_v6_package` → `rebuild_zip=True` → assert stable sha256
  and `missing_required_files == []`.
- **Value parity:** Phase 9 harness (`docs/PHASE_9_END_TO_END_PARITY_HARNESS.md`) vs the
  frozen reference — file presence, columns, row counts, numeric tolerance for scores,
  zone-geometry tolerance.
- **Artifact class:** every v6 artifact is `FILESYSTEM_ONLY` and never served (pattern in
  `tests/integration/test_artifact_serving.py`).
- **Redaction:** confirm no v6 coordinate columns or zone geometry can leak into an API
  response (the outputs are filesystem-only and absent from artifact listings).
- Location: `tests/parity/` (alongside the existing `tests/parity/test_v6_package.py`).

## Non-goals / safety

- No public exposure or HTTP serving of any v6 output.
- No Earth Engine beyond the existing core acquisition path.
- No claim-confirmation wording; candidate scores are probabilities/scores only
  (`docs/PARITY_MODE_CONTRACT.md`).
- No formula guessing — generation waits on V6-G1 source-lock.
- No change to artifact-serving policy, existing output names, or core stage formulas.
