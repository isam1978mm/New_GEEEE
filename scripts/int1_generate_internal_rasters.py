"""Generate INT-1 internal AI_BEH raster app outputs from local app sources.

This local operator script computes notebook-named AI_BEH semantic rasters from
an app run's ``s2_raw_cube.npy`` and ``stage_s2_indices.manifest.json``.

It does not read frozen reference rasters, does not call Earth Engine, does not
change API/frontend code, and writes no rasters unless ``--write`` is passed.

Important: two INT-1 formulas require B8A. If the selected app source cube does
not contain B8A, the script reports ``blocked_missing_source_bands`` and refuses
a full write rather than silently substituting B8.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

import numpy as np

DEFAULT_DENOMINATOR_EPSILON = 1e-6
DEFAULT_NODATA = -9999.0


class INT1WriterError(ValueError):
    """Raised when INT-1 raster generation cannot proceed safely."""


@dataclass(frozen=True)
class OutputSpec:
    output_name: str
    required_bands: tuple[str, ...]
    formula: Callable[[dict[str, np.ndarray], float], np.ndarray]


class MissingBandsError(INT1WriterError):
    def __init__(self, missing_bands: tuple[str, ...]) -> None:
        super().__init__("missing required source bands: " + ", ".join(missing_bands))
        self.missing_bands = missing_bands


def _safe_divide(numerator: np.ndarray, denominator: np.ndarray, eps: float) -> np.ndarray:
    result = np.full(numerator.shape, np.nan, dtype=np.float64)
    valid = np.abs(denominator) > eps
    np.divide(numerator, denominator, out=result, where=valid)
    return result.astype(np.float32, copy=False)


def _nd(left: np.ndarray, right: np.ndarray, eps: float) -> np.ndarray:
    return _safe_divide(left - right, left + right, eps)


def _ratio(numerator_band: str, denominator_band: str) -> Callable[[dict[str, np.ndarray], float], np.ndarray]:
    return lambda bands, eps: _safe_divide(bands[numerator_band], bands[denominator_band], eps)


def _normalized_difference(left_band: str, right_band: str) -> Callable[[dict[str, np.ndarray], float], np.ndarray]:
    return lambda bands, eps: _nd(bands[left_band], bands[right_band], eps)


def _difference(left_band: str, right_band: str) -> Callable[[dict[str, np.ndarray], float], np.ndarray]:
    return lambda bands, eps: (bands[left_band] - bands[right_band]).astype(np.float32, copy=False)


def _ert_proxy(bands: dict[str, np.ndarray], eps: float) -> np.ndarray:
    denominator = bands["B11"] + 0.001
    return _safe_divide(bands["B8"] + bands["B4"], denominator, eps)


INT1_OUTPUT_SPECS: tuple[OutputSpec, ...] = (
    OutputSpec(
        "AI_BEH_VegRoot_REL_ND_DOM_lin_640.tif",
        ("B8", "B4"),
        _normalized_difference("B8", "B4"),
    ),
    OutputSpec(
        "AI_BEH_IronOxide_REL_Ratio_DOM_lin_640.tif",
        ("B4", "B3"),
        _ratio("B4", "B3"),
    ),
    OutputSpec(
        "AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640.tif",
        ("B11", "B12"),
        _ratio("B11", "B12"),
    ),
    OutputSpec(
        "AI_BEH_GoldAlloy_REL_Ratio_DOM_lin_640.tif",
        ("B12", "B11"),
        _ratio("B12", "B11"),
    ),
    OutputSpec(
        "AI_BEH_SilverCopper_REL_Ratio_DOM_lin_640.tif",
        ("B4", "B2"),
        _ratio("B4", "B2"),
    ),
    OutputSpec(
        "AI_BEH_ERT_Resistivity_Proxy_DOM_lin_640.tif",
        ("B8", "B4", "B11"),
        _ert_proxy,
    ),
    OutputSpec(
        "AI_BEH_SecretEntry_REL_ND_DOM_lin_640.tif",
        ("B12", "B8A"),
        _normalized_difference("B12", "B8A"),
    ),
    OutputSpec(
        "AI_BEH_StatueLogic_REL_Diff_DOM_lin_640.tif",
        ("B11", "B4"),
        _difference("B11", "B4"),
    ),
    OutputSpec(
        "AI_BEH_Gold_Pure_Density_19_3_DOM_lin_640.tif",
        ("B12", "B11"),
        _ratio("B12", "B11"),
    ),
    OutputSpec(
        "AI_BEH_Artifacts_Jars_Chests_DOM_lin_640.tif",
        ("B11", "B8A"),
        _ratio("B11", "B8A"),
    ),
    OutputSpec(
        "AI_BEH_Mercury_RareChemicals_DOM_lin_640.tif",
        ("B1", "B3"),
        _ratio("B1", "B3"),
    ),
    OutputSpec(
        "AI_BEH_Gemstones_AncientGlass_DOM_lin_640.tif",
        ("B2", "B12"),
        _ratio("B2", "B12"),
    ),
    OutputSpec(
        "AI_BEH_Alloys_Statues_REL_ND_DOM_lin_640.tif",
        ("B4", "B8"),
        _normalized_difference("B4", "B8"),
    ),
)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        result = generate_int1_internal_rasters(
            run_dir=Path(args.run_dir),
            output_dir=Path(args.output_dir) if args.output_dir else None,
            write=args.write,
            overwrite=args.overwrite,
            allow_partial=args.allow_partial,
            denominator_epsilon=args.denominator_epsilon,
        )
    except INT1WriterError as exc:
        print(json.dumps({"ok": False, "status": "error", "error": str(exc)}, indent=2, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


def generate_int1_internal_rasters(
    *,
    run_dir: Path,
    output_dir: Path | None = None,
    write: bool = False,
    overwrite: bool = False,
    allow_partial: bool = False,
    denominator_epsilon: float = DEFAULT_DENOMINATOR_EPSILON,
) -> dict[str, Any]:
    source_root = Path(run_dir)
    output_root = Path(output_dir) if output_dir else source_root
    if denominator_epsilon <= 0:
        raise INT1WriterError("denominator_epsilon must be positive")

    bands = _load_source_bands(source_root)
    available_bands = tuple(sorted(bands))
    missing_bands = _missing_bands(available_bands)
    runnable_specs = tuple(
        spec for spec in INT1_OUTPUT_SPECS if not (set(spec.required_bands) - set(available_bands))
    )
    blocked_specs = tuple(spec for spec in INT1_OUTPUT_SPECS if spec not in runnable_specs)

    result: dict[str, Any] = {
        "ok": not missing_bands or bool(allow_partial),
        "status": "dry_run_ready" if not missing_bands else "blocked_missing_source_bands",
        "mode": "write" if write else "dry_run",
        "created_at": datetime.now(UTC).isoformat(),
        "source_run_dir": str(source_root),
        "output_dir": str(output_root),
        "source_cube_name": "s2_raw_cube.npy",
        "source_manifest_name": "stage_s2_indices.manifest.json",
        "source_layout": "HWC",
        "available_bands": list(available_bands),
        "missing_source_bands": list(missing_bands),
        "expected_output_count": len(INT1_OUTPUT_SPECS),
        "runnable_output_count": len(runnable_specs),
        "blocked_output_count": len(blocked_specs),
        "blocked_outputs": [
            {"output_name": spec.output_name, "missing_bands": sorted(set(spec.required_bands) - set(available_bands))}
            for spec in blocked_specs
        ],
        "outputs_written": False,
        "written_output_count": 0,
        "written_outputs": [],
        "reference_outputs_read": False,
        "earth_engine_called": False,
        "api_frontend_changed": False,
        "raster_payloads_committed": False,
        "notes": (
            "Full INT-1 generation requires B8A. This script refuses full write when B8A is missing."
            if missing_bands
            else "All INT-1 source bands are available."
        ),
    }

    if missing_bands and write and not allow_partial:
        raise MissingBandsError(missing_bands)
    if not write:
        return result

    profile = _build_raster_profile(source_root, next(iter(bands.values())).shape)
    output_root.mkdir(parents=True, exist_ok=True)
    written: list[dict[str, Any]] = []
    for spec in runnable_specs:
        output_path = output_root / spec.output_name
        if output_path.exists() and not overwrite:
            raise INT1WriterError(f"output already exists; use --overwrite: {spec.output_name}")
        data = spec.formula(bands, denominator_epsilon)
        _write_tif(output_path, data, profile)
        written.append({"output_name": spec.output_name, "size_bytes": output_path.stat().st_size})

    result.update(
        {
            "ok": not missing_bands or bool(allow_partial),
            "status": "int1_internal_rasters_written" if not missing_bands else "partial_int1_internal_rasters_written",
            "outputs_written": True,
            "written_output_count": len(written),
            "written_outputs": written,
        }
    )
    return result


def _load_source_bands(run_dir: Path) -> dict[str, np.ndarray]:
    manifest_path = run_dir / "stage_s2_indices.manifest.json"
    cube_path = run_dir / "s2_raw_cube.npy"
    if not manifest_path.is_file():
        raise INT1WriterError("stage_s2_indices.manifest.json is missing")
    if not cube_path.is_file():
        raise INT1WriterError("s2_raw_cube.npy is missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_bands = tuple(str(band) for band in manifest.get("metadata", {}).get("source_bands", ()))
    if not source_bands:
        raise INT1WriterError("source_bands are missing from stage_s2_indices.manifest.json")
    cube = np.load(cube_path, allow_pickle=False)
    if cube.ndim != 3:
        raise INT1WriterError("s2_raw_cube.npy must be a 3D array")
    if cube.shape[-1] == len(source_bands):
        return {band: cube[..., index].astype(np.float32, copy=False) for index, band in enumerate(source_bands)}
    if cube.shape[0] == len(source_bands):
        return {band: cube[index, ...].astype(np.float32, copy=False) for index, band in enumerate(source_bands)}
    raise INT1WriterError("s2_raw_cube.npy shape does not match source_bands count")


def _missing_bands(available_bands: tuple[str, ...]) -> tuple[str, ...]:
    available = set(available_bands)
    required = {band for spec in INT1_OUTPUT_SPECS for band in spec.required_bands}
    return tuple(sorted(required - available))


def _build_raster_profile(run_dir: Path, shape: tuple[int, int]) -> dict[str, Any]:
    try:
        from affine import Affine
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise INT1WriterError("affine is not importable") from exc

    grid_path = run_dir / "grid_manifest.json"
    if not grid_path.is_file():
        raise INT1WriterError("grid_manifest.json is missing")
    grid = json.loads(grid_path.read_text(encoding="utf-8"))
    transform_values = grid.get("crs_transform")
    if not isinstance(transform_values, list) or len(transform_values) < 6:
        raise INT1WriterError("grid_manifest.json crs_transform is missing or invalid")
    transform = Affine(
        float(transform_values[0]),
        float(transform_values[1]),
        float(transform_values[2]),
        float(transform_values[3]),
        float(transform_values[4]),
        float(transform_values[5]),
    )
    return {
        "driver": "GTiff",
        "height": int(shape[0]),
        "width": int(shape[1]),
        "count": 1,
        "dtype": "float32",
        "crs": f"EPSG:{int(grid['epsg'])}",
        "transform": transform,
        "nodata": DEFAULT_NODATA,
        "compress": "deflate",
    }


def _write_tif(path: Path, data: np.ndarray, profile: dict[str, Any]) -> None:
    try:
        import rasterio
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise INT1WriterError("rasterio is not importable") from exc

    temp_path = path.with_suffix(path.suffix + ".tmp")
    with rasterio.open(temp_path, "w", **profile) as dataset:
        dataset.write(data.astype(np.float32, copy=False), 1)
    os.replace(temp_path, path)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate INT-1 AI_BEH internal rasters from local app source cube.")
    parser.add_argument("--run-dir", required=True, help="App run directory containing s2_raw_cube.npy and stage_s2_indices.manifest.json.")
    parser.add_argument("--output-dir", help="Directory where AI_BEH GeoTIFFs are written. Defaults to --run-dir.")
    parser.add_argument("--write", action="store_true", help="Actually write rasters. Default is dry-run only.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs.")
    parser.add_argument("--allow-partial", action="store_true", help="Write only outputs whose source bands are available. Not sufficient for INT-1 closeout.")
    parser.add_argument("--denominator-epsilon", type=float, default=DEFAULT_DENOMINATOR_EPSILON)
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
