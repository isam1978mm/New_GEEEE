from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
import d1_sar_s1_recovery_contract as sar_contract


def touch_all(root: Path) -> None:
    for name in sar_contract.REQUIRED_OUTPUTS:
        folder = root / ("NPY_STACKS" if name.endswith(".npy") else "GEOTIFF_RADAR_BANDS")
        folder.mkdir(parents=True, exist_ok=True)
        (folder / name).write_text("placeholder", encoding="utf-8")


def test_contract_ready_when_all_required_outputs_exist_on_both_sides(tmp_path: Path) -> None:
    app = tmp_path / "app"
    ref = tmp_path / "ref"
    touch_all(app)
    touch_all(ref)
    result = sar_contract.build_d1_sar_s1_recovery_contract(app_output_dir=app, reference_sar_root=ref)
    assert result["overall_status"] == "contract_ready"
    assert result["ready_for_value_parity_count"] == len(sar_contract.REQUIRED_OUTPUTS)
    assert result["value_parity_proven"] is False


def test_contract_blocks_when_outputs_missing_on_both_sides(tmp_path: Path) -> None:
    app = tmp_path / "app"
    ref = tmp_path / "ref"
    app.mkdir()
    ref.mkdir()
    result = sar_contract.build_d1_sar_s1_recovery_contract(app_output_dir=app, reference_sar_root=ref)
    assert result["overall_status"] == "blocked_missing_required_outputs"
    assert result["missing_required_count"] == len(sar_contract.REQUIRED_OUTPUTS)


def test_non_equivalent_app_outputs_do_not_make_contract_ready(tmp_path: Path) -> None:
    app = tmp_path / "app"
    ref = tmp_path / "ref"
    app.mkdir()
    ref.mkdir()
    (app / "RADAR_VV_dB_640_app.tif").write_text("placeholder", encoding="utf-8")
    result = sar_contract.build_d1_sar_s1_recovery_contract(app_output_dir=app, reference_sar_root=ref)
    assert result["overall_status"] == "blocked_missing_required_outputs"
    assert any(item["app_present"] for item in result["non_equivalent_app_outputs"])
    assert all(item["equivalent_to_required_s1_filtered_output"] is False for item in result["non_equivalent_app_outputs"])
