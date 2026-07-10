# Current Status

This is the quick reconciliation point for the current private/local app state.

## Current baseline

```text
expected git status: clean after pull/test
private artifacts: outside Git
browser policy: metadata-only for private/operator package surfaces
```

## Audit fix execution status

The audit closeout checklist is maintained in:

```text
docs/AUDIT_FIX_PLAN_STUB.md
```

Current audit item status:

```text
Item 0 — Scope And Docs Lock: done
Item 1 — P0 Correctness Fixes: done
Item 2 — No Misleading Success: done
Item 3 — Run Reliability: done
Item 4 — Raster And Data Quality: done after georeferenced-raster patches/tests
Item 5 — Export Package Provenance: done after provenance backend tests
Item 6 — Naming Cleanup: done for user-facing UI/API copy; internal v6_* names kept intentionally
Item 7 — Status Docs Cleanup: in progress in this document set
```

## Paid Imagery Export Package

The user-facing feature name is now:

```text
Paid Imagery Export Package
```

Internal module, route, and file names may still use `V6` or `v6_*`. That is legacy/internal naming only and is kept temporarily to avoid breaking routes, saved files, tests, and package contracts.

Implemented behavior:

```text
Generate export package
Review package metadata
Retrieve package ZIP
Metadata-only browser panel
Operator token forwarding
Backend denial/unavailable handling
ZIP/report generation-token pairing
Validation-gated package readiness
Package provenance recorded in private inventory/validation metadata
Placeholder map labeled as placeholder/no imagery
No frozen external notebook parity claim unless a verified external source is supplied
```

Boundary:

```text
No package rows displayed in browser
No spatial payload bodies displayed in browser
No coordinates displayed in browser
Coordinate-bearing package outputs remain private/filesystem-only
```

## Parity track status

The in-scope parity notebook remains:

```text
notebooks/new.ipynb
```

The old/external V6 notebook/source-lock track is not closed as notebook parity. The export-package app feature is active, but frozen external V6 notebook parity remains unresolved until a verified external source is supplied.

Closed or explicitly statused parity work remains documented in the dedicated verifier/result docs, including REPORT_640, AIREADY-S1, HYPER-1A, HYPER-1B, INT-1, S1-1, S1 filtered stack, PAN/optical, AI_READY support stack, and D1D object tables.

## Still blocked / not claimed

```text
No claim that app/browser exposes private rows, raw arrays, coordinates, KMZ contents, filesystem paths, or private geometry.
No claim that the Paid Imagery Export Package is a live ordering/payment/provider integration.
No claim that external V6 notebook parity is frozen or verified.
No claim that source-recovery-only families are notebook-parity complete.
```
