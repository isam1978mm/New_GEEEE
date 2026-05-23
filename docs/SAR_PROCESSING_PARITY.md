# SAR Processing Parity

Goal F15 adds a local-only SAR processing parity report for post-F14 runs where source-selection identity already matches.

The report compares:

- `qa/sar/sar_summary.csv` against notebook `SUMMARY_RADAR*.csv`
- SAR rasters for `VV_dB`, `VH_dB`, `logRatio_dB`, and notebook `angle` versus app `incidence`
- SAR NPY band exports for the same bands
- `logRatio == VV_dB - VH_dB` inside notebook and app outputs
- downstream `stacks/tensor_support/radar_linear_support_stack.npy`

The report writes:

- `data/reports/sar_processing_parity_<run_id>.json`
- `data/reports/sar_processing_parity_<run_id>.csv`

Both outputs are `FILESYSTEM_ONLY` and local-only. They use notebook root labels and relative paths only.

Run it with:

```bash
python -m scripts.report_sar_processing_parity \
  --app-run-dir data/runs/<run_id> \
  --notebook-root <notebook_root> \
  --output-dir data/reports
```

Repeat `--notebook-root` to search multiple notebook roots.

For F17 trend diagnostics, pass a previous local report:

```bash
python -m scripts.report_sar_processing_parity \
  --app-run-dir data/runs/<run_id> \
  --notebook-root <notebook_root> \
  --output-dir data/reports \
  --prior-report data/reports/<previous_sar_processing_report>.json
```

Key diagnostics:

- raw match percent
- common-valid-mask match percent
- mask overlap percent
- mean and median difference
- correlation
- linear fit `app ≈ slope * notebook + intercept`
- exact notebook/app summary deltas by band
- notebook `QA_RADAR_META*.json` parsing for `LOCAL_DEM_RTC`, pair count, and exact RADAR NPY output keys
- relative row/column pixel probes at center and corners for each available SAR array
- optional prior-report improvement/regression rows when `--prior-report` is provided
- likely cause categories such as masking, constant offset, RTC/scale difference, or downstream stack divergence

F17 diagnostic scope:

- Pixel probes use relative labels plus row/column indexes only; they do not store coordinates.
- `QA_RADAR_META` absolute notebook paths are never copied into the report; only root labels, relative files, and sanitized processing flags are reported.
- Prior-report comparisons are trend evidence only and must not be treated as numeric parity.
- No SAR science formula, source-selection rule, notebook code, or tolerance is changed by these diagnostics.

F18 pixel-output source of truth:

- SAR pixel outputs mirror notebook Cells 22, 24, and 25.
- Cell 25 uses the `cell25_pixel_export` source-selection profile: `pair_cap_hours = 36`, `orbit_window_days = 9`, `min_pairs = 2`, and target pair counts `[4, 3, 2]`.
- Cell 21 `QA_S1_MASTER_UNITS` remains auxiliary QA only; its `48h/12d` parameters are not used to drive app SAR pixel outputs.
- The local DEM RTC valid mask follows Cell 25: VV/VH must be non-nodata, while `corr` and `cos_inc` must be finite. The output `incidence` file stores the sampled raw Sentinel-1 `angle` band where angle is not nodata.

F19 SAR NPY mapping:

- Numeric parity resolves notebook SAR NPYs from `QA_RADAR_META*.json` `outputs.npys` when present.
- Notebook `outputs.npys.angle` maps to the app `npy_radar_bands/incidence.npy` output.
- Absolute notebook paths embedded in `QA_RADAR_META` are normalized to repository-local relative artifact paths before report rows are written.

F16 finding:

- The notebook `NO-COP-DEM` path applies a dB-domain border mask first:
  - `VV > -35`
  - `VH > -42`
  - `29 < angle < 46`
- The notebook then applies `dB -> linear -> sigma-lee -> lee -> dB` per image before ASC/DESC pair median and final pair-stack median.
- Local DEM RTC remains a later local NumPy step after sampling the fused `VV_dB`, `VH_dB`, and `angle` cube to the locked GRID.
- `logRatio_dB` remains `VV_dB - VH_dB` after local DEM RTC on both notebook and app sides.

App reconciliation:

- `app/pipeline/stages/sar_rtc.py` now reproduces the notebook per-image no-Copernicus-DEM preprocessing path before pair aggregation.
- SAR pair-selection was not changed in F16.
- Local DEM RTC formulas and tolerances were not weakened in F16.

This report is diagnostic only. It does not change SAR source selection, notebook code, numeric tolerances, or public API behavior.
