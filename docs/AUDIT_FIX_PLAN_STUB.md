# Audit Fix Execution Plan

## Scope

This is the execution plan for the private/local app audit.

Priorities:

1. output correctness;
2. no misleading success;
3. notebook/app parity honesty;
4. provenance and data-quality checks;
5. useful local operator exports.

The paid images request/export package is in scope. It is an offline export package for manual operator use. It is not a live external ordering integration.

## Phase 0 — Scope And Docs Lock

Files:

```text
docs/V6_PACKAGE_GENERATION_SCOPE.md
docs/V6_REAL_PACKAGE_1.md
docs/V6_FINAL_WIRING_1.md
docs/V6_APP_FLOW_1.md
docs/V6_APP_UI_1.md
docs/PARITY_EXCEPTIONS.md
```

Tasks:

- keep the paid images request/export package in scope;
- explain that `V6` is legacy/internal naming for the export package;
- remove wording that says the feature is deprecated, parked, removed, or out of current work;
- record parity corrections in `docs/PARITY_EXCEPTIONS.md`.

## Phase 1 — P0 Correctness Fixes

### Thermal inertia

Files:

```text
app/pipeline/stages/secret_layers.py
app/pipeline/stages/thermal.py
```

Tasks:

- make local and EE-style thermal inertia use the same source/unit basis;
- record source and unit in metadata;
- add regression tests.

### Fusion target mask

Files:

```text
app/pipeline/stages/s2_indices.py
```

Tasks:

- fix raw-DN versus reflectance threshold handling;
- add the expected cloud filter;
- align deterministic twin and production path;
- add regression tests.

### Empty source/all-nodata blocking

Files:

```text
app/pipeline/stages/s2_indices.py
app/pipeline/stages/thermal.py
app/pipeline/stages/dem.py
```

Tasks:

- add source collection size gates;
- raise `StageError` when required source data is missing;
- add valid-fraction checks after fetch;
- record valid-fraction information.

## Phase 2 — No Misleading Success

### Full-job output report

File:

```text
app/services/full_job_local_output_report.py
```

Tasks:

- remove unconditional coverage;
- scan the actual run directory;
- report present and missing files per output family;
- add missing-output tests.

### Paid images request/export package readiness

Files:

```text
app/services/v6_app_flow.py
app/services/v6_real_package.py
app/services/v6_package_validator.py
frontend-v2/src/app/components/V6PrivatePackagePanel.tsx
```

Tasks:

- `package_ready=true` only after OK validation;
- pair ZIP and validation report by one generation token;
- reject mismatched ZIP/report pairs;
- disable retrieve action when validation is not OK;
- keep UI/review responses metadata-only.

### Manifest/history errors

Files:

```text
app/services/operator_outputs.py
app/services/run_history.py
app/api/runs.py
```

Tasks:

- distinguish missing files from corrupt/unreadable files;
- surface read errors instead of silently returning clean empty state.

## Phase 3 — Run Reliability

### Stale queued run cleanup

File:

```text
app/services/run_state.py
```

Tasks:

- include orphan `QUEUED` runs in stale startup cleanup;
- add tests for queued and running stale runs.

### Atomic JSON writes

Files:

```text
app/services/storage.py
app/services/run_history.py
app/services/v6_real_package.py
app/services/roi_contract.py
```

Tasks:

- add a shared atomic JSON write helper;
- replace truncate-in-place writes;
- add tests where practical.

## Phase 4 — Raster And Data Quality

Files:

```text
app/pipeline/stages/thermal.py
app/pipeline/stages/s2_indices.py
app/pipeline/stages/pca_anomaly.py
app/pipeline/stages/feature_stacks.py
```

Tasks:

- replace plain TIFF writes with georeferenced raster writes where required;
- keep sidecars;
- verify raster readers still work;
- add CRS/transform/nodata checks;
- prevent invalid pixels from silently becoming legal zero values without a validity signal;
- gate or warn on low valid fraction.

## Phase 5 — Export Package Provenance

Files:

```text
app/services/v6_local_package_input.py
app/services/v6_real_package.py
app/services/v6_package_validator.py
frontend-v2/src/app/components/V6PrivatePackagePanel.tsx
```

Tasks:

- record package provenance;
- record score basis;
- record geometry basis;
- label fallback score or fallback geometry when used;
- label placeholder map content when used;
- keep package artifacts local/private;
- keep UI metadata-only;
- do not claim frozen external notebook parity unless a verified source is supplied.

## Phase 6 — Naming Cleanup

Tasks:

- user-facing name should be `Paid Imagery Export Package` or `Imagery Export Package`;
- keep internal `v6_*` names temporarily if renaming is risky;
- add comments/docstrings that V6 is legacy/internal naming;
- do not break existing routes or tests.

## Phase 7 — Status Docs Cleanup

Files:

```text
docs/CURRENT_STATUS.md
docs/PARITY_OPEN_ITEMS_PRIORITIZED_CHECKLIST.md
docs/PARITY_EXCEPTIONS.md
```

Tasks:

- remove contradictions between status docs and open-items docs;
- document known placeholders and tolerated gaps;
- document what remains not implemented.

## Verification

Run:

```powershell
python -m pytest tests/unit/ tests/integration/ tests/parity/ tests/notebook_parity/ -q
cd frontend-v2
npm run build
```

Done when:

- no all-nodata success is reported as done;
- no export package is ready unless validation is OK;
- ZIP/report generations match;
- full-job coverage is based on actual files;
- corrupt manifests/history are visible;
- orphan queued runs do not block forever;
- required rasters are georeferenced;
- paid images request/export package remains in scope and correctly labeled.
