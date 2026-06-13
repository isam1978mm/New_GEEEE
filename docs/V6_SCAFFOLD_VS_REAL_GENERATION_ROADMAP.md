# V6 Scaffold Versus Real Generation Roadmap

## Correction

The current `v6_generator_*` code is a scaffold and package-writer path.

It is not the real V6 Earth Engine/scoring generator.

The scaffold proves that the app can assemble the expected V6 package file roles, inventory JSON, ZIP, and validation report from synthetic or safe app-input fixture rows. It does not calculate real candidates from satellite or geospatial data.

## Current Scaffold Status

The current app-side scaffold can generate the following package roles:

- timestamped top candidate CSV;
- timestamped top candidate GeoJSON;
- enhanced top candidate CSV;
- enhanced top candidate GeoJSON;
- stable candidate priority CSV;
- quality diagnostics CSV;
- request zones CSV;
- request zones GeoJSON;
- quote template CSV;
- quote comparison CSV;
- archive request summary TXT;
- visual inspection map HTML;
- inventory JSON;
- ZIP package;
- validation report.

The current scaffold uses:

```text
synthetic fixture data
or
safe app-input JSON fixture data
```

The current scaffold does not use:

```text
Earth Engine
Sentinel-2 imagery
terrain datasets
water masks
vegetation or bare-soil calculations
road/building warning layers
real grid scoring
real request-zone geometry
real V6 notebook artifacts
real coordinates
provider ordering
frontend/API exposure
```

## Same Output Roles Versus Same Real Outputs

There are two separate meanings of "same outputs."

### Same Output Roles

This means the app creates files with the expected V6 package roles and structure.

Current scaffold status:

```text
same output roles: yes
```

### Same Real Outputs

This means the app computes the real V6 candidate tables, diagnostics, request zones, and map from real AOI/geospatial inputs.

Current scaffold status:

```text
same real outputs: no
```

The app will only produce the same real outputs after the real Earth Engine/app pipeline generation path is implemented.

## Coordinates And GeoJSON Clarification

The current scaffold does not write real coordinates.

The current scaffold also does not write fake coordinates.

It writes empty GeoJSON `FeatureCollection` shells only to prove file structure.

Current status:

```text
real coordinates: no
fake coordinates: no
empty safe GeoJSON shell: yes
```

Target real status:

```text
real app-generated candidate/request-zone geometry: yes
```

That target requires the real Earth Engine/app scoring path first.

## Correct Roadmap

The corrected roadmap is:

```text
V6-SCAFFOLD-1: package writer, inventory, ZIP, validation scaffold
V6-REAL-GEE-1: port notebook Earth Engine AOI/grid/data-source logic into app runtime boundary
V6-REAL-GEE-2: port Sentinel-2, terrain, water, vegetation/bare-soil, road/building warning layers
V6-REAL-SCORING-1: port grid scoring and candidate ranking logic
V6-REAL-ZONES-1: generate real request zones from ranked candidates
V6-REAL-PACKAGE-1: feed real app-generated candidates/zones/diagnostics into package writer
V6-APP-FLOW-1: add private backend job and UI/API flow for generate/review/download
V6-PAID-TRACKING-1: add manual quote/status tracking after real generation works
```

## What The Current Scaffold Is Good For

The scaffold is still useful, but only as foundation work.

It provides:

- a package writer;
- inventory/hash logic;
- ZIP creation;
- role/name/category checks;
- safe CLI output rules;
- tests proving package shape;
- a target contract for real outputs to plug into later.

It does not replace the real generator.

## What Must Be Built Next

The next real task is not more scaffold work.

The next real task is:

```text
V6-REAL-GEE-1: create the app-side Earth Engine runtime boundary and port AOI/grid/data-source logic from the notebook into app services.
```

After that, continue with:

```text
V6-REAL-GEE-2: port the geospatial feature layers.
V6-REAL-SCORING-1: port scoring and ranking.
V6-REAL-ZONES-1: port request-zone generation.
V6-REAL-PACKAGE-1: feed real outputs into the package writer.
V6-APP-FLOW-1: expose private app workflow for generate/review/download.
```

## Real Generation Checklist

### V6-REAL-GEE-1: Earth Engine Runtime Boundary And AOI/Grid

- [ ] Add app-side Earth Engine runtime adapter.
- [ ] Keep Earth Engine out of unit tests.
- [ ] Add explicit runtime configuration for credentials/auth behavior.
- [ ] Port AOI input validation.
- [ ] Port deterministic grid construction.
- [ ] Return internal grid-cell records usable by scoring.
- [ ] Avoid logging exact coordinates in normal logs.
- [ ] Add synthetic tests for AOI/grid behavior without Earth Engine.

Acceptance:

- [ ] App has a real runtime boundary for Earth Engine.
- [ ] Unit tests do not call Earth Engine.
- [ ] AOI/grid logic is app-side, not notebook-side.

### V6-REAL-GEE-2: Geospatial Feature Layers

- [ ] Port Sentinel-2 source loading and date filtering.
- [ ] Port cloud/visibility support features.
- [ ] Port terrain features.
- [ ] Port water mask features.
- [ ] Port vegetation/bare-soil index features.
- [ ] Port road/building warning layers.
- [ ] Output per-grid-cell feature summaries.
- [ ] Add synthetic tests for feature summary schema.

Acceptance:

- [ ] App produces feature rows needed by the V6 scorer.
- [ ] Feature extraction is separated from package writing.
- [ ] No real feature rows or coordinates are printed in logs.

### V6-REAL-SCORING-1: Candidate Scoring And Ranking

- [ ] Port V6 scoring weights.
- [ ] Port false-positive penalty logic.
- [ ] Port quality-adjusted scoring.
- [ ] Port final priority ranking.
- [ ] Add deterministic tie handling.
- [ ] Add tests for missing/invalid feature values.

Acceptance:

- [ ] App produces real candidate table rows from app-generated feature rows.
- [ ] Ranking is deterministic.
- [ ] Scoring is testable without Earth Engine.

### V6-REAL-ZONES-1: Request-Zone Generation

- [ ] Port request-zone grouping logic.
- [ ] Generate real request-zone geometry from real app-generated candidates.
- [ ] Generate request-zone CSV rows.
- [ ] Generate request-zone GeoJSON.
- [ ] Keep exact geometry private.
- [ ] Add tests with synthetic safe geometry.

Acceptance:

- [ ] App produces request-zone CSV and GeoJSON from candidate data.
- [ ] Request zones are suitable for quote-package generation.
- [ ] No public coordinate exposure is introduced.

### V6-REAL-PACKAGE-1: Real Outputs Into Package Writer

- [ ] Feed real candidate CSV data into package writer.
- [ ] Feed real candidate GeoJSON into package writer.
- [ ] Feed real diagnostics into package writer.
- [ ] Feed real request zones into package writer.
- [ ] Feed real summary/map artifacts into package writer.
- [ ] Validate final package roles and inventory.

Acceptance:

- [ ] App generates full V6 package with real app-generated contents.
- [ ] Package writer no longer depends on synthetic rows for real workflow.
- [ ] Existing validator/contract pass on generated real package shape.

### V6-APP-FLOW-1: Private App Workflow

- [ ] Add private backend job for V6 generation.
- [ ] Add private operator status endpoint.
- [ ] Add private package metadata/review endpoint.
- [ ] Add private package download endpoint.
- [ ] Add UI button only after backend redaction tests pass.
- [ ] Never expose rows, coordinates, GeoJSON feature bodies, HTML contents, or summary contents in public DTOs.

Acceptance:

- [ ] Operator can generate/review/download from the app.
- [ ] CLI is no longer the normal operator workflow.
- [ ] Frontend/API exposure is private and redaction-tested.

## Rule Going Forward

Do not mark V6 real generation as complete until the app computes real candidate data from real app geospatial processing and feeds that into the V6 package writer.
