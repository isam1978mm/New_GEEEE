# Parity Scope

## Validated Production-Core Scope

The accepted notebook-grid validation baseline has no F11 FAIL rows. It validates notebook-equivalent production-core output parity for the frozen reference run when the app and notebook use the same authoritative GRID.

Validated production-core scope includes:

- GRID-locked DEM outputs and notebook-matched DEM derivatives
- SAR GeoTIFF and NPY outputs
- radar DB stack outputs
- selected DEM derivative outputs exposed by the current notebook reference set
- focus mask output
- other core rasters and arrays covered by F11/F24/F13 reports

This is an output/math parity statement for the accepted reference workflow. It is not a claim of fresh-ROI notebook parity, archaeological validity, or generalization beyond the accepted notebook-equivalent production-core workflow.

## Experimental Notebook Tail Exclusions

The experimental notebook tail is excluded from production-core parity. That includes notebook-only, Drive/Colab-specific, UI-specific, exploratory, classifier, and source-notebook-label workflows that are not part of the v1 defensible core pipeline.

Experimental classifier logic remains CLI-only, neutralized, and `FILESYSTEM_ONLY` under the separate experimental module rules. It is not part of public API behavior, production-core parity, or automatic pipeline execution.

## GRID Decision

GRID provenance is Option B:

- production `/runs` remain app-authoritative
- notebook-exact GRID remains local validation/replay-only scaffolding
- the app matches notebook-equivalent production-core outputs only when the authoritative GRID is identical
- the accepted notebook-grid validation baseline proves parity under the notebook-exact validation GRID, not under arbitrary fresh production ROIs

Production GRID behavior, notebook-exact GRID override behavior, and public API redaction behavior are unchanged by this scope document.

## SKIP_MISSING_NOTEBOOK

`SKIP_MISSING_NOTEBOOK` means the app artifact exists but the frozen notebook reference set does not currently expose a matching notebook artifact for that row.

It is not a numeric parity failure. It also is not a pass for notebook parity. It means the row is outside the current notebook-matched reference contract until a matching notebook reference artifact is added and recorded in the frozen reference manifest.

App-only outputs are therefore not parity failures merely because the current notebook reference set lacks matching files.

## DEM Derivative Contract

Current required H1 notebook-matched DEM derivative parity is limited to:

- `slope.tif`
- `aspect.tif`
- `TPI.tif`
- `roughness.tif`

The following app outputs are not notebook-matched in the current frozen reference set:

- `curvature.tif`
- `TRI.tif`
- `TWI.tif`

They can become required parity targets later only if matching notebook reference files are added to the frozen reference set and documented in the reference manifest.

## Fresh-ROI Caveat

Fresh-ROI notebook parity is not claimed. The closed parity result proves that the app matches notebook-equivalent production-core outputs for the accepted reference workflow when the authoritative GRID is identical.

For new production `/runs`, the production GRID remains app-authoritative. Notebook-exact GRID is not the default production convention.

## Future Frozen Reference Fixture

Future work should formalize the frozen reference set as a repo fixture:

- path: `tests/notebook_parity/fixtures/reference_run_v1/`
- required manifest listing every notebook-matched artifact
- required checksums for fixture artifacts
- explicit status for app-only artifacts that are not notebook-matched in that fixture

The current laptop-path reference bundle is useful validation evidence, but it is not yet a repo fixture contract.

## Reference Refresh Policy

Reference refresh is allowed only when an audit proves the existing frozen reference is internally inconsistent with its notebook-derived source.

Rules:

- require a pre-condition proof before any refresh
- require a post-condition proof after any refresh
- derive the refreshed reference from the notebook expression plus frozen reference inputs only
- never derive a refreshed reference from app outputs
- do not relax tolerance during a reference refresh
- keep refresh scope to one file unless broader scope is explicitly approved

Worked examples:

- DEM hillshade refresh:
  - pre-condition was true because the old frozen hillshade reference did not exactly match the notebook Cell 13 hillshade expression applied to frozen `DEM_640.tif`
  - the refresh was executed for `DEM_GEO8_TIFS/hillshade_0to1_640.tif` only
  - post-condition verification showed the refreshed reference exactly matched the notebook expression result
  - strict zero-tolerance DEM parity now passes

- `RADAR_STACK_HWC` refresh attempt:
  - pre-condition was false because the existing frozen `RADAR_STACK_HWC` reference already matched `np.stack` of frozen SAR band references exactly
  - refresh was correctly not executed
  - the remaining app-vs-reference mismatch stays classified as accepted upstream SAR-band-residual inheritance
  - no SAR reference refresh, SAR math change, or tolerance change applies
