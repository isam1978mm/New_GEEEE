# V6-GENERATOR-1 Notebook-To-App Stage Map

## Purpose

V6-GENERATOR-1 converts the V6 notebook reference into an app-side generation design.

This is a design and tracking step. It does not implement the generator yet.

The final direction is that the app independently generates the full V6 package. The notebook is only a reference/parity source and must not remain the production runtime dependency.

## Final Runtime Target

```text
operator input
-> app-side V6 generation pipeline
-> app-generated candidates and diagnostics
-> app-generated request zones
-> app-generated paid-imagery request package
-> app-generated inventory and ZIP
-> app-side validation
-> operator review
-> manual quote/request workflow first
```

The verifier/importer built during the V6 integration track remains useful, but it should be used as QA and source-lock checking for generated packages, not as the primary V6 workflow.

## Reference Notebook Summary

The V6 reference notebook has these high-level sections:

1. Install dependencies.
2. Define imports and configuration.
3. Authenticate and initialize Earth Engine.
4. Build AOI and fixed grid.
5. Load public GEE datasets and build indices.
6. Build legal/environmental exclusion masks and false-positive warning layers.
7. Score pixels as paid archive request candidates.
8. Reduce pixel scores to grid cells and rank candidates.
9. Export basic top candidates to CSV and GeoJSON.
10. Build visual inspection map.
11. Build all-cell quality diagnostics and v5 warning scores.
12. Run sensitivity/stability analysis and seasonal stability.
13. Add v6 road/building filters and v6 priority score.
14. Create v6 request zones.
15. Create paid-imagery quote template and comparison scorer.
16. Create paid archive request summary text.
17. Export map HTML and build final V6 ZIP package.
18. State final lawful desk-based output rule.

The app must reproduce this workflow as explicit services/stages rather than notebook cells.

## App Stage Map

### Stage 0: Configuration And Inputs

Notebook reference:

```text
imports/configuration cell
```

App replacement:

```text
V6GenerationInput
V6GenerationConfig
V6RunContext
```

Inputs:

- project identifier or app run context;
- AOI bounding box or app-selected AOI;
- date range;
- grid size;
- top-N candidate count;
- request-zone max count;
- request-zone grouping distance;
- scoring weights;
- output directory.

Rules:

- no notebook globals;
- no Google Drive paths;
- no hardcoded Colab folders;
- operator input must be validated before generation;
- exact coordinates must not be logged in normal logs.

### Stage 1: Earth Engine Runtime Boundary

Notebook reference:

```text
Authenticate and initialize Earth Engine
```

App replacement:

```text
V6DataSource adapter
EarthEngineV6DataSource implementation
SyntheticV6DataSource test implementation
```

Purpose:

- isolate Earth Engine access behind a runtime adapter;
- keep unit tests independent from Earth Engine;
- allow synthetic fixtures for CI;
- make future data-source replacement possible.

Rules:

- Earth Engine is allowed only in an explicit runtime stage, never in unit tests;
- tests use synthetic data source only;
- auth fallback behavior must follow app safety rules and must not reintroduce notebook-style interactive auth in backend code;
- no provider/order API belongs in this stage.

### Stage 2: AOI And Grid Construction

Notebook reference:

```text
Build AOI and fixed grid
```

App replacement:

```text
build_v6_aoi()
build_v6_grid()
V6GridCell model
```

Outputs:

- AOI object or internal geometry representation;
- grid metadata;
- grid cells with internal cell IDs;
- safe grid summary metadata.

Rules:

- generated grid must be deterministic from input;
- grid metadata can be logged only in safe form;
- exact geometries stay private and are written only into generated package files, not ordinary logs.

### Stage 3: Public Dataset Feature Extraction

Notebook reference:

```text
Load public GEE datasets and build indices
```

App replacement:

```text
V6SignalFeatureBuilder
```

Expected feature families:

- Sentinel-2 visibility/cloud support signals;
- vegetation/soil/bare-ground signals;
- terrain slope/elevation-derived signals;
- water/legal/environmental exclusion signals;
- built/road false-positive warning signals;
- count/coverage diagnostics.

Rules:

- feature extraction must be reproducible from config;
- output features should be numeric summaries per grid cell;
- no claim of proving archaeological/material targets;
- generated feature tables are request-prioritization data only.

### Stage 4: Exclusion And Warning Masks

Notebook reference:

```text
Build legal/environmental exclusion masks and v5 false-positive warning layers
```

App replacement:

```text
V6EligibilityAndWarningBuilder
```

Outputs:

- eligibility score;
- water warning fraction;
- built-area warning fraction;
- road/proximity warning fraction;
- modern-feature warning metadata;
- false-positive penalty components.

Rules:

- warning layers reduce priority or flag review;
- warnings do not automatically prove a candidate is invalid;
- exclusion logic must be documented and testable with synthetic fixtures.

### Stage 5: Candidate Pixel/Cell Scoring

Notebook reference:

```text
Score pixels as paid archive request candidates
Reduce scores to grid cells and rank candidates
```

App replacement:

```text
V6CandidateScorer
V6GridReducer
V6CandidateRanker
```

Outputs:

- cell-level candidate score;
- visibility score;
- remote-sensing contrast score;
- terrain score;
- eligibility score;
- source-count diagnostics;
- ranked candidate table.

Rules:

- scoring weights must be configuration-controlled;
- ranking must be deterministic;
- output must support top-N selection;
- unit tests must cover ranking ties and missing values with synthetic data.

### Stage 6: Basic Top Candidate Export

Notebook reference:

```text
Export basic top candidates to CSV and GeoJSON
```

App replacement:

```text
V6CandidateExporter
```

Outputs:

- `lawful_gee_candidate_scout_top_<N>_<timestamp>.csv`
- `lawful_gee_candidate_scout_top_<N>_<timestamp>.geojson`

Rules:

- CSV headers must match contract;
- GeoJSON must be FeatureCollection;
- normal logs must not print candidate rows or coordinates;
- tests use synthetic candidates only.

### Stage 7: Quality Diagnostics And Stability

Notebook reference:

```text
v5 all-cell confidence, score gaps, false-positive warnings
v5 sensitivity/stability analysis and seasonal stability
```

App replacement:

```text
V6QualityDiagnosticsBuilder
V6StabilityAnalyzer
```

Outputs:

- quality diagnostics table;
- score percentile;
- score gap from median;
- next-candidate score gap;
- confidence values;
- scenario sensitivity results;
- seasonal stability metrics.

Package role:

- `quality_diagnostics_all_cells_v6.csv`

Rules:

- keep diagnostics deterministic;
- synthetic tests cover score normalization, scenario weights, and missing features;
- diagnostics are private package outputs, not public app claims.

### Stage 8: V6 Priority Upgrade

Notebook reference:

```text
v6 stronger road/building filters and v6 priority score
```

App replacement:

```text
V6PriorityScorer
```

Outputs:

- v6 false-positive penalty;
- v6 quality-adjusted score;
- v6 review priority score;
- v6 final priority rank;
- enhanced top candidate table.

Package roles:

- `stable_candidate_priority_list_v6.csv`
- `top25_enhanced_v6.csv`
- `top25_enhanced_v6.geojson`

Rules:

- stronger road/building filters are warnings and priority adjustments;
- do not remove candidates silently unless explicitly configured;
- all score formulas must be documented and tested with synthetic rows.

### Stage 9: Request-Zone Creation

Notebook reference:

```text
v6 request-zone creation
```

App replacement:

```text
V6RequestZoneBuilder
```

Purpose:

- merge nearby high-priority cells into quote-ready polygons;
- reduce scattered single-cell purchase requests;
- provide provider-ready coverage areas.

Outputs:

- request-zone records;
- request-zone polygons;
- primary candidate references;
- zone scores;
- zone area/priority metadata.

Package roles:

- `request_zones_v6.csv`
- `request_zones_v6.geojson`

Rules:

- request zones are for imagery quoting, not field authorization;
- generated zones must be private package outputs;
- no coordinates in ordinary logs;
- tests use synthetic safe geometries.

### Stage 10: Paid-Imagery Quote Package

Notebook reference:

```text
paid-imagery quote comparison template and scorer
```

App replacement:

```text
V6QuoteTemplateBuilder
V6QuoteComparisonScorer
```

Outputs:

- vendor quote template rows;
- optional quote-comparison scaffold;
- provider-offer scoring logic for later operator-entered quotes.

Package roles:

- `paid_imagery_quote_template_v6.csv`
- `paid_imagery_quote_comparison_v6.csv`

Rules:

- this stage creates a request/quote package only;
- it does not order imagery;
- it does not store payment credentials;
- it does not submit provider API requests;
- provider quote scoring is advisory and operator-reviewed.

### Stage 11: Paid Archive Request Summary

Notebook reference:

```text
Create v6 paid archive request summary text
```

App replacement:

```text
V6PaidArchiveSummaryBuilder
```

Output:

- `paid_archive_request_summary.txt`

Contents:

- package purpose;
- date range;
- request-zone count;
- top candidate summary;
- quote package instructions;
- lawful desk-based limitation statement.

Rules:

- summary text is a generated package artifact;
- do not print the full summary contents in logs;
- examples in docs must be generic or redacted;
- summary must not imply excavation, ownership, field authorization, or proof.

### Stage 12: Visual Inspection Map

Notebook reference:

```text
Visual inspection map
Export v6 map HTML
```

App replacement:

```text
V6InspectionMapBuilder
```

Output:

- `visual_inspection_map.html`

Rules:

- map is a private operator review artifact;
- no public map serving until a separate reviewed design exists;
- no map content in logs or docs;
- synthetic map fixture can be simple placeholder HTML for generator tests.

### Stage 13: Inventory And ZIP Packaging

Notebook reference:

```text
build final v6 ZIP package
```

App replacement:

```text
V6PackageInventoryBuilder
V6PackageZipWriter
```

Outputs:

- inventory JSON;
- final V6 ZIP package;
- safe validation report.

Rules:

- include filenames, sizes, and SHA256 hashes;
- keep package output in operator-supplied path outside Git by default;
- do not stage generated outputs;
- validator must verify generated package structure.

### Stage 14: Validation And QA

Notebook reference:

```text
implicit manual checking plus final ZIP output
```

App replacement:

```text
V6GeneratedPackageValidator
```

Validation should use:

- existing V6 package validator;
- existing source-lock contract;
- generated inventory validation;
- CSV header checks;
- GeoJSON top-level checks;
- role/category count checks;
- ZIP member count checks.

Rules:

- generated package must fail closed when required files are missing;
- validation output must be safe metadata only;
- validation must not expose rows, coordinates, GeoJSON feature bodies, HTML, or summary contents.

## Proposed App Module Boundaries

Future implementation may use these module boundaries:

```text
app/services/v6_generator_inputs.py
app/services/v6_generator_grid.py
app/services/v6_generator_features.py
app/services/v6_generator_scoring.py
app/services/v6_generator_diagnostics.py
app/services/v6_generator_request_zones.py
app/services/v6_generator_quotes.py
app/services/v6_generator_summary.py
app/services/v6_generator_map.py
app/services/v6_generator_package.py
app/cli/v6_package_generate.py
tests/unit/test_v6_generator_*.py
```

These names are proposed boundaries, not mandatory file names.

## Synthetic Fixture Strategy

V6-GENERATOR-2 must start with synthetic fixtures.

Synthetic fixtures should provide:

- small grid with fake cell IDs;
- fake numeric score columns;
- fake warning fractions;
- fake quality/stability columns;
- fake request-zone geometry that is safe and not derived from real V6 coordinates;
- fake quote-template metadata;
- generic summary text;
- placeholder HTML map.

Synthetic fixture tests must prove package shape without relying on real V6 package contents.

## Paid Imagery Buying/Requesting Boundary

Generating the paid-imagery request package belongs inside the V6 app generator.

Actually buying/requesting paid imagery is a separate workflow.

The staged plan is:

```text
Level 1: app generates request package; operator manually sends to provider
Level 2: app tracks provider quotes and status manually
Level 3: app submits provider API order only after real provider integration and explicit operator approval
```

No automatic purchase or provider order submission belongs in V6-GENERATOR work.

## In Scope For V6-GENERATOR-2

- synthetic package generator service;
- generate all required package roles from synthetic inputs;
- inventory JSON generation;
- ZIP generation;
- validation against contract shape;
- unit tests only.

## Out Of Scope For V6-GENERATOR-2

- real Earth Engine execution;
- real V6 coordinates;
- real V6 package rows;
- frontend;
- public API routes;
- provider quote tracking;
- provider API ordering;
- automatic paid imagery purchase;
- committing generated artifacts.

## Acceptance For V6-GENERATOR-1

This stage map is accepted when:

- the notebook workflow is mapped into app stages;
- package generation is clearly separated from paid imagery buying/requesting;
- the full V6 package role list is documented;
- future module boundaries are proposed;
- safety and synthetic fixture strategy are defined;
- next implementation step is V6-GENERATOR-2.

## Next Step

```text
V6-GENERATOR-2: implement an app-side synthetic V6 package generator that creates every required package role, inventory JSON, and ZIP, then validates the generated package shape without using real V6 artifacts.
```