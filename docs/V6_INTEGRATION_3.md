# V6-INTEGRATION-3 Private Read-Only Import Summary

## Scope

V6-INTEGRATION-3 adds a private CLI/service that verifies an external frozen V6 package and writes a
metadata-only safe import summary to an operator-specified JSON path.

This is not a V6 writer, app route, frontend feature, artifact-serving path, or Earth Engine flow.
It does not extract the ZIP, copy generated payload files, write run artifacts, or expose V6 content
through HTTP.

## Graphify Status

Graphify was used first from `graphify-out/graph.json`. It identified the relevant existing surfaces:

- `app/services/v6_package_validator.py` and `app/cli/v6_package_verify.py` from V6-INTEGRATION-1.
- `app/services/v6_package_contract.py` from V6-INTEGRATION-2.
- `app/pipeline/parity/v6_package.py` as an older parity helper that copies V6 files into a run
  parity tree. V6-INTEGRATION-3 does not use or modify that helper.

`graphify-out/` remains untracked and must not be staged or committed.

## Added Service

Service:

```text
app/services/v6_package_importer.py
```

Primary function:

```text
write_v6_safe_import_summary(
    zip_path=<external_zip>,
    inventory_path=<external_inventory>,
    output_path=<operator_summary_json>,
    reference_doc_path="docs/V6_FROZEN_REFERENCE.md",
)
```

Behavior:

- runs the existing V6-INTEGRATION-1 validator for ZIP SHA256, inventory JSON, member sizes, member
  hashes, payload count, ZIP entry count, and category counts;
- applies the V6-INTEGRATION-2 contract for required payload roles and category mapping;
- reads only CSV header lines;
- checks CSV headers against role-specific required header names;
- reads only enough GeoJSON top-level text to identify `type` and confirm a `features` array;
- writes only approved safe metadata to the requested JSON path.

## Added Private CLI

Command:

```bash
python -m app.cli.v6_package_import --zip <external_zip> --inventory <external_inventory> --out <safe_summary_json>
```

The CLI prints only:

- validation status;
- output path;
- payload count;
- ZIP entry count;
- role/category counts.

It does not print payload hashes, CSV headers, GeoJSON type values, row contents, candidate details,
feature properties, feature coordinates, HTML contents, or summary-text contents.

## Safe Metadata Written

The summary JSON may contain only:

- `contract_version`;
- `generated_at`;
- `validation_status`;
- `package_filename`;
- `inventory_filename`;
- `package_sha256`;
- `package_size_bytes`;
- `payload_count`;
- `zip_entry_count`;
- `category_counts`;
- `role_counts`;
- `payload_files` with file name, role, category, byte size, and SHA256;
- `csv_headers` with header names only;
- `geojson_roles` with role name and top-level `type` only.

The summary JSON intentionally does not persist:

- external source paths;
- CSV row values;
- candidate rows;
- exact coordinate values;
- GeoJSON feature bodies;
- GeoJSON feature properties;
- GeoJSON coordinates;
- HTML map contents;
- text summary contents;
- copied payload artifacts.

## Artifact And Safety Policy

All generated V6 payloads remain `FILESYSTEM_ONLY` and outside Git.

V6-INTEGRATION-3 does not add:

- FastAPI routes;
- frontend controls;
- artifact downloads;
- tile previews;
- run-directory package copies;
- ZIP extraction;
- V6 package generation;
- Earth Engine calls.

The output summary is private operator metadata. It must not be exposed as a public DTO or frontend
artifact without a later redaction review.

## Validation

Synthetic unit tests cover:

- verified summary creation for a complete synthetic package;
- invalid status when a CSV header contract fails;
- CLI stdout staying limited to safe status/count fields.

The real external V6 package may be checked with output outside Git, for example:

```bash
python -m app.cli.v6_package_import \
  --zip C:\Dev\New_GEE_EXTERNAL_V6\V6_FROZEN_REFERENCE_20260612T182318Z.zip \
  --inventory C:\Dev\New_GEE_EXTERNAL_V6\V6_FROZEN_REFERENCE_inventory_20260612T182318Z.json \
  --out C:\Dev\New_GEE_EXTERNAL_V6\V6_SAFE_IMPORT_SUMMARY_20260613.json
```

Do not stage or commit that output.

## Next Step

If V6 needs to move beyond private metadata import, open a separate design task for an internal-only
provenance store and redaction review. Do not add V6 writers, Earth Engine dependencies, API routes,
frontend controls, or artifact serving in that task unless explicitly authorized.
