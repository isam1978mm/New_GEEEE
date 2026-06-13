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
- [x] V6-GENERATOR-1 notebook-to-app stage map documented.
- [x] V6-GENERATOR-2 synthetic app-side V6 package generator implemented.
- [x] Synthetic app-side V6 package generation CLI added.
- [x] Synthetic app-generated V6 package validated against the source-lock contract.
- [x] V6-GENERATOR-3 app-input fixture models connected to generator and CLI.
- [ ] App-generated package compared against the frozen reference package shape.
- [ ] Private operator review/download flow added.
- [ ] Paid imagery quote tracking added.
- [ ] Provider API ordering designed only after selecting a real provider.

## Non-Negotiable Direction

- [x] The V6 notebook is treated as reference/parity source only.
- [x] The app does not rely on Colab runtime, Google Drive runtime paths, notebook globals, or manual notebook execution for synthetic/app-input fixture V6 package generation.
- [x] The app can now generate the full V6 package shape independently with synthetic fixtures.
- [x] The app can now generate the full V6 package shape from safe app-input fixtures.
- [ ] The app can generate the full V6 package from real app pipeline outputs.
- [x] The verifier/importer remains QA and audit support, not the primary V6 workflow.

## V6 Package Generation Scope

The app-side generator now produces all package roles below from synthetic fixtures and safe app-input fixtures. Real app-output generation remains a later step.

- [x] Timestamped top candidate CSV.
- [x] Timestamped top candidate GeoJSON.
- [x] Enhanced top candidate CSV.
- [x] Enhanced top candidate GeoJSON.
- [x] Stable candidate priority CSV.
- [x] Quality diagnostics CSV.
- [x] Request zones CSV.
- [x] Request zones GeoJSON.
- [x] Paid imagery quote template CSV.
- [x] Paid imagery quote comparison CSV.
- [x] Paid archive request summary TXT.
- [x] Visual inspection map HTML.
- [x] Inventory JSON with filenames, sizes, and SHA256 hashes.
- [x] Final V6 ZIP package.
- [x] Validation report.

## Generator Stage Checklist

### V6-GENERATOR-1: Notebook-To-App Generation Design

- [x] Map V6 notebook logic into app stages.
- [x] Identify app inputs required to generate V6 outputs.
- [x] Identify current app pipeline outputs that can feed V6 generation.
- [x] Define generator stage boundaries.
- [x] Define synthetic fixture strategy.
- [x] Define safety/redaction policy for generated files and logs.
- [x] Define validation strategy using current V6 validator and contract.
- [x] Document what notebook logic is in-scope and out-of-scope.
- [x] No generator code added in V6-GENERATOR-1.

Acceptance:

- [x] Documentation explains how the app replaces notebook generation.
- [x] Documentation separates package generation from paid imagery ordering.
- [x] Documentation lists exact output roles and stage map.

### V6-GENERATOR-2: Synthetic App-Side Package Generator

- [x] Add generator service using synthetic input fixtures first.
- [x] Generate all required file roles from synthetic data.
- [x] Generate CSVs with correct headers.
- [x] Generate GeoJSON FeatureCollection shells with synthetic safe geometry only.
- [x] Generate TXT summary from synthetic metadata.
- [x] Generate simple private visual map output or safe placeholder HTML from synthetic data.
- [x] Generate inventory JSON.
- [x] Generate ZIP package.
- [x] Do not use real V6 package data.
- [x] Do not run Earth Engine.
- [x] Do not touch notebooks.

Acceptance:

- [x] Unit tests prove all expected output roles are generated.
- [x] Unit tests prove inventory hashes and sizes match generated files.
- [x] Unit tests prove no real coordinates or real candidate rows are used.
- [x] Unit tests prove generated synthetic ZIP passes the existing V6 validator with a synthetic reference document.

### V6-GENERATOR-3: Connect Generator To App Input Models

- [x] Define app input model for V6 generation.
- [x] Define safe app-input fixture loading.
- [x] Keep synthetic fixture path available for tests.
- [x] Add private CLI mode that accepts app-input JSON fixture data.
- [x] CLI takes operator-supplied output directory.
- [x] CLI does not write into Git by default.
- [x] CLI prints only safe status, output path, counts, and validation result.
- [x] CLI does not print rows, coordinates, GeoJSON contents, HTML contents, or candidate IDs.

Acceptance:

- [x] CLI can generate a package from synthetic fixtures.
- [x] CLI can generate a package from app-input fixture data.
- [x] CLI output passes safety checks.
- [x] CLI generated ZIP passes validator/contract checks.

### V6-GENERATOR-4: Generated Package Validation Failure Modes

- [x] Reuse V6 package validator against synthetic app-generated ZIP.
- [x] Reuse V6 source-lock contract for synthetic package shape.
- [x] Add generator-specific validation for generated inventory.
- [x] Validate CSV headers.
- [x] Validate GeoJSON top-level structure.
- [x] Validate category counts and role counts.
- [x] Validate ZIP member count and payload count.
- [ ] Add explicit failure-mode tests for missing required payloads.
- [ ] Add explicit failure-mode tests for bad CSV headers.
- [ ] Add explicit failure-mode tests for invalid GeoJSON top-level structure.
- [ ] Add explicit failure-mode tests for inventory hash/size mismatch.
- [ ] Extend validation to real app-output package fixtures.

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

- [x] Treat paid imagery request package generation as app-side generation.
- [x] Treat actual paid imagery buying/requesting as procurement workflow.
- [ ] Add manual quote status tracking only after generator works with app inputs.
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

- [ ] `python -m pytest tests/unit/test_v6_generator_package.py -q`
- [ ] `python -m pytest tests/unit/test_v6_package_validator.py -q`
- [ ] `python -m pytest tests/unit/test_v6_package_contract.py -q`
- [ ] `python -m pytest tests/unit/test_v6_package_importer.py -q`
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
V6-GENERATOR-4: add explicit generated-package validation failure-mode tests.
```

This task should prove the generator fails closed for missing files, bad headers, invalid top-level GeoJSON, and inventory mismatch without using real V6 artifacts.