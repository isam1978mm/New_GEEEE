from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

import numpy as np
import rasterio
from PIL import Image

from app.db.models.enums import ArtifactClass
from app.errors import StageError
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.qa_paths import ensure_run_qa_dir
from app.pipeline.stages.dem import raster_sidecar_path, write_georeferenced_raster, write_raster_sidecar
from app.pipeline.stages.grid import GridSpec
from app.services.storage import read_manifest

HYPERCUBE_TIF_NAME = "hypercube.tif"
HYPERCUBE_NPY_NAME = "hypercube.npy"
HYPERCUBE_BAND_ORDER_NAME = "hypercube_band_order.csv"
HYPERCUBE_STATS_NAME = "hypercube_band_stats.csv"
HYPERCUBE_NORM_PARAMS_NAME = "hypercube_norm_params.csv"
HYPERCUBE_AUDIT_NAME = "hypercube_audit.csv"
NOTEBOOK_STACK_OUTPUT_DIR = "NPY_STACKS"
NOTEBOOK_HYPERCUBE_TIF_NAME = "FINAL_TESLA_V7_2_HYPERCUBE.tif"
NOTEBOOK_HYPERCUBE_NPY_NAME = "FINAL_TESLA_V7_2_HYPERCUBE.npy"
NOTEBOOK_HYPERCUBE_PATCHED_14B_NAME = "FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif"
NOTEBOOK_PATCHED_14B_STATUS = "implemented"
NOTEBOOK_FINAL_TESLA_STATUS = "implemented"
NOTEBOOK_FINAL_TESLA_SOURCE_FAMILY = "notebook_secret_report_fusion_v1"
NOTEBOOK_PATCHED_14B_REASON = (
    "Frozen notebook FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B is a 13-band patched stack. "
    "Its AI_READY_640_EM_Anomaly band is sourced from DEM_640.tif per the notebook patch report, and "
    "AI_READY_640_Magnetic_Anomaly remains unavailable."
)
NOTEBOOK_FINAL_TESLA_LAYER_ORDER: tuple[tuple[str, str], ...] = (
    ("AI_READY_640_Secret_Gold_Halo", "AI_READY_640/AI_READY_640_Secret_Gold_Halo.tif"),
    ("AI_READY_640_Secret_Silver_Oxide", "AI_READY_640/AI_READY_640_Secret_Silver_Oxide.tif"),
    ("AI_READY_640_Secret_Tunnel_Ceiling", "AI_READY_640/AI_READY_640_Secret_Tunnel_Ceiling.tif"),
    ("AI_READY_640_Secret_Thermal_Inertia", "AI_READY_640/AI_READY_640_Secret_Thermal_Inertia.tif"),
    ("AI_READY_640_Secret_Chemical_Protector", "AI_READY_640/AI_READY_640_Secret_Chemical_Protector.tif"),
    ("AI_READY_640_Secret_Hidden_Doors", "AI_READY_640/AI_READY_640_Secret_Hidden_Doors.tif"),
    ("REPORT_640_FINAL_Zero_Point_Targets", "REPORT_640_FINAL_Zero_Point_Targets.tif"),
    ("REPORT_640_Mass_Report", "REPORT_640_Mass_Report.tif"),
    ("REPORT_640_Pottery_Report", "REPORT_640_Pottery_Report.tif"),
)
NOTEBOOK_PATCHED_14B_LAYER_ORDER: tuple[tuple[str, str], ...] = (
    *NOTEBOOK_FINAL_TESLA_LAYER_ORDER,
    ("AI_READY_640_EM_Anomaly", "DEM_GEO8_TIFS/DEM_640.tif"),
    ("DEM_Slope", "DEM_GEO8_TIFS/slope_deg_640.tif"),
    ("DEM_TPI", "DEM_GEO8_TIFS/tpi_100m_640.tif"),
    ("DEM_Roughness", "DEM_GEO8_TIFS/roughness_100m_640.tif"),
)
NOTEBOOK_PATCHED_14B_BAND_DESCRIPTIONS: tuple[str, ...] = (
    "Secret_Gold_Halo",
    "Secret_Silver_Oxide",
    "Secret_Tunnel_Ceiling",
    "Secret_Thermal_Inertia",
    "Secret_Chemical_Protector",
    "Secret_Hidden_Doors",
    "REPORT_640_FINAL_Zero_Point_Targets",
    "REPORT_640_Mass_Report",
    "REPORT_640_Pottery_Report",
    "AI_READY_640_EM_Anomaly",
    "DEM_Slope",
    "DEM_TPI",
    "DEM_Roughness",
)
NOTEBOOK_PATCHED_14B_ACTUAL_BAND_COUNT = len(NOTEBOOK_PATCHED_14B_LAYER_ORDER)
EXCLUDED_TIFS = {HYPERCUBE_TIF_NAME, "pca_anomaly.tif"}
EPS = 1e-6
VALID_MASK_POLICY = "all_feature_channels_finite"


def _read_single_band_tif(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.array(image, dtype=np.float32)


def collect_hypercube_sources(run_dir: Path) -> list[Path]:
    return sorted(path for path in run_dir.glob("*.tif") if path.name not in EXCLUDED_TIFS)


def _validate_source_sidecar(path: Path, grid_spec: GridSpec) -> dict[str, object]:
    sidecar_path = raster_sidecar_path(path)
    if not sidecar_path.is_file():
        raise StageError(f"Missing raster sidecar for hypercube source: {path.name}")
    sidecar = read_manifest(sidecar_path)
    if sidecar["crs"] != grid_spec.crs:
        raise StageError(f"Hypercube source CRS mismatch: {path.name}")
    if [float(value) for value in sidecar["transform"]] != [float(value) for value in grid_spec.manifest.crs_transform]:
        raise StageError(f"Hypercube source transform mismatch: {path.name}")
    if (int(sidecar["height"]), int(sidecar["width"])) != (grid_spec.size, grid_spec.size):
        raise StageError(f"Hypercube source size mismatch: {path.name}")
    return sidecar


def build_hypercube_products(
    source_layers: list[tuple[str, np.ndarray]],
    *,
    nodata: float,
) -> dict[str, object]:
    if not source_layers:
        raise StageError("Hypercube assembly requires at least one source TIFF.")

    source_band_names = [name for name, _array in source_layers]
    layers = [array.astype(np.float32, copy=True) for _name, array in source_layers]
    cube_source = np.stack(layers, axis=-1).astype(np.float32)
    cube_source[cube_source == nodata] = np.nan
    cube_source[~np.isfinite(cube_source)] = np.nan

    mask_any = np.isfinite(cube_source).any(axis=-1).astype(np.uint8)
    mask_all = np.isfinite(cube_source).all(axis=-1).astype(np.uint8)
    cube_clean = cube_source.copy().astype(np.float32)

    channel_count = cube_source.shape[-1]
    cube_norm = np.full_like(cube_source, np.nan, dtype=np.float32)
    medians = np.zeros((channel_count,), dtype=np.float32)
    iqrs = np.zeros((channel_count,), dtype=np.float32)

    for index in range(channel_count):
        channel = cube_source[:, :, index]
        finite = np.isfinite(channel)
        valid = channel[finite]
        if valid.size < 100:
            med = 0.0
            iqr = 1.0
        else:
            med = float(np.median(valid))
            q25 = float(np.percentile(valid, 25))
            q75 = float(np.percentile(valid, 75))
            iqr = max(q75 - q25, EPS)
        medians[index] = np.float32(med)
        iqrs[index] = np.float32(iqr)
        normalized = np.full(channel.shape, np.nan, dtype=np.float32)
        normalized[finite] = np.clip((channel[finite] - med) / iqr, -8.0, 8.0).astype(np.float32)
        cube_norm[:, :, index] = normalized

    cube_norm_plus_mask = np.concatenate([cube_norm, mask_all[:, :, None].astype(np.float32)], axis=-1)
    cube_out = np.where(np.isfinite(cube_norm_plus_mask), cube_norm_plus_mask, nodata).astype(np.float32)
    persisted_band_names = [*source_band_names, "valid_mask"]

    return {
        "source_band_names": source_band_names,
        "band_names": persisted_band_names,
        "cube_raw": cube_out,
        "cube_clean": cube_clean,
        "cube_norm": cube_norm,
        "cube_norm_plus_mask": cube_norm_plus_mask,
        "mask_any": mask_any,
        "mask_all": mask_all,
        "medians": medians,
        "iqrs": iqrs,
        "valid_mask_policy": VALID_MASK_POLICY,
    }


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def remove_stale_notebook_final_tesla_outputs(run_dir: Path) -> None:
    notebook_stack_dir = run_dir / NOTEBOOK_STACK_OUTPUT_DIR
    for filename in (
        NOTEBOOK_HYPERCUBE_TIF_NAME,
        NOTEBOOK_HYPERCUBE_NPY_NAME,
        NOTEBOOK_HYPERCUBE_PATCHED_14B_NAME,
    ):
        path = notebook_stack_dir / filename
        sidecar = raster_sidecar_path(path)
        if path.exists():
            path.unlink()
        if sidecar.exists():
            sidecar.unlink()


def _load_named_source_layers(
    run_dir: Path,
    grid_spec: GridSpec,
    source_order: tuple[tuple[str, str], ...],
) -> tuple[list[tuple[str, np.ndarray]], list[str]]:
    source_layers: list[tuple[str, np.ndarray]] = []
    missing_paths: list[str] = []
    for band_name, relative_path in source_order:
        path = run_dir / relative_path
        if not path.is_file():
            missing_paths.append(relative_path)
            continue
        sidecar = _validate_source_sidecar(path, grid_spec)
        array = _read_single_band_tif(path)
        nodata = float(sidecar["nodata"])
        array = np.where(array == nodata, grid_spec.nodata, array).astype(np.float32, copy=False)
        source_layers.append((band_name, array))
    return source_layers, missing_paths


def load_notebook_final_tesla_source_layers(run_dir: Path, grid_spec: GridSpec) -> tuple[list[tuple[str, np.ndarray]], list[str]]:
    return _load_named_source_layers(run_dir, grid_spec, NOTEBOOK_FINAL_TESLA_LAYER_ORDER)


def load_notebook_patched_14b_source_layers(run_dir: Path, grid_spec: GridSpec) -> tuple[list[tuple[str, np.ndarray]], list[str]]:
    return _load_named_source_layers(run_dir, grid_spec, NOTEBOOK_PATCHED_14B_LAYER_ORDER)


def write_notebook_final_tesla_outputs(
    run_dir: Path,
    grid_spec: GridSpec,
    source_layers: list[tuple[str, np.ndarray]],
) -> dict[str, Path]:
    notebook_stack_dir = run_dir / NOTEBOOK_STACK_OUTPUT_DIR
    notebook_stack_dir.mkdir(parents=True, exist_ok=True)
    tif_path = notebook_stack_dir / NOTEBOOK_HYPERCUBE_TIF_NAME
    npy_path = notebook_stack_dir / NOTEBOOK_HYPERCUBE_NPY_NAME

    band_names = [name for name, _array in source_layers]
    hwc = np.stack([array for _name, array in source_layers], axis=-1).astype(np.float32, copy=False)
    chw = np.stack([array for _name, array in source_layers], axis=0).astype(np.float32, copy=False)
    # Preserve notebook CHW arrays as-is, but encode non-finite TIFF pixels with the
    # dataset nodata sentinel so GeoTIFF masks match the frozen notebook export.
    tif_hwc = np.where(np.isfinite(hwc), hwc, grid_spec.nodata).astype(np.float32, copy=False)

    write_georeferenced_raster(tif_path, tif_hwc, grid_spec)
    write_raster_sidecar(
        tif_path,
        grid_manifest=grid_spec.manifest,
        nodata=grid_spec.nodata,
        dtype="float32",
        shape=hwc.shape[:2],
    )
    with rasterio.open(tif_path, "r+") as dataset:
        for band_index, band_name in enumerate(band_names, start=1):
            dataset.set_band_description(band_index, band_name)
    np.save(npy_path, chw)

    return {
        "final_tesla_tif": tif_path,
        "final_tesla_npy": npy_path,
    }


def write_notebook_patched_14b_output(
    run_dir: Path,
    grid_spec: GridSpec,
    source_layers: list[tuple[str, np.ndarray]],
) -> Path:
    notebook_stack_dir = run_dir / NOTEBOOK_STACK_OUTPUT_DIR
    notebook_stack_dir.mkdir(parents=True, exist_ok=True)
    tif_path = notebook_stack_dir / NOTEBOOK_HYPERCUBE_PATCHED_14B_NAME

    hwc = np.stack([array for _name, array in source_layers], axis=-1).astype(np.float32, copy=False)
    tif_hwc = np.where(np.isfinite(hwc), hwc, grid_spec.nodata).astype(np.float32, copy=False)

    write_georeferenced_raster(tif_path, tif_hwc, grid_spec)
    write_raster_sidecar(
        tif_path,
        grid_manifest=grid_spec.manifest,
        nodata=grid_spec.nodata,
        dtype="float32",
        shape=hwc.shape[:2],
    )
    with rasterio.open(tif_path, "r+") as dataset:
        for band_index, band_name in enumerate(NOTEBOOK_PATCHED_14B_BAND_DESCRIPTIONS, start=1):
            dataset.set_band_description(band_index, band_name)

    return tif_path


def write_hypercube_outputs(run_dir: Path, grid_spec: GridSpec, products: dict[str, object]) -> dict[str, Path]:
    cube_raw = products["cube_raw"]
    assert isinstance(cube_raw, np.ndarray)
    band_names = products["band_names"]
    assert isinstance(band_names, list)
    source_band_names = products["source_band_names"]
    assert isinstance(source_band_names, list)

    tif_path = run_dir / HYPERCUBE_TIF_NAME
    npy_path = run_dir / HYPERCUBE_NPY_NAME
    order_path = run_dir / HYPERCUBE_BAND_ORDER_NAME
    stats_path = run_dir / HYPERCUBE_STATS_NAME
    norm_params_path = run_dir / HYPERCUBE_NORM_PARAMS_NAME
    audit_path = ensure_run_qa_dir(run_dir) / "parity" / HYPERCUBE_AUDIT_NAME
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    write_georeferenced_raster(tif_path, cube_raw, grid_spec)
    np.save(npy_path, cube_raw)
    write_raster_sidecar(
        tif_path,
        grid_manifest=grid_spec.manifest,
        nodata=grid_spec.nodata,
        dtype="float32",
        shape=cube_raw.shape[:2],
    )

    order_rows = [
        {"band_index": index, "band_name": name, "source_file": f"{name}.tif"}
        for index, name in enumerate(source_band_names)
    ]
    order_rows.append(
        {
            "band_index": len(source_band_names),
            "band_name": "valid_mask",
            "source_file": "generated",
        }
    )
    _write_csv(order_path, ["band_index", "band_name", "source_file"], order_rows)

    cube_norm = products["cube_norm"]
    assert isinstance(cube_norm, np.ndarray)
    stats_rows = []
    for index, name in enumerate(source_band_names):
        channel = cube_norm[:, :, index]
        valid = channel[np.isfinite(channel)]
        stats_rows.append(
            {
                "band_name": name,
                "source_file": f"{name}.tif",
                "valid_px": int(valid.size),
                "nan_px": int(np.isnan(channel).sum()),
                "min": float(np.nanmin(channel)) if valid.size else "",
                "max": float(np.nanmax(channel)) if valid.size else "",
                "mean": float(np.nanmean(channel)) if valid.size else "",
                "std": float(np.nanstd(channel)) if valid.size else "",
                "median": float(np.nanmedian(channel)) if valid.size else "",
                "iqr": float(np.nanpercentile(channel, 75) - np.nanpercentile(channel, 25)) if valid.size else "",
            }
        )
    _write_csv(stats_path, list(stats_rows[0].keys()) if stats_rows else ["band_name"], stats_rows)

    medians = products["medians"]
    iqrs = products["iqrs"]
    assert isinstance(medians, np.ndarray)
    assert isinstance(iqrs, np.ndarray)
    _write_csv(
        norm_params_path,
        ["band_index", "band_name", "median", "iqr"],
        (
            {
                "band_index": index,
                "band_name": name,
                "median": float(medians[index]),
                "iqr": float(iqrs[index]),
            }
            for index, name in enumerate(source_band_names)
        ),
    )

    cube_norm_plus_mask = products["cube_norm_plus_mask"]
    assert isinstance(cube_norm_plus_mask, np.ndarray)
    audit_rows = []
    for index, name in enumerate(band_names):
        channel = cube_norm_plus_mask[:, :, index]
        finite = np.isfinite(channel)
        values = channel[finite]
        audit_rows.append(
            {
                "band_index": index,
                "band_name": name,
                "valid_fraction": float(finite.mean()) if finite.size else 0.0,
                "min": float(values.min()) if values.size else "",
                "max": float(values.max()) if values.size else "",
                "mean": float(values.mean()) if values.size else "",
                "std": float(values.std()) if values.size else "",
            }
        )
    _write_csv(audit_path, ["band_index", "band_name", "valid_fraction", "min", "max", "mean", "std"], audit_rows)

    return {
        "hypercube_tif": tif_path,
        "hypercube_npy": npy_path,
        "band_order_csv": order_path,
        "band_stats_csv": stats_path,
        "norm_params_csv": norm_params_path,
        "audit_csv": audit_path,
    }


class HypercubeStage(Stage):
    name = "hypercube"
    parity_category = ParityCategory.PARITY_REPRODUCES

    def __init__(self, *, grid_spec: GridSpec) -> None:
        self.grid_spec = grid_spec

    async def run(self, context: StageContext) -> StageResult:
        remove_stale_notebook_final_tesla_outputs(context.run_dir)
        sources = collect_hypercube_sources(context.run_dir)
        source_layers: list[tuple[str, np.ndarray]] = []
        for path in sources:
            sidecar = _validate_source_sidecar(path, self.grid_spec)
            array = _read_single_band_tif(path)
            nodata = float(sidecar["nodata"])
            array = np.where(array == nodata, self.grid_spec.nodata, array).astype(np.float32)
            source_layers.append((path.stem, array))

        products = build_hypercube_products(source_layers, nodata=self.grid_spec.nodata)
        outputs = write_hypercube_outputs(context.run_dir, self.grid_spec, products)
        notebook_source_layers, missing_notebook_sources = load_notebook_final_tesla_source_layers(
            context.run_dir,
            self.grid_spec,
        )
        notebook_outputs: dict[str, Path] | None = None
        notebook_patched_14b_tif: Path | None = None
        if not missing_notebook_sources and len(notebook_source_layers) == len(NOTEBOOK_FINAL_TESLA_LAYER_ORDER):
            notebook_outputs = write_notebook_final_tesla_outputs(context.run_dir, self.grid_spec, notebook_source_layers)
        patched_source_layers, missing_patched_sources = load_notebook_patched_14b_source_layers(context.run_dir, self.grid_spec)
        if not missing_patched_sources and len(patched_source_layers) == NOTEBOOK_PATCHED_14B_ACTUAL_BAND_COUNT:
            notebook_patched_14b_tif = write_notebook_patched_14b_output(context.run_dir, self.grid_spec, patched_source_layers)

        artifacts = [
            build_stage_artifact(
                name="hypercube_tif",
                relative_path=outputs["hypercube_tif"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=outputs["hypercube_tif"].stat().st_size,
            ),
            build_stage_artifact(
                name="hypercube_npy",
                relative_path=outputs["hypercube_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=outputs["hypercube_npy"].stat().st_size,
            ),
            build_stage_artifact(
                name="hypercube_band_order",
                relative_path=outputs["band_order_csv"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=outputs["band_order_csv"].stat().st_size,
            ),
            build_stage_artifact(
                name="hypercube_band_stats",
                relative_path=outputs["band_stats_csv"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=outputs["band_stats_csv"].stat().st_size,
            ),
            build_stage_artifact(
                name="hypercube_norm_params",
                relative_path=outputs["norm_params_csv"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=outputs["norm_params_csv"].stat().st_size,
            ),
            build_stage_artifact(
                name="hypercube_audit",
                relative_path=outputs["audit_csv"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["audit_csv"].stat().st_size,
                http_servable=False,
            ),
        ]
        if notebook_outputs is not None:
            artifacts.extend(
                [
                    build_stage_artifact(
                        name="notebook_FINAL_TESLA_V7_2_HYPERCUBE_tif",
                        relative_path=notebook_outputs["final_tesla_tif"].relative_to(context.run_dir).as_posix(),
                        artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                        size_bytes=notebook_outputs["final_tesla_tif"].stat().st_size,
                    ),
                    build_stage_artifact(
                        name="notebook_FINAL_TESLA_V7_2_HYPERCUBE_npy",
                        relative_path=notebook_outputs["final_tesla_npy"].relative_to(context.run_dir).as_posix(),
                        artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                        size_bytes=notebook_outputs["final_tesla_npy"].stat().st_size,
                    ),
                ]
            )
        if notebook_patched_14b_tif is not None:
            artifacts.append(
                build_stage_artifact(
                    name="notebook_FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B_tif",
                    relative_path=notebook_patched_14b_tif.relative_to(context.run_dir).as_posix(),
                    artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                    size_bytes=notebook_patched_14b_tif.stat().st_size,
                )
            )
        band_names = products["band_names"]
        assert isinstance(band_names, list)
        notebook_output_statuses: list[dict[str, object]]
        if notebook_outputs is not None:
            source_layer_order = [name for name, _relative_path in NOTEBOOK_FINAL_TESLA_LAYER_ORDER]
            notebook_output_statuses = [
                {
                    "filename": NOTEBOOK_HYPERCUBE_TIF_NAME,
                    "status": NOTEBOOK_FINAL_TESLA_STATUS,
                    "source_family": NOTEBOOK_FINAL_TESLA_SOURCE_FAMILY,
                    "source_layer_order": source_layer_order,
                },
                {
                    "filename": NOTEBOOK_HYPERCUBE_NPY_NAME,
                    "status": NOTEBOOK_FINAL_TESLA_STATUS,
                    "source_family": NOTEBOOK_FINAL_TESLA_SOURCE_FAMILY,
                    "source_layer_order": source_layer_order,
                    "layout": "CHW",
                },
            ]
            if notebook_patched_14b_tif is not None:
                patched_layer_order = [name for name, _relative_path in NOTEBOOK_PATCHED_14B_LAYER_ORDER]
                notebook_output_statuses.append(
                    {
                        "filename": NOTEBOOK_HYPERCUBE_PATCHED_14B_NAME,
                        "status": NOTEBOOK_PATCHED_14B_STATUS,
                        "source_family": f"{NOTEBOOK_FINAL_TESLA_SOURCE_FAMILY}_patched_v2",
                        "source_layer_order": patched_layer_order,
                        "actual_band_count": NOTEBOOK_PATCHED_14B_ACTUAL_BAND_COUNT,
                        "note": "Filename says 14B, but the frozen notebook artifact contains 13 bands.",
                        "em_anomaly_source_equivalent": "DEM_GEO8_TIFS/DEM_640.tif",
                        "reason": NOTEBOOK_PATCHED_14B_REASON,
                    }
                )
            else:
                notebook_output_statuses.append(
                    {
                        "filename": NOTEBOOK_HYPERCUBE_PATCHED_14B_NAME,
                        "status": "not_implemented_no_source_equivalent",
                        "reason": NOTEBOOK_PATCHED_14B_REASON,
                    }
                )
        else:
            missing_summary = ", ".join(missing_notebook_sources) if missing_notebook_sources else "unknown notebook source gap"
            missing_reason = (
                "Notebook FINAL_TESLA hypercube requires 6 AI_READY_640_Secret_* layers and 3 REPORT_640_* rasters; "
                f"missing required source rasters in current run: {missing_summary}."
            )
            notebook_output_statuses = [
                {
                    "filename": NOTEBOOK_HYPERCUBE_TIF_NAME,
                    "status": "not_implemented_no_source_equivalent",
                    "reason": missing_reason,
                },
                {
                    "filename": NOTEBOOK_HYPERCUBE_NPY_NAME,
                    "status": "not_implemented_no_source_equivalent",
                    "reason": missing_reason,
                },
                {
                    "filename": NOTEBOOK_HYPERCUBE_PATCHED_14B_NAME,
                    "status": "not_implemented_no_source_equivalent",
                    "reason": NOTEBOOK_PATCHED_14B_REASON,
                },
            ]
        return StageResult(
            artifacts=artifacts,
            metadata={
                "band_names": band_names,
                "band_count": len(band_names),
                "shape": [self.grid_spec.size, self.grid_spec.size, len(band_names)],
                "valid_mask_policy": str(products.get("valid_mask_policy", VALID_MASK_POLICY)),
                "notebook_output_statuses": notebook_output_statuses,
            },
        )
