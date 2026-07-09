# V6-REAL-PACKAGE-1 Paid Imagery Export Package Feed

## Current Status

`V6` is legacy/internal naming for the app's Paid Imagery Export Package.

This feature remains in scope. It generates an offline export package for manual operator use outside the app. It is not a live ordering service or external provider integration.

V6-REAL-PACKAGE-1 feeds app-generated scored candidates and generated request zones into the package writer path.

Implemented now:

- package input model;
- package payload builder from scored candidates and request zones;
- timestamped top candidate CSV payload;
- timestamped top candidate spatial payload;
- enhanced candidate CSV payload;
- diagnostics CSV payload;
- stable priority CSV payload;
- request-zone CSV payload;
- request-zone spatial payload;
- quote template CSV payload;
- quote comparison CSV payload;
- archive request summary payload;
- private map placeholder payload;
- inventory JSON;
- ZIP package;
- validation report;
- safe CLI summary;
- unit tests.

Later phases added the private backend generate/review/retrieve flow and frontend metadata panel. This document remains the feed-layer record.

## Added Files

```text
app/services/v6_real_package.py
tests/unit/test_v6_real_package.py
```

## What This Step Does

The package feed accepts:

- app-generated scored candidates;
- app-generated request zones;
- run ID;
- timestamp.

It writes the full package payload set, inventory JSON, ZIP package, and validation report using app-generated rows.

The old external V6 notebook/package source is not treated as verified parity unless that source is supplied and frozen. Generated rows must carry honest provenance in the fixing phase.

## Safety Rules

- Generated package files remain filesystem artifacts only.
- Do not commit generated package output folders.
- Safe summaries do not include candidate rows or spatial payload bodies.
- CLI summary remains metadata-only.
- Private spatial payloads are package data, not public status data.
- UI/API exposure must remain metadata-only.

## Current Follow-Up Work

The audit fixing plan tracks the remaining work:

```text
docs/AUDIT_FIX_PLAN_STUB.md
```

Relevant checklist items:

- export package readiness must depend on OK validation;
- ZIP and validation report must be paired by generation;
- package provenance must record score basis and geometry basis;
- placeholder map content must be labeled if used;
- user-facing wording should say Paid Imagery Export Package or Imagery Export Package.

## Checklist

- [x] Add package input model.
- [x] Feed scored candidate rows into package payloads.
- [x] Feed request-zone rows into package payloads.
- [x] Feed request-zone spatial payload into package payloads.
- [x] Generate inventory JSON.
- [x] Generate ZIP package.
- [x] Generate validation report.
- [x] Keep CLI summary metadata-only.
- [x] Add unit tests.
- [ ] Add provenance fields for package source, score basis, and geometry basis.
- [ ] Gate package readiness on OK validation.
- [ ] Pair ZIP and validation report by generation.
- [ ] Label placeholder map content when used.
