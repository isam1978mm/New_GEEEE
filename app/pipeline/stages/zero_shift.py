from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from app.db.models.enums import ArtifactClass
from app.pipeline._base import build_stage_artifact
from app.pipeline._base import ParityCategory, Stage, StageContext, StageResult
from app.pipeline.stages.dem import raster_sidecar_path
from app.pipeline.stages.grid import GridSpec, pixel_center_from_transform
from app.errors import GridDriftError

TOL_CENTER_M = 0.001
TOL_ROT = 1e-12
HALF_PIXEL_TOLERANCE_M = 0.01


def read_raster_metadata(raster_path: Path) -> dict[str, object]:
    sidecar_path = raster_sidecar_path(raster_path)
    if not sidecar_path.is_file():
        raise GridDriftError(f"Missing raster metadata sidecar for {raster_path.name}.")
    return json.loads(sidecar_path.read_text(encoding="utf-8"))


def inspect_raster_alignment(raster_path: Path, grid_spec: GridSpec) -> list[str]:
    metadata = read_raster_metadata(raster_path)
    transform = tuple(float(value) for value in metadata["transform"])
    crs = str(metadata["crs"])
    width = int(metadata["width"])
    height = int(metadata["height"])

    issues: list[str] = []
    if crs != grid_spec.crs:
        issues.append("crs_mismatch")
    if width != grid_spec.size or height != grid_spec.size:
        issues.append("size_mismatch")

    if abs(transform[1]) > TOL_ROT or abs(transform[3]) > TOL_ROT:
        issues.append("rotation_detected")

    master_transform = grid_spec.transform
    master_ul = pixel_center_from_transform(master_transform, row=0, col=0)
    master_lr = pixel_center_from_transform(master_transform, row=grid_spec.size - 1, col=grid_spec.size - 1)
    ul = pixel_center_from_transform(transform, row=0, col=0)
    lr = pixel_center_from_transform(transform, row=height - 1, col=width - 1)

    dx_ul = ul[0] - master_ul[0]
    dy_ul = ul[1] - master_ul[1]
    dx_lr = lr[0] - master_lr[0]
    dy_lr = lr[1] - master_lr[1]

    if abs(dx_ul) > TOL_CENTER_M or abs(dy_ul) > TOL_CENTER_M or abs(dx_lr) > TOL_CENTER_M or abs(dy_lr) > TOL_CENTER_M:
        issues.append("pixel_center_mismatch")

    half_px_x = abs(abs(dx_ul) - abs(master_transform[0]) / 2.0) <= HALF_PIXEL_TOLERANCE_M
    half_px_y = abs(abs(dy_ul) - abs(master_transform[4]) / 2.0) <= HALF_PIXEL_TOLERANCE_M
    if half_px_x or half_px_y:
        issues.append("half_pixel_shift")

    return issues


def validate_raster_alignment(raster_path: Path, grid_spec: GridSpec) -> None:
    issues = inspect_raster_alignment(raster_path, grid_spec)
    if issues:
        raise GridDriftError(f"{raster_path.name} failed alignment checks: {','.join(issues)}")


def inspect_array_alignment(array_path: Path, grid_spec: GridSpec) -> list[str]:
    array = np.load(array_path)
    issues: list[str] = []
    if array.shape != (grid_spec.size, grid_spec.size):
        issues.append("size_mismatch")
    return issues


def validate_array_alignment(array_path: Path, grid_spec: GridSpec) -> None:
    issues = inspect_array_alignment(array_path, grid_spec)
    if issues:
        raise GridDriftError(f"{array_path.name} failed alignment checks: {','.join(issues)}")


def write_zero_shift_reports(
    run_dir: Path,
    *,
    tif_paths: list[Path],
    npy_paths: list[Path],
    tif_issues: dict[str, list[str]],
    npy_issues: dict[str, list[str]],
) -> tuple[Path, Path]:
    qa_dir = run_dir / "qa" / "grid_dem"
    qa_dir.mkdir(parents=True, exist_ok=True)
    summary_path = qa_dir / "zero_shift_summary.json"
    audit_path = qa_dir / "drift_audit.csv"

    failing_artifacts = [
        name
        for name, issues in {**tif_issues, **npy_issues}.items()
        if issues
    ]
    summary_payload = {
        "stage": "zero_shift",
        "status": "grid_locked" if not failing_artifacts else "grid_drift_detected",
        "validated_tifs": len(tif_paths),
        "validated_arrays": len(npy_paths),
        "failing_artifacts": failing_artifacts,
        "issue_count": sum(len(issues) for issues in tif_issues.values()) + sum(len(issues) for issues in npy_issues.values()),
    }
    summary_path.write_text(json.dumps(summary_payload, indent=2, sort_keys=True), encoding="utf-8")

    rows: list[dict[str, str]] = []
    for path in tif_paths:
        issues = tif_issues[path.name]
        rows.append(
            {
                "artifact_name": path.name,
                "artifact_type": "tif",
                "passes_alignment": str(not issues).lower(),
                "issues": "|".join(issues),
            }
        )
    for path in npy_paths:
        issues = npy_issues[path.name]
        rows.append(
            {
                "artifact_name": path.name,
                "artifact_type": "npy",
                "passes_alignment": str(not issues).lower(),
                "issues": "|".join(issues),
            }
        )
    with audit_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["artifact_name", "artifact_type", "passes_alignment", "issues"])
        writer.writeheader()
        writer.writerows(rows)

    return summary_path, audit_path


class ZeroShiftStage(Stage):
    name = "zero_shift"
    parity_category = ParityCategory.PARITY_REPRODUCES

    def __init__(self, *, grid_spec: GridSpec) -> None:
        self.grid_spec = grid_spec

    async def run(self, context: StageContext) -> StageResult:
        tif_paths = sorted(path for path in context.run_dir.rglob("*.tif") if path.is_file())
        npy_paths = sorted(path for path in context.run_dir.rglob("*.npy") if path.is_file())
        if not tif_paths:
            raise GridDriftError("No GeoTIFF outputs found for zero-shift validation.")

        tif_issues: dict[str, list[str]] = {path.name: inspect_raster_alignment(path, self.grid_spec) for path in tif_paths}
        npy_issues: dict[str, list[str]] = {path.name: inspect_array_alignment(path, self.grid_spec) for path in npy_paths}
        summary_path, audit_path = write_zero_shift_reports(
            context.run_dir,
            tif_paths=tif_paths,
            npy_paths=npy_paths,
            tif_issues=tif_issues,
            npy_issues=npy_issues,
        )

        for tif_path in tif_paths:
            validate_raster_alignment(tif_path, self.grid_spec)
        for npy_path in npy_paths:
            validate_array_alignment(npy_path, self.grid_spec)

        return StageResult(
            artifacts=[
                build_stage_artifact(
                    name="zero_shift_summary",
                    relative_path=summary_path.relative_to(context.run_dir).as_posix(),
                    artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                    size_bytes=summary_path.stat().st_size,
                    http_servable=False,
                ),
                build_stage_artifact(
                    name="drift_audit",
                    relative_path=audit_path.relative_to(context.run_dir).as_posix(),
                    artifact_class=ArtifactClass.FILESYSTEM_ONLY,
                    size_bytes=audit_path.stat().st_size,
                    http_servable=False,
                ),
            ],
            metadata={
                "validated_tifs": len(tif_paths),
                "validated_arrays": len(npy_paths),
                "status": "grid_locked",
            }
        )
