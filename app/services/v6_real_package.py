"""V6 real app-output package feed.

This module feeds scored candidates and generated request zones into the existing
V6 package shape, inventory, ZIP, and validation flow.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import io
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence
import zipfile

from app.services.storage import write_bytes_atomic, write_text_atomic
from app.services.v6_generator_package import (
    GENERATOR_STATUS_INVALID,
    GENERATOR_STATUS_VERIFIED,
    V6GeneratedPackageResult,
    validate_generated_v6_payload_shape,
)
from app.services.v6_real_scoring import V6ScoredCandidate
from app.services.v6_real_zones import V6RequestZone, request_zones_to_geojson
from app.services.v6_zip_readiness import build_v6_zip_readiness_report


_TIMESTAMP_PATTERN = re.compile(r"^\d{8}T\d{6}Z$")
_CHUNK_SIZE = 1024 * 1024
_DEFAULT_SOURCE_MODE = "local_existing_run_outputs"
_DEFAULT_SCORE_BASIS = "app_scored_candidates_v6_review_priority_score"
_DEFAULT_GEOMETRY_BASIS = "app_generated_request_zones_from_grid_cells"
_DEFAULT_PACKAGE_PROVENANCE = "app_generated_private_local_export_package"
_DEFAULT_PLACEHOLDER_MAP_LABEL = "visual_inspection_map_is_placeholder_no_imagery"


@dataclass(frozen=True)
class V6RealPackageInputs:
    run_id: str
    timestamp: str
    scored_candidates: tuple[V6ScoredCandidate, ...]
    request_zones: tuple[V6RequestZone, ...]
    source_mode: str = _DEFAULT_SOURCE_MODE
    score_basis: str = _DEFAULT_SCORE_BASIS
    geometry_basis: str = _DEFAULT_GEOMETRY_BASIS
    package_provenance: str = _DEFAULT_PACKAGE_PROVENANCE
    fallback_score_used: bool = False
    fallback_geometry_used: bool = False
    placeholder_map_label: str = _DEFAULT_PLACEHOLDER_MAP_LABEL
    frozen_notebook_parity_claimed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.run_id, str) or not self.run_id.strip():
            raise ValueError("run_id is required")
        if not _TIMESTAMP_PATTERN.fullmatch(self.timestamp):
            raise ValueError("timestamp must use YYYYMMDDTHHMMSSZ format")
        if not self.scored_candidates:
            raise ValueError("scored_candidates must not be empty")
        if not self.request_zones:
            raise ValueError("request_zones must not be empty")

    def safe_summary(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "scored_candidate_count": len(self.scored_candidates),
            "request_zone_count": len(self.request_zones),
            "source_mode": self.source_mode,
            "score_basis": self.score_basis,
            "geometry_basis": self.geometry_basis,
            "package_provenance": self.package_provenance,
            "fallback_score_used": bool(self.fallback_score_used),
            "fallback_geometry_used": bool(self.fallback_geometry_used),
            "placeholder_map_label": self.placeholder_map_label,
            "frozen_notebook_parity_claimed": bool(self.frozen_notebook_parity_claimed),
            "contains_rows": False,
            "contains_geometry": False,
        }

    def provenance_metadata(self) -> dict[str, Any]:
        return {
            "source_mode": self.source_mode,
            "score_basis": self.score_basis,
            "geometry_basis": self.geometry_basis,
            "package_provenance": self.package_provenance,
            "fallback_score_used": bool(self.fallback_score_used),
            "fallback_geometry_used": bool(self.fallback_geometry_used),
            "placeholder_map_label": self.placeholder_map_label,
            "frozen_notebook_parity_claimed": bool(self.frozen_notebook_parity_claimed),
            "privacy": {
                "artifact_class": "LOCAL_SENSITIVE",
                "filesystem_only": True,
                "frontend_metadata_only": True,
                "public_access": False,
            },
        }


def generate_v6_package_from_real_outputs(
    *,
    output_dir: str | Path,
    package_inputs: V6RealPackageInputs,
    package_name: str | None = None,
) -> V6GeneratedPackageResult:
    root = Path(output_dir)
    payload_dir = root / "payloads"
    root.mkdir(parents=True, exist_ok=True)
    payload_dir.mkdir(parents=True, exist_ok=True)

    payloads = build_v6_payloads_from_real_outputs(package_inputs=package_inputs)
    for name, content in payloads.items():
        write_bytes_atomic(payload_dir / name, content)

    inventory_name = f"V6_REAL_GENERATED_inventory_{package_inputs.timestamp}.json"
    zip_name = package_name or f"V6_REAL_GENERATED_{package_inputs.timestamp}.zip"
    inventory_path = root / inventory_name
    zip_path = root / zip_name
    validation_report_path = root / f"V6_REAL_GENERATED_validation_{package_inputs.timestamp}.json"

    records = [
        {
            "file": name,
            "size_bytes": len(content),
            "sha256": _sha256_bytes(content),
        }
        for name, content in sorted(payloads.items())
    ]
    provenance = package_inputs.provenance_metadata()
    inventory_payload = {
        "created_utc": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "generator": "app-side V6 real-output package generator",
        "input_run_id": package_inputs.run_id,
        "file_count": len(records),
        "package_provenance": provenance,
        "records": records,
    }
    inventory_text = json.dumps(inventory_payload, indent=2, sort_keys=True)
    inventory_bytes = inventory_text.encode("utf-8")
    write_text_atomic(inventory_path, inventory_text, encoding="utf-8")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(payloads.items()):
            archive.writestr(name, content)
        archive.writestr(inventory_path.name, inventory_bytes)

    zip_readiness = build_v6_zip_readiness_report(
        zip_path=zip_path,
        inventory_path=inventory_path,
        payload_records=records,
    )
    validation_report = validate_generated_v6_payload_shape(
        payloads=payloads,
        inventory_filename=inventory_path.name,
    )
    validation_report.update(
        {
            "zip_filename": zip_path.name,
            "inventory_filename": inventory_path.name,
            "input_run_id": package_inputs.run_id,
            "zip_entry_count": len(payloads) + 1,
            "package_sha256": _sha256_path(zip_path),
            "real_output_feed": True,
            "package_provenance": provenance,
            "zip_ready": bool(zip_readiness["zip_ready"]),
            "zip_readiness": zip_readiness,
        }
    )
    if not zip_readiness["zip_ready"]:
        issues = list(validation_report.get("issues", []))
        issues.extend(f"zip_readiness:{issue}" for issue in zip_readiness["issues"])
        validation_report["issues"] = sorted(set(issues))
        validation_report["validation_status"] = GENERATOR_STATUS_INVALID
    write_text_atomic(
        validation_report_path,
        json.dumps(validation_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return V6GeneratedPackageResult(
        output_dir=str(root),
        zip_path=str(zip_path),
        inventory_path=str(inventory_path),
        validation_report_path=str(validation_report_path),
        validation_status=str(validation_report["validation_status"]),
        payload_count=len(payloads),
        zip_entry_count=len(payloads) + 1,
        category_counts=dict(validation_report["category_counts"]),
        payload_file_names=tuple(sorted(payloads)),
        issues=tuple(validation_report["issues"]),
    )


def build_v6_payloads_from_real_outputs(*, package_inputs: V6RealPackageInputs) -> dict[str, bytes]:
    timestamp = package_inputs.timestamp
    top25_csv = f"lawful_gee_candidate_scout_top_25_{timestamp}.csv"
    top25_geojson = f"lawful_gee_candidate_scout_top_25_{timestamp}.geojson"
    provenance_columns = _provenance_columns(package_inputs)

    candidates_by_cell = {candidate.cell_id: candidate for candidate in package_inputs.scored_candidates}
    top_candidates = tuple(sorted(package_inputs.scored_candidates, key=lambda item: item.final_priority_rank_v6))[:25]

    top_candidate_rows = [
        {
            "cell_id": candidate.cell_id,
            "candidate_score": _format_score(candidate.candidate_score),
            "final_priority_rank_v6": candidate.final_priority_rank_v6,
            "v6_review_priority_score": _format_score(candidate.v6_review_priority_score),
            "v6_false_positive_warning_count": candidate.v6_false_positive_warning_count,
            **provenance_columns,
        }
        for candidate in top_candidates
    ]
    enhanced_rows = [
        {
            **candidate.as_package_row(),
            "candidate_score": _format_score(candidate.candidate_score),
            "remote_sensing_contrast": _format_score(candidate.remote_sensing_contrast),
            "s2_confidence": _format_score(candidate.s2_confidence),
            "v6_false_positive_penalty": _format_score(candidate.v6_false_positive_penalty),
            "v6_quality_adjusted_score": _format_score(candidate.v6_quality_adjusted_score),
            "v6_no_warning_bonus": _format_score(candidate.v6_no_warning_bonus),
            "v6_review_priority_score": _format_score(candidate.v6_review_priority_score),
            **provenance_columns,
        }
        for candidate in top_candidates
    ]
    request_zone_rows = [
        {
            "request_zone_id": zone.request_zone_id,
            "primary_cell_id": zone.source_cell_id,
            "source_cell_id": zone.source_cell_id,
            "quote_id": zone.quote_id,
            "final_priority_rank_v6": zone.final_priority_rank_v6,
            "v6_review_priority_score": _format_score(zone.v6_review_priority_score),
            "v6_false_positive_warning_count": zone.v6_false_positive_warning_count,
            **provenance_columns,
        }
        for zone in package_inputs.request_zones
    ]
    quote_template_rows = [
        {
            "quote_id": zone.quote_id,
            "request_zone_id": zone.request_zone_id,
            "primary_cell_id": zone.source_cell_id,
            "final_priority_rank_v6": zone.final_priority_rank_v6,
            **provenance_columns,
        }
        for zone in package_inputs.request_zones
    ]
    quote_comparison_rows = [
        {
            "quote_id": zone.quote_id,
            "request_zone_id": zone.request_zone_id,
            "quote_score": _format_score(candidates_by_cell[zone.source_cell_id].v6_review_priority_score),
            "source_cell_id": zone.source_cell_id,
            **provenance_columns,
        }
        for zone in package_inputs.request_zones
        if zone.source_cell_id in candidates_by_cell
    ]
    zone_geojson = request_zones_to_geojson(package_inputs.request_zones)
    top_geojson = _candidate_zone_geojson(top_candidates, package_inputs.request_zones)

    return {
        top25_csv: _csv_bytes_from_dicts(
            [
                "cell_id",
                "candidate_score",
                "final_priority_rank_v6",
                "v6_review_priority_score",
                "v6_false_positive_warning_count",
                *_PROVENANCE_HEADERS,
            ],
            top_candidate_rows,
        ),
        top25_geojson: _json_bytes(top_geojson),
        "top25_enhanced_v6.csv": _csv_bytes_from_dicts(_ENHANCED_HEADERS, enhanced_rows),
        "top25_enhanced_v6.geojson": _json_bytes(top_geojson),
        "quality_diagnostics_all_cells_v6.csv": _csv_bytes_from_dicts(_ENHANCED_HEADERS, enhanced_rows),
        "stable_candidate_priority_list_v6.csv": _csv_bytes_from_dicts(_STABLE_HEADERS, enhanced_rows),
        "request_zones_v6.csv": _csv_bytes_from_dicts(
            [
                "request_zone_id",
                "primary_cell_id",
                "source_cell_id",
                "quote_id",
                "final_priority_rank_v6",
                "v6_review_priority_score",
                "v6_false_positive_warning_count",
                *_PROVENANCE_HEADERS,
            ],
            request_zone_rows,
        ),
        "request_zones_v6.geojson": _json_bytes(zone_geojson),
        "paid_imagery_quote_template_v6.csv": _csv_bytes_from_dicts(
            ["quote_id", "request_zone_id", "primary_cell_id", "final_priority_rank_v6", *_PROVENANCE_HEADERS],
            quote_template_rows,
        ),
        "paid_imagery_quote_comparison_v6.csv": _csv_bytes_from_dicts(
            ["quote_id", "request_zone_id", "quote_score", "source_cell_id", *_PROVENANCE_HEADERS],
            quote_comparison_rows,
        ),
        "paid_archive_request_summary.txt": (
            "App-generated V6 request package summary.\n"
            f"Input run: {package_inputs.run_id}\n"
            f"Candidate count: {len(package_inputs.scored_candidates)}\n"
            f"Request zone count: {len(package_inputs.request_zones)}\n"
            f"Package provenance: {package_inputs.package_provenance}\n"
            f"Score basis: {package_inputs.score_basis}\n"
            f"Geometry basis: {package_inputs.geometry_basis}\n"
            f"Fallback score used: {bool(package_inputs.fallback_score_used)}\n"
            f"Fallback geometry used: {bool(package_inputs.fallback_geometry_used)}\n"
            f"Frozen external notebook parity claimed: {bool(package_inputs.frozen_notebook_parity_claimed)}\n"
            "This package is generated from app-side scored candidates and request zones.\n"
            "The visual inspection map is a placeholder and does not contain imagery.\n"
        ).encode("utf-8"),
        "visual_inspection_map.html": (
            "<!doctype html>\n"
            "<html><head><meta charset=\"utf-8\"><title>V6 App Generated Map Placeholder</title></head>\n"
            "<body><p>Private app-generated V6 map placeholder. No imagery is embedded in this HTML.</p></body></html>\n"
        ).encode("utf-8"),
    }


_PROVENANCE_HEADERS = [
    "score_basis",
    "geometry_basis",
    "package_provenance",
    "fallback_score_used",
    "fallback_geometry_used",
    "frozen_notebook_parity_claimed",
]

_ENHANCED_HEADERS = [
    "cell_id",
    "candidate_score",
    "v6_review_priority_score",
    "final_priority_rank_v6",
    "remote_sensing_contrast",
    "s2_confidence",
    "v6_false_positive_warning_count",
    "v6_false_positive_penalty",
    "v6_quality_adjusted_score",
    "v6_no_warning_bonus",
    *_PROVENANCE_HEADERS,
]

_STABLE_HEADERS = [
    "cell_id",
    "candidate_score",
    "v6_review_priority_score",
    "final_priority_rank_v6",
    "v6_false_positive_warning_count",
    *_PROVENANCE_HEADERS,
]


def _provenance_columns(package_inputs: V6RealPackageInputs) -> dict[str, object]:
    return {
        "score_basis": package_inputs.score_basis,
        "geometry_basis": package_inputs.geometry_basis,
        "package_provenance": package_inputs.package_provenance,
        "fallback_score_used": bool(package_inputs.fallback_score_used),
        "fallback_geometry_used": bool(package_inputs.fallback_geometry_used),
        "frozen_notebook_parity_claimed": bool(package_inputs.frozen_notebook_parity_claimed),
    }


def _candidate_zone_geojson(
    candidates: Sequence[V6ScoredCandidate],
    zones: Sequence[V6RequestZone],
) -> dict[str, Any]:
    zones_by_cell = {zone.source_cell_id: zone for zone in zones}
    features = []
    for candidate in candidates:
        zone = zones_by_cell.get(candidate.cell_id)
        if zone is None:
            continue
        feature = zone.as_geojson_feature()
        feature["properties"] = {
            **feature["properties"],
            "cell_id": candidate.cell_id,
            "candidate_score": candidate.candidate_score,
            "v6_review_priority_score": candidate.v6_review_priority_score,
        }
        features.append(feature)
    return {"type": "FeatureCollection", "features": features}


def _csv_bytes_from_dicts(headers: Sequence[str], rows: Sequence[Mapping[str, Any]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(headers), extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(dict(row))
    return output.getvalue().encode("utf-8")


def _json_bytes(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _format_score(value: float) -> str:
    return f"{value:.6g}"


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()
