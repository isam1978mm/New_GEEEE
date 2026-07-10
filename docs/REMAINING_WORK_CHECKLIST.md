# Remaining Work Checklist

This document is the short operational view for what remains after the audit-fix sequence.

For the audit execution checklist, see:

```text
docs/AUDIT_FIX_PLAN_STUB.md
```

## 0. Current baseline

```text
[x] Git expected clean after pull/test
[x] Full focused backend tests passing for recent audit patches
[x] Paid Imagery Export Package app flow implemented
[x] Package readiness is validation-gated
[x] ZIP/report generations are paired by token
[x] Package provenance is recorded
[x] Browser package panel is metadata-only
[x] Required raster outputs are georeferenced with CRS/transform/nodata checks
[x] Atomic JSON writes implemented for target services
```

## 1. Completed audit-fix work

```text
[x] Item 0 — Scope And Docs Lock
[x] Item 1 — P0 Correctness Fixes
[x] Item 2 — No Misleading Success
[x] Item 3 — Run Reliability
[x] Item 4 — Raster And Data Quality
[x] Item 5 — Export Package Provenance
[x] Item 6 — Naming Cleanup
[x] Item 7 — Status Docs Cleanup
```

## 2. Paid Imagery Export Package / old V6 status

User-facing name:

```text
Paid Imagery Export Package
```

Status:

```text
[x] App UI/backend flow implemented
[x] Generate / review metadata / retrieve ZIP exists
[x] Metadata-only browser behavior
[x] Local/private filesystem-only package artifacts
[x] Package provenance, score basis, geometry basis, fallback labels, and placeholder-map labels recorded
[x] No frozen external notebook parity claim unless a verified external source is supplied
```

Internal `V6` / `v6_*` names remain legacy implementation names for compatibility. Do not rename routes/modules/files in a broad sweep unless there is a dedicated migration plan.

The separate old/external V6 notebook-source parity track remains unresolved, not complete. It can restart only after the operator supplies the separate originating V6 notebook/export source or a verified frozen package.

## 3. Remaining parity/source-recovery candidates

No next parity gate is selected yet. Choose one explicitly.

```text
[ ] SAR/S1 support, intermediate, and QA/provenance outputs outside S1-1 and stack
    Do not broaden S1-1 or S1 filtered stack passes into all SAR/S1 parity.

[ ] Standalone AI_READY Fraction/MH/AN files
    Only if the operator supplies real notebook/source evidence later.
```

## 4. H5 / prediction serving boundaries still blocked

H5 is complete at aggregate level. These remain blocked:

```text
[ ] row-level prediction UI
[ ] raw prediction CSV download
[ ] sample_id exposure
[ ] private file paths in API/frontend responses
[ ] feature values in API/frontend responses
[ ] model artifact serving
[ ] feature matrix serving
[ ] map overlays
[ ] public serving
```

Allowed H5 level remains aggregate/redacted only.

## 5. Deployment/auth/public exposure — later only

```text
[ ] Real auth provider integration
[ ] Production deployment hardening
[ ] Public-user feature design
[ ] External provider ordering/payment integration
```

These are not part of the current local/private audit closeout.
