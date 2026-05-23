# SAR Source-Selection Parity

F13 isolates SAR source-selection differences before any SAR science formula changes.

The local-only report is written by:

```bash
python scripts/report_sar_source_selection_parity.py \
  --app-run-dir data/runs/<run_id> \
  --notebook-root <notebook-output-root> \
  --output-dir data/reports
```

Repeat `--notebook-root` for downloaded notebook subfolders such as a separate radar output folder.

Outputs:

- `sar_source_selection_parity_<run_id>.json`
- `sar_source_selection_parity_<run_id>.csv`

Both outputs are operator-local `FILESYSTEM_ONLY` reports. They use root labels and relative paths only; they must not be served over HTTP or exposed through public API DTOs.

The app-side SAR metadata is `qa/sar/sar_pair_diagnostics.json`. It records:

- Sentinel-1 collection id.
- Date window and notebook-style filters.
- Active selection profile: `notebook_qa_s1_master_units`.
- Notebook-style source parameters: `orbit_window_days = 12`, `pair_cap_hours = 48`, `max_pairs = 4`.
- Selected VV/VH/angle input bands and VV/VH/logRatio/incidence output bands.
- ASC/DESC selected image ids and pair time deltas when Earth Engine diagnostics are available.
- The `angle -> incidence` output mapping.
- Local DEM RTC, refined-Lee filtering, dB-linear-dB, and grid sampling flags.

Interpretation rules:

- A SAR numeric mismatch remains a source-selection diagnosis until image ids, date window, orbit pairing, angle/incidence source, and processing path are reconciled.
- `logRatio_dB` should be treated as downstream of VV/VH unless evidence proves an independent formula issue.
- `incidence` is the app output name for the sampled Sentinel-1 `angle` band after local DEM RTC masking.
- Radar tensor stack mismatches are downstream diagnostics until the SAR bands are source-aligned.
- Do not weaken numeric tolerances or mark mismatched SAR rows as pass.
- Do not change notebook code.
