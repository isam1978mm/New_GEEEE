# V6 Package Parity Contract

## Purpose

Phase 2 implements the first working notebook-parity layer for the v6 paid-archive package outputs. The goal is package/file/schema parity: validate, import, summarize, hash, and rebuild the notebook package files while preserving original filenames in the run-local parity tree.

This phase does not change raster math, SAR math, Sentinel-2 formulas, DEM formulas, PCA logic, object extraction logic, classifier logic, API routes, frontend behavior, database models, migrations, artifact serving policy, existing output names, or existing pipeline stage formulas.

## Required Package Files

The import layer supports these component files:

```text
lawful_gee_candidate_scout_top_25_<timestamp>.csv
lawful_gee_candidate_scout_top_25_<timestamp>.geojson
top25_enhanced_v6.csv
top25_enhanced_v6.geojson
quality_diagnostics_all_cells_v6.csv
stable_candidate_priority_list_v6.csv
request_zones_v6.csv
request_zones_v6.geojson
paid_imagery_quote_template_v6.csv
paid_imagery_quote_comparison_v6.csv
paid_archive_request_summary.txt
visual_inspection_map.html
```

The rebuilt/export zip is written as:

```text
paid_archive_request_candidate_package_FINAL_v6_ZONES_QUOTES.zip
```

The zip is treated as an export artifact produced from the imported component files. A source package may itself be a zip, but the required import members are the component files above.

## Timestamped Filename Handling

The lawful top-25 outputs are matched by filename pattern:

```text
lawful_gee_candidate_scout_top_25_*.csv
lawful_gee_candidate_scout_top_25_*.geojson
```

At least one CSV and one GeoJSON matching those patterns must be present. Imported filenames are preserved exactly in the parity tree and rebuilt zip.

## Minimal CSV Schema Validation

Schema checks are intentionally conservative. If the exact notebook schema is uncertain, Phase 2 requires only minimum columns needed to identify the file type and keep later parity work honest.

| File | Minimum required columns |
| --- | --- |
| `lawful_gee_candidate_scout_top_25_*.csv` | one of `candidate_id`, `object_id`, `id` |
| `top25_enhanced_v6.csv` | one of `candidate_id`, `object_id`, `id`; and one of `candidate_score`, `review_priority_score` |
| `stable_candidate_priority_list_v6.csv` | one of `candidate_id`, `object_id`, `id`; and one of `review_priority_score`, `candidate_score` |
| `quality_diagnostics_all_cells_v6.csv` | one of `cell_id`, `candidate_id`, `object_id`, `id` |
| `request_zones_v6.csv` | `zone_id` |
| `paid_imagery_quote_template_v6.csv` | `zone_id` |
| `paid_imagery_quote_comparison_v6.csv` | `zone_id` |

Unknown full notebook schemas remain a limitation of Phase 2. Later parity phases may tighten these checks against a frozen notebook reference package.

## GeoJSON Validation

GeoJSON files must parse as JSON and must have a `FeatureCollection` shape with a `features` array:

```text
lawful_gee_candidate_scout_top_25_*.geojson
top25_enhanced_v6.geojson
request_zones_v6.geojson
```

These files are treated as coordinate-bearing parity artifacts.

## Output Layout

Imported package files are copied under a run directory:

```text
data/runs/<run_id>/
  parity/
    root/
      lawful_gee_candidate_scout_top_25_<timestamp>.csv
      lawful_gee_candidate_scout_top_25_<timestamp>.geojson
      top25_enhanced_v6.csv
      top25_enhanced_v6.geojson
      quality_diagnostics_all_cells_v6.csv
      stable_candidate_priority_list_v6.csv
      request_zones_v6.csv
      request_zones_v6.geojson
      paid_imagery_quote_template_v6.csv
      paid_imagery_quote_comparison_v6.csv
      paid_archive_request_summary.txt
      paid_archive_request_candidate_package_FINAL_v6_ZONES_QUOTES.zip
    maps/
      visual_inspection_map.html
  manifests/
    parity_manifest.json
    v6_package_import_manifest.json
```

All imported paths must stay under the run directory. Path traversal in zip entries is blocked.

## Manifest Outputs

`v6_package_import_manifest.json` contains:

| Field | Meaning |
| --- | --- |
| `schema_version` | Current value: `v6_package_import_manifest_v1`. |
| `run_id` | Run identifier supplied by the caller. |
| `imported_at` | ISO-8601 import timestamp. |
| `source_type` | `directory` or `zip`. |
| `source_path` | Source package path used for private provenance. |
| `package_files` | Array of imported file records. |
| `file_name` | Original notebook filename. |
| `parity_path` | Run-relative parity output path. |
| `sha256` | SHA256 hash of the imported file bytes. |
| `size_bytes` | Imported file size. |
| `family` | Phase 0 output family. |
| `validation_status` | Per-file validation status. |
| `missing_required_files` | Empty when import succeeds. |
| `warnings` | Non-fatal import notes. |
| `rebuilt_zip_path` | Run-relative rebuilt zip path when requested. |
| `rebuilt_zip_sha256` | SHA256 hash of the rebuilt zip when requested. |

The Phase 1 `parity_manifest.json` receives one entry per imported file and one entry for the rebuilt zip when rebuild/export is requested. Entries preserve original notebook names and default to no HTTP serving.

## Import Directory Flow

1. Read top-level files from the source directory.
2. Validate fixed required filenames and timestamped top-25 patterns.
3. Validate minimum CSV columns.
4. Validate GeoJSON JSON/FeatureCollection shape.
5. Copy files into `parity/root/` or `parity/maps/`.
6. Compute SHA256 and byte-size records.
7. Write `v6_package_import_manifest.json`.
8. Write the Phase 1 parity manifest.

## Import Zip Flow

1. Read top-level zip members.
2. Reject absolute, nested, duplicate, or traversal member paths.
3. Apply the same required-file, CSV, and GeoJSON validations.
4. Copy member bytes into the parity tree with original filenames preserved.
5. Write the same import and parity manifests as the directory flow.

## Rebuild And Export Flow

When rebuild/export is requested, the helper writes:

```text
parity/root/paid_archive_request_candidate_package_FINAL_v6_ZONES_QUOTES.zip
```

The rebuilt zip contains the imported component files with original member filenames preserved. It does not run Earth Engine, generate new candidate rankings, interpret claims, or modify source math.

## Relationship To Phase 1 Parity Manifest

The v6 package helper uses the Phase 1 parity helper to:

- resolve run-local parity paths;
- create standard parity directories;
- block traversal outside the run directory;
- write `parity_manifest.json`;
- mark notebook names, families, modes, artifact classes, coordinate-bearing status, and verification flags.

Coordinate-bearing GeoJSON and `visual_inspection_map.html` entries are marked `requires_coordinates=true`, `artifact_class=FILESYSTEM_ONLY`, `target_mode=notebook_parity`, and `http_servable=false`.

No entry defaults to `public_shared`.

## Phase 2 Non-Goals

Phase 2 does not:

- change raster math, SAR math, Sentinel-2 formulas, DEM formulas, PCA logic, object extraction logic, or classifier logic;
- run Earth Engine;
- change API routes, frontend files, database models, migrations, artifact serving policy, or existing output names;
- add public/shared exposure for v6 package files;
- decide which parity outputs belong in the clean app UI;
- implement classifier/model logic.

The probability-only classifier wording rule remains in `docs/PARITY_MODE_CONTRACT.md`; Phase 2 does not implement classifier outputs.
