# V6-REAL-REDUCE-1 Feature Reduction And Scorer Bridge

## Current Status

V6-REAL-REDUCE-1 connects reduced per-grid-cell feature records to the V6 scorer.

Implemented now:

- feature reduction config;
- reduced feature row model;
- reduction boundary class;
- converter from reduced runtime records to typed rows;
- safe reduction summaries;
- bridge from reduced feature rows to `score_v6_candidates`;
- unit tests using fake reduced records only.

This still does not complete the full real V6 output path. The next missing piece is request-zone generation from scored candidates.

## Added Files

```text
app/services/v6_real_reduce.py
tests/unit/test_v6_real_reduce.py
```

## What This Step Does

The reducer boundary accepts a feature stack and grid cells, reduces features over each grid cell, converts returned properties into typed `V6ReducedFeatureRow` records, and sends those rows into the V6 scoring service.

The unit tests do not call the external geospatial service. They use fake reduced records that mimic returned properties.

## Safety Rules

- Unit tests are offline.
- Geometry bodies are ignored when converting records.
- Safe summaries include counts and IDs only.
- Feature values are not included in safe summaries.
- Package writing stays separate.
- Request-zone creation stays separate.
- UI/API exposure is not added in this step.

## Still Not Done

- request-zone generation;
- real package feed;
- private app generate/review/download flow.

## Next Step

```text
V6-REAL-ZONES-1: generate request-zone records from scored candidates.
```

## Checklist

- [x] Add feature reduction config.
- [x] Add reduced feature row model.
- [x] Add runtime reduction boundary class.
- [x] Convert reduced records into typed rows.
- [x] Validate required feature bands during conversion.
- [x] Preserve optional scoring metadata.
- [x] Add safe reduction summaries.
- [x] Connect reduced rows to V6 scorer.
- [x] Add unit tests with fake reduced records.
- [ ] Generate request-zone records.
- [ ] Generate request-zone GeoJSON.
- [ ] Feed scored candidates and zones into package writer.
- [ ] Add private app generate/review/download flow.
