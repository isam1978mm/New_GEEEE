from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from app.db.models.enums import ArtifactClass
from app.errors import StageError
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.qa_paths import ensure_run_qa_dir
from app.pipeline.stages.dem import write_georeferenced_raster, write_raster_sidecar
from app.pipeline.stages.grid import GridSpec
from app.pipeline.stages.s2_indices import S2_SOURCE_BANDS, S2_RAW_CUBE_NPY_NAME
from app.pipeline.stages.thermal import RAW_ST_B10_NPY_NAME

EPS = 1e-10
REPORT_640_MANIFEST_NAME = "REPORT_640_manifest.json"

_S2_BAND_INDEX = {name: index for index, name in enumerate(S2_SOURCE_BANDS)}


def load_s2_raw_cube(run_dir: Path) -> np.ndarray:
    path = run_dir / S2_RAW_CUBE_NPY_NAME
    if not path.is_file():
        raise StageError("S2 raw band cube is required before report_640 stage.")
    return np.load(path)


def load_st_b10_raw(run_dir: Path) -> np.ndarray:
    path = run_dir / RAW_ST_B10_NPY_NAME
    if not path.is_file():
        raise StageError("Raw ST_B10 source is required before report_640 stage.")
    return np.load(path)


def compute_report_pottery_report(s2_cube: np.ndarray, *, nodata: float) -> np.ndarray:
    """B12 / B11"""
    b12 = s2_cube[:, :, _S2_BAND_INDEX["B12"]]
    b11 = s2_cube[:, :, _S2_BAND_INDEX["B11"]]
    valid = (b12 != nodata) & (b11 != nodata) & np.isfinite(b12) & np.isfinite(b11) & (b11 != 0.0)
    result = np.full(b12.shape, nodata, dtype=np.float32)
    result[valid] = (b12[valid] / b11[valid]).astype(np.float32)
    return result


def compute_report_mass_report(s2_cube: np.ndarray, st_b10_raw: np.ndarray, *, nodata: float) -> np.ndarray:
    """B12 * ST_B10 / 1000"""
    b12 = s2_cube[:, :, _S2_BAND_INDEX["B12"]]
    valid = (
        (b12 != nodata)
        & (st_b10_raw != nodata)
        & np.isfinite(b12)
        & np.isfinite(st_b10_raw)
    )
    result = np.full(b12.shape, nodata, dtype=np.float32)
    result[valid] = ((b12[valid] * st_b10_raw[valid]) / np.float32(1000.0)).astype(np.float32)
    return result


def compute_report_zero_point_targets(s2_cube: np.ndarray, *, nodata: float) -> np.ndarray:
    """Threshold intersection of behavior tensors derived from S2 raw bands."""
    b12 = s2_cube[:, :, _S2_BAND_INDEX["B12"]]
    b11 = s2_cube[:, :, _S2_BAND_INDEX["B11"]]
    b4 = s2_cube[:, :, _S2_BAND_INDEX["B4"]]
    b3 = s2_cube[:, :, _S2_BAND_INDEX["B3"]]
    b8 = s2_cube[:, :, _S2_BAND_INDEX["B8"]]

    valid = (
        (b12 != nodata) & (b11 != nodata) & (b4 != nodata) & (b3 != nodata) & (b8 != nodata)
        & np.isfinite(b12) & np.isfinite(b11) & np.isfinite(b4) & np.isfinite(b3) & np.isfinite(b8)
        & (b11 != 0.0) & (b3 != 0.0) & ((b8 + b4) != 0.0)
    )

    # AI_BEH_GoldAlloy_Signal = B12 / B11 > 1.45
    gold_alloy = np.full(b12.shape, 0.0, dtype=np.float32)
    gold_alloy[valid] = (b12[valid] / b11[valid]).astype(np.float32)
    cond1 = (gold_alloy > 1.45) & valid

    # AI_BEH_IronOxide_Hardness = B4 / B3 > 1.25
    iron_oxide = np.full(b12.shape, 0.0, dtype=np.float32)
    iron_oxide[valid] = (b4[valid] / b3[valid]).astype(np.float32)
    cond2 = (iron_oxide > 1.25) & valid

    # AI_BEH_VegRoot_Anomaly = NDVI = (B8 - B4) / (B8 + B4) > 0.35
    ndvi = np.full(b12.shape, 0.0, dtype=np.float32)
    ndvi[valid] = ((b8[valid] - b4[valid]) / (b8[valid] + b4[valid])).astype(np.float32)
    cond3 = (ndvi > 0.35) & valid

    result = np.full(b12.shape, nodata, dtype=np.float32)
    result[valid] = np.float32(0.0)
    result[cond1 & cond2 & cond3] = np.float32(1.0)
    return result


def write_report_640_output(
    run_dir: Path, grid_spec: GridSpec, name: str, array: np.ndarray
) -> Path:
    tif_path = run_dir / f"{name}.tif"
    write_georeferenced_raster(tif_path, array, grid_spec)
    write_raster_sidecar(
        tif_path,
        grid_manifest=grid_spec.manifest,
        nodata=grid_spec.nodata,
        dtype="float32",
        shape=array.shape[:2],
    )
    return tif_path


def write_report_640_manifest(
    run_dir: Path,
    *,
    implemented: list[dict],
    not_implemented: list[dict],
) -> Path:
    qa_dir = ensure_run_qa_dir(run_dir)
    qa_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = qa_dir / REPORT_640_MANIFEST_NAME
    reports: dict[str, dict] = {}
    for item in implemented:
        reports[item["filename"]] = {
            "status": "implemented",
            "formula": item["formula"],
            "source_equivalent": item.get("source_equivalent"),
        }
    for item in not_implemented:
        reports[item["filename"]] = {
            "status": "not_implemented_no_source_equivalent",
            "source_equivalent": None,
            "reason": item["reason"],
        }
    payload = {
        "schema": "notebook_report_640_manifest_v1",
        "stage": "report_640",
        "reports": reports,
    }
    manifest_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return manifest_path


class Report640Stage(Stage):
    """Compute REPORT_640 rasters from persisted pipeline outputs."""

    name = "report_640"
    parity_category = ParityCategory.PARITY_REPRODUCES

    def __init__(self, *, grid_spec: GridSpec) -> None:
        self.grid_spec = grid_spec

    async def run(self, context: StageContext) -> StageResult:
        nodata = self.grid_spec.nodata
        s2_cube = load_s2_raw_cube(context.run_dir)
        st_b10_raw = load_st_b10_raw(context.run_dir)

        implemented_specs: list[dict] = []
        artifacts = []
        layer_metadata: dict[str, dict] = {}

        # Pottery_Report
        array = compute_report_pottery_report(s2_cube, nodata=nodata)
        expected_shape = (self.grid_spec.size, self.grid_spec.size)
        if array.shape[:2] != expected_shape:
            raise StageError(f"REPORT_640_Pottery_Report shape {array.shape[:2]} != expected {expected_shape}")
        tif_path = write_report_640_output(
            context.run_dir, self.grid_spec, "REPORT_640_Pottery_Report", array
        )
        artifacts.append(
            build_stage_artifact(
                name="REPORT_640_Pottery_Report",
                relative_path=tif_path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=tif_path.stat().st_size,
            )
        )
        implemented_specs.append({
            "filename": "REPORT_640_Pottery_Report.tif",
            "formula": "B12 / B11",
            "source_equivalent": "s2_raw_cube.npy",
        })
        layer_metadata["REPORT_640_Pottery_Report"] = {"status": "implemented", "formula": "B12 / B11"}

        # Mass_Report
        array = compute_report_mass_report(s2_cube, st_b10_raw, nodata=nodata)
        if array.shape[:2] != expected_shape:
            raise StageError(f"REPORT_640_Mass_Report shape {array.shape[:2]} != expected {expected_shape}")
        tif_path = write_report_640_output(
            context.run_dir, self.grid_spec, "REPORT_640_Mass_Report", array
        )
        artifacts.append(
            build_stage_artifact(
                name="REPORT_640_Mass_Report",
                relative_path=tif_path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=tif_path.stat().st_size,
            )
        )
        implemented_specs.append({
            "filename": "REPORT_640_Mass_Report.tif",
            "formula": "B12 * ST_B10 / 1000",
            "source_equivalent": f"{S2_RAW_CUBE_NPY_NAME} + {RAW_ST_B10_NPY_NAME}",
        })
        layer_metadata["REPORT_640_Mass_Report"] = {
            "status": "implemented",
            "formula": "B12 * ST_B10 / 1000",
        }

        # FINAL_Zero_Point_Targets
        array = compute_report_zero_point_targets(s2_cube, nodata=nodata)
        if array.shape[:2] != expected_shape:
            raise StageError(f"REPORT_640_FINAL_Zero_Point_Targets shape {array.shape[:2]} != expected {expected_shape}")
        tif_path = write_report_640_output(
            context.run_dir, self.grid_spec, "REPORT_640_FINAL_Zero_Point_Targets", array
        )
        artifacts.append(
            build_stage_artifact(
                name="REPORT_640_FINAL_Zero_Point_Targets",
                relative_path=tif_path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.LOCAL_SENSITIVE,
                size_bytes=tif_path.stat().st_size,
            )
        )
        implemented_specs.append({
            "filename": "REPORT_640_FINAL_Zero_Point_Targets.tif",
            "formula": "threshold_intersection(GoldAlloy>1.45, IronOxide>1.25, VegRoot>0.35)",
            "source_equivalent": "s2_raw_cube.npy",
        })
        layer_metadata["REPORT_640_FINAL_Zero_Point_Targets"] = {
            "status": "implemented",
            "formula": "threshold_intersection(GoldAlloy>1.45, IronOxide>1.25, VegRoot>0.35)",
        }

        manifest_path = write_report_640_manifest(
            context.run_dir,
            implemented=implemented_specs,
            not_implemented=[],
        )
        artifacts.append(
            build_stage_artifact(
                name="REPORT_640_manifest",
                relative_path=manifest_path.relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=manifest_path.stat().st_size,
                http_servable=False,
            )
        )

        return StageResult(
            artifacts=artifacts,
            metadata={
                "implemented_reports": [spec["filename"] for spec in implemented_specs],
                "not_implemented_reports": [],
                "report_details": layer_metadata,
            },
        )
