"""Generate HYPER-1A 2.5 m resampled hypercube app outputs.

This is a local, operator-run generator for the notebook-named outputs:

- FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif
- FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy

It reads the app-produced source GeoTIFF FINAL_TESLA_V7_2_HYPERCUBE.tif,
performs notebook-compatible cubic upsampling to 2.5 m, and writes the two
outputs under the chosen app output directory.

It does not read or copy reference outputs, does not call Earth Engine, does not
change API/frontend/runtime service code, and writes nothing unless --write is
provided.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

SOURCE_HYPERCUBE_NAME = "FINAL_TESLA_V7_2_HYPERCUBE.tif"
OUTPUT_TIF_NAME = "FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif"
OUTPUT_NPY_NAME = "FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy"
DEFAULT_OUTPUT_RES_M = 2.5
DEFAULT_RESAMPLING_ORDER = 3
EXPECTED_BAND_COUNT = 9


class Hyper1AGenerationError(ValueError):
    """Raised when HYPER-1A generation inputs are invalid."""


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        result = generate_hyper_1a_res_2p5m(
            source_dir=Path(args.source_dir),
            output_dir=Path(args.output_dir) if args.output_dir else None,
            write=args.write,
            overwrite=args.overwrite,
            output_res_m=args.output_res_m,
        )
    except Hyper1AGenerationError as exc:
        print(json.dumps({"ok": False, "status": "error", "error": str(exc)}, indent=2, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] in {"dry_run_ready", "hyper_1a_res_2p5m_written"} else 1


def generate_hyper_1a_res_2p5m(
    *,
    source_dir: Path,
    output_dir: Path | None = None,
    write: bool = False,
    overwrite: bool = False,
    output_res_m: float = DEFAULT_OUTPUT_RES_M,
) -> dict[str, Any]:
    """Generate or dry-run HYPER-1A 2.5 m outputs from an app source hypercube."""

    source_root = Path(source_dir)
    output_root = Path(output_dir) if output_dir else source_root
    source_path = _find_source_hypercube(source_root)
    output_tif_path = output_root / OUTPUT_TIF_NAME
    output_npy_path = output_root / OUTPUT_NPY_NAME

    if output_res_m <= 0:
        raise Hyper1AGenerationError("output_res_m must be positive")
    if not source_path.is_file():
        raise Hyper1AGenerationError(f"source hypercube is missing: {SOURCE_HYPERCUBE_NAME}")
    if output_tif_path.exists() and not overwrite and write:
        raise Hyper1AGenerationError(f"output already exists; use --overwrite: {OUTPUT_TIF_NAME}")
    if output_npy_path.exists() and not overwrite and write:
        raise Hyper1AGenerationError(f"output already exists; use --overwrite: {OUTPUT_NPY_NAME}")

    source_summary = _read_source_summary(source_path, output_res_m=output_res_m)
    result: dict[str, Any] = {
        "ok": True,
        "status": "dry_run_ready",
        "mode": "write" if write else "dry_run",
        "created_at": datetime.now(UTC).isoformat(),
        "source_name": SOURCE_HYPERCUBE_NAME,
        "source_present": True,
        "source_dir": str(source_root),
        "output_dir": str(output_root),
        "output_tif_name": OUTPUT_TIF_NAME,
        "output_npy_name": OUTPUT_NPY_NAME,
        "output_tif_written": False,
        "output_npy_written": False,
        "source_band_count": source_summary["source_band_count"],
        "source_width": source_summary["source_width"],
        "source_height": source_summary["source_height"],
        "source_dtype": source_summary["source_dtype"],
        "source_crs": source_summary["source_crs"],
        "source_pixel_size": source_summary["source_pixel_size"],
        "output_res_m": output_res_m,
        "zoom_factor": source_summary["zoom_factor"],
        "expected_output_shape_chw": source_summary["expected_output_shape_chw"],
        "resampling_order": DEFAULT_RESAMPLING_ORDER,
        "earth_engine_called": False,
        "reference_outputs_read": False,
        "api_frontend_changed": False,
        "raster_payloads_committed": False,
    }

    if source_summary["source_band_count"] != EXPECTED_BAND_COUNT:
        raise Hyper1AGenerationError(
            f"expected {EXPECTED_BAND_COUNT} source bands, found {source_summary['source_band_count']}"
        )

    if not write:
        return result

    _generate_outputs(
        source_path=source_path,
        output_tif_path=output_tif_path,
        output_npy_path=output_npy_path,
        output_res_m=output_res_m,
    )
    tif_size = output_tif_path.stat().st_size
    npy_size = output_npy_path.stat().st_size
    result.update(
        {
            "status": "hyper_1a_res_2p5m_written",
            "output_tif_written": True,
            "output_npy_written": True,
            "output_tif_size_bytes": tif_size,
            "output_npy_size_bytes": npy_size,
        }
    )
    return result


def _find_source_hypercube(source_root: Path) -> Path:
    direct = source_root / SOURCE_HYPERCUBE_NAME
    if direct.is_file():
        return direct
    nested = source_root / "NPY_STACKS" / SOURCE_HYPERCUBE_NAME
    if nested.is_file():
        return nested
    return direct


def _read_source_summary(source_path: Path, *, output_res_m: float) -> dict[str, Any]:
    try:
        import rasterio
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise Hyper1AGenerationError("rasterio is not importable") from exc

    with rasterio.open(source_path) as dataset:
        source_res = tuple(float(abs(value)) for value in dataset.res)
        if not source_res or source_res[0] <= 0:
            raise Hyper1AGenerationError("source raster has invalid pixel size")
        if abs(source_res[0] - source_res[1]) > 1e-9:
            raise Hyper1AGenerationError("source raster must have square pixels")
        zoom_factor = source_res[0] / output_res_m
        if abs(round(zoom_factor) - zoom_factor) > 1e-9:
            raise Hyper1AGenerationError("source pixel size must be an integer multiple of output_res_m")
        expected_height = int(round(dataset.height * zoom_factor))
        expected_width = int(round(dataset.width * zoom_factor))
        return {
            "source_band_count": int(dataset.count),
            "source_width": int(dataset.width),
            "source_height": int(dataset.height),
            "source_dtype": ",".join(str(item) for item in dataset.dtypes),
            "source_crs": str(dataset.crs),
            "source_pixel_size": source_res,
            "zoom_factor": zoom_factor,
            "expected_output_shape_chw": [int(dataset.count), expected_height, expected_width],
        }


def _generate_outputs(
    *,
    source_path: Path,
    output_tif_path: Path,
    output_npy_path: Path,
    output_res_m: float,
) -> None:
    try:
        import rasterio
        from affine import Affine
        from scipy.ndimage import zoom
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise Hyper1AGenerationError(f"required dependency is not importable: {exc.name}") from exc

    with rasterio.open(source_path) as source:
        source_res = float(abs(source.res[0]))
        zoom_factor = source_res / output_res_m
        data = source.read().astype(np.float32, copy=False)
        descriptions = tuple(source.descriptions)
        profile = source.profile.copy()
        transform = source.transform * Affine.scale(1 / zoom_factor, 1 / zoom_factor)

    upsampled = np.stack(
        [zoom(band, zoom_factor, order=DEFAULT_RESAMPLING_ORDER).astype(np.float32, copy=False) for band in data],
        axis=0,
    ).astype(np.float32, copy=False)

    profile.update(
        {
            "height": int(upsampled.shape[1]),
            "width": int(upsampled.shape[2]),
            "count": int(upsampled.shape[0]),
            "transform": transform,
            "dtype": "float32",
        }
    )

    output_tif_path.parent.mkdir(parents=True, exist_ok=True)
    output_npy_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_save_npy(output_npy_path, upsampled)
    _atomic_write_tif(output_tif_path, upsampled, profile, descriptions)


def _atomic_save_npy(path: Path, data: np.ndarray) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("wb") as handle:
        np.save(handle, data)
    os.replace(temp_path, path)


def _atomic_write_tif(path: Path, data: np.ndarray, profile: dict[str, Any], descriptions: tuple[str | None, ...]) -> None:
    import rasterio

    temp_path = path.with_suffix(path.suffix + ".tmp")
    with rasterio.open(temp_path, "w", **profile) as dataset:
        dataset.write(data)
        for band_index, description in enumerate(descriptions, start=1):
            if description:
                dataset.set_band_description(band_index, description)
    os.replace(temp_path, path)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate HYPER-1A RES_2p5M app outputs from an app source hypercube.")
    parser.add_argument("--source-dir", required=True, help="Directory containing FINAL_TESLA_V7_2_HYPERCUBE.tif or NPY_STACKS/that file.")
    parser.add_argument("--output-dir", help="Directory where RES_2p5M outputs are written. Defaults to --source-dir.")
    parser.add_argument("--output-res-m", type=float, default=DEFAULT_OUTPUT_RES_M)
    parser.add_argument("--write", action="store_true", help="Actually write outputs. Default is dry-run only.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing RES_2p5M outputs.")
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
