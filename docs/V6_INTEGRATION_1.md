# V6-INTEGRATION-1 Read-Only Package Contract

## Scope

V6-INTEGRATION-1 adds a read-only local validator for the external frozen V6 package. The validator
does not import package files into a run directory, does not extract the ZIP, does not copy generated
artifacts into Git, and does not change the active `notebooks/new.ipynb` parity baseline.

Graphify was queried first, but `graphify-out/graph.json` was unavailable in this checkout. The
implementation followed the tracked V6 reference docs, notebook safety policy, reference-bundle
validator patterns, and existing local CLI style.

## Behavior

The validator:

- reads the expected ZIP SHA256 from `docs/V6_FROZEN_REFERENCE.md`;
- verifies the external ZIP hash;
- verifies that the external inventory JSON exists and parses;
- streams ZIP members without extraction;
- compares ZIP payload filenames, byte sizes, and SHA256 values against inventory records;
- excludes the inventory JSON itself from payload counts when it is present inside the ZIP;
- reports high-level category counts only.

The local CLI is:

```bash
python -m app.cli.v6_package_verify --zip <external_zip> --inventory <external_inventory>
```

The CLI prints a safe JSON summary and exits nonzero if package validation is not verified.

## Safe Summary Contract

Default output includes:

- package path;
- hash status;
- inventory status;
- payload count;
- category counts;
- artifact policy;
- integration status;
- issue counts.

Default output does not include row contents, coordinate values, geometries, candidate details, map
contents, per-file hashes, or package member contents.

## Category Contract

Package entries are classified into these high-level categories:

| Category | Meaning |
| --- | --- |
| `candidate_tables` | Candidate/ranking table or candidate GeoJSON package members. |
| `request_zones` | Request-zone CSV or GeoJSON package members. |
| `diagnostics` | Quality diagnostics package members. |
| `quote_templates` | Quote template or quote comparison package members. |
| `summary_text` | Plain-text package summary. |
| `visual_map` | Local visual inspection map. |
| `unknown` | Any package member outside the current known V6 filename contract. |

## Artifact Policy

The V6 frozen package remains an external generated artifact bundle.

- Do not commit the ZIP, inventory JSON, CSV, GeoJSON, HTML, TXT package outputs, generated folders,
  or the V6 notebook.
- Do not add the V6 notebook to `notebooks/`.
- Do not serve V6 package outputs through the API or frontend.
- Do not treat V6 package verification as `notebooks/new.ipynb` parity evidence.

## Integration Status

This layer is ready as a read-only external package verifier.

It does not close V6 app integration. Future V6 work still needs a separate source-lock task to define
schemas, source contract, acceptance criteria, and any app writer/import behavior.

## Next Step

Open a dedicated V6 source-lock and integration-design task. That task should use the verified frozen
package as external evidence without moving generated artifacts or the V6 notebook into the repo.
