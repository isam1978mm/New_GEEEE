# V6-REAL-ZONES-1 Request-Zone Generation

## Current Status

V6-REAL-ZONES-1 adds request-zone generation from scored candidates and grid cells.

Implemented now:

- request-zone config;
- request-zone model;
- ranked candidate to request-zone generation;
- quote ID assignment;
- CSV row export;
- spatial JSON export;
- safe summaries;
- unit tests.

This still does not complete the full real V6 package path. The next missing step is feeding scored candidates and generated zones into the package writer.

## Added Files

```text
app/services/v6_real_zones.py
tests/unit/test_v6_real_zones.py
```

## What This Step Does

The zone generator accepts scored candidates and matching grid cells.

It sorts candidates by final V6 priority rank, selects up to the configured maximum, and creates request-zone records with stable IDs.

It can export:

- request-zone CSV rows;
- request-zone spatial JSON features;
- safe summary metadata.

## Safety Rules

- Safe summaries redact bounds values.
- CSV rows do not include bounds values.
- Spatial JSON output is package data, not public status data.
- Package writing stays separate.
- UI/API exposure is not added in this step.

## Still Not Done

- feed scored candidates and zones into package writer;
- create package payloads from real app rows;
- private app generate/review/download flow.

## Next Step

```text
V6-REAL-PACKAGE-1: feed scored candidates and generated request zones into the package writer.
```

## Checklist

- [x] Add request-zone config.
- [x] Add request-zone model.
- [x] Generate request-zone records from scored candidates.
- [x] Preserve final priority rank.
- [x] Preserve review priority score.
- [x] Preserve warning count.
- [x] Add quote IDs.
- [x] Export request-zone CSV rows.
- [x] Export request-zone spatial JSON features.
- [x] Add safe request-zone summaries.
- [x] Add unit tests.
- [ ] Feed scored candidates into package writer.
- [ ] Feed request zones into package writer.
- [ ] Add private app generate/review/download flow.
