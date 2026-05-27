from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image

from app.db.models.enums import ArtifactClass
from app.errors import StageError
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.qa_paths import ensure_run_qa_dir
from app.pipeline.stages.dem import raster_sidecar_path, write_georeferenced_raster, write_raster_sidecar
from app.pipeline.stages.grid import GridSpec
from app.services.storage import read_manifest

SCIENCE_CORE_BANDS = (
    "VV_dB",
    "VH_dB",
    "logRatio_dB",
    "incidence",
    "NDVI",
    "NDWI",
    "NDMI",
    "NBR",
    "IRONOX",
    "IRON_SWIR",
    "BSI",
    "slope",
    "aspect",
    "curvature",
    "TPI",
    "TRI",
    "roughness",
    "TWI",
    "lst",
)
SCIENCE_CORE_STACK_TIF = "science_core_stack.tif"
SCIENCE_CORE_STACK_NPY = "science_core_stack.npy"
RADAR_LINEAR_SUPPORT_STACK_TIF = "radar_linear_support_stack.tif"
RADAR_LINEAR_SUPPORT_STACK_NPY = "radar_linear_support_stack.npy"
RADAR_DB_SUPPORT_STACK_TIF = "radar_db_support_stack.tif"
RADAR_DB_SUPPORT_STACK_NPY = "radar_db_support_stack.npy"
AI_READY_SUPPORT_STACK_TIF = "ai_ready_support_stack.tif"
AI_READY_SUPPORT_STACK_NPY = "ai_ready_support_stack.npy"
S2_MASK_SUPPORT_TIF = "s2_mask_support_valid.tif"
BAND_STATS_CSV = "band_stats.csv"
STACK_PRESENCE_SUMMARY_JSON = "stack_presence_summary.json"
TENSOR_AUDIT_SUMMARY_JSON = "tensor_audit_summary.json"
GEOMETRY_CONSISTENCY_SUMMARY_JSON = "geometry_consistency_summary.json"
NOTEBOOK_STACK_OUTPUT_DIR = "NPY_STACKS"
NOTEBOOK_RADAR_STACK_NPY = "RADAR_STACK_HWC_640_app.npy"
S2_MASK_SUPPORT_BANDS = ("NDVI", "NDWI", "NDMI", "NBR", "IRONOX", "IRON_SWIR", "BSI")
RADAR_STACK_BANDS = ("VV_dB", "VH_dB", "logRatio_dB", "incidence")
EPS = 1e-6


def _read_single_band_tif(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.array(image, dtype=np.float32)


def _save_multipage_tiff(path: Path, cube_hwc: np.ndarray) -> None:
    pages = [Image.fromarray(cube_hwc[:, :, band_index].astype(np.float32)) for band_index in range(cube_hwc.shape[-1])]
    first, *rest = pages
    first.save(path, format="TIFF", save_all=True, append_images=rest)


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _db_to_linear(array: np.ndarray, *, nodata: float) -> np.ndarray:
    linear = np.where(array == nodata, nodata, np.power(10.0, array / 10.0)).astype(np.float32)
    return linear


def _build_ai_ready_stack(cube: np.ndarray, *, nodata: float) -> np.ndarray:
    channel_count = cube.shape[-1]
    ready = np.zeros_like(cube, dtype=np.float32)
    for index in range(channel_count):
        channel = cube[:, :, index]
        valid_mask = channel != nodata
        valid_values = channel[valid_mask]
        if valid_values.size < 100:
            if valid_values.size:
                low = float(valid_values.min())
                high = float(valid_values.max())
            else:
                low = 0.0
                high = 1.0
        else:
            low = float(np.percentile(valid_values, 2))
            high = float(np.percentile(valid_values, 98))
        span = max(high - low, EPS)
        normalized = np.clip((channel - low) / span, 0.0, 1.0).astype(np.float32)
        ready[:, :, index] = np.where(valid_mask, normalized, 0.0).astype(np.float32)
    return ready


def collect_science_core_layers(run_dir: Path, grid_spec: GridSpec) -> list[tuple[str, np.ndarray]]:
    layers: list[tuple[str, np.ndarray]] = []
    missing: list[str] = []
    for name in SCIENCE_CORE_BANDS:
        path = run_dir / f"{name}.tif"
        if not path.is_file():
            missing.append(path.name)
            continue
        sidecar_path = raster_sidecar_path(path)
        if not sidecar_path.is_file():
            raise StageError(f"Missing raster sidecar for feature-stack source: {path.name}")
        sidecar = read_manifest(sidecar_path)
        if sidecar["crs"] != grid_spec.crs:
            raise StageError(f"Feature-stack source CRS mismatch: {path.name}")
        if [float(value) for value in sidecar["transform"]] != [float(value) for value in grid_spec.manifest.crs_transform]:
            raise StageError(f"Feature-stack source transform mismatch: {path.name}")
        if (int(sidecar["height"]), int(sidecar["width"])) != (grid_spec.size, grid_spec.size):
            raise StageError(f"Feature-stack source size mismatch: {path.name}")
        array = _read_single_band_tif(path)
        nodata = float(sidecar["nodata"])
        array = np.where(array == nodata, grid_spec.nodata, array).astype(np.float32)
        layers.append((name, array))
    if missing:
        raise StageError(f"Feature-stack stage requires science-core sources before assembly: {', '.join(missing)}")
    return layers


def build_feature_stack_products(
    source_layers: list[tuple[str, np.ndarray]],
    *,
    nodata: float,
) -> dict[str, object]:
    band_names = [name for name, _array in source_layers]
    cube = np.stack([array for _name, array in source_layers], axis=-1).astype(np.float32)
    valid = cube != nodata
    mask_bands = [band_names.index(name) for name in S2_MASK_SUPPORT_BANDS]
    s2_mask = valid[:, :, mask_bands].all(axis=-1).astype(np.float32)

    vv_db = cube[:, :, band_names.index("VV_dB")]
    vh_db = cube[:, :, band_names.index("VH_dB")]
    log_ratio_db = cube[:, :, band_names.index("logRatio_dB")]
    incidence = cube[:, :, band_names.index("incidence")]
    radar_linear_stack = np.stack(
        [
            _db_to_linear(vv_db, nodata=nodata),
            _db_to_linear(vh_db, nodata=nodata),
            _db_to_linear(log_ratio_db, nodata=nodata),
            np.where(incidence == nodata, nodata, incidence).astype(np.float32),
        ],
        axis=-1,
    ).astype(np.float32)
    radar_db_stack = np.stack([vv_db, vh_db, log_ratio_db, incidence], axis=-1).astype(np.float32)
    ai_ready_stack = _build_ai_ready_stack(cube, nodata=nodata)

    stats_rows: list[dict[str, object]] = []
    for band_index, band_name in enumerate(band_names):
        channel = cube[:, :, band_index]
        valid_mask = channel != nodata
        valid_values = channel[valid_mask]
        stats_rows.append(
            {
                "band_index": band_index,
                "band_name": band_name,
                "source_file": f"{band_name}.tif",
                "valid_count": int(valid_mask.sum()),
                "nodata_count": int(channel.size - int(valid_mask.sum())),
                "min": float(valid_values.min()) if valid_values.size else "",
                "max": float(valid_values.max()) if valid_values.size else "",
                "mean": float(valid_values.mean()) if valid_values.size else "",
            }
        )

    stack_presence_summary = {
        "stage": "feature_stacks",
        "band_count": len(band_names),
        "band_names": band_names,
        "missing_expected_bands": [],
        "all_expected_bands_present": True,
        "variant_families": [
            {
                "artifact_name": "radar_db_support_stack",
                "source_notebook_family": "RADAR_STACK_HWC_640",
                "band_names": ["VV_dB", "VH_dB", "logRatio_dB", "angle"],
            },
            {
                "artifact_name": "radar_linear_support_stack",
                "source_notebook_family": "SIGMA0_MASTER_640",
                "band_names": ["vv_sigma0_linear", "vh_sigma0_linear", "ratio_sigma0_linear", "incidence_angle"],
            },
            {
                "artifact_name": "ai_ready_support_stack",
                "source_notebook_family": "TESLA_V7_2_TENSOR_EXPORT",
                "band_names": band_names,
            },
        ],
        "notebook_family_statuses": [
            {
                "family": "NANO_STACK",
                "status": "deferred",
                "reason": "Cells 36-37 are duplicate nano-scale variants with unstable internals and no single canonical formula yet.",
            },
            {
                "family": "SIGMA0_MASTER_640",
                "status": "implemented",
                "artifact_name": "radar_linear_support_stack",
                "reason": "Neutral linearized radar support stack captures the reproducible sigma0-style variant without notebook master naming.",
            },
            {
                "family": "GPHYS_MASTER_640",
                "status": "deferred",
                "reason": "Geophysics master formulas remain domain-specific and need a canonical neutral formula capture before implementation.",
            },
            {
                "family": "RAD_MASTER_CUBE_640",
                "status": "deferred",
                "reason": "The notebook radar master cube is a near-duplicate assembly of existing science-core radar layers without a distinct stable contract.",
            },
            {
                "family": "ULTIMATE_GPHYS_SCAN_640",
                "status": "deferred",
                "reason": "The notebook averages multiple geophysics scans with unstable composition and needs a fixed reproducible definition.",
            },
            {
                "family": "TESLA_V7_2_VARIANTS",
                "status": "implemented_subset",
                "artifact_name": "ai_ready_support_stack",
                "reason": "F2 implements the useful grid-locked tensor-export subset only; Tesla inference and target-oriented variants remain out of scope.",
            },
        ],
    }
    tensor_audit_summary = {
        "stage": "feature_stacks",
        "shape": [int(cube.shape[0]), int(cube.shape[1]), int(cube.shape[2])],
        "dtype": str(cube.dtype),
        "valid_fraction_min": round(min(float((cube[:, :, i] != nodata).mean()) for i in range(cube.shape[-1])), 6),
        "valid_fraction_max": round(max(float((cube[:, :, i] != nodata).mean()) for i in range(cube.shape[-1])), 6),
        "s2_mask_valid_fraction": round(float(s2_mask.mean()), 6),
    }
    geometry_consistency_summary = {
        "stage": "feature_stacks",
        "all_sources_grid_aligned": True,
        "source_count": len(band_names),
        "stack_shape": [int(cube.shape[0]), int(cube.shape[1]), int(cube.shape[2])],
    }

    return {
        "band_names": band_names,
        "cube": cube,
        "s2_mask": s2_mask,
        "radar_linear_band_names": ["vv_sigma0_linear", "vh_sigma0_linear", "ratio_sigma0_linear", "incidence_angle"],
        "radar_linear_stack": radar_linear_stack,
        "radar_db_band_names": ["VV_dB", "VH_dB", "logRatio_dB", "angle"],
        "radar_db_stack": radar_db_stack,
        "ai_ready_stack": ai_ready_stack,
        "band_stats_rows": stats_rows,
        "stack_presence_summary": stack_presence_summary,
        "tensor_audit_summary": tensor_audit_summary,
        "geometry_consistency_summary": geometry_consistency_summary,
    }


def write_feature_stack_outputs(run_dir: Path, grid_spec: GridSpec, products: dict[str, object]) -> dict[str, Path]:
    cube = products["cube"]
    s2_mask = products["s2_mask"]
    radar_linear_stack = products["radar_linear_stack"]
    radar_db_stack = products["radar_db_stack"]
    ai_ready_stack = products["ai_ready_stack"]
    band_stats_rows = products["band_stats_rows"]
    stack_presence_summary = products["stack_presence_summary"]
    tensor_audit_summary = products["tensor_audit_summary"]
    geometry_consistency_summary = products["geometry_consistency_summary"]
    assert isinstance(cube, np.ndarray)
    assert isinstance(s2_mask, np.ndarray)
    assert isinstance(radar_linear_stack, np.ndarray)
    assert isinstance(radar_db_stack, np.ndarray)
    assert isinstance(ai_ready_stack, np.ndarray)
    assert isinstance(band_stats_rows, list)
    assert isinstance(stack_presence_summary, dict)
    assert isinstance(tensor_audit_summary, dict)
    assert isinstance(geometry_consistency_summary, dict)

    tensor_dir = run_dir / "stacks" / "tensor_support"
    optical_dir = run_dir / "stacks" / "optical_support"
    qa_dir = ensure_run_qa_dir(run_dir) / "stacks"
    notebook_stack_dir = run_dir / NOTEBOOK_STACK_OUTPUT_DIR
    tensor_dir.mkdir(parents=True, exist_ok=True)
    optical_dir.mkdir(parents=True, exist_ok=True)
    qa_dir.mkdir(parents=True, exist_ok=True)
    notebook_stack_dir.mkdir(parents=True, exist_ok=True)

    stack_tif_path = tensor_dir / SCIENCE_CORE_STACK_TIF
    stack_npy_path = tensor_dir / SCIENCE_CORE_STACK_NPY
    radar_linear_tif_path = tensor_dir / RADAR_LINEAR_SUPPORT_STACK_TIF
    radar_linear_npy_path = tensor_dir / RADAR_LINEAR_SUPPORT_STACK_NPY
    radar_db_tif_path = tensor_dir / RADAR_DB_SUPPORT_STACK_TIF
    radar_db_npy_path = tensor_dir / RADAR_DB_SUPPORT_STACK_NPY
    ai_ready_tif_path = tensor_dir / AI_READY_SUPPORT_STACK_TIF
    ai_ready_npy_path = tensor_dir / AI_READY_SUPPORT_STACK_NPY
    s2_mask_path = optical_dir / S2_MASK_SUPPORT_TIF
    band_stats_path = qa_dir / BAND_STATS_CSV
    stack_presence_path = qa_dir / STACK_PRESENCE_SUMMARY_JSON
    tensor_audit_path = qa_dir / TENSOR_AUDIT_SUMMARY_JSON
    geometry_summary_path = qa_dir / GEOMETRY_CONSISTENCY_SUMMARY_JSON
    notebook_radar_stack_npy_path = notebook_stack_dir / NOTEBOOK_RADAR_STACK_NPY

    _save_multipage_tiff(stack_tif_path, cube)
    np.save(stack_npy_path, cube)
    _save_multipage_tiff(radar_linear_tif_path, radar_linear_stack)
    np.save(radar_linear_npy_path, radar_linear_stack)
    np.save(notebook_radar_stack_npy_path, radar_linear_stack)
    write_georeferenced_raster(radar_db_tif_path, radar_db_stack, grid_spec)
    np.save(radar_db_npy_path, radar_db_stack)
    _save_multipage_tiff(ai_ready_tif_path, ai_ready_stack)
    np.save(ai_ready_npy_path, ai_ready_stack)
    Image.fromarray(s2_mask.astype(np.float32)).save(s2_mask_path, format="TIFF")
    write_raster_sidecar(
        stack_tif_path,
        grid_manifest=grid_spec.manifest,
        nodata=grid_spec.nodata,
        dtype="float32",
        shape=cube.shape[:2],
    )
    write_raster_sidecar(
        radar_linear_tif_path,
        grid_manifest=grid_spec.manifest,
        nodata=grid_spec.nodata,
        dtype="float32",
        shape=radar_linear_stack.shape[:2],
    )
    write_raster_sidecar(
        radar_db_tif_path,
        grid_manifest=grid_spec.manifest,
        nodata=grid_spec.nodata,
        dtype="float32",
        shape=radar_db_stack.shape[:2],
    )
    write_raster_sidecar(
        ai_ready_tif_path,
        grid_manifest=grid_spec.manifest,
        nodata=grid_spec.nodata,
        dtype="float32",
        shape=ai_ready_stack.shape[:2],
    )
    write_raster_sidecar(
        s2_mask_path,
        grid_manifest=grid_spec.manifest,
        nodata=grid_spec.nodata,
        dtype="float32",
        shape=s2_mask.shape,
    )

    _write_csv(
        band_stats_path,
        ["band_index", "band_name", "source_file", "valid_count", "nodata_count", "min", "max", "mean"],
        band_stats_rows,
    )
    stack_presence_path.write_text(json.dumps(stack_presence_summary, indent=2, sort_keys=True), encoding="utf-8")
    tensor_audit_path.write_text(json.dumps(tensor_audit_summary, indent=2, sort_keys=True), encoding="utf-8")
    geometry_summary_path.write_text(json.dumps(geometry_consistency_summary, indent=2, sort_keys=True), encoding="utf-8")

    return {
        "stack_tif": stack_tif_path,
        "stack_npy": stack_npy_path,
        "radar_linear_tif": radar_linear_tif_path,
        "radar_linear_npy": radar_linear_npy_path,
        "radar_db_tif": radar_db_tif_path,
        "radar_db_npy": radar_db_npy_path,
        "ai_ready_tif": ai_ready_tif_path,
        "ai_ready_npy": ai_ready_npy_path,
        "s2_mask_tif": s2_mask_path,
        "band_stats_csv": band_stats_path,
        "stack_presence_summary_json": stack_presence_path,
        "tensor_audit_summary_json": tensor_audit_path,
        "geometry_consistency_summary_json": geometry_summary_path,
        "notebook_radar_stack_npy": notebook_radar_stack_npy_path,
    }


class FeatureStacksStage(Stage):
    name = "feature_stacks"
    parity_category = ParityCategory.PARITY_REPRODUCES

    def __init__(self, *, grid_spec: GridSpec) -> None:
        self.grid_spec = grid_spec

    async def run(self, context: StageContext) -> StageResult:
        source_layers = collect_science_core_layers(context.run_dir, self.grid_spec)
        products = build_feature_stack_products(source_layers, nodata=self.grid_spec.nodata)
        outputs = write_feature_stack_outputs(context.run_dir, self.grid_spec, products)
        artifacts = [
            build_stage_artifact(
                name="science_core_stack_tif",
                relative_path=outputs["stack_tif"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["stack_tif"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="science_core_stack_npy",
                relative_path=outputs["stack_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["stack_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="radar_linear_support_stack_tif",
                relative_path=outputs["radar_linear_tif"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["radar_linear_tif"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="radar_linear_support_stack_npy",
                relative_path=outputs["radar_linear_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["radar_linear_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="radar_db_support_stack_tif",
                relative_path=outputs["radar_db_tif"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["radar_db_tif"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="radar_db_support_stack_npy",
                relative_path=outputs["radar_db_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["radar_db_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="ai_ready_support_stack_tif",
                relative_path=outputs["ai_ready_tif"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["ai_ready_tif"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="ai_ready_support_stack_npy",
                relative_path=outputs["ai_ready_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["ai_ready_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="s2_mask_support_valid",
                relative_path=outputs["s2_mask_tif"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["s2_mask_tif"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="band_stats",
                relative_path=outputs["band_stats_csv"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["band_stats_csv"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="stack_presence_summary",
                relative_path=outputs["stack_presence_summary_json"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["stack_presence_summary_json"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="tensor_audit_summary",
                relative_path=outputs["tensor_audit_summary_json"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["tensor_audit_summary_json"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="geometry_consistency_summary",
                relative_path=outputs["geometry_consistency_summary_json"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["geometry_consistency_summary_json"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="notebook_RADAR_STACK_HWC_640_npy",
                relative_path=outputs["notebook_radar_stack_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["notebook_radar_stack_npy"].stat().st_size,
                http_servable=False,
            ),
        ]
        band_names = products["band_names"]
        assert isinstance(band_names, list)
        return StageResult(
            artifacts=artifacts,
            metadata={
                "band_names": band_names,
                "band_count": len(band_names),
                "stack_shape": [self.grid_spec.size, self.grid_spec.size, len(band_names)],
            },
        )
