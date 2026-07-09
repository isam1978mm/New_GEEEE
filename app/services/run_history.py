from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel

from app.config import Settings
from app.services.storage import initialize_run_storage, read_manifest

RUN_STATUS_HISTORY_NAME = "run_status_history.json"

SAFE_STAGE_LABELS: dict[str, str] = {
    "grid": "GRID setup",
    "dem": "DEM",
    "zero_shift": "Zero shift",
    "sar_rtc": "SAR RTC",
    "s2_indices": "Sentinel-2 indices",
    "dem_derivatives": "DEM derivatives",
    "thermal": "Thermal",
    "feature_stacks": "Feature stacks",
    "focus_mask": "Focus mask",
    "location_exports": "Location exports",
    "field_ops_exports": "Field ops exports",
    "gps_compare": "GPS comparison",
    "hypercube": "Hypercube",
    "pca_anomaly": "PCA anomaly",
    "object_extract": "Object extraction",
    "classifier": "Classifier",
    "alignment_qa": "Alignment QA",
}

SAFE_EVENT_TYPES = {
    "run_created",
    "run_queued",
    "run_started",
    "stage_started",
    "stage_done",
    "stage_failed",
    "run_done",
    "run_failed",
    "run_stale_failed",
    "history_read_error",
}


class RunHistoryEvent(BaseModel):
    timestamp: datetime
    event_type: str
    label: str
    message: str
    stage_name: str | None = None


def append_run_event(
    settings: Settings,
    run_id: str,
    event_type: str,
    *,
    stage_name: str | None = None,
    timestamp: datetime | None = None,
) -> None:
    event = build_run_event(event_type=event_type, stage_name=stage_name, timestamp=timestamp)
    if event is None:
        return
    events = read_run_history_events(settings, run_id, include_read_errors=False)
    events.append(event)
    run_dir = initialize_run_storage(settings, run_id)
    payload = {"events": [event.model_dump(mode="json") for event in events]}
    (run_dir / RUN_STATUS_HISTORY_NAME).write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def read_run_history_events(
    settings: Settings,
    run_id: str,
    *,
    include_read_errors: bool = True,
) -> list[RunHistoryEvent]:
    run_dir = initialize_run_storage(settings, run_id)
    history_path = run_dir / RUN_STATUS_HISTORY_NAME
    if not history_path.exists():
        return []
    try:
        payload = read_manifest(history_path)
    except (OSError, ValueError):
        return _history_read_error_events() if include_read_errors else []
    raw_events = payload.get("events")
    if not isinstance(raw_events, list):
        return _history_read_error_events() if include_read_errors else []
    events: list[RunHistoryEvent] = []
    for raw_event in raw_events:
        if not isinstance(raw_event, dict):
            continue
        event = _coerce_event(raw_event)
        if event is not None:
            events.append(event)
    return events


def build_run_event(
    *,
    event_type: str,
    stage_name: str | None = None,
    timestamp: datetime | None = None,
) -> RunHistoryEvent | None:
    if event_type not in SAFE_EVENT_TYPES:
        return None
    if event_type.startswith("stage_"):
        if stage_name not in SAFE_STAGE_LABELS:
            return None
        stage_label = SAFE_STAGE_LABELS[stage_name]
    else:
        stage_name = None
        stage_label = None

    label, message = _event_text(event_type, stage_label)
    event_time = timestamp or datetime.now(timezone.utc)
    return RunHistoryEvent(
        timestamp=event_time,
        event_type=event_type,
        label=label,
        stage_name=stage_name,
        message=message,
    )


def _coerce_event(raw_event: dict[str, Any]) -> RunHistoryEvent | None:
    event_type = raw_event.get("event_type")
    timestamp = raw_event.get("timestamp")
    stage_name = raw_event.get("stage_name")
    if not isinstance(event_type, str) or event_type not in SAFE_EVENT_TYPES:
        return None
    if not isinstance(timestamp, str):
        return None
    try:
        event_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    safe_stage = stage_name if isinstance(stage_name, str) else None
    return build_run_event(event_type=event_type, stage_name=safe_stage, timestamp=event_time)


def _history_read_error_events() -> list[RunHistoryEvent]:
    event = build_run_event(event_type="history_read_error")
    return [event] if event is not None else []


def _event_text(event_type: str, stage_label: str | None) -> tuple[str, str]:
    if event_type == "run_created":
        return "Run created", "Run record created."
    if event_type == "run_queued":
        return "Run queued", "Run accepted for processing."
    if event_type == "run_started":
        return "Run started", "Pipeline execution started."
    if event_type == "run_done":
        return "Run completed", "Pipeline execution completed."
    if event_type == "run_failed":
        return "Run failed", "Pipeline execution failed."
    if event_type == "run_stale_failed":
        return "Run marked stale", "Run did not complete before process restart."
    if event_type == "history_read_error":
        return "Run history unreadable", "Run history metadata could not be read."
    if event_type == "stage_started" and stage_label:
        return f"{stage_label} started", f"{stage_label} stage started."
    if event_type == "stage_done" and stage_label:
        return f"{stage_label} completed", f"{stage_label} stage completed."
    if event_type == "stage_failed" and stage_label:
        return f"{stage_label} failed", f"{stage_label} stage failed."
    return "Run event", "Run status changed."
