# V6-REAL-PACKAGE-1 Real Output Package Feed

## Current Status

V6-REAL-PACKAGE-1 feeds app-generated scored candidates and generated request zones into the V6 package writer path.

Implemented now:

- real package input model;
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

This completes the package-feed bridge, but it does not add the private app UI/API generate/review/download flow yet.

## Added Files

```text
app/services/v6_real_package.py
tests/unit/test_v6_real_package.py
```

## What This Step Does

The real package feed accepts:

- app-generated scored candidates;
- app-generated request zones;
- run ID;
- timestamp.

It writes the full V6 package payload set, inventory JSON, ZIP package, and validation report using app-generated rows instead of synthetic fixture rows.

## Safety Rules

- Generated real package files remain filesystem artifacts only.
- Do not commit generated package output folders.
- Safe summaries do not include candidate rows or spatial payload bodies.
- CLI summary remains metadata-only.
- Private spatial payloads are package data, not public status data.
- UI/API exposure is not added in this step.

## Still Not Done

- private backend generate job;
- private status endpoint;
- private package metadata/review endpoint;
- private package download endpoint;
- UI generate/review/download flow;
- redaction tests for API DTOs.

## Next Step

```text
V6-APP-FLOW-1: add private backend generate/review/download flow for the real package path.
```

## Checklist

- [x] Add real package input model.
- [x] Feed scored candidate rows into package payloads.
- [x] Feed request-zone rows into package payloads.
- [x] Feed request-zone spatial payload into package payloads.
- [x] Generate inventory JSON.
- [x] Generate ZIP package.
- [x] Generate validation report.
- [x] Keep CLI summary metadata-only.
- [x] Add unit tests.
- [ ] Add private backend generation job.
- [ ] Add private status endpoint.
- [ ] Add private package metadata/review endpoint.
- [ ] Add private package download endpoint.
- [ ] Add frontend generate/review/download UI.
