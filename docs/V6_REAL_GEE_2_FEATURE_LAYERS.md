# V6-REAL-GEE-2 Feature-Layer Boundary

## Current Status

V6-REAL-GEE-2 has started the feature-layer extraction path.

Implemented now:

- feature-layer config;
- feature-stack plan with source IDs and required output bands;
- app-side feature stack builder method;
- required feature-row schema;
- feature-row validation helper;
- unit tests for config, source plan, band schema, and row validation.

This is still not the complete real V6 output path. The app now has the service boundary and formulas, but the full pipeline still needs reduction to grid rows, scoring, ranking, request-zone creation, package feed, and private app workflow.

## Added Files

```text
app/services/v6_real_gee_features.py
tests/unit/test_v6_real_gee_features.py
```

## Feature Families Covered

The feature-stack boundary covers:

- optical image collection date/cloud filtering;
- NDVI;
- BSI;
- MNDWI;
- low-vegetation proxy;
- bare-soil proxy;
- visibility score;
- local spectral contrast;
- terrain slope;
- TPI;
- gentle-slope terrain score;
- surface-water mask;
- water-edge warning;
- land-cover class;
- built-up fraction;
- cropland fraction;
- built probability;
- strong built warning;
- nearby building warning;
- road-like edge warning;
- modern-corridor warning.

## Safety Rules

- Unit tests do not call the external geospatial service.
- Feature extraction stays separate from package writing.
- Feature-row validation returns issue codes only.
- No candidate rows are printed.
- No geometry bodies are printed.
- No UI/API exposure is added in this step.

## Next Step

```text
V6-REAL-SCORING-1: port scoring, penalties, quality-adjusted score, and candidate ranking over reduced feature rows.
```

## Checklist

- [x] Add feature-layer config.
- [x] Add feature-stack plan.
- [x] Add required feature-band schema.
- [x] Add app-side feature stack builder method.
- [x] Add feature-row validator.
- [x] Add unit tests for config, source plan, schema, and validation.
- [ ] Reduce feature stack to grid-cell rows.
- [ ] Port scoring weights.
- [ ] Port false-positive warning/penalty logic.
- [ ] Port quality-adjusted score.
- [ ] Port final candidate ranking.
- [ ] Generate real request zones.
- [ ] Feed real outputs into package writer.
- [ ] Add private app generate/review/download flow.
