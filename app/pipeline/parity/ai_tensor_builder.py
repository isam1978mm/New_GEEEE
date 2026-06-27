from __future__ import annotations

from datetime import UTC, datetime
import csv
import json
from pathlib import Path
from typing import Mapping

import numpy as np

from app.pipeline.qa_paths import ensure_run_qa_dir

try:
    import rasterio
except Exception:  # pragma: no cover
    rasterio = None


AI_TENSOR_BUILDER_SCHEMA_VERSION = "plan_b29_ai_tensor_builder_v1"
SOURCE_CELL = "cell_148"
SOURCE_NOTEBOOK_FAMILY = "STAGE_4_AI_TENSOR_BUILDER"

AI_TENSOR_OUTPUT_DIR = "AI_TENSORS_STAGE4"
OUT_FULL_NPY = "AI_FULL_52B_FLOAT32_640.npy"
OUT_YOLO_RGB = "YOLOV11_RGB_640.npy"
OUT_YOLO_VIS = "YOLOV11_RGB_VISUAL.tif"
OUT_CNN = "CNN_MULTI_24B_640.npy"
OUT_SWIN = "SWINSEGFORMER_16B_640.npy"
OUT_PCA_RGB = "PCA_RGB_640.npy"
OUT_NEGATIVE = "AI_NEGATIVE_MASK_640.npy"
OUT_JSON = "STAGE4_AI_TENSOR_BUILDER.json"
OUT_CSV = "STAGE4_AI_TENSOR_BANDS.csv"

FULL_TENSOR_BAND_SPECS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Secret_Gold_Halo", ("Secret_Gold_Halo", "AI_READY_640_Secret_Gold_Halo")),
    ("Secret_Silver_Oxide", ("Secret_Silver_Oxide", "AI_READY_640_Secret_Silver_Oxide")),
    ("Secret_Tunnel_Ceiling", ("Secret_Tunnel_Ceiling", "AI_READY_640_Secret_Tunnel_Ceiling")),
    ("Secret_Thermal_Inertia", ("Secret_Thermal_Inertia", "AI_READY_640_Secret_Thermal_Inertia")),
    ("Secret_Chemical_Protector", ("Secret_Chemical_Protector", "AI_READY_640_Secret_Chemical_Protector")),
    ("Secret_Hidden_Doors", ("Secret_Hidden_Doors", "AI_READY_640_Secret_Hidden_Doors")),
    ("REPORT_640_FINAL_Zero_Point_Targets", ("REPORT_640_FINAL_Zero_Point_Targets",)),
    ("REPORT_640_Mass_Report", ("REPORT_640_Mass_Report",)),
    ("REPORT_640_Pottery_Report", ("REPORT_640_Pottery_Report",)),
    ("AI_BEH_Gold_Pure_Density_19_3_DOM_lin_640", ("AI_BEH_Gold_Pure_Density_19_3_DOM_lin_640",)),
    ("AI_BEH_Artifacts_Jars_Chests_DOM_lin_640", ("AI_BEH_Artifacts_Jars_Chests_DOM_lin_640",)),
    ("AI_BEH_Mercury_RareChemicals_DOM_lin_640", ("AI_BEH_Mercury_RareChemicals_DOM_lin_640",)),
    ("AI_BEH_Gemstones_AncientGlass_DOM_lin_640", ("AI_BEH_Gemstones_AncientGlass_DOM_lin_640",)),
    ("AI_BEH_Alloys_Statues_REL_ND_DOM_lin_640", ("AI_BEH_Alloys_Statues_REL_ND_DOM_lin_640",)),
    ("AIX_MaskVegetationRoots_Norm01", ("MaskVegetationRoots_Norm01",)),
    ("AIX_MaskWaterMoisture_Norm01", ("MaskWaterMoisture_Norm01",)),
    ("AIX_IndexIronOxide_Norm01", ("IndexIronOxide_Norm01",)),
    ("AIX_IndexFerricIron_Norm01", ("IndexFerricIron_Norm01",)),
    ("AIX_IndexClayThermal_Norm01", ("IndexClayThermal_Norm01",)),
    ("AIX_MaskCharcoalLead_Norm01", ("MaskCharcoalLead_Norm01",)),
    ("AIX_MaskQuartzBasalt_Norm01", ("MaskQuartzBasalt_Norm01",)),
    ("AIX_MaskCarbonate_Norm01", ("MaskCarbonate_Norm01",)),
    ("AIX_ThermalTimeSeriesAnomaly_Norm01", ("ThermalTimeSeriesAnomaly_Norm01",)),
    ("AIX_Jan_IronOxideProxy_Norm01", ("Jan_IronOxideProxy_Norm01",)),
    ("AIX_Jan_MineralAlterationProxy_Norm01", ("Jan_MineralAlterationProxy_Norm01",)),
    ("AIX_Jan_ThermalAnomaly_Norm01", ("Jan_ThermalAnomaly_Norm01",)),
    ("AIX_Apr_IronOxideProxy_Norm01", ("Apr_IronOxideProxy_Norm01",)),
    ("AIX_Apr_MineralAlterationProxy_Norm01", ("Apr_MineralAlterationProxy_Norm01",)),
    ("AIX_Apr_ThermalAnomaly_Norm01", ("Apr_ThermalAnomaly_Norm01",)),
    ("AIX_Aug_IronOxideProxy_Norm01", ("Aug_IronOxideProxy_Norm01",)),
    ("AIX_Aug_MineralAlterationProxy_Norm01", ("Aug_MineralAlterationProxy_Norm01",)),
    ("AIX_Aug_ThermalAnomaly_Norm01", ("Aug_ThermalAnomaly_Norm01",)),
    ("AIX_Elevation_Norm01", ("Elevation_Norm01",)),
    ("AIX_Slope_Norm01", ("Slope_Norm01",)),
    ("AIX_Aspect_Norm01", ("Aspect_Norm01",)),
    ("AIX_Hillshade_Norm01", ("Hillshade_Norm01",)),
    ("ENT_VV_LocalEntropy_w3_lin", ("ENT_VV_LocalEntropy_w3_lin",)),
    ("AUX_OrbitalLogRatio_dB", ("AUX_OrbitalLogRatio_dB",)),
    ("AUX_VH_to_VV_MoistureProxy_lin", ("AUX_VH_to_VV_MoistureProxy_lin",)),
    ("SIM_GPR_VoidScan_lin", ("SIM_GPR_VoidScan_lin",)),
    ("SIM_MagneticAnomalies_lin", ("SIM_MagneticAnomalies_lin",)),
    ("SIM_EMI_Conductivity_lin", ("SIM_EMI_Conductivity_lin",)),
    ("SIM_MicroGravity_Density_lin", ("SIM_MicroGravity_Density_lin",)),
    ("NANO_Depth_Penetration", ("NANO_Depth_Penetration",)),
    ("NANO_Human_Geometry_Detector", ("NANO_Human_Geometry_Detector",)),
    ("NANO_Mass_Anomaly", ("NANO_Mass_Anomaly",)),
    ("NANO_RVI_Clean", ("NANO_RVI_Clean",)),
    ("TGT_HighSpecular_LowCrossPol", ("TGT_HighSpecular_LowCrossPol",)),
    ("TGT_BrightMetallic_Mix", ("TGT_BrightMetallic_Mix",)),
    ("TGT_CompactMetal_Contrast", ("TGT_CompactMetal_Contrast",)),
    ("TGT_StrongDoubleBounce", ("TGT_StrongDoubleBounce",)),
    ("TGT_MidReflectance_Band", ("TGT_MidReflectance_Band",)),
)

YOLO_CHANNELS = ("YOLO_METAL", "YOLO_VOID", "YOLO_THERMAL")
CNN_BASE_CHANNELS = (
    "gold", "silver", "tunnel", "door", "mass", "pottery", "vv", "vh",
    "ratio", "thermal", "delta", "slope", "rough", "tpi", "quartz",
    "lime", "moist", "risk", "support", "negative",
)
CNN_DERIVED_CHANNELS = ("support_grad_x", "support_grad_y", "support_grad_mag", "support_local_mean")
SWIN_CHANNELS = (
    "support", "risk", "thermal", "delta", "tunnel", "door", "mass", "gold",
    "silver", "vv", "vh", "ratio", "slope", "rough", "quartz", "moist",
)


def _norm01(array: np.ndarray) -> np.ndarray:
    x = np.asarray(array, dtype=np.float32).copy()
    x[~np.isfinite(x)] = np.nan
    valid = np.isfinite(x)
    if int(valid.sum()) < 10:
        return np.zeros_like(x, dtype=np.float32)
    p2, p98 = np.nanpercentile(x[valid], [2, 98])
    if not np.isfinite(p2) or not np.isfinite(p98) or abs(float(p98 - p2)) < 1e-6:
        return np.zeros_like(x, dtype=np.float32)
    y = np.clip((x - p2) / (p98 - p2), 0.0, 1.0)
    y[~np.isfinite(y)] = 0.0
    return y.astype(np.float32)


def _finite(array: np.ndarray) -> np.ndarray:
    out = np.asarray(array, dtype=np.float32).copy()
    out[~np.isfinite(out)] = 0.0
    return out.astype(np.float32)


def _mean3(array: np.ndarray) -> np.ndarray:
    x = np.pad(_finite(array), 1, mode="edge")
    out = (
        x[:-2, :-2] + x[:-2, 1:-1] + x[:-2, 2:] +
        x[1:-1, :-2] + x[1:-1, 1:-1] + x[1:-1, 2:] +
        x[2:, :-2] + x[2:, 1:-1] + x[2:, 2:]
    ) / 9.0
    return out.astype(np.float32)


def _infer_shape(bands: Mapping[str, np.ndarray]) -> tuple[int, int]:
    for value in bands.values():
        arr = np.asarray(value)
        if arr.ndim == 2:
            return int(arr.shape[0]), int(arr.shape[1])
    raise ValueError("No 2D source bands were provided.")


def _select_band(
    bands: Mapping[str, np.ndarray],
    output_name: str,
    keywords: tuple[str, ...],
    shape: tuple[int, int],
) -> tuple[np.ndarray, str | None]:
    lower_to_name = {name.lower(): name for name in bands}
    for keyword in (output_name, *keywords):
        match = lower_to_name.get(keyword.lower())
        if match is not None:
            return _finite(bands[match]), match

    low_keywords = [keyword.lower() for keyword in keywords]
    for name, array in bands.items():
        low_name = name.lower()
        if any(keyword in low_name for keyword in low_keywords):
            return _finite(array), name

    return np.zeros(shape, dtype=np.float32), None


def _pca_rgb(full_tensor: np.ndarray) -> np.ndarray:
    channels, height, width = full_tensor.shape
    flat = full_tensor.reshape(channels, -1).T.astype(np.float32)
    flat[~np.isfinite(flat)] = 0.0
    flat = flat - flat.mean(axis=0, keepdims=True)

    cov = (flat.T @ flat) / max(flat.shape[0] - 1, 1)
    eigvals, eigvecs = np.linalg.eigh(cov.astype(np.float64))
    order = np.argsort(eigvals)[::-1][:3]
    components = eigvecs[:, order].astype(np.float32)
    projected = flat @ components

    out = projected.reshape(height, width, 3).transpose(2, 0, 1)
    return np.stack([_norm01(out[index]) for index in range(3)], axis=0).astype(np.float32)


def _load_secret_tifs(run_dir: Path) -> dict[str, np.ndarray]:
    if rasterio is None:
        return {}
    output: dict[str, np.ndarray] = {}
    secret_dir = run_dir / "AI_READY_640"
    for path in secret_dir.glob("AI_READY_640_Secret_*.tif"):
        with rasterio.open(path) as src:
            arr = src.read(1).astype(np.float32)
        short = path.stem.replace("AI_READY_640_", "")
        output[short] = arr
        output[path.stem] = arr
    return output


def _load_stack_alias_bands(run_dir: Path) -> dict[str, np.ndarray]:
    stack_dir = run_dir / "NPY_STACKS"
    manifest_path = stack_dir / "STACK_ALIAS_MANIFEST.json"
    output: dict[str, np.ndarray] = {}

    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in manifest.get("aliases", []):
            filename = entry.get("filename")
            band_names = entry.get("band_names")
            if not isinstance(filename, str) or not isinstance(band_names, list):
                continue
            path = stack_dir / filename
            if not path.is_file():
                continue
            cube = np.load(path)
            if cube.ndim != 3:
                continue
            if cube.shape[-1] == len(band_names):
                for index, band_name in enumerate(band_names):
                    output[str(band_name)] = cube[:, :, index].astype(np.float32)
            elif cube.shape[0] == len(band_names):
                for index, band_name in enumerate(band_names):
                    output[str(band_name)] = cube[index].astype(np.float32)

    radar_path = run_dir / "stacks" / "tensor_support" / "radar_db_support_stack.npy"
    if radar_path.is_file():
        radar = np.load(radar_path)
        radar_names = ("VV_dB", "VH_dB", "logRatio_dB", "incidence")
        if radar.ndim == 3 and radar.shape[-1] >= len(radar_names):
            for index, name in enumerate(radar_names):
                output[name] = radar[:, :, index].astype(np.float32)

    return output


def load_plan_b29_source_bands(run_dir: str | Path) -> dict[str, np.ndarray]:
    run_dir = Path(run_dir)
    bands: dict[str, np.ndarray] = {}
    bands.update(_load_stack_alias_bands(run_dir))
    bands.update(_load_secret_tifs(run_dir))
    if not bands:
        raise FileNotFoundError("No Plan B #29 source bands found. Run S2, secret_layers, and feature_stacks first.")
    return bands


def build_plan_b29_ai_tensors_from_bands(source_bands: Mapping[str, np.ndarray]) -> dict[str, object]:
    shape = _infer_shape(source_bands)

    selected: dict[str, np.ndarray] = {}
    selected_sources: dict[str, str | None] = {}
    for output_name, keywords in FULL_TENSOR_BAND_SPECS:
        arr, source_name = _select_band(source_bands, output_name, keywords, shape)
        selected[output_name] = _norm01(arr)
        selected_sources[output_name] = source_name

    full_band_names = [name for name, _keywords in FULL_TENSOR_BAND_SPECS]
    full_tensor = np.stack([selected[name] for name in full_band_names], axis=0).astype(np.float32)

    gold = selected["Secret_Gold_Halo"]
    silver = selected["Secret_Silver_Oxide"]
    tunnel = selected["Secret_Tunnel_Ceiling"]
    thermal = selected["Secret_Thermal_Inertia"]
    chemical = selected["Secret_Chemical_Protector"]
    door = selected["Secret_Hidden_Doors"]
    zero = selected["REPORT_640_FINAL_Zero_Point_Targets"]
    mass = selected["REPORT_640_Mass_Report"]
    pottery = selected["REPORT_640_Pottery_Report"]

    vv = selected["TGT_CompactMetal_Contrast"]
    vh = selected["AUX_VH_to_VV_MoistureProxy_lin"]
    ratio = selected["AUX_OrbitalLogRatio_dB"]
    delta = selected["AIX_ThermalTimeSeriesAnomaly_Norm01"]
    quartz = selected["AIX_MaskQuartzBasalt_Norm01"]
    lime = selected["AIX_MaskCarbonate_Norm01"]
    moist = selected["AIX_MaskWaterMoisture_Norm01"]
    slope = selected["AIX_Slope_Norm01"]
    rough = selected["AIX_Hillshade_Norm01"]
    tpi = selected["AIX_Aspect_Norm01"]

    risk = _norm01(
        0.28 * quartz +
        0.22 * lime +
        0.20 * moist +
        0.18 * silver +
        0.12 * thermal -
        0.15 * tunnel
    )

    support = _norm01(
        0.25 * selected["TGT_CompactMetal_Contrast"] +
        0.20 * (1.0 - risk) +
        0.18 * tunnel +
        0.14 * door +
        0.13 * mass +
        0.10 * zero
    )

    metal_channel = _norm01(0.40 * gold + 0.25 * silver + 0.20 * mass + 0.15 * vv)
    void_channel = _norm01(0.45 * tunnel + 0.25 * door + 0.15 * tpi + 0.15 * rough)
    thermal_channel = _norm01(0.40 * thermal + 0.35 * delta + 0.25 * support)

    metal_channel = np.clip(metal_channel - 0.35 * risk, 0.0, 1.0).astype(np.float32)
    void_channel = np.clip(void_channel - 0.25 * moist, 0.0, 1.0).astype(np.float32)
    thermal_channel = np.clip(thermal_channel - 0.25 * quartz, 0.0, 1.0).astype(np.float32)

    yolo_rgb = np.stack([metal_channel, void_channel, thermal_channel], axis=0).astype(np.float32)

    negative = np.where(risk > 0.5, 1.0, 0.0).astype(np.float32)

    cnn_base = [
        gold, silver, tunnel, door, mass, pottery, vv, vh, ratio, thermal,
        delta, slope, rough, tpi, quartz, lime, moist, risk, support, negative,
    ]
    grad_y, grad_x = np.gradient(support.astype(np.float32))
    cnn_stack = np.concatenate(
        [
            np.stack([_norm01(x) for x in cnn_base], axis=0),
            _norm01(grad_x)[None],
            _norm01(grad_y)[None],
            _norm01(np.hypot(grad_x, grad_y))[None],
            _norm01(_mean3(support))[None],
        ],
        axis=0,
    ).astype(np.float32)

    swin_stack = np.stack(
        [
            support, risk, thermal, delta, tunnel, door, mass, gold, silver,
            vv, vh, ratio, slope, rough, quartz, moist,
        ],
        axis=0,
    ).astype(np.float32)

    pca_rgb = _pca_rgb(full_tensor)
    missing = [name for name, source_name in selected_sources.items() if source_name is None]

    return {
        "full_tensor": full_tensor,
        "full_tensor_band_names": full_band_names,
        "full_tensor_sources": selected_sources,
        "yolo_rgb": yolo_rgb,
        "yolo_channels": list(YOLO_CHANNELS),
        "cnn_tensor": cnn_stack,
        "cnn_channels": list(CNN_BASE_CHANNELS + CNN_DERIVED_CHANNELS),
        "swin_tensor": swin_stack,
        "swin_channels": list(SWIN_CHANNELS),
        "pca_rgb": pca_rgb,
        "pca_channels": ["PCA_1", "PCA_2", "PCA_3"],
        "negative_mask": negative,
        "missing_source_bands_zero_filled": missing,
    }


def _write_yolo_visual(path: Path, yolo_rgb: np.ndarray, source_tif: Path | None = None) -> None:
    if rasterio is None:
        return
    height, width = yolo_rgb.shape[1:]
    if source_tif is not None and source_tif.is_file():
        with rasterio.open(source_tif) as src:
            profile = src.profile.copy()
    else:
        profile = {
            "driver": "GTiff",
            "height": height,
            "width": width,
            "count": 3,
            "dtype": "float32",
            "nodata": 0.0,
        }
    profile.update(count=3, dtype="float32", nodata=0.0, compress="deflate")
    with rasterio.open(path, "w", **profile) as dst:
        for index, name in enumerate(YOLO_CHANNELS, start=1):
            dst.write(yolo_rgb[index - 1].astype(np.float32), index)
            dst.set_band_description(index, name)


def write_plan_b29_ai_tensor_builder_outputs(
    run_dir: str | Path,
    run_id: str,
    *,
    source_bands: Mapping[str, np.ndarray] | None = None,
) -> dict[str, Path]:
    run_dir = Path(run_dir)
    bands = dict(source_bands) if source_bands is not None else load_plan_b29_source_bands(run_dir)
    products = build_plan_b29_ai_tensors_from_bands(bands)

    out_dir = run_dir / AI_TENSOR_OUTPUT_DIR
    qa_dir = ensure_run_qa_dir(run_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    qa_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "full_tensor": out_dir / OUT_FULL_NPY,
        "yolo_rgb": out_dir / OUT_YOLO_RGB,
        "yolo_visual": out_dir / OUT_YOLO_VIS,
        "cnn_tensor": out_dir / OUT_CNN,
        "swin_tensor": out_dir / OUT_SWIN,
        "pca_rgb": out_dir / OUT_PCA_RGB,
        "negative_mask": out_dir / OUT_NEGATIVE,
        "report_json": qa_dir / OUT_JSON,
        "bands_csv": qa_dir / OUT_CSV,
    }

    np.save(paths["full_tensor"], products["full_tensor"])
    np.save(paths["yolo_rgb"], products["yolo_rgb"])
    np.save(paths["cnn_tensor"], products["cnn_tensor"])
    np.save(paths["swin_tensor"], products["swin_tensor"])
    np.save(paths["pca_rgb"], products["pca_rgb"])
    np.save(paths["negative_mask"], products["negative_mask"])

    source_tif = run_dir / "stacks" / "tensor_support" / "ai_ready_support_stack.tif"
    _write_yolo_visual(paths["yolo_visual"], products["yolo_rgb"], source_tif=source_tif)

    rows = [
        {"tensor": "full", "shape": list(products["full_tensor"].shape), "channels": len(products["full_tensor_band_names"])},
        {"tensor": "YOLOv11", "shape": list(products["yolo_rgb"].shape), "channels": ",".join(products["yolo_channels"])},
        {"tensor": "CNN", "shape": list(products["cnn_tensor"].shape), "channels": int(products["cnn_tensor"].shape[0])},
        {"tensor": "Swin/SegFormer", "shape": list(products["swin_tensor"].shape), "channels": int(products["swin_tensor"].shape[0])},
        {"tensor": "PCA_RGB", "shape": list(products["pca_rgb"].shape), "channels": ",".join(products["pca_channels"])},
        {"tensor": "negative_mask", "shape": list(products["negative_mask"].shape), "channels": 1},
    ]
    with paths["bands_csv"].open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["tensor", "shape", "channels"])
        writer.writeheader()
        writer.writerows(rows)

    def rel(path: Path) -> str:
        return path.relative_to(run_dir).as_posix()

    report = {
        "schema_version": AI_TENSOR_BUILDER_SCHEMA_VERSION,
        "run_id": run_id,
        "stage": "STAGE 4 ? AI TENSOR BUILDER",
        "source_cell": SOURCE_CELL,
        "source_notebook_family": SOURCE_NOTEBOOK_FAMILY,
        "supporting_source_cells": ["cell_147", "cell_231"],
        "status": "implemented_tensor_builder_only",
        "privacy": "FILESYSTEM_ONLY",
        "http_servable": False,
        "frontend_visible": False,
        "downloadable_via_api": False,
        "trains_models": False,
        "runs_inference": False,
        "downloads_weights": False,
        "adds_heavy_ml_dependencies": False,
        "creates_model_artifacts": False,
        "notebook_value_parity_verified": False,
        "outputs": {key: rel(path) for key, path in paths.items()},
        "shapes": {
            "full": list(products["full_tensor"].shape),
            "yolo": list(products["yolo_rgb"].shape),
            "cnn": list(products["cnn_tensor"].shape),
            "swin": list(products["swin_tensor"].shape),
            "pca_rgb": list(products["pca_rgb"].shape),
            "negative_mask": list(products["negative_mask"].shape),
        },
        "channels": {
            "full": products["full_tensor_band_names"],
            "yolo": products["yolo_channels"],
            "cnn": products["cnn_channels"],
            "swin": products["swin_channels"],
            "pca_rgb": products["pca_channels"],
        },
        "normalization_policy": "robust per-channel p2-p98 norm01; non-finite/nodata values become 0.0",
        "missing_source_bands_zero_filled": products["missing_source_bands_zero_filled"],
        "next_dependency_unblocking_item": "Plan B item #31/#32 after model/dependency policy is selected",
        "created_at": datetime.now(UTC).isoformat(),
    }
    paths["report_json"].write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return paths
