from __future__ import annotations

from pathlib import Path

from app.config import Settings
from app.services.run_history import RUN_STATUS_HISTORY_NAME, append_run_event, read_run_history_events


def _settings(root: Path) -> Settings:
    return Settings(data_dir=root, database_path=root / "test.db")


def test_read_run_history_distinguishes_missing_from_corrupt_history(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_id = "run-1"

    assert read_run_history_events(settings, run_id) == []

    history_path = tmp_path / "runs" / run_id / RUN_STATUS_HISTORY_NAME
    history_path.parent.mkdir(parents=True)
    history_path.write_text("{not-json", encoding="utf-8")

    events = read_run_history_events(settings, run_id)
    assert len(events) == 1
    assert events[0].event_type == "history_read_error"
    assert events[0].label == "Run history unreadable"
    assert events[0].message == "Run history metadata could not be read."
    assert events[0].stage_name is None


def test_append_run_event_does_not_persist_synthetic_history_read_error(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_id = "run-1"
    history_path = tmp_path / "runs" / run_id / RUN_STATUS_HISTORY_NAME
    history_path.parent.mkdir(parents=True)
    history_path.write_text("{not-json", encoding="utf-8")

    append_run_event(settings, run_id, "run_started")

    events = read_run_history_events(settings, run_id)
    assert [event.event_type for event in events] == ["run_started"]
