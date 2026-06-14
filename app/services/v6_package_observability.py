"""Safe metadata-only observability for the V6 private package flow."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
import logging
from threading import Lock
from typing import Any, Mapping

LOGGER_NAME = "app.v6_package_flow"

_SAFE_COUNTERS: Counter[tuple[str, str, str]] = Counter()
_COUNTER_LOCK = Lock()
_LOGGER = logging.getLogger(LOGGER_NAME)


@dataclass(frozen=True)
class V6PackageFlowObservation:
    action: str
    outcome: str
    status_code: int
    request_id: str
    run_id: str
    package_ready: bool
    flow_enabled: bool
    actor_authenticated: bool
    operator_role_present: bool
    denial_reason: str | None = None
    validation_status: str | None = None
    payload_count: int | None = None
    zip_entry_count: int | None = None
    issue_count: int | None = None
    warning_count: int | None = None

    @property
    def rollback_state(self) -> str:
        return "enabled" if self.flow_enabled else "disabled"


def record_v6_package_flow_observation(observation: V6PackageFlowObservation) -> None:
    """Record one safe metadata-only V6 package-flow event.

    The emitted log and counters intentionally exclude package bodies, candidate rows,
    spatial payloads, file paths, bearer values, provider credentials, and coordinates.
    """

    safe_event = observation_to_safe_log_dict(observation)
    assert_safe_v6_observation_payload(safe_event)

    with _COUNTER_LOCK:
        _SAFE_COUNTERS[("action", observation.action, observation.outcome)] += 1
        _SAFE_COUNTERS[("status", observation.action, str(observation.status_code))] += 1
        _SAFE_COUNTERS[("rollback_state", observation.rollback_state, observation.outcome)] += 1
        if observation.outcome == "denied":
            _SAFE_COUNTERS[("denied", observation.denial_reason or "generic", observation.action)] += 1

    _LOGGER.info(
        "v6_package_flow_event %s",
        json.dumps(safe_event, sort_keys=True, separators=(",", ":")),
    )


def observation_to_safe_log_dict(observation: V6PackageFlowObservation) -> dict[str, Any]:
    """Return the exact metadata shape permitted in logs."""

    event: dict[str, Any] = {
        "action": observation.action,
        "outcome": observation.outcome,
        "status_code": observation.status_code,
        "request_id": observation.request_id,
        "run_id": observation.run_id,
        "package_ready": observation.package_ready,
        "rollback_state": observation.rollback_state,
        "actor_authenticated": observation.actor_authenticated,
        "operator_role_present": observation.operator_role_present,
    }
    if observation.denial_reason:
        event["denial_reason"] = observation.denial_reason
    if observation.validation_status:
        event["validation_status"] = observation.validation_status
    if observation.payload_count is not None:
        event["payload_count"] = observation.payload_count
    if observation.zip_entry_count is not None:
        event["zip_entry_count"] = observation.zip_entry_count
    if observation.issue_count is not None:
        event["issue_count"] = observation.issue_count
    if observation.warning_count is not None:
        event["warning_count"] = observation.warning_count
    return event


def get_v6_package_flow_counters_snapshot() -> dict[str, int]:
    """Return a stable, string-keyed snapshot for tests or diagnostics."""

    with _COUNTER_LOCK:
        return {"|".join(key): value for key, value in sorted(_SAFE_COUNTERS.items())}


def reset_v6_package_flow_counters_for_tests() -> None:
    """Reset in-memory counters for unit tests only."""

    with _COUNTER_LOCK:
        _SAFE_COUNTERS.clear()


def assert_safe_v6_observation_payload(payload: Mapping[str, Any]) -> None:
    """Guard the observability contract against accidentally logging private data."""

    forbidden_keys = {
        "authorization",
        "access_token",
        "bearer",
        "token",
        "candidate_rows",
        "feature_rows",
        "scored_candidates",
        "request_zones",
        "spatial_payload",
        "geometry",
        "coordinates",
        "bounds",
        "bbox",
        "zip_path",
        "package_path",
        "input_path",
        "output_dir",
        "provider_credentials",
    }
    normalized_keys = {str(key).lower() for key in payload.keys()}
    leaked = forbidden_keys.intersection(normalized_keys)
    if leaked:
        raise ValueError(f"unsafe V6 observability fields: {sorted(leaked)}")


__all__ = [
    "LOGGER_NAME",
    "V6PackageFlowObservation",
    "assert_safe_v6_observation_payload",
    "get_v6_package_flow_counters_snapshot",
    "observation_to_safe_log_dict",
    "record_v6_package_flow_observation",
    "reset_v6_package_flow_counters_for_tests",
]
