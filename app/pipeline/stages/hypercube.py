from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image

from app.db.models.enums import ArtifactClass
from app.errors import StageError
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult, build_stage_artifact
from app.pipeline.stages.dem import raster_sidecar_path, write_raster_sidecar
from app.pipeline.stages.grid import GridSpec
from app.services.storage import read_manifest

HYPERCUBE_TIF_NAME = "hypercube.tif"
HYPERCUBE_NPY_NAME = "hypercube.npy"
HYPERCUBE_BAND_ORDER_NAME = "hypercube_band_order.csv"
HYPERCUBE_STATS_NAME = "hypercube_band_stats.csv"
HYPERCUBE_NORM_PARAMS_NAME = "hypercube_norm_params.csv"
HYPERCUBE_AUDIT_NAME = "hypercube_audit.csv"
EXCLUDED_TIFS = {HYPERCUBE_TIF_NAME, "pca_anomaly.tif"}
EPS = 1e-6


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
) -> dict[str, np.ndarray | list[str] | np.ndarray]:
    if not source_layers:
        raise StageError("Hypercube assembly requires at least one source TIFF.")

    source_band_names = [name for name, _array in source_layers]
    layers = [array.astype(np.float32, copy=True) for _name, array in source_layers]
    cube_raw = np.stack(layers, axis=-1).astype(np.float32)
    cube_raw[cube_raw == nodata] = np.nan
    cube_raw[~np.isfinite(cube_raw)] = np.nan

    mask_any = np.isfinite(cube_raw).any(axis=-1).astype(np.uint8)
    mask_all = np.isfinite(cube_raw).all(axis=-1).astype(np.uint8)
    cube_clean = np.nan_to_num(cube_raw, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)

    channel_count = cube_raw.shape[-1]
    cube_norm = np.empty_like(cube_clean, dtype=np.float32)
    medians = np.zeros((channel_count,), dtype=np.float32)
    iqrs = np.zeros((channel_count,), dtype=np.float32)

    for index in range(channel_count):
        channel = cube_raw[:, :, index]
        valid = channel[np.isfinite(channel)]
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
        normalized = np.clip((cube_clean[:, :, index] - med) / iqr, -8.0, 8.0)
        cube_norm[:, :, index] = normalized.astype(np.float32)

    cube_norm_plus_mask = np.concatenate([cube_norm, mask_any[:, :, None].astype(np.float32)], axis=-1)
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
    }


def _save_multipage_tiff(path: Path, cube_hwc: np.ndarray) -> None:
    pages = [Image.fromarray(cube_hwc[:, :, band_index].astype(np.float32)) for band_index in range(cube_hwc.shape[-1])]
    first, *rest = pages
    first.save(path, format="TIFF", save_all=True, append_images=rest)


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


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
    audit_path = run_dir / "qa" / "parity" / HYPERCUBE_AUDIT_NAME
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    _save_multipage_tiff(tif_path, cube_raw)
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
        band_names = products["band_names"]
        assert isinstance(band_names, list)
        return StageResult(
            artifacts=artifacts,
            metadata={
                "band_names": band_names,
                "band_count": len(band_names),
                "shape": [self.grid_spec.size, self.grid_spec.size, len(band_names)],
            },
        )
