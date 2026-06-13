# V6 Generator Tracking Checklist

## Purpose

This checklist keeps the V6 direction tracked in the repository.

The goal is not to depend on the external notebook as the production generator. The goal is for the app to independently generate the full V6 package, then use the existing V6 verifier and contract as QA for generated outputs.

## Current State

- [x] Frozen external V6 reference package documented.
- [x] Read-only V6 package verifier added.
- [x] V6 source-lock/schema contract added.
- [x] Private safe summary importer added.
- [x] Internal provenance storage gates documented.
- [x] Final product direction documented: app-side V6 generation, not notebook dependency.
- [ ] App-side V6 generator implemented.
- [ ] App-side V6 package generation CLI added.
- [ ] App-generated V6 package validated against the source-lock contract.
- [ ] App-generated package compared against the frozen reference package shape.
- [ ] Private operator review/download flow added.
- [ ] Paid imagery quote tracking added.
- [ ] Provider API ordering designed only after selecting a real provider.

## Non-Negotiable Direction

- [ ] The V6 notebook is treated as reference/parity source only.
- [ ] The app does not rely on Colab runtime, Google Drive runtime paths, notebook globals, or manual notebook execution to generate V6 outputs.
- [ ] The app can generate the full V6 package independently.
- [ ] The verifier/importer remains QA and audit support, not the primary V6 workflow.

## V6 Package Generation Scope

The app-side generator must eventually produce all package roles below.

- [ ] Timestamped top candidate CSV.
- [ ] Timestamped top candidate GeoJSON.
- [ ] Enhanced top candidate CSV.
- [ ] Enhanced top candidate GeoJSON.
- [ ] Stable candidate priority CSV.
- [ ] Quality diagnostics CSV.
- [ ] Request zones CSV.
- [ ] Request zones GeoJSON.
- [ ] Paid imagery quote template CSV.
- [ ] Paid imagery quote comparison CSV.
- [ ] Paid archive request summary TXT.
- [ ] Visual inspection map HTML.
- [ ] Inventory JSON with filenames, sizes, and SHA256 hashes.
- [ ] Final V6 ZIP package.
- [ ] Validation report.

## Generator Stage Checklist

### V6-GENERATOR-1: Notebook-To-App Generation Design

- [ ] Map V6 notebook logic into app stages.
- [ ] Identify app inputs required to generate V6 outputs.
- [ ] Identify current app pipeline outputs that can feed V6 generation.
- [ ] Define generator stage boundaries.
- [ ] Define synthetic fixture strategy.
- [ ] Define safety/redaction policy for generated files and logs.
- [ ] Define validation strategy using current V6 validator and contract.
- [ ] Document what notebook logic is in-scope and out-of-scope.
- [ ] No code generation yet unless needed for pure constants/schema.

Acceptance:

- [ ] Documentation explains how the app replaces notebook generation.
- [ ] Documentation separates package generation from paid imagery ordering.
- [ ] Documentation lists exact output roles and stage map.

### V6-GENERATOR-2: Synthetic App-Side Package Generator

- [ ] Add generator service using synthetic input fixtures first.
- [ ] Generate all required file roles from synthetic data.
- [ ] Generate CSVs with correct headers.
- [ ] Generate GeoJSON FeatureCollection shells with synthetic safe geometry only.
- [ ] Generate TXT summary from synthetic metadata.
- [ ] Generate simple private visual map output or safe placeholder HTML from synthetic data.
- [ ] Generate inventory JSON.
- [ ] Generate ZIP package.
- [ ] Do not use real V6 package data.
- [ ] Do not run Earth Engine.
- [ ] Do not touch notebooks.

Acceptance:

- [ ] Unit tests prove all expected output roles are generated.
- [ ] Unit tests prove inventory hashes and sizes match generated files.
- [ ] Unit tests prove no real coordinates or real candidate rows are used.

### V6-GENERATOR-3: Private CLI For App-Side Generation

- [ ] Add private CLI command for synthetic or app-input generation.
- [ ] CLI takes operator-supplied output directory.
- [ ] CLI does not write into Git by default.
- [ ] CLI prints only safe status, output path, counts, and validation result.
- [ ] CLI does not print rows, coordinates, GeoJSON contents, HTML contents, or full sensitive paths.

Acceptance:

- [ ] CLI can generate a package from synthetic fixtures.
- [ ] CLI output passes safety checks.
- [ ] CLI generated ZIP passes validator/contract checks.

### V6-GENERATOR-4: Generated Package Validation

- [ ] Reuse V6 package validator against app-generated ZIP.
- [ ] Reuse V6 source-lock contract where applicable.
- [ ] Add generator-specific validation for generated inventory.
- [ ] Validate CSV headers.
- [ ] Validate GeoJSON top-level structure.
- [ ] Validate category counts and role counts.
- [ ] Validate ZIP member count and payload count.

Acceptance:

- [ ] Generated package fails clearly when any required role is missing.
- [ ] Generated package fails clearly when inventory hashes do not match.
- [ ] Generated package fails clearly when CSV headers are wrong.
- [ ] Generated package fails clearly when GeoJSON top-level structure is wrong.

### V6-GENERATOR-5: Frozen Reference Shape Comparison

- [ ] Compare app-generated package shape to frozen V6 reference shape.
- [ ] Compare roles, filenames patterns, categories, file extensions, and inventory structure.
- [ ] Compare CSV header sets only.
- [ ] Compare GeoJSON top-level structure only.
- [ ] Do not compare or expose real rows, coordinates, feature properties, map contents, or text summary contents.

Acceptance:

- [ ] Shape comparison uses safe metadata only.
- [ ] No real V6 sensitive content enters tests or logs.
- [ ] Differences are reported as safe metadata differences only.

### V6-GENERATOR-6: Private Operator Review And Download

- [ ] Add private operator review flow only after backend generator is stable.
- [ ] Review shows safe package metadata and validation status.
- [ ] Review allows private download of generated package only if allowed by operator workflow.
- [ ] No public API exposure.
- [ ] No frontend exposure unless explicitly designed and redaction-tested.
- [ ] No artifact serving without a reviewed private route/design.

Acceptance:

- [ ] Review path is private/internal only.
- [ ] Public DTOs do not include V6 package contents.
- [ ] Redaction tests cover logs and responses.

## Paid Imagery Workflow Checklist

### V6-PAID-IMAGERY-1: Manual Quote/Request Tracking

- [ ] Treat paid imagery request package generation as app-side generation.
- [ ] Treat actual paid imagery buying/requesting as procurement workflow.
- [ ] Add manual quote status tracking only after generator works.
- [ ] Track provider name, quote date, product type, quoted resolution, quoted cost, delivery estimate, status, and private operator notes.
- [ ] Do not store payment credentials.
- [ ] Do not submit provider orders automatically.
- [ ] Do not claim imagery is purchased unless operator marks it as ordered/delivered.

Acceptance:

- [ ] Manual tracking does not require provider credentials.
- [ ] Manual tracking does not expose sensitive geometry publicly.
- [ ] Manual tracking has clear statuses.

### V6-PAID-IMAGERY-2: Provider API Ordering Design

This is optional and only after a real provider is selected.

- [ ] Identify provider and API documentation.
- [ ] Define authentication and secret storage.
- [ ] Define billing/payment policy.
- [ ] Define explicit operator approval gate.
- [ ] Define order state machine.
- [ ] Define cancellation and error handling.
- [ ] Define audit logging without sensitive coordinates in normal logs.
- [ ] Define mocked tests with no real purchases.
- [ ] Keep automatic ordering disabled by default.

Acceptance:

- [ ] No real purchase can happen in tests.
- [ ] No order submission happens without explicit operator approval.
- [ ] Provider credentials are never committed.
- [ ] Provider response data is redacted before any public exposure.

## Safety Checklist For Every V6 Generator Task

- [ ] Do not commit real V6 ZIP files.
- [ ] Do not commit real V6 CSV files.
- [ ] Do not commit real V6 GeoJSON files.
- [ ] Do not commit real V6 HTML map files.
- [ ] Do not commit real V6 TXT summaries.
- [ ] Do not commit external inventory files.
- [ ] Do not commit the V6 notebook.
- [ ] Do not commit generated package folders.
- [ ] Do not commit Graphify output.
- [ ] Do not commit pytest cache/temp folders.
- [ ] Do not expose exact coordinates in logs or docs.
- [ ] Do not expose candidate rows in logs or docs.
- [ ] Do not expose GeoJSON feature bodies, feature properties, or coordinate arrays.
- [ ] Do not expose HTML map contents.
- [ ] Do not expose paid archive summary contents unless specifically redacted.
- [ ] Do not run Earth Engine in unit tests.
- [ ] Use synthetic fixtures first.
- [ ] Keep public API/frontend out until backend generator and redaction checks are stable.

## Validation Checklist For Every Task

Run only relevant tests for touched code, but keep this baseline visible:

- [ ] `python -m pytest tests/unit/test_v6_package_validator.py -q`
- [ ] `python -m pytest tests/unit/test_v6_package_contract.py -q`
- [ ] `python -m pytest tests/unit/test_v6_package_importer.py -q`
- [ ] Generator-specific tests once added.
- [ ] `python -m pytest tests/unit/test_notebook_safety.py -q --basetemp .pytest-v6-generator`

## Git Hygiene Checklist

Before every commit:

- [ ] `git status --short` reviewed.
- [ ] Only intended source/docs/test files are staged.
- [ ] No generated packages are staged.
- [ ] No external V6 files are staged.
- [ ] No graphify-out files are staged.
- [ ] No pytest temp/cache files are staged.
- [ ] `git diff --cached --name-only` reviewed.

## Current Next Step

The next tracked task is:

```text
V6-GENERATOR-1: Document notebook-to-app generation design and exact stage map.
```

This task should convert the V6 notebook reference into an app-side generator stage map. It should not implement the generator yet unless a tiny constants/helper module is clearly needed.