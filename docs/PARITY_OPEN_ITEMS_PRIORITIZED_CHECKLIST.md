# Parity Open Items — Prioritized Checklist

## Purpose

A single prioritized, grouped view of every notebook-parity item that is **not yet closed**,
so the next slice can be chosen without re-deriving status from scattered docs.

This file is a **derived status snapshot**, not a new roadmap. The authoritative roadmap is
`docs/NOTEBOOK_PARITY_FULL_CHECKLIST.md` (closed at Phase 10). Any build here still needs its
own scoped, user-approved goal per
`docs/SELECTED_NOTEBOOK_CAPABILITIES_IMPLEMENTATION_ROADMAP.md`. Rows are reconciled from
`docs/parity_expected_outputs.json` (source of truth), `docs/NOTEBOOK_VS_APP_OUTPUTS.md`, and
`gaps.md`; where they disagree, the JSON wins.

## How to read this

**Status vocabulary** (from the JSON inventory):

- `missing` — no app writer identified.
- `partial` — some writer/alias exists; coverage incomplete.
- `unknown_needs_verification` — writer exists and runs, but notebook-value parity is unproven.
- `notebook_only_pending` — intentionally not in app source yet.
- `requires_external_dependency` — blocked on weights/training data/source.
- `broken_notebook_cell` — non-runnable notebook source; reference only.

**Grouping rule** (the three blocker types):

- **Group A — Actionable now:** `requires_external_dependency=false`, not policy-gated. A
  writer / alias / stack assembly can be built today from a normal run.
- **Group B — Blocked on a frozen notebook reference (and/or EE source):** cannot be *closed*
  without the operator-owned frozen reference bundle — either to build (missing source) or to
  prove notebook-value parity (`unknown_needs_verification`).
- **Group C — Blocked by policy/safety, or structurally not reproduced:** deliberate.

**Universal final gate:** every row's `notebook_value_parity_verified` is currently `false`.
Notebook-*value* parity for any family requires the operator-owned frozen reference bundle
(`docs/D1_REAL_REFERENCE_COLLECTION_OUTSIDE_GIT.md`,
`docs/FUTURE_SLICE_D1_FROZEN_REFERENCE_BUNDLE_COLLECTION_PLAN.md`). Group A means "build is
unblocked," not "parity is proven."

---

## Group A — Actionable now

| Item (id) | Priority | Status | What to build | Contract / module |
|---|---|---|---|---|
| v6 candidate ranking (`candidate_ranking_csv_geojson`) | **Critical** | partial | Generate `top25_enhanced_v6.*`, `stable_candidate_priority_list_v6.csv`, `quality_diagnostics_all_cells_v6.csv`, `lawful_gee_candidate_scout_top_25_<timestamp>.*` from object/PCA outputs. Needs formula source-lock first. | `docs/V6_PACKAGE_GENERATION_SCOPE.md`, `docs/V6_PACKAGE_PARITY_CONTRACT.md` |
| v6 package + summary (`v6_candidate_package_outputs`) | **Critical** | missing | `paid_archive_request_summary.txt`, rebuilt `…FINAL_v6_ZONES_QUOTES.zip` (reuse `v6_package._write_rebuilt_zip`). | `docs/V6_PACKAGE_GENERATION_SCOPE.md` |
| Request zones (`request_zone_outputs`) | **Critical** | missing | `request_zones_v6.csv/.geojson` — cluster candidates into zones. | `docs/V6_PACKAGE_GENERATION_SCOPE.md` |
| Imagery quotes (`quote_template_comparison_outputs`) | High | missing | `paid_imagery_quote_template_v6.csv`, `paid_imagery_quote_comparison_v6.csv`. | `docs/V6_PACKAGE_GENERATION_SCOPE.md` |
| Visual inspection map (`visual_inspection_map_html`) | High | missing | Static, offline `visual_inspection_map.html` (no CDN per safety constants); `FILESYSTEM_ONLY`. | `docs/PHASE_6_PRIVATE_MAP_ARTIFACT_PARITY_CONTRACT.md` |
| DEM curvature variants (`dem_curvature_variants`) | Med-high | partial | `curv_laplacian/plan/profile_640.tif` (app writes 1 of 3). Formulas already recovered. | `docs/DEM_CURVATURE_PARITY_RECONSTRUCTION.md`, `docs/DEM_PLAN_PROFILE_CURVATURE_FORMULA_RECOVERY.md`; `app/pipeline/parity/dem_curvature_reconstruction.py`, `dem_plan_profile_recovery.py` |
| Resampled/filtered stacks (`hypercube_resampled_filtered_missing`) | Med-high | missing | `FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.*`, `S1_FILTERED_LAYERS_STACK_640.npy`. Recovery done. | `docs/HYPERCUBE_RES_2P5M_PARITY_CONTRACT.md`, `docs/S1_FILTERED_LAYERS_STACK_PARITY_CONTRACT.md`; `hypercube_res25_recovery.py`, `s1_filtered_stack_recovery.py` |
| Hypercube notebook aliases (`hypercube_tensor_outputs`) | High | partial | Wire conditional `FINAL_TESLA_*` aliases (depend on report/secret sources). | `docs/RASTER_TENSOR_PARITY_ALIAS_CONTRACT.md` |
| QA naming parity (`qa_alignment_zero_pca_stack_outputs`) | Med-high | partial | Notebook-compatible QA filenames for alignment/zero-shift/PCA/stack audits. | `docs/PHASE_5_QA_INTERMEDIATE_PARITY_CONTRACT.md` |
| Focus-mask QA aliases (`focus_mask_outputs`) | Med-high | partial | `QA/FOCUS_MASK_17m_inside_640.tif/.json` aliases of existing `full_job/focus/*`. | `docs/PHASE_6_PRIVATE_MAP_ARTIFACT_PARITY_CONTRACT.md` |
| Private coord/map filename parity (`coordinate_map_kmz_geojson_outputs`) | High | partial | Extend notebook filename/folder parity for GeoJSON/KMZ. Stays `FILESYSTEM_ONLY` (public exposure is Group C). | `docs/PHASE_6_PRIVATE_MAP_ARTIFACT_PARITY_CONTRACT.md` |

---

## Group B — Blocked on a frozen notebook reference (and/or EE source)

Writers may exist and run; these cannot be **closed** until the operator supplies the frozen
reference bundle (to prove value parity) and, where noted, the EE source data.

| Item (id) | Priority | Status | Blocker | Contract / verifier |
|---|---|---|---|---|
| REPORT_640 rasters (`report_640_outputs`) | High | unknown_needs_verification | Writer exists; value unverified. Notebook-parity report raster, not core. | `docs/REPORT_640_PARITY_VERIFICATION_CONTRACT.md`; `report_640_verify.py` |
| AI_READY_640_Secret_* (`ai_ready_secret_outputs`) | High | unknown_needs_verification | 6-raster writer exists; value unverified. Notebook-parity semantic raster, not core. | `docs/SECRET_LAYERS_PARITY_VERIFICATION_CONTRACT.md`; `secret_layers_verify.py` |
| AI_BEH broader series (`ai_beh_broader_series`) | High | partial | Broader series pending + value unverified. | `docs/AI_BEH_*_PARITY_CONTRACT.md` (6), `docs/AI_READY_*_PARITY_CONTRACT.md` (3) |
| SAR core bands value parity (`sar_radar_core_outputs`) | High | unknown_needs_verification | Aliases exist; value unverified; needs S1 + reference. | `docs/SAR_PROCESSING_PARITY.md` |
| S2 indices value parity (`s2_optical_index_outputs`) | High | unknown_needs_verification | Core app; value unverified. `IRON_SWIR` correction is an accepted difference. | `docs/PARITY_EXCEPTIONS.md`, `docs/IRON_SWIR_PROVENANCE.md` |
| DEM/terrain alias value parity (`dem_terrain_outputs`) | Med-high | unknown_needs_verification | Aliases exist; value unverified. | `docs/RASTER_TENSOR_PARITY_ALIAS_CONTRACT.md` |
| S1 ASC/DESC filtered stacks (`sar_asc_desc_filtered_outputs`) | High | missing | No writer; needs separate ASC/DESC + reference. | `docs/SAR_ASC_DESC_SUPPORT_STACK_RECOVERY.md`; `sar_asc_desc_verify.py` |
| Panchromatic family (`panchromatic_optical_outputs`) | Medium | missing | No PAN writer; needs optical source + reference. | `docs/PAN_LAYERS_STACK_PARITY_CONTRACT.md`; `pan_components_verify.py` |
| QA grid/run manifest (`qa_grid_run_manifest_outputs`) | High | unknown_needs_verification | Writer runs; value unverified. | `docs/PHASE_5_QA_INTERMEDIATE_PARITY_CONTRACT.md` |
| QA SAR provenance (`qa_sar_provenance_outputs`) | High | partial | Folded into app names; notebook filename parity + value pending. | `docs/PHASE_5_QA_INTERMEDIATE_PARITY_CONTRACT.md` |
| Object extraction value parity (`object_extraction_outputs`) | Med-high | unknown_needs_verification | Core app; value-parity pending reference. | `docs/PHASE_9_END_TO_END_PARITY_HARNESS.md` |

---

## Group C — Blocked by policy/safety, or structurally not reproduced

| Item (id) | Priority | Status | Reason |
|---|---|---|---|
| Original classifier labels (`classifier_original_label_parity_outputs`) | Med-high | notebook_only_pending | **Policy.** Original labels live only in `docs/CLASS_MAPPING.md`; must not enter app source, tests, logs, filenames, API, or frontend. |
| Neutral classifier (`classifier_neutral_current_outputs`) | Med-high | partial | Present as neutral `Class_*`, probability-only, CLI/`FILESYSTEM_ONLY`. Original-label behavior intentionally withheld. | 
| Probability-only ML classifier (`future_probability_only_classifier_outputs`) | High (future) | notebook_only_pending | Design done (Phase 8); blocked on dataset source approval (Slice 13) + calibration. | 
| Deep-learning inference (`deep_learning_model_cells`) | Medium | requires_external_dependency | Needs approved weights/training data; Special Track H/I governance. `docs/ML_DATA_TRAINING_READINESS_PLAN.md`. |
| Broken constructor cell (`broken_model_constructor_cell`) | Low | broken_notebook_cell | Non-runnable notebook source; reference only, not ported. |
| Public exposure of coord/map/KMZ | — | (policy) | Build is private (Group A); **public** exposure is Special Track G, needs explicit approval. `docs/SPECIAL_TRACK_G_EXACT_COORDINATE_OVERLAY_ACCESS_CONTROL.md`. |
| Pre-RTC SAR intermediates (`pre_rtc_sar_intermediates`) | Med-high | partial | **Structural.** Post-RTC arrays match; earlier stages are `not_implemented_no_source_equivalent` (production SAR does not retain them). |

---

## Recommended next slices

Priority-ordered, each a separately-approved goal:

1. **V6-G0 + V6-G1** — freeze a notebook v6 reference package and source-lock the ranking
   formulas. Unblocks the entire Critical-tier v6 family. See `docs/V6_PACKAGE_GENERATION_SCOPE.md`.
2. **DEM curvature variants** — formulas already recovered; low-risk Group-A win.
3. **Visual inspection map + private coord/map filename parity** — Group A, `FILESYSTEM_ONLY`.

Reference-blocked Group B work should be sequenced behind the D1 frozen-reference collection,
since none of it can reach proven value parity without it.
