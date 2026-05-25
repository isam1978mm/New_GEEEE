# Project Status Handoff

## Closed

- Notebook-grid production-core parity is accepted for the current reference workflow.
- The final F11 baseline has no FAIL rows.
- GRID provenance is decided as Option B: production GRID remains app-authoritative, while notebook-exact GRID is validation/replay-only.
- The SAR parity test harness was fixed so the fake Earth Engine image path matches the production SAR call flow.
- `PARITY_SCOPE.md` and `OUTPUT_PARITY_CONTRACT.md` were updated to reflect the accepted parity scope.
- `curvature.tif`, `TRI.tif`, and `TWI.tif` are app-only DEM derivative outputs, not required H1 notebook-matched outputs in the current reference set.
- The reference bundle is external. The committed repo contract is the manifest/checksum record, not the binary bundle.
- `MANIFEST.json` has real checksums, redacted paths, and safe semantic categories.
- Configured local checksum validation against the operator-supplied reference bundle passes.
- `SKIP_MISSING_NOTEBOOK` means the current frozen reference set does not expose a matching notebook artifact for that row; it is not a numeric parity failure.

## Open

- Fresh-ROI notebook parity is not claimed.
- Production GRID versioning/replay protection is not implemented.
- Notebook reference binaries are still external and must be copied out-of-band for any new machine or future VPS.
- The full experimental notebook tail remains outside the accepted production-core parity scope.
- Optional future work includes improving safe category coverage, adding a VPS deployment runbook, and implementing GRID convention versioning.

## Operating Notes

- Do not treat notebook-exact GRID as the production default.
- Do not commit reference binaries.
- Do not expose local bundle configuration through public API responses.
- Do not change SAR math, GRID behavior, tolerances, notebook code, or the production pipeline without a new explicit goal.
