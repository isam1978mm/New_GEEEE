from __future__ import annotations

import numpy as np

from app.pipeline.stages.pca_anomaly import compute_pca_anomaly


def test_pca_excludes_binary_valid_mask_channel_and_keeps_invalid_pixels_nodata() -> None:
    nodata = -9999.0
    cube = np.zeros((4, 4, 3), dtype=np.float32)
    base = np.arange(16, dtype=np.float32).reshape(4, 4)
    cube[:, :, 0] = base
    cube[:, :, 1] = base * 2.0
    cube[:, :, 2] = 1.0
    cube[0, 0, 0] = 1000.0
    cube[0, 0, 1] = 1000.0
    cube[0, 0, 2] = 0.0

    anomaly, report = compute_pca_anomaly(cube, nodata=nodata, seed=0)

    assert report["used_valid_mask_channel"] is True
    assert report["feature_channel_count"] == 2
    assert report["valid_pixel_count"] == 15
    assert anomaly[0, 0] == np.float32(nodata)
    assert np.all(anomaly[cube[:, :, 2] == 1.0] >= 0.0)
