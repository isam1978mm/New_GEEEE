from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

import numpy as np
import rasterio
from rasterio.transform import Affine

from app.db.models.enums import ArtifactClass
from app.errors import StageError
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.stages.dem import write_raster_sidecar
from app.pipeline.stages.feature_stacks import SCIENCE_CORE_BANDS
from app.pipeline.stages.grid import GridSpec

FOCUS_MASK_TIF_NAME = "focus_zone_17m.tif"
FOCUS_MASK_NPY_NAME = "focus_zone_17m.npy"
FOCUS_WINDOW_NPY_NAME = "focus_zone_ai_ready_window.npy"
FOCUS_SUMMARY_JSON_NAME = "focus_zone_summary.json"
FOCUS_BAND_SUMMARY_CSV_NAME = "focus_zone_band_summary.csv"
FOCUS_DIR_PARTS = ("full_job", "focus")
FOCUS_SIZE_M = 17.0


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def load_ai_ready_support_stack(run_dir: Path) -> np.ndarray:
    path = run_dir / "stacks" / "tensor_support" / "ai_ready_support_stack.npy"
    if not path.is_file():
        raise StageError("Focus-mask stage requires ai_ready_support_stack.npy from feature_stacks.")
    return np.load(path).astype(np.float32)


def build_focus_mask_products(
    ai_ready_stack: np.ndarray,
    *,
    grid_spec: GridSpec,
    focus_size_m: float = FOCUS_SIZE_M,
) -> dict[str, object]:
    if ai_ready_stack.ndim != 3:
        raise StageError("Focus-mask stage requires a 3D ai_ready support stack.")
    if ai_ready_stack.shape[0] != grid_spec.size or ai_ready_stack.shape[1] != grid_spec.size:
        raise StageError("Focus-mask stage requires ai_ready support stack on the authoritative grid.")

    transform = grid_spec.transform
    pixel_size_m = float((abs(transform[0]) + abs(transform[4])) / 2.0)
    radius_px = float(focus_size_m) / pixel_size_m
    center_row = float(grid_spec.size) / 2.0
    center_col = float(grid_spec.size) / 2.0

    rows, cols = np.meshgrid(np.arange(grid_spec.size), np.arange(grid_spec.size), indexing="ij")
    dist_px = np.sqrt((rows.astype(np.float64) - center_row) ** 2 + (cols.astype(np.float64) - center_col) ** 2)
    mask = (dist_px <= radius_px).astype(np.float32)
    row_indices, col_indices = np.where(mask == 1.0)

    if row_indices.size == 0 or col_indices.size == 0:
        raise StageError("Focus-mask stage could not derive a non-empty focus zone from the configured grid.")

    row_min = int(row_indices.min())
    row_max = int(row_indices.max())
    col_min = int(col_indices.min())
    col_max = int(col_indices.max())
    cropped_window = ai_ready_stack[row_min : row_max + 1, col_min : col_max + 1, :].astype(np.float32)
    masked_window = cropped_window * mask[row_min : row_max + 1, col_min : col_max + 1, None]

    band_summary_rows: list[dict[str, object]] = []
    for index in range(ai_ready_stack.shape[-1]):
        channel = ai_ready_stack[:, :, index]
        values = channel[mask == 1.0]
        band_summary_rows.append(
            {
                "band_index": index,
                "band_name": SCIENCE_CORE_BANDS[index] if index < len(SCIENCE_CORE_BANDS) else f"band_{index}",
                "focus_mean": float(values.mean()) if values.size else "",
                "focus_min": float(values.min()) if values.size else "",
                "focus_max": float(values.max()) if values.size else "",
            }
        )

    summary = {
        "stage": "focus_mask",
        "focus_size_m": float(focus_size_m),
        "mask_pixel_count": int(mask.sum()),
        "window_shape": [int(masked_window.shape[0]), int(masked_window.shape[1]), int(masked_window.shape[2])],
        "analysis_source": "ai_ready_support_stack",
        "public_safe": False,
    }
    return {
        "mask": mask,
        "masked_window": masked_window,
        "summary": summary,
        "band_summary_rows": band_summary_rows,
    }


def write_focus_mask_outputs(run_dir: Path, grid_spec: GridSpec, products: dict[str, object]) -> dict[str, Path]:
    mask = products["mask"]
    masked_window = products["masked_window"]
    summary = products["summary"]
    band_summary_rows = products["band_summary_rows"]
    assert isinstance(mask, np.ndarray)
    assert isinstance(masked_window, np.ndarray)
    assert isinstance(summary, dict)
    assert isinstance(band_summary_rows, list)

    focus_dir = run_dir.joinpath(*FOCUS_DIR_PARTS)
    focus_dir.mkdir(parents=True, exist_ok=True)

    mask_tif_path = focus_dir / FOCUS_MASK_TIF_NAME
    mask_npy_path = focus_dir / FOCUS_MASK_NPY_NAME
    focus_window_path = focus_dir / FOCUS_WINDOW_NPY_NAME
    summary_path = focus_dir / FOCUS_SUMMARY_JSON_NAME
    band_summary_path = focus_dir / FOCUS_BAND_SUMMARY_CSV_NAME

    _write_focus_mask_tif(mask_tif_path, mask, grid_spec)
    np.save(mask_npy_path, mask.astype(np.float32))
    np.save(focus_window_path, masked_window.astype(np.float32))
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    _write_csv(band_summary_path, ["band_index", "band_name", "focus_mean", "focus_min", "focus_max"], band_summary_rows)
    write_raster_sidecar(
        mask_tif_path,
        grid_manifest=grid_spec.manifest,
        nodata=0.0,
        dtype="uint8",
        shape=mask.shape,
    )

    return {
        "focus_mask_tif": mask_tif_path,
        "focus_mask_npy": mask_npy_path,
        "focus_window_npy": focus_window_path,
        "focus_summary_json": summary_path,
        "focus_band_summary_csv": band_summary_path,
    }


def _write_focus_mask_tif(path: Path, mask: np.ndarray, grid_spec: GridSpec) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=int(mask.shape[0]),
        width=int(mask.shape[1]),
        count=1,
        dtype="uint8",
        crs=grid_spec.crs,
        transform=Affine(*grid_spec.transform),
        nodata=0,
        compress="deflate",
    ) as dataset:
        dataset.write(mask.astype(np.uint8, copy=False), 1)


class FocusMaskStage(Stage):
    name = "focus_mask"
    parity_category = ParityCategory.PARITY_REPLACES
    parity_reason = "Replaces notebook location-bearing 17m focus-region outputs with local-only FILESYSTEM_ONLY mask products."

    def __init__(self, *, grid_spec: GridSpec) -> None:
        self.grid_spec = grid_spec

    async def run(self, context: StageContext) -> StageResult:
        ai_ready_stack = load_ai_ready_support_stack(context.run_dir)
        products = build_focus_mask_products(ai_ready_stack, grid_spec=self.grid_spec)
        outputs = write_focus_mask_outputs(context.run_dir, self.grid_spec, products)
        artifacts = [
            build_stage_artifact(
                name="focus_zone_17m_tif",
                relative_path=outputs["focus_mask_tif"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["focus_mask_tif"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="focus_zone_17m_npy",
                relative_path=outputs["focus_mask_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["focus_mask_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="focus_zone_ai_ready_window",
                relative_path=outputs["focus_window_npy"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["focus_window_npy"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="focus_zone_summary",
                relative_path=outputs["focus_summary_json"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["focus_summary_json"].stat().st_size,
                http_servable=False,
            ),
            build_stage_artifact(
                name="focus_band_summary",
                relative_path=outputs["focus_band_summary_csv"].relative_to(context.run_dir).as_posix(),
                artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                size_bytes=outputs["focus_band_summary_csv"].stat().st_size,
                http_servable=False,
            ),
        ]
        summary = products["summary"]
        assert isinstance(summary, dict)
        return StageResult(
            artifacts=artifacts,
            metadata={
                "focus_size_m": float(summary["focus_size_m"]),
                "mask_pixel_count": int(summary["mask_pixel_count"]),
                "window_shape": summary["window_shape"],
            },
        )
