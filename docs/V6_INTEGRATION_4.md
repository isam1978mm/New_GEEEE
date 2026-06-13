# V6-INTEGRATION-4 Internal Provenance Storage Design

## Scope

V6-INTEGRATION-4 defines the internal-only provenance storage contract for the safe V6 summary
envelope produced by V6-INTEGRATION-3.

This task is docs-only. It does not add database writes, migrations, API routes, frontend controls,
artifact serving, V6 writers, Earth Engine calls, notebook changes, or generated V6 package files.

## Graphify Result

Graphify was used first from `graphify-out/graph.json`. It confirmed the relevant current surfaces:

- `app/services/v6_package_validator.py` and `app/cli/v6_package_verify.py` verify the external
  frozen V6 package without extraction.
- `app/services/v6_package_contract.py` defines V6 source-lock and schema helper checks.
- `app/services/v6_package_importer.py` and `app/cli/v6_package_import.py` write the private safe
  summary envelope.
- Existing redaction and storage services exist, but there is no minimal V6-specific internal model
  pattern that should be extended in this docs-first slice.

`graphify-out/` remains local tool output and must not be staged or committed.

## Purpose

The internal provenance store, if implemented later, records that an operator verified a specific
external V6 package and preserved a metadata-only audit envelope. Its purpose is:

- private reproducibility evidence for the V6 source-lock package;
- local auditability of package verification status;
- support for operator troubleshooting when a V6 package no longer matches the frozen contract;
- a future handoff point for internal-only provenance views after a redaction review.

It is not a user-facing artifact, not an API response schema, not a frontend data source, and not a
copy of generated V6 outputs.

## Storage Decision

Do not persist real V6 payload artifacts in the app database or run directory.

Future implementation may persist only the safe summary envelope from V6-INTEGRATION-3, either:

1. as one internal JSON column on a dedicated private provenance table; or
2. as an internal metadata JSON file under a private operator-selected location outside Git.

If a database table is added later, it should be internal-only and should not be joined into public
run DTOs, artifact DTOs, run history DTOs, or frontend payloads.

Recommended table shape for a later task:

```text
v6_package_provenance
  id
  created_at
  operator_label nullable
  validation_status
  safe_summary_json
```

The table must not contain a source path column by default. If an operator-private path is later
approved, it must be stored in a separate encrypted or access-controlled internal field, excluded
from public DTOs and logs, and covered by explicit tests.

## Allowed Safe Metadata

The internal provenance store may persist only:

- contract version;
- generated timestamp;
- validation status;
- package filename;
- inventory filename;
- package SHA256;
- package size;
- payload count;
- ZIP entry count;
- category counts;
- role counts;
- payload filenames;
- payload sizes;
- payload SHA256 values;
- CSV header names only;
- GeoJSON role names and top-level type only.

No other field is allowed without a new source-lock and redaction review.

## Forbidden Persisted Data

The internal provenance store must not persist:

- external full source paths unless explicitly operator-private in a later approved design;
- CSV row values;
- candidate rows;
- coordinates;
- geometries;
- GeoJSON feature bodies;
- GeoJSON feature properties;
- GeoJSON coordinate arrays;
- HTML map contents;
- paid archive summary text contents;
- copied payload artifacts;
- extracted ZIP members;
- generated package folders;
- V6 notebook contents;
- API URLs or frontend references for V6 package outputs.

The forbidden list applies to database rows, JSON files, logs, tests, fixtures, CLI stdout, API
responses, frontend state, and documentation examples.

## Retention Policy

V6 provenance metadata is private operator audit metadata.

- Default retention: keep the latest verified safe summary only unless the operator explicitly
  chooses to retain history.
- If history is retained, keep immutable append-only records with generated timestamp and validation
  status, but still no payload bodies or source paths.
- Deletion must remove the safe summary metadata without touching the external package; the app does
  not own the external package files.
- Backups must follow the same private-data handling as SQLite and other local app data under
  `./data/`.
- The external ZIP, inventory, generated CSV/GeoJSON/HTML/TXT outputs, and V6 notebook remain outside
  Git regardless of provenance metadata retention.

## Operator-Supplied Path Policy

The V6 package path and inventory path are operator-supplied runtime inputs.

Allowed behavior:

- accept paths from a private CLI or future private internal service;
- use paths transiently to stream the ZIP and read the inventory;
- print the CLI output path only for the operator's requested safe summary destination;
- store package and inventory basenames in the safe summary.

Forbidden behavior:

- discover default V6 package paths;
- scan operator directories for V6 files;
- persist full external source paths by default;
- expose source paths in API responses, frontend state, logs, docs examples, or test fixtures;
- copy source files into the repository or run directory.

If full source path retention is ever required, it must be explicitly operator-private, disabled by
default, excluded from all public DTOs, and covered by redaction/logging tests before implementation.

## Redaction Review Gates

Before any future implementation stores or exposes V6 provenance, the task must pass these gates:

1. **Schema gate:** prove every persisted key is in the allowed safe metadata list.
2. **Value gate:** prove no stored value contains coordinate-like pairs, geometry literals, GeoJSON
   feature bodies, HTML contents, text-summary contents, external source paths, or candidate rows.
3. **DTO gate:** prove V6 provenance is absent from public run DTOs, artifact DTOs, error responses,
   run history, OpenAPI output, and frontend API payloads.
4. **Logging gate:** prove INFO-and-above logs do not include source paths, hashes beyond approved
   internal metadata, CSV headers if not intentionally private, row values, coordinates, or GeoJSON
   content.
5. **Artifact gate:** prove no V6 payload is registered as an artifact, served through
   `serve_artifact_response()`, listed, previewed, tiled, or downloadable.
6. **Test fixture gate:** prove tests use synthetic fixtures only and do not include real V6 rows,
   coordinates, GeoJSON contents, HTML map contents, or external package files.
7. **Migration gate:** prove any database migration is SQLite-compatible and does not add
   PostgreSQL-only or advanced SQLite-only behavior.
8. **Access gate:** prove any internal view is operator-only and unavailable through public API or
   frontend paths.

## Future API And Frontend Exposure Blockers

Public API or frontend exposure remains blocked until a separate approved task defines:

- a business need for showing V6 provenance;
- a public DTO that omits hashes, paths, coordinates, geometry, candidate rows, and raw headers if
  required by the redaction contract;
- tests proving every response passes `verify_redacted()`;
- operator-only authorization behavior if any private view is added;
- a decision on whether package SHA256 and payload SHA256 values remain internal-only.

Until those conditions are met, V6 provenance must stay private CLI/internal metadata only.

## Acceptance Checklist For Future Implementation

A later implementation can be accepted only if all items below are true:

- [ ] No V6 ZIP, CSV, GeoJSON, HTML, TXT, generated folder, inventory JSON, or V6 notebook is added
      to Git.
- [ ] No ZIP extraction or payload copying occurs.
- [ ] No Earth Engine call is added.
- [ ] No public API route or frontend control is added.
- [ ] Only the allowed safe metadata fields are persisted.
- [ ] Full external source paths are not persisted unless separately approved as operator-private.
- [ ] CSV validation reads headers only.
- [ ] GeoJSON validation reads top-level type/role only and does not persist feature bodies,
      properties, or coordinates.
- [ ] HTML and text-summary files are never read into stored provenance.
- [ ] Stored metadata is not registered as a public artifact.
- [ ] Public DTO and log redaction tests cover the new storage path.
- [ ] Tests use synthetic packages only.
- [ ] `tests/unit/test_v6_package_importer.py`, `tests/unit/test_v6_package_contract.py`,
      `tests/unit/test_v6_package_validator.py`, and notebook-safety tests pass.

## Next Step

If durable storage is needed, open a small implementation task for an internal-only provenance schema
or JSON-store helper using the allowed metadata list above. That task should add focused synthetic
tests and must not add API/frontend exposure.
