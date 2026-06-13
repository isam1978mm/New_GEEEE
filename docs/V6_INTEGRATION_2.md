# V6-INTEGRATION-2 Schema and Source-Lock Contract

## Scope

V6-INTEGRATION-2 defines the formal schema/source-lock contract and future app-side import design for
the frozen external V6 package. It does not import, extract, copy, stage, commit, generate, serve, or
preview V6 package artifacts.

Graphify was checked first. `graphify-out/graph.json` was available in this checkout and identified
the current V6 surfaces:

- `app/services/v6_package_validator.py` and `app/cli/v6_package_verify.py`: read-only external
  package verifier added by V6-INTEGRATION-1.
- `app/pipeline/parity/v6_package.py`: older parity helper that copies V6 files into a run parity
  tree. This helper is not the future app-side import design for this task and was not modified.
- `docs/V6_FROZEN_REFERENCE.md`, `docs/V6_INTAKE_1.md`, and `docs/V6_INTEGRATION_1.md`: current
  V6 package documentation.

## External Package Check

The real external package was inspected by stream/read-only commands only. The ZIP was not extracted
to disk, and no CSV rows, feature properties, feature coordinates, map contents, or summary text
contents were printed.

| Item | Value |
| --- | --- |
| ZIP filename | `V6_FROZEN_REFERENCE_20260612T182318Z.zip` |
| ZIP size | `100920` bytes |
| ZIP SHA256 | `cf3732b48b7500c6fd1112316852fa01c2ce7fbb62257610a9d6e07742139a58` |
| Inventory filename | `V6_FROZEN_REFERENCE_inventory_20260612T182318Z.json` |
| Inventory size | `2242` bytes |
| Inventory SHA256 | `8c8d77db9951edd470f1b61c172a9b7cd7ae1ffe2d19e299b162131d1627ca94` |
| ZIP entries | `13` entries including the inventory JSON |
| Payload files | `12` generated V6 payload files excluding the inventory JSON |

## Required Payload Files

The source-locked V6 package requires exactly these payload roles:

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

The timestamped top-25 files must match:

```text
lawful_gee_candidate_scout_top_25_<YYYYMMDDTHHMMSSZ>.csv
lawful_gee_candidate_scout_top_25_<YYYYMMDDTHHMMSSZ>.geojson
```

## Optional Payload Files

No optional generated payload files are source-locked for V6-INTEGRATION-2.

The inventory JSON may appear inside the ZIP, but it is audit metadata, not a generated payload file.
Any other unexpected payload member is an integration-warning at minimum and should be treated as a
contract failure unless a later source-lock task explicitly extends this list.

## Category Mapping

| Category | Payload roles |
| --- | --- |
| `candidate_tables` | Timestamped top-25 CSV/GeoJSON, `top25_enhanced_v6.csv`, `top25_enhanced_v6.geojson`, `stable_candidate_priority_list_v6.csv` |
| `request_zones` | `request_zones_v6.csv`, `request_zones_v6.geojson` |
| `diagnostics` | `quality_diagnostics_all_cells_v6.csv` |
| `quote_templates` | `paid_imagery_quote_template_v6.csv`, `paid_imagery_quote_comparison_v6.csv` |
| `summary_text` | `paid_archive_request_summary.txt` |
| `visual_map` | `visual_inspection_map.html` |
| `unknown` | Any member outside the source-locked required/optional payload contract |

## Payload Identity

These file sizes and SHA256 values are source-lock metadata only. They must not be printed in public
API responses or frontend views.

| File | Size bytes | SHA256 |
| --- | ---: | --- |
| `lawful_gee_candidate_scout_top_25_20260612T181454Z.csv` | `11671` | `f21380386cbef50f9c40dfdfd1a0a4a6f96b88bcd8d8c77dd8a4140389190dc0` |
| `lawful_gee_candidate_scout_top_25_20260612T181454Z.geojson` | `31467` | `c31208d29f08229aa90bb8510c12860d7d44a5fb8e8d2d03407ef563d1ffac35` |
| `paid_archive_request_summary.txt` | `9631` | `f0b88eb96003c9d4b5dde7d1c9b3233cc3af192f6a36ed20ef933d08a59dd8c8` |
| `paid_imagery_quote_comparison_v6.csv` | `737` | `943a6992d024595d2fd716ca37afa7898494e3a56b0c69292da7a4e9b21f9207` |
| `paid_imagery_quote_template_v6.csv` | `564` | `aaa8a6eb2a774a842efe29d46b33f2d287a044fd97b0f57eeaac9b33cf3d1be6` |
| `quality_diagnostics_all_cells_v6.csv` | `64071` | `c2cb9fe053713ef0ea86612757a9bc78fdff68d2c90e7998766ec9cf70b92431` |
| `request_zones_v6.csv` | `1078` | `58fe707a485781c70c1691297b3d877c142d469d1d071339eba249d35023d5c5` |
| `request_zones_v6.geojson` | `6038` | `10229720a065a7fedead3d1c4edec6ae60c32845f51f4c1ce729189748346e36` |
| `stable_candidate_priority_list_v6.csv` | `14835` | `68209d10a76950d157d80ea59400097ca24e2b1972ac125f0bf5fb1fbb6dfe76` |
| `top25_enhanced_v6.csv` | `33542` | `76ed6c6bfcf2185a78bee89f1aba0600dba0237d28a77fa657ffe32430e77168` |
| `top25_enhanced_v6.geojson` | `94480` | `2975a4dce867061e0cc243c6947067747d8f30839571a93a346e62e67bf56fb1` |
| `visual_inspection_map.html` | `73623` | `31d3bfc0a12df0b82d8289f5fbb5db1b08ca972d37a5e650ee3283d82532220a` |

## CSV Header Contract

CSV validation is header-only for this source-lock. Import code must not read or log rows during
schema validation.

### `lawful_gee_candidate_scout_top_25_<timestamp>.csv`

```text
"", bare_soil_proxy, bsi, builtup_frac, builtup_near_frac, candidate_score, cell_id, center_lat,
center_lon, col, cropland_frac, eligible_mask, land_ok, low_vegetation, mndwi, ndvi,
protected_mask, remote_sensing_contrast, row, s2_count, sar_contrast, slope_deg,
spectral_contrast, surface_water, terrain_score, tpi_m, visibility_score, vv_minus_vh,
water_edge_frac, worldcover_mode
```

### `top25_enhanced_v6.csv`

```text
bare_soil_proxy, bsi, builtup_frac, builtup_near_frac, candidate_score, cell_id, center_lat,
center_lon, col, cropland_frac, eligible_mask, land_ok, low_vegetation, mndwi, ndvi,
protected_mask, remote_sensing_contrast, row, s2_count, sar_contrast, slope_deg,
spectral_contrast, surface_water, terrain_score, tpi_m, visibility_score, vv_minus_vh,
water_edge_frac, worldcover_mode, score_rank, score_percentile, score_gap_from_median,
next_candidate_score, score_gap_to_next_rank, s2_confidence_all, visibility_score_rank_pct,
remote_sensing_contrast_rank_pct, terrain_score_rank_pct, component_agreement,
confidence_score_all, builtup_warning, cropland_heavy_warning, water_edge_warning,
modern_linear_edge_warning, false_positive_warning_count, false_positive_penalty,
quality_adjusted_score, s2_confidence, balanced_score, balanced_rank, visibility_heavy_score,
visibility_heavy_rank, contrast_heavy_score, contrast_heavy_rank, terrain_heavy_score,
terrain_heavy_rank, top10_count, top25_count, avg_rank, stability_score,
dry_window_season_score, dry_window_s2_count, dry_window_visibility,
dry_window_spectral_contrast, dry_window_ndvi, dry_window_bsi, dry_window_season_rank,
cool_wet_window_season_score, cool_wet_window_s2_count, cool_wet_window_visibility,
cool_wet_window_spectral_contrast, cool_wet_window_ndvi, cool_wet_window_bsi,
cool_wet_window_season_rank, season_top10_count, season_top25_count, season_avg_rank,
season_score_mean, season_score_std, stability_score_norm, season_stability_norm,
review_priority_score, v6_dw_built_prob, v6_dw_built_frac, v6_strong_built_frac,
v6_building_near_frac, v6_road_like_edge_frac, v6_modern_corridor_frac, v6_building_warning,
v6_road_like_warning, v6_false_positive_warning_count, v6_false_positive_penalty,
v6_quality_adjusted_score, v6_no_warning_bonus, v6_review_priority_score,
final_priority_rank_v6
```

### `quality_diagnostics_all_cells_v6.csv`

```text
bare_soil_proxy, bsi, builtup_frac, builtup_near_frac, candidate_score, cell_id, center_lat,
center_lon, col, cropland_frac, eligible_mask, land_ok, low_vegetation, mndwi, ndvi,
protected_mask, remote_sensing_contrast, row, s2_count, sar_contrast, slope_deg,
spectral_contrast, surface_water, terrain_score, tpi_m, visibility_score, vv_minus_vh,
water_edge_frac, worldcover_mode, score_rank, score_percentile, score_gap_from_median,
next_candidate_score, score_gap_to_next_rank, s2_confidence_all, visibility_score_rank_pct,
remote_sensing_contrast_rank_pct, terrain_score_rank_pct, component_agreement,
confidence_score_all, builtup_warning, cropland_heavy_warning, water_edge_warning,
modern_linear_edge_warning, false_positive_warning_count, false_positive_penalty,
quality_adjusted_score, s2_confidence, balanced_score, balanced_rank, visibility_heavy_score,
visibility_heavy_rank, contrast_heavy_score, contrast_heavy_rank, terrain_heavy_score,
terrain_heavy_rank, top10_count, top25_count, avg_rank, stability_score,
dry_window_season_score, dry_window_s2_count, dry_window_visibility,
dry_window_spectral_contrast, dry_window_ndvi, dry_window_bsi, dry_window_season_rank,
cool_wet_window_season_score, cool_wet_window_s2_count, cool_wet_window_visibility,
cool_wet_window_spectral_contrast, cool_wet_window_ndvi, cool_wet_window_bsi,
cool_wet_window_season_rank, season_top10_count, season_top25_count, season_avg_rank,
season_score_mean, season_score_std, stability_score_norm, season_stability_norm,
review_priority_score, v6_dw_built_prob, v6_dw_built_frac, v6_strong_built_frac,
v6_building_near_frac, v6_road_like_edge_frac, v6_modern_corridor_frac, v6_building_warning,
v6_road_like_warning, v6_false_positive_warning_count, v6_false_positive_penalty,
v6_quality_adjusted_score, v6_no_warning_bonus, v6_review_priority_score
```

### `stable_candidate_priority_list_v6.csv`

```text
cell_id, center_lon, center_lat, candidate_score, v6_quality_adjusted_score,
v6_review_priority_score, confidence_score_all, stability_score, top10_count, top25_count,
avg_rank, season_top10_count, season_top25_count, season_avg_rank, season_score_mean,
season_score_std, score_gap_from_median, score_gap_to_next_rank, balanced_rank,
visibility_heavy_rank, contrast_heavy_rank, terrain_heavy_rank, visibility_score,
remote_sensing_contrast, terrain_score, s2_count, builtup_frac, builtup_near_frac,
cropland_frac, water_edge_frac, v6_dw_built_prob, v6_dw_built_frac, v6_strong_built_frac,
v6_building_near_frac, v6_road_like_edge_frac, v6_modern_corridor_frac, builtup_warning,
v6_building_warning, v6_road_like_warning, cropland_heavy_warning, water_edge_warning,
modern_linear_edge_warning, false_positive_warning_count, v6_false_positive_warning_count,
worldcover_mode, dry_window_season_score, cool_wet_window_season_score,
dry_window_season_rank, cool_wet_window_season_rank
```

### `request_zones_v6.csv`

```text
request_zone_id, primary_cell_id, candidate_ids, candidate_count, max_v6_review_priority_score,
mean_v6_review_priority_score, max_v6_false_positive_warning_count, west, south, east, north,
buffer_m, cluster_distance_m
```

### `paid_imagery_quote_template_v6.csv`

```text
quote_id, provider, request_zone_id, primary_cell_id, candidate_ids, archive_or_tasking,
acquisition_date, resolution_m, cloud_cover_pct, off_nadir_deg, price, currency, license_ok,
metadata_complete, covers_requested_zone, notes
```

### `paid_imagery_quote_comparison_v6.csv`

```text
quote_id, provider, request_zone_id, primary_cell_id, candidate_ids, archive_or_tasking,
acquisition_date, resolution_m, cloud_cover_pct, off_nadir_deg, price, currency, license_ok,
metadata_complete, covers_requested_zone, notes, resolution_score, cloud_score,
off_nadir_score, price_score, license_score, metadata_score, coverage_score, quote_score,
quote_decision
```

## GeoJSON Role Contract

GeoJSON validation is top-level only for this source-lock. Import code may verify that each file is a
JSON object with `type: FeatureCollection` and a `features` array. It must not log or persist feature
coordinate values or feature property values.

| File | Role | Observed top-level keys | Observed feature count |
| --- | --- | --- | ---: |
| `lawful_gee_candidate_scout_top_25_<timestamp>.geojson` | Timestamped top-25 candidate collection | `crs`, `features`, `name`, `type` | `25` |
| `top25_enhanced_v6.geojson` | Enhanced top-25 candidate collection | `crs`, `features`, `name`, `type` | `25` |
| `request_zones_v6.geojson` | Request-zone collection | `features`, `type` | `5` |

## Artifact Policy

Every V6 generated package output is `FILESYSTEM_ONLY`.

- Keep the real V6 ZIP, inventory JSON, CSV, GeoJSON, HTML, TXT files, generated folders, and V6
  notebook outside Git.
- Do not add V6 package files to `data/runs/` as part of this source-lock.
- Do not serve, list, preview, tile, or download V6 package outputs through HTTP.
- Do not add V6 package files to frontend controls.
- Do not call Earth Engine for V6 import.
- Do not run V6 automatically after the core pipeline.

## Safety Policy

V6 package files are generated external artifacts and include coordinate-bearing members. The safe
inspection boundary is:

- allowed: ZIP filename, inventory filename, file names, byte sizes, SHA256 values, CSV headers, and
  GeoJSON top-level structure;
- forbidden: CSV row contents, candidate details, exact coordinate values, feature properties,
  feature coordinates, GeoJSON feature bodies, HTML map contents, text-summary contents, filesystem
  paths in public DTOs, and any API/frontend exposure.

Any future private logging must report only aggregate status, issue counts, payload counts, and
category counts. Public JSON responses must continue to pass the redaction contract.

## Source-Lock Identity Fields

The formal source-lock identity is the tuple of:

- contract version: `v6_external_package_contract_v1`;
- ZIP filename, ZIP byte size, and ZIP SHA256;
- inventory filename, inventory byte size, and inventory SHA256;
- payload count and ZIP entry count including the inventory;
- payload file names, byte sizes, and SHA256 values;
- CSV header sets;
- GeoJSON top-level roles;
- category counts.

These fields identify the frozen package for private verification. They are not a public DTO schema.

## App-Side Import Design

Future app-side V6 import remains read-only.

1. The operator supplies the external ZIP path and external inventory path at runtime. The app does
   not discover, download, or assume a default external package location.
2. The import path runs the existing read-only verifier first: ZIP hash, inventory JSON, top-level
   member names, sizes, hashes, and category counts by streaming ZIP members without extraction.
3. The import path applies the V6-INTEGRATION-2 contract: required payload names, no optional
   payloads unless later approved, CSV header-only validation, and GeoJSON top-level validation.
4. The app stores only safe summary metadata by default: contract version, verification status,
   issue counts, payload count, category counts, ZIP entry count, and package/inventory basenames if
   needed for operator display. It does not store external filesystem paths, CSV rows, feature
   values, feature coordinates, HTML contents, text-summary contents, or generated artifact copies.
5. Per-file hashes and full header sets remain private source-lock evidence. Persisting them in a
   database table would require a later internal-only provenance design and redaction review.
6. The import result is never a public artifact list, download endpoint, tile endpoint, or frontend
   preview.

This design supersedes using `app/pipeline/parity/v6_package.py` as an app import path. That older
helper copies package files into a run parity tree and can rebuild a ZIP; those behaviors are outside
the V6-INTEGRATION-2 app-side import design.

## Current Implementation

Added `app/services/v6_package_contract.py` as a lightweight contract module. It contains:

- required fixed payload file definitions;
- required timestamped top-25 filename patterns;
- category mapping;
- source-lock identity field names;
- safe payload-name validation;
- CSV header-only validation for caller-supplied contracts;
- GeoJSON top-level summarization that does not inspect feature bodies.

The module intentionally does not embed the real package's full CSV header lists. Those are recorded
in this private source-lock report.

## Next Step

If V6 import becomes an app feature, add a private read-only import command or service that composes
`validate_v6_package()` with `v6_package_contract` checks and persists only the safe summary metadata
defined above. Do not add writers, Earth Engine calls, API artifact exposure, frontend controls, or
generated package files.
