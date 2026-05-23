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
- Active SAR pixel-output selection profile: `cell25_pixel_export`.
- Cell 25 pixel-output source parameters: `orbit_window_days = 9`, `pair_cap_hours = 36`, `max_pairs = 4`, `min_pairs = 2`, targets `[4, 3, 2]`.
- Cell 21 `QA_S1_MASTER_UNITS` profile is recorded as auxiliary QA only and does not drive SAR pixel outputs.
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

F18 profile distinction:

- `cell25_pixel_export_profile` compares app SAR pixel-output metadata against `QA_RADAR_META*.json` or `SUMMARY_RADAR*` filename provenance.
- `cell21_master_units_qa_profile` reports `QA_S1_MASTER_UNITS.json` as auxiliary metadata so its `48h/12d` values are not confused with the actual Cell 25 `36h/9d` pixel-export profile.

F19 provenance rule:

- Cell 25 `QA_RADAR_META*.json` is the source of truth for SAR pixel-output provenance.
- If Cell 25 metadata proves `pairs4_pairdt36h_orbitpm9d` but does not include per-pair ASC/DESC image IDs, `image_identity` and `orbit_pairing` report `MISSING_CELL25_PAIR_IDS` rather than a mismatch.
- Cell 21 `QA_S1_MASTER_UNITS.json` pair IDs remain auxiliary and must not be compared as if they were Cell 25 pixel-export pair IDs.
- If a future Cell 25 metadata file includes true per-pair ASC/DESC IDs and pair deltas, the report compares app pair provenance against those Cell 25 IDs directly.

F22 Cell 25 pair sidecar:

- True Cell 25 pair provenance can be supplied as `QA/QA_RADAR_CELL25_PAIR_IDS_<run_id>_pairs4_pairdt36h_orbitpm9d.json` under a notebook root, or by passing `--cell25-pairs-json <path>` to `scripts/report_sar_source_selection_parity.py`.
- The sidecar is `FILESYSTEM_ONLY` and should contain `source_profile = cell25_pixel_export`, `orbit_window_days = 9`, `pair_cap_hours = 36`, selected ASC/DESC tracks, and `pairs` entries with `asc_id`, `desc_id`, `asc_timestamp`, `desc_timestamp`, and `dt_hours`.
- `scripts/export_cell25_sar_pair_provenance.py` can export that sidecar from an app run grid using the same Earth Engine service-account path and Cell 25 source-selection logic as the app:

```bash
python scripts/export_cell25_sar_pair_provenance.py \
  --app-run-dir data/runs/<run_id> \
  --output-dir <notebook-output-root>/QA
```

- `source_identity_classification` reports `SOURCE_ID_UNPROVEN` when true Cell 25 pair IDs are absent, `SOURCE_ID_MISMATCH` when sidecar IDs differ from app diagnostics, and `SOURCE_ID_MATCH_PROCESSING_DELTA_REMAINS` when true Cell 25 source identity matches and SAR numeric residuals should be diagnosed as processing deltas.
