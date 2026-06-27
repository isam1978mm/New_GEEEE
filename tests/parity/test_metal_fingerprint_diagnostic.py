import csv
import json

from app.pipeline.parity.metal_fingerprint_diagnostic import (
    OUTPUT_CSV_NAME,
    OUTPUT_JSON_NAME,
    OUTPUT_TXT_NAME,
    SOURCE_CELL,
    diagnose_metal_signature,
    write_plan_b33_metal_fingerprint_diagnostic_outputs,
)


def _write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_plan_b33_formula_selects_expected_material():
    sig = {
        "Secret_Gold_Halo": "2.0",
        "Secret_Silver_Oxide": "0.1",
        "Secret_Tunnel_Ceiling": "0.0",
        "Secret_Thermal_Inertia": "0.0",
        "Secret_Chemical_Protector": "0.4",
        "Secret_Hidden_Doors": "0.0",
        "REPORT_640_Mass_Report": "1.5",
        "REPORT_640_Pottery_Report": "0.0",
        "REPORT_640_FINAL_Zero_Point_Targets": "0.0",
    }

    scores, best_label, best_score = diagnose_metal_signature(sig)

    assert best_label in scores
    assert best_label == "Gold"
    assert best_score == scores["Gold"]


def test_plan_b33_writes_private_diagnostic_outputs(tmp_path):
    focus = tmp_path / "full_job" / "focus"

    _write_csv(
        focus / "AI_FOCUS_17M_PIXEL_REPORT_V7_2.csv",
        [
            {
                "row": "1",
                "col": "1",
                "UTM_E": "100.0",
                "UTM_N": "200.0",
                "Secret_Gold_Halo": "2.0",
                "Secret_Silver_Oxide": "0.1",
                "Secret_Tunnel_Ceiling": "0.0",
                "Secret_Thermal_Inertia": "0.0",
                "Secret_Chemical_Protector": "0.4",
                "Secret_Hidden_Doors": "0.0",
                "REPORT_640_Mass_Report": "1.5",
                "REPORT_640_Pottery_Report": "0.0",
                "REPORT_640_FINAL_Zero_Point_Targets": "0.0",
            },
            {
                "row": "2",
                "col": "2",
                "UTM_E": "500.0",
                "UTM_N": "600.0",
                "Secret_Gold_Halo": "0.0",
                "Secret_Silver_Oxide": "0.0",
                "Secret_Tunnel_Ceiling": "2.0",
                "Secret_Thermal_Inertia": "1.0",
                "Secret_Chemical_Protector": "0.0",
                "Secret_Hidden_Doors": "0.0",
                "REPORT_640_Mass_Report": "0.0",
                "REPORT_640_Pottery_Report": "0.0",
                "REPORT_640_FINAL_Zero_Point_Targets": "1.0",
            },
        ],
    )

    _write_csv(
        focus / "AI_FOCUS_17M_TARGETS_V7_2.csv",
        [
            {
                "Target_ID": "T001",
                "Classification": "TEST_TARGET",
                "UTM_E": "101.0",
                "UTM_N": "201.0",
            }
        ],
    )

    paths = write_plan_b33_metal_fingerprint_diagnostic_outputs(tmp_path, "run-33")

    assert paths["csv"] == focus / OUTPUT_CSV_NAME
    assert paths["json"] == focus / OUTPUT_JSON_NAME
    assert paths["txt"] == focus / OUTPUT_TXT_NAME

    payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert payload["source_cell"] == SOURCE_CELL
    assert payload["status"] == "implemented_private_diagnostic"
    assert payload["privacy"] == "FILESYSTEM_ONLY"
    assert payload["http_servable"] is False
    assert payload["frontend_visible"] is False
    assert payload["downloadable_via_api"] is False
    assert payload["uses_model_inference"] is False
    assert payload["imports_torch"] is False
    assert payload["loads_weights"] is False
    assert payload["runs_forward_pass"] is False
    assert payload["creates_geojson"] is False
    assert payload["creates_kmz"] is False
    assert payload["target_count"] == 1

    record = payload["records"][0]
    assert record["Target_ID"] == "T001"
    assert record["Nearest_Pixel_Row"] == "1"
    assert record["Nearest_Pixel_Col"] == "1"
    assert record["Best_Material"] == "Gold"

    txt = paths["txt"].read_text(encoding="utf-8")
    assert "AI METAL FINGERPRINT DIAGNOSTIC V7.2" in txt
    assert "source_cell=cell_185" in txt


def test_plan_b33_module_does_not_expose_model_execution_functions():
    import app.pipeline.parity.metal_fingerprint_diagnostic as module

    forbidden_prefixes = (
        "train_",
        "fit_",
        "learn_",
        "infer_",
        "predict_",
        "run_model_",
        "load_model_",
        "download_",
        "install_",
        "forward_",
    )
    forbidden = [name for name in dir(module) if name.startswith(forbidden_prefixes)]

    assert forbidden == []
