from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scripts.export_cell25_sar_intermediates import (
    build_intermediate_manifest,
    serialize_stage_arrays,
    write_intermediate_manifest,
)


def test_serialize_stage_arrays_writes_full_f24_manifest_layout(tmp_path: Path) -> None:
    base_output_dir = tmp_path / "qa" / "sar" / "intermediates"
    sample = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    stage_arrays = {
        "per_image_products_db": {
            "pair0_asc": {"VV_dB": sample, "VH_dB": sample + 10.0, "angle": sample + 30.0},
            "pair0_desc": {"VV_dB": sample, "VH_dB": sample + 10.0, "angle": sample + 30.0},
        },
        "pair_median": {
            "pair0": {"VV_dB": sample, "VH_dB": sample + 10.0, "angle": sample + 30.0},
        },
        "final_median_pre_rtc": {
            "final": {"VV_dB": sample, "VH_dB": sample + 10.0, "angle": sample + 30.0},
        },
        "post_sample_pre_rtc": {
            "final": {"VV_dB": sample, "VH_dB": sample + 10.0, "angle": sample + 30.0},
        },
        "post_rtc": {
            "final": {"VV_dB": sample, "VH_dB": sample + 10.0, "logRatio_dB": sample - sample, "angle": sample + 30.0},
        },
    }

    stages = serialize_stage_arrays(stage_arrays, base_output_dir)
    manifest = build_intermediate_manifest(
        stages=stages,
        missing_stages=[],
        recommended_next_action="Rerun F24 with matching notebook-side intermediates.",
    )
    manifest_path = write_intermediate_manifest(base_output_dir / "sar_intermediate_manifest.json", manifest)

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["artifact_class"] == "FILESYSTEM_ONLY"
    assert payload["local_only"] is True
    assert payload["stages"]["per_image_products_db"]["items"][0]["bands"]["VV_dB"] == "per_image_products_db/pair0_asc_VV_dB.npy"
    assert payload["stages"]["pair_median"]["items"][0]["bands"]["VH_dB"] == "pair_median/pair0_VH_dB.npy"
    assert payload["stages"]["post_rtc"]["bands"]["logRatio_dB"] == "post_rtc/final_logRatio_dB.npy"
    assert np.array_equal(np.load(base_output_dir / "post_rtc" / "final_VV_dB.npy"), sample)
    serialized = json.dumps(payload, sort_keys=True)
    assert "C:\\" not in serialized
    assert "/Users/" not in serialized
    assert "/home/" not in serialized
    assert "coordinates" not in serialized
