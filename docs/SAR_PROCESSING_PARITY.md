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

F20 SAR numeric delta diagnostics:

- `f20_edge_interior_*` rows compare edge pixels against interior pixels for each SAR band/container.
- `f20_nodata_edge_overlap_*` rows summarize invalid-mask overlap and edge-skewed nodata counts.
- `f20_angle_delta_distribution_*` rows count large angle/incidence deltas and report whether they are edge-localized.
- `f20_*_excluding_angle_delta_*` rows recompute VV/VH/logRatio deltas after excluding pixels with large angle/incidence deltas.
- These rows use counts, percentages, relative row/column diagnostics, and relative artifact labels only. They do not change SAR science logic, source selection, notebook code, or tolerances.

F21 VV/VH residual isolation:

- Notebook Cells 22, 24, and 25 were rechecked against `app/pipeline/stages/sar_rtc.py` for the residual candidates.
- The checked notebook behavior is: dB-domain border mask using `VV > -35`, `VH > -42`, `29 < angle < 46`; dB-to-linear conversion; sigma Lee using `ee.Kernel.square(kernel_m, "meters", True)`, mean/std thresholds, and `lin.where(within, lee)`; Lee fallback with constant noise variance `0.25`; per-image `VV_dB`, `VH_dB`, `angle`; ASC/DESC pair median followed by final pair-stack median; and `toFloat`, `unmask(NODATA)`, `reproject`, `clip`, `sampleRectangle` only for sampling.
- No exact notebook-code-backed SAR logic bug was identified in F21, so F21 remains diagnostic-only.
- `f21_residual_distribution_*` rows add count-only residual histograms for `<=1e-4`, `<=1e-3`, `<=1e-2`, `<=5e-2`, `<=1e-1`, and `>1e-1`.
- `f21_sign_balance_*` rows report positive, negative, and near-zero delta counts.
- `f21_regression_residual_*` rows compare original VV/VH residuals to local report-only linear-fit-adjusted residuals.
- `f21_vv_vh_residual_symmetry_*` rows compare VV and VH residual deltas to distinguish band-specific behavior from shared filter, aggregation, source-ID, or sampling behavior.

F23 true-processing-delta diagnostics:

- F23 assumes source identity is proven separately by F13 with a true Cell 25 pair sidecar and `SOURCE_ID_MATCH_PROCESSING_DELTA_REMAINS`.
- `f23_large_residual_spatial_bins_*` rows count `>0.1 dB` residuals by row/column quartile bins and tile-boundary bands. They store counts only, not coordinates.
- `f23_large_residual_context_*` rows count large residuals in high-slope, mid/high-incidence, and low/high-backscatter groups when the required local arrays are available.
- `f23_low_slope_mid_incidence_subset_*` rows recompute residual stats on low-slope and mid-incidence pixels to test whether terrain/incidence explains the delta.
- `f23_dtype_casting_profile_*` rows compare final-array residuals after report-only float32 casting checks.
- `f23_vv_vh_large_residual_overlap_*` rows count shared versus band-specific large residual pixels.
- `f23_median_domain_profile` documents that median-domain/order proof requires per-image or per-pair Cell 25 intermediate captures; final arrays alone are insufficient to change SAR math.

F24 Cell 25 intermediate parity diagnostics:

- `report_sar_processing_parity.py` accepts optional local-only `--source-report`, `--notebook-intermediate-manifest`, and `--app-intermediate-manifest` inputs.
- `f24_source_identity_gate` blocks intermediate interpretation unless F13/F22 proved `SOURCE_ID_MATCH_PROCESSING_DELTA_REMAINS` on the same run.
- `intermediate_per_image_products_db`, `intermediate_pair_median`, `intermediate_final_median_pre_rtc`, `intermediate_post_sample_pre_rtc`, and `intermediate_post_rtc` compare local-only Cell 25 intermediate manifests when available.
- `intermediate_post_rtc` reuses existing final notebook/app VV/VH/logRatio arrays plus notebook `angle` versus app `incidence`.
- `first_divergence_stage` classifies:
  - `SOURCE_ID_MATCHED_INTERMEDIATES_MISSING`
  - `APP_INTERMEDIATES_MISSING`
  - `FIRST_DIVERGENCE_PER_IMAGE_FILTER`
  - `FIRST_DIVERGENCE_PAIR_MEDIAN`
  - `FIRST_DIVERGENCE_FINAL_MEDIAN_OR_REPROJECT`
  - `FIRST_DIVERGENCE_LOCAL_RTC`
  - `FIRST_DIVERGENCE_NOT_FOUND`
- `FIRST_DIVERGENCE_LOCAL_RTC` is valid only when all earlier intermediate stages are present and matched. If notebook intermediates exist but app-side earlier stages are missing, `first_divergence_stage` is blocked instead of claiming local RTC.
- Missing notebook-side stages are reported as `MISSING_NOTEBOOK_INTERMEDIATE`; the report does not guess missing Cell 25 intermediates from final arrays alone.
- `scripts/export_cell25_sar_intermediates.py` has two explicit modes:
  - `--mode post-rtc-only` exports the feasible offline app-side stage, `post_rtc`, from existing local final arrays into `qa/sar/intermediates/` or a caller-provided output directory.
  - `--mode live-cell25-full` replays the app Cell 25 path with Earth Engine access and exports `per_image_products_db`, `pair_median`, `final_median_pre_rtc`, `post_sample_pre_rtc`, and `post_rtc`.
- Full app-side intermediate export requires explicit local operator approval before running because it uses Earth Engine credentials.
- Earlier notebook-side stages still require a local notebook export in the same manifest layout:

```python
import json, os, shutil
import numpy as np

if "pairs" not in globals():
    raise RuntimeError("Run the Cell 25 pair-selection cell first so `pairs` is defined.")
if "per_image_products_db" not in globals():
    raise RuntimeError("Run the NO-COP-DEM per_image_products_db cell first.")
if "img_by_id" not in globals():
    raise RuntimeError("Run the Cell 25 image-id helper cell first.")
if "to_grid_radar" not in globals() or "finalize_for_sample" not in globals():
    raise RuntimeError("Run the Cell 25 grid/finalize helpers first.")

OUT_BASE = os.path.join(PATHS["qa_root"], "sar", "intermediates")
os.makedirs(OUT_BASE, exist_ok=True)

def _stage_cube(img, band_names):
    sampled = finalize_for_sample(to_grid_radar(ee.Image(img).select(list(band_names))))
    cube = np.full((OUT_SIZE, OUT_SIZE, len(band_names)), NODATA, dtype=np.float32)
    for ty in range(n_tiles):
        for tx in range(n_tiles):
            x0_t = xmin_f + (tx * TILE_SIZE * SCALE)
            y1_t = ymax_f - (ty * TILE_SIZE * SCALE)
            x1_t = x0_t + (TILE_SIZE * SCALE)
            y0_t = y1_t - (TILE_SIZE * SCALE)
            tile_geo = ee.Geometry.Rectangle([x0_t, y0_t, x1_t, y1_t], CRS, False)
            rect = sampled.sampleRectangle(region=tile_geo, defaultValue=NODATA).getInfo()
            for bi, bn in enumerate(band_names):
                arr = np.array(rect["properties"][bn], dtype=np.float32)[:TILE_SIZE, :TILE_SIZE]
                cube[ty*TILE_SIZE:(ty+1)*TILE_SIZE, tx*TILE_SIZE:(tx+1)*TILE_SIZE, bi] = arr
    return {bn: cube[:, :, bi] for bi, bn in enumerate(band_names)}

def _write_stage_arrays(stage_name, label, bands):
    payload = {}
    for band_name, arr in bands.items():
        rel = os.path.join(stage_name, f"{label}_{band_name}.npy")
        abs_path = os.path.join(OUT_BASE, rel)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        np.save(abs_path, arr.astype(np.float32))
        payload[band_name] = rel.replace("\\", "/")
    return payload

stage_manifest = {
    "artifact_class": "FILESYSTEM_ONLY",
    "local_only": True,
    "source_profile": "cell25_pixel_export",
    "stages": {
        "per_image_products_db": {"items": []},
        "pair_median": {"items": []},
    },
}

pair_images = []
for idx, (a, d, _dt) in enumerate(pairs):
    asc_im = per_image_products_db(img_by_id(a["id"]))
    desc_im = per_image_products_db(img_by_id(d["id"]))
    stage_manifest["stages"]["per_image_products_db"]["items"].append({
        "label": f"pair{idx}_asc",
        "bands": _write_stage_arrays("per_image_products_db", f"pair{idx}_asc", _stage_cube(asc_im, ["VV_dB", "VH_dB", "angle"])),
    })
    stage_manifest["stages"]["per_image_products_db"]["items"].append({
        "label": f"pair{idx}_desc",
        "bands": _write_stage_arrays("per_image_products_db", f"pair{idx}_desc", _stage_cube(desc_im, ["VV_dB", "VH_dB", "angle"])),
    })
    pair_im = ee.ImageCollection([asc_im, desc_im]).median().select(["VV_dB", "VH_dB", "angle"])
    pair_images.append(pair_im)
    stage_manifest["stages"]["pair_median"]["items"].append({
        "label": f"pair{idx}",
        "bands": _write_stage_arrays("pair_median", f"pair{idx}", _stage_cube(pair_im, ["VV_dB", "VH_dB", "angle"])),
    })

final_pair_stack = ee.ImageCollection(pair_images).median().select(["VV_dB", "VH_dB", "angle"])
final_pre_rtc = _stage_cube(final_pair_stack, ["VV_dB", "VH_dB", "angle"])
stage_manifest["stages"]["final_median_pre_rtc"] = {
    "items": [{"label": "final", "bands": _write_stage_arrays("final_median_pre_rtc", "final", final_pre_rtc)}]
}

final_for_sample = finalize_for_sample(to_grid_radar(final_pair_stack))
cube_3 = np.full((OUT_SIZE, OUT_SIZE, 3), NODATA, dtype=np.float32)
for ty in range(n_tiles):
    for tx in range(n_tiles):
        x0_t = xmin_f + (tx * TILE_SIZE * SCALE)
        y1_t = ymax_f - (ty * TILE_SIZE * SCALE)
        x1_t = x0_t + (TILE_SIZE * SCALE)
        y0_t = y1_t - (TILE_SIZE * SCALE)
        tile_geo = ee.Geometry.Rectangle([x0_t, y0_t, x1_t, y1_t], CRS, False)
        rect = final_for_sample.sampleRectangle(region=tile_geo, defaultValue=NODATA).getInfo()
        for bi, bn in enumerate(["VV_dB", "VH_dB", "angle"]):
            arr = np.array(rect["properties"][bn], dtype=np.float32)[:TILE_SIZE, :TILE_SIZE]
            cube_3[ty*TILE_SIZE:(ty+1)*TILE_SIZE, tx*TILE_SIZE:(tx+1)*TILE_SIZE, bi] = arr

stage_manifest["stages"]["post_sample_pre_rtc"] = {
    "items": [{
        "label": "final",
        "bands": _write_stage_arrays("post_sample_pre_rtc", "final", {
            "VV_dB": cube_3[:, :, 0],
            "VH_dB": cube_3[:, :, 1],
            "angle": cube_3[:, :, 2],
        }),
    }]
}

with rasterio.open(DEM_REF_TIF) as ref:
    dem = ref.read(1).astype(np.float32)
    dem_nd = ref.nodata
if dem_nd is not None:
    dem = np.where(dem == dem_nd, np.nan, dem)
dz_dy, dz_dx = np.gradient(dem, SCALE, SCALE)
slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
corr = np.where(np.isfinite(np.cos(slope_rad)), np.maximum(np.cos(slope_rad), 0.25), np.nan)
ang = cube_3[:, :, 2]
cos_inc = np.where(np.isfinite(np.cos(np.deg2rad(ang))), np.maximum(np.cos(np.deg2rad(ang)), 1e-6), np.nan)
valid = (cube_3[:, :, 0] != NODATA) & (cube_3[:, :, 1] != NODATA) & np.isfinite(corr) & np.isfinite(cos_inc)
vv_lin = np.full(dem.shape, np.nan, dtype=np.float32)
vh_lin = np.full(dem.shape, np.nan, dtype=np.float32)
vv_lin[valid] = np.power(10.0, cube_3[:, :, 0][valid] / 10.0)
vh_lin[valid] = np.power(10.0, cube_3[:, :, 1][valid] / 10.0)
vv_lin = vv_lin / cos_inc / corr
vh_lin = vh_lin / cos_inc / corr
vv_db_corr = np.full(dem.shape, NODATA, dtype=np.float32)
vh_db_corr = np.full(dem.shape, NODATA, dtype=np.float32)
log_ratio = np.full(dem.shape, NODATA, dtype=np.float32)
vv_db_corr[valid] = 10.0 * np.log10(np.maximum(vv_lin[valid], 1e-12))
vh_db_corr[valid] = 10.0 * np.log10(np.maximum(vh_lin[valid], 1e-12))
log_ratio[valid] = vv_db_corr[valid] - vh_db_corr[valid]
stage_manifest["stages"]["post_rtc"] = {
    "label": "final",
    "bands": _write_stage_arrays("post_rtc", "final", {
        "VV_dB": vv_db_corr,
        "VH_dB": vh_db_corr,
        "logRatio_dB": log_ratio,
        "angle": ang.astype(np.float32),
    }),
}

manifest_path = os.path.join(OUT_BASE, "sar_intermediate_manifest.json")
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(stage_manifest, f, ensure_ascii=False, indent=2)
print("✅ Wrote local-only Cell 25 SAR intermediate manifest:", manifest_path)

if "PATHS_DRIVE_GLOBAL" in globals() and PATHS_DRIVE_GLOBAL:
    drive_base = os.path.join(PATHS_DRIVE_GLOBAL["qa_root"], "sar", "intermediates")
    os.makedirs(drive_base, exist_ok=True)
    shutil.copy2(manifest_path, os.path.join(drive_base, "sar_intermediate_manifest.json"))
    print("✅ Copied manifest to Drive RUN:", drive_base)
```

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
