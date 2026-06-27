from __future__ import annotations

from datetime import UTC, datetime
import csv
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "plan_b33_metal_fingerprint_diagnostic_v1"
SOURCE_CELL = "cell_185"
SOURCE_NOTEBOOK_FAMILY = "METAL_FINGERPRINT_DIAGNOSTIC"

FOCUS_DIR_PARTS = ("full_job", "focus")
PIXEL_REPORT_NAME = "AI_FOCUS_17M_PIXEL_REPORT_V7_2.csv"
TARGET_REPORT_NAME = "AI_FOCUS_17M_TARGETS_V7_2.csv"

OUTPUT_CSV_NAME = "AI_METAL_FINGERPRINT_DIAGNOSTIC_V7_2.csv"
OUTPUT_JSON_NAME = "AI_METAL_FINGERPRINT_DIAGNOSTIC_V7_2.json"
OUTPUT_TXT_NAME = "AI_METAL_FINGERPRINT_DIAGNOSTIC_V7_2.txt"

SCORE_LABELS = [
    "Gold",
    "Silver",
    "Copper",
    "Ingots",
    "Coins",
    "Mixed_Metals",
    "Pottery",
    "Glass",
    "Stone_Block",
    "Pure_Void",
]


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _nearest_pixel_signature(target: dict[str, str], pixel_rows: list[dict[str, str]]) -> dict[str, str]:
    e = _to_float(target.get("UTM_E"))
    n = _to_float(target.get("UTM_N"))

    best_row = pixel_rows[0]
    best_d2 = float("inf")

    for row in pixel_rows:
        pe = _to_float(row.get("UTM_E"))
        pn = _to_float(row.get("UTM_N"))
        d2 = (pe - e) ** 2 + (pn - n) ** 2
        if d2 < best_d2:
            best_d2 = d2
            best_row = row

    return best_row


def diagnose_metal_signature(sig_row: dict[str, str]) -> tuple[dict[str, float], str, float]:
    gold_halo = _to_float(sig_row.get("Secret_Gold_Halo"))
    silver_ox = _to_float(sig_row.get("Secret_Silver_Oxide"))
    tunnel = _to_float(sig_row.get("Secret_Tunnel_Ceiling"))
    thermal = _to_float(sig_row.get("Secret_Thermal_Inertia"))
    chem = _to_float(sig_row.get("Secret_Chemical_Protector"))
    hidden = _to_float(sig_row.get("Secret_Hidden_Doors"))
    mass = _to_float(sig_row.get("REPORT_640_Mass_Report"))
    pottery = _to_float(sig_row.get("REPORT_640_Pottery_Report"))
    zero = _to_float(sig_row.get("REPORT_640_FINAL_Zero_Point_Targets"))

    scores = {
        "Gold": 1.45 * gold_halo + 0.90 * mass + 0.35 * chem - 0.35 * pottery - 0.20 * tunnel,
        "Silver": 1.35 * silver_ox + 0.60 * mass + 0.15 * chem - 0.20 * pottery,
        "Copper": 0.75 * silver_ox + 0.85 * mass + 0.20 * chem - 0.10 * tunnel,
        "Ingots": 1.10 * mass + 0.85 * gold_halo + 0.35 * silver_ox + 0.20 * hidden,
        "Coins": 0.75 * silver_ox + 0.65 * gold_halo + 0.35 * mass + 0.15 * pottery,
        "Mixed_Metals": 0.80 * mass + 0.55 * silver_ox + 0.45 * gold_halo + 0.25 * chem,
        "Pottery": 1.20 * pottery + 0.20 * thermal - 0.20 * mass,
        "Glass": 0.95 * pottery + 0.30 * thermal + 0.10 * chem,
        "Stone_Block": 0.95 * mass + 0.30 * hidden - 0.25 * gold_halo - 0.15 * silver_ox,
        "Pure_Void": 1.20 * tunnel + 0.55 * thermal + 0.20 * zero - 0.35 * mass,
    }

    best_label = max(scores, key=scores.get)
    best_score = float(scores[best_label])
    return scores, best_label, best_score


def build_metal_fingerprint_diagnostic(run_dir: str | Path, run_id: str) -> dict[str, Any]:
    run_dir = Path(run_dir)
    focus_dir = run_dir.joinpath(*FOCUS_DIR_PARTS)

    pixel_path = focus_dir / PIXEL_REPORT_NAME
    target_path = focus_dir / TARGET_REPORT_NAME

    if not pixel_path.is_file():
        raise FileNotFoundError(f"Pixel fingerprint report not found: {pixel_path}")
    if not target_path.is_file():
        raise FileNotFoundError(f"Target report not found: {target_path}")

    pixel_rows = _read_csv(pixel_path)
    target_rows = _read_csv(target_path)

    if not pixel_rows:
        raise RuntimeError("Pixel fingerprint report is empty.")
    if not target_rows:
        raise RuntimeError("Target report is empty.")

    diagnostic_rows: list[dict[str, Any]] = []

    for i, target in enumerate(target_rows, start=1):
        sig = _nearest_pixel_signature(target, pixel_rows)
        scores, best_label, best_score = diagnose_metal_signature(sig)

        target_id = target.get("Target_ID") or target.get("???_?????") or str(i)
        classification = target.get("Classification") or target.get("???_?????") or "UNRESOLVED_TARGET"

        out: dict[str, Any] = {
            "Target_ID": target_id,
            "Classification": classification,
            "Source_Cell": SOURCE_CELL,
            "Nearest_Pixel_Row": sig.get("row", ""),
            "Nearest_Pixel_Col": sig.get("col", ""),
            "Best_Material": best_label,
            "Best_Score": round(best_score, 6),
        }

        for label in SCORE_LABELS:
            out[f"Score_{label}"] = round(float(scores[label]), 6)

        # Keep UTM local/private because this artifact is filesystem-only.
        out["UTM_E"] = round(_to_float(target.get("UTM_E")), 3)
        out["UTM_N"] = round(_to_float(target.get("UTM_N")), 3)

        diagnostic_rows.append(out)

    payload = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "source_cell": SOURCE_CELL,
        "source_notebook_family": SOURCE_NOTEBOOK_FAMILY,
        "status": "implemented_private_diagnostic",
        "privacy": "FILESYSTEM_ONLY",
        "http_servable": False,
        "frontend_visible": False,
        "downloadable_via_api": False,
        "uses_model_inference": False,
        "imports_torch": False,
        "loads_weights": False,
        "runs_forward_pass": False,
        "creates_geojson": False,
        "creates_kmz": False,
        "target_count": len(diagnostic_rows),
        "score_labels": SCORE_LABELS,
        "input_files": {
            "target_report": str(Path(*FOCUS_DIR_PARTS) / TARGET_REPORT_NAME),
            "pixel_report": str(Path(*FOCUS_DIR_PARTS) / PIXEL_REPORT_NAME),
        },
        "output_files": {
            "csv": str(Path(*FOCUS_DIR_PARTS) / OUTPUT_CSV_NAME),
            "json": str(Path(*FOCUS_DIR_PARTS) / OUTPUT_JSON_NAME),
            "txt": str(Path(*FOCUS_DIR_PARTS) / OUTPUT_TXT_NAME),
        },
        "records": diagnostic_rows,
    }

    return payload


def write_plan_b33_metal_fingerprint_diagnostic_outputs(
    run_dir: str | Path,
    run_id: str,
) -> dict[str, Path]:
    run_dir = Path(run_dir)
    focus_dir = run_dir.joinpath(*FOCUS_DIR_PARTS)
    focus_dir.mkdir(parents=True, exist_ok=True)

    payload = build_metal_fingerprint_diagnostic(run_dir, run_id)
    records = payload["records"]
    assert isinstance(records, list)

    csv_path = focus_dir / OUTPUT_CSV_NAME
    json_path = focus_dir / OUTPUT_JSON_NAME
    txt_path = focus_dir / OUTPUT_TXT_NAME

    _write_csv(csv_path, records)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "AI METAL FINGERPRINT DIAGNOSTIC V7.2",
        f"source_cell={SOURCE_CELL}",
        f"status={payload['status']}",
        f"privacy={payload['privacy']}",
        f"target_count={payload['target_count']}",
        "",
    ]

    for row in records:
        lines.extend([
            f"Target {row['Target_ID']}: {row['Classification']}",
            f"  Best_Material={row['Best_Material']} Best_Score={row['Best_Score']}",
            f"  Gold={row['Score_Gold']} Silver={row['Score_Silver']} Copper={row['Score_Copper']}",
            f"  Ingots={row['Score_Ingots']} Coins={row['Score_Coins']} Mixed={row['Score_Mixed_Metals']}",
            f"  Pottery={row['Score_Pottery']} Glass={row['Score_Glass']} Stone={row['Score_Stone_Block']} Void={row['Score_Pure_Void']}",
            "",
        ])

    txt_path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "csv": csv_path,
        "json": json_path,
        "txt": txt_path,
    }
