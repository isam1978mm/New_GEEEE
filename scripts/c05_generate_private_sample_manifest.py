"""Generate a private C05 WorldCover sample manifest outside Git.

This script samples a local ESA WorldCover raster and creates private background
candidate references for the C05 negative/background source.

Default behavior is dry-run only. It writes nothing unless --write is provided.

It does not download WorldCover data, create I1 rows, assemble I2, run the
readiness validator, train, infer, call Earth Engine, or change app/API/frontend
code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = Path(r"C:\Dev\New_GEE_PRIVATE\C05_RAW")
DEFAULT_MANIFEST_NAME = "c05_sample_manifest.private.jsonl"
DEFAULT_LINEAGE_NAME = "c05_sample_lineage.private.jsonl"
DEFAULT_SUMMARY_NAME = "c05_sample_manifest.private.summary.json"
DEFAULT_TARGET_COUNT = 217
DEFAULT_SEED = 20260616

# Conservative clean-background WorldCover class values.
# Operator can override with --allowed-classes.
# Excludes built-up and bare/sparse by default because those can be hard-negative
# or confusing classes rather than clean background.
DEFAULT_ALLOWED_CLASSES = (10, 20, 30, 40, 80, 90, 95, 100)


class C05SamplerError(ValueError):
    """Raised when private C05 sampling cannot proceed safely."""


def main() -> int:
    args = _parse_args()

    raster_path = Path(args.worldcover_raster)
    output_dir = Path(args.output_dir)
    allowed_classes = _parse_allowed_classes(args.allowed_classes)

    _validate_private_existing_file(raster_path, "worldcover raster")
    _validate_private_output_dir(output_dir)

    samples, summary = _sample_worldcover(
        raster_path=raster_path,
        target_count=args.target_count,
        seed=args.seed,
        allowed_classes=allowed_classes,
        max_attempts=args.max_attempts,
    )

    summary.update(
        {
            "status": "ready_to_write_private_sample_manifest" if args.write else "dry_run_only",
            "source_id": "C05",
            "source_role": "negative_background",
            "requested_count": args.target_count,
            "selected_count": len(samples),
            "seed": args.seed,
            "allowed_worldcover_classes": list(allowed_classes),
            "manifest_written": False,
            "i1_rows_created": 0,
            "i2_pack_assembled": False,
            "validator_run_on_real_data": False,
            "training_started": False,
            "inference_started": False,
        }
    )

    if args.write:
        if len(samples) != args.target_count:
            raise SystemExit(
                f"C05 sample manifest write refused: selected {len(samples)} of "
                f"requested {args.target_count} samples."
            )
        output_dir.mkdir(parents=True, exist_ok=True)
        _write_jsonl(output_dir / DEFAULT_MANIFEST_NAME, [_manifest_row(s) for s in samples])
        _write_jsonl(output_dir / DEFAULT_LINEAGE_NAME, [_lineage_row(s) for s in samples])
        summary["manifest_written"] = True
        summary["status"] = "private_sample_manifest_written"
        _write_json(output_dir / DEFAULT_SUMMARY_NAME, summary)

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a private C05 sample manifest from a local WorldCover raster."
    )
    parser.add_argument(
        "--worldcover-raster",
        required=True,
        help="Path to a local ESA WorldCover raster outside Git.",
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--target-count", type=int, default=DEFAULT_TARGET_COUNT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--allowed-classes",
        default=",".join(str(value) for value in DEFAULT_ALLOWED_CLASSES),
        help="Comma-separated WorldCover class values allowed as clean background.",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=250000,
        help="Maximum random pixel attempts before failing the requested count.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write private manifest and lineage files outside Git.",
    )
    return parser.parse_args()


def _sample_worldcover(
    *,
    raster_path: Path,
    target_count: int,
    seed: int,
    allowed_classes: set[int],
    max_attempts: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if target_count <= 0:
        raise C05SamplerError("target_count must be positive")
    if max_attempts < target_count:
        raise C05SamplerError("max_attempts must be >= target_count")

    try:
        import rasterio
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise C05SamplerError(
            "rasterio is required to sample WorldCover rasters. Install project GIS dependencies first."
        ) from exc

    rng = random.Random(seed)
    selected: list[dict[str, Any]] = []
    seen_cells: set[tuple[int, int]] = set()
    class_counts: dict[str, int] = {}
    attempts = 0
    nodata_count = 0
    disallowed_count = 0
    duplicate_count = 0

    with rasterio.open(raster_path) as dataset:
        if dataset.count < 1:
            raise C05SamplerError("WorldCover raster has no bands")
        width = int(dataset.width)
        height = int(dataset.height)
        nodata = dataset.nodata

        while len(selected) < target_count and attempts < max_attempts:
            attempts += 1
            row = rng.randrange(0, height)
            col = rng.randrange(0, width)
            cell_key = (row, col)
            if cell_key in seen_cells:
                duplicate_count += 1
                continue
            seen_cells.add(cell_key)

            value = dataset.read(1, window=((row, row + 1), (col, col + 1)))[0][0]
            try:
                class_value = int(value)
            except (TypeError, ValueError):
                nodata_count += 1
                continue

            if nodata is not None and class_value == int(nodata):
                nodata_count += 1
                continue
            if class_value not in allowed_classes:
                disallowed_count += 1
                continue

            fingerprint = _stable_hash(
                {
                    "source": "C05",
                    "seed": seed,
                    "row": row,
                    "col": col,
                    "class_value": class_value,
                    "raster_name": raster_path.name,
                }
            )
            ref = f"c05_wc_ref_{fingerprint[:16]}"
            class_name = f"worldcover_class_{class_value}"
            selected.append(
                {
                    "source_record_ref": ref,
                    "background_class": "non_target_background",
                    "worldcover_class": class_name,
                    "worldcover_class_value": class_value,
                    "private_row": row,
                    "private_col": col,
                    "private_fingerprint": fingerprint,
                }
            )
            class_counts[class_name] = class_counts.get(class_name, 0) + 1

        summary = {
            "raster_file_name": raster_path.name,
            "raster_width": width,
            "raster_height": height,
            "attempts": attempts,
            "nodata_count": nodata_count,
            "disallowed_class_count": disallowed_count,
            "duplicate_cell_count": duplicate_count,
            "selected_class_counts": dict(sorted(class_counts.items())),
        }

    return selected, summary


def _manifest_row(sample: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_record_ref": sample["source_record_ref"],
        "background_class": sample["background_class"],
    }


def _lineage_row(sample: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_record_ref": sample["source_record_ref"],
        "worldcover_class": sample["worldcover_class"],
        "worldcover_class_value": sample["worldcover_class_value"],
        "private_row": sample["private_row"],
        "private_col": sample["private_col"],
        "private_fingerprint": sample["private_fingerprint"],
    }


def _parse_allowed_classes(text: str) -> set[int]:
    values: set[int] = set()
    for part in text.split(","):
        stripped = part.strip()
        if not stripped:
            continue
        try:
            values.add(int(stripped))
        except ValueError as exc:
            raise C05SamplerError(f"invalid allowed class value: {stripped}") from exc
    if not values:
        raise C05SamplerError("at least one allowed class is required")
    return values


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    os.replace(temp_path, path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temp_path, path)


def _stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _validate_private_existing_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"{label} does not exist: {path}")
    _validate_private_path_not_inside_repo(path, label)


def _validate_private_output_dir(path: Path) -> None:
    _validate_private_path_not_inside_repo(path, "output directory")


def _validate_private_path_not_inside_repo(path: Path, label: str) -> None:
    try:
        path.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError:
        return
    raise ValueError(f"{label} must be outside the repository")


if __name__ == "__main__":
    raise SystemExit(main())
