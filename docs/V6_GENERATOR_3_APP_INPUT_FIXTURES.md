# V6-GENERATOR-3 App Input Fixture Connection

## Scope

V6-GENERATOR-3 connects the synthetic V6 package generator to explicit app-input fixture models.

This is still not the real Earth Engine generation path. It is the next bridge between pure synthetic generation and future app pipeline output generation.

## Added And Updated Files

```text
app/services/v6_generator_inputs.py
app/services/v6_generator_package.py
app/cli/v6_package_generate.py
tests/unit/test_v6_generator_package.py
```

## What Changed

### Input Models

A new input module defines safe app-side fixture models:

```text
V6GenerationInput
V6InputCandidate
V6InputRequestZone
```

The input model currently accepts:

- run ID;
- timestamp;
- candidate IDs;
- candidate scores;
- V6 review priority scores;
- request-zone IDs;
- primary candidate references;
- quote IDs;
- quote scores.

The input model rejects geometry-like keys and does not accept raw GeoJSON feature bodies.

### Generator Service

The package generator now has two entry points:

```text
generate_synthetic_v6_package(...)
generate_v6_package_from_input(...)
```

The first keeps the default synthetic path.

The second generates the same complete V6 package shape from a safe app-input fixture.

### CLI

The private CLI now supports two modes:

```bash
python -m app.cli.v6_package_generate --out <operator_output_dir>
```

and:

```bash
python -m app.cli.v6_package_generate --out <operator_output_dir> --input-json <app_input_fixture.json>
```

The CLI still prints only safe package metadata.

## What This Does Not Do

V6-GENERATOR-3 does not:

- run Earth Engine;
- use the V6 notebook runtime;
- use Google Drive paths;
- use real V6 rows;
- use real request geometry;
- read the external frozen V6 package;
- call providers;
- submit provider requests;
- add frontend or public API exposure;
- store generated package files in Git by default.

## Test Coverage

Updated tests cover:

- default synthetic package generation;
- inventory hash and size matching;
- existing V6 package validator compatibility;
- safe validation report contents;
- CLI default synthetic generation;
- app-input JSON fixture loading;
- package generation from app-input fixture;
- CLI generation from app-input fixture with safe printed output.

## Why This Step Matters

V6-GENERATOR-2 proved the app can generate the full package shape with fixed synthetic data.

V6-GENERATOR-3 proves the generator can accept explicit app-shaped input data and produce the same package roles.

That prepares the next task: connecting the generator to real app pipeline output adapters while keeping Earth Engine and sensitive geometry behind a controlled runtime boundary.

## Next Step

```text
V6-GENERATOR-4: add app-output adapter validation and failure-mode tests so generated packages fail clearly when required roles, headers, inventory hashes, or top-level GeoJSON structure are wrong.
```