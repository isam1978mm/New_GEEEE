# V6 App Generation and Paid Imagery Workflow

## Decision

The final V6 direction is app-side generation, not notebook dependency.

The V6 notebook is a reference implementation and parity source. It is not the long-term runtime dependency for V6 package generation.

The application target is:

```text
operator input
-> app pipeline
-> app-generated V6 candidates
-> app-generated request zones
-> app-generated paid-imagery request package
-> app-side validation
-> operator review
-> paid-imagery request/order workflow
```

## Current Bridge Versus Final Target

The current V6 verifier/import work is a bridge and guardrail. It verifies a known-good external V6 package and can write a safe metadata-only summary.

That bridge is useful for source-locking and QA, but it is not the final product workflow.

The final product workflow must let the app independently generate the full V6 package that the notebook generated.

## App Must Generate The Full V6 Package

The app-side generator should be able to create the complete V6 package without relying on Colab or a notebook runtime.

The generated package should include:

- candidate tables;
- enhanced top candidate tables;
- stable candidate priority table;
- quality diagnostics table;
- request zones table;
- request zones GeoJSON;
- paid imagery quote template CSV;
- paid imagery quote comparison CSV;
- paid archive request summary text;
- visual inspection map HTML;
- package inventory JSON;
- final ZIP package;
- validation report.

The package validator and source-lock contract from the V6 integration track should become QA for app-generated outputs.

## Two Separate Concepts

V6 has two related but separate product concerns.

### 1. Generate Paid-Imagery Request Package

This is an app generation problem.

The app creates the package that an operator can send to imagery providers. This includes request zones, package metadata, quote templates, comparison files, summary text, map output, inventory, and ZIP.

This belongs inside the app-side V6 generator.

### 2. Actually Buy Or Request Paid Imagery

This is a procurement/provider workflow.

The app must not claim it can buy imagery automatically unless a real provider integration exists.

The app can support paid imagery ordering in staged levels:

```text
Level 1: generate request package for manual operator submission
Level 2: track provider quotes and order status
Level 3: submit provider API orders only after explicit operator approval
```

## Paid Imagery Workflow View

### Level 1: Request Package Generation

This is the first target.

The app generates a vendor-ready paid imagery request package. The operator reviews the package and sends it manually to one or more providers.

Allowed behavior:

- generate request zones;
- generate quote template CSV;
- generate quote comparison CSV;
- generate paid archive request summary;
- generate visual inspection map;
- generate final package ZIP;
- validate generated package;
- allow private operator review/download.

Not allowed at this level:

- automatic purchase;
- automatic payment;
- automatic provider order submission;
- storing payment credentials;
- claiming imagery has been purchased;
- public exposure of sensitive request geometry or candidate details.

### Level 2: Quote Tracking

After the app can generate the request package, it may track quote status from providers.

Allowed tracked metadata may include:

- provider name;
- quote date;
- requested product type;
- quoted resolution;
- quoted area or scene count;
- quoted cost;
- delivery estimate;
- status such as requested, quoted, approved, ordered, delivered, rejected;
- private operator notes.

Still not allowed:

- automatic purchase without explicit approval;
- exposing sensitive request geometry publicly;
- storing provider credentials without a secure design;
- treating quote metadata as proof that imagery has been purchased.

### Level 3: Provider API Ordering

This is a later optional target only if a real provider API is selected.

Before implementation, the project must have:

- provider API documentation;
- credential and secret-storage design;
- billing/payment rules;
- explicit operator approval flow;
- audit log design;
- cancellation/error handling;
- tests using mocked provider APIs;
- no real purchase in tests;
- no automatic order submission by default.

The order state machine should be explicit:

```text
package generated
-> quote requested
-> quote received
-> operator approved
-> order submitted
-> imagery delivered
-> imagery accepted/rejected
```

The app may submit a paid imagery order only after explicit operator confirmation.

## Correct Implementation Track

The next work should move from V6 integration/import to app-side generation.

Recommended sequence:

```text
V6-GENERATOR-1: document notebook-to-app generation design and exact stage map
V6-GENERATOR-2: implement app-side package generator using synthetic fixtures
V6-GENERATOR-3: add private CLI to generate V6 package from app inputs
V6-GENERATOR-4: validate generated package against V6 source-lock contract
V6-GENERATOR-5: compare generated package shape with frozen reference package
V6-GENERATOR-6: add private operator review/download flow
V6-PAID-IMAGERY-1: add manual quote/request tracking
V6-PAID-IMAGERY-2: design provider API ordering only if a real provider is chosen
```

## Generator Architecture

The app-side V6 generator should be structured as deterministic stages:

1. Input validation.
2. Candidate generation or candidate intake from app pipeline outputs.
3. Candidate scoring and top candidate selection.
4. Request-zone construction.
5. Quality diagnostics generation.
6. Quote template generation.
7. Quote comparison scaffold generation.
8. Paid archive request summary generation.
9. Visual inspection map generation.
10. Inventory generation.
11. ZIP packaging.
12. Validation using V6 contract and package verifier.

Each stage should have tests with synthetic data first.

The generator should not depend on Colab notebook state, Google Drive paths, or notebook globals.

## Required Safety Boundaries

Do not commit real generated V6 packages or external paid imagery outputs.

Do not log or document exact candidate rows, request geometry coordinates, GeoJSON feature bodies, GeoJSON feature properties, or map contents.

Do not run Earth Engine in unit tests.

Do not add automatic provider purchasing behavior without a separate provider API design.

Do not expose V6 paid imagery workflow through public API/frontend until backend generation, validation, redaction, and operator review are stable.

## Acceptance Definition For App-Side V6 Package Generation

The app-side generator can be accepted only when:

- it can generate all expected V6 package roles without the notebook runtime;
- generated package files match the source-lock role/category contract;
- generated CSV files have valid headers;
- generated GeoJSON files are structurally valid without exposing sensitive contents in logs;
- package inventory includes sizes and SHA256 values;
- final ZIP passes the V6 validator or a generator-specific equivalent;
- tests use synthetic fixtures only;
- no real V6 artifacts are committed;
- no paid imagery purchase is implied unless a provider workflow exists.

## Final Statement

The app should generate the full V6 package independently.

The paid-imagery request package belongs inside the app generator.

Actual paid imagery buying/requesting is a separate procurement workflow. The first implementation should be manual request-package generation. Quote tracking can follow. Provider API ordering comes later only with real provider integration, secure credentials, billing rules, and explicit operator approval.