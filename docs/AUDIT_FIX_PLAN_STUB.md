# Audit Fix Execution Plan

## Scope

This is the execution plan and closeout checklist for the private/local app audit.

Priorities:

1. output correctness;
2. no misleading success;
3. notebook/app parity honesty;
4. provenance and data-quality checks;
5. useful local operator exports.

The Paid Imagery Export Package is in scope. It is an offline export package for manual operator use. It is not a live external ordering, payment, or provider integration.

Internal `V6` / `v6_*` names are legacy implementation names and may remain temporarily for route, package, and test compatibility.

## Current Checklist

### Item 0 — Scope And Docs Lock

- [x] 0.1 Keep the paid images request/export package in scope.
- [x] 0.2 Explain that `V6` is legacy/internal naming for the export package.
- [x] 0.3 Update remaining V6 docs to remove deprecated/parked/out-of-scope wording.
- [x] 0.4 Record parity corrections in `docs/PARITY_EXCEPTIONS.md`.
- [x] 0.5 Verify docs diff.

### Item 1 — P0 Correctness Fixes

- [x] 1.1 Thermal inertia: align local and EE-style source/unit basis.
- [x] 1.2 Thermal inertia: record source and unit in metadata.
- [x] 1.3 Thermal inertia: add regression tests.
- [x] 1.4 Fusion target mask: fix raw-DN versus reflectance threshold handling.
- [x] 1.5 Fusion target mask: add expected cloud filter.
- [x] 1.6 Fusion target mask: align deterministic twin and production path.
- [x] 1.7 Fusion target mask: add regression tests.
- [x] 1.8 Empty/all-nodata: add source collection size gates or equivalent valid-data blockers.
- [x] 1.9 Empty/all-nodata: raise `StageError` when required source data is missing.
- [x] 1.10 Empty/all-nodata: add valid-fraction checks after fetch.
- [x] 1.11 Empty/all-nodata: record valid-fraction information.

### Item 2 — No Misleading Success

- [x] 2.1 Full-job report: remove unconditional coverage.
- [x] 2.2 Full-job report: scan actual run directory.
- [x] 2.3 Full-job report: report present and missing files per output family.
- [x] 2.4 Full-job report: add missing-output tests.
- [x] 2.5 Export package: `package_ready=true` only after OK validation.
- [x] 2.6 Export package: pair ZIP and validation report by one generation token.
- [x] 2.7 Export package: reject mismatched ZIP/report pairs.
- [x] 2.8 Export package: disable retrieve action when validation is not OK.
- [x] 2.9 Export package: keep UI/review responses metadata-only.
- [x] 2.10 Manifest/history: distinguish missing files from corrupt/unreadable files.
- [x] 2.11 Manifest/history: surface read errors instead of silently returning clean empty state.

### Item 3 — Run Reliability

- [x] 3.1 Include orphan `QUEUED` runs in stale startup cleanup.
- [x] 3.2 Add tests for queued and running stale runs.
- [x] 3.3 Add a shared atomic JSON write helper.
- [x] 3.4 Replace truncate-in-place writes.
- [x] 3.5 Add atomic-write tests where practical.

### Item 4 — Raster And Data Quality

- [x] 4.1 Replace plain TIFF writes with georeferenced raster writes where required.
- [x] 4.2 Keep sidecars.
- [x] 4.3 Verify raster readers still work.
- [x] 4.4 Add CRS/transform/nodata checks.
- [x] 4.5 Prevent invalid pixels from silently becoming legal zero values without a validity signal.
- [x] 4.6 Gate or warn on low valid fraction.

### Item 5 — Export Package Provenance

- [x] 5.1 Record package provenance.
- [x] 5.2 Record score basis.
- [x] 5.3 Record geometry basis.
- [x] 5.4 Label fallback score or fallback geometry when used.
- [x] 5.5 Label placeholder map content when used.
- [x] 5.6 Keep package artifacts local/private.
- [x] 5.7 Keep UI metadata-only.
- [x] 5.8 Do not claim frozen external notebook parity unless a verified source is supplied.

### Item 6 — Naming Cleanup

- [x] 6.1 Use user-facing name `Paid Imagery Export Package` or `Imagery Export Package`.
- [x] 6.2 Keep internal `v6_*` names temporarily if renaming is risky.
- [x] 6.3 Add comments/docs that V6 is legacy/internal naming.
- [x] 6.4 Do not break existing routes or tests.

### Item 7 — Status Docs Cleanup

- [x] 7.1 Remove contradictions between status docs and open-items docs.
- [x] 7.2 Document known placeholders and tolerated gaps.
- [x] 7.3 Document what remains not implemented.

## Verification Record

Focused local verification reported during this closeout:

```text
Item 3 stale cleanup: passed
Item 3 atomic JSON / run-history / package tests: passed
Item 4 georeferenced raster tests: passed
Item 4 remaining raster writer tests: 11 passed
Item 5 V6 provenance/package tests: 21 passed
```

Final full verification command remains:

```powershell
python -m pytest tests/unit/ tests/integration/ tests/parity/ tests/notebook_parity/ -q
cd frontend-v2
npm run build
```

Done conditions:

- no all-nodata success is reported as done;
- no export package is ready unless validation is OK;
- ZIP/report generations match;
- full-job coverage is based on actual files;
- corrupt manifests/history are visible;
- orphan queued runs do not block forever;
- required rasters are georeferenced;
- Paid Imagery Export Package remains in scope and correctly labeled;
- old/external V6 notebook parity is not claimed unless a verified source is supplied.
