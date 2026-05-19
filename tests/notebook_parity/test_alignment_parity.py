from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image

from app.pipeline._base import ParityCategory
from app.pipeline.stages.alignment_qa import AlignmentQaStage, build_alignment_reports
from app.pipeline.stages.dem import write_raster_sidecar
from app.pipeline.stages.grid import build_run_grid


def test_alignment_parity_matches_notebook_style_grid_audit_and_center_offset_checks() -> None:
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        grid_spec = build_run_grid(35.59499, 36.12694)
        _write_raster(run_dir / "dem.tif", np.ones((grid_spec.size, grid_spec.size), dtype=np.float32), grid_spec)
        anomaly = np.full((grid_spec.size, grid_spec.size), grid_spec.nodata, dtype=np.float32)
        anomaly[10:-10, 10:-10] = 0.5
        _write_raster(run_dir / "pca_anomaly.tif", anomaly, grid_spec)

        audit_rows, summary, mask_selection = build_alignment_reports(run_dir, grid_spec)

        assert AlignmentQaStage.parity_category is ParityCategory.PARITY_REPRODUCES
        assert len(audit_rows) == 2
        assert summary["pass"] is True
        assert summary["checked_raster_count"] == 2
        assert summary["max_center_offset_px"] == 0.0
        assert mask_selection["anchor_artifact"] == "dem.tif"
        assert mask_selection["selection_rule"] == "highest_valid_fraction"


def _write_raster(path: Path, array: np.ndarray, grid_spec) -> None:
    Image.fromarray(array.astype(np.float32)).save(path, format="TIFF")
    write_raster_sidecar(
        path,
        grid_manifest=grid_spec.manifest,
        nodata=grid_spec.nodata,
        dtype="float32",
        shape=array.shape,
    )
