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

Key diagnostics:

- raw match percent
- common-valid-mask match percent
- mask overlap percent
- mean and median difference
- correlation
- linear fit `app ≈ slope * notebook + intercept`
- likely cause categories such as masking, constant offset, RTC/scale difference, or downstream stack divergence

This report is diagnostic only. It does not change SAR source selection, notebook code, numeric tolerances, or public API behavior.
