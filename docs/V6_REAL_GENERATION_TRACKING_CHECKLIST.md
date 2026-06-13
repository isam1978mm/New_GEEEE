# V6 Real Generation Tracking Checklist

## Correction

The current `v6_generator_*` code is a scaffold and package writer.

It is not the real V6 geospatial generator.

Do not mark real V6 generation complete until the app computes real candidate data from real app geospatial processing and feeds those app outputs into the V6 package writer.

## Current Status

### Scaffold / Package Writer

- [x] Create V6 package file roles from synthetic fixtures.
- [x] Create V6 package file roles from safe app-input fixtures.
- [x] Create inventory JSON.
- [x] Create ZIP package.
- [x] Create validation report.
- [x] Validate expected file roles.
- [x] Validate CSV header shape.
- [x] Validate GeoJSON top-level shell.
- [x] Validate inventory hashes and sizes.
- [x] CLI can write a scaffold package into an operator output folder.

### Real Generation

- [ ] Real app-side Earth Engine runtime boundary.
- [ ] Real AOI validation.
- [ ] Real grid construction.
- [ ] Real Sentinel-2 data access.
- [ ] Real terrain feature access.
- [ ] Real water mask feature access.
- [ ] Real vegetation/bare-soil index generation.
- [ ] Real road/building warning layer generation.
- [ ] Real per-grid-cell scoring.
- [ ] Real candidate ranking.
- [ ] Real request-zone generation.
- [ ] Real app-generated candidates and request zones fed into package writer.
- [ ] Private app generate/review/download workflow.

## Important Clarification

Current scaffold status:

```text
same output roles: yes
same real geospatial outputs: no
real coordinates: no
fake coordinates: no
empty safe GeoJSON shell: yes
Earth Engine: no
app button/download flow: no
```

## Correct Roadmap

### V6-SCAFFOLD-1: Package Writer Foundation

Status: done as scaffold only.

- [x] Build all package roles from fixture data.
- [x] Build inventory JSON.
- [x] Build ZIP package.
- [x] Build validation report.
- [x] Keep notebook runtime out.
- [x] Keep real artifact files out.
- [x] Keep real coordinates out.

Acceptance:

- [x] App can write package-shaped output without notebook runtime.
- [x] Unit tests pass for scaffold package writing.

### V6-REAL-GEE-1: Runtime Boundary And AOI/Grid

Status: next.

- [ ] Add app-side Earth Engine runtime adapter.
- [ ] Keep Earth Engine calls out of unit tests.
- [ ] Add runtime configuration for auth/credential behavior.
- [ ] Port AOI input validation from notebook logic.
- [ ] Port deterministic grid construction from notebook logic.
- [ ] Return app-side grid-cell records for scoring.
- [ ] Do not print exact coordinates in normal logs.
- [ ] Add synthetic tests for AOI/grid behavior without Earth Engine calls.

Acceptance:

- [ ] App has a real Earth Engine runtime boundary.
- [ ] AOI/grid construction is app-side, not notebook-side.
- [ ] Unit tests do not call Earth Engine.
- [ ] No notebook globals or Google Drive paths are required.

### V6-REAL-GEE-2: Geospatial Feature Layers

- [ ] Port Sentinel-2 source loading and date filtering.
- [ ] Port cloud/visibility support features.
- [ ] Port terrain features.
- [ ] Port water mask features.
- [ ] Port vegetation/bare-soil index features.
- [ ] Port road/building warning layers.
- [ ] Produce per-grid-cell feature summaries.
- [ ] Add synthetic tests for feature summary schema.

Acceptance:

- [ ] App produces feature rows needed by the V6 scorer.
- [ ] Feature extraction is separate from package writing.
- [ ] No real feature rows or coordinates are printed in logs.

### V6-REAL-SCORING-1: Candidate Scoring And Ranking

- [ ] Port V6 scoring weights.
- [ ] Port false-positive warning/penalty logic.
- [ ] Port quality-adjusted scoring.
- [ ] Port final priority ranking.
- [ ] Add deterministic tie handling.
- [ ] Add tests for missing/invalid feature values.

Acceptance:

- [ ] App produces candidate table rows from app-generated feature rows.
- [ ] Ranking is deterministic.
- [ ] Scoring is testable without Earth Engine.

### V6-REAL-ZONES-1: Request-Zone Generation

- [ ] Port request-zone grouping logic.
- [ ] Generate request-zone records from ranked candidates.
- [ ] Generate request-zone geometry from app-side candidate/grid geometry.
- [ ] Generate request-zone CSV.
- [ ] Generate request-zone GeoJSON.
- [ ] Keep exact geometry private.
- [ ] Add tests with synthetic safe geometry.

Acceptance:

- [ ] App produces request-zone CSV and GeoJSON from candidate data.
- [ ] Request zones are suitable for quote package generation.
- [ ] No public coordinate exposure is introduced.

### V6-REAL-PACKAGE-1: Real App Outputs Into Package Writer

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

### V6-APP-FLOW-1: Private Generate / Review / Download Flow

- [ ] Add private backend generation job.
- [ ] Add private status endpoint.
- [ ] Add private package metadata/review endpoint.
- [ ] Add private package download endpoint.
- [ ] Add UI button only after backend redaction tests pass.
- [ ] Never expose rows, coordinates, GeoJSON feature bodies, HTML contents, or summary contents in public DTOs.

Acceptance:

- [ ] Operator can generate, review, and download from the app.
- [ ] CLI is no longer the normal operator workflow.
- [ ] Frontend/API exposure is private and redaction-tested.

## Safety Checklist

- [ ] Do not commit real V6 ZIP files.
- [ ] Do not commit real V6 CSV files.
- [ ] Do not commit real V6 GeoJSON files.
- [ ] Do not commit real V6 HTML map files.
- [ ] Do not commit real V6 TXT summaries.
- [ ] Do not commit external inventory files.
- [ ] Do not commit the V6 notebook.
- [ ] Do not commit generated package folders.
- [ ] Do not expose exact coordinates in logs or docs.
- [ ] Do not expose candidate rows in logs or docs.
- [ ] Do not expose GeoJSON feature bodies, feature properties, or coordinate arrays.
- [ ] Do not expose HTML map contents.
- [ ] Do not run Earth Engine in unit tests.

## Current Next Step

```text
V6-REAL-GEE-1: implement the app-side Earth Engine runtime boundary and AOI/grid logic.
```

Do not continue expanding scaffold-only generation until this real generation path is started.
