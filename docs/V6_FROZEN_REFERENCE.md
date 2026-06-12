# V6 Frozen Reference Export

Status: frozen external reference package.

This document records the external V6 export generated from the V6 notebook and frozen outside Git. The V6 export is not part of the tracked application source, not part of `notebooks/new.ipynb` parity scope, and must not be committed as generated artifacts.

## Location

External Google Drive folder:

```text
My Drive / New_GEE_REFERENCE / V6_FROZEN_REFERENCE
```

## Frozen package

Inventory file:

```text
V6_FROZEN_REFERENCE_inventory_20260612T182318Z.json
```

ZIP package:

```text
V6_FROZEN_REFERENCE_20260612T182318Z.zip
```

ZIP SHA256:

```text
cf3732b48b7500c6fd1112316852fa01c2ce7fbb62257610a9d6e07742139a58
```

Frozen file count:

```text
12
```

## Frozen contents

- `lawful_gee_candidate_scout_top_25_20260612T181454Z.csv`
- `lawful_gee_candidate_scout_top_25_20260612T181454Z.geojson`
- `paid_archive_request_summary.txt`
- `paid_imagery_quote_comparison_v6.csv`
- `paid_imagery_quote_template_v6.csv`
- `quality_diagnostics_all_cells_v6.csv`
- `request_zones_v6.csv`
- `request_zones_v6.geojson`
- `stable_candidate_priority_list_v6.csv`
- `top25_enhanced_v6.csv`
- `top25_enhanced_v6.geojson`
- `visual_inspection_map.html`

## Artifact policy

The frozen V6 export package and generated V6 output files must remain outside Git.

Do not commit:

- V6 ZIP packages
- V6 generated CSV files
- V6 generated GeoJSON files
- V6 generated HTML maps
- V6 generated summary TXT files
- V6 notebook export folders
- V6 generated package folders

## Scope

This frozen package is external V6 reference material for `V6-INTAKE-1`.

It does not change the active parity scope for `notebooks/new.ipynb`.

It does not replace the D1C source-locked reference bundle.

## Next task

`V6-INTAKE-1` will inspect this frozen V6 reference package and classify it as one or more of:

1. reference-only material,
2. source-lockable package material,
3. future app-integration candidate,
4. generated artifact bundle that remains outside Git.

## Intake report

See `docs/V6_INTAKE_1.md` for the V6-INTAKE-1 package intake status and project-role
classification.
