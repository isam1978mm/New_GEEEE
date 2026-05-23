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
