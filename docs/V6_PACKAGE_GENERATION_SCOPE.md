# V6 Paid-Archive Package — Wishlist (Deferred)

## Status

**WISHLIST / DEFERRED.** V6 paid-archive packaging is not on the near-term path.

This document supersedes the earlier V6 generation-scope wording that treated V6 as a critical next implementation slice. That earlier status was written before provenance was checked. The repo's only in-scope notebook is `notebooks/new.ipynb`, and V6 paid-archive outputs have not been verified as outputs of that notebook.

V6 remains blocked at the source until the operator supplies the separate originating V6 notebook or a real frozen V6 package that proves the workflow exists outside this repo.

## What It Is

V6 is a downstream procurement / packaging layer. It is not the core screening pipeline.

Conceptually, it turns screening candidates into a paid-imagery request workflow:

1. Rank candidates.
2. Cluster candidates into request zones.
3. Generate commercial satellite-imagery quote rows for those zones.
4. Bundle the results into a paid-archive request package.
5. Optionally include a visual inspection map.

Expected component outputs, if the workflow is ever revived:

- `lawful_gee_candidate_scout_top_25_<timestamp>.csv` / `.geojson`
- `top25_enhanced_v6.csv` / `.geojson`
- `stable_candidate_priority_list_v6.csv`
- `quality_diagnostics_all_cells_v6.csv`
- `request_zones_v6.csv` / `.geojson`
- `paid_imagery_quote_template_v6.csv`
- `paid_imagery_quote_comparison_v6.csv`
- `paid_archive_request_summary.txt`
- `visual_inspection_map.html`

The rebuilt package ZIP, if revived later, would be:

- `paid_archive_request_candidate_package_FINAL_v6_ZONES_QUOTES.zip`

So the deferred target is 12 component files plus one rebuilt ZIP/package artifact.

All V6 outputs remain coordinate-bearing parity artifacts. They must stay `FILESYSTEM_ONLY`, `http_servable=false`, and out of public API/frontend exposure.

## Why It Is Deferred

1. **Not essential to the app.** The app's near-term purpose is screening: acquire inputs, process SAR/DEM/hypercube/PCA, extract candidate objects, run neutral classifier/diagnostics, and export safely. V6 only adds paid-imagery ordering.

2. **Provenance gap.** V6 filenames appear in app contracts/docs/tests and gap inventories, but the source notebook that actually emits them is not in this repo.

3. **`notebooks/new.ipynb` does not do it.** The in-repo notebook produces upstream screening/candidate material, not V6 request zones, quote rows, paid-archive package files, or `visual_inspection_map.html` as a V6 package artifact.

## Hard Blocker Before Any V6 Work

The separate V6 candidate-scout / paid-archive notebook must be located and supplied before any V6 implementation, freezing, or formula-locking work can start.

That external source must prove the workflow that emits the component files above and the ranking fields previously referenced in the gap notes, such as:

- `candidate_score`
- `review_priority_score`
- `season_*`
- `balanced_rank`
- `false_positive_warning_count`

Without that source notebook or a real frozen output package, V6 cannot be frozen, source-locked, generated, or value-verified.

## Revive Later — Gated Order

Nothing past W1 can start until the originating notebook or real package exists.

- **W1 — Operator supplies source.** Locate and provide the real V6 notebook/package source. Confirm it produces all 12 component files plus the rebuilt package ZIP.
- **W2 — V6-G0 / B1.** Freeze that notebook's V6 package outside Git.
- **W3 — V6-G1 / B2.** Source-lock ranking, zone-clustering, and quote formulas from the supplied notebook.
- **W4 — V6-G2+.** Only after W1-W3, consider generation of candidates, zones, quotes, summary, map, and package.

Safety gates if revived:

- all V6 outputs `FILESYSTEM_ONLY`
- `http_servable=false`
- no public exposure
- no exact coordinate leakage in API/frontend/logs
- score/probability wording only

## Relationship to the Near-Term Plan

Near-term work stays focused on `notebooks/new.ipynb` parity and the app's real screening value:

- SAR / DEM / feature stack processing
- hypercube and PCA/anomaly outputs
- object/candidate extraction
- neutral classifier workflow
- local diagnostics and safe exports
- public/private artifact safety boundaries

V6 is optional downstream procurement packaging. Revisit it only if paid-imagery ordering becomes a real requirement and the originating V6 notebook/package is supplied.

## Existing App Import Code

`app/pipeline/parity/v6_package.py` is retained as-is. It imports, validates, and rebuilds a V6 package if one is supplied. It does not prove that `notebooks/new.ipynb` generates such a package, and it does not implement V6 generation.

Do not delete or expand that code in this documentation correction.

## Decision Record

- **2026-06-09:** Reclassified V6 from critical implementation track to wishlist/deferred after provenance review. `notebooks/new.ipynb` is the only in-repo notebook and has not been verified to produce V6 paid-archive package outputs. B1/V6-G0 and B2/V6-G1 must not be run from `notebooks/new.ipynb` because there is no V6 package source to freeze or source-lock there.

(End of V6_PACKAGE_GENERATION_SCOPE.md.)
