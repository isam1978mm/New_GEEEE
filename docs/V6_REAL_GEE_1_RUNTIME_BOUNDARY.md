# V6-REAL-GEE-1 Runtime Boundary And AOI/Grid

## Current Status

V6-REAL-GEE-1 has started the real generation path by adding an app-side runtime boundary and deterministic AOI/grid helpers.

This is not the full real V6 geospatial generator yet.

Implemented now:

- lazy external geospatial runtime adapter;
- runtime configuration object;
- validated AOI bounding-box model;
- deterministic row/column grid builder;
- safe AOI/grid summaries that redact bounds values;
- unit tests using an injected fake runtime module.

Not implemented yet:

- Sentinel-2 feature extraction;
- terrain feature extraction;
- water mask feature extraction;
- vegetation/bare-soil index calculation;
- road/building warning layers;
- real scoring;
- real candidate ranking;
- real request-zone geometry generation;
- private app UI/API generate/download flow.

## Added Files

```text
app/services/v6_real_gee_runtime.py
tests/unit/test_v6_real_gee_runtime.py
```

## Runtime Boundary

The runtime adapter does not import the external geospatial library at module import time.

The external service is loaded only when the explicit runtime method is called.

Unit tests inject a fake module so tests do not call the external service.

## AOI And Grid

The app now has validated internal AOI bounds and deterministic grid-cell construction.

The grid builder creates row-major cell IDs like:

```text
V6_CELL_R001_C001
V6_CELL_R001_C002
```

Safe summaries redact AOI/grid bounds values and expose only safe metadata such as cell count and cell IDs.

## Safety Rules

- Unit tests must not call the external geospatial service.
- Normal summaries must not print exact bounds values.
- No notebook globals are used.
- No Google Drive runtime paths are used.
- No real V6 artifact files are used.
- No frontend/API exposure is added in this step.

## Next Step

```text
V6-REAL-GEE-2: port the real geospatial feature layers: Sentinel-2, terrain, water masks, vegetation/bare-soil indices, and road/building warning layers.
```

## Checklist

- [x] Add app-side runtime adapter.
- [x] Keep external service calls out of unit tests.
- [x] Add runtime configuration object.
- [x] Add AOI input validation.
- [x] Add deterministic grid construction.
- [x] Return internal grid-cell records for scoring.
- [x] Redact AOI/grid bounds values in safe summaries.
- [x] Add unit tests for AOI/grid behavior without external service calls.
- [ ] Port real geospatial feature extraction.
- [ ] Port real scoring.
- [ ] Generate real request zones.
- [ ] Feed real outputs into package writer.
- [ ] Add private app generate/review/download flow.
