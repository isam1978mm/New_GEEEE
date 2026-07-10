# V6 App Generation and Paid Imagery Export Workflow

## Decision

The app-side package feature is active and should be referred to publicly as the **Paid Imagery Export Package**.

Internal `V6` / `v6_*` names remain legacy implementation names for compatibility with routes, generated filenames, tests, and existing package contracts.

The old/external V6 notebook remains a separate unresolved source-lock/parity track. The active app package must not claim frozen external V6 notebook parity unless a verified external source is supplied.

## Current App Target

```text
operator input
-> app pipeline
-> app-generated candidates or app-derived candidate intake
-> app-generated request zones
-> app-generated Paid Imagery Export Package
-> app-side validation
-> operator review
-> manual provider submission outside the app
```

## App Must Generate The Export Package

The app-side generator should create the complete export package without relying on Colab or notebook runtime state.

The generated package includes:

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

## Two Separate Concepts

### 1. Generate Paid Imagery Export Package

This is app generation. The app creates a private ZIP package that an operator can manually review and use outside the app. This includes request zones, package metadata, quote templates, comparison files, summary text, placeholder map output, inventory, and ZIP.

### 2. Actually Buy Or Order Paid Imagery

This is a procurement/provider workflow and is not implemented.

The app must not claim it can buy imagery automatically unless a real provider integration exists.

Allowed staged levels:

```text
Level 1: generate export package for manual operator use
Level 2: track provider quotes and order status
Level 3: submit provider API orders only after explicit operator approval
```

## Level 1: Export Package Generation

Allowed behavior:

- generate request zones;
- generate quote template CSV;
- generate quote comparison CSV;
- generate paid archive request summary;
- generate visual inspection placeholder map;
- generate final package ZIP;
- validate generated package;
- allow private operator metadata review/download.

Not allowed at this level:

- automatic purchase;
- automatic payment;
- automatic provider order submission;
- storing payment credentials;
- claiming imagery has been purchased;
- public exposure of sensitive request geometry or candidate details.

## Provenance Requirements

The package must record:

```text
package provenance
score basis
geometry basis
fallback score label when used
fallback geometry label when used
placeholder map label when used
filesystem-only/private policy
frontend metadata-only policy
frozen external notebook parity claimed: false unless verified source supplied
```

## Required Safety Boundaries

Do not commit real generated V6 packages or external paid imagery outputs.

Do not log or document exact candidate rows, request geometry coordinates, GeoJSON feature bodies, GeoJSON feature properties, or map contents.

Do not run Earth Engine in unit tests.

Do not add automatic provider purchasing behavior without a separate provider API design.

Do not expose package rows or geometry through public API/frontend. Browser review remains metadata-only.

## Final Statement

The app should generate the Paid Imagery Export Package independently.

Actual paid imagery buying/ordering is a separate procurement workflow. The current implementation is manual export-package generation, private validation, metadata review, and private ZIP retrieval only.
