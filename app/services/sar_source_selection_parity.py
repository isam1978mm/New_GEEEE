from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

SAR_SOURCE_SELECTION_PARITY_PREFIX = "sar_source_selection_parity"
SAR_SOURCE_SELECTION_FIELDNAMES = [
    "check",
    "status",
    "notebook_value",
    "app_value",
    "evidence",
    "recommended_next_action",
]
NOTEBOOK_SAR_QA_PATTERNS = (
    "QA/QA_RADAR_CELL25_PAIR_IDS*.json",
    "QA/QA_S1_MASTER_UNITS.json",
    "QA/QA_RADAR_META*.json",
    "QA_RADAR_CELL25_PAIR_IDS*.json",
    "QA_S1_MASTER_UNITS.json",
    "QA_RADAR_META*.json",
    "SUMMARY_RADAR*.csv",
    "qa/sar/sar_pair_diagnostics.json",
    "*sar*selection*.json",
    "*SAR*selection*.json",
)


@dataclass(frozen=True, slots=True)
class SarSourceSelectionRow:
    check: str
    status: str
    notebook_value: str
    app_value: str
    evidence: str
    recommended_next_action: str

    def to_report_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class NotebookSarMetadata:
    root_label: str
    relative_path: str
    payload: dict[str, Any]


def build_sar_source_selection_parity_report(
    *,
    app_run_dir: Path,
    notebook_roots: list[Path],
    cell25_pairs_json: list[Path] | None = None,
) -> dict[str, Any]:
    app_payload = _load_app_sar_metadata(app_run_dir)
    notebook_metadata = find_notebook_sar_metadata(notebook_roots)
    notebook_metadata.extend(load_cell25_pair_sidecars(cell25_pairs_json or []))
    rows = build_sar_source_selection_rows(app_payload=app_payload, notebook_metadata=notebook_metadata)
    status_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row.status] = status_counts.get(row.status, 0) + 1
    return {
        "report_type": "sar_source_selection_parity",
        "artifact_class": "FILESYSTEM_ONLY",
        "local_only": True,
        "app_run_id": app_run_dir.name,
        "notebook_root_labels": [root.name for root in notebook_roots],
        "app_metadata_file": "qa/sar/sar_pair_diagnostics.json"
        if (app_run_dir / "qa" / "sar" / "sar_pair_diagnostics.json").is_file()
        else "",
        "notebook_metadata_files": [
            {"root_label": item.root_label, "relative_path": item.relative_path} for item in notebook_metadata
        ],
        "rows": [row.to_report_dict() for row in rows],
        "summary": {
            "row_count": len(rows),
            "status_counts": status_counts,
        },
    }


def write_sar_source_selection_parity_report(
    *,
    app_run_dir: Path,
    notebook_roots: list[Path],
    output_dir: Path,
    cell25_pairs_json: list[Path] | None = None,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_sar_source_selection_parity_report(
        app_run_dir=app_run_dir,
        notebook_roots=notebook_roots,
        cell25_pairs_json=cell25_pairs_json,
    )
    stem = f"{SAR_SOURCE_SELECTION_PARITY_PREFIX}_{app_run_dir.name}"
    json_path = output_dir / f"{stem}.json"
    csv_path = output_dir / f"{stem}.csv"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SAR_SOURCE_SELECTION_FIELDNAMES)
        writer.writeheader()
        for row in report["rows"]:
            writer.writerow({field: row.get(field, "") for field in SAR_SOURCE_SELECTION_FIELDNAMES})
    return json_path, csv_path


def find_notebook_sar_metadata(notebook_roots: list[Path]) -> list[NotebookSarMetadata]:
    matches: dict[tuple[str, str], NotebookSarMetadata] = {}
    for root in notebook_roots:
        for pattern in NOTEBOOK_SAR_QA_PATTERNS:
            for path in root.rglob(pattern):
                if not path.is_file():
                    continue
                relative_path = path.relative_to(root).as_posix()
                payload = _load_notebook_metadata_payload(path)
                matches[(root.name, relative_path)] = NotebookSarMetadata(
                    root_label=root.name,
                    relative_path=relative_path,
                    payload=payload,
                )
    return list(matches.values())


def load_cell25_pair_sidecars(paths: list[Path]) -> list[NotebookSarMetadata]:
    metadata: list[NotebookSarMetadata] = []
    for path in paths:
        if not path.is_file():
            continue
        metadata.append(
            NotebookSarMetadata(
                root_label=path.parent.name or "cell25_pair_sidecar",
                relative_path=path.name,
                payload=_load_notebook_metadata_payload(path),
            )
        )
    return metadata


def build_sar_source_selection_rows(
    *,
    app_payload: dict[str, Any] | None,
    notebook_metadata: list[NotebookSarMetadata],
) -> list[SarSourceSelectionRow]:
    notebook_payload = _merge_notebook_payloads(notebook_metadata)
    cell25_payload = _cell25_payload(notebook_metadata)
    notebook_files = ", ".join(f"{item.root_label}:{item.relative_path}" for item in notebook_metadata)
    rows: list[SarSourceSelectionRow] = [
        SarSourceSelectionRow(
            check="notebook_qa_metadata",
            status="FOUND" if notebook_metadata else "MISSING",
            notebook_value=notebook_files,
            app_value="qa/sar/sar_pair_diagnostics.json" if app_payload is not None else "",
            evidence=(
                "Notebook SAR QA metadata was found by root label and relative path."
                if notebook_metadata
                else "No notebook SAR QA metadata file was found in the provided roots."
            ),
            recommended_next_action=(
                "Compare source-selection fields below before changing SAR formulas."
                if notebook_metadata
                else "Provide SUMMARY_RADAR*.csv or SAR selection JSON from the notebook run."
            ),
        )
    ]
    if app_payload is None:
        rows.append(
            SarSourceSelectionRow(
                check="app_sar_metadata",
                status="MISSING",
                notebook_value="",
                app_value="",
                evidence="The app run does not contain qa/sar/sar_pair_diagnostics.json.",
                recommended_next_action="Run the SAR RTC stage with F13 metadata capture enabled by default.",
            )
        )
        return rows

    rows.extend(
        [
            _profile_row(
                check="cell25_pixel_export_profile",
                notebook_payload=notebook_payload,
                app_payload=app_payload,
                expected_profile="cell25_pixel_export",
            ),
            _cell21_auxiliary_row(notebook_metadata),
            _compare_scalar(
                check="collection_id",
                notebook_value=_first_value(notebook_payload, "collection_id"),
                app_value=str(app_payload.get("collection_id", "")),
                missing_evidence="Notebook metadata does not declare the Sentinel-1 collection id.",
                mismatch_action="Confirm both runs use the same Sentinel-1 collection before changing SAR math.",
            ),
            _compare_scalar(
                check="date_window",
                notebook_value=_date_window_value(notebook_payload),
                app_value=_date_window_value(app_payload),
                missing_evidence="Notebook metadata does not declare a comparable date window.",
                mismatch_action="Reconcile notebook/app SAR date windows before comparing pixel values.",
            ),
            _compare_scalar(
                check="image_identity",
                notebook_value=_cell25_pair_identity_value(cell25_payload, notebook_payload),
                app_value=_pair_identity_value(app_payload),
                missing_evidence=_missing_cell25_pair_evidence(
                    cell25_payload,
                    fallback="Notebook metadata does not expose selected ASC/DESC image ids.",
                ),
                mismatch_action="Align selected Sentinel-1 image ids before changing RTC formulas.",
                missing_status=_missing_cell25_pair_status(cell25_payload),
                missing_action=_missing_cell25_pair_action(cell25_payload),
            ),
            _compare_scalar(
                check="orbit_pairing",
                notebook_value=_cell25_pair_delta_value(cell25_payload, notebook_payload),
                app_value=_pair_delta_value(app_payload),
                missing_evidence=_missing_cell25_pair_evidence(
                    cell25_payload,
                    fallback="Notebook metadata does not expose comparable pair time deltas.",
                ),
                mismatch_action="Reconcile orbit pair selection and pair time deltas before changing SAR math.",
                missing_status=_missing_cell25_pair_status(cell25_payload),
                missing_action=_missing_cell25_pair_action(cell25_payload),
            ),
            _source_identity_classification_row(app_payload=app_payload, cell25_payload=cell25_payload),
            _compare_scalar(
                check="vv_vh_pair_count",
                notebook_value=_pair_count_value(notebook_payload),
                app_value=_pair_count_value(app_payload),
                missing_evidence="Notebook metadata does not expose a comparable VV/VH pair count.",
                mismatch_action="Reconcile pair count before changing SAR math.",
            ),
            _compare_scalar(
                check="orbit_directions",
                notebook_value=_orbit_directions_value(notebook_payload),
                app_value=_orbit_directions_value(app_payload),
                missing_evidence="Notebook metadata does not expose comparable orbit directions.",
                mismatch_action="Confirm both runs use the same ASC/DESC orbit-direction policy before changing SAR math.",
            ),
            _compare_scalar(
                check="source_parameters",
                notebook_value=_source_parameters_value(notebook_payload),
                app_value=_source_parameters_value(app_payload),
                missing_evidence="Notebook metadata does not expose comparable SAR source parameters.",
                mismatch_action="Reconcile orbit window, pair cap, and master image metadata before changing SAR formulas.",
            ),
            _master_id_row(notebook_payload=notebook_payload, app_payload=app_payload),
            _band_mapping_row(app_payload=app_payload, notebook_payload=notebook_payload),
            _processing_path_row(app_payload=app_payload, notebook_payload=notebook_payload),
            SarSourceSelectionRow(
                check="radar_linear_support_stack",
                status="DOWNSTREAM_DIAGNOSTIC",
                notebook_value="",
                app_value="",
                evidence="Radar tensor stack parity should be evaluated after SAR source-selection identity is resolved.",
                recommended_next_action="Do not rewrite stack logic until VV/VH/logRatio/incidence source parity is understood.",
            ),
        ]
    )
    return rows


def _load_app_sar_metadata(app_run_dir: Path) -> dict[str, Any] | None:
    path = app_run_dir / "qa" / "sar" / "sar_pair_diagnostics.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _load_notebook_metadata_payload(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if path.name.startswith("QA_RADAR_CELL25_PAIR_IDS"):
            return _normalize_cell25_pair_sidecar_payload(payload, path.name)
        if path.name == "QA_S1_MASTER_UNITS.json":
            return _normalize_qa_s1_master_units_payload(payload)
        if path.name.startswith("QA_RADAR_META"):
            return _normalize_qa_radar_meta_payload(payload, path.name)
        return payload
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    payload: dict[str, Any] = {"rows": rows}
    if rows:
        payload.update(_collapse_csv_rows(rows))
        profile = _profile_from_text(path.name)
        if profile:
            payload.update(profile)
    return payload


def _normalize_cell25_pair_sidecar_payload(payload: dict[str, Any], filename: str) -> dict[str, Any]:
    profile = _profile_from_text(filename)
    pairs = _normalize_pairs_used(payload.get("pairs") or payload.get("pairs_used") or [])
    normalized: dict[str, Any] = {
        "source_kind": "QA_RADAR_CELL25_PAIR_IDS",
        "selection_profile": "cell25_pixel_export",
        "pairs": pairs,
        "pair_count": len(pairs),
    }
    if profile:
        normalized.update(profile)
    source_profile = payload.get("source_profile") or payload.get("selection_profile")
    if source_profile not in (None, ""):
        normalized["selection_profile"] = str(source_profile)
    for key in ("orbit_window_days", "pair_cap_hours", "selected_asc_track", "selected_desc_track"):
        value = payload.get(key) or payload.get(key.upper())
        if value not in (None, ""):
            normalized[key] = _normalize_number_string(value) if key.endswith(("days", "hours", "track")) else str(value)
    start = payload.get("start_date") or payload.get("START")
    end = payload.get("end_date") or payload.get("END")
    if start and end:
        normalized["date_window"] = {"start_date": str(start), "end_date": str(end)}
    return normalized


def _normalize_qa_s1_master_units_payload(payload: dict[str, Any]) -> dict[str, Any]:
    pairs = _normalize_pairs_used(payload.get("pairs_used") or payload.get("PAIRS_USED") or [])
    normalized: dict[str, Any] = {
        "source_kind": "QA_S1_MASTER_UNITS",
        "pairs": pairs,
        "pair_count": len(pairs),
    }
    master_id = payload.get("MASTER_ID") or payload.get("master_id")
    if master_id not in (None, ""):
        normalized["master_id"] = str(master_id)
    orbit_window_days = payload.get("orbit_window_days") or payload.get("ORBIT_WINDOW_DAYS")
    if orbit_window_days not in (None, ""):
        normalized["orbit_window_days"] = _normalize_number_string(orbit_window_days)
    pair_cap_hours = payload.get("pair_cap_hours") or payload.get("PAIR_CAP_HOURS")
    if pair_cap_hours not in (None, ""):
        normalized["pair_cap_hours"] = _normalize_number_string(pair_cap_hours)
    return normalized


def _normalize_qa_radar_meta_payload(payload: dict[str, Any], filename: str) -> dict[str, Any]:
    profile = _profile_from_text(filename)
    normalized: dict[str, Any] = {
        "source_kind": "QA_RADAR_META",
        "selection_profile": "cell25_pixel_export",
        "processing_path": {
            "local_dem_rtc": bool(payload.get("LOCAL_DEM_RTC")),
            "grid_sampling": "sampleRectangle",
        },
    }
    if profile:
        normalized.update(profile)
    pair_count = payload.get("pairs_used")
    if isinstance(pair_count, list):
        pairs = _normalize_pairs_used(pair_count)
        if pairs:
            normalized["pairs"] = pairs
            normalized["pair_count"] = len(pairs)
    elif pair_count not in (None, ""):
        normalized["pair_count"] = _normalize_number_string(pair_count)
    start = payload.get("START")
    end = payload.get("END")
    if start and end:
        normalized["date_window"] = {"start_date": str(start), "end_date": str(end)}
    return normalized


def _profile_from_text(value: str) -> dict[str, str]:
    profile: dict[str, str] = {}
    pair_match = re.search(r"pairdt(?P<hours>\d+)h", value)
    orbit_match = re.search(r"orbitpm(?P<days>\d+)d", value)
    pairs_match = re.search(r"pairs(?P<count>\d+)", value)
    if pair_match:
        profile["pair_cap_hours"] = _normalize_number_string(pair_match.group("hours"))
    if orbit_match:
        profile["orbit_window_days"] = _normalize_number_string(orbit_match.group("days"))
    if pairs_match:
        profile["pair_count"] = _normalize_number_string(pairs_match.group("count"))
    if profile:
        profile["selection_profile"] = "cell25_pixel_export"
    return profile


def _normalize_pairs_used(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    pairs: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        asc_id = item.get("asc_id") or item.get("ASC_ID") or item.get("ascending_id") or item.get("ASCENDING_ID")
        desc_id = item.get("desc_id") or item.get("DESC_ID") or item.get("descending_id") or item.get("DESCENDING_ID")
        if asc_id and desc_id:
            pair: dict[str, str] = {"asc_id": str(asc_id), "desc_id": str(desc_id)}
            dt_hours = item.get("dt_hours") or item.get("DT_HOURS") or item.get("pair_dt_hours") or item.get("PAIR_DT_HOURS")
            if dt_hours not in (None, ""):
                pair["dt_hours"] = _normalize_number_string(dt_hours)
            pairs.append(pair)
    return pairs


def _collapse_csv_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    collapsed: dict[str, Any] = {}
    for row in rows:
        normalized = {_normalize_key(key): value for key, value in row.items() if value not in (None, "")}
        for key, value in normalized.items():
            if key in {"band_name", "band"}:
                collapsed.setdefault("selected_band_list", []).append(value)
            elif key not in collapsed:
                collapsed[key] = value
    if "selected_band_list" in collapsed:
        collapsed["selected_band_list"] = sorted(set(collapsed["selected_band_list"]))
    return collapsed


def _merge_notebook_payloads(metadata: list[NotebookSarMetadata]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for item in sorted(metadata, key=_metadata_priority):
        for key, value in item.payload.items():
            normalized_key = _normalize_key(key)
            if normalized_key not in merged and value not in (None, "", []):
                merged[normalized_key] = value
    return merged


def _metadata_priority(item: NotebookSarMetadata) -> int:
    if item.payload.get("source_kind") == "QA_RADAR_CELL25_PAIR_IDS":
        return 0
    if item.payload.get("selection_profile") == "cell25_pixel_export":
        return 1
    if item.payload.get("source_kind") == "QA_S1_MASTER_UNITS":
        return 3
    return 2


def _cell25_payload(metadata: list[NotebookSarMetadata]) -> dict[str, Any] | None:
    for item in sorted(metadata, key=_metadata_priority):
        if item.payload.get("selection_profile") == "cell25_pixel_export":
            return item.payload
    return None


def _profile_row(
    *,
    check: str,
    notebook_payload: dict[str, Any],
    app_payload: dict[str, Any],
    expected_profile: str,
) -> SarSourceSelectionRow:
    notebook_value = str(notebook_payload.get("selection_profile") or "")
    source_filters = app_payload.get("source_filters")
    app_value = ""
    if isinstance(source_filters, dict):
        app_value = str(source_filters.get("selection_profile") or "")
    status = "MATCH" if notebook_value == expected_profile and app_value == expected_profile else "MISMATCH"
    return SarSourceSelectionRow(
        check=check,
        status=status,
        notebook_value=notebook_value,
        app_value=app_value,
        evidence="SAR pixel parity compares the Cell 25 pixel-export profile, not the Cell 21 master-units QA profile.",
        recommended_next_action=(
            "No action required."
            if status == "MATCH"
            else "Use Cell 25 QA_RADAR_META/SUMMARY metadata for SAR pixel-output parity."
        ),
    )


def _cell21_auxiliary_row(metadata: list[NotebookSarMetadata]) -> SarSourceSelectionRow:
    found = any(item.payload.get("source_kind") == "QA_S1_MASTER_UNITS" for item in metadata)
    return SarSourceSelectionRow(
        check="cell21_master_units_qa_profile",
        status="AUXILIARY_QA" if found else "MISSING",
        notebook_value="cell21_master_units_qa_auxiliary" if found else "",
        app_value="auxiliary_only",
        evidence="QA_S1_MASTER_UNITS is reported as auxiliary QA and does not drive SAR pixel-output source selection.",
        recommended_next_action="Do not use Cell 21 pair parameters for pixel outputs unless Cell 25 imports them.",
    )


def _compare_scalar(
    *,
    check: str,
    notebook_value: str,
    app_value: str,
    missing_evidence: str,
    mismatch_action: str,
    missing_status: str = "NEEDS_MANUAL_REVIEW",
    missing_action: str = "Capture this field from the notebook run if available.",
) -> SarSourceSelectionRow:
    if not notebook_value:
        return SarSourceSelectionRow(
            check=check,
            status=missing_status,
            notebook_value="",
            app_value=app_value,
            evidence=missing_evidence,
            recommended_next_action=missing_action,
        )
    status = "MATCH" if notebook_value == app_value else "MISMATCH"
    return SarSourceSelectionRow(
        check=check,
        status=status,
        notebook_value=notebook_value,
        app_value=app_value,
        evidence=(
            f"{check} matches between notebook and app metadata."
            if status == "MATCH"
            else f"{check} differs between notebook and app metadata."
        ),
        recommended_next_action="No action required." if status == "MATCH" else mismatch_action,
    )


def _cell25_pair_identity_value(cell25_payload: dict[str, Any] | None, merged_payload: dict[str, Any]) -> str:
    if cell25_payload is None:
        return ""
    return _pair_identity_value(cell25_payload)


def _cell25_pair_delta_value(cell25_payload: dict[str, Any] | None, merged_payload: dict[str, Any]) -> str:
    if cell25_payload is None:
        return ""
    return _pair_delta_value(cell25_payload)


def _missing_cell25_pair_status(cell25_payload: dict[str, Any] | None) -> str:
    if cell25_payload is None:
        return "MISSING_CELL25_PAIR_IDS"
    return "MISSING_CELL25_PAIR_IDS"


def _missing_cell25_pair_action(cell25_payload: dict[str, Any] | None) -> str:
    if cell25_payload is None:
        return "Provide a true Cell 25 QA_RADAR_CELL25_PAIR_IDS sidecar; do not use Cell 21 pair IDs as fallback truth."
    return "Cell 25 QA_RADAR_META lacks per-pair ASC/DESC IDs; do not compare against Cell 21 auxiliary pair IDs."


def _missing_cell25_pair_evidence(cell25_payload: dict[str, Any] | None, *, fallback: str) -> str:
    if cell25_payload is None:
        return f"{fallback} Cell 21 QA_S1_MASTER_UNITS pair IDs are auxiliary and are not used as Cell 25 truth."
    return "Cell 25 QA_RADAR_META proves the pixel-export profile but lacks per-pair ASC/DESC IDs and pair time deltas."


def _source_identity_classification_row(
    *,
    app_payload: dict[str, Any],
    cell25_payload: dict[str, Any] | None,
) -> SarSourceSelectionRow:
    app_identity = _pair_identity_value(app_payload)
    app_deltas = _pair_delta_value(app_payload)
    notebook_identity = "" if cell25_payload is None else _pair_identity_value(cell25_payload)
    notebook_deltas = "" if cell25_payload is None else _pair_delta_value(cell25_payload)
    if not notebook_identity:
        status = "SOURCE_ID_UNPROVEN"
        evidence = "True Cell 25 pair IDs are missing; source identity remains unproven and Cell 21 IDs are not used as fallback."
        action = "Capture QA_RADAR_CELL25_PAIR_IDS from Cell 25 before attributing residuals to processing math."
    elif notebook_identity != app_identity:
        status = "SOURCE_ID_MISMATCH"
        evidence = "True Cell 25 pair IDs differ from app SAR pair diagnostics."
        action = "Reconcile source identity before changing SAR processing math."
    elif notebook_deltas and app_deltas and notebook_deltas != app_deltas:
        status = "SOURCE_ID_MISMATCH"
        evidence = "True Cell 25 pair IDs match but pair time deltas differ from app SAR pair diagnostics."
        action = "Reconcile orbit pairing before changing SAR processing math."
    else:
        status = "SOURCE_ID_MATCH_PROCESSING_DELTA_REMAINS"
        evidence = "True Cell 25 pair IDs match the app pair diagnostics; remaining numeric residuals should be diagnosed as processing deltas."
        action = "Use SAR processing parity diagnostics for the remaining VV/VH residual."
    return SarSourceSelectionRow(
        check="source_identity_classification",
        status=status,
        notebook_value=notebook_identity,
        app_value=app_identity,
        evidence=evidence,
        recommended_next_action=action,
    )


def _band_mapping_row(*, app_payload: dict[str, Any], notebook_payload: dict[str, Any]) -> SarSourceSelectionRow:
    mapping = app_payload.get("angle_incidence_mapping", {})
    notebook_band = str(mapping.get("notebook_band", "angle"))
    app_band = str(mapping.get("app_output_band", "incidence"))
    notebook_bands = _list_value(notebook_payload.get("selected_band_list"))
    app_bands = _list_value(app_payload.get("output_band_list"))
    status = "DOCUMENTED" if notebook_band == "angle" and app_band == "incidence" else "NEEDS_MANUAL_REVIEW"
    return SarSourceSelectionRow(
        check="angle_incidence_mapping",
        status=status,
        notebook_value=",".join(notebook_bands),
        app_value=",".join(app_bands),
        evidence=f"Notebook angle band is mapped to app incidence output as local-only metadata: {notebook_band}->{app_band}.",
        recommended_next_action="Treat angle/incidence naming as a mapping issue unless source metadata proves a numeric source mismatch.",
    )


def _processing_path_row(*, app_payload: dict[str, Any], notebook_payload: dict[str, Any]) -> SarSourceSelectionRow:
    app_path = app_payload.get("processing_path", {})
    notebook_path = notebook_payload.get("processing_path", {})
    app_value = _compact_json(app_path)
    notebook_value = _compact_json(notebook_path)
    status = "NEEDS_MANUAL_REVIEW" if not notebook_value else ("MATCH" if notebook_value == app_value else "MISMATCH")
    return SarSourceSelectionRow(
        check="processing_path",
        status=status,
        notebook_value=notebook_value,
        app_value=app_value,
        evidence="Processing-path flags cover local DEM RTC, refined-Lee filtering, dB-linear-dB processing, and grid sampling.",
        recommended_next_action=(
            "Capture notebook processing-path flags if available."
            if status == "NEEDS_MANUAL_REVIEW"
            else "No action required."
            if status == "MATCH"
            else "Reconcile RTC/filtering/source processing before changing SAR formulas."
        ),
    )


def _master_id_row(*, notebook_payload: dict[str, Any], app_payload: dict[str, Any]) -> SarSourceSelectionRow:
    notebook_value = str(notebook_payload.get("master_id") or notebook_payload.get("MASTER_ID") or "")
    app_value = str(app_payload.get("master_id") or app_payload.get("MASTER_ID") or "")
    if notebook_value and not app_value:
        return SarSourceSelectionRow(
            check="master_id",
            status="NOTEBOOK_ONLY",
            notebook_value=notebook_value,
            app_value="",
            evidence="Notebook QA_S1_MASTER_UNITS records MASTER_ID, while app pair selection is driven by selected ASC/DESC pairs.",
            recommended_next_action="Treat MASTER_ID as notebook-only provenance unless app selection starts using it explicitly.",
        )
    status = "MATCH" if notebook_value == app_value else "MISMATCH"
    return SarSourceSelectionRow(
        check="master_id",
        status=status,
        notebook_value=notebook_value,
        app_value=app_value,
        evidence="MASTER_ID comparison is provenance-only and does not change SAR formulas.",
        recommended_next_action="No action required." if status == "MATCH" else "Inspect master-image provenance if pair identities still differ.",
    )


def _first_value(payload: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = payload.get(_normalize_key(key))
        if value not in (None, "", []):
            return _string_value(value)
    return ""


def _date_window_value(payload: dict[str, Any]) -> str:
    date_window = payload.get("date_window")
    if isinstance(date_window, dict):
        start = date_window.get("start_date") or date_window.get("start")
        end = date_window.get("end_date") or date_window.get("end")
        if start and end:
            return f"{start}..{end}"
    start = payload.get("start_date") or payload.get("start")
    end = payload.get("end_date") or payload.get("end")
    return f"{start}..{end}" if start and end else ""


def _pair_identity_value(payload: dict[str, Any]) -> str:
    pairs = payload.get("pairs")
    if isinstance(pairs, list):
        values = []
        for pair in pairs:
            if not isinstance(pair, dict):
                continue
            asc_id = pair.get("asc_id") or pair.get("ascending_id")
            desc_id = pair.get("desc_id") or pair.get("descending_id")
            if asc_id and desc_id:
                values.append(f"{asc_id}>{desc_id}")
        return "|".join(values)
    asc_id = payload.get("asc_id") or payload.get("ascending_id")
    desc_id = payload.get("desc_id") or payload.get("descending_id")
    return f"{asc_id}>{desc_id}" if asc_id and desc_id else ""


def _pair_delta_value(payload: dict[str, Any]) -> str:
    pairs = payload.get("pairs")
    if isinstance(pairs, list):
        values = []
        for pair in pairs:
            if not isinstance(pair, dict):
                continue
            value = pair.get("dt_hours") or pair.get("pair_dt_hours")
            if value not in (None, ""):
                values.append(_normalize_number_string(value))
        return "|".join(values)
    value = payload.get("dt_hours") or payload.get("pair_dt_hours")
    return _normalize_number_string(value) if value not in (None, "") else ""


def _pair_count_value(payload: dict[str, Any]) -> str:
    value = payload.get("pair_count") or payload.get("vv_vh_pair_count")
    if value not in (None, ""):
        return str(value)
    pairs = payload.get("pairs")
    if isinstance(pairs, list):
        return str(len(pairs))
    return ""


def _orbit_directions_value(payload: dict[str, Any]) -> str:
    source_filters = payload.get("source_filters")
    if isinstance(source_filters, dict):
        directions = _list_value(source_filters.get("orbit_directions"))
        if directions:
            return ",".join(directions)
    directions = _list_value(payload.get("orbit_directions") or payload.get("orbit_direction"))
    return ",".join(directions)


def _source_parameters_value(payload: dict[str, Any]) -> str:
    values: dict[str, str] = {}
    orbit_window_days = payload.get("orbit_window_days")
    if orbit_window_days in (None, ""):
        source_filters = payload.get("source_filters")
        if isinstance(source_filters, dict):
            orbit_window_days = source_filters.get("max_orbit_dt_days")
    if orbit_window_days not in (None, ""):
        values["orbit_window_days"] = _normalize_number_string(orbit_window_days)
    pair_cap_hours = payload.get("pair_cap_hours")
    if pair_cap_hours in (None, ""):
        source_filters = payload.get("source_filters")
        if isinstance(source_filters, dict):
            pair_cap_hours = source_filters.get("max_pair_dt_hours")
    if pair_cap_hours not in (None, ""):
        values["pair_cap_hours"] = _normalize_number_string(pair_cap_hours)
    return _compact_json(values)


def _normalize_number_string(value: Any) -> str:
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else f"{value:.6f}".rstrip("0").rstrip(".")
    text = str(value)
    try:
        numeric = float(text)
    except ValueError:
        return text
    return str(int(numeric)) if numeric.is_integer() else f"{numeric:.6f}".rstrip("0").rstrip(".")


def _normalize_key(key: str) -> str:
    return key.strip().lower().replace(" ", "_").replace("-", "_")


def _list_value(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, tuple):
        return [str(item) for item in value]
    if isinstance(value, str) and value:
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _string_value(value: Any) -> str:
    if isinstance(value, (dict, list, tuple)):
        return _compact_json(value)
    return str(value)


def _compact_json(value: Any) -> str:
    if value in (None, "", [], {}):
        return ""
    return json.dumps(value, sort_keys=True, separators=(",", ":"))
