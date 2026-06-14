"""Private V6 app generate/review/download flow."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

from app.config import Settings
from app.pipeline.parity.operator_overlay_access_foundation import (
    GENERIC_DENIAL_MESSAGE,
    GENERIC_DENIAL_REASON_CODE,
    GENERIC_DENIAL_STATUS,
    GENERIC_DENIAL_SUPPORT_REFERENCE,
    OPERATOR_ROLE,
)
from app.services.operator_run_authorization import resolve_run_authorization
from app.services.storage import get_run_dir
from app.services.v6_package_observability import V6PackageFlowObservation, record_v6_package_flow_observation
from app.services.v6_real_gee_runtime import validate_v6_aoi_bounds
from app.services.v6_real_package import V6RealPackageInputs, generate_v6_package_from_real_outputs
from app.services.v6_real_scoring import V6ScoredCandidate
from app.services.v6_real_zones import V6RequestZone


V6_PRIVATE_INPUT_RELATIVE_PATH = Path("private") / "v6" / "real_package_inputs.json"
V6_PRIVATE_PACKAGE_RELATIVE_DIR = Path("private") / "v6" / "generated_package"


@dataclass(frozen=True)
class V6PrivatePackageFlowResult:
    status_code: int
    body: dict[str, Any]
    file_path: Path | None = None
    file_name: str | None = None


@dataclass(frozen=True)
class V6PrivatePackageAccessContext:
    actor_id: str | None
    is_authenticated: bool
    roles: tuple[str, ...]
    authorized_run_ids: tuple[str, ...]
    request_id: str


def generate_private_v6_package(
    *,
    settings: Settings,
    run_id: str,
    access_context: V6PrivatePackageAccessContext,
) -> V6PrivatePackageFlowResult:
    denial_reason = _access_denial_reason(settings=settings, run_id=run_id, access_context=access_context)
    if denial_reason is not None:
        return _observe_and_return(
            action="generate",
            settings=settings,
            run_id=run_id,
            access_context=access_context,
            result=_denied(access_context.request_id),
            denial_reason=denial_reason,
        )

    input_path = _private_input_path(settings, run_id)
    if not input_path.is_file():
        return _observe_and_return(
            action="generate",
            settings=settings,
            run_id=run_id,
            access_context=access_context,
            result=_not_available(run_id=run_id, request_id=access_context.request_id),
        )

    try:
        package_inputs = load_v6_real_package_inputs(input_path)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return _observe_and_return(
            action="generate",
            settings=settings,
            run_id=run_id,
            access_context=access_context,
            result=V6PrivatePackageFlowResult(
                status_code=400,
                body=_operator_body(
                    outcome="invalid_package_inputs",
                    run_id=run_id,
                    request_id=access_context.request_id,
                    package_ready=False,
                ),
            ),
        )

    output_dir = _private_package_dir(settings, run_id)
    result = generate_v6_package_from_real_outputs(output_dir=output_dir, package_inputs=package_inputs)
    return _observe_and_return(
        action="generate",
        settings=settings,
        run_id=run_id,
        access_context=access_context,
        result=V6PrivatePackageFlowResult(
            status_code=200,
            body=_package_result_body(
                outcome="generated",
                run_id=run_id,
                request_id=access_context.request_id,
                result=result,
            ),
        ),
    )


def review_private_v6_package(
    *,
    settings: Settings,
    run_id: str,
    access_context: V6PrivatePackageAccessContext,
) -> V6PrivatePackageFlowResult:
    denial_reason = _access_denial_reason(settings=settings, run_id=run_id, access_context=access_context)
    if denial_reason is not None:
        return _observe_and_return(
            action="review",
            settings=settings,
            run_id=run_id,
            access_context=access_context,
            result=_denied(access_context.request_id),
            denial_reason=denial_reason,
        )

    report_path = _latest_validation_report_path(settings, run_id)
    zip_path = _latest_zip_path(settings, run_id)
    if report_path is None or zip_path is None:
        return _observe_and_return(
            action="review",
            settings=settings,
            run_id=run_id,
            access_context=access_context,
            result=_not_available(run_id=run_id, request_id=access_context.request_id),
        )

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _observe_and_return(
            action="review",
            settings=settings,
            run_id=run_id,
            access_context=access_context,
            result=V6PrivatePackageFlowResult(
                status_code=200,
                body=_operator_body(
                    outcome="not_available",
                    run_id=run_id,
                    request_id=access_context.request_id,
                    package_ready=False,
                ),
            ),
        )

    body = _operator_body(
        outcome="available",
        run_id=run_id,
        request_id=access_context.request_id,
        package_ready=True,
    )
    body.update(
        {
            "validation_status": str(report.get("validation_status", "unknown")),
            "payload_count": int(report.get("payload_count", 0) or 0),
            "zip_entry_count": int(report.get("zip_entry_count", 0) or 0),
            "category_counts": dict(report.get("category_counts", {})),
            "issue_count": len(report.get("issues", []) or []),
            "warning_count": len(report.get("warnings", []) or []),
            "zip_filename": zip_path.name,
            "validation_report_filename": report_path.name,
        }
    )
    return _observe_and_return(
        action="review",
        settings=settings,
        run_id=run_id,
        access_context=access_context,
        result=V6PrivatePackageFlowResult(status_code=200, body=body),
    )


def resolve_private_v6_package_download(
    *,
    settings: Settings,
    run_id: str,
    access_context: V6PrivatePackageAccessContext,
) -> V6PrivatePackageFlowResult:
    denial_reason = _access_denial_reason(settings=settings, run_id=run_id, access_context=access_context)
    if denial_reason is not None:
        return _observe_and_return(
            action="retrieve",
            settings=settings,
            run_id=run_id,
            access_context=access_context,
            result=_denied(access_context.request_id),
            denial_reason=denial_reason,
        )

    zip_path = _latest_zip_path(settings, run_id)
    if zip_path is None:
        return _observe_and_return(
            action="retrieve",
            settings=settings,
            run_id=run_id,
            access_context=access_context,
            result=_not_available(run_id=run_id, request_id=access_context.request_id),
        )
    return _observe_and_return(
        action="retrieve",
        settings=settings,
        run_id=run_id,
        access_context=access_context,
        result=V6PrivatePackageFlowResult(
            status_code=200,
            body=_operator_body(
                outcome="available",
                run_id=run_id,
                request_id=access_context.request_id,
                package_ready=True,
            ),
            file_path=zip_path,
            file_name=zip_path.name,
        ),
    )


def load_v6_real_package_inputs(path: str | Path) -> V6RealPackageInputs:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, Mapping):
        raise ValueError("package input must be an object")
    candidates_raw = payload.get("scored_candidates")
    zones_raw = payload.get("request_zones")
    if not isinstance(candidates_raw, list) or not isinstance(zones_raw, list):
        raise ValueError("package input rows are required")

    candidates = tuple(_candidate_from_mapping(row) for row in candidates_raw)
    zones = tuple(_zone_from_mapping(row) for row in zones_raw)
    return V6RealPackageInputs(
        run_id=_required_str(payload.get("run_id"), "run_id"),
        timestamp=_required_str(payload.get("timestamp"), "timestamp"),
        scored_candidates=candidates,
        request_zones=zones,
    )


def _candidate_from_mapping(row: object) -> V6ScoredCandidate:
    if not isinstance(row, Mapping):
        raise ValueError("candidate row must be an object")
    return V6ScoredCandidate(
        cell_id=_required_str(row.get("cell_id"), "cell_id"),
        candidate_score=float(row.get("candidate_score")),
        remote_sensing_contrast=float(row.get("remote_sensing_contrast")),
        s2_confidence=float(row.get("s2_confidence")),
        builtup_warning=int(row.get("builtup_warning")),
        cropland_heavy_warning=int(row.get("cropland_heavy_warning")),
        water_edge_warning=int(row.get("water_edge_warning")),
        modern_linear_edge_warning=int(row.get("modern_linear_edge_warning")),
        v6_building_warning=int(row.get("v6_building_warning")),
        v6_road_like_warning=int(row.get("v6_road_like_warning")),
        false_positive_warning_count=int(row.get("false_positive_warning_count")),
        v6_false_positive_warning_count=int(row.get("v6_false_positive_warning_count")),
        v6_false_positive_penalty=float(row.get("v6_false_positive_penalty")),
        v6_quality_adjusted_score=float(row.get("v6_quality_adjusted_score")),
        v6_no_warning_bonus=float(row.get("v6_no_warning_bonus")),
        v6_review_priority_score=float(row.get("v6_review_priority_score")),
        final_priority_rank_v6=int(row.get("final_priority_rank_v6")),
    )


def _zone_from_mapping(row: object) -> V6RequestZone:
    if not isinstance(row, Mapping):
        raise ValueError("request zone row must be an object")
    bounds_raw = row.get("bounds")
    if not isinstance(bounds_raw, Mapping):
        raise ValueError("request zone bounds are required")
    bounds = validate_v6_aoi_bounds(
        west=float(bounds_raw.get("west")),
        south=float(bounds_raw.get("south")),
        east=float(bounds_raw.get("east")),
        north=float(bounds_raw.get("north")),
    )
    return V6RequestZone(
        request_zone_id=_required_str(row.get("request_zone_id"), "request_zone_id"),
        source_cell_id=_required_str(row.get("source_cell_id"), "source_cell_id"),
        quote_id=_required_str(row.get("quote_id"), "quote_id"),
        final_priority_rank_v6=int(row.get("final_priority_rank_v6")),
        v6_review_priority_score=float(row.get("v6_review_priority_score")),
        v6_false_positive_warning_count=int(row.get("v6_false_positive_warning_count")),
        bounds=bounds,
    )


def _access_denial_reason(
    *,
    settings: Settings,
    run_id: str,
    access_context: V6PrivatePackageAccessContext,
) -> str | None:
    if not settings.v6_package_flow_enabled:
        return "package_flow_disabled"
    if not access_context.is_authenticated:
        return "operator_not_authenticated"
    if OPERATOR_ROLE not in set(access_context.roles):
        return "operator_role_missing"
    run_authorization = resolve_run_authorization(settings=settings, actor_id=access_context.actor_id, run_id=run_id)
    header_authorized = run_id in set(access_context.authorized_run_ids)
    if not run_authorization.allowed and not header_authorized:
        return "run_not_authorized"
    return None


def _deny_if_not_allowed(
    *,
    settings: Settings,
    run_id: str,
    access_context: V6PrivatePackageAccessContext,
) -> V6PrivatePackageFlowResult | None:
    if _access_denial_reason(settings=settings, run_id=run_id, access_context=access_context) is not None:
        return _denied(access_context.request_id)
    return None


def _denied(request_id: str) -> V6PrivatePackageFlowResult:
    return V6PrivatePackageFlowResult(
        status_code=403,
        body={
            "outcome": "denied",
            "status": GENERIC_DENIAL_STATUS,
            "reason_code": GENERIC_DENIAL_REASON_CODE,
            "request_id": request_id,
            "message": GENERIC_DENIAL_MESSAGE,
            "retry_allowed": False,
            "support_reference": GENERIC_DENIAL_SUPPORT_REFERENCE,
        },
    )


def _not_available(*, run_id: str, request_id: str) -> V6PrivatePackageFlowResult:
    return V6PrivatePackageFlowResult(
        status_code=200,
        body=_operator_body(
            outcome="not_available",
            run_id=run_id,
            request_id=request_id,
            package_ready=False,
        ),
    )


def _package_result_body(*, outcome: str, run_id: str, request_id: str, result: Any) -> dict[str, Any]:
    body = _operator_body(outcome=outcome, run_id=run_id, request_id=request_id, package_ready=result.is_verified)
    warnings = getattr(result, "warnings", ())
    body.update(
        {
            "validation_status": result.validation_status,
            "payload_count": result.payload_count,
            "zip_entry_count": result.zip_entry_count,
            "category_counts": dict(result.category_counts),
            "issue_count": len(result.issues),
            "warning_count": len(warnings),
            "zip_filename": Path(result.zip_path).name,
            "inventory_filename": Path(result.inventory_path).name,
            "validation_report_filename": Path(result.validation_report_path).name,
        }
    )
    return body


def _operator_body(*, outcome: str, run_id: str, request_id: str, package_ready: bool) -> dict[str, Any]:
    return {
        "outcome": outcome,
        "run_id": run_id,
        "request_id": request_id,
        "package_ready": package_ready,
        "filesystem_only": True,
        "frontend_visible": "operator_only",
        "public_access": False,
    }


def _observe_and_return(
    *,
    action: str,
    settings: Settings,
    run_id: str,
    access_context: V6PrivatePackageAccessContext,
    result: V6PrivatePackageFlowResult,
    denial_reason: str | None = None,
) -> V6PrivatePackageFlowResult:
    body = result.body
    record_v6_package_flow_observation(
        V6PackageFlowObservation(
            action=action,
            outcome=_safe_str(body.get("outcome"), "unknown"),
            status_code=result.status_code,
            request_id=_safe_str(body.get("request_id"), access_context.request_id),
            run_id=_safe_str(body.get("run_id"), run_id),
            package_ready=body.get("package_ready") is True,
            flow_enabled=bool(settings.v6_package_flow_enabled),
            actor_authenticated=access_context.is_authenticated,
            operator_role_present=OPERATOR_ROLE in set(access_context.roles),
            denial_reason=denial_reason,
            validation_status=_safe_optional_str(body.get("validation_status")),
            payload_count=_safe_optional_int(body.get("payload_count")),
            zip_entry_count=_safe_optional_int(body.get("zip_entry_count")),
            issue_count=_safe_optional_int(body.get("issue_count")),
            warning_count=_safe_optional_int(body.get("warning_count")),
        )
    )
    return result


def _private_input_path(settings: Settings, run_id: str) -> Path:
    return get_run_dir(settings, run_id) / V6_PRIVATE_INPUT_RELATIVE_PATH


def _private_package_dir(settings: Settings, run_id: str) -> Path:
    return get_run_dir(settings, run_id) / V6_PRIVATE_PACKAGE_RELATIVE_DIR


def _latest_validation_report_path(settings: Settings, run_id: str) -> Path | None:
    output_dir = _private_package_dir(settings, run_id)
    if not output_dir.is_dir():
        return None
    reports = sorted(output_dir.glob("V6_REAL_GENERATED_validation_*.json"))
    return reports[-1] if reports else None


def _latest_zip_path(settings: Settings, run_id: str) -> Path | None:
    output_dir = _private_package_dir(settings, run_id)
    if not output_dir.is_dir():
        return None
    zip_paths = sorted(output_dir.glob("V6_REAL_GENERATED_*.zip"))
    return zip_paths[-1] if zip_paths else None


def _required_str(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value.strip()


def _safe_str(value: object, fallback: str) -> str:
    return value if isinstance(value, str) and value else fallback


def _safe_optional_str(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _safe_optional_int(value: object) -> int | None:
    return value if isinstance(value, int) else None


__all__ = [
    "V6_PRIVATE_INPUT_RELATIVE_PATH",
    "V6_PRIVATE_PACKAGE_RELATIVE_DIR",
    "V6PrivatePackageAccessContext",
    "V6PrivatePackageFlowResult",
    "generate_private_v6_package",
    "review_private_v6_package",
    "resolve_private_v6_package_download",
    "load_v6_real_package_inputs",
]
