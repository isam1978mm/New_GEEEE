from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

B8A_NPY_NAME = "S2_B8A_640.npy"
B8A_TIF_NAME = "S2_B8A_640.tif"
B8A_MANIFEST_NAME = "stage_s2_b8a_recovery.manifest.json"
B8A_BAND_NAME = "B8A"
DEFAULT_NODATA = -9999.0


class B8ARecoveryError(ValueError):
    pass


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        result = recover_b8a_from_local_array(
            app_run_dir=Path(args.app_run_dir),
            b8a_array=Path(args.b8a_array) if args.b8a_array else None,
            output_dir=Path(args.output_dir) if args.output_dir else None,
            write=args.write,
            overwrite=args.overwrite,
        )
    except B8ARecoveryError as exc:
        print(json.dumps({"ok": False, "status": "error", "error": str(exc)}, indent=2, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


def recover_b8a_from_local_array(
    *,
    app_run_dir: Path,
    b8a_array: Path | None = None,
    output_dir: Path | None = None,
    write: bool = False,
    overwrite: bool = False,
) -> dict[str, Any]:
    run_root = Path(app_run_dir)
    output_root = Path(output_dir) if output_dir else run_root
    grid_path = run_root / "grid_manifest.json"
    s2_manifest_path = run_root / "stage_s2_indices.manifest.json"
    npy_path = output_root / B8A_NPY_NAME
    tif_path = output_root / B8A_TIF_NAME
    manifest_path = output_root / B8A_MANIFEST_NAME

    if not grid_path.is_file():
        raise B8ARecoveryError("grid_manifest.json is missing")
    if not s2_manifest_path.is_file():
        raise B8ARecoveryError("stage_s2_indices.manifest.json is missing")

    grid = json.loads(grid_path.read_text(encoding="utf-8"))
    s2_manifest = json.loads(s2_manifest_path.read_text(encoding="utf-8"))
    source_bands = list(s2_manifest.get("metadata", {}).get("source_bands", []))
    size_px = int(grid.get("size_px") or grid.get("size") or 640)
    existing_outputs = [path.name for path in (npy_path, tif_path, manifest_path) if path.exists()]

    result: dict[str, Any] = {
        "ok": True,
        "status": "dry_run_ready",
        "mode": "write" if write else "dry_run",
        "created_at": datetime.now(UTC).isoformat(),
        "app_run_dir": str(run_root),
        "output_dir": str(output_root),
        "band_name": B8A_BAND_NAME,
        "output_npy_name": B8A_NPY_NAME,
        "output_tif_name": B8A_TIF_NAME,
        "manifest_name": B8A_MANIFEST_NAME,
        "expected_shape": [size_px, size_px],
        "source_bands_before_recovery": source_bands,
        "b8a_already_in_s2_manifest": B8A_BAND_NAME in source_bands,
        "local_b8a_array": str(b8a_array) if b8a_array else None,
        "existing_outputs": existing_outputs,
        "reference_outputs_read": False,
        "earth_engine_called": False,
        "api_frontend_changed": False,
        "raster_payloads_committed": False,
        "output_npy_written": False,
        "output_tif_written": False,
        "manifest_written": False,
    }

    if not write:
        return result
    if b8a_array is None:
        raise B8ARecoveryError("--b8a-array is required for local-array recovery")
    if existing_outputs and not overwrite:
        raise B8ARecoveryError("B8A recovery outputs already exist; use --overwrite")
    if not b8a_array.is_file():
        raise B8ARecoveryError("B8A source array does not exist")

    array = np.load(b8a_array, allow_pickle=False).astype(np.float32, copy=False)
    if array.shape != (size_px, size_px):
        raise B8ARecoveryError(f"B8A array shape must be {(size_px, size_px)}, got {array.shape}")

    output_root.mkdir(parents=True, exist_ok=True)
    _atomic_save_npy(npy_path, array)
    _write_tif(tif_path, array, grid)
    _write_manifest(manifest_path, run_root, output_root, grid, array)
    result.update(
        {
            "status": "s2_b8a_recovery_written",
            "output_npy_written": True,
            "output_tif_written": True,
            "manifest_written": True,
            "output_npy_size_bytes": npy_path.stat().st_size,
            "output_tif_size_bytes": tif_path.stat().st_size,
            "finite_count": int(np.isfinite(array).sum()),
            "nan_count": int(np.isnan(array).sum()),
            "min": float(np.nanmin(array)),
            "max": float(np.nanmax(array)),
        }
    )
    return result


def _atomic_save_npy(path: Path, array: np.ndarray) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("wb") as handle:
        np.save(handle, array.astype(np.float32, copy=False))
    os.replace(temp_path, path)


def _write_tif(path: Path, array: np.ndarray, grid: dict[str, Any]) -> None:
    try:
        import rasterio
        from affine import Affine
    except ImportError as exc:
        raise B8ARecoveryError(f"required dependency is not importable: {exc.name}") from exc

    transform_values = grid.get("crs_transform")
    if not isinstance(transform_values, list) or len(transform_values) < 6:
        raise B8ARecoveryError("grid_manifest.json crs_transform is missing or invalid")
    transform = Affine(*[float(value) for value in transform_values[:6]])
    epsg = int(grid.get("epsg"))
    profile = {
        "driver": "GTiff",
        "height": int(array.shape[0]),
        "width": int(array.shape[1]),
        "count": 1,
        "dtype": "float32",
        "crs": f"EPSG:{epsg}",
        "transform": transform,
        "nodata": DEFAULT_NODATA,
        "compress": "deflate",
    }
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with rasterio.open(temp_path, "w", **profile) as dataset:
        dataset.write(array.astype(np.float32, copy=False), 1)
        dataset.set_band_description(1, B8A_BAND_NAME)
    os.replace(temp_path, path)


def _write_manifest(path: Path, app_run_dir: Path, output_dir: Path, grid: dict[str, Any], array: np.ndarray) -> None:
    payload = {
        "stage_name": "s2_b8a_recovery",
        "status": "done",
        "artifact_class": "LOCAL_SENSITIVE",
        "filesystem_only": True,
        "http_servable": False,
        "created_at": datetime.now(UTC).isoformat(),
        "app_run_dir": str(app_run_dir),
        "output_dir": str(output_dir),
        "source_band": B8A_BAND_NAME,
        "outputs": {"npy": B8A_NPY_NAME, "tif": B8A_TIF_NAME},
        "grid": grid,
        "array_summary": {
            "shape": list(array.shape),
            "dtype": str(array.dtype),
            "finite_count": int(np.isfinite(array).sum()),
            "nan_count": int(np.isnan(array).sum()),
            "min": float(np.nanmin(array)),
            "max": float(np.nanmax(array)),
        },
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recover INT-1 B8A from a local same-run B8A array.")
    parser.add_argument("--app-run-dir", required=True)
    parser.add_argument("--b8a-array", help="Local same-run B8A .npy array to register as S2_B8A_640.npy.")
    parser.add_argument("--output-dir")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
