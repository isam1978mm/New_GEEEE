# V6-GENERATOR-2 Synthetic Package Generator

## Scope

V6-GENERATOR-2 adds the first app-side V6 package generator slice.

This slice is synthetic-only. It proves the app can create the full V6 package shape, inventory JSON, ZIP, and safe validation report without relying on the V6 notebook runtime, Colab, Google Drive, Earth Engine, or real V6 artifacts.

## Added Files

```text
app/services/v6_generator_package.py
app/cli/v6_package_generate.py
tests/unit/test_v6_generator_package.py
```

## What The Generator Does

The service writes a complete synthetic V6 package into an operator-supplied output directory.

It generates:

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
- final ZIP package;
- safe validation report.

## Private CLI

Command:

```bash
python -m app.cli.v6_package_generate --out <operator_output_dir>
```

Optional:

```bash
python -m app.cli.v6_package_generate --out <operator_output_dir> --timestamp 20260101T120000Z --package-name V6_SYNTHETIC_GENERATED_20260101T120000Z.zip
```

The CLI prints only safe metadata:

- validation status;
- output directory;
- generated ZIP path;
- generated inventory path;
- generated validation report path;
- payload count;
- ZIP entry count;
- category counts;
- issue count.

It does not print candidate rows, coordinates, GeoJSON feature bodies, HTML contents, summary text contents, CSV headers, or provider workflow information.

## Validation Behavior

The synthetic generator validates package shape using the V6 source-lock contract.

It checks:

- required payload filenames;
- timestamped top-25 filename pattern;
- CSV headers;
- GeoJSON top-level structure;
- role/category counts;
- payload count;
- ZIP entry count;
- generated inventory record hashes and sizes.

The generated ZIP can also be validated by the existing read-only V6 package validator when a reference document with the generated ZIP SHA256 is supplied in tests.

## Safety Boundaries

This generator does not:

- run Earth Engine;
- call a provider API;
- submit provider requests;
- use real V6 rows;
- use real V6 coordinates;
- use the external frozen V6 package as input;
- copy or extract real V6 artifacts;
- write into Git by default;
- add frontend controls;
- add public API routes;
- modify notebooks.

Synthetic GeoJSON files use empty `FeatureCollection` shells to prove package structure without introducing real geometry.

## Tests

Test file:

```text
tests/unit/test_v6_generator_package.py
```

Coverage:

- generated package includes every required role;
- generated inventory matches ZIP member sizes and SHA256 values;
- generated ZIP passes the existing V6 package validator with a synthetic reference document;
- generated validation report is safe metadata only;
- CLI writes the package and prints only safe counts/status.

## Relationship To Previous V6 Work

The V6 integration track remains useful as QA:

- V6-INTEGRATION-1 verifier validates package hash/inventory/member counts.
- V6-INTEGRATION-2 contract validates required roles and schemas.
- V6-INTEGRATION-3 safe importer proves metadata-only import.
- V6-GENERATOR-2 starts app-side generation.

This means the app is now moving from external package verification toward independent package generation.

## Next Step

```text
V6-GENERATOR-3: connect the synthetic generator to app-input models and add a private generation CLI path that can later accept app pipeline outputs, while keeping Earth Engine and provider workflow outside unit tests.
```